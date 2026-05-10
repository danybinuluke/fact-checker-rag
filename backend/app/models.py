"""
Pydantic models for API request/response schemas.

All request and response types for the Fact-Checking RAG API endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Shared / Nested Models ────────────────────────────────────────────────

class ClaimModel(BaseModel):
    """A single extracted factual claim."""

    claim: str = Field(..., description="The factual claim text.")
    entities: List[str] = Field(default_factory=list, description="Key entities in the claim.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score.")
    source_doc: Optional[str] = Field(default=None, description="Source document identifier.")


class GraphNode(BaseModel):
    """A node in the knowledge graph."""

    id: str = Field(..., description="Unique node identifier.")
    label: str = Field(..., description="Display label.")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence score.")
    type: str = Field(..., description="Node type: claim | source | document.")


class GraphEdge(BaseModel):
    """An edge in the knowledge graph."""

    source: str = Field(..., description="Source node ID.")
    target: str = Field(..., description="Target node ID.")
    relationship: str = Field(..., description="Relationship type: supports | contradicts | neutral_to.")
    weight: float = Field(default=0.5, ge=0.0, le=1.0, description="Relationship strength.")


# ── Request Models ────────────────────────────────────────────────────────

class ExtractClaimsRequest(BaseModel):
    """Request body for /extract-claims."""

    text: str = Field(..., min_length=1, description="Text to extract claims from.")
    document_id: Optional[str] = Field(default=None, description="Optional document identifier.")


class VerifyClaimRequest(BaseModel):
    """Request body for /verify-claim."""

    claim: str = Field(..., min_length=1, description="The claim to verify.")
    model: Optional[str] = Field(default=None, description="Preferred LLM model (Gemini | Ollama).")


# ── Response Models ───────────────────────────────────────────────────────

class ExtractClaimsResponse(BaseModel):
    """Response body for /extract-claims."""

    status: str
    document: str
    claims: List[ClaimModel]
    claims_count: int = 0
    latency_ms: float = 0.0
    timestamp: Optional[datetime] = None

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat() if v else None}}


class VerifyClaimResponse(BaseModel):
    """Response body for /verify-claim."""

    status: str
    user_claim: str
    verification_status: str = Field(..., description="SUPPORT | CONTRADICTION | NEUTRAL")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    corpus_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    training_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str = Field(default="unknown", description="Evidence source: corpus | training | both | none")
    corpus_match_found: bool = False
    corpus_match_score: float = 0.0
    explanation: str = ""
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    response_time_ms: float = 0.0
    timestamp: Optional[datetime] = None

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat() if v else None}}


class UploadDocumentResponse(BaseModel):
    """Response body for /upload-document."""

    status: str
    filename: str
    claims_count: int
    text_preview: str
    document_id: str


class HealthResponse(BaseModel):
    """Response body for /health."""

    status: str
    primary_llm: str
    secondary_llm: Optional[str] = None
    tertiary_llm: Optional[str] = None
    available_models: List[str]
    services: Dict[str, str] = Field(default_factory=dict)


class GraphDataResponse(BaseModel):
    """Response body for /graph-data."""

    nodes: List[GraphNode]
    edges: List[GraphEdge]


class MetricsResponse(BaseModel):
    """Response body for /metrics."""

    performance: Dict[str, Any]
    models: Dict[str, Any]
    system_info: Dict[str, Any]
