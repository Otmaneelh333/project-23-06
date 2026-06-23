"""Tests déterministes du routage vers la Dead Letter Queue."""

import pytest

from app import dlq as dlq_module
from app import graph as graph_module


def fake_failure(query: str) -> dict:
    """Double de l'API externe retournant une indisponibilité 503."""
    return {"status": "FAILURE", "payload": {}, "error": "HTTP_ERROR_503"}


@pytest.fixture
def failure_execution(monkeypatch, tmp_path):
    """Exécute l'agent sur une DLQ temporaire et renvoie sa sortie et son entrée."""
    monkeypatch.setattr(graph_module, "call_wikipedia_api", fake_failure)
    monkeypatch.setattr(dlq_module, "DLQ_PATH", tmp_path / "data" / "dlq_messages.jsonl")

    prompt = "Where Morocco is located?"
    result = graph_module.run_agent(prompt)
    messages = dlq_module.read_dlq_messages()
    return result, messages, prompt


def test_agent_returns_fallback_when_api_fails(failure_execution):
    result, _, _ = failure_execution

    assert result["status"] == "FALLBACK"
    assert "service externe" in result["answer"]
    assert result["dlq_id"] is not None
    assert result["api_error"] == "HTTP_ERROR_503"


def test_dlq_entry_contains_prompt_and_failed_status(failure_execution):
    _, messages, prompt = failure_execution

    assert len(messages) == 1
    assert messages[0]["original_prompt"] == prompt
    assert messages[0]["status"] == "FAILED_ROUTED_TO_DLQ"
