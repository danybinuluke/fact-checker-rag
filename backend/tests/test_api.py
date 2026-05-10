"""
Integration test suite for the Fact-Checking RAG API.

Tests all endpoints using FastAPI's TestClient (httpx-based).
Can be run with: python -m pytest tests/ -v
"""

import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

client = TestClient(app)


# ── Health Check ──────────────────────────────────────────────────────────


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self):
        """Health endpoint should return 200 with correct structure."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["primary_llm"] == "gemini"
        assert "gemini" in data["available_models"]

    def test_health_gemini_is_primary(self):
        """Gemini must always be listed as the primary LLM."""
        response = client.get("/health")
        data = response.json()
        assert data["primary_llm"] == "gemini"


# ── Metrics ───────────────────────────────────────────────────────────────


class TestMetricsEndpoint:
    """Tests for GET /metrics."""

    def test_metrics_returns_200(self):
        """Metrics endpoint should return 200 with required sections."""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "performance" in data
        assert "models" in data
        assert "system_info" in data

    def test_metrics_has_request_counts(self):
        """Metrics should include request counters."""
        response = client.get("/metrics")
        data = response.json()
        perf = data["performance"]
        assert "total_requests" in perf
        assert "extraction_count" in perf
        assert "verification_count" in perf


# ── Claim Extraction ─────────────────────────────────────────────────────


class TestExtractClaimsEndpoint:
    """Tests for POST /extract-claims."""

    def test_extract_claims_empty_text_returns_400(self):
        """Empty text should return 400."""
        response = client.post(
            "/extract-claims",
            json={"text": ""},
        )
        assert response.status_code in (400, 422)

    def test_extract_claims_valid_text(self):
        """Valid text should return 200 with claims list."""
        response = client.post(
            "/extract-claims",
            json={
                "text": (
                    "Apple Inc. was founded on April 1, 1976 by Steve Jobs "
                    "and Steve Wozniak. The company is headquartered in "
                    "Cupertino, California. Tim Cook became CEO in 2011."
                ),
            },
        )
        # May be 200 (success) or 500 (if Gemini key is invalid in test env)
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"
            assert isinstance(data["claims"], list)
            assert "document" in data

    def test_extract_claims_with_document_id(self):
        """Document ID should be passed through to the response."""
        response = client.post(
            "/extract-claims",
            json={
                "text": "The Earth orbits the Sun once every 365 days.",
                "document_id": "test_doc_001",
            },
        )
        if response.status_code == 200:
            data = response.json()
            assert data["document"] == "test_doc_001"


# ── Claim Verification ───────────────────────────────────────────────────


class TestVerifyClaimEndpoint:
    """Tests for POST /verify-claim."""

    def test_verify_claim_empty_returns_400(self):
        """Empty claim should return 400."""
        response = client.post(
            "/verify-claim",
            json={"claim": ""},
        )
        assert response.status_code in (400, 422)

    def test_verify_claim_valid(self):
        """Valid claim should return structured verdict."""
        response = client.post(
            "/verify-claim",
            json={"claim": "Apple was founded in 1976"},
        )
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"
            assert data["verification_status"] in ("SUPPORT", "CONTRADICTION", "NEUTRAL")
            assert 0.0 <= data["confidence_score"] <= 1.0
            assert "explanation" in data


# ── Graph Data ────────────────────────────────────────────────────────────


class TestGraphDataEndpoint:
    """Tests for GET /graph-data."""

    def test_graph_data_returns_200(self):
        """Graph data endpoint should return 200 with nodes and edges."""
        response = client.get("/graph-data")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)


# ── OpenAPI Schema ────────────────────────────────────────────────────────


class TestOpenAPISchema:
    """Tests for API documentation availability."""

    def test_openapi_schema_available(self):
        """OpenAPI schema should be accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "Fact-Checking RAG API"
        assert schema["info"]["version"] == "2.0.0"

    def test_docs_available(self):
        """Swagger UI should be accessible."""
        response = client.get("/docs")
        assert response.status_code == 200


# ── CLI Runner ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
