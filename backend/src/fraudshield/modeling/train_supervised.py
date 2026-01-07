# FraudShield-Enterprise/backend/src/fraudshield/modeling/train_supervised.py

"""
Minimal credible ML lifecycle demo (requires `fraudshield[ml]`).

Trains a LogisticRegression on a tiny synthetic dataset and registers it via joblib.

In a real system:
- Offline dataset creation via feature store
- Proper train/val split and metrics
- Robust model registry (MLflow/Vertex/SageMaker)
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from ..core.settings import settings
from .registry import set_latest


def train_and_register() -> str:
    """
    Train a minimal sklearn LogisticRegression model and register it as the latest model.

    Returns:
        model_path: Path to the saved joblib artifact.
    """
    # Imports only available when installing `fraudshield[ml]`
    import joblib  # type: ignore
    import numpy as np  # type: ignore
    from sklearn.linear_model import LogisticRegression  # type: ignore

    # Tiny synthetic dataset (demo only)
    # Feature order MUST match modeling/scoring.py:
    # [amount, ip_is_proxy, txn_count_1h, account_age_days, device_ip_mismatch,
    #  shipping_is_freight_forwarder, ship_bill_mismatch]
    X = np.array(
        [
            [100, 0, 0, 400, 0, 0, 0],
            [2500, 1, 2, 30, 1, 1, 0],
            [5000, 1, 7, 2, 1, 1, 1],
            [50, 0, 1, 900, 0, 0, 0],
            [1800, 0, 6, 5, 1, 0, 1],
            [3200, 1, 3, 12, 1, 1, 0],
            [75, 0, 0, 1200, 0, 0, 0],
        ],
        dtype=float,
    )
    y = np.array([0, 1, 1, 0, 1, 1, 0], dtype=int)

    model = LogisticRegression(max_iter=500, class_weight="balanced")
    model.fit(X, y)

    s = settings()
    os.makedirs(s.model_registry_path, exist_ok=True)

    version = "sklearn_lr_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    model_path = os.path.join(s.model_registry_path, f"{version}.joblib")

    joblib.dump(model, model_path)
    set_latest(model_path=model_path, model_version=version)

    print(f"✅ Registered sklearn model: {model_path} (version={version})")
    return model_path


if __name__ == "__main__":
    train_and_register()
