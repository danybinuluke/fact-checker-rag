"""
LLM Service — Legacy wrapper for the new LLM architecture.
Now delegates all work to app.llm.llm_manager.
"""

import logging
import json
from typing import Any, Dict, Optional
import asyncio

from app.config import get_settings
from app.llm import get_llm_manager

logger = logging.getLogger(__name__)
def is_ollama_available() -> bool:
    """
    Legacy helper to check if Ollama is enabled and reachable.
    Used by the system router for health reporting.
    """
    settings = get_settings()
    if not settings.ollama_enabled or settings.is_production:
        return False
    
    import requests
    try:
        resp = requests.get(settings.ollama_url, timeout=2)
        return resp.status_code == 200
    except Exception:
        return False

def init_gemini() -> None:
    """
    Legacy helper to initialize Gemini.
    Now simply ensures the LLMManager is ready.
    """
    get_llm_manager()
    logger.info("Modular LLM manager initialized via legacy init_gemini.")

class LLMServiceError(Exception):
    """Raised when all LLM providers fail."""
    pass

def generate_content(
    prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 1024,
    preferred_model: Optional[str] = None,
) -> str:
    """
    Legacy synchronous wrapper for generate_content.
    Warning: This uses asyncio.run() and should be avoided in async contexts.
    """
    manager = get_llm_manager()
    try:
        # Note: In a production environment, you should use the async manager directly.
        # This wrapper exists only for backward compatibility during the refactor.
        text, _ = asyncio.run(manager.generate(prompt, temperature=temperature, max_tokens=max_tokens))
        return text
    except Exception as exc:
        logger.error("Legacy generate_content failed: %s", exc)
        raise LLMServiceError(str(exc))

def parse_json_response(text: str) -> Optional[Dict]:
    """
    Parse a JSON object from an LLM response.
    Delegates to a internal helper to maintain compatibility.
    """
    if not text:
        return None

    try:
        # Strip markdown code fences
        cleaned = text
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}") + 1

        if start_idx == -1 or end_idx <= start_idx:
            return json.loads(cleaned) # Try direct parse

        return json.loads(cleaned[start_idx:end_idx])

    except (json.JSONDecodeError, IndexError, ValueError) as exc:
        logger.warning("Failed to parse JSON from LLM response: %s", exc)
        return None
