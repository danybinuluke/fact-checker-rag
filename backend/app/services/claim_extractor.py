"""
Claim Extractor Service — extracts factual claims from text.

Uses Gemini (primary) with Ollama fallback via llm_service.
Produces structured JSON with claims, entities, and confidence scores.
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from app.services.neo4j_service import ClaimNode, get_graph_store
from app.services.pinecone_service import corpus_manager

logger = logging.getLogger(__name__)


async def extract_claims(text: str, document_id: str = "user_input") -> Dict[str, Any]:
    """
    Extract factual claims from text using the LLM pipeline.

    Pipeline:
    1. Send text to LLM with extraction prompt
    2. Parse structured JSON response
    3. Add text to corpus (vector store)
    4. Store claim nodes in graph DB
    5. Return structured results

    Args:
        text: The source text to extract claims from.
        document_id: Optional identifier for the source document.

    Returns:
        Dict with status, document, claims list, and latency.
    """
    start_time = time.time()

    # Step 1: Add text to corpus for future similarity searches
    corpus_manager.add_to_corpus(text)

    # Step 2: Extract claims via LLM
    claims = await _extract_via_llm(text)

    # Step 3: Validate and normalize claims
    claims = _normalize_claims(claims)

    # Step 4: Store claim nodes in graph DB
    await _store_claims_in_graph(claims, document_id)

    elapsed_ms = (time.time() - start_time) * 1000

    return {
        "status": "success",
        "document": document_id,
        "claims": claims,
        "claims_count": len(claims),
        "latency_ms": elapsed_ms,
    }


async def _extract_via_llm(text: str) -> List[Dict[str, Any]]:
    """
    Send text to the LLM manager and receive normalized claims.

    Args:
        text: Source text (truncated for safety).

    Returns:
        List of claim dicts, or empty list on failure.
    """
    try:
        from app.llm import get_llm_manager
        
        manager = get_llm_manager()
        # Truncate text to avoid context window issues
        result = await manager.extract_claims(text[:20000])
        
        # Convert Pydantic models to dicts for downstream compatibility
        return [claim.model_dump() for claim in result.claims]
        
    except Exception as exc:
        logger.error("All LLMs failed for claim extraction: %s", exc)
        return []


def _normalize_claims(claims: List[Dict]) -> List[Dict[str, Any]]:
    """
    Validate and normalize claim data.

    Ensures each claim has required fields with valid ranges.
    """
    normalized = []
    for claim in claims:
        if not isinstance(claim, dict) or "claim" not in claim:
            continue
        claim_text = str(claim["claim"]).strip()
        if not claim_text:
            continue
        normalized.append({
            "claim": claim_text,
            "entities": claim.get("entities", []),
            "confidence": min(1.0, max(0.0, float(claim.get("confidence", 0.5)))),
        })
    return normalized


async def _store_claims_in_graph(
    claims: List[Dict[str, Any]], document_id: str
) -> None:
    """
    Store extracted claims as nodes in the graph database.

    Args:
        claims: List of normalized claim dicts.
        document_id: Source document identifier.
    """
    try:
        graph = get_graph_store()
        for i, claim in enumerate(claims):
            node = ClaimNode(
                id=f"{document_id}_claim_{i}_{uuid.uuid4().hex[:8]}",
                text=claim["claim"],
                confidence=claim["confidence"],
                entities=claim.get("entities", []),
                source_doc=document_id,
                node_type="extracted_claim",
            )
            await graph.store_claim_node(node)
    except Exception as exc:
        logger.error("Failed to store claims in graph: %s", exc)
