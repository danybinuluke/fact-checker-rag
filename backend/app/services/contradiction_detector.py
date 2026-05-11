"""
Contradiction Detector Service — verifies claims against the corpus.

Pipeline:
1. Query vector store for semantically similar claims
2. Send user claim + retrieved evidence to LLM for reasoning
3. Parse verdict (SUPPORT / CONTRADICTION / NEUTRAL)
4. Store relationship in graph DB
5. Return structured result with confidence and evidence
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from app.services.neo4j_service import ClaimNode, ClaimRelationship, get_graph_store
from app.services.pinecone_service import ScoredMatch, corpus_manager

logger = logging.getLogger(__name__)


async def verify_claim(user_claim: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify a claim against the stored corpus using hybrid RAG.

    Pipeline:
    1. Vector similarity search against corpus
    2. LLM-based contradiction reasoning
    3. Store result as graph relationship
    4. Return structured verdict

    Args:
        user_claim: The claim text to verify.

    Returns:
        Dict with verification status, confidence, evidence, and timing.
    """
    start_time = time.time()

    # Stage 1: Retrieve similar claims from vector store
    similar_matches = corpus_manager.query_similar(
        user_claim, top_k=10, threshold=0.2
    )
    similar_texts = [m.text for m in similar_matches]
    corpus_match_found = len(similar_matches) > 0
    best_similarity = similar_matches[0].score if similar_matches else 0.0

    # Stage 2: LLM reasoning
    analysis = await _analyze_claim(user_claim, similar_texts, model=model)

    # Stage 3: Store in graph DB
    await _store_verification_in_graph(user_claim, analysis)

    elapsed_ms = (time.time() - start_time) * 1000

    return {
        "status": "success",
        "user_claim": user_claim,
        "verification_status": analysis.get("status", "NEUTRAL"),
        "confidence_score": analysis.get("confidence", 0.0),
        "corpus_confidence": analysis.get("corpus_confidence", 0.0),
        "training_confidence": analysis.get("training_confidence", 0.0),
        "source": analysis.get("source", "unknown"),
        "corpus_match_found": corpus_match_found,
        "corpus_match_score": best_similarity,
        "explanation": analysis.get("explanation", ""),
        "supporting_evidence": analysis.get("supporting", []),
        "contradicting_evidence": analysis.get("contradicting", []),
        "response_time_ms": elapsed_ms,
    }


async def _analyze_claim(
    user_claim: str, similar_claims: List[str], model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform deep analysis of a claim using the fallback-enabled LLM manager.
    """
    try:
        from app.llm import get_llm_manager
        
        similar_text = _format_similar_claims(similar_claims)
        manager = get_llm_manager()
        
        # Verify claim using the fallback chain (starting with preferred provider if specified)
        result = await manager.verify_claim(user_claim, similar_text, provider=model)
        
        # Return as dictionary for backward compatibility with FastAPI router
        return result.model_dump()
        
    except Exception as exc:
        logger.error("All LLM providers failed for claim verification: %s", exc)
        return {
            "status": "NEUTRAL",
            "confidence": 0.0,
            "corpus_confidence": 0.0,
            "training_confidence": 0.0,
            "source": "none",
            "explanation": f"System error: All LLM verification providers failed. {str(exc)}",
            "supporting": [],
            "contradicting": [],
        }


def _normalize_analysis(data: Dict) -> Dict[str, Any]:
    """Normalize and validate the LLM analysis response."""
    status = data.get("status", "NEUTRAL").upper()
    if status not in ("SUPPORT", "CONTRADICTION", "NEUTRAL"):
        status = "NEUTRAL"

    return {
        "status": status,
        "confidence": min(1.0, max(0.0, float(data.get("confidence", 0.0)))),
        "corpus_confidence": min(1.0, max(0.0, float(data.get("corpus_confidence", 0.0)))),
        "training_confidence": min(1.0, max(0.0, float(data.get("training_confidence", 0.0)))),
        "source": data.get("source", "unknown"),
        "explanation": data.get("explanation", ""),
        "supporting": data.get("supporting", []),
        "contradicting": data.get("contradicting", []),
    }


def _format_similar_claims(claims: List[str]) -> str:
    """Format retrieved claims for the LLM prompt."""
    if not claims:
        return (
            "No similar claims found in corpus. "
            "Rely on your internal knowledge but note its unverified status."
        )
    return "\n".join(f"{i}. {claim}" for i, claim in enumerate(claims, 1))


async def _store_verification_in_graph(
    user_claim: str, analysis: Dict[str, Any]
) -> None:
    """Store the verification result as a graph relationship."""
    try:
        graph = get_graph_store()
        claim_id = f"verify_{uuid.uuid4().hex[:12]}"

        # Store the verified claim as a node
        node = ClaimNode(
            id=claim_id,
            text=user_claim,
            confidence=analysis.get("confidence", 0.0),
            node_type="verified_claim",
        )
        await graph.store_claim_node(node)

        # Map verdict to relationship type
        status = analysis.get("status", "NEUTRAL")
        rel_map = {
            "SUPPORT": "supports",
            "CONTRADICTION": "contradicts",
            "NEUTRAL": "neutral_to",
        }
        rel_type = rel_map.get(status, "neutral_to")

        # Create a corpus root node if needed and link
        corpus_node = ClaimNode(
            id="corpus_root", text="Knowledge Corpus",
            confidence=1.0, node_type="source"
        )
        await graph.store_claim_node(corpus_node)

        rel = ClaimRelationship(
            source_id=claim_id,
            target_id="corpus_root",
            rel_type=rel_type,
            confidence=analysis.get("confidence", 0.0),
            evidence=analysis.get("explanation", ""),
        )
        await graph.store_relationship(rel)

    except Exception as exc:
        logger.error("Failed to store verification in graph: %s", exc)
