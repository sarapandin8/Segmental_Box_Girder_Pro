from __future__ import annotations

import json

import pytest

from core.bg40_defaults import BG40_DEFAULT
from core.project_io import ProjectJsonLoadError, load_project_json_bytes, project_json_fingerprint, project_load_summary
from core.validation import PROJECT_SCHEMA_VERSION


def test_load_project_json_bytes_migrates_schema_and_keeps_project_data() -> None:
    legacy = json.loads(json.dumps(BG40_DEFAULT))
    legacy["meta"]["schema_version"] = "0.3.8-old"
    legacy["project"]["name"] = "USER_PROJECT"
    raw = json.dumps(legacy).encode("utf-8")
    loaded = load_project_json_bytes(raw, "saved_project.json")
    assert loaded["project"]["name"] == "USER_PROJECT"
    assert loaded["meta"]["schema_version"] == PROJECT_SCHEMA_VERSION
    summary = project_load_summary(loaded)
    assert summary["project"] == "USER_PROJECT"
    assert summary["schema_version"] == PROJECT_SCHEMA_VERSION


def test_load_project_json_bytes_rejects_invalid_json() -> None:
    with pytest.raises(ProjectJsonLoadError):
        load_project_json_bytes(b"{not json", "bad.json")


def test_project_json_fingerprint_changes_with_content() -> None:
    a = project_json_fingerprint(b"{}", "project.json")
    b = project_json_fingerprint(b'{"x":1}', "project.json")
    assert a != b


def test_app_project_json_loader_uses_explicit_button_not_auto_rerun_loop() -> None:
    from pathlib import Path

    app_text = Path(__file__).resolve().parents[1].joinpath("app.py").read_text()
    assert 'st.file_uploader("Load Project JSON", type=["json"], key="project_json_upload")' in app_text
    assert 'st.button("Load uploaded project", key="load_project_json_button"' in app_text
    assert 'json.loads(uploaded.read().decode("utf-8"))' not in app_text
