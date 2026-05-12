"""
Claims Router — endpoints for claim extraction and document upload.

POST /extract-claims   → Extract factual claims from text
POST /upload-document  → Upload a document, extract text, and add to corpus
"""

import io
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models import (
    ClaimModel,
    ExtractClaimsRequest,
    ExtractClaimsResponse,
    UploadDocumentResponse,
)
from app.services.claim_extractor import extract_claims
from app.services.pinecone_service import corpus_manager
from app.routers.system import record_request, record_error

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Claims"])


@router.post("/extract-claims", response_model=ExtractClaimsResponse)
async def handle_extract_claims(request: ExtractClaimsRequest) -> ExtractClaimsResponse:
    """
    Extract factual claims from provided text.

    Uses Gemini (primary) or Ollama (fallback) to identify 5-10 key factual
    claims with confidence scores and entity extraction.
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty.")

        doc_id = request.document_id or "user_input"
        result = await extract_claims(request.text, doc_id)
        record_request("extract", result.get("latency_ms", 0))

        return ExtractClaimsResponse(
            status=result["status"],
            document=result["document"],
            claims=[
                ClaimModel(
                    claim=c["claim"],
                    entities=c.get("entities", []),
                    confidence=c.get("confidence", 0.5),
                    source_doc=doc_id,
                )
                for c in result["claims"]
            ],
            claims_count=result["claims_count"],
            latency_ms=result["latency_ms"],
            timestamp=datetime.now(timezone.utc),
        )

    except HTTPException:
        raise
    except Exception as exc:
        record_error()
        logger.error("Claim extraction failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Claim extraction failed: {str(exc)}")


@router.post("/upload-document", response_model=UploadDocumentResponse)
async def handle_upload_document(file: UploadFile = File(...)) -> UploadDocumentResponse:
    """
    Upload a document (TXT, PDF, DOCX), extract text, and add to corpus.

    The extracted text is automatically chunked, embedded, and stored in the
    vector database. Claims are also extracted and stored in the graph DB.
    """
    try:
        content = await file.read()
        filename = (file.filename or "unknown").lower()
        text = ""

        if filename.endswith(".txt"):
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("windows-1252", errors="ignore")
        elif filename.endswith(".pdf"):
            import fitz  # PyMuPDF
            doc = fitz.open(stream=content, filetype="pdf")
            text = "\n".join(page.get_text() for page in doc)
            
            # If PyMuPDF extracts very little text or garbled text, 
            # we can fallback to pdfplumber locally instead of using an API
            import string
            printable = set(string.printable)
            printable_ratio = sum(1 for c in text if c in printable) / max(len(text), 1)
            
            if len(text) < 50 or printable_ratio < 0.5:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        elif filename.endswith(".docx"):
            import docx
            doc = docx.Document(io.BytesIO(content))
            text = "\n".join(para.text for para in doc.paragraphs)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {filename}. Use .txt, .pdf, or .docx",
            )

        text = text.replace("\x00", " ")
        text = "".join(c for c in text if c.isprintable() or c in "\n\r\t")

        if not text.strip():
            raise HTTPException(
                status_code=400, detail="Could not extract any readable text from the document. If this is a PDF, it might be an image-based scan."
            )

        import string
        printable = set(string.printable)
        printable_ratio = sum(1 for c in text if c in printable) / max(len(text), 1)
        if len(text) > 50 and printable_ratio < 0.3:
            raise HTTPException(
                status_code=400, 
                detail="Extracted text appears to be corrupted or encoded with garbled characters. Please ensure the document is a readable text file and not an image-based or encrypted PDF."
            )

        result = await extract_claims(text, file.filename or "uploaded_doc")
        record_request("extract", result.get("latency_ms", 0))

        return UploadDocumentResponse(
            status="success",
            filename=file.filename or "unknown",
            claims_count=result["claims_count"],
            text_preview=text[:200] + "..." if len(text) > 200 else text,
            document_id=result["document"],
        )

    except HTTPException:
        raise
    except Exception as exc:
        record_error()
        logger.error("Document upload failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to process document: {str(exc)}"
        )
