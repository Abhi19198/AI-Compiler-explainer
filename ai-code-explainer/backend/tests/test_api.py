"""Tests for the FastAPI app: /health and POST /explain.

The real Claude call is never made here: ``routers.explain.explain_code``
is replaced with a stub, so these tests run with no API key and no network.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from main import app
from routers import explain as explain_router

SAMPLE_RESULT = {
    "language_detected": "python",
    "line_by_line_explanation": [
        {"line": "x = 1", "explanation": "Assigns 1 to x."},
        {"line": "print(x)", "explanation": "Prints the value of x."},
    ],
    "time_complexity": {"value": "O(1)", "reasoning": "No loops or recursion."},
    "space_complexity": {"value": "O(1)", "reasoning": "A constant number of variables."},
    "dry_run": {
        "sample_input": "none",
        "steps": [{"step": 1, "state": "x=1", "note": "Assignment runs."}],
        "final_output": "1",
    },
    "flowchart_mermaid": "flowchart TD\n    A[Start] --> B[End]",
    "bugs_and_suggestions": [],
    "summary": "Assigns 1 to x and prints it.",
}


@pytest.fixture
def client(monkeypatch):
    """TestClient with a fresh, empty explain cache per test."""
    explain_router._cache.clear()
    monkeypatch.setattr(explain_router, "explain_code", AsyncMock(return_value=SAMPLE_RESULT))
    return TestClient(app)


def test_health_ok():
    with TestClient(app) as c:
        assert c.get("/health").json() == {"status": "ok"}


def test_explain_success(client):
    res = client.post("/explain", json={"code": "x = 1\nprint(x)", "language_hint": "python"})
    assert res.status_code == 200
    body = res.json()
    assert body["language_detected"] == "python"
    assert body["time_complexity"]["value"] == "O(1)"
    assert body["summary"] == "Assigns 1 to x and prints it."


def test_explain_passes_language_hint_to_llm(client):
    client.post("/explain", json={"code": "x = 1", "language_hint": "python"})
    explain_router.explain_code.assert_awaited_once_with("x = 1", "python")


def test_explain_caches_identical_requests(client):
    payload = {"code": "x = 1", "language_hint": "python"}
    assert client.post("/explain", json=payload).status_code == 200
    assert client.post("/explain", json=payload).status_code == 200
    # Second identical request must not call the LLM again.
    explain_router.explain_code.assert_awaited_once()


def test_explain_empty_code_rejected(client):
    res = client.post("/explain", json={"code": "", "language_hint": "python"})
    assert res.status_code == 422


def test_explain_missing_code_rejected(client):
    res = client.post("/explain", json={"language_hint": "python"})
    assert res.status_code == 422


def test_explain_code_over_max_length_rejected(client):
    res = client.post("/explain", json={"code": "x" * 8001})
    assert res.status_code == 422


def test_explain_code_at_max_length_accepted(client):
    res = client.post("/explain", json={"code": "x" * 8000})
    assert res.status_code == 200


def test_explain_wrong_type_rejected(client):
    res = client.post("/explain", json={"code": 123})
    assert res.status_code == 422


def test_explain_missing_api_key_returns_502(monkeypatch):
    explain_router._cache.clear()
    monkeypatch.setattr(
        explain_router,
        "explain_code",
        AsyncMock(side_effect=ValueError("ANTHROPIC_API_KEY is missing.")),
    )
    with TestClient(app) as c:
        res = c.post("/explain", json={"code": "x = 1"})
    assert res.status_code == 502
    assert "ANTHROPIC_API_KEY" in res.json()["detail"]


def test_explain_unexpected_error_returns_generic_500(monkeypatch):
    explain_router._cache.clear()
    monkeypatch.setattr(
        explain_router,
        "explain_code",
        AsyncMock(side_effect=RuntimeError("boom")),
    )
    with TestClient(app) as c:
        res = c.post("/explain", json={"code": "x = 1"})
    assert res.status_code == 500
    # Internal error text must not leak to the client.
    assert "boom" not in res.json()["detail"]
