from __future__ import annotations

import json
from typing import Any, Dict


def extract_json(obj: Any) -> Dict[str, Any]:
    """Robust JSON extraction used for LLM/task outputs.

    Supports:
    - objects with `.raw`
    - markdown fences
    - surrounding prose (extracts the first {...} block)
    """

    if hasattr(obj, "raw"):
        obj = getattr(obj, "raw")

    s = str(obj or "").strip()
    if not s:
        return {"_error": "empty_output"}

    # Strip markdown fences
    s = s.replace("```json", "").replace("```", "").strip()

    # First try: direct parse
    try:
        parsed = json.loads(s)
        if isinstance(parsed, dict):
            return parsed
        return {"value": parsed}
    except Exception:
        pass

    # Fallback: substring parse for first JSON object
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(s[start : end + 1])
        except Exception:
            return {"_error": "invalid_json", "raw": s[:2000]}

    return {"_error": "no_json_found", "raw": s[:2000]}
