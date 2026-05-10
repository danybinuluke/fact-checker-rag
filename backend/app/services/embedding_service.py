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

# ── Module-level state ────────────────────────────────────────────────────

_model = None


def _load_model():
    """
    Lazily load the sentence-transformers model.

    Loads on first call and caches globally. This avoids the ~2s startup
    cost if embeddings are never needed during a particular request.
    """
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        settings = get_settings()
        logger.info("Loading embedding model: %s (one-time initialization)...", settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded successfully.")
    return _model


def encode(text: str) -> np.ndarray:
    """
    Encode a single text string into a dense vector.

    Args:
        text: The input text to embed.

    Returns:
        A numpy array of shape (embedding_dimension,).
    """
    model = _load_model()
    return model.encode(text, convert_to_tensor=False)


def encode_batch(texts: List[str]) -> np.ndarray:
    """
    Encode multiple text strings into dense vectors.

    Args:
        texts: List of input texts.

    Returns:
        A numpy array of shape (len(texts), embedding_dimension).
    """
    if not texts:
        return np.array([])

    model = _load_model()
    return model.encode(texts, convert_to_tensor=False, show_progress_bar=False)


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
