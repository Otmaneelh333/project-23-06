"""Persistance locale d'une dead-letter queue au format JSON Lines."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .schemas import DLQMessage


DLQ_PATH = Path(__file__).resolve().parents[1] / "data" / "dlq_messages.jsonl"


def _append_jsonl(path: Path, entry: dict[str, Any]) -> None:
    """Ajoute une entrée JSON sérialisable au fichier fourni."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")


def write_to_dlq(user_input: str, api_error: str, api_payload: dict | None = None) -> str:
    """Enregistre un échec d'API dans la DLQ locale et retourne son UUID.

    ``DLQ_PATH`` peut être remplacé avec ``monkeypatch`` dans les tests afin
    d'isoler l'écriture dans un répertoire temporaire.
    """
    dlq_id = str(uuid4())
    entry: dict[str, Any] = {
        "id": dlq_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "original_prompt": user_input,
        "status": "FAILED_ROUTED_TO_DLQ",
        "error": api_error,
        "payload": api_payload or {},
    }
    _append_jsonl(DLQ_PATH, entry)
    return dlq_id


def read_dlq_messages() -> list[dict]:
    """Retourne les messages lisibles de la DLQ, ou une liste vide si absente."""
    if not DLQ_PATH.is_file():
        return []

    messages: list[dict] = []
    with DLQ_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(entry, dict):
                messages.append(entry)
    return messages


class LocalDLQ:
    """Écrit les échecs dans un fichier JSONL, une ligne par message."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def publish(self, message: DLQMessage) -> None:
        """Ajoute un message d'échec à la file locale."""
        _append_jsonl(self.path, message.model_dump())
