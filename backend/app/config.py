"""
Application configuration using pydantic-settings.

Loads all settings from environment variables and .env file.
Provides a single cached Settings instance via get_settings().
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Central configuration for the Fact-Checking RAG system.

    All values can be overridden via environment variables or .env file.
    """

    # ── LLM: Gemini (Primary) ──────────────────────────────────────────
    gemini_api_key: str = Field(
        ...,
        description="Google Gemini API key. Required for production.",
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model identifier.",
    )

    # ── LLM: Ollama (Fallback — development only) ─────────────────────
    ollama_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL.",
    )
    ollama_model: str = Field(
        default="qwen3:8b",
        description="Ollama model to use as fallback.",
    )
    ollama_enabled: bool = Field(
        default=False,
        description="Enable Ollama fallback. Must be False in production.",
    )

    # ── Pinecone (Vector DB) ───────────────────────────────────────────
    pinecone_api_key: str = Field(
        default="",
        description="Pinecone API key. If empty, falls back to in-memory vector store.",
    )
    pinecone_index_name: str = Field(
        default="fact-checker-claims",
        description="Name of the Pinecone index.",
    )
    pinecone_cloud: str = Field(
        default="aws",
        description="Pinecone cloud provider.",
    )
    pinecone_region: str = Field(
        default="us-east-1",
        description="Pinecone deployment region.",
    )

    # ── Neo4j (Graph DB) ──────────────────────────────────────────────
    neo4j_uri: str = Field(
        default="",
        description="Neo4j Aura connection URI. If empty, falls back to in-memory graph.",
    )
    neo4j_user: str = Field(
        default="neo4j",
        description="Neo4j username.",
    )
    neo4j_password: str = Field(
        default="",
        description="Neo4j password.",
    )

    # ── Application ───────────────────────────────────────────────────
    environment: str = Field(
        default="development",
        description="Runtime environment: development | production",
    )
    port: int = Field(
        default=8000,
        description="Server port.",
    )
    log_level: str = Field(
        default="info",
        description="Logging level.",
    )

    # ── Embedding ─────────────────────────────────────────────────────
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence-transformers model name for embeddings.",
    )
    embedding_dimension: int = Field(
        default=384,
        description="Dimensionality of the embedding vectors.",
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"

    @property
    def pinecone_configured(self) -> bool:
        """Check if Pinecone credentials are provided."""
        return bool(self.pinecone_api_key)

    @property
    def neo4j_configured(self) -> bool:
        """Check if Neo4j credentials are provided."""
        return bool(self.neo4j_uri and self.neo4j_password)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    The instance is created once and reused across the application lifetime.
    """
    return Settings()


# ── Prompt Templates ──────────────────────────────────────────────────────

EXTRACTION_PROMPT = """You are a fact-extraction expert.

From the given text, extract exactly 5-10 KEY FACTUAL CLAIMS.

For EACH claim:
1. State the claim clearly (under 20 words)
2. List key entities (people, places, dates, numbers)
3. Rate your confidence this is factual (0.0-1.0)

IMPORTANT: Return ONLY valid JSON with no markdown or extra text.

Format:
{{
  "claims": [
    {{
      "claim": "...",
      "entities": [...],
      "confidence": 0.95
    }}
  ]
}}

Text:
{text}

JSON:"""


VERIFICATION_PROMPT = """You are a Hybrid Fact-Checking Agent. Your mission is to verify a claim by comparing your internal knowledge against the provided User Documents.

User Claim: "{user_claim}"

=== SOURCE 1: USER DOCUMENTS (Corpus) ===
{similar_claims_text}

=== SOURCE 2: YOUR INTERNAL KNOWLEDGE ===
(Use your own training data)

=== INSTRUCTIONS ===
1. **Be Decisive**: If you know a claim is true or false from your training knowledge, give a status of SUPPORT or CONTRADICTION. Do NOT default to NEUTRAL just because the documents are silent.
2. **Identify Corroboration**:
   - If BOTH agree: Status is SUPPORT, Source is "both" (Corroborated).
   - If only YOU know it: Status is SUPPORT/CONTRADICTION, Source is "training" (Unverified by docs).
   - If only DOCS know it: Status is SUPPORT/CONTRADICTION, Source is "corpus" (External evidence).
   - If they DISAGREE: Status is CONTRADICTION, Source is "both" (Conflict detected).

=== OUTPUT (JSON) ===
Return EXACTLY this JSON structure:
{{
  "status": "SUPPORT|CONTRADICTION|NEUTRAL",
  "confidence": 0.0,
  "corpus_confidence": 0.0,
  "training_confidence": 0.0,
  "source": "both|corpus|training",
  "explanation": "Clearly state what you know vs what the documents say.",
  "supporting": ["Quotes from docs OR facts from your knowledge"],
  "contradicting": ["Conflicting quotes or facts"]
}}

JSON:"""
