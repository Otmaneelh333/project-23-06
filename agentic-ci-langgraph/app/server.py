"""API HTTP minimale pour appeler l'agent."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from .graph import run_agent

app = FastAPI(title="agentic-ci-langgraph")
logger = logging.getLogger(__name__)


class AgentRunRequest(BaseModel):
    """Corps de la requête d'exécution de l'agent."""

    input: str = Field(min_length=1, max_length=500)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "langgraph-agent"}


@app.post("/agent/run")
def run(request: AgentRunRequest) -> dict:
    """Exécute l'agent et retourne directement sa réponse finale."""
    try:
        return run_agent(request.input)
    except Exception:
        logger.exception("Erreur inattendue pendant l'exécution de l'agent")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Le service ne peut pas traiter cette demande pour le moment.",
        ) from None
