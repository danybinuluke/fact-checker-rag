import logging
import json
import re
from google import genai
from google.genai import types
from app.config import get_settings
from app.llm.base import LLMProvider, ExtractionResult, VerificationResult
from app.llm.prompts import EXTRACTION_PROMPT, VERIFICATION_PROMPT

logger = logging.getLogger(__name__)

class GeminiProvider(LLMProvider):
    """Google Gemini API Provider implementation."""

    def __init__(self):
        settings = get_settings()
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_id = settings.gemini_model

    def _clean_json_response(self, text: str) -> str:
        """Remove markdown code blocks if present."""
        if "```json" in text:
            match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)
        elif "```" in text:
            match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1)
        
        # Fallback if there was no closing backtick or regex failed
        text = text.replace("```json", "").replace("```", "").strip()
        return text

    async def generate(
        self, 
        prompt: str, 
        temperature: float = 0.3, 
        max_tokens: int = 1024
    ) -> tuple[str, str]:
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            # Use self.model_id as the actual model for Gemini
            return response.text, self.model_id
        except Exception as exc:
            logger.error("Gemini generation error: %s", exc)
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
        data["provider"] = "Gemini"
        data["model"] = actual_model
        return VerificationResult(**data)
