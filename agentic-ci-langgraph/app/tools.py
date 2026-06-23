"""Outils externes de l'agent."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from .schemas import FAILURE, SUCCESS


WIKIPEDIA_API = "https://fr.wikipedia.org/api/rest_v1/page/summary"


def call_wikipedia_api(query: str) -> dict[str, Any]:
    """Appelle Wikipédia et retourne toujours un résultat normalisé.

    Cette fonction constitue la frontière réseau du workflow : les noeuds du
    graphe peuvent donc traiter son retour sans bloc ``try/except``.
    """
    normalized_query = query.strip()
    if not normalized_query:
        return {"status": FAILURE, "payload": {}, "error": "EMPTY_INPUT"}

    url = f"{WIKIPEDIA_API}/{quote(normalized_query, safe='')}"
    try:
        response = requests.get(url, headers={"Accept": "application/json"}, timeout=8)
        if response.status_code >= 400:
            return {"status": FAILURE, "payload": {}, "error": f"HTTP_ERROR_{response.status_code}"}

        payload = response.json()
        if not isinstance(payload, dict):
            return {"status": FAILURE, "payload": {}, "error": "EXCEPTION: Réponse JSON invalide"}
        return {"status": SUCCESS, "payload": payload, "error": None}
    except requests.Timeout:
        return {"status": FAILURE, "payload": {}, "error": "TIMEOUT"}
    except Exception as error:
        return {"status": FAILURE, "payload": {}, "error": f"EXCEPTION: {error}"}


def extract_summary(payload: dict[str, Any]) -> str:
    """Extrait un résumé de la réponse REST ou MediaWiki, sinon une chaîne vide."""
    extract = payload.get("extract")
    if isinstance(extract, str) and extract.strip():
        return extract.strip()

    query = payload.get("query")
    pages = query.get("pages") if isinstance(query, dict) else None
    if isinstance(pages, dict):
        for page in pages.values():
            if isinstance(page, dict):
                extract = page.get("extract")
                if isinstance(extract, str) and extract.strip():
                    return extract.strip()
    return ""

