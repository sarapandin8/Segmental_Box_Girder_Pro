from pathlib import Path

APP_SOURCE = Path(__file__).resolve().parents[1] / "app.py"


def test_m21_header_uses_safe_commercial_card():
    src = APP_SOURCE.read_text(encoding="utf-8")
    assert ".block-container {padding-top: 2.25rem" in src
    assert "app-header-card" in src
    assert "app-header-title" in src
    assert "Segmental Box Girder Pro" in src


def test_dashboard_uses_professional_wording_without_chapter_prompt():
    src = APP_SOURCE.read_text(encoding="utf-8")
    assert "Reference baseline loaded" in src
    assert "Review current workspace" in src
    assert "Baseline keyed" not in src
    assert "Review chapter UI" not in src


def test_navigation_keeps_single_source_of_truth_keys():
    src = APP_SOURCE.read_text(encoding="utf-8")
    assert 'st.radio("WORKSPACE", WORKSPACE_LABELS, key="current_workspace")' in src
    assert 'st.radio("SUBPAGE", ws["subpages"], key="current_subpage")' in src
    assert "old_nav" not in src
