from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from core.validation import ensure_project_schema

MAX_PROJECT_JSON_BYTES = 20 * 1024 * 1024  # 20 MB guard; project JSON should normally be much smaller.


class ProjectJsonLoadError(ValueError):
    """Raised when a saved project JSON cannot be loaded safely."""


def project_json_fingerprint(raw: bytes, filename: str = "") -> str:
    """Return a stable fingerprint for an uploaded JSON file."""
    h = hashlib.sha256()
    h.update(filename.encode("utf-8", errors="ignore"))
    h.update(b"\0")
    h.update(raw)
    return h.hexdigest()


def load_project_json_bytes(raw: bytes, filename: str = "") -> Dict[str, Any]:
    """Decode, validate, and migrate a saved project JSON payload.

    The function is intentionally side-effect free so the Streamlit UI can call it
    only from an explicit Apply/Load button. This prevents file_uploader rerun loops
    when an uploaded file remains present across Streamlit reruns.
    """
    if not raw:
        raise ProjectJsonLoadError("The uploaded project JSON is empty.")
    if len(raw) > MAX_PROJECT_JSON_BYTES:
        raise ProjectJsonLoadError(
            f"The uploaded project JSON is too large ({len(raw) / (1024 * 1024):.1f} MB). "
            "Check that this is a saved project JSON, not an input spreadsheet or image."
        )
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ProjectJsonLoadError("The uploaded file is not valid UTF-8 JSON.") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProjectJsonLoadError(f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ProjectJsonLoadError("The project JSON root must be an object/dictionary.")
    try:
        return ensure_project_schema(data)
    except Exception as exc:  # noqa: BLE001 - convert migration errors to a user-facing load error.
        raise ProjectJsonLoadError(f"Project JSON schema migration failed: {exc}") from exc


def project_load_summary(project: Dict[str, Any]) -> Dict[str, str]:
    """Compact user-facing summary for a migrated project dict."""
    meta = project.get("meta", {}) if isinstance(project, dict) else {}
    p = project.get("project", {}) if isinstance(project, dict) else {}
    return {
        "project": str(p.get("name", "-")),
        "bridge_object": str(p.get("bridge_object", "-")),
        "schema_version": str(meta.get("schema_version", "-")),
        "baseline_report": str(meta.get("baseline_report", "-")),
    }
