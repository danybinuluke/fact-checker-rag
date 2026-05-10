"""
LLM Service — Gemini (primary) with Ollama (fallback).

Provides a unified interface for LLM inference. Gemini is ALWAYS tried first.
Ollama is ONLY used when:
  1. Gemini fails with an exception
  2. ollama_enabled is True in settings
  3. The environment is 'development'

In production, Ollama is never invoked.

Uses the modern google.genai SDK (replaces deprecated google.generativeai).
"""

import json
import logging
from typing import Any, Dict, Optional

from google import genai
from google.genai import types

from app.config import get_settings

logger = logging.getLogger(__name__)

# ── Module-level state ────────────────────────────────────────────────────

_gemini_client: Optional[genai.Client] = None
_ollama_client: Optional[Any] = None
_ollama_checked: bool = False
_ollama_available: bool = False


class LLMServiceError(Exception):
    """Raised when both Gemini and Ollama fail to produce a response."""
    pass


# ── Initialization ────────────────────────────────────────────────────────

def init_gemini() -> None:
    """
    Configure the Gemini client using the new google.genai SDK.

    Called once during application startup.
    """
    global _gemini_client
    settings = get_settings()
    _gemini_client = genai.Client(api_key=settings.gemini_api_key)
    logger.info("Gemini configured with model: %s", settings.gemini_model)


def _init_ollama_client() -> None:
    """
    Lazily initialize the Ollama OpenAI-compatible client.

    Only called when fallback is actually needed.
    """
    global _ollama_client, _ollama_checked, _ollama_available
    if _ollama_checked:
        return

    settings = get_settings()
    _ollama_checked = True

    if not settings.ollama_enabled:
        logger.info("Ollama fallback is disabled.")
        _ollama_available = False
        return

    if settings.is_production:
        logger.warning("Ollama fallback disabled in production environment.")
        _ollama_available = False
        return

    try:
        from openai import OpenAI
        import requests

        _ollama_client = OpenAI(
            base_url=f"{settings.ollama_url}/v1",
            api_key="ollama",
        )
        # Quick connectivity check
        resp = requests.get(settings.ollama_url, timeout=2)
        if resp.status_code == 200:
            _ollama_available = True
            logger.info("Ollama fallback available at %s", settings.ollama_url)
        else:
            _ollama_available = False
            logger.warning("Ollama server returned status %d", resp.status_code)
    except Exception as exc:
        _ollama_available = False
        logger.warning("Ollama not available: %s", exc)


def is_ollama_available() -> bool:
    """
    Check whether the Ollama fallback is available.

    Performs a lazy initialization check on first call.
    """
    if not _ollama_checked:
        _init_ollama_client()
    return _ollama_available


# ── Core Generation ───────────────────────────────────────────────────────


def _extract_gemini_text(response) -> str:
    """
    Extract text content from a Gemini response.

    Gemini 2.5 Flash is a thinking model — response.text may be None
    when the model uses internal reasoning. In that case, we iterate
    over the candidate parts and concatenate non-thought text parts.

    Args:
        response: The GenerateContentResponse from the genai SDK.

    Returns:
        The concatenated text content.
    """
    # Try the simple accessor first
    if response.text is not None:
        return response.text.strip()

    # Fallback: extract from candidates, skipping thought parts
    text_parts = []
    if response.candidates:
        for candidate in response.candidates:
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.text and not getattr(part, "thought", False):
                        text_parts.append(part.text)

    result = "".join(text_parts).strip()
    if not result:
        logger.warning("Gemini response contained no extractable text.")
    return result

def generate_with_gemini(
    prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str:
    """
    Generate content using Google Gemini via the new google.genai SDK.

    Args:
        prompt: The input prompt.
        temperature: Sampling temperature (0.0–1.0).
        max_tokens: Maximum output tokens.

    Returns:
        The raw text response from Gemini.

    Raises:
        Exception: On any Gemini API error.
    """
    global _gemini_client
    if _gemini_client is None:
        init_gemini()

    settings = get_settings()
    response = _gemini_client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            top_p=0.8,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        ),
    )
    return _extract_gemini_text(response)


def generate_with_ollama(
    prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> Optional[str]:
    """
    Generate content using Ollama (fallback).

    Only invoked when Gemini fails and Ollama is available.

    Args:
        prompt: The input prompt.
        temperature: Sampling temperature.
        max_tokens: Maximum output tokens.

    Returns:
        The raw text response, or None if Ollama is unavailable.
    """
    if not is_ollama_available() or _ollama_client is None:
        return None

    settings = get_settings()
    response = _ollama_client.chat.completions.create(
        model=settings.ollama_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=300,
    )
    return response.choices[0].message.content.strip()


def generate_content(
    prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str:
    """
    Unified LLM generation with automatic fallback.

    1. Try Gemini (primary).
    2. If Gemini fails AND Ollama is enabled in development → try Ollama.
    3. If both fail → raise LLMServiceError.

    Args:
        prompt: The input prompt.
        temperature: Sampling temperature.
        max_tokens: Maximum output tokens.

    Returns:
        The raw text response from whichever model succeeds.

    Raises:
        LLMServiceError: When all models fail.
    """
    # Step 1: Try Gemini (always primary)
    try:
        result = generate_with_gemini(prompt, temperature, max_tokens)
        if result:
            return result
    except Exception as exc:
        logger.error("Gemini generation failed: %s", exc)

    # Step 2: Try Ollama fallback (development only)
    settings = get_settings()
    if settings.ollama_enabled and not settings.is_production:
        logger.info("Falling back to Ollama...")
        try:
            result = generate_with_ollama(prompt, temperature, max_tokens)
            if result:
                return result
        except Exception as exc:
            logger.error("Ollama generation also failed: %s", exc)

    raise LLMServiceError(
        "All LLM providers failed. Check Gemini API key and connectivity."
    )


# ── Response Parsing ──────────────────────────────────────────────────────

def parse_json_response(text: str) -> Optional[Dict]:
    """
    Parse a JSON object from an LLM response, handling markdown wrapping.

    Args:
        text: Raw LLM response text.

    Returns:
        Parsed dict, or None if parsing fails.
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

        # Extract JSON object boundaries
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}") + 1

        if start_idx == -1 or end_idx <= start_idx:
            return None

        return json.loads(cleaned[start_idx:end_idx])

    except (json.JSONDecodeError, IndexError) as exc:
        logger.warning("Failed to parse JSON from LLM response: %s", exc)
        return None
