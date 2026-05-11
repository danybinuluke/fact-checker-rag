"""
Embedding Service — sentence-transformers all-MiniLM-L6-v2.

Provides lazy-loaded embedding generation for claims and queries.
The model is loaded once on first use and cached for the application lifetime.
"""

import logging
from typing import List, Optional

import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)

# ── Gemini Client Setup ───────────────────────────────────────────────────

_client = None


def _get_client():
    """Lazily initialize the Gemini client."""
    global _client
    if _client is None:
        from google import genai
        settings = get_settings()
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def encode(text: str) -> np.ndarray:
    """
    Encode a single text string into a dense vector using Gemini API.

    Args:
        text: The input text to embed.

    Returns:
        A numpy array of shape (embedding_dimension,).
    """
    from google.genai import types
    settings = get_settings()
    client = _get_client()
    
    result = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=settings.embedding_dimension)
    )
    return np.array(result.embeddings[0].values)


def encode_batch(texts: List[str]) -> np.ndarray:
    """
    Encode multiple text strings into dense vectors using Gemini API.

    Args:
        texts: List of input texts.

    Returns:
        A numpy array of shape (len(texts), embedding_dimension).
    """
    if not texts:
        return np.array([])

    import concurrent.futures
    from google.genai import types
    settings = get_settings()
    client = _get_client()
    config = types.EmbedContentConfig(output_dimensionality=settings.embedding_dimension)
    
    def _embed_single(t: str):
        res = client.models.embed_content(
            model="gemini-embedding-2", 
            contents=t, 
            config=config
        )
        return res.embeddings[0].values

    # Process chunks concurrently since this is I/O bound
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        embeddings = list(executor.map(_embed_single, texts))

    return np.array(embeddings)


def cosine_similarity_score(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        vec_a: First vector.
        vec_b: Second vector.

    Returns:
        Cosine similarity score in [-1, 1].
    """
    dot = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))
