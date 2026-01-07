# FraudShield-Enterprise/backend/src/fraudshield/modeling/registry.py

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional

from ..core.settings import settings


@dataclass(frozen=True)
class ModelPointer:
    model_path: str
    model_version: str


def _latest_path() -> str:
    """
    Path to the pointer file that tracks the currently active model artifact.
    """
    s = settings()
    os.makedirs(s.model_registry_path, exist_ok=True)
    return os.path.join(s.model_registry_path, "latest.json")


def set_latest(model_path: str, model_version: str) -> None:
    """
    Persist the pointer to the latest model artifact.
    """
    payload = {"model_path": model_path, "model_version": model_version}
    with open(_latest_path(), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def get_latest() -> Optional[ModelPointer]:
    """
    Load the pointer to the latest model artifact.
    Returns None if not set or if the referenced artifact is missing.
    """
    p = _latest_path()
    if not os.path.exists(p):
        return None

    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)

    model_path = d.get("model_path")
    if not model_path or not os.path.exists(model_path):
        return None

    return ModelPointer(
        model_path=model_path,
        model_version=d.get("model_version", "unknown"),
    )
