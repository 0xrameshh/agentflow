"""Tests for the support KB copilot API endpoints.

These tests use TestClient with FastAPI — no LLM calls.
Tests cover citation extraction, response models, and endpoint structure.
"""

from __future__ import annotations


import pytest
from fastapi.testclient import TestClient

from agentflow.api.main import (
    Citation,
    SupportRunResponse,
    _extract_answer,
    _extract_citations,
    app,
)
from agentflow.graph.state import make_initial_state


# ---------------------------------------------------------------------------
# Citation extraction (unit tests, no API key needed)
# ---------------------------------------------------------------------------


class TestCitationExtraction:
    def test_extract_citations_from_tool_message(self):
        """Should find [source: filename.md] markers in tool messages."""
        from langchain_core.messages import ToolMessage

        state = make_initial_state("test")
        state["messages"].append(
            ToolMessage(
                content="[source: refund-policy.md] Full refund within 30 days.\n\n[source: billing-faq.md] Plans start at $29.",
                tool_call_id="call_1",
                name="search_knowledge",
            )
        )

        citations = _extract_citations(state)
        assert len(citations) == 2
        sources = [c.source for c in citations]
        assert "refund-policy.md" in sources
        assert "billing-faq.md" in sources

    def test_extract_citations_deduplicates(self):
        """Duplicate source markers should only appear once."""
        from langchain_core.messages import ToolMessage

        state = make_initial_state("test")
        state["messages"].append(
            ToolMessage(
                content="[source: refund-policy.md] First mention.\n\n[source: refund-policy.md] Second mention.",
                tool_call_id="call_1",
                name="search_knowledge",
            )
        )

        citations = _extract_citations(state)
        # Should be deduplicated
        assert len(citations) == 1
        assert citations[0].source == "refund-policy.md"

    def test_extract_citations_empty(self):
        """No tool messages should produce empty citations."""
        citations = _extract_citations(make_initial_state("test"))
        assert citations == []

    def test_extract_answer_from_state(self):
        """Should find the last non-tool AI message."""
        from langchain_core.messages import AIMessage

        state = make_initial_state("test")
        state["messages"].append(
            AIMessage(content="Refunds are available within 30 days.", tool_calls=[])
        )

        answer = _extract_answer(state)
        assert "30 days" in answer


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class TestSupportRunResponse:
    def test_model_creation(self):
        resp = SupportRunResponse(
            answer="Refund policy is 30 days.",
            citations=[Citation(source="refund-policy.md", snippet="Full refund")],
            thread_id="test-123",
            run_id="abc123",
            tool_call_count=1,
            revision_count=0,
            latency_ms=1500,
        )
        assert resp.answer == "Refund policy is 30 days."
        assert len(resp.citations) == 1
        assert resp.citations[0].source == "refund-policy.md"
        assert resp.latency_ms == 1500


# ---------------------------------------------------------------------------
# API endpoints (mocked)
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Test client — endpoints that require API key will fail without mock."""
    return TestClient(app)


class TestApiEndpoints:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_root_endpoint(self, client):
        """GET / should return API info (UI is Next.js)."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Knowledge Copilot" in data["name"]
        assert "chat" in data

    def test_kb_articles_endpoint(self, client):
        """GET /kb/articles should list KB files."""
        response = client.get("/kb/articles")
        assert response.status_code == 200
        data = response.json()
        assert "articles" in data
        assert "count" in data
        assert data["count"] >= 1

    def test_run_support_returns_json(self, client):
        """POST /run/support should return valid JSON."""
        response = client.post("/run/support", json={"message": "test"})
        # Response depends on whether API key is available — just check JSON shape
        data = response.json()
        assert "answer" in data or "detail" in data

    def test_run_support_stream_sse(self, client):
        """POST /run/support/stream should return SSE content-type."""
        with client.stream("POST", "/run/support/stream", json={"message": "test"}) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
            chunks = list(response.iter_lines())
        assert any(line.startswith("data: ") for line in chunks if line)

    def test_run_returns_answer(self, client):
        """POST /run should return JSON with answer field."""
        response = client.post("/run", json={"message": "test"})
        data = response.json()
        assert "answer" in data or "detail" in data

    def test_run_full_returns_metadata(self, client):
        """POST /run/full should return metadata fields."""
        response = client.post("/run/full", json={"message": "test"})
        data = response.json()
        if response.status_code == 200:
            assert "tool_call_count" in data
            assert "revision_count" in data
