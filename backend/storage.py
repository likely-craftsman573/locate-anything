"""SQLite-backed search history + image storage (stdlib only)."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS searches (
    id              TEXT PRIMARY KEY,
    task            TEXT NOT NULL,
    prompt          TEXT NOT NULL,
    generation_mode TEXT NOT NULL,
    image_path      TEXT NOT NULL,
    image_width     INTEGER NOT NULL,
    image_height    INTEGER NOT NULL,
    result_json     TEXT NOT NULL,
    stats_json      TEXT,
    timing_ms       REAL NOT NULL,
    created_at      TEXT NOT NULL
);
"""


class Store:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.images_dir = self.data_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "history.db"
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(_SCHEMA)
        self._conn.commit()

    @staticmethod
    def new_id() -> str:
        return uuid.uuid4().hex

    def image_path_for(self, search_id: str, suffix: str) -> Path:
        suffix = suffix if suffix.startswith(".") else f".{suffix}"
        return self.images_dir / f"{search_id}{suffix}"

    def save(
        self,
        *,
        search_id: str,
        task: str,
        prompt: str,
        generation_mode: str,
        image_path: Path,
        image_width: int,
        image_height: int,
        result: dict,
        stats: dict | None,
        timing_ms: float,
    ) -> dict:
        created_at = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """INSERT INTO searches (id, task, prompt, generation_mode, image_path,
                   image_width, image_height, result_json, stats_json, timing_ms, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                search_id,
                task,
                prompt,
                generation_mode,
                str(image_path),
                image_width,
                image_height,
                json.dumps(result),
                json.dumps(stats) if stats is not None else None,
                timing_ms,
                created_at,
            ),
        )
        self._conn.commit()
        return self.get(search_id)

    def get(self, search_id: str) -> dict | None:
        row = self._conn.execute("SELECT * FROM searches WHERE id = ?", (search_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def list(self, limit: int = 50, offset: int = 0) -> tuple[list[dict], int]:
        total = self._conn.execute("SELECT COUNT(*) FROM searches").fetchone()[0]
        rows = self._conn.execute(
            "SELECT * FROM searches ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows], total

    def delete(self, search_id: str) -> bool:
        row = self.get(search_id)
        if row is None:
            return False
        try:
            Path(row["image_path"]).unlink(missing_ok=True)
        except OSError:
            pass
        self._conn.execute("DELETE FROM searches WHERE id = ?", (search_id,))
        self._conn.commit()
        return True

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        d = dict(row)
        d["result"] = json.loads(d.pop("result_json"))
        stats = d.pop("stats_json")
        d["stats"] = json.loads(stats) if stats else None
        return d
