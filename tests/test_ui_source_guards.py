from pathlib import Path

APP_SOURCE = Path(__file__).resolve().parents[1] / "app.py"
VALIDATION_SOURCE = Path(__file__).resolve().parents[1] / "core" / "validation.py"
README_SOURCE = Path(__file__).resolve().parents[1] / "README.md"


def _src() -> str:
    return APP_SOURCE.read_text(encoding="utf-8")


def test_m21_header_uses_safe_commercial_card():
    src = _src()
    assert ".block-container {padding-top: 2.10rem" in src
    assert "app-header-card" in src
    assert "app-header-title" in src
    assert "Segmental Box Girder Pro" in src


def test_dashboard_uses_professional_wording_without_chapter_prompt():
    src = _src()
    assert "Reference baseline loaded" in src
    assert "Review current workspace" in src
    assert "Baseline keyed" not in src
    assert "Review chapter UI" not in src


def test_navigation_keeps_single_source_of_truth_keys():
    src = _src()
    assert 'st.radio("WORKSPACE", WORKSPACE_LABELS, key="current_workspace")' in src
    assert 'st.radio("SUBPAGE", ws["subpages"], key="current_subpage")' in src
    assert "old_nav" not in src


def test_m22_layout_balances_main_container_leftward():
    src = _src()
    assert "max-width: 1680px" in src
    assert "margin-left: 0" in src
    assert "margin-right: auto" in src
    assert "padding-left: 2.0rem" in src


def test_m22_sidebar_readability_css_is_explicit():
    src = _src()
    assert '[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {font-size: 0.84rem' in src
    assert "sidebar-context-row" in src
    assert "sidebar-context-value" in src


def test_m22_status_wording_distinguishes_baseline_and_app_results():
    src = _src()
    assert "Baseline Ready" in src
    assert "Baseline PASS" in src
    assert "App PASS" in src or "app_status" in src
    assert "Status wording separates R10 baseline readiness" in src


def test_m22_fea_status_does_not_overstate_import_engine():
    src = _src()
    assert "Baseline summary active" in src
    assert "Detailed station-by-station FEA import pending" in src
    assert "full envelope checks" in src


def test_m22_schema_version_is_updated():
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert 'PROJECT_SCHEMA_VERSION = "0.3.2-commercial-m2.2"' in validation_src


def test_readme_documents_m22_status_honesty():
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "Commercial M2.2" in readme
    assert "Baseline Ready" in readme
    assert "station-by-station FEA import remains pending" in readme
