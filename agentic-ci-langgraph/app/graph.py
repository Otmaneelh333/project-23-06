"""Workflow LangGraph résilient de consultation Wikipédia."""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph

from .dlq import write_to_dlq
from .schemas import (
    FAILURE,
    ROUTE_DLQ,
    ROUTE_SUCCESS,
    SUCCESS,
    AgentState,
    create_initial_state,
)
from .tools import call_wikipedia_api, extract_summary


def prepare_input(state: AgentState) -> AgentState:
    """Nettoie l'entrée utilisateur avant tout appel externe."""
    return {"normalized_input": state.get("user_input", "").strip()}


def call_api_node(state: AgentState) -> AgentState:
    """Appelle l'API via sa façade normalisée, sans exception propagée."""
    result = call_wikipedia_api(state.get("normalized_input", ""))
    status = result.get("status", FAILURE)
    return {
        "api_status": status,
        "api_payload": result.get("payload", {}),
        "api_error": result.get("error"),
        "route": ROUTE_SUCCESS if status == SUCCESS else ROUTE_DLQ,
    }


def route_after_api(state: AgentState) -> Literal["success", "dlq"]:
    """Oriente vers la génération de réponse ou la DLQ."""
    return ROUTE_SUCCESS if state.get("api_status") == SUCCESS else ROUTE_DLQ


def generate_answer_node(state: AgentState) -> AgentState:
    """Produit une réponse utilisateur à partir du résumé retourné."""
    summary = extract_summary(state.get("api_payload", {}))
    answer = summary or "L'information demandée est actuellement indisponible."
    return {"answer": answer}


def validate_answer_node(state: AgentState) -> AgentState:
    """Applique les règles de conformité minimales de l'atelier."""
    answer = state.get("answer", "")
    errors: list[str] = []
    if not answer.strip():
        errors.append("La réponse est vide.")
    if len(answer) < 20:
        errors.append("La réponse doit contenir au moins 20 caractères.")
    if "None" in answer:
        errors.append("La réponse contient la valeur interdite 'None'.")
    if "NaN" in answer:
        errors.append("La réponse contient la valeur interdite 'NaN'.")
    return {"is_conform": not errors, "conformity_errors": errors}


def send_to_dlq_node(state: AgentState) -> AgentState:
    """Persiste l'échec et garantit une réponse de repli utilisable."""
    dlq_id = write_to_dlq(
        user_input=state.get("user_input", ""),
        api_error=state.get("api_error") or "UNKNOWN_ERROR",
        api_payload=state.get("api_payload", {}),
    )
    return {
        "dlq_id": dlq_id,
        "answer": "Le service externe est momentanément indisponible. Votre demande a été enregistrée pour traitement.",
        "is_conform": True,
        "conformity_errors": [],
    }


def final_response_node(state: AgentState) -> AgentState:
    """Construit le seul objet rendu par l'agent au code appelant."""
    return {
        "final_response": {
            "status": SUCCESS if state.get("route") == ROUTE_SUCCESS else "FALLBACK",
            "input": state.get("user_input", ""),
            "answer": state.get("answer", ""),
            "is_conform": state.get("is_conform", False),
            "conformity_errors": state.get("conformity_errors", []),
            "dlq_id": state.get("dlq_id"),
            "api_error": state.get("api_error"),
        }
    }


def build_graph():
    """Construit et compile le workflow LangGraph."""
    workflow = StateGraph(AgentState)
    workflow.add_node("prepare_input", prepare_input)
    workflow.add_node("call_api_node", call_api_node)
    workflow.add_node("generate_answer_node", generate_answer_node)
    workflow.add_node("validate_answer_node", validate_answer_node)
    workflow.add_node("send_to_dlq_node", send_to_dlq_node)
    workflow.add_node("final_response_node", final_response_node)

    workflow.add_edge(START, "prepare_input")
    workflow.add_edge("prepare_input", "call_api_node")
    workflow.add_conditional_edges(
        "call_api_node",
        route_after_api,
        {ROUTE_SUCCESS: "generate_answer_node", ROUTE_DLQ: "send_to_dlq_node"},
    )
    workflow.add_edge("generate_answer_node", "validate_answer_node")
    workflow.add_edge("validate_answer_node", "final_response_node")
    workflow.add_edge("send_to_dlq_node", "final_response_node")
    workflow.add_edge("final_response_node", END)
    return workflow.compile()


def run_agent(user_input: str) -> dict:
    """Exécute le workflow et retourne uniquement sa réponse finale."""
    result = build_graph().invoke(create_initial_state(user_input))
    return result["final_response"]


if __name__ == "__main__":
    print(run_agent("Where Morocco is located?"))
