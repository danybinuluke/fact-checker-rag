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


    gemini_api_key: str = Field(
        ...,
        description="Google Gemini API key. Required for production.",
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model identifier.",
    )


    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter API key.",
    )
    openrouter_model: str = Field(
        default="deepseek/deepseek-chat-v3:free",
        description="OpenRouter model identifier.",
    )


    ollama_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL.",
    )
    ollama_model: str = Field(
        default="qwen3:8b",
        description="Ollama model identifier.",
    )
    ollama_enabled: bool = Field(
        default=False,
        description="Enable Ollama fallback.",
    )


    llm_timeout: int = Field(
        default=30,
        description="Global timeout for LLM requests in seconds.",
    )


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

    embedding_model: str = Field(
        default="gemini-embedding-2",
        description="Model name for embeddings.",
    )
    embedding_dimension: int = Field(
        default=384,
        description="Dimensionality of the embedding vectors.",
    )

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def pinecone_configured(self) -> bool:
        return bool(self.pinecone_api_key)

    @property
    def neo4j_configured(self) -> bool:
        return bool(self.neo4j_uri and self.neo4j_password)

    @property
    def openrouter_configured(self) -> bool:
        return bool(self.openrouter_api_key)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()

