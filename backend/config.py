"""Runtime configuration, read from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

VALID_MODES = ("fast", "hybrid", "slow")


def _as_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    mock: bool
    model_path: str
    default_mode: str
    data_dir: str


@lru_cache
def get_settings() -> Settings:
    mode = os.environ.get("LA_DEFAULT_MODE", "hybrid").strip().lower()
    if mode not in VALID_MODES:
        mode = "hybrid"
    return Settings(
        mock=_as_bool(os.environ.get("LA_MOCK")),
        model_path=os.environ.get("LA_MODEL_PATH", "nvidia/LocateAnything-3B"),
        default_mode=mode,
        data_dir=os.environ.get("LA_DATA_DIR", "./data"),
    )
