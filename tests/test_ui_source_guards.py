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


def test_m3c_schema_version_is_updated():
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert 'PROJECT_SCHEMA_VERSION = "0.3.6-commercial-m3c"' in validation_src


def test_readme_documents_m3c_dpt_and_aashto_ir_milestone():
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "Commercial M3C" in readme or "COMMERCIAL.M3C" in readme
    assert "1.3 Design Loads" in readme
    assert "general_ss_s1_by_district.csv" in readme
    assert "Bangkok Basin Zone 1–10" in readme
    assert "AASHTO LRFD 2014 Table 3.10.7.1-1" in readme
    assert "Full station-by-station FEA import remains pending" in readme


def test_m3b_load_pages_use_editable_tables_and_code_basis():
    src = _src()
    assert "st.data_editor" in src
    assert "sdl_component_editor" in src
    assert "Code basis:" in src
    assert "EN 1991-2 Art. 6.4.3" in src
    assert "EN 1991-2 Art. 6.5.3" in src
    assert "EN 1991-2 Art. 6.5.2" in src
    assert "EN 1991-2 Art. 6.5.1" in src
    assert "DPT 1301/1302-61" in src


def test_m3a_load_figures_and_plotly_modebar_are_present():
    src = _src()
    assert "u20_loading_diagram" in src
    assert "rail_horizontal_forces_diagram" in src
    assert "wind_bridge_direction_diagram" in src
    assert "response_spectrum_figure" in src
    assert "PLOTLY_CONFIG" in src


def test_m3a_no_duplicate_sdl_summary_input_pattern():
    src = _src()
    assert 'D["load_components"]["sdl_components"] = edited.to_dict("records")' in src
    assert "FEA summary reads from the same load schema" in src


def test_m3c_aashto_ir_controls_are_present_once_in_eq_page():
    src = _src()
    assert "AASHTO bridge seismic parameters" in src
    assert "eq_aashto_operational_category" in src
    assert "eq_aashto_substructure_type" in src
    assert "eq_importance_factor_preset" in src
    assert "eq_manual_response_modification_factor" in src
    assert "seismic_R_source" in src
    assert "AASHTO LRFD 2014 Table 3.10.7.1-1" in src

def test_m3c_aashto_reference_data_files_exist():
    root = APP_SOURCE.resolve().parents[0]
    assert (root / "data" / "aashto_lrfd_2014" / "response_modification_factors_substructures_3_10_7_1_1.csv").exists()
    assert (root / "data" / "aashto_lrfd_2014" / "response_modification_factors_connections_3_10_7_1_2.csv").exists()
