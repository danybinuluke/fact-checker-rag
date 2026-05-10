import logging
import json
import re
from openai import AsyncOpenAI
from app.config import get_settings
from app.llm.base import LLMProvider, ExtractionResult, VerificationResult
from app.llm.prompts import EXTRACTION_PROMPT, VERIFICATION_PROMPT

logger = logging.getLogger(__name__)

class OpenRouterProvider(LLMProvider):
    """OpenRouter API Provider implementation using OpenAI SDK."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
            max_retries=0, # Disable SDK retries to allow instant fallback to other models
        )
        self.model_id = settings.openrouter_model
        self.timeout = settings.llm_timeout
        self._cached_free_models = []

    async def _get_free_models(self) -> list[str]:
        """Fetch currently available free models from OpenRouter."""
        if self._cached_free_models:
            return self._cached_free_models

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://openrouter.ai/api/v1/models")
                if resp.status_code == 200:
                    data = resp.json()
                    # Filter for models where all pricing components are 0
                    free_models = [
                        m["id"] for m in data.get("data", [])
                        if float(m.get("pricing", {}).get("prompt", 1)) == 0 
                        and float(m.get("pricing", {}).get("completion", 1)) == 0
                    ]
                    # Prioritize Gemini and Llama if available
                    free_models.sort(key=lambda x: ("gemini" in x.lower() or "llama" in x.lower()), reverse=True)
                    self._cached_free_models = free_models
                    return free_models
        except Exception as e:
            logger.warning("Failed to fetch free models from OpenRouter: %s", e)
        
        return []

    def _clean_json_response(self, text: str) -> str:
        """Remove markdown code blocks if present."""
        if "```json" in text:
            text = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL).group(1)
        elif "```" in text:
            text = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL).group(1)
        return text.strip()

    async def generate(
        self, 
        prompt: str, 
        temperature: float = 0.3, 
        max_tokens: int = 1024
    ) -> tuple[str, str]:
        # If 'auto' or 'free' is specified, discover models dynamically
        if self.model_id.lower() in ("auto", "free", "auto-free"):
            models = await self._get_free_models()
            if not models:
                # Fallback to some common ones if discovery fails
                models = ["google/gemini-flash-1.5-8b:free", "meta-llama/llama-3-8b-instruct:free"]
        else:
            models = [m.strip() for m in self.model_id.split(",") if m.strip()]

        last_exc = None
        for model in models:
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=self.timeout
                )
                return response.choices[0].message.content, response.model
            except Exception as exc:
                logger.warning("OpenRouter attempt failed for model %s: %s", model, exc)
                last_exc = exc
                continue
        
        logger.error("All OpenRouter models failed.")
        raise last_exc or Exception("OpenRouter generation failed")

    async def extract_claims(self, text: str) -> ExtractionResult:
        prompt = EXTRACTION_PROMPT.format(text=text)
        raw_response, _ = await self.generate(prompt, temperature=0.2)
        cleaned = self._clean_json_response(raw_response)
        data = json.loads(cleaned)
        return ExtractionResult(**data)

    async def verify_claim(self, claim: str, context_docs: str) -> VerificationResult:
        prompt = VERIFICATION_PROMPT.format(
            user_claim=claim, 
            similar_claims_text=context_docs
        )
        raw_response, actual_model = await self.generate(prompt, temperature=0.1, max_tokens=2048)
        cleaned = self._clean_json_response(raw_response)
        data = json.loads(cleaned)
        data["provider"] = "OpenRouter"
        data["model"] = actual_model
        return VerificationResult(**data)
