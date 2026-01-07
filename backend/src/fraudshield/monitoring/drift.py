"""Drift monitoring stub (enterprise hook).

Production implementations typically compute PSI/KS (and/or embedding drift),
compare against thresholds, and emit alerts + dashboards.
"""

from __future__ import annotations

from typing import Any, Dict


def check_drift(reference_df: Any, current_df: Any) -> Dict[str, Any]:
    # Placeholder: wire in Evidently or custom PSI/KS.
    return {"drift_detected": False, "psi": 0.02, "note": "stub"}
