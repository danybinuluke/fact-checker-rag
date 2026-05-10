"""
Verification Router — endpoint for claim verification.

POST /verify-claim → Verify a claim against the stored corpus
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.models import VerifyClaimRequest, VerifyClaimResponse
from app.services.contradiction_detector import verify_claim
from app.routers.system import record_request, record_error

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Verification"])


@router.post("/verify-claim", response_model=VerifyClaimResponse)
async def handle_verify_claim(request: VerifyClaimRequest) -> VerifyClaimResponse:
    """
    Verify a claim against the knowledge corpus.

    Pipeline:
    1. Retrieves semantically similar claims from vector store
    2. Sends to LLM for SUPPORT / CONTRADICTION / NEUTRAL reasoning
    3. Stores the relationship in graph DB
    4. Returns verdict with confidence and evidence
    """
    try:
        if not request.claim.strip():
            raise HTTPException(status_code=400, detail="Claim cannot be empty.")

        result = await verify_claim(request.claim, model=request.model)
        record_request("verify", result.get("response_time_ms", 0))

        return VerifyClaimResponse(
            status=result["status"],
            user_claim=result["user_claim"],
            verification_status=result["verification_status"],
            confidence_score=result["confidence_score"],
            corpus_confidence=result.get("corpus_confidence", 0.0),
            training_confidence=result.get("training_confidence", 0.0),
            source=result.get("source", "unknown"),
            corpus_match_found=result.get("corpus_match_found", False),
            corpus_match_score=result.get("corpus_match_score", 0.0),
            explanation=result["explanation"],
            supporting_evidence=result["supporting_evidence"],
            contradicting_evidence=result["contradicting_evidence"],
            response_time_ms=result["response_time_ms"],
            timestamp=datetime.now(timezone.utc),
        )

    except HTTPException:
        raise
    except Exception as exc:
        record_error()
        logger.error("Claim verification failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Claim verification failed: {str(exc)}"
        )
