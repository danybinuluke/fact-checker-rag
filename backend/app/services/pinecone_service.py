"""
Pinecone Service — vector database for claim storage and retrieval.

Falls back to in-memory store if PINECONE_API_KEY is not set.
"""

import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
from app.config import get_settings
from app.services import embedding_service

logger = logging.getLogger(__name__)


@dataclass
class ScoredMatch:
    """A claim matched by vector similarity."""
    id: str
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class InMemoryVectorStore:
    """Fallback vector store using sklearn cosine similarity."""

    def __init__(self) -> None:
        self._vectors: Dict[str, np.ndarray] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._texts: Dict[str, str] = {}

    def upsert(self, ids: List[str], embeddings: List[np.ndarray],
               texts: List[str], metadata_list: Optional[List[Dict]] = None) -> int:
        for i, (vid, vec, text) in enumerate(zip(ids, embeddings, texts)):
            self._vectors[vid] = vec
            self._texts[vid] = text
            self._metadata[vid] = (metadata_list[i] if metadata_list else {})
        return len(ids)

    def query(self, query_vector: np.ndarray, top_k: int = 10,
              threshold: float = 0.25) -> List[ScoredMatch]:
        if not self._vectors:
            return []
        from sklearn.metrics.pairwise import cosine_similarity
        ids = list(self._vectors.keys())
        matrix = np.array([self._vectors[vid] for vid in ids])
        sims = cosine_similarity([query_vector], matrix)[0]
        ranked = sorted(zip(ids, sims), key=lambda x: x[1], reverse=True)
        return [ScoredMatch(id=vid, text=self._texts[vid], score=float(s),
                            metadata=self._metadata.get(vid, {}))
                for vid, s in ranked[:top_k] if s >= threshold]

    def stats(self) -> Dict[str, Any]:
        return {"total_vectors": len(self._vectors), "store_type": "in-memory"}


class PineconeVectorStore:
    """Production vector store using Pinecone."""

    def __init__(self) -> None:
        self._index = None
        self._initialized = False

    def init(self) -> None:
        if self._initialized:
            return
        settings = get_settings()
        from pinecone import Pinecone, ServerlessSpec
        pc = Pinecone(api_key=settings.pinecone_api_key)
        existing = [idx.name for idx in pc.list_indexes()]
        if settings.pinecone_index_name not in existing:
            pc.create_index(name=settings.pinecone_index_name,
                            dimension=settings.embedding_dimension, metric="cosine",
                            spec=ServerlessSpec(cloud=settings.pinecone_cloud,
                                                region=settings.pinecone_region))
        self._index = pc.Index(settings.pinecone_index_name)
        self._initialized = True
        logger.info("Pinecone index '%s' connected.", settings.pinecone_index_name)

    def upsert(self, ids: List[str], embeddings: List[np.ndarray],
               texts: List[str], metadata_list: Optional[List[Dict]] = None) -> int:
        self.init()
        vectors = []
        for i, (vid, vec, text) in enumerate(zip(ids, embeddings, texts)):
            meta = metadata_list[i] if metadata_list else {}
            meta["text"] = text[:1000]
            vectors.append({"id": vid, "values": vec.tolist(), "metadata": meta})
        for i in range(0, len(vectors), 100):
            self._index.upsert(vectors=vectors[i:i+100])
        return len(vectors)

    def query(self, query_vector: np.ndarray, top_k: int = 10,
              threshold: float = 0.25) -> List[ScoredMatch]:
        self.init()
        results = self._index.query(vector=query_vector.tolist(), top_k=top_k,
                                     include_metadata=True)
        return [ScoredMatch(id=m["id"], text=m.get("metadata", {}).get("text", ""),
                            score=m.get("score", 0.0), metadata=m.get("metadata", {}))
                for m in results.get("matches", []) if m.get("score", 0) >= threshold]

    def stats(self) -> Dict[str, Any]:
        self.init()
        desc = self._index.describe_index_stats()
        return {"total_vectors": desc.get("total_vector_count", 0),
                "store_type": "pinecone"}


_store = None

def get_vector_store():
    """Get the active vector store (Pinecone or in-memory fallback)."""
    global _store
    if _store is not None:
        return _store
    settings = get_settings()
    if settings.pinecone_configured:
        logger.info("Using Pinecone vector store.")
        _store = PineconeVectorStore()
        _store.init()
    else:
        logger.info("Pinecone not configured — using in-memory vector store.")
        _store = InMemoryVectorStore()
    return _store


class CorpusManager:
    """Manages document corpus: chunking, embedding, and vector storage."""

    def __init__(self) -> None:
        self._chunk_count: int = 0

    def add_to_corpus(self, text: str) -> int:
        """Chunk text, embed, and store in vector DB. Returns chunks added."""
        if not text or not text.strip():
            return 0
        chunks = self._chunk_text(text)
        if not chunks:
            return 0
        embeddings = embedding_service.encode_batch(chunks)
        ids = [f"chunk_{self._chunk_count + i}" for i in range(len(chunks))]
        metadata = [{"source": "uploaded_document", "chunk_index": self._chunk_count + i}
                     for i in range(len(chunks))]
        store = get_vector_store()
        count = store.upsert(ids, embeddings, chunks, metadata)
        self._chunk_count += count
        logger.info("Added %d chunks to corpus. Total: %d", count, self._chunk_count)
        return count

    def query_similar(self, text: str, top_k: int = 10,
                      threshold: float = 0.25) -> List[ScoredMatch]:
        """Query corpus for similar claims."""
        query_embedding = embedding_service.encode(text)
        store = get_vector_store()
        return store.query(query_embedding, top_k=top_k, threshold=threshold)

    def get_stats(self) -> Dict[str, Any]:
        store = get_vector_store()
        stats = store.stats()
        stats["chunks_added"] = self._chunk_count
        return stats

    @staticmethod
    def _chunk_text(text: str, max_size: int = 800, min_size: int = 30) -> List[str]:
        """Split text into paragraph/sentence chunks."""
        raw = re.split(r"\n\s*\n", text)
        chunks: List[str] = []
        for chunk in raw:
            chunk = chunk.strip()
            if not chunk:
                continue
            if len(chunk) > max_size:
                sentences = re.split(r"(?<=[.!?])\s+", chunk)
                temp = ""
                for s in sentences:
                    if len(temp) + len(s) < max_size:
                        temp += " " + s
                    else:
                        if len(temp.strip()) >= min_size:
                            chunks.append(temp.strip())
                        temp = s
                if len(temp.strip()) >= min_size:
                    chunks.append(temp.strip())
            elif len(chunk) >= min_size:
                chunks.append(chunk)
        return chunks


corpus_manager = CorpusManager()
