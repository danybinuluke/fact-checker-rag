from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ExtractionClaim(BaseModel):
    """Normalized factual claim extracted from text."""
    claim: str
    entities: List[str] = Field(default_factory=list)
    confidence: float

class ExtractionResult(BaseModel):
    """Container for multiple extracted claims."""
    claims: List[ExtractionClaim]

class VerificationResult(BaseModel):
    """Normalized verification response."""
    status: str  # SUPPORT | CONTRADICTION | NEUTRAL
    confidence: float
    corpus_confidence: float
    training_confidence: float
    source: str  # both | corpus | training
    explanation: str
    supporting: List[str] = Field(default_factory=list)
    contradicting: List[str] = Field(default_factory=list)
    provider: Optional[str] = None
    model: Optional[str] = None

class LLMProvider(ABC):
    """
    Abstract Base Class for LLM providers.
    Ensures consistent interface across Gemini, OpenRouter, and Ollama.
    """

    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        temperature: float = 0.3, 
        max_tokens: int = 1024
    ) -> tuple[str, str]:
        """Raw text generation. Returns (text, model_id)."""
        pass

    @abstractmethod
    async def extract_claims(self, text: str) -> ExtractionResult:
        """Extract structured claims from text."""
        pass

    @abstractmethod
    async def verify_claim(
        self, 
        claim: str, 
        context_docs: str
    ) -> VerificationResult:
        """Verify a claim against context and internal knowledge."""
        pass
