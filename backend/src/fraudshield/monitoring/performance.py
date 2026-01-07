"""Performance monitoring stub (enterprise hook).

Production implementations join decisions with *delayed labels* (chargebacks, disputes, confirmed fraud)
and compute precision/recall, capture rate, false positive rate, threshold tuning, etc.
"""

from __future__ import annotations

from typing import Any, Dict


def compute_performance(decisions_df: Any, labels_df: Any) -> Dict[str, Any]:
    return {"precision": None, "recall": None, "note": "stub - requires labels"}
