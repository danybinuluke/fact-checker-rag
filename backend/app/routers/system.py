"""
System Router — health check and metrics endpoints.

GET /health  → System health and service connectivity
GET /metrics → Performance metrics and system information
"""

import logging
import os
import sys
import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models import HealthResponse, MetricsResponse
from app.services.llm_service import is_ollama_available
from app.services.neo4j_service import get_graph_store
from app.services.pinecone_service import corpus_manager, get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(tags=["System"])

# ── Tracked Metrics ───────────────────────────────────────────────────────

_metrics: Dict[str, Any] = {
    "requests_total": 0,
    "extraction_count": 0,
    "verification_count": 0,
    "errors_total": 0,
    "latencies_ms": [],
    "start_time": time.time(),
}


def record_request(endpoint: str, latency_ms: float = 0.0) -> None:
    """Record a request for metrics tracking."""
    _metrics["requests_total"] += 1
    if endpoint == "extract":
        _metrics["extraction_count"] += 1
    elif endpoint == "verify":
        _metrics["verification_count"] += 1
    if latency_ms > 0:
        _metrics["latencies_ms"].append(latency_ms)
        # Keep only last 1000 latencies to bound memory
        if len(_metrics["latencies_ms"]) > 1000:
            _metrics["latencies_ms"] = _metrics["latencies_ms"][-1000:]


def record_error() -> None:
    """Record an error for metrics tracking."""
    _metrics["errors_total"] += 1


# ── Endpoints ─────────────────────────────────────────────────────────────


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    System health check.

    Reports primary/fallback LLM status and service connectivity
    for Pinecone and Neo4j.
    """
    settings = get_settings()
    available_models = ["gemini"]
    services: Dict[str, str] = {}

    # Check OpenRouter availability (Secondary)
    if settings.openrouter_configured:
        available_models.append("openrouter")
        services["openrouter"] = "available"

    # Check Ollama availability (Tertiary)
    if settings.ollama_enabled and not settings.is_production:
        if is_ollama_available():
            available_models.append("ollama")
            services["ollama"] = "available"
        else:
            services["ollama"] = "unavailable"

    # Check vector store
    try:
        store = get_vector_store()
        stats = store.stats()
        services["vector_store"] = f"{stats['store_type']} ({stats['total_vectors']} vectors)"
    except Exception:
        services["vector_store"] = "error"

    # Check graph store
    try:
        graph = get_graph_store()
        stats = graph.stats()
        services["graph_store"] = stats["store_type"]
    except Exception:
        services["graph_store"] = "error"

    return HealthResponse(
        status="healthy",
        primary_llm="gemini",
        secondary_llm="openrouter" if settings.openrouter_configured else "disabled",
        tertiary_llm="ollama" if settings.ollama_enabled else "disabled",
        available_models=available_models,
        services=services,
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """
    Performance metrics and system information.

    Reports request counts, latency statistics, model info, and
    runtime environment details.
    """
    settings = get_settings()

    # Calculate latency stats
    latencies = _metrics["latencies_ms"]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    p95_latency = (
        sorted(latencies)[int(len(latencies) * 0.95)]
        if len(latencies) >= 20
        else avg_latency
    )

    # Uptime
    uptime_s = time.time() - _metrics["start_time"]

    # Corpus stats
    corpus_stats = corpus_manager.get_stats()

    return MetricsResponse(
        performance={
            "total_requests": _metrics["requests_total"],
            "extraction_count": _metrics["extraction_count"],
            "verification_count": _metrics["verification_count"],
            "errors_total": _metrics["errors_total"],
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": round(p95_latency, 2),
            "uptime_seconds": round(uptime_s, 1),
            "corpus_vectors": corpus_stats.get("total_vectors", 0),
        },
        models={
            "primary": f"Gemini ({settings.gemini_model})",
            "secondary": f"OpenRouter ({settings.openrouter_model})" if settings.openrouter_configured else "disabled",
            "tertiary": f"Ollama ({settings.ollama_model})" if settings.ollama_enabled else "disabled",
            "ollama_available": is_ollama_available() if settings.ollama_enabled else False,
            "embedding_model": settings.embedding_model,
        },
        system_info={
            "environment": settings.environment,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "vector_store": corpus_stats.get("store_type", "unknown"),
            "graph_store": get_graph_store().stats().get("store_type", "unknown"),
        },
    )
