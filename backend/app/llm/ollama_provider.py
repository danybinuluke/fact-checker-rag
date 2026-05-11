import logging
import json
import re
from openai import AsyncOpenAI
from app.config import get_settings
from app.llm.base import LLMProvider, ExtractionResult, VerificationResult
from app.llm.prompts import EXTRACTION_PROMPT, VERIFICATION_PROMPT

logger = logging.getLogger(__name__)

class OllamaProvider(LLMProvider):
    """Ollama Local Provider implementation using OpenAI-compatible SDK."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            base_url=f"{settings.ollama_url}/v1",
            api_key="ollama", # Placeholder for local
        )
        self.model_id = settings.ollama_model
        self.timeout = settings.llm_timeout

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
        try:
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout
            )
            return response.choices[0].message.content, response.model
        except Exception as exc:
            logger.error("Ollama generation error: %s", exc)
            raise

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
        data["provider"] = "Ollama"
        data["model"] = actual_model
        return VerificationResult(**data)

def is_ollama_available() -> bool:
    settings = get_settings()
    if not settings.ollama_enabled or settings.is_production:
        return False
    
    import requests
    try:
        resp = requests.get(settings.ollama_url, timeout=2)
        return resp.status_code == 200
    except Exception:
        return False
