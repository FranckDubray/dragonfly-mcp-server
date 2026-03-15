from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Settings


@dataclass
class RunState:
    corpus: str
    mode: str
    last_processed_archive: str | None = None
    status: str = "idle"
    updated_at: str | None = None
    extra: dict[str, Any] | None = None


class LocalStateStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.state_dir = settings.workdir / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _state_path(self, corpus: str, mode: str) -> Path:
        return self.state_dir / f"{corpus}_{mode}_state.json"

    def load(self, corpus: str, mode: str) -> RunState:
        path = self._state_path(corpus, mode)
        if not path.exists():
            return RunState(corpus=corpus, mode=mode)

        payload = json.loads(path.read_text(encoding="utf-8"))
        return RunState(
            corpus=payload.get("corpus", corpus),
            mode=payload.get("mode", mode),
            last_processed_archive=payload.get("last_processed_archive"),
            status=payload.get("status", "idle"),
            updated_at=payload.get("updated_at"),
            extra=payload.get("extra") or {},
        )

    def save(self, state: RunState) -> Path:
        path = self._state_path(state.corpus, state.mode)
        payload = {
            "corpus": state.corpus,
            "mode": state.mode,
            "last_processed_archive": state.last_processed_archive,
            "status": state.status,
            "updated_at": state.updated_at,
            "extra": state.extra or {},
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
