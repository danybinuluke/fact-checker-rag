import logging
from typing import List, Optional, Any, Callable
from app.config import get_settings
from app.llm.base import LLMProvider, ExtractionResult, VerificationResult
from app.llm.gemini_provider import GeminiProvider
from app.llm.openrouter_provider import OpenRouterProvider
from app.llm.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)

class LLMManager:
    """
    Orchestrator for LLM providers.
    Implements the fallback chain: Gemini -> OpenRouter -> Ollama.
    """

    def __init__(self):
        self.settings = get_settings()
        self.providers: List[LLMProvider] = []
        
        # Initialize providers based on configuration
        # 1. Gemini (Primary)
        try:
            self.providers.append(GeminiProvider())
        except Exception as e:
            logger.warning("Failed to initialize Gemini provider: %s", e)

        # 2. OpenRouter (Secondary)
        if self.settings.openrouter_configured:
            try:
                self.providers.append(OpenRouterProvider())
            except Exception as e:
                logger.warning("Failed to initialize OpenRouter provider: %s", e)

        # 3. Ollama (Tertiary)
        if self.settings.ollama_enabled:
            try:
                self.providers.append(OllamaProvider())
            except Exception as e:
                logger.warning("Failed to initialize Ollama provider: %s", e)

    async def _execute_with_fallback(
        self, 
        func: Callable[[LLMProvider], Any],
        preferred_provider: Optional[str] = None
    ) -> Any:
        """
        Execute a provider method with sequential fallback.
        If preferred_provider is specified, starts the chain from that provider.
        """
        last_exception = None
        
        # Determine the starting point
        start_index = 0
        if preferred_provider:
            for i, p in enumerate(self.providers):
                if preferred_provider.lower() in p.__class__.__name__.lower():
                    start_index = i
                    break
        
        for i in range(start_index, len(self.providers)):
            provider = self.providers[i]
            provider_name = provider.__class__.__name__
            try:
                logger.info("Attempting request with %s...", provider_name)
                return await func(provider)
            except Exception as e:
                logger.warning("%s failed: %s. Trying next provider...", provider_name, e)
                last_exception = e
                continue
        
        logger.error("All LLM providers in the chain failed.")
        raise last_exception or Exception("No LLM providers available.")

    async def extract_claims(self, text: str, provider: Optional[str] = None) -> ExtractionResult:
        """Extract claims using the fallback chain."""
        return await self._execute_with_fallback(
            lambda p: p.extract_claims(text),
            preferred_provider=provider
        )

    async def verify_claim(self, claim: str, context_docs: str, provider: Optional[str] = None) -> VerificationResult:
        """Verify claim using the fallback chain."""
        return await self._execute_with_fallback(
            lambda p: p.verify_claim(claim, context_docs),
            preferred_provider=provider
        )

    async def generate(self, prompt: str, provider: Optional[str] = None, **kwargs) -> tuple[str, str]:
        """Raw generation using the fallback chain. Returns (text, model_id)."""
        return await self._execute_with_fallback(
            lambda p: p.generate(prompt, **kwargs),
            preferred_provider=provider
        )

# Global singleton instance
_manager: Optional[LLMManager] = None

def get_llm_manager() -> LLMManager:
    """Return the global LLMManager instance."""
    global _manager
    if _manager is None:
        _manager = LLMManager()
    return _manager
