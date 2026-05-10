import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.llm.llm_manager import LLMManager
from app.llm.base import ExtractionResult, VerificationResult

@pytest.fixture
def mock_settings():
    with patch("app.llm.llm_manager.get_settings") as mock:
        settings = MagicMock()
        settings.gemini_api_key = "test_key"
        settings.gemini_model = "test_model"
        settings.openrouter_api_key = "test_or_key"
        settings.openrouter_model = "test_or_model"
        settings.ollama_url = "http://test_ollama"
        settings.ollama_model = "test_ollama_model"
        settings.ollama_enabled = True
        settings.llm_timeout = 30
        settings.openrouter_configured = True
        mock.return_value = settings
        yield settings

@pytest.mark.asyncio
async def test_llm_manager_fallback_success(mock_settings):
    """Test that manager correctly falls back when primary fails."""
    
    with patch("app.llm.gemini_provider.genai.Client"), \
         patch("app.llm.openrouter_provider.AsyncOpenAI"), \
         patch("app.llm.ollama_provider.AsyncOpenAI"):
        
        manager = LLMManager()
        
        # Mock providers
        gemini = AsyncMock()
        gemini.extract_claims.side_effect = Exception("Gemini Down")
        
        openrouter = AsyncMock()
        openrouter.extract_claims.return_value = ExtractionResult(claims=[{"claim": "OR Claim", "confidence": 0.9}])
        
        # Inject mocks
        manager.providers = [gemini, openrouter]
        
        result = await manager.extract_claims("test text")
        
        assert result.claims[0].claim == "OR Claim"
        assert gemini.extract_claims.called
        assert openrouter.extract_claims.called

@pytest.mark.asyncio
async def test_llm_manager_all_fail(mock_settings):
    """Test behavior when all providers fail."""
    
    with patch("app.llm.gemini_provider.genai.Client"), \
         patch("app.llm.openrouter_provider.AsyncOpenAI"), \
         patch("app.llm.ollama_provider.AsyncOpenAI"):
        
        manager = LLMManager()
        
        p1 = AsyncMock()
        p1.extract_claims.side_effect = Exception("P1 Fail")
        p2 = AsyncMock()
        p2.extract_claims.side_effect = Exception("P2 Fail")
        
        manager.providers = [p1, p2]
        
        with pytest.raises(Exception) as exc:
            await manager.extract_claims("test text")
        
        assert "P2 Fail" in str(exc.value)
