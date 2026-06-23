"""Schémas et types partagés par l'agent."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """Entrée publique de l'agent."""

    question: str = Field(min_length=1, max_length=500)


class QuestionResponse(BaseModel):
    """Sortie publique de l'agent."""

    answer: str
    source_url: str | None = None
    routed_to_dlq: bool = False


class DLQMessage(BaseModel):
    """Message persistant lorsqu'un appel externe échoue."""

    question: str
    error_type: str
    error_message: str
    status_code: int | None = None


SUCCESS = "SUCCESS"
FAILURE = "FAILURE"
ROUTE_SUCCESS = "success"
ROUTE_DLQ = "dlq"


class AgentState(TypedDict, total=False):
    """État partagé par les noeuds d'un :class:`langgraph.graph.StateGraph`.

    ``total=False`` permet à chaque noeud de ne retourner que les clés qu'il
    met à jour, comportement attendu par LangGraph lors de la fusion d'état.
    Les champs ``question`` et associés sont conservés temporairement pour la
    compatibilité avec le premier exemple de graphe de l'atelier.
    """

    user_input: str
    normalized_input: str
    api_status: str
    api_payload: dict[str, Any]
    api_error: str | None
    route: str
    answer: str
    is_conform: bool
    conformity_errors: list[str]
    dlq_id: str | None
    final_response: dict[str, Any]

    # Compatibilité avec le graphe déjà présent dans le projet.
    question: str
    source_url: str
    error_type: Literal["http_error", "timeout", "exception"]
    error_message: str
    status_code: int
    routed_to_dlq: bool


def create_initial_state(user_input: str) -> AgentState:
    """Construit l'état initial stable, prêt à être envoyé au StateGraph."""
    return {
        "user_input": user_input,
        "normalized_input": "",
        "api_status": "",
        "api_payload": {},
        "api_error": None,
        "route": "",
        "answer": "",
        "is_conform": False,
        "conformity_errors": [],
        "dlq_id": None,
        "final_response": {},
    }
