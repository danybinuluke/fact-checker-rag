"""
Fact-Checking RAG System — FastAPI Application Entry Point.

Production-grade fact-checking and contradiction detection platform
powered by Google Gemini (primary) with Ollama Qwen3 8B fallback.

Architecture:
    Gemini API (primary LLM)
    └→ Ollama Qwen3 8B (fallback, dev only)
    Sentence-Transformers (embeddings)
    Pinecone (vector DB, or in-memory fallback)
    Neo4j Aura (graph DB, or in-memory fallback)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import claims, graph, system, verification
from app.services.llm_service import init_gemini
from app.services.neo4j_service import get_graph_store
from app.services.embedding_service import preload_model

# ── Logging ───────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Startup:
        - Load settings and validate configuration
        - Initialize Gemini SDK
        - Log service availability

    Shutdown:
        - Close Neo4j driver (if connected)
    """
    settings = get_settings()
    logger.info("Starting Fact-Checking RAG System v2.0")
    logger.info("Environment: %s", settings.environment)
    logger.info("Primary LLM: Gemini (%s)", settings.gemini_model)

    # Initialize Gemini
    try:
        init_gemini()
        logger.info("✓ Gemini SDK initialized.")
    except Exception as exc:
        logger.error("✗ Gemini initialization failed: %s", exc)

    # Log Pinecone status
    if settings.pinecone_configured:
        logger.info("✓ Pinecone configured (index: %s)", settings.pinecone_index_name)
    else:
        logger.info("⚠ Pinecone not configured — using in-memory vector store.")

    # Log Neo4j status
    if settings.neo4j_configured:
        logger.info("✓ Neo4j configured (%s)", settings.neo4j_uri)
    else:
        logger.info("⚠ Neo4j not configured — using in-memory graph store.")

    # Log OpenRouter status
    if settings.openrouter_configured:
        logger.info("✓ OpenRouter fallback enabled (model: %s)", settings.openrouter_model)
    else:
        logger.info("⚠ OpenRouter fallback disabled (API key missing).")

    # Log Ollama status
    if settings.ollama_enabled and not settings.is_production:
        logger.info("✓ Ollama fallback enabled (model: %s)", settings.ollama_model)
    else:
        logger.info("⚠ Ollama fallback disabled.")

    # Preload embedding model (essential for production startup)
    try:
        preload_model()
    except Exception as exc:
        logger.error("✗ Embedding model preloading failed: %s", exc)

    yield

    # Shutdown: close Neo4j
    try:
        graph = get_graph_store()
        await graph.close()
    except Exception:
        pass

    logger.info("Fact-Checking RAG System shut down.")


# ── FastAPI App ───────────────────────────────────────────────────────────

app = FastAPI(
    title="Fact-Checking RAG API",
    description=(
        "Production-grade fact-checking and contradiction detection platform. "
        "Extracts claims from documents, generates embeddings for semantic retrieval, "
        "detects SUPPORT/CONTRADICTION/NEUTRAL relationships, and stores them in a "
        "knowledge graph."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fact-checker-dbl.vercel.app",
        "https://fact-checker-rag-frontend.vercel.app",  # Common alternative
        "http://localhost:3000",                        # Local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(system.router)
app.include_router(claims.router)
app.include_router(verification.router)
app.include_router(graph.router)


# ── Development Entry Point ──────────────────────────────────────────────

if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )
