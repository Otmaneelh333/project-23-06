"""Tests déterministes du chemin nominal du graphe."""

from app import graph as graph_module


def fake_success(query: str) -> dict:
    """Double de l'API Wikipédia : aucune requête réseau n'est effectuée."""
    return {
        "status": "SUCCESS",
        "payload": {
            "title": "Morocco",
            "extract": (
                "Morocco is a country in North Africa with coastlines on the "
                "Atlantic Ocean and Mediterranean Sea."
            ),
        },
        "error": None,
    }


def test_agent_success_response_is_conform_and_not_routed_to_dlq(monkeypatch):
    monkeypatch.setattr(graph_module, "call_wikipedia_api", fake_success)

    result = graph_module.run_agent("Where Morocco is located?")

    assert result["status"] == "SUCCESS"
    assert result["answer"]
    assert result["is_conform"] is True
    assert result["dlq_id"] is None
    assert result["api_error"] is None
