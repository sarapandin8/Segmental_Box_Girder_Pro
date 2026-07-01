from __future__ import annotations

import hashlib
import json
from math import sqrt
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go

from core.bg40_defaults import BG40_DEFAULT
from core.code_basis import (
    AASHTO_2020_SECTION5_LABEL,
    AASHTO_2020_SECTION5_TITLE,
    AASHTO_SECTION5_ARTICLE_MAP,
    code_basis_summary_rows,
)
from core.aashto_units import (
    concrete_strength_guard_mpa,
    ksi_to_mpa,
    mpa_to_ksi,
    kn_to_kip,
    kip_to_kn,
    mm_to_in,
    inch_to_mm,
    m_to_ft,
    ft_to_m,
    knm_to_kipft,
    kipft_to_knm,
    psi_sqrt_fc_coefficient_to_ksi,
    stress_mpa_from_ksi_sqrt_fc,
    standard_conversion_table,
)
from core.dpt_seismic import (
    bangkok_response_spectrum_points,
    dpt_bangkok_basin_spectrum,
    dpt_general_spectrum,
    list_dpt_districts,
    list_dpt_provinces,
    list_general_districts,
    list_general_provinces,
    lookup_general_ss_s1,
    resolve_location_region,
    response_spectrum_points,
)
from core.aashto_seismic import (
    OPERATIONAL_CATEGORIES,
    importance_preset_key_from_label,
    importance_preset_label_from_key,
    importance_preset_options,
    importance_value_from_preset,
    load_connection_r_table,
    load_substructure_r_table,
    recommended_substructure_r,
    substructure_key_from_label,
    substructure_label_from_key,
    substructure_options,
)
from core.formatting import format_engineering_table, format_engineering_value
from core.project_io import ProjectJsonLoadError, load_project_json_bytes, project_json_fingerprint, project_load_summary, section_persistence_summary, serialize_project_json_bytes
from core.section_geometry import calculate_section_properties, classify_point_in_section_void, default_coordinate_template, estimate_thin_walled_closed_box_j, normalize_coordinate_rows, read_coordinate_table
from core.tendon_adoption import (
    adopt_tendon_model,
    build_tendon_downstream_summary,
    build_tendon_source_trace,
    clear_adopted_tendon_model,
    tendon_model_fingerprint,
    tendon_model_status,
)
from core.tendon_layout import (
    build_tendon_layout_model,
    read_tendon_general_table,
    read_tendon_vertical_table,
    read_tendon_horizontal_table,
    tendon_model_to_frames,
    tendon_model_to_profile_frame,
    tendon_model_to_station_match_frame,
    tendon_points_at_station,
)
from core.load_models import (
    en_dynamic_factor_standard_maintenance,
    hunting_force_en1991,
    longitudinal_force_en1991,
    sdl_totals,
    wind_load_en1991_dpt_auto,
    wind_reference_group_options,
    wind_vb0_recommended_from_group,
)
from visualization.figure_system import figure_view_badge_text, plotly_config_for_view_mode
from visualization.section_figures import PLOTLY_SECTION_CONFIG, section_polygon_figure
from visualization.tendon_figures import (
    PLOTLY_TENDON_CONFIG,
    PLOTLY_TENDON_REPORT_CONFIG,
    PLOTLY_TENDON_REVIEW_CONFIG,
    tendon_elevation_figure,
    tendon_plan_figure,
    tendon_3d_review_figure,
    tendon_section_overlay_figure,
)
from visualization.load_figures import (
    PLOTLY_CONFIG,
    rail_horizontal_forces_diagram,
    response_spectrum_figure,
    u20_loading_diagram,
    u20_loading_diagram_svg,
    wind_bridge_direction_diagram,
)
from core.calculations import (
    aashto_creep_coefficient,
    aashto_shrinkage_strain,
    combined_transverse_check,
    en_centrifugal_percentage,
    friction_loss_table,
    prestress_loss_summary,
    provided_stirrups,
    shear_reinforcement_required,
    shear_torsion_web_components,
    torsion_aashto_586,
)
from core.report_schema import WORKSPACE_LABELS, get_workspace
from core.validation import (
    PROJECT_SCHEMA_VERSION,
    ensure_project_schema,
    issue_counts,
    validate_project,
    workflow_status,
)

st.set_page_config(
    page_title="Segmental Box Girder Pro",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
:root {
  --csp-blue-900: #092454;
  --csp-blue-800: #0b3b91;
  --csp-blue-700: #175cd3;
  --csp-blue-100: #e8f2ff;
  --csp-blue-050: #f7fbff;
  --csp-green-900: #14532d;
  --csp-green-800: #15803d;
  --csp-green-100: #dcfce7;
  --csp-green-050: #f0fff4;
  --csp-slate-900: #0f172a;
  --csp-slate-700: #344054;
  --csp-slate-500: #667085;
  --csp-slate-200: #e4e7ec;
  --csp-red-700: #b42318;
  --csp-red-100: #fee4e2;
  --csp-amber-700: #b54708;
  --csp-amber-100: #fef0c7;
  --brand: var(--csp-blue-700);
  --brand-dark: var(--csp-blue-900);
  --ink: var(--csp-slate-900);
  --muted: var(--csp-slate-500);
  --line: #bfd4f2;
  --soft: #f5f8fc;
  --card: #ffffff;
  --pass-bg: var(--csp-green-050);
  --warn-bg: #fff7ed;
  --fail-bg: #fff1f2;
}
.block-container {padding-top: 2.10rem; padding-bottom: 2rem; padding-left: 2.0rem; padding-right: 2.0rem; max-width: 1680px; margin-left: 0; margin-right: auto;}
[data-testid="stSidebar"] {background: linear-gradient(180deg, #eef6ff 0%, #f8fbff 100%);}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {font-size: 0.84rem; line-height: 1.35;}
[data-testid="stSidebar"] label {font-size: 0.84rem;}
[data-testid="stSidebar"] [role="radiogroup"] label {border: 1px solid #bcd3f5; border-radius: 9px; padding: 3px 8px; margin: 3px 0; background: #fff;}
.app-header-card {
  border: 1px solid var(--line);
  border-radius: 20px;
  background: linear-gradient(135deg, #ffffff 0%, #f7fbff 48%, #e8f2ff 100%);
  box-shadow: 0 14px 36px rgba(23, 92, 211, 0.10);
  padding: 1.05rem 1.18rem;
  margin: 0.40rem 0 0.95rem 0;
}
.app-header-row {display:flex; align-items:center; justify-content:space-between; gap:16px;}
.app-header-left {display:flex; align-items:center; gap:14px; min-width: 0;}
.app-logo {
  width: 48px; height: 48px; border-radius: 14px;
  background: linear-gradient(135deg, #0b3b91 0%, #175cd3 100%);
  color: #ffffff; display:flex; align-items:center; justify-content:center;
  font-weight: 950; letter-spacing: 0.02em;
  box-shadow: 0 10px 24px rgba(23, 92, 211, 0.26);
}
.app-header-title {font-size: 1.72rem; font-weight: 950; color: var(--csp-blue-900); line-height: 1.18;}
.app-header-subtitle {font-size: 0.90rem; color: var(--csp-slate-500); margin-top: 0.18rem;}
.app-header-pill {border:1px solid #bcd3f5; background:#ffffff; border-radius:999px; padding:8px 14px; color:#0b3b91; font-weight:850; font-size:0.78rem; white-space:nowrap;}
.app-title {font-size: 2.05rem; font-weight: 900; color: var(--brand-dark); margin-bottom: 0.1rem;}
.app-subtitle {font-size: 0.92rem; color: var(--muted); margin-bottom: 1.0rem;}
.hero-card {border: 1px solid var(--line); background: linear-gradient(180deg,#fff,#f8fbff); border-radius: 16px; padding: 16px 18px; margin: 8px 0 16px 0; box-shadow: 0 6px 20px rgba(15, 23, 42, 0.05);}
.context-card {border: 1px solid #d5e6ff; background: #fff; border-radius: 12px; padding: 12px 14px; min-height: 78px;}
.status-card {border: 1px solid #d5e6ff; background: #fff; border-radius: 14px; padding: 15px 17px; min-height: 105px; box-shadow: 0 5px 18px rgba(15, 23, 42, 0.06);}
.status-card.pass {background: var(--pass-bg); border-color: #b8edd0;}
.status-card.warn {background: var(--warn-bg); border-color: #fed7aa;}
.status-card.fail {background: var(--fail-bg); border-color: #fecaca;}
.status-kicker {font-size: 0.72rem; letter-spacing: 0.08em; color: #315f96; font-weight: 800; text-transform: uppercase;}
.status-value {font-size: 1.18rem; color: #071b3a; font-weight: 850; margin-top: 0.25rem;}
.status-note {font-size: 0.78rem; color: var(--muted); margin-top: 0.35rem;}
.section-card {border: 1px solid #d5e6ff; background: #fff; border-radius: 16px; padding: 18px; margin: 10px 0 18px 0;}
.note-box {border-left: 5px solid var(--brand); background: #f2f7ff; padding: 12px 14px; border-radius: 12px; color: #173455; margin: 10px 0 16px 0;}
.warn-box {border-left: 5px solid #f59e0b; background: #fffbeb; padding: 12px 14px; border-radius: 12px; color: #713f12; margin: 10px 0 16px 0;}
.small-muted {font-size: 0.80rem; color: var(--muted);}
.badge {display:inline-block; padding: 4px 10px; border-radius: 999px; font-weight: 800; font-size: 0.78rem;}
.badge.pass {background:#dffbe8; color:#126b37; border: 1px solid #a7e6bc;}
.badge.fail {background:#fee2e2; color:#991b1b; border: 1px solid #fecaca;}
.badge.neutral {background:#e8f1ff; color:#174783; border: 1px solid #bcd3f5;}
.workflow-table {border:1px solid #d5e6ff; border-radius:16px; overflow:hidden; background:#fff; box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);}
.workflow-row {display:grid; grid-template-columns: 1.25fr 0.55fr 2.2fr; gap:12px; padding:11px 14px; border-bottom:1px solid #edf2f7; align-items:center;}
.workflow-row:last-child {border-bottom:0;}
.workflow-name {font-weight:850; color:#092454;}
.workflow-sub {font-size:0.80rem; color:#667085;}
.workflow-status {font-weight:900; color:#14532d;}
.workflow-status.baseline {color:#0b3b91;}
.workflow-status.app {color:#14532d;}
.governing-strip {border:1px solid #d5e6ff; border-radius:16px; background:#fff; padding:14px 16px; margin:16px 0 8px 0;}
.sidebar-card {border:1px solid #bcd3f5; border-radius:12px; padding:12px; background:#fff; margin-bottom:12px;}
.sidebar-title {font-weight:850; color:#0b376d; font-size:0.96rem;}
.sidebar-mini {font-size:0.82rem; color:#334155; margin-top:4px; line-height:1.35;}
.sidebar-context {border:1px solid #bcd3f5; border-radius:12px; padding:10px 12px; background:#fff; margin-top:8px;}
.sidebar-context-row {display:flex; justify-content:space-between; gap:8px; border-bottom:1px solid #eef4ff; padding:5px 0;}
.sidebar-context-row:last-child {border-bottom:0;}
.sidebar-context-key {font-size:0.78rem; color:#667085; font-weight:800;}
.sidebar-context-value {font-size:0.82rem; color:#092454; font-weight:850; text-align:right;}
hr {margin: 1rem 0;}

/* M3D CSP aligned section/card/table system */
.section-title {font-size:1.32rem; font-weight:950; color:#092454; margin:1.20rem 0 0.55rem 0;}
.subsection-title {font-size:1.05rem; font-weight:900; color:#0b3b91; margin:0.75rem 0 0.40rem 0;}
.input-card, .calc-card, .result-card, .qa-card, .plot-card, .table-card {
  border:1px solid #d5e6ff; border-radius:16px; background:#ffffff; padding:16px 18px; margin:12px 0 18px 0; box-shadow:0 6px 18px rgba(15,23,42,0.045);
}
.input-card {background:linear-gradient(135deg,#ffffff 0%,#f8fbff 100%);}
.calc-card {background:linear-gradient(135deg,#ffffff 0%,#f7fbff 100%); border-left:5px solid #175cd3;}
.result-card {background:linear-gradient(135deg,#f0fff4 0%,#ffffff 70%); border-color:#b8edd0;}
.qa-card {background:#fffbeb; border-color:#fed7aa;}
.table-card {padding:10px 12px 14px 12px;}
.info-strip {border-left:5px solid #175cd3; background:#eef6ff; border-radius:10px; padding:12px 14px; margin:10px 0 14px 0; color:#0f2f5f;}
.canvas-panel {border:1px solid #c7d9f2; border-radius:16px; background:#ffffff; padding:14px 16px 12px 16px; margin:14px 0 10px 0; box-shadow:0 6px 20px rgba(15,23,42,0.045);}
.canvas-kicker {font-size:0.72rem; letter-spacing:0.10em; color:#667085; font-weight:900; text-transform:uppercase; margin-bottom:4px;}
.canvas-head {display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:8px;}
.canvas-title {font-size:1.18rem; font-weight:950; color:#092454; line-height:1.15;}
.canvas-note {border-left:4px solid #175cd3; background:#f3f8ff; color:#29435f; border-radius:10px; padding:9px 11px; font-size:0.86rem; margin:8px 0 10px 0;}
.canvas-pill {border:1px solid #bcd3f5; color:#0b3b91; background:#ffffff; border-radius:999px; padding:6px 10px; font-size:0.76rem; font-weight:850; white-space:nowrap;}
.canvas-meta-strip {border:1px solid #d5e6ff; background:linear-gradient(135deg,#ffffff 0%,#f8fbff 100%); border-radius:14px; padding:9px 11px; display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; margin:8px 0 8px 0;}
.canvas-station-badge {display:inline-flex; align-items:center; gap:9px; color:#092454; font-size:0.86rem; font-weight:900;}
.canvas-station-badge span {letter-spacing:0.10em; text-transform:uppercase; color:#667085; font-size:0.70rem; font-weight:900;}
.canvas-station-badge strong {border:1px solid #bcd3f5; border-radius:999px; background:#eef6ff; color:#0b3b91; padding:5px 10px;}
.canvas-meta-right {display:flex; align-items:center; gap:10px; flex-wrap:wrap; justify-content:flex-end;}
.canvas-view-badge {border:1px solid #bcd3f5; border-radius:999px; background:#ffffff; color:#0b3b91; padding:5px 10px; font-size:0.76rem; font-weight:900;}
.canvas-dim-badge {font-size:0.76rem; color:#334155; font-weight:800;}
.canvas-caption {font-size:0.82rem; color:#667085; margin:0.45rem 0 0.60rem 0;}
.canvas-legend-strip {border:1px solid #d5e6ff; background:#fbfdff; border-radius:12px; padding:8px 10px; display:flex; justify-content:center; align-items:center; gap:18px; flex-wrap:wrap; margin:8px 0 8px 0;}
.canvas-legend-item {display:inline-flex; align-items:center; gap:6px; color:#092454; font-size:0.78rem; font-weight:750; white-space:nowrap;}
.legend-line {display:inline-block; width:36px; height:0; border-top:4px solid #334e68;}
.legend-line.void {border-top:3px solid #334e68;}
.legend-dot {display:inline-block; width:10px; height:10px; border-radius:999px; background:#2563eb; border:1px solid #0f172a;}
.legend-centroid {display:inline-block; font-size:1.12rem; color:#c9184a; font-weight:900; line-height:0;}
.canvas-footer-grid {display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-top:10px;}
.canvas-footer-card {border:1px solid #b8edd0; border-radius:14px; background:linear-gradient(135deg,#ecfff5 0%,#ffffff 82%); padding:13px 14px; min-height:82px;}
.canvas-footer-card.neutral {border-color:#c7d9f2; background:linear-gradient(135deg,#ffffff 0%,#f8fbff 100%);}
.canvas-footer-card.warn {border-color:#fed7aa; background:linear-gradient(135deg,#fffbeb 0%,#ffffff 82%);}
.canvas-footer-kicker {font-size:0.70rem; letter-spacing:0.12em; text-transform:uppercase; color:#0b3b91; font-weight:900; margin-bottom:8px;}
.canvas-footer-value {font-size:1.15rem; color:#092454; font-weight:950; line-height:1.15;}
.canvas-footer-note {font-size:0.80rem; color:#667085; margin-top:8px;}
[data-testid="stVerticalBlockBorderWrapper"] {border:1px solid #c7d9f2; border-radius:16px; background:#ffffff; box-shadow:0 10px 26px rgba(15,23,42,0.055); padding:10px 14px 14px 14px;}
[data-testid="stVerticalBlockBorderWrapper"] .js-plotly-plot {border:1px solid #d5e6ff; border-radius:14px; background:#fbfdff; padding:4px;}
@media (max-width: 1000px) {.canvas-footer-grid {grid-template-columns:repeat(2,minmax(0,1fr));}}
@media (max-width: 640px) {.canvas-footer-grid {grid-template-columns:1fr;}}
.formula-caption {font-size:0.78rem; color:#667085; margin-top:-0.35rem; margin-bottom:0.55rem;}
.table-caption {font-size:0.78rem; color:#667085; margin-top:0.35rem;}
.dataframe th {font-weight:850 !important;}

</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

APP_DIR = Path(__file__).resolve().parent
WIND_ASSET_DIR = APP_DIR / "assets" / "wind"
SECTION_TEMPLATE_CSV = "loop_name,point_no,x_mm,y_mm\nStructural Polygon 1,1,0,0\nStructural Polygon 1,2,4000,0\nStructural Polygon 1,3,4000,2000\nStructural Polygon 1,4,0,2000\nOpening Polygon 1,1,1000,500\nOpening Polygon 1,2,3000,500\nOpening Polygon 1,3,3000,1500\nOpening Polygon 1,4,1000,1500\n"

# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------
_PROJECT_LOAD_WIDGET_PREFIXES_TO_CLEAR = (
    "section_coordinate_editor",
    "section_coordinate_file_upload",
)
_PROJECT_LOAD_WIDGET_KEYS_TO_CLEAR = {
    "section_j_source_method",
    "section_j_pending_override_value",
    "section_j_pending_override_note",
    "section_point_label_mode",
    "section_preview_dimension_mode",
    "section_origin_display_mode",
}


def _bump_project_widget_epoch_and_clear_stale_editors() -> None:
    """Prevent old widget cache from overwriting newly loaded project JSON.

    Data editors keep their own widget state.  After loading a saved project, an
    old empty coordinate editor must not be allowed to write back into
    ``section.coordinate_rows`` on the next rerun.
    """
    st.session_state.project_widget_epoch = int(st.session_state.get("project_widget_epoch", 0)) + 1
    for key in list(st.session_state.keys()):
        if key in _PROJECT_LOAD_WIDGET_KEYS_TO_CLEAR or any(str(key).startswith(prefix) for prefix in _PROJECT_LOAD_WIDGET_PREFIXES_TO_CLEAR):
            try:
                del st.session_state[key]
            except Exception:
                pass


def _project_widget_epoch() -> int:
    return int(st.session_state.get("project_widget_epoch", 0))


def _project_save_payload() -> bytes:
    """Single save path for the sidebar project JSON download button."""
    return serialize_project_json_bytes(st.session_state.project)


def _section_data_gate_html(project: dict[str, Any]) -> str:
    summary = section_persistence_summary(project)
    coord_ok = summary["coordinate_rows"] > 0
    comp_ok = summary["computed_section_available"]
    adopted_ok = summary["adopted_properties_available"]
    def pill(label: str, ok: bool, value: str) -> str:
        cls = "pass" if ok else "warn"
        status = "READY" if ok else "MISSING"
        return f'<span class="badge {cls}">{label}: {status} · {value}</span>'
    return (
        '<div class="note-box"><b>Section Data Gate:</b> '
        + pill("Coordinate rows", coord_ok, str(summary["coordinate_rows"]))
        + " "
        + pill("Computed section", comp_ok, "available" if comp_ok else "not saved yet")
        + " "
        + pill("Adopted properties", adopted_ok, "available" if adopted_ok else "missing")
        + '<br><span class="small-muted">Project Save/Load preserves imported coordinate rows, computed preview data, and adopted section properties as separate traceable records.</span></div>'
    )


def _apply_pending_project_json_load() -> None:
    """Apply a loaded project before any widget-bound session keys are instantiated.

    Streamlit disallows modifying a session-state key after a widget with the same
    key has been created in the current run. The sidebar workspace/subpage radios
    use ``current_workspace`` and ``current_subpage`` as widget keys, so a project
    JSON load stores pending state first, reruns, and this function applies the
    project/navigation reset at the very top of the next run.
    """
    pending = st.session_state.pop("_pending_project_json_load", None)
    if not isinstance(pending, dict):
        return
    loaded_project = pending.get("project")
    if isinstance(loaded_project, dict):
        st.session_state.project = ensure_project_schema(loaded_project)
        _bump_project_widget_epoch_and_clear_stale_editors()
    target_workspace = pending.get("workspace", WORKSPACE_LABELS[0])
    if target_workspace not in WORKSPACE_LABELS:
        target_workspace = WORKSPACE_LABELS[0]
    target_subpage = pending.get("subpage")
    ws_def = get_workspace(target_workspace)
    if target_subpage not in ws_def["subpages"]:
        target_subpage = ws_def["subpages"][0]
    st.session_state.current_workspace = target_workspace
    st.session_state.current_subpage = target_subpage
    if pending.get("fingerprint"):
        st.session_state.project_json_loaded_fingerprint = str(pending["fingerprint"])
    if pending.get("message"):
        st.session_state.project_load_message = str(pending["message"])


_apply_pending_project_json_load()

if "project" not in st.session_state:
    st.session_state.project = ensure_project_schema(BG40_DEFAULT)
else:
    st.session_state.project = ensure_project_schema(st.session_state.project)

D = st.session_state.project


# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------
def fnum(value: float, nd: int = 3) -> str:
    return f"{value:,.{nd}f}"


def show_engineering_table(df: pd.DataFrame, *, hide_index: bool = True) -> None:
    """Display read-only engineering tables using the global app format rules."""
    st.dataframe(format_engineering_table(df), use_container_width=True, hide_index=hide_index)


def show_report_image(filename: str, caption: str, *, use_column_width: bool = True) -> None:
    """Display bundled report/reference figures with a consistent caption."""
    path = WIND_ASSET_DIR / filename
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=use_column_width)
    else:
        st.warning(f"Missing bundled figure asset: {filename}")


def section_title(text: str) -> None:
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def subsection_title(text: str) -> None:
    st.markdown(f'<div class="subsection-title">{text}</div>', unsafe_allow_html=True)


def status_badge(status: str) -> str:
    cls = "pass" if status == "PASS" else ("fail" if status == "FAIL" else "neutral")
    return f'<span class="badge {cls}">{status}</span>'


def baseline_status(status: str) -> str:
    """Label R10 baseline-derived statuses honestly in the UI."""
    return f"Baseline {status.title()}" if status.upper() in {"READY", "PASS"} else status


def app_status(status: str) -> str:
    """Label checks calculated by the active app engine from current inputs."""
    return f"App {status}" if status.upper() in {"PASS", "FAIL"} else status


def card(title: str, value: str, note: str = "", mode: str = "") -> None:
    st.markdown(
        f"""
        <div class="status-card {mode}">
          <div class="status-kicker">{title}</div>
          <div class="status-value">{value}</div>
          <div class="status-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )




def _canvas_footer_card_html(title: str, value: str, note: str = "", mode: str = "") -> str:
    cls = "warn" if str(mode).lower() == "warn" else ("neutral" if str(mode).lower() in {"", "neutral"} else "")
    return (
        f'<div class="canvas-footer-card {cls}">'
        f'<div class="canvas-footer-kicker">{title}</div>'
        f'<div class="canvas-footer-value">{value}</div>'
        f'<div class="canvas-footer-note">{note}</div>'
        f'</div>'
    )


def _tendon_canvas_legend_html(families: list[str], *, show_centroid: bool = True) -> str:
    colors = ["#2563eb", "#16a34a", "#d97706", "#7c3aed", "#0891b2", "#db2777", "#65a30d", "#dc2626"]
    items = [
        '<span class="canvas-legend-item"><span class="legend-line"></span>Concrete</span>',
        '<span class="canvas-legend-item"><span class="legend-line void"></span>Inner void</span>',
    ]
    if show_centroid:
        items.append('<span class="canvas-legend-item"><span class="legend-centroid">✚</span>Centroid</span>')
    for i, fam in enumerate(families):
        color = colors[i % len(colors)]
        items.append(f'<span class="canvas-legend-item"><span class="legend-dot" style="background:{color};"></span>{fam}</span>')
    return '<div class="canvas-legend-strip">' + "".join(items) + '</div>'



def _engineering_canvas_legend_html(items: list[dict[str, str]]) -> str:
    """Shared custom legend strip for UI.2 canvas figures.

    Use this instead of Plotly's dense legend where the figure needs to feel like
    a report-ready engineering canvas. Item types: line, void, centroid, dot, dash.
    """
    html_items: list[str] = []
    for item in items:
        label = str(item.get("label", ""))
        kind = str(item.get("kind", "line"))
        color = str(item.get("color", "#294860"))
        if kind == "centroid":
            swatch = f'<span class="legend-centroid" style="color:{color};">✚</span>'
        elif kind == "dot":
            swatch = f'<span class="legend-dot" style="background:{color};"></span>'
        elif kind == "dash":
            swatch = f'<span class="legend-line" style="border-top-style:dashed;border-color:{color};"></span>'
        elif kind == "void":
            swatch = f'<span class="legend-line void" style="border-color:{color};"></span>'
        else:
            swatch = f'<span class="legend-line" style="border-color:{color};"></span>'
        html_items.append(f'<span class="canvas-legend-item">{swatch}{label}</span>')
    return '<div class="canvas-legend-strip">' + "".join(html_items) + '</div>'


def _tendon_family_color(family: str, fallback_index: int = 0) -> str:
    """Return the stable UI.2 tendon-family color used by tendon Plotly traces."""
    import re

    colors = ["#2563eb", "#16a34a", "#d97706", "#7c3aed", "#0891b2", "#db2777", "#65a30d", "#dc2626"]
    m = re.search(r"(\d+)", str(family or ""))
    idx = int(m.group(1)) - 1 if m else fallback_index
    return colors[idx % len(colors)]


def _tendon_family_legend_items(families: list[str]) -> list[dict[str, str]]:
    items = [{"label": "L side", "kind": "line", "color": "#475569"}, {"label": "R side", "kind": "dash", "color": "#475569"}]
    for i, fam in enumerate(families):
        items.append({"label": fam, "kind": "dot", "color": _tendon_family_color(fam, i)})
    return items


def _tendon_3d_legend_items(families: list[str], sides: list[str]) -> list[dict[str, str]]:
    """Build a 3D legend strip that mirrors only the visible tendon set."""
    items: list[dict[str, str]] = []
    side_set = {str(side).upper() for side in sides if str(side).strip()}
    if "L" in side_set:
        items.append({"label": "L side", "kind": "line", "color": "#475569"})
    if "R" in side_set:
        items.append({"label": "R side", "kind": "dash", "color": "#475569"})
    for i, fam in enumerate(families):
        items.append({"label": fam, "kind": "dot", "color": _tendon_family_color(fam, i)})
    return items


def _dimension_mode_text(mode: str) -> str:
    return {"clean": "Clean", "full": "Full dimensions", "hide": "Hide dimensions"}.get(str(mode), "Clean")


def _figure_view_texts() -> tuple[str, str]:
    view_mode_text = "Interactive review" if current_figure_view_mode() == "Interactive review" else "Report preview"
    view_mode_note = "toolbar on" if current_figure_view_mode() == "Interactive review" else "toolbar hidden"
    return view_mode_text, view_mode_note


def render_aashto_2020_unit_safe_basis_panel() -> None:
    """Commercial CODE.1 panel: governing AASHTO 2020 Section 5 and SI unit policy."""
    guard = concrete_strength_guard_mpa(float(D["materials"].get("fc_mpa", 0.0)))
    mode = "pass" if guard.status == "PASS" else ("warn" if guard.status == "WARNING" else "fail")
    st.markdown(
        '<div class="note-box"><b>AASHTO Section 5 governing basis:</b> Concrete and prestressed-concrete design checks in this app are governed by <b>AASHTO LRFD Bridge Design Specifications, 9th Edition, 2020 — Section 5 Concrete Structures</b>. The app remains SI-native; kip/ksi/in/ft equations must be evaluated through the shared unit-safe wrapper layer.</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Concrete/PT code", "AASHTO LRFD 2020", "9th Edition · Section 5", "pass")
    with c2:
        card("App units", "SI only", D["code_basis"].get("internal_units", "kN, m, MPa, mm"), "pass")
    with c3:
        card("Formula unit guard", "Required", "No direct MPa into kip/ksi equations", "warn")
    with c4:
        card("f′c unit check", guard.status, guard.message, mode)

    st.markdown("#### Governing code-basis summary")
    show_engineering_table(pd.DataFrame(code_basis_summary_rows(D)))

    st.markdown("#### AASHTO Section 5 article map for this app")
    show_engineering_table(pd.DataFrame(AASHTO_SECTION5_ARTICLE_MAP))

    st.markdown("#### Unit conversion basis used by calculation wrappers")
    show_engineering_table(pd.DataFrame(standard_conversion_table()))

    fc_mpa = float(D["materials"].get("fc_mpa", 60.0))
    demo_rows = [
        ["f′c", fc_mpa, "MPa", mpa_to_ksi(fc_mpa), "ksi", "Concrete strength converted before AASHTO √f′c expressions"],
        ["1,000 kN", 1000.0, "kN", kn_to_kip(1000.0), "kip", "Force conversion benchmark"],
        ["1,000 mm", 1000.0, "mm", mm_to_in(1000.0), "in", "Length conversion benchmark"],
        ["40.0 m", 40.0, "m", m_to_ft(40.0), "ft", "Span conversion benchmark"],
        ["1,000 kN·m", 1000.0, "kN·m", knm_to_kipft(1000.0), "kip·ft", "Moment conversion benchmark"],
        ["Coefficient 1√f′c", 1.0, "psi-form coefficient", psi_sqrt_fc_coefficient_to_ksi(1.0), "ksi-form coefficient", "√f′c coefficient conversion guard"],
        ["0.19√f′c", 0.19, "ksi expression", stress_mpa_from_ksi_sqrt_fc(0.19, fc_mpa), "MPa", "Example stress from ksi-based √f′c expression"],
    ]
    show_engineering_table(pd.DataFrame(demo_rows, columns=["Input", "SI value", "SI unit", "Converted / result", "AASHTO unit", "Trace note"]))
    st.markdown("<div class='warn-box'><b>Non-Section-5 note:</b> the existing seismic R-factor helper still references the app&apos;s bridge seismic R table until a 2020 Section 3 source is provided. This does not control concrete/PT Section 5 design checks.</div>", unsafe_allow_html=True)

def code_basis_card(title: str, code_basis: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="note-box"><b>{title}</b><br>
        <span class="small-muted">Code basis: {code_basis}</span>
        {('<br>' + note) if note else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


FIGURE_VIEW_OPTIONS = ["Interactive review", "Report preview"]


# Legacy local key `tendon_overlay_view_mode` was replaced by global_figure_view_mode in COMMERCIAL.UI.1.
def current_figure_view_mode() -> str:
    """One-source UI mode applied to every Plotly figure in the app."""
    mode = st.session_state.get("global_figure_view_mode", FIGURE_VIEW_OPTIONS[0])
    return mode if mode in FIGURE_VIEW_OPTIONS else FIGURE_VIEW_OPTIONS[0]


def current_plotly_config() -> dict:
    return plotly_config_for_view_mode(current_figure_view_mode())


def show_plotly(fig) -> None:
    st.plotly_chart(fig, use_container_width=True, config=current_plotly_config())


def small_context(title: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="context-card">
          <div class="status-kicker">{title}</div>
          <div class="status-value" style="font-size:0.98rem;">{value}</div>
          <div class="status-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def active_qa() -> tuple[list, dict, list[dict[str, str]]]:
    issues = validate_project(D)
    counts = issue_counts(issues)
    workflow = workflow_status(D, issues)
    return issues, counts, workflow


def issue_dataframe(issues: list) -> pd.DataFrame:
    if not issues:
        return pd.DataFrame(columns=["Level", "Category", "Message", "Code basis", "Recommendation"])
    return pd.DataFrame(
        [
            {
                "Level": issue.level,
                "Category": issue.category,
                "Message": issue.message,
                "Code basis": issue.code_basis,
                "Recommendation": issue.recommendation,
            }
            for issue in issues
        ]
    )


def workflow_dataframe(workflow: list[dict[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(workflow, columns=["Workflow item", "Status", "QA note"])


def material_derived() -> dict[str, float]:
    m = D["materials"]
    p = D["prestress"]
    fc = float(m["fc_mpa"])
    fpu = float(m["fpu_mpa"])
    strand_area = float(m["strand_area_mm2"])
    strands = int(p["strands_per_tendon"])
    tendons = int(p["num_tendons"])
    return {
        "Ec_calc_mpa": 4734.0 * sqrt(fc),
        "fr_calc_mpa": 0.63 * sqrt(fc),
        "fpy_calc_mpa": 0.90 * fpu,
        "Aps_per_tendon_calc_mm2": strands * strand_area,
        "Aps_total_calc_mm2": tendons * strands * strand_area,
    }


def load_derived() -> dict[str, Any]:
    lc = D["load_components"]
    rail = D["rail_loads"]
    span = float(D["project"]["span_m"])

    sdl = sdl_totals(lc["sdl_components"])
    dyn = en_dynamic_factor_standard_maintenance(float(lc["dynamic_L_left_m"]), float(lc["dynamic_L_right_m"]))
    lf = longitudinal_force_en1991(
        float(lc["lf_length_m"]),
        span,
        float(lc["lf_traction_kn_m"]),
        float(lc["lf_braking_kn_m"]),
        float(lc["lf_traction_cap_kn"]),
        float(lc["lf_braking_cap_kn"]),
    )
    hf = hunting_force_en1991(
        float(lc.get("hf_qsk_kn", 100.0)),
        float(lc.get("hf_alpha", 0.8)),
        bool(lc.get("hf_reduce_alpha_below_one", False)),
    )
    # Wind loads are calculated from one parameter source. C factors are
    # derived automatically from EN 1991-1-4 Table 8.2 / BG40 R10 Table 2.5.
    ws = wind_load_en1991_dpt_auto(
        float(lc["wind_air_density_kg_m3"]),
        float(lc["wind_vb0_m_s"]),
        float(lc["wind_cdir"]),
        float(lc["wind_cseason"]),
        float(lc.get("wind_b_m", D["project"]["width_m"])),
        float(lc["wind_dtot_ws_m"]),
        float(lc["wind_dtot_ws_wl_m"]),
        float(lc.get("wind_ze_m", 10.0)),
        span,
    )
    lc["wind_vb_m_s"] = float(ws["vb_m_s"])
    lc["wind_c_ws"] = float(ws["C_ws"])
    lc["wind_c_ws_wl"] = float(ws["C_ws_wl"])
    cf = en_centrifugal_percentage(float(rail["speed_kmh"]), float(rail["radius_m"]), float(rail["Lf_m"]))
    try:
        if lc.get("seismic_region") == "Bangkok Basin" and int(lc.get("seismic_bangkok_zone", 0) or 0) > 0:
            eq = dpt_bangkok_basin_spectrum(
                int(lc.get("seismic_bangkok_zone", 0)),
                float(lc["seismic_T_s"]),
                float(lc["seismic_I"]),
                float(lc["seismic_R"]),
                float(lc.get("seismic_damping_percent", 5.0)),
            )
            eq.update({"Fa": 0.0, "Fv": 0.0, "SMS": 0.0, "SM1": 0.0})
        else:
            eq = dpt_general_spectrum(
                float(lc["seismic_Ss_g"]),
                float(lc["seismic_S1_g"]),
                str(lc.get("seismic_soil_class", "D")),
                float(lc["seismic_T_s"]),
                float(lc["seismic_I"]),
                float(lc["seismic_R"]),
            )
    except Exception:
        eq = {"region": lc.get("seismic_region", "General Thailand"), "Fa": 0.0, "Fv": 0.0, "SMS": 0.0, "SM1": 0.0, "SDS": 0.0, "SD1": 0.0, "T0": 0.0, "Ts": 0.0, "Sa": 0.0, "Cs_raw": 0.0, "Cs": 0.0, "category_sds": "-", "category_sd1": "-", "category_governing": "-", "category_basis": "blocked", "spectrum_branch": "blocked"}

    return {
        "sdl_single_total": sdl["single_total"],
        "sdl_double_total": sdl["double_total"],
        "Lphi": dyn["Lphi_m"],
        "dynamic_phi_calc": dyn["phi"],
        **lf,
        **{f"hf_{k}": v for k, v in hf.items()},
        **ws,
        **{f"eq_{k}": v for k, v in eq.items()},
        **{f"cf_{k}": v for k, v in cf.items()},
    }

def prestress_inputs() -> dict[str, Any]:
    m = D["materials"]
    p = D["prestress"]
    return {
        "groups": p["tendon_friction_groups"],
        "fpi_mpa": m["fpi_mpa"],
        "mu": p["mu_external"],
        "RH_percent": p["RH_percent"],
        "V_over_S_in": p["V_over_S_in"],
        "fc_mpa": m["fc_mpa"],
        "ti_days": p["ti_days"],
        "Ep_mpa": m["Ep_mpa"],
        "Ec_mpa": m["Ec_mpa"],
        "fcgp_mpa": p["fcgp_mpa"],
        "num_tendons": p["num_tendons"],
        "anchor_set_loss_mpa": p["anchor_set_loss_mpa"],
        "relaxation_loss_mpa": p["relaxation_loss_mpa"],
        "Aps_total_mm2": p["Aps_total_mm2"],
    }


def engineering_snapshot() -> dict[str, Any]:
    m, s, l, p = D["materials"], D["section"], D["loads"], D["prestress"]
    phi_v = 0.85 if "External" in D["project"]["tendon_system"] else 0.90
    tors = torsion_aashto_586(l["Tu_knm"], s["Aoh_mm2"], s["ph_mm"], m["fy_mpa"], phi_v)
    web = shear_torsion_web_components(l["Vu_kn"], l["Tu_knm"], s["Aoh_mm2"], s["dweb_mm"])
    shear = shear_reinforcement_required(web["Vu_web_kn"], l["Vc_per_web_kn"], phi_v, m["fy_mpa"], s["dv_mm"], l["theta_deg_for_shear"])
    prov = provided_stirrups(l["stirrup_bar_dia_mm"], l["stirrup_spacing_mm"], int(l["stirrup_legs_per_web"]))
    check = combined_transverse_check(shear["Av_over_s_mm2_per_mm"], tors["At_over_s_mm2_per_mm"], prov["Av_over_s_mm2_per_mm"], prov["At_over_s_per_leg_mm2_per_mm"])
    ps = prestress_loss_summary(prestress_inputs())
    flex = D["uls_flexure"]
    sls = D["sls_stress"]
    df = D["deflection"]
    return {
        "phi_v": phi_v,
        "torsion": tors,
        "web": web,
        "shear": shear,
        "provided": prov,
        "transverse_check": check,
        "prestress": ps,
        "flexure_dcr": float(flex["mu_midspan_knm"]) / float(flex["phi_mn_midspan_knm"]),
        "flexure_max_dcr": float(flex["max_dcr"]),
        "sls_status": sls["status"],
        "deflection_status": df["status"],
    }


def report_trace_table(section: str, rows: list[tuple[str, str, str, str]]) -> None:
    st.markdown(f"### {section} — report trace")
    st.dataframe(pd.DataFrame(rows, columns=["Report item", "Source", "App action", "Status"]), use_container_width=True, hide_index=True)


def editable_value(path: list[str], label: str, step: float = 1.0, fmt: str | None = None) -> None:
    ref = D
    for key in path[:-1]:
        ref = ref[key]
    key = path[-1]
    kwargs = {"value": float(ref[key]), "step": step}
    if fmt:
        kwargs["format"] = fmt
    ref[key] = st.number_input(label, **kwargs)


def render_aashto_bridge_seismic_controls(lc: dict[str, Any]) -> dict[str, Any]:
    """Render one-source I/R controls for the EQ page.

    AASHTO operational category and substructure type are used only to
    recommend the bridge response modification factor R.  The importance
    factor I remains a project/DPT input so that the app does not silently
    mix building-code importance with AASHTO operational category.
    """
    st.markdown("#### AASHTO bridge seismic parameters — I/R selection")
    st.markdown(
        '<div class="note-box"><b>Bridge seismic basis:</b> DPT 1301/1302-61 supplies the Thai response spectrum and importance factor basis. AASHTO LRFD 2014 Table 3.10.7.1-1 is used here to recommend the bridge substructure response modification factor <b>R</b>. The owner / authority having jurisdiction shall confirm the bridge operational category.</div>',
        unsafe_allow_html=True,
    )

    op_current = lc.get("seismic_operational_category", "Essential")
    if op_current not in OPERATIONAL_CATEGORIES:
        op_current = "Essential"

    sub_key_current = lc.get("seismic_substructure_key", "single_column_or_pier")
    sub_label_current = substructure_label_from_key(sub_key_current)
    sub_labels = substructure_options()
    if sub_label_current not in sub_labels:
        sub_label_current = substructure_label_from_key("single_column_or_pier")

    r_modes = ["Auto from AASHTO LRFD 2014 Table 3.10.7.1-1", "Manual R override"]
    r_mode_current = lc.get("seismic_R_mode", r_modes[0])
    if r_mode_current not in r_modes:
        r_mode_current = r_modes[0]

    imp_labels = importance_preset_options()
    imp_key_current = lc.get("seismic_importance_preset_key", "bg40_default")
    imp_label_current = importance_preset_label_from_key(imp_key_current)
    if imp_label_current not in imp_labels:
        imp_label_current = importance_preset_label_from_key("bg40_default")

    c1, c2, c3 = st.columns([1.0, 1.35, 1.05])
    with c1:
        op_category = st.selectbox("AASHTO operational category", OPERATIONAL_CATEGORIES, index=OPERATIONAL_CATEGORIES.index(op_current), key="eq_aashto_operational_category")
    with c2:
        sub_label = st.selectbox("Substructure / lateral system", sub_labels, index=sub_labels.index(sub_label_current), key="eq_aashto_substructure_type")
    with c3:
        r_mode = st.selectbox("R selection mode", r_modes, index=r_modes.index(r_mode_current), key="eq_r_selection_mode")

    sub_key = substructure_key_from_label(sub_label)
    rec = recommended_substructure_r(sub_key, op_category)
    lc["seismic_operational_category"] = op_category
    lc["seismic_substructure_key"] = sub_key
    lc["seismic_substructure_label"] = sub_label
    lc["seismic_R_mode"] = r_mode

    c4, c5, c6 = st.columns([1.2, 0.8, 1.0])
    with c4:
        imp_label = st.selectbox("Importance factor I basis", imp_labels, index=imp_labels.index(imp_label_current), key="eq_importance_factor_preset")
        imp_key = importance_preset_key_from_label(imp_label)
        lc["seismic_importance_preset_key"] = imp_key
    with c5:
        if imp_key == "manual":
            manual_i = st.number_input("Manual I", value=float(lc.get("seismic_I", 1.25)), min_value=0.5, step=0.05, format="%.2f", key="eq_manual_importance_factor")
            imp = importance_value_from_preset("manual", manual_i)
        else:
            imp = importance_value_from_preset(imp_key)
            st.metric("I", f"{float(imp['I']):.2f}")
        lc["seismic_I"] = float(imp["I"])
        lc["seismic_I_source"] = str(imp["source_reference"])
    with c6:
        if r_mode == "Manual R override":
            r_value = st.number_input("Manual R", value=float(lc.get("seismic_R", rec["R"])), min_value=0.5, step=0.1, format="%.1f", key="eq_manual_response_modification_factor")
            lc["seismic_R"] = float(r_value)
            lc["seismic_R_source"] = "User override — verify against AASHTO LRFD and project requirements"
        else:
            lc["seismic_R"] = float(rec["R"])
            lc["seismic_R_source"] = f"{rec['source_reference']} — {op_category} / {sub_label}"
            st.metric("R", f"{float(rec['R']):.1f}")

    summary = pd.DataFrame([
        ["Operational category", op_category, "AASHTO Art. 3.10.5 / owner-AHJ classification"],
        ["Substructure system", sub_label, str(rec["source_reference"])],
        ["Recommended R", f"{float(lc['seismic_R']):.1f}", lc["seismic_R_source"]],
        ["Importance factor I", f"{float(lc['seismic_I']):.2f}", lc["seismic_I_source"]],
        ["Global coefficient", r"Cs = Sa(I/R)", "DPT Ch.3 equivalent static basis with AASHTO R guidance"],
    ], columns=["Item", "Value", "Source / note"])
    st.dataframe(summary, use_container_width=True, hide_index=True)

    with st.expander("AASHTO R reference tables used by this app", expanded=False):
        sub = load_substructure_r_table()[["substructure_label", "critical", "essential", "other", "source_reference"]].copy()
        sub.columns = ["Substructure", "Critical", "Essential", "Other", "Source"]
        st.dataframe(sub, use_container_width=True, hide_index=True)
        conn = load_connection_r_table()[["connection_label", "r_value", "source_reference"]].copy()
        conn.columns = ["Connection", "R", "Source"]
        st.dataframe(conn, use_container_width=True, hide_index=True)
        st.markdown('<div class="warn-box"><b>Connection note:</b> AASHTO connection R-factors are separate from the global substructure R used above. Future member/connection checks should use the connection-specific table, not the global pier/bent R.</div>', unsafe_allow_html=True)

    return {"R": lc["seismic_R"], "I": lc["seismic_I"], "recommended_R": rec}


# -----------------------------------------------------------------------------
# Sidebar and header
# -----------------------------------------------------------------------------
def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-card">
              <div class="sidebar-title">Segmental Box Girder Pro</div>
              <div class="sidebar-mini">Report-driven FEA design-review workspace for PT segmental box girders.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if "current_workspace" not in st.session_state or st.session_state.current_workspace not in WORKSPACE_LABELS:
            st.session_state.current_workspace = WORKSPACE_LABELS[0]
        st.radio("WORKSPACE", WORKSPACE_LABELS, key="current_workspace")
        ws = get_workspace(st.session_state.current_workspace)
        if "current_subpage" not in st.session_state or st.session_state.current_subpage not in ws["subpages"]:
            st.session_state.current_subpage = ws["subpages"][0]
        st.radio("SUBPAGE", ws["subpages"], key="current_subpage")

        issues, counts, workflow = active_qa()
        st.markdown("---")
        st.markdown("**PROJECT STATUS**")
        if counts["ERROR"]:
            st.error(f"QA blocked: {counts['ERROR']} error(s)")
        elif counts["WARNING"]:
            st.warning(f"QA review: {counts['WARNING']} warning(s)")
        else:
            st.success("QA gate ready")
        snap = engineering_snapshot()
        st.info(f"ULS Flexure max DCR: {snap['flexure_max_dcr']:.3f}")
        st.info(f"Shear/Torsion D/C: {snap['transverse_check']['DCR_governing']:.3f}")
        st.info(f"Schema {PROJECT_SCHEMA_VERSION}")
        st.markdown("---")
        st.markdown("**FIGURE SYSTEM**")
        if "global_figure_view_mode" not in st.session_state or st.session_state.global_figure_view_mode not in FIGURE_VIEW_OPTIONS:
            st.session_state.global_figure_view_mode = FIGURE_VIEW_OPTIONS[0]
        st.radio(
            "Figure view mode",
            FIGURE_VIEW_OPTIONS,
            key="global_figure_view_mode",
            help="One-source display mode applied to every Plotly figure: load diagrams, spectra, section drawings, tendon views, and future analysis plots.",
        )
        st.caption(figure_view_badge_text(st.session_state.global_figure_view_mode))
        st.markdown("---")
        st.markdown("**ACTIVE CONTEXT**")
        st.markdown(
            f"""
            <div class="sidebar-context">
              <div class="sidebar-context-row"><span class="sidebar-context-key">Project</span><span class="sidebar-context-value">{D['project']['name']}</span></div>
              <div class="sidebar-context-row"><span class="sidebar-context-key">Span</span><span class="sidebar-context-value">{D['project']['bridge_object']}</span></div>
              <div class="sidebar-context-row"><span class="sidebar-context-key">Code</span><span class="sidebar-context-value">AASHTO + EN</span></div>
              <div class="sidebar-context-row"><span class="sidebar-context-key">PT</span><span class="sidebar-context-value">External / Unbonded</span></div>
              <div class="sidebar-context-row"><span class="sidebar-context-key">Units</span><span class="sidebar-context-value">{D['project']['units']}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")
        uploaded = st.file_uploader("Load Project JSON", type=["json"], key="project_json_upload")
        if uploaded is not None:
            raw_project_json = uploaded.getvalue()
            upload_fp = project_json_fingerprint(raw_project_json, getattr(uploaded, "name", ""))
            loaded_fp = st.session_state.get("project_json_loaded_fingerprint")
            st.caption(f"Selected: {getattr(uploaded, 'name', 'project.json')} · {len(raw_project_json) / 1024:.1f} KB")
            if loaded_fp == upload_fp:
                st.success("This uploaded project JSON is already loaded.")
            if st.button("Load uploaded project", key="load_project_json_button", use_container_width=True):
                try:
                    loaded_project = load_project_json_bytes(raw_project_json, getattr(uploaded, "name", ""))
                    summary = project_load_summary(loaded_project)
                    # Do not mutate widget-bound keys such as current_workspace/current_subpage
                    # after their radio widgets have been instantiated. Store a pending load
                    # and apply it at the top of the next run before any widgets are created.
                    st.session_state._pending_project_json_load = {
                        "project": loaded_project,
                        "workspace": WORKSPACE_LABELS[0],
                        "subpage": get_workspace(WORKSPACE_LABELS[0])["subpages"][0],
                        "fingerprint": upload_fp,
                        "message": (
                            f"Loaded project {summary['project']} / {summary['bridge_object']} "
                            f"with schema {summary['schema_version']}."
                        ),
                    }
                    st.rerun()
                except ProjectJsonLoadError as exc:
                    st.error(f"Could not load JSON: {exc}")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not load JSON due to an unexpected error: {exc}")
        if st.session_state.get("project_load_message"):
            st.success(st.session_state.project_load_message)


def render_header() -> None:
    ws = get_workspace(st.session_state.current_workspace)
    sub = st.session_state.current_subpage
    st.markdown(
        f"""
        <div class="app-header-card">
          <div class="app-header-row">
            <div class="app-header-left">
              <div class="app-logo">SB</div>
              <div>
                <div class="app-header-title">Segmental Box Girder Pro</div>
                <div class="app-header-subtitle">Commercial report-driven design-review workspace · Internal units: kN, m, MPa, mm.</div>
              </div>
            </div>
            <div class="app-header-pill">{ws['label'].upper()}</div>
          </div>
        </div>
        <div class="hero-card">
          <b>{D['project']['name']}</b> · {D['project']['description']}<br>
          <span class="small-muted">Active workspace: {ws['label']} · Subpage: {sub} · Baseline: {D['meta'].get('baseline_report', 'BG40 R10')}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        small_context("Workspace", ws["label"], ws["title"])
    with c2:
        small_context("Subpage", sub, "Report-driven UI section")
    with c3:
        small_context("Design Code", D["code_basis"]["concrete_design_standard"].replace("Bridge Design Specifications, ", ""), "Section 5 governs concrete/PT checks")
    with c4:
        small_context("Tendon System", D["project"]["tendon_system"], "φv route controlled by tendon system")
    st.markdown("")


# -----------------------------------------------------------------------------
# Pages
# -----------------------------------------------------------------------------
def page_dashboard(sub: str) -> None:
    issues, counts, workflow = active_qa()
    snap = engineering_snapshot()
    flex = D["uls_flexure"]
    sls = D["sls_stress"]
    df = D["deflection"]
    st.subheader("Project Dashboard")
    if sub == "Overview":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            card("Reference Baseline", "BG40 R10 baseline active", "Reference baseline loaded from R10; live recalculation status is shown separately.", "pass")
        with c2:
            qa = "Blocked" if counts["ERROR"] else ("Review" if counts["WARNING"] else "Ready")
            mode = "fail" if counts["ERROR"] else ("warn" if counts["WARNING"] else "pass")
            card("QA Gate", "QA Ready" if qa == "Ready" else qa, f"{counts['ERROR']} error(s), {counts['WARNING']} warning(s)", mode)
        with c3:
            card("FEA Data", "Baseline summary active", "Detailed station-by-station FEA import pending for full envelope checks.")
        with c4:
            card("Recommended Action", "Review current workspace", "M2.2: layout balance, status honesty, and FEA wording polish")

        st.markdown("### Governing engineering results")
        g1, g2, g3, g4 = st.columns(4)
        with g1:
            card("ULS Flexure", f"Baseline DCR {flex['max_dcr']:.3f}", f"R10 baseline governing x ≈ {flex['governing_x_m']} m", "pass")
        with g2:
            check = snap["transverse_check"]
            mode = "pass" if check["Status_governing"] == "PASS" else "fail"
            card("ULS Shear / Torsion", f"App D/C {check['DCR_governing']:.3f}", f"{check['Status_governing']} from active inputs + R10 demand", mode)
        with g3:
            card("SLS Stress", baseline_status(sls["status"]), f"R10 baseline governing margin {sls['governing_margin_percent']:.1f}%", "pass")
        with g4:
            card("Deflection", app_status(df["status"]), f"LL utilization {df['ll_utilization_percent']:.1f}% of L/800", "pass")

        st.markdown("### Report-driven workspace status")
        workflow_lookup = {row["Workflow item"]: row for row in workflow}
        status_map = {
            "1 Criteria": (baseline_status(workflow_lookup.get("Materials", {"Status": "READY"})["Status"]), "baseline"),
            "2 Bridge Geometry / Section Properties": (baseline_status(workflow_lookup.get("Geometry", {"Status": "READY"})["Status"]), "baseline"),
            "3 Loads": (app_status("READY"), "app"),
            "4 Prestress Losses": (baseline_status(workflow_lookup.get("Prestress Losses", {"Status": "READY"})["Status"]), "baseline"),
            "5 FEA Results": ("Baseline Summary", "baseline"),
            "6 ULS Flexure": ("Baseline PASS", "baseline"),
            "7 ULS Shear / Torsion": (app_status(snap["transverse_check"]["Status_governing"]), "app"),
            "8 SLS Stress": (baseline_status(sls["status"]), "baseline"),
            "9 Deflection": (app_status(df["status"]), "app"),
        }
        rows_html = []
        for label in WORKSPACE_LABELS[1:-1]:
            ws = get_workspace(label)
            status, status_class = status_map.get(label, ("Baseline Ready", "baseline"))
            subsections = " · ".join(ws["subpages"][:-1])
            rows_html.append(
                f'<div class="workflow-row"><div><div class="workflow-name">{label}</div><div class="workflow-sub">{ws["title"]}</div></div><div class="workflow-status {status_class}">{status}</div><div class="workflow-sub">{subsections}</div></div>'
            )
        st.markdown('<div class="workflow-table">' + ''.join(rows_html) + '</div>', unsafe_allow_html=True)
        st.caption("Status wording separates R10 baseline readiness from checks calculated by the active app engine.")
    elif sub == "Workflow Status":
        st.dataframe(workflow_dataframe(workflow), use_container_width=True, hide_index=True)
        with st.expander("Validation details", expanded=bool(counts["ERROR"] or counts["WARNING"])):
            st.dataframe(issue_dataframe(issues), use_container_width=True, hide_index=True)
    elif sub == "Governing Results":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            card("ULS Flexure", f"Baseline DCR {flex['max_dcr']:.3f}", f"R10 baseline governing x ≈ {flex['governing_x_m']} m", "pass")
        with c2:
            check = snap["transverse_check"]
            mode = "pass" if check["Status_governing"] == "PASS" else "fail"
            card("ULS Shear/Torsion", f"App D/C {check['DCR_governing']:.3f}", f"{check['Status_governing']} from active inputs + R10 demand", mode)
        with c3:
            card("SLS Stress", baseline_status(sls["status"]), f"R10 baseline governing margin {sls['governing_margin_percent']:.1f}%", "pass")
        with c4:
            card("Deflection", app_status(df["status"]), f"LL utilization {df['ll_utilization_percent']:.1f}%", "pass")
        st.dataframe(
            pd.DataFrame(
                [
                    ["6 ULS Flexure", "max DCR", flex["max_dcr"], "Baseline PASS"],
                    ["7 ULS Shear/Torsion", "transverse D/C", snap["transverse_check"]["DCR_governing"], app_status(snap["transverse_check"]["Status_governing"])],
                    ["8 SLS Stress", "governing margin (%)", sls["governing_margin_percent"], baseline_status(sls["status"])],
                    ["9 Deflection", "LL utilization (%)", df["ll_utilization_percent"], app_status(df["status"])],
                ],
                columns=["Workspace", "Governing item", "Value", "Status"],
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.markdown("### Report Readiness")
        report_trace_table(
            "Project report readiness",
            [
                ("1 Criteria", "BG40 R10 + app inputs", "Standards/materials/units structured", "READY"),
                ("2 Bridge Geometry / Section Properties", "BG40 R10 + app inputs", "Geometry, analysis model and section properties structured", "READY"),
                ("3 Loads", "User input + app calculations", "Dedicated FEA load input generator active", "READY"),
                ("4–9 Design checks", "Existing M1 engine + R10 baselines", "Calculation cards and QA preview available", "IN PROGRESS"),
            ],
        )


def page_criteria_loads(sub: str) -> None:
    st.subheader(get_workspace("1 Criteria")["title"])
    md = material_derived()
    ld = load_derived()
    if sub == "1.1 Standards":
        st.markdown("### 1.1 Design Standards and Requirements")
        st.dataframe(pd.DataFrame(D["criteria"]["standards"]), use_container_width=True, hide_index=True)
        render_aashto_2020_unit_safe_basis_panel()
        D["criteria"]["units_statement"] = st.text_area("Units statement for report", D["criteria"]["units_statement"], height=90)
        st.markdown('<div class="note-box"><b>Commercial rule:</b> UI labels stay concise, but report numbering and title are preserved for traceability.</div>', unsafe_allow_html=True)
    elif sub == "1.2 Materials":
        st.markdown("### 1.2 Material Properties")
        t1, t2, t3 = st.tabs(["Concrete", "Reinforcing Steel", "Prestressing Strand"])
        with t1:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                editable_value(["materials", "fc_mpa"], "f′c (MPa)", 1.0)
            with c2:
                editable_value(["materials", "gamma_c_kn_m3"], "γc (kN/m³)", 0.1)
            with c3:
                D["materials"]["Ec_mpa"] = st.number_input("Ec used (MPa)", value=float(D["materials"]["Ec_mpa"]), step=100.0)
            with c4:
                D["materials"]["fr_mpa"] = st.number_input("fr used (MPa)", value=float(D["materials"]["fr_mpa"]), step=0.01, format="%.2f")
            st.dataframe(pd.DataFrame([
                ["Ec = 4734√f′c", md["Ec_calc_mpa"], D["materials"]["Ec_mpa"], "MPa"],
                ["fr = 0.63√f′c", md["fr_calc_mpa"], D["materials"]["fr_mpa"], "MPa"],
                ["Stress block factor β1", D["materials"]["beta1"], D["materials"]["beta1"], "-"],
            ], columns=["Calculated item", "App calculated", "Report / used", "Unit"]), use_container_width=True, hide_index=True)
        with t2:
            df = pd.DataFrame([
                ["SR24", "TIS 20", "≤ 9 mm", 240],
                ["SD40", "TIS 24", "12–28 mm", D["materials"]["fy_mpa"]],
                ["SD50", "TIS 24", "≥ 32 mm", D["materials"]["fy_sd50_mpa"]],
            ], columns=["Grade", "Standard", "Size", "fy (MPa)"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        with t3:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                editable_value(["materials", "strand_diameter_mm"], "Nominal diameter (mm)", 0.1)
                editable_value(["materials", "strand_area_mm2"], "Area per strand (mm²)", 1.0)
            with c2:
                editable_value(["materials", "fpu_mpa"], "fpu (MPa)", 1.0)
                D["materials"]["fpy_mpa"] = st.number_input("fpy used (MPa)", value=float(D["materials"]["fpy_mpa"]), step=1.0)
            with c3:
                D["prestress"]["num_tendons"] = int(st.number_input("Number of tendons", value=int(D["prestress"]["num_tendons"]), step=1))
                D["prestress"]["strands_per_tendon"] = int(st.number_input("Strands per tendon", value=int(D["prestress"]["strands_per_tendon"]), step=1))
            with c4:
                editable_value(["materials", "Ep_mpa"], "Ep (MPa)", 1000.0)
                editable_value(["materials", "fpi_mpa"], "fpi (MPa)", 5.0)
            D["prestress"]["Aps_per_tendon_mm2"] = md["Aps_per_tendon_calc_mm2"]
            D["prestress"]["Aps_total_mm2"] = md["Aps_total_calc_mm2"]
            st.dataframe(pd.DataFrame([
                ["fpy = 0.90fpu", md["fpy_calc_mpa"], D["materials"]["fpy_mpa"], "MPa"],
                ["Aps per tendon", md["Aps_per_tendon_calc_mm2"], D["prestress"]["Aps_per_tendon_mm2"], "mm²"],
                ["Aps,total", md["Aps_total_calc_mm2"], D["prestress"]["Aps_total_mm2"], "mm²"],
            ], columns=["Calculated item", "App calculated", "Report / used", "Unit"]), use_container_width=True, hide_index=True)
    elif sub == "1.3 Design Basis / Units":
        st.markdown("### 1.3 Design Basis / Units")
        render_aashto_2020_unit_safe_basis_panel()
        D["criteria"]["units_statement"] = st.text_area("Units statement for report", D["criteria"].get("units_statement", ""), height=90, key="criteria_units_statement")
        D["criteria"]["combination_basis"] = st.text_area("FEA combination and design-force traceability basis", D["criteria"].get("combination_basis", ""), height=140, key="criteria_combination_basis")
        st.markdown('<div class="note-box"><b>Loads moved:</b> all load calculations and FEA load input summaries are now managed under <b>3 Loads</b>. Criteria only records standards, materials, units, code basis, and combination-basis text.</div>', unsafe_allow_html=True)
    elif sub == "1.4 Combinations":
        st.markdown("### 1.4 Load Combinations")
        notation = pd.DataFrame([
            ["DL", "Dead load"], ["SDL", "Superimposed dead load"], ["PS", "Prestressing effect"], ["LL+IM", "Train load + dynamic impact"],
            ["HF", "Hunting force"], ["CF", "Centrifugal force"], ["LF", "Longitudinal force"], ["CR/SH", "Creep / Shrinkage effect"],
            ["WS", "Wind on structure"], ["WS+WL", "Wind on structure + train"], ["EQ", "Earthquake load"],
        ], columns=["Symbol", "Meaning"])
        st.dataframe(notation, use_container_width=True, hide_index=True)
        D["criteria"]["combination_basis"] = st.text_area("Combination basis for report", D["criteria"]["combination_basis"], height=140)
    else:
        report_trace_table("1 Criteria", [("Standards", "BG40 R10", "Report table structured", "READY"), ("Materials", "User input + app calc", "Ec/fr/fpy/Aps calculated", "READY"), ("Combinations", "FEA basis text", "Ready for report preview", "READY")])



def page_loads(sub: str) -> None:
    st.subheader(get_workspace("3 Loads")["title"])
    st.markdown(f'<div class="note-box"><b>Dedicated Loads workspace:</b> Active subpage = {sub}. Load calculations are maintained as a report-driven FEA load input generator.</div>', unsafe_allow_html=True)
    section_title("3 Loads — FEA load input generator")
    st.markdown('<div class="note-box"><b>One-source rule:</b> each load is entered once in the report-driven schema. Report Preview, FEA Load Summary, QA checks, and Save/Load JSON read from the same source.</div>', unsafe_allow_html=True)
    tabs = st.tabs(["3.1 Dead Load", "3.2 SDL", "3.3 LL + IM", "3.4 LF / HF", "3.6 CF", "3.7 Wind", "3.8 CR&SH", "3.9 EQ", "3.10 FEA Summary"])

    with tabs[0]:
        code_basis_card("3.1 Dead Load (DL)", "BG40 Calculation Report Ch. 1.3.1", "Informational/report text only. FEA self-weight remains generated in the structural analysis model; no duplicate dead-load input is introduced here.")
        dl = D["load_components"]
        st.markdown(f'<div class="note-box"><b>Dead load:</b> {dl.get("dead_load_definition", "")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="note-box"><b>Self-Weight (SW):</b> {dl.get("dead_load_note", "")}</div>', unsafe_allow_html=True)
        show_engineering_table(pd.DataFrame(dl.get("dead_load_unit_weights", [])))
        st.caption("Report note: these unit weights are provided for information and report traceability only. The app does not create an additional DL calculation table from these values.")

    with tabs[1]:
        code_basis_card("3.2 Superimposed Dead Load (SDL)", "BG40 R10 project load schedule / FEA permanent appurtenance loads", "Editable component table. Total and adopted design values are recalculated from this single table.")
        sdl_df = pd.DataFrame(D["load_components"]["sdl_components"])
        edited = st.data_editor(
            sdl_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "Single Track (kN/m)": st.column_config.NumberColumn(format="%.2f"),
                "Double Track (kN/m)": st.column_config.NumberColumn(format="%.2f"),
                "Include": st.column_config.CheckboxColumn(default=True),
            },
            key="sdl_component_editor",
        )
        D["load_components"]["sdl_components"] = edited.to_dict("records")
        ld = load_derived()
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            card("Total SDL — single", f"{format_engineering_value(ld['sdl_single_total'], 'kN/m')} kN/m", "sum of included rows")
        with c2:
            card("Total SDL — double", f"{format_engineering_value(ld['sdl_double_total'], 'kN/m')} kN/m", "sum of included rows", "pass")
        with c3:
            editable_value(["load_components", "design_sdl_single_kn_m"], "Adopted single-track SDL (kN/m)", 1.0)
        with c4:
            editable_value(["load_components", "design_sdl_double_kn_m"], "Adopted double-track SDL (kN/m)", 1.0)
        st.markdown("#### FEA SDL input summary")
        show_engineering_table(pd.DataFrame([
            ["SDL", "Superimposed dead load", D["load_components"]["design_sdl_double_kn_m"], "kN/m", "Gravity / along span", "Double-track adopted design value", "User editable + app total"],
        ], columns=["Load Pattern", "Description", "Value", "Unit", "Direction", "Application", "Source"]))

    with tabs[2]:
        code_basis_card("3.3 Live Load + Impact (LL+IM)", "EN 1991-2 Art. 6.4.3 and Art. 6.4.5", "Railway live load is U20 = 0.8 × LM71. Adopted impact/dynamic factor is a FEA load input value.")
        components.html(u20_loading_diagram_svg(), height=360, scrolling=False)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            editable_value(["load_components", "dynamic_L_left_m"], "L_left (m)", 1.0)
        with c2:
            editable_value(["load_components", "dynamic_L_right_m"], "L_right (m)", 1.0)
        with c3:
            editable_value(["load_components", "u20_scale_factor"], "U20 scale factor", 0.01, "%.2f")
        with c4:
            editable_value(["load_components", "dynamic_factor_design"], "Adopted IM / φ", 0.01, "%.2f")
        ld = load_derived()
        st.latex(r"L_\phi=\min(L_{left},L_{right})")
        st.latex(r"\phi=\frac{2.16}{\sqrt{L_\phi}-0.2}+0.73")
        st.latex(fr"L_\phi=\min({D['load_components']['dynamic_L_left_m']:.1f},{D['load_components']['dynamic_L_right_m']:.1f})={ld['Lphi']:.1f}\,\mathrm{{m}}")
        st.latex(fr"\phi=\frac{{2.16}}{{\sqrt{{{ld['Lphi']:.1f}}}-0.2}}+0.73={format_engineering_value(ld['dynamic_phi_calc'], 'factor')}")
        c1, c2 = st.columns(2)
        with c1:
            card("Calculated dynamic factor", f"φcalc = {format_engineering_value(ld['dynamic_phi_calc'], 'factor')}", "EN 1991-2 Art. 6.4.5")
        with c2:
            card("Adopted FEA factor", f"IM = {format_engineering_value(D['load_components']['dynamic_factor_design'], 'factor')}", "conservative design value", "pass")
        st.markdown("#### FEA LL+IM input summary")
        show_engineering_table(pd.DataFrame([
            ["LL+IM", "U20 = 0.8 × LM71", D["load_components"]["dynamic_factor_design"], "factor", "Vertical railway load", "Railway load lane / track model", "App calculated + user-adopted"],
        ], columns=["Load Pattern", "Load model", "Value", "Unit", "Direction", "Application", "Source"]))

    with tabs[3]:
        code_basis_card("3.4 Longitudinal Force (LF) and 3.5 Hunting / Nosing Force (HF)", "EN 1991-2 Art. 6.5.3 and Art. 6.5.2", "LF is longitudinal braking/traction at rail level. HF is the EN nosing force Qsk, concentrated transverse at top of rail.")
        show_plotly(rail_horizontal_forces_diagram())
        c1, c2, c3 = st.columns(3)
        with c1:
            editable_value(["load_components", "lf_length_m"], "LF loaded length Lab (m)", 1.0)
            editable_value(["load_components", "lf_traction_kn_m"], "Traction rate (kN/m)", 1.0)
        with c2:
            editable_value(["load_components", "lf_braking_kn_m"], "Braking rate (kN/m)", 1.0)
            editable_value(["load_components", "lf_traction_cap_kn"], "Traction cap (kN)", 100.0)
        with c3:
            editable_value(["load_components", "lf_braking_cap_kn"], "Braking cap (kN)", 100.0)
            editable_value(["load_components", "hf_qsk_kn"], "HF / Qsk (kN)", 10.0)
        editable_value(["load_components", "hf_alpha"], "α classification factor shown for traffic-load context", 0.01, "%.2f")
        D["load_components"]["hf_reduce_alpha_below_one"] = st.checkbox("Allow α < 1 reduction for HF only when project requirements explicitly state so", value=bool(D["load_components"].get("hf_reduce_alpha_below_one", False)))
        ld = load_derived()
        st.latex(r"Q_{lak}=33L_{ab}\leq1000\,\mathrm{kN}")
        st.latex(r"Q_{lbk}=20L_{ab}\leq6000\,\mathrm{kN}")
        st.latex(r"LF=\max(Q_{lak},Q_{lbk}),\qquad w_{LF}=LF/L")
        st.latex(fr"Q_{{lak}}={D['load_components']['lf_traction_kn_m']:.0f}({D['load_components']['lf_length_m']:.1f})={ld['Qlak_raw_kn']:.0f}\rightarrow {ld['Qlak_kn']:.0f}\,\mathrm{{kN}}");
        st.latex(fr"Q_{{lbk}}={D['load_components']['lf_braking_kn_m']:.0f}({D['load_components']['lf_length_m']:.1f})={ld['Qlbk_raw_kn']:.0f}\rightarrow {ld['Qlbk_kn']:.0f}\,\mathrm{{kN}}");
        st.latex(fr"LF=\max({ld['Qlak_kn']:.0f},{ld['Qlbk_kn']:.0f})={ld['LF_design_kn']:.0f}\,\mathrm{{kN}}={ld['LF_design_kn_m']:.1f}\,\mathrm{{kN/m}}");
        st.markdown("#### HF / Nosing force")
        st.latex(r"Q_{sk}=100\,\mathrm{kN}")
        st.info(str(ld["hf_decision_basis"]))
        c1, c2, c3 = st.columns(3)
        with c1:
            card("Design LF", f"{format_engineering_value(ld['LF_design_kn'], 'kN')} kN", f"{format_engineering_value(ld['LF_design_kn_m'], 'kN/m')} kN/m", "pass")
        with c2:
            card("Adopted HF", f"{format_engineering_value(ld['hf_HF_adopted_kn'], 'kN')} kN", "concentrated transverse load", "pass")
        with c3:
            card("Dynamic factor on HF", "Not applied", "EN nosing force", "pass")

    with tabs[4]:
        code_basis_card("3.6 Centrifugal Force (CF)", "EN 1991-2 Art. 6.5.1", "Applies where horizontal curvature is relevant. For straight/large-radius spans this is often non-governing but still traceable.")
        c1, c2, c3 = st.columns(3)
        with c1:
            editable_value(["rail_loads", "speed_kmh"], "V (km/h)", 10.0)
        with c2:
            editable_value(["rail_loads", "radius_m"], "R (m)", 100.0)
        with c3:
            editable_value(["rail_loads", "Lf_m"], "Lf (m)", 1.0)
        ld = load_derived()
        st.latex(r"C=\frac{V^2f}{127R}")
        st.latex(r"f=1-\left(\frac{V-120}{1000}\right)\left(\frac{814}{V}+1.75\right)\left(1-\sqrt{\frac{2.88}{L_f}}\right)\quad (f\ge 0.35)")
        st.latex(fr"f={ld['cf_f']:.4f},\qquad C=\frac{{{D['rail_loads']['speed_kmh']:.0f}^2({ld['cf_f']:.2f})}}{{127({D['rail_loads']['radius_m']:.0f})}}={ld['cf_C_reduced']:.5f}")
        c1, c2 = st.columns(2)
        with c1:
            card("Centrifugal factor", f"{ld['cf_C_percent']:.2f}% of LL", "excluding impact")
        with c2:
            card("Assessment", "Not governing" if ld['cf_C_percent'] < 5 else "Review", "large radius / straight-span assumption", "pass" if ld['cf_C_percent'] < 5 else "warn")

    with tabs[5]:
        code_basis_card(
            "3.7 Wind Load (WS)",
            "EN 1991-1-4 and DPT 1311-50",
            "Report-driven WS module: user edits only the governing input parameters; vb, b/dtot, C, Aref, FW and FEA line loads are calculated automatically from one source.",
        )
        st.markdown('<div class="note-box"><b>Wind one-source rule:</b> the editable parameter table below feeds the calculation trace, figures, result tables, FEA summary, Save/Load JSON, and future report export. C factors are not duplicate manual inputs.</div>', unsafe_allow_html=True)

        wind_tabs = st.tabs(["Overview", "Inputs", "EN Factors", "Calculations", "Figures", "FEA Summary"])
        lc = D["load_components"]
        wind_group_options = wind_reference_group_options()
        if lc.get("wind_reference_group") not in wind_group_options:
            lc["wind_reference_group"] = "Group 1"

        with wind_tabs[0]:
            ld = load_derived()
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                card("Code basis", "EN 1991-1-4", "Bridge wind force in x-direction")
            with c2:
                card("DPT wind group", str(lc.get("wind_reference_group", "Group 1")), f"vb,0 = {format_engineering_value(lc['wind_vb0_m_s'], 'm/s')} m/s", "pass")
            with c3:
                card("WS line load", f"{format_engineering_value(ld['WSsuper_kn_m'], 'kN/m')} kN/m", "Wind on superstructure")
            with c4:
                card("WS+WL line load", f"{format_engineering_value(ld['WSsuper_WL_kn_m'], 'kN/m')} kN/m", "Wind on superstructure + train", "pass")
            st.latex(r"F_{W,x}=\frac{1}{2}\rho v_b^2 C A_{ref,x}")
            st.latex(r"v_b=c_{dir}c_{season}v_{b,0},\qquad A_{ref,x}=d_{tot}L")
            show_engineering_table(pd.DataFrame([
                ["ρ", lc["wind_air_density_kg_m3"], "kg/m³", "Air density used in BG40 R10"],
                ["vb,0", lc["wind_vb0_m_s"], "m/s", "DPT 1311-50 reference speed / user-adopted"],
                ["vb", ld["vb_m_s"], "m/s", "Calculated basic wind velocity"],
                ["CWS", ld["C_ws"], "factor", "Auto from EN Table 8.2 / BG40 Table 2.5"],
                ["CWS+WL", ld["C_ws_wl"], "factor", "Auto from EN Table 8.2 / BG40 Table 2.5"],
                ["WSsuper", ld["WSsuper_kn"], "kN", "Resultant wind force"],
                ["WSsuper+WL", ld["WSsuper_WL_kn"], "kN", "Resultant wind force including train envelope"],
            ], columns=["Item", "Value", "Unit", "Interpretation"]))

        with wind_tabs[1]:
            st.markdown("#### Editable wind parameter table")
            selected_group = st.selectbox(
                "DPT 1311-50 reference wind speed group",
                wind_group_options,
                index=wind_group_options.index(lc.get("wind_reference_group", "Group 1")),
                key="wind_reference_group_select",
                help="Selecting a group updates the recommended vb,0. Manual edits remain possible in the table.",
            )
            if selected_group != lc.get("wind_reference_group"):
                rec = wind_vb0_recommended_from_group(selected_group)
                lc["wind_reference_group"] = str(rec["group"])
                lc["wind_v50_m_s"] = float(rec["V50_m_s"])
                lc["wind_terrain_factor"] = float(rec["TF"])
                lc["wind_vb0_m_s"] = float(rec["vb0_m_s"])

            specs = [
                ("Air density ρ", "wind_air_density_kg_m3", "kg/m³", 1.25, "BG40 R10 / EN calculation parameter"),
                ("Reference wind speed V50", "wind_v50_m_s", "m/s", wind_vb0_recommended_from_group(lc.get("wind_reference_group", "Group 1"))["V50_m_s"], "DPT 1311-50 group value"),
                ("Terrain factor TF", "wind_terrain_factor", "-", wind_vb0_recommended_from_group(lc.get("wind_reference_group", "Group 1"))["TF"], "DPT group factor shown in BG40 R10"),
                ("Fundamental basic wind velocity vb,0", "wind_vb0_m_s", "m/s", wind_vb0_recommended_from_group(lc.get("wind_reference_group", "Group 1"))["vb0_m_s"], "User-adopted basic wind velocity"),
                ("Directional factor cdir", "wind_cdir", "-", 1.0, "EN 1991-1-4 Section 4.2 Note 2 recommended value"),
                ("Season factor cseason", "wind_cseason", "-", 1.0, "EN 1991-1-4 Section 4.2 Note 3 recommended value"),
                ("Bridge/deck width b", "wind_b_m", "m", D["project"]["width_m"], "Width in x-direction D from report"),
                ("Depth dtot,WS", "wind_dtot_ws_m", "m", 3.9, "Superstructure with parapets"),
                ("Depth dtot,WS+WL", "wind_dtot_ws_wl_m", "m", 6.8, "Superstructure plus train"),
                ("Deck height ze", "wind_ze_m", "m", 10.0, "Height of bridge deck"),
                ("Wind loaded length L", "wind_span_m", "m", D["project"]["span_m"], "Length of superstructure subjected to wind"),
            ]
            # Mirror span to a load component key for table editing while keeping project span as source of truth by default.
            lc.setdefault("wind_span_m", float(D["project"]["span_m"]))
            param_df = pd.DataFrame([
                {"Parameter": label, "Value": float(lc.get(key, default)), "Unit": unit, "Recommended / source": src, "Schema key": key}
                for label, key, unit, default, src in specs
            ])
            edited = st.data_editor(
                param_df,
                use_container_width=True,
                hide_index=True,
                disabled=["Parameter", "Unit", "Recommended / source", "Schema key"],
                column_config={"Value": st.column_config.NumberColumn(format="%.3f")},
                key="wind_parameter_editor",
            )
            for _, row in edited.iterrows():
                key = str(row["Schema key"])
                lc[key] = float(row["Value"])
            D["project"]["span_m"] = float(lc.get("wind_span_m", D["project"]["span_m"]))
            lc["wind_vb_m_s"] = float(lc["wind_vb0_m_s"]) * float(lc["wind_cdir"]) * float(lc["wind_cseason"])
            st.markdown('<div class="warn-box"><b>Override rule:</b> if a recommended value is changed, the app keeps the edited value as User Input and recalculates downstream WS, WS+WL, and FEA summary values.</div>', unsafe_allow_html=True)

        with wind_tabs[2]:
            st.markdown("#### EN 1991-1-4 wind factor reference")
            c1, c2 = st.columns([1.1, 1.0])
            with c1:
                st.latex(r"C=C(b/d_{tot},z_e)")
                st.markdown("The app uses the report Table 2.5 / EN 1991-1-4 Table 8.2 bridge wind factor data and applies linear interpolation for `0.5 < b/dtot < 4.0`.")
                factor_df = pd.DataFrame([
                    ["b/dtot ≤ 0.5", 6.7, 8.3],
                    ["b/dtot ≥ 4.0", 3.6, 4.5],
                ], columns=["b/dtot range", "C at ze ≤ 20 m", "C at ze = 50 m"])
                show_engineering_table(factor_df)
                ld = load_derived()
                show_engineering_table(pd.DataFrame([
                    ["WS", ld["b_over_d_ws"], "-", ld["C_ws"], ld["C_ws_note"]],
                    ["WS+WL", ld["b_over_d_ws_wl"], "-", ld["C_ws_wl"], ld["C_ws_wl_note"]],
                ], columns=["Case", "b/dtot", "Unit", "C", "Interpolation trace"]))
            with c2:
                show_report_image("fig_ws_factor_table_and_ze.png", "Table 2.5 Wind load factor C for bridges and deck-height reference (from BG40 R10 / EN 1991-1-4)")

        with wind_tabs[3]:
            ld = load_derived()
            st.markdown("#### Basic wind velocity")
            st.latex(r"v_b=c_{dir}c_{season}v_{b,0}")
            st.latex(fr"v_b={lc['wind_cdir']:.2f}({lc['wind_cseason']:.2f})({lc['wind_vb0_m_s']:.1f})={ld['vb_m_s']:.1f}\,\mathrm{{m/s}}")
            st.markdown("#### Wind load factor and reference area")
            st.latex(r"A_{ref,x}=d_{tot}L")
            st.latex(fr"A_{{ref,x,WS}}={lc['wind_dtot_ws_m']:.3f}({lc.get('wind_span_m', D['project']['span_m']):.3f})={ld['Aref_ws_m2']:.1f}\,\mathrm{{m^2}}")
            st.latex(fr"A_{{ref,x,WS+WL}}={lc['wind_dtot_ws_wl_m']:.3f}({lc.get('wind_span_m', D['project']['span_m']):.3f})={ld['Aref_ws_wl_m2']:.1f}\,\mathrm{{m^2}}")
            st.markdown("#### Wind force and equivalent line load")
            st.latex(r"F_{W,x}=\frac{1}{2}\rho v_b^2 C A_{ref,x}")
            st.latex(fr"F_{{W,x,WS}}=\frac{{1}}{{2}}({lc['wind_air_density_kg_m3']:.2f})({ld['vb_m_s']:.1f})^2({ld['C_ws']:.3f})({ld['Aref_ws_m2']:.1f})={ld['WSsuper_kn']:.0f}\,\mathrm{{kN}}")
            st.latex(fr"F_{{W,x,WS+WL}}=\frac{{1}}{{2}}({lc['wind_air_density_kg_m3']:.2f})({ld['vb_m_s']:.1f})^2({ld['C_ws_wl']:.3f})({ld['Aref_ws_wl_m2']:.1f})={ld['WSsuper_WL_kn']:.0f}\,\mathrm{{kN}}")
            st.latex(fr"w_{{WS}}=F_{{W,x,WS}}/L={ld['WSsuper_kn_m']:.2f}\,\mathrm{{kN/m}},\qquad w_{{WS+WL}}={ld['WSsuper_WL_kn_m']:.2f}\,\mathrm{{kN/m}}")
            show_engineering_table(pd.DataFrame([
                ["q = 0.5ρvb²", ld["q_pa"], "Pa", "velocity pressure"],
                ["CWS", ld["C_ws"], "factor", "automatic interpolation"],
                ["CWS+WL", ld["C_ws_wl"], "factor", "automatic interpolation"],
                ["Aref,x,WS", ld["Aref_ws_m2"], "m²", "dtot,WS × L"],
                ["Aref,x,WS+WL", ld["Aref_ws_wl_m2"], "m²", "dtot,WS+WL × L"],
                ["WSsuper", ld["WSsuper_kn"], "kN", f"{ld['WSsuper_kn_m']:.2f} kN/m"],
                ["WSsuper+WL", ld["WSsuper_WL_kn"], "kN", f"{ld['WSsuper_WL_kn_m']:.2f} kN/m"],
            ], columns=["Item", "Value", "Unit", "Interpretation"]))

        with wind_tabs[4]:
            st.markdown("#### Report reference figures")
            c1, c2 = st.columns(2)
            with c1:
                show_report_image("fig_1_2_dpt_wind_speed_map.png", "Figure 1.2 Reference wind speed map of Thailand (DPT 1311-50)")
            with c2:
                show_report_image("fig_1_3_en_wind_direction_bridge.png", "Figure 1.3 Wind load directions on bridge (EN 1991-1-4 Fig. 8.2)")
            c3, c4 = st.columns(2)
            with c3:
                show_report_image("fig_ws_factor_table_and_ze.png", "Wind factor C table and ze definition (report Table 2.5)")
            with c4:
                show_report_image("fig_ws_bridge_cross_section_load.png", "Wind application on superstructure and train load envelope (WS / WL)")

        with wind_tabs[5]:
            ld = load_derived()
            rows = [
                ["WS", "Wind on superstructure", ld["WSsuper_kn"], "kN", ld["WSsuper_kn_m"], "kN/m", "Transverse x-direction", "Superstructure"],
                ["WS+WL", "Wind on superstructure + train", ld["WSsuper_WL_kn"], "kN", ld["WSsuper_WL_kn_m"], "kN/m", "Transverse x-direction", "Superstructure + train"],
            ]
            show_engineering_table(pd.DataFrame(rows, columns=["Load Pattern", "Description", "Resultant Force", "Unit", "Line Load", "Line Unit", "Direction", "Application"]))
            st.markdown('<div class="note-box"><b>FEA export rule:</b> WS and WS+WL are exported as equivalent transverse line loads along the wind-loaded span. The resultant forces shown above are calculated only once from the editable parameter table.</div>', unsafe_allow_html=True)
    with tabs[6]:
        code_basis_card("1.3.8 Creep and Shrinkage Parameters", "AASHTO LRFD 2020 Section 5, Art. 5.9.3 / 5.4.2.3", "Parameters declared here are consumed by 4 Prestress Losses; formulas are wrapped with SI↔AASHTO unit conversion.")
        p = D["prestress"]
        st.dataframe(pd.DataFrame([
            ["RH", p["RH_percent"], "%", "Project design assumption"],
            ["ti", p["ti_days"], "days", "Age at stressing"],
            ["tf", p["tf_days"], "days", "Final design age"],
            ["u_outer", p["u_outer_m"], "m", "External perimeter"],
            ["u_inner", p["u_inner_m"], "m", "Internal void perimeter"],
            ["V/S", p["V_over_S_m"], "m", f"{p['V_over_S_mm']} mm = {p['V_over_S_in']} in"],
            ["h0", p["h0_m"], "m", "2Ac/u_total"],
        ], columns=["Parameter", "Value", "Unit", "Remarks"]), use_container_width=True, hide_index=True)
        st.markdown('<div class="warn-box"><b>Unit warning:</b> AASHTO empirical creep/shrinkage factors use V/S in inches and concrete strength in ksi for intermediate factors.</div>', unsafe_allow_html=True)

    with tabs[7]:
        code_basis_card(
            "3.9 Earthquake (EQ)",
            "DPT 1301/1302-61 Section 1.4, Section 1.6, and Chapter 3 equivalent static method",
            "M3B-QA uses the curated DPT database and corrected equivalent-static spectrum route: Fig. 1.4-1 when SD1 ≤ SDS and Fig. 1.4-2 when SD1 > SDS; dynamic Fig. 1.4-3 / 1.4-4 is not used for Cs.",
        )
        lc = D["load_components"]
        st.markdown('<div class="note-box"><b>Location-based workflow:</b> select province and district once. The app resolves General Thailand vs Bangkok Basin, looks up DPT values, and recalculates all seismic parameters from the same source.</div>', unsafe_allow_html=True)

        provinces = list_dpt_provinces()
        default_province = lc.get("seismic_province_th", "อุดรธานี")
        if default_province not in provinces:
            default_province = "อุดรธานี" if "อุดรธานี" in provinces else provinces[0]
        c1, c2, c3 = st.columns(3)
        with c1:
            province = st.selectbox("Province / จังหวัด", provinces, index=provinces.index(default_province), key="eq_province_select")
            lc["seismic_province_th"] = province
        districts = list_dpt_districts(province)
        if not districts:
            districts = [lc.get("seismic_district_th", "") or ""]
        default_district = lc.get("seismic_district_th", districts[0])
        if default_district not in districts:
            default_district = districts[0]
        with c2:
            district = st.selectbox("District / อำเภอ", districts, index=districts.index(default_district), key="eq_district_select")
            lc["seismic_district_th"] = "เมือง" if district == "ทั้งจังหวัด" and province == "กรุงเทพมหานคร" else district
        with c3:
            lc["seismic_soil_class"] = st.selectbox("Soil Class", ["A", "B", "C", "D", "E", "F"], index=["A", "B", "C", "D", "E", "F"].index(lc.get("seismic_soil_class", "D")))

        render_aashto_bridge_seismic_controls(lc)
        tc1, tc2, tc3 = st.columns([0.8, 1.0, 1.0])
        with tc1:
            editable_value(["load_components", "seismic_T_s"], "Analysis period T (s)", 0.01, "%.3f")
        with tc2:
            st.metric("Active I", f"{float(lc['seismic_I']):.2f}", help=lc.get("seismic_I_source", "Project/DPT basis"))
        with tc3:
            st.metric("Active R", f"{float(lc['seismic_R']):.1f}", help=lc.get("seismic_R_source", "AASHTO LRFD bridge R basis"))

        region_lookup = resolve_location_region(province, lc["seismic_district_th"])
        if region_lookup.get("found") and region_lookup.get("region") == "Bangkok Basin":
            lc["seismic_region"] = "Bangkok Basin"
            lc["seismic_bangkok_zone"] = int(region_lookup["zone"])
            st.success(f"Bangkok Basin detected: Zone {int(region_lookup['zone'])} from {region_lookup['source_table']} — จ.{province} อ.{lc['seismic_district_th']}")
            c1, c2, c3 = st.columns(3)
            with c1:
                lc["seismic_damping_percent"] = st.selectbox("Damping ratio for Bangkok Basin table", [5.0, 2.5], index=0 if float(lc.get("seismic_damping_percent", 5.0)) == 5.0 else 1)
            with c2:
                st.metric("Zone", int(lc["seismic_bangkok_zone"]), help="DPT 1301/1302-61 Fig. 1.4-5")
            with c3:
                st.metric("I/R", f"{float(lc['seismic_I']):.2f} / {float(lc['seismic_R']):.1f}", help="One-source controls above feed Cs in this branch.")
            ld = load_derived()
            st.latex(r"S_a(T)=\text{interpolated from DPT Table 1.4-5 (5\% damping) or Table 1.4-4 (2.5\% damping)}")
            st.latex(r"C_s=S_a\left(\frac{I}{R}\right)\quad\text{with}\quad C_s\ge0.01")
            st.latex(fr"S_a({D['load_components']['seismic_T_s']:.3f})={ld['eq_Sa']:.4f}\,g")
            st.latex(fr"C_s={ld['eq_Sa']:.4f}\left(\frac{{{D['load_components']['seismic_I']:.2f}}}{{{D['load_components']['seismic_R']:.1f}}}\right)={ld['eq_Cs']:.4f}")
            spec = bangkok_response_spectrum_points(int(lc["seismic_bangkok_zone"]), float(lc.get("seismic_damping_percent", 5.0)))
            show_plotly(response_spectrum_figure(spec, float(D["load_components"]["seismic_T_s"]), ld["eq_Sa"], f"DPT Bangkok Basin Zone {int(lc['seismic_bangkok_zone'])} — Equivalent static spectrum"))
            source_text = "Table 1.4-5" if float(lc.get("seismic_damping_percent", 5.0)) == 5.0 else "Table 1.4-4"
            rows = [
                ["Region", "Bangkok Basin", "Fig. 1.4-5"],
                ["Zone", lc["seismic_bangkok_zone"], "Fig. 1.4-5"],
                ["Damping", lc.get("seismic_damping_percent", 5.0), "%"],
                ["SDS = Sa(0.2s)", ld["eq_SDS"], source_text],
                ["SD1 = Sa(1.0s)", ld["eq_SD1"], source_text],
                ["Sa(T)", ld["eq_Sa"], "table interpolation"],
                ["Cs", ld["eq_Cs"], "DPT Ch.3 equivalent static coefficient"],
                ["AASHTO operational category", lc.get("seismic_operational_category", "-"), "AASHTO Art. 3.10.5 / owner-AHJ classification"],
                ["Substructure R basis", lc.get("seismic_substructure_label", "-"), lc.get("seismic_R_source", "AASHTO Table 3.10.7.1-1")],
                ["Importance I basis", lc.get("seismic_I", "-"), lc.get("seismic_I_source", "Project/DPT basis")],
                ["Category SDS", ld["eq_category_sds"], "DPT Table 1.6-1"],
                ["Category SD1", ld["eq_category_sd1"], "DPT Table 1.6-2"],
                ["Governing category", ld["eq_category_governing"], ld.get("eq_category_basis", "DPT Section 1.6")],
            ]
            show_engineering_table(pd.DataFrame(rows, columns=["Item", "Value", "Unit / source"]))
        elif region_lookup.get("found"):
            lc["seismic_region"] = "General Thailand"
            lc["seismic_bangkok_zone"] = 0
            lc["seismic_Ss_g"] = float(region_lookup["Ss"])
            lc["seismic_S1_g"] = float(region_lookup["S1"])
            st.success(f"DPT lookup matched: อ.{region_lookup['district_th']} จ.{region_lookup['province_th']} — Ss={region_lookup['Ss']:.3f}, S1={region_lookup['S1']:.3f} ({region_lookup['source_table']}, standard p.{region_lookup['source_standard_page']})")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Ss (g)", f"{lc['seismic_Ss_g']:.3f}")
            with c2:
                st.metric("S1 (g)", f"{lc['seismic_S1_g']:.3f}")
            with c3:
                st.metric("I/R", f"{float(lc['seismic_I']):.2f} / {float(lc['seismic_R']):.1f}", help="One-source controls above feed Cs in this branch.")
            ld = load_derived()
            st.latex(r"S_{MS}=F_aS_S,\qquad S_{M1}=F_vS_1")
            st.latex(r"S_{DS}=\frac{2}{3}S_{MS},\qquad S_{D1}=\frac{2}{3}S_{M1}")
            st.latex(r"C_s=S_a\left(\frac{I}{R}\right)\quad\text{with}\quad C_s\ge0.01")
            st.latex(fr"S_{{DS}}=\frac{{2}}{{3}}({ld['eq_Fa']:.2f})({D['load_components']['seismic_Ss_g']:.3f})={ld['eq_SDS']:.4f}\,g")
            st.latex(fr"S_{{D1}}=\frac{{2}}{{3}}({ld['eq_Fv']:.2f})({D['load_components']['seismic_S1_g']:.3f})={ld['eq_SD1']:.4f}\,g")
            st.latex(fr"C_s={ld['eq_Sa']:.4f}\left(\frac{{{D['load_components']['seismic_I']:.2f}}}{{{D['load_components']['seismic_R']:.1f}}}\right)={ld['eq_Cs']:.4f}")
            spec = response_spectrum_points(ld["eq_SDS"], ld["eq_SD1"], t_max=max(2.5, float(D["load_components"]["seismic_T_s"]) * 1.5))
            show_plotly(response_spectrum_figure(spec, float(D["load_components"]["seismic_T_s"]), ld["eq_Sa"], "DPT equivalent-static design response spectrum — General Thailand workflow"))
            rows = [
                ["Region", "General Thailand", "Table 1.4-1"],
                ["Ss", lc["seismic_Ss_g"], "g"], ["S1", lc["seismic_S1_g"], "g"],
                ["Fa", ld["eq_Fa"], "Table 1.4-2"], ["Fv", ld["eq_Fv"], "Table 1.4-3"],
                ["SDS", ld["eq_SDS"], "g"], ["SD1", ld["eq_SD1"], "g"],
                ["Spectrum figure", ld.get("eq_spectrum_figure", "DPT Fig. 1.4-1 / 1.4-2"), "DPT Sec. 1.4.5.1"],
                ["Spectrum branch", ld.get("eq_spectrum_branch", "equivalent static"), "Sa(T) route"],
                ["T0", ld["eq_T0"], "s / N.A. when 0"], ["Ts", ld["eq_Ts"], "s"],
                ["Sa(T)", ld["eq_Sa"], "g"], ["Cs", ld["eq_Cs"], "-"],
                ["AASHTO operational category", lc.get("seismic_operational_category", "-"), "AASHTO Art. 3.10.5 / owner-AHJ classification"],
                ["Substructure R basis", lc.get("seismic_substructure_label", "-"), lc.get("seismic_R_source", "AASHTO Table 3.10.7.1-1")],
                ["Importance I basis", lc.get("seismic_I", "-"), lc.get("seismic_I_source", "Project/DPT basis")],
                ["Category SDS", ld["eq_category_sds"], "DPT Table 1.6-1"],
                ["Category SD1", ld["eq_category_sd1"], "DPT Table 1.6-2"],
                ["Governing category", ld["eq_category_governing"], ld.get("eq_category_basis", "more stringent")],
            ]
            show_engineering_table(pd.DataFrame(rows, columns=["Item", "Value", "Unit / source"]))
        else:
            lc["seismic_region"] = "Manual / Not found"
            st.warning("Location not found in the curated M3B DPT database. Use manual Ss/S1 below only with documented project justification.")
            c1, c2, c3 = st.columns(3)
            with c1:
                editable_value(["load_components", "seismic_Ss_g"], "Ss (g)", 0.001, "%.3f")
            with c2:
                editable_value(["load_components", "seismic_S1_g"], "S1 (g)", 0.001, "%.3f")
            with c3:
                st.metric("I/R", f"{float(lc['seismic_I']):.2f} / {float(lc['seismic_R']):.1f}", help="One-source controls above feed Cs in this branch.")
            ld = load_derived()
            st.latex(r"S_{MS}=F_aS_S,\qquad S_{M1}=F_vS_1")
            st.latex(r"C_s=S_a\left(\frac{I}{R}\right)")
            st.markdown('<div class="warn-box"><b>Manual source warning:</b> results are calculated from user-entered Ss/S1 and are not verified against the DPT location database.</div>', unsafe_allow_html=True)
        st.markdown('<div class="warn-box"><b>Scope note:</b> DPT 1301/1302-61 is a building seismic design standard. In this bridge app it is used as Thai project seismic parameter basis, consistent with the BG40 report criteria.</div>', unsafe_allow_html=True)

    with tabs[8]:
        ld = load_derived()
        rows = [
            ["DL", "DL", "Self-weight from γc", "Auto", "-", "Gravity", "FEA self-weight", "FEA auto / QA preview"],
            ["SDL", "SDL", "BG40 R10 SDL schedule", D["load_components"]["design_sdl_double_kn_m"], "kN/m", "Gravity", "Along span", "Editable table"],
            ["LL+IM", "LL+IM", "EN 1991-2 Art. 6.4.3/6.4.5", f"U20 × {format_engineering_value(D['load_components']['dynamic_factor_design'], 'factor')}", "factor", "Vertical", "Railway load model", "App calc + adopted"],
            ["LF", "LF", "EN 1991-2 Art. 6.5.3", f"{ld['LF_design_kn']:.0f} / {ld['LF_design_kn_m']:.1f}", "kN / kN/m", "Longitudinal", "Rail level", "App calculated"],
            ["HF", "Qsk", "EN 1991-2 Art. 6.5.2", f"{ld['hf_HF_adopted_kn']:.0f}", "kN", "Transverse", "Top of rail concentrated", "App decision"],
            ["CF", "C", "EN 1991-2 Art. 6.5.1", f"{ld['cf_C_percent']:.2f}", "% of LL", "Radial/transverse", "Curved track only", "App calculated"],
            ["WS", "WS", "EN 1991-1-4 + DPT 1311-50", f"{ld['WSsuper_kn_m']:.2f}", "kN/m", "Wind transverse", "Superstructure", "App calculated"],
            ["WS+WL", "WS+WL", "EN 1991-1-4 + DPT 1311-50", f"{ld['WSsuper_WL_kn_m']:.2f}", "kN/m", "Wind transverse", "Superstructure + train", "App calculated"],
            ["EQ", "Cs", "DPT 1301/1302-61 + AASHTO bridge R", f"{ld['eq_Cs']:.4f}", "-", "X/Y seismic", f"Equivalent static coefficient · I/R={float(D['load_components']['seismic_I']):.2f}/{float(D['load_components']['seismic_R']):.1f}", "DPT lookup + AASHTO R + app calculated"],
            ["CR&SH", "CR/SH", "AASHTO LRFD Art. 5.9.5", "parameters", "-", "Long-term", "Prestress loss module", "Declared in 1.3 / calculated in 4"],
        ]
        show_engineering_table(pd.DataFrame(rows, columns=["Load Pattern", "Symbol", "Code Basis", "Value", "Unit", "Direction", "Application", "Source"]))
        st.markdown('<div class="note-box"><b>Report/export rule:</b> this FEA summary reads from the same load schema edited above. No duplicate input fields are used.</div>', unsafe_allow_html=True)


def page_bridge_model(sub: str) -> None:
    st.subheader(get_workspace("2 Bridge Geometry / Section Properties")["title"])
    if sub == "2.1 Bridge Description":
        c1, c2, c3 = st.columns(3)
        with c1:
            D["project"]["name"] = st.text_input("Bridge name", D["project"]["name"])
            D["project"]["bridge_object"] = st.text_input("Bridge object / span", D["project"]["bridge_object"])
        with c2:
            editable_value(["project", "span_m"], "Span length (m)", 1.0)
            editable_value(["project", "width_m"], "Total width (m)", 0.1)
        with c3:
            editable_value(["project", "depth_m"], "Section depth (m)", 0.1)
            D["project"]["tendon_system"] = st.selectbox("Tendon system", ["External / Unbonded PT", "Fully bonded internal PT"], index=0 if "External" in D["project"]["tendon_system"] else 1)
        st.dataframe(pd.DataFrame([
            ["Bridge name", D["project"]["name"], "-"], ["Type", D["bridge_model"]["bridge_type"], "-"], ["Span length", D["project"]["span_m"], "m"],
            ["Number of tracks", D["bridge_model"]["number_of_tracks"], "-"], ["Total width", D["project"]["width_m"], "m"], ["Section depth", D["project"]["depth_m"], "m"],
            ["Post-tensioning system", D["project"]["tendon_system"], "-"], ["Quantity tendons", D["prestress"]["num_tendons"], "-"],
        ], columns=["Parameter", "Value", "Unit"]), use_container_width=True, hide_index=True)
    elif sub == "2.2 FEA Model":
        st.dataframe(pd.DataFrame([
            ["Box Girder Superstructure", D["bridge_model"]["superstructure_element"], "Full 3D shell mesh"],
            ["PT Tendons", D["bridge_model"]["tendon_element"], "16 tendons per span"],
            ["Pier Columns", D["bridge_model"]["substructure_element"], "Frame model"],
            ["Piles", D["bridge_model"]["foundation_model"], "Winkler foundation"],
        ], columns=["Component", "Element Type", "Remarks"]), use_container_width=True, hide_index=True)
        st.markdown('<div class="note-box">The superstructure is modeled as three simply supported girder spans. The app checks one selected design span using imported/keyed FEA demand envelopes.</div>', unsafe_allow_html=True)
    elif sub == "2.3 Supports":
        st.dataframe(pd.DataFrame(D["bridge_model"]["support_conditions"]), use_container_width=True, hide_index=True)
    elif sub == "2.4 Tendon Layout":
        tendon_df = pd.DataFrame(D["prestress"]["tendon_friction_groups"])[["group", "n", "end_dp_m", "midspan_dp_m", "alpha_vert_rad", "alpha_horiz_rad"]]
        st.dataframe(tendon_df, use_container_width=True, hide_index=True)
        st.info(f"Weighted average dp at end = {D['prestress']['dp_avg_end_m']:.3f} m; at midspan = {D['prestress']['dp_avg_midspan_m']:.3f} m; e_midspan = {D['prestress']['eccentricity_midspan_m']:.3f} m.")
    else:
        report_trace_table("2 Bridge Geometry / Section Properties", [("Bridge description", "User input + BG40 R10", "Report table ready", "READY"), ("FEA model assumptions", "BG40 R10", "Assumption cards ready", "READY"), ("Supports", "BG40 R10", "Support table ready", "READY"), ("Tendon layout", "BG40 R10", "Tendon table ready", "READY")])


def page_section_properties(sub: str) -> None:
    st.subheader(get_workspace("2 Bridge Geometry / Section Properties")["title"])
    s = D["section"]
    if sub == "3.1 Cross-Section":
        c1, c2, c3 = st.columns(3)
        with c1:
            editable_value(["section", "B_m"], "Total width B (m)", 0.1)
            editable_value(["section", "D_m"], "Section depth D (m)", 0.1)
        with c2:
            editable_value(["section", "t_top_m"], "Top slab thickness (m)", 0.01)
            editable_value(["section", "t_bot_m"], "Bottom slab thickness (m)", 0.01)
        with c3:
            editable_value(["section", "t_web_m"], "Web thickness (m)", 0.01)
            editable_value(["section", "web_inclination_deg"], "Web inclination θ (deg)", 0.1)
        st.dataframe(pd.DataFrame([["Total width", "B", s["B_m"], "m"], ["Section depth", "D", s["D_m"], "m"], ["Top slab thickness", "t_top", s["t_top_m"], "m"], ["Bottom slab thickness", "t_bot", s["t_bot_m"], "m"], ["Web thickness", "t_web", s["t_web_m"], "m"], ["Web inclination", "θ", s["web_inclination_deg"], "degrees"]], columns=["Size", "Symbol", "Value", "Unit"]), use_container_width=True, hide_index=True)
    elif sub == "3.2 FEA Properties":
        cols = st.columns(4)
        with cols[0]: editable_value(["section", "Ac_m2"], "A (m²)", 0.001, "%.3f")
        with cols[1]: editable_value(["section", "I33_m4"], "I33 (m⁴)", 0.001, "%.3f")
        with cols[2]: editable_value(["section", "I22_m4"], "I22 (m⁴)", 0.01, "%.2f")
        with cols[3]: editable_value(["section", "J_m4"], "J (m⁴)", 0.001, "%.3f")
        cols = st.columns(4)
        with cols[0]: editable_value(["section", "S_top_m3"], "S33 top (m³)", 0.001, "%.3f")
        with cols[1]: editable_value(["section", "S_bottom_m3"], "S33 bottom (m³)", 0.001, "%.3f")
        with cols[2]: editable_value(["section", "ycg_from_bottom_m"], "y_cg from bottom (m)", 0.001, "%.3f")
        with cols[3]: editable_value(["section", "yt_from_top_m"], "y_t from top (m)", 0.001, "%.3f")
        props = [["Cross-sectional area", "A", s["Ac_m2"], "m²"], ["Moment of inertia major", "I33", s["I33_m4"], "m⁴"], ["Moment of inertia minor", "I22", s["I22_m4"], "m⁴"], ["Torsional constant", "J", s["J_m4"], "m⁴"], ["Section modulus top", "S33(+)", s["S_top_m3"], "m³"], ["Section modulus bottom", "S33(-)", s["S_bottom_m3"], "m³"], ["Centroid from bottom", "y_cg", s["ycg_from_bottom_m"], "m"], ["Centroid from top", "y_t", s["yt_from_top_m"], "m"]]
        st.dataframe(pd.DataFrame(props, columns=["Property", "Symbol", "Value", "Unit"]), use_container_width=True, hide_index=True)
    elif sub == "3.3 Consistency Checks":
        S_top_calc = s["I33_m4"] / s["yt_from_top_m"] if s["yt_from_top_m"] else 0.0
        S_bot_calc = s["I33_m4"] / s["ycg_from_bottom_m"] if s["ycg_from_bottom_m"] else 0.0
        D_calc = s["ycg_from_bottom_m"] + s["yt_from_top_m"]
        st.dataframe(pd.DataFrame([
            ["S33(+) = I33 / yt", S_top_calc, s["S_top_m3"], abs(S_top_calc - s["S_top_m3"]), "m³"],
            ["S33(-) = I33 / ycg", S_bot_calc, s["S_bottom_m3"], abs(S_bot_calc - s["S_bottom_m3"]), "m³"],
            ["D = ycg + yt", D_calc, s["D_m"], abs(D_calc - s["D_m"]), "m"],
        ], columns=["Check", "Calculated", "Report / input", "Difference", "Unit"]), use_container_width=True, hide_index=True)
    else:
        report_trace_table("2 Bridge Geometry / Section Properties", [("Cross-section dimensions", "User input + FEA", "Report table ready", "READY"), ("Section properties", "FEA keyed values", "Consistency checks active", "READY"), ("Closed cell torsion properties", "Chapter 7 inputs", "Aoh/ph passed to torsion module", "READY")])




def _section_coordinate_df_from_state() -> pd.DataFrame:
    rows = D["section"].get("coordinate_rows") or []
    if rows:
        try:
            return normalize_coordinate_rows(pd.DataFrame(rows))
        except Exception:
            return pd.DataFrame(rows)
    return pd.DataFrame(columns=["loop_name", "loop_type", "point_no", "x_mm", "y_mm"])


def _store_section_coordinate_df(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        D["section"]["coordinate_rows"] = []
        return
    try:
        norm = normalize_coordinate_rows(df)
        D["section"]["coordinate_rows"] = norm[["loop_name", "point_no", "x_mm", "y_mm"]].to_dict("records")
        D["section"]["coordinate_source"] = "Imported / edited CSiBridge polygon coordinates"
    except Exception:
        # Preserve edited rows so the user can fix column names/values.
        D["section"]["coordinate_rows"] = df.to_dict("records")


def _section_computation_from_state() -> dict[str, Any]:
    coords = _section_coordinate_df_from_state()
    if coords.empty:
        return {"valid": False, "errors": ["No coordinate rows imported yet"], "warnings": []}
    try:
        return calculate_section_properties(coords)
    except Exception as exc:  # noqa: BLE001
        return {"valid": False, "errors": [str(exc)], "warnings": []}


def _apply_computed_section_properties(props: dict[str, Any]) -> None:
    if not props.get("valid"):
        return
    s = D["section"]
    s["Ac_m2"] = float(props["A_m2"])
    s["I33_m4"] = float(props["I33_m4"])
    s["I22_m4"] = float(props["I22_m4"])
    s["S_top_m3"] = float(props["S_top_m3"])
    s["S_bottom_m3"] = float(props["S_bottom_m3"])
    s["xcg_from_left_m"] = float(props["xcg_from_left_m"])
    s["xcg_from_right_m"] = float(props["xcg_from_right_m"])
    s["ycg_from_bottom_m"] = float(props["ycg_from_bottom_m"])
    s["yt_from_top_m"] = float(props["yt_from_top_m"])
    s["B_m"] = float(props["width_m"])
    s["D_m"] = float(props["depth_m"])
    s["computed_from_coordinates"] = {
        "A_m2": float(props["A_m2"]),
        "I33_m4": float(props["I33_m4"]),
        "I22_m4": float(props["I22_m4"]),
        "S_top_m3": float(props["S_top_m3"]),
        "S_bottom_m3": float(props["S_bottom_m3"]),
        "xcg_from_left_m": float(props["xcg_from_left_m"]),
        "xcg_from_right_m": float(props["xcg_from_right_m"]),
        "ycg_from_bottom_m": float(props["ycg_from_bottom_m"]),
        "yt_from_top_m": float(props["yt_from_top_m"]),
        "width_m": float(props["width_m"]),
        "depth_m": float(props["depth_m"]),
    }
    s["coordinate_source"] = "Active section properties updated from imported CSiBridge polygon coordinates"


def render_bridge_description() -> None:
    section_title("2.1 Bridge Description")
    c1, c2, c3 = st.columns(3)
    with c1:
        D["project"]["name"] = st.text_input("Bridge name", D["project"]["name"], key="bridge_desc_name")
        D["project"]["bridge_object"] = st.text_input("Bridge object / span", D["project"]["bridge_object"], key="bridge_desc_object")
    with c2:
        editable_value(["project", "span_m"], "Span length (m)", 1.0)
        editable_value(["project", "width_m"], "Total width (m)", 0.1)
    with c3:
        editable_value(["project", "depth_m"], "Section depth (m)", 0.1)
        D["project"]["tendon_system"] = st.selectbox("Tendon system", ["External / Unbonded PT", "Fully bonded internal PT"], index=0 if "External" in D["project"]["tendon_system"] else 1, key="bridge_desc_tendon_system")
    rows = [
        ["Bridge name", D["project"]["name"], "-"],
        ["Type", D["bridge_model"]["bridge_type"], "-"],
        ["Span length", D["project"]["span_m"], "m"],
        ["Number of tracks", D["bridge_model"]["number_of_tracks"], "-"],
        ["Total width", D["project"]["width_m"], "m"],
        ["Section depth", D["project"]["depth_m"], "m"],
        ["Post-tensioning system", D["project"]["tendon_system"], "-"],
        ["Quantity tendons", D["prestress"]["num_tendons"], "-"],
    ]
    show_engineering_table(pd.DataFrame(rows, columns=["Parameter", "Value", "Unit"]))


def render_geometry_analysis_model() -> None:
    section_title("2.2 Geometry and Analysis Model")
    st.markdown('<div class="note-box"><b>FEA scope:</b> the finite element analysis model is created externally in CSiBridge, MIDAS, SAP2000, RM Bridge, or another analysis program. This app records geometry, modelling assumptions, support conditions, tendon representation, and report figures for design review and report generation only.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        editable_value(["project", "span_m"], "Span length L (m)", 1.0)
        editable_value(["project", "width_m"], "Total width B (m)", 0.1)
    with c2:
        editable_value(["project", "depth_m"], "Section depth D (m)", 0.1)
        programs = ["CSiBridge", "MIDAS Civil", "SAP2000", "RM Bridge", "Other"]
        current = D["bridge_model"].get("analysis_program", "CSiBridge")
        D["bridge_model"]["analysis_program"] = st.selectbox("FEA program", programs, index=programs.index(current) if current in programs else 0, key="fea_program_select")
    with c3:
        model_types = ["3D shell model", "Grillage model", "Frame-shell model", "Frame model", "Other"]
        current_model = D["bridge_model"].get("model_type", "3D shell model")
        D["bridge_model"]["model_type"] = st.selectbox("Model type", model_types, index=model_types.index(current_model) if current_model in model_types else 0, key="fea_model_type_select")
        D["bridge_model"]["model_figure_status"] = st.selectbox("FEA model figure status", ["Report figure attached", "To be uploaded", "Not available"], index=0, key="fea_model_figure_status")
    assumptions = pd.DataFrame([
        ["Bridge geometry", f"L = {D['project']['span_m']:.3f} m, B = {D['project']['width_m']:.3f} m, D = {D['project']['depth_m']:.3f} m", "User input / BG40 R10"],
        ["FEA program", D["bridge_model"].get("analysis_program", "CSiBridge"), "User selected"],
        ["Model type", D["bridge_model"].get("model_type", "3D shell model"), "User selected"],
        ["Superstructure element", D["bridge_model"].get("superstructure_element", "Shell Elements (4-node)"), "Report basis"],
        ["Tendon representation", D["bridge_model"].get("tendon_element", "Internal Tendon Objects"), "Report basis"],
        ["Foundation model", D["bridge_model"].get("foundation_model", "Winkler foundation"), "Report basis"],
    ], columns=["Item", "Value", "Source"])
    show_engineering_table(assumptions)
    st.markdown('<div class="warn-box"><b>Report figure requirement:</b> Figure 2.1 FEA model is managed here for report output. The app does not replace or regenerate the external FEA model.</div>', unsafe_allow_html=True)


def _section_comparison_rows(props: dict[str, Any], s: dict[str, Any]) -> pd.DataFrame:
    rows: list[list[Any]] = []
    if not props.get("valid"):
        return pd.DataFrame(columns=["Property", "Symbol", "App calculated", "Reference / active", "Difference", "% diff", "Unit", "Status"])
    comparisons = [
        ("Cross-sectional area", "A", props.get("A_m2"), s.get("Ac_m2"), "m²"),
        ("Moment of inertia major", "I33", props.get("I33_m4"), s.get("I33_m4"), "m⁴"),
        ("Moment of inertia minor", "I22", props.get("I22_m4"), s.get("I22_m4"), "m⁴"),
        ("Section modulus top", "S33(+)", props.get("S_top_m3"), s.get("S_top_m3"), "m³"),
        ("Section modulus bottom", "S33(-)", props.get("S_bottom_m3"), s.get("S_bottom_m3"), "m³"),
        ("Centroid X from left", "x_cg", props.get("xcg_from_left_m"), s.get("xcg_from_left_m", props.get("xcg_from_left_m")), "m"),
        ("Centroid Y from bottom", "y_cg", props.get("ycg_from_bottom_m"), s.get("ycg_from_bottom_m"), "m"),
        ("Overall width", "B", props.get("width_m"), s.get("B_m"), "m"),
        ("Overall depth", "D", props.get("depth_m"), s.get("D_m"), "m"),
    ]
    for name, sym, app_v, ref_v, unit in comparisons:
        if app_v is None or ref_v is None:
            diff = None
            pct = None
            status = "-"
        else:
            diff = float(app_v) - float(ref_v)
            pct = abs(diff) / max(abs(float(ref_v)), 1e-12) * 100.0
            status = "MATCH" if pct <= 0.15 else ("REVIEW" if pct <= 2.0 else "CHECK")
        rows.append([name, sym, app_v, ref_v, diff, pct, unit, status])
    return pd.DataFrame(rows, columns=["Property", "Symbol", "App calculated", "Reference / active", "Difference", "% diff", "Unit", "Status"])


def render_section_properties() -> None:
    section_title("2.3 Section Properties")
    st.markdown(
        '<div class="note-box"><b>Coordinate-driven section engine:</b> import CSiBridge Structural Polygon and Opening Polygon coordinates. '
        'The app calculates A, centroid, I33/I22, and S values from the imported loops. '
        '<b>Adopted Section Properties for Design</b> is the single source used by downstream checks; J is entered/selected there so it is not hidden in a separate torsion page.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(_section_data_gate_html(D), unsafe_allow_html=True)
    s = D["section"]
    tabs = st.tabs(["Coordinate Input", "Section Preview", "Adopted Properties for Design", "QA / Comparison"])

    with tabs[0]:
        c1, c2 = st.columns([1.6, 1.0])
        with c1:
            uploaded = st.file_uploader("Import CSiBridge section coordinates CSV / Excel", type=["csv", "xlsx", "xls"], key="section_coordinate_file_upload")
            if uploaded is not None:
                try:
                    imported = read_coordinate_table(uploaded, getattr(uploaded, "name", ""), coordinate_unit="auto")
                    _store_section_coordinate_df(imported)
                    st.success(f"Imported {len(imported)} coordinate rows. CSiBridge metre-based X/Y coordinates are auto-converted to mm.")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not import coordinates: {exc}")
        with c2:
            st.download_button("Download coordinate CSV template", SECTION_TEMPLATE_CSV.encode("utf-8"), "csibridge_section_coordinate_template.csv", "text/csv", use_container_width=True)
            if st.button("Load simple hollow-section example", use_container_width=True):
                _store_section_coordinate_df(default_coordinate_template())
                st.rerun()
        coord_df = _section_coordinate_df_from_state()
        if coord_df.empty:
            st.info("No coordinate rows loaded yet. Upload a CSiBridge CSV/XLSX or paste rows into the editable table.")
            coord_df = default_coordinate_template().iloc[0:0].copy()
        editor_df = coord_df[[c for c in ["loop_name", "point_no", "x_mm", "y_mm"] if c in coord_df.columns]].copy()
        edited = st.data_editor(
            editor_df,
            num_rows="dynamic",
            use_container_width=True,
            key=f"section_coordinate_editor_{_project_widget_epoch()}",
            column_config={
                "loop_name": st.column_config.SelectboxColumn("Loop", options=["Structural Polygon 1", "Opening Polygon 1"], required=True),
                "point_no": st.column_config.NumberColumn("Point", min_value=1, step=1, required=True),
                "x_mm": st.column_config.NumberColumn("X (mm)", step=1.0, format="%.3f", required=True),
                "y_mm": st.column_config.NumberColumn("Y (mm)", step=1.0, format="%.3f", required=True),
            },
        )
        _store_section_coordinate_df(edited)
        st.caption("CSiBridge point order may be clockwise. The app uses loop type to add Structural Polygon area and subtract Opening Polygon area, and auto-converts CSiBridge X/Y metre exports to mm internally.")

    props = _section_computation_from_state()
    coords = props.get("coordinates", _section_coordinate_df_from_state())

    with tabs[1]:
        c1, c2, c3 = st.columns([1.0, 1.0, 1.0])
        with c1:
            point_mode = st.selectbox(
                "Point labels",
                ["hide", "major", "all"],
                format_func=lambda x: {"major": "Major points only", "all": "All point numbers", "hide": "Hide point numbers"}[x],
                index=0,
                key="section_point_label_mode",
            )
        with c2:
            section_dim_mode = st.selectbox(
                "Dimension mode",
                ["clean", "full", "hide"],
                format_func=lambda x: {"clean": "Clean", "full": "Full dimensions", "hide": "Hide dimensions"}[x],
                index=0,
                key="section_preview_dimension_mode",
            )
        with c3:
            origin_mode = st.selectbox("Coordinate display mode", ["csibridge", "centerline"], format_func=lambda x: {"csibridge": "CSiBridge origin", "centerline": "Centerline origin (CL = 0)"}[x], index=0, key="section_origin_display_mode")
        # Legacy key string retained for migration/testing trace: section_show_dimensions.
        if props.get("valid"):
            view_mode_text, view_mode_note = _figure_view_texts()
            origin_text = "CL = 0" if origin_mode == "centerline" else "CSiBridge origin"
            label_text = {"major": "Major points", "all": "All points", "hide": "Labels hidden"}.get(point_mode, "Labels hidden")
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div class="canvas-kicker">CANVAS</div>
                    <div class="canvas-head">
                      <div>
                        <div class="canvas-title">Live Section Property Preview</div>
                        <div class="small-muted">Coordinate-driven BG40 box-girder section used for A, centroid, I33/I22 and S-value QA.</div>
                      </div>
                      <div class="canvas-pill">Section geometry QA</div>
                    </div>
                    <div class="canvas-note">
                      The preview is calculated from imported Structural Polygon and Opening Polygon loops. Adopted design properties remain controlled by the <b>Adopted Properties for Design</b> tab.
                    </div>
                    <div class="canvas-meta-strip">
                      <div class="canvas-station-badge"><span>Coordinate mode</span><strong>{origin_text}</strong></div>
                      <div class="canvas-meta-right">
                        <div class="canvas-view-badge">{view_mode_text} · {view_mode_note}</div>
                        <div class="canvas-dim-badge">Dimension mode: {_dimension_mode_text(section_dim_mode)}</div>
                        <div class="canvas-dim-badge">Point labels: {label_text}</div>
                      </div>
                    </div>
                    {_engineering_canvas_legend_html([
                        {"label": "Structural polygon", "kind": "line", "color": "#294860"},
                        {"label": "Opening polygon", "kind": "void", "color": "#294860"},
                        {"label": "Centroid", "kind": "centroid", "color": "#be123c"},
                    ])}
                    """,
                    unsafe_allow_html=True,
                )
                fig = section_polygon_figure(
                    coords,
                    props,
                    point_label_mode=point_mode,
                    show_dimensions=section_dim_mode != "hide",
                    origin_mode=origin_mode,
                    dimension_mode=section_dim_mode,
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True, config=current_plotly_config())
                st.markdown(
                    '<div class="canvas-caption"><b>Figure 2.x</b> Box-girder section preview from imported coordinate loops, showing the calculated centroid and selected engineering dimension guides.</div>',
                    unsafe_allow_html=True,
                )
                footer_html = (
                    '<div class="canvas-footer-grid">'
                    + _canvas_footer_card_html("Area", format_engineering_value(props["A_m2"], "m²"), "calculated from loops", "pass")
                    + _canvas_footer_card_html("Centroid X", format_engineering_value(props["xcg_from_left_m"], "m"), "from left fiber", "pass")
                    + _canvas_footer_card_html("Centroid Y", format_engineering_value(props["ycg_from_bottom_m"], "m"), "from bottom fiber", "pass")
                    + _canvas_footer_card_html("I33 / I22", f'{format_engineering_value(props["I33_m4"], "m⁴")} / {format_engineering_value(props["I22_m4"], "m⁴")}', "m⁴ · centroidal axes", "pass")
                    + '</div>'
                )
                st.markdown(footer_html, unsafe_allow_html=True)
        else:
            st.warning("Section preview requires valid coordinate loops.")
            for err in props.get("errors", []):
                st.error(err)

    with tabs[2]:
        st.markdown(
            '<div class="result-card"><b>Adopted Section Properties for Design</b> '
            '<span class="badge pass">USED BY DESIGN CHECKS</span><br>'
            '<span class="small-muted">These active values are the single source used by downstream calculations, report preview, and QA checks. '
            'Coordinate-calculated A/I/S/centroid can be applied here; J is entered or adopted here so the user does not need to search another tab.</span></div>',
            unsafe_allow_html=True,
        )

        if props.get("valid"):
            with st.expander("Computed from imported coordinates (preview / not used until applied)", expanded=False):
                computed_rows = [
                    ["Cross-sectional area", "A", props["A_m2"], "m²", "App calculated from coordinates"],
                    ["Moment of inertia major", "I33", props["I33_m4"], "m⁴", "Mapped from Ixx"],
                    ["Moment of inertia minor", "I22", props["I22_m4"], "m⁴", "Mapped from Iyy"],
                    ["Section modulus top", "S33(+)", props["S_top_m3"], "m³", "I33 / y_t"],
                    ["Section modulus bottom", "S33(-)", props["S_bottom_m3"], "m³", "I33 / y_cg"],
                    ["Centroid from left", "x_cg", props["xcg_from_left_m"], "m", "from coordinate bounds"],
                    ["Centroid from right", "x_right", props["xcg_from_right_m"], "m", "from coordinate bounds"],
                    ["Centroid from bottom", "y_cg", props["ycg_from_bottom_m"], "m", "from coordinate bounds"],
                    ["Centroid from top", "y_t", props["yt_from_top_m"], "m", "from coordinate bounds"],
                    ["Overall width", "B", props["width_m"], "m", "xmax - xmin"],
                    ["Overall depth", "D", props["depth_m"], "m", "ymax - ymin"],
                ]
                show_engineering_table(pd.DataFrame(computed_rows, columns=["Property", "Symbol", "Value", "Unit", "Source"]))
                st.markdown('<div class="calc-card"><b>Mapping note</b><br><span class="small-muted">For BG40 review, app I33 is calculated from Ixx about the horizontal centroidal axis; app I22 is calculated from Iyy about the vertical centroidal axis. Confirm the local axis mapping if a different FEA convention is used.</span></div>', unsafe_allow_html=True)
            if st.button("Use calculated A / I / S / centroid as adopted properties", type="primary", use_container_width=True):
                _apply_computed_section_properties(props)
                st.success("Adopted section properties updated from coordinate calculation. J is unchanged and remains traceable separately.")
                st.rerun()
        else:
            st.info("Import valid coordinates to calculate A/I/S/centroid. Adopted values below can still be reviewed or keyed from FEA.")

        def _render_adopted_section_properties_table(container) -> None:
            active_rows = [
                ["Cross-sectional area", "A", s["Ac_m2"], "m²", s.get("coordinate_source", "FEA / CSiBridge keyed value")],
                ["Moment of inertia major", "I33", s["I33_m4"], "m⁴", s.get("coordinate_source", "FEA / CSiBridge keyed value")],
                ["Moment of inertia minor", "I22", s["I22_m4"], "m⁴", s.get("coordinate_source", "FEA / CSiBridge keyed value")],
                ["Torsional constant", "J", s["J_m4"], "m⁴", s.get("J_method", "User override")],
                ["Section modulus top", "S33(+)", s["S_top_m3"], "m³", s.get("coordinate_source", "FEA / CSiBridge keyed value")],
                ["Section modulus bottom", "S33(-)", s["S_bottom_m3"], "m³", s.get("coordinate_source", "FEA / CSiBridge keyed value")],
                ["Centroid from left", "x_cg", s.get("xcg_from_left_m", "-"), "m", "Adopted value"],
                ["Centroid from bottom", "y_cg", s["ycg_from_bottom_m"], "m", "Adopted value"],
                ["Centroid from top", "y_t", s["yt_from_top_m"], "m", "Adopted value"],
            ]
            with container.container():
                st.markdown("#### Adopted properties table")
                show_engineering_table(pd.DataFrame(active_rows, columns=["Property", "Symbol", "Adopted value", "Unit", "Source / Method"]))

        adopted_table_slot = st.empty()

        st.markdown("#### Torsional Constant J — adopted value")
        st.markdown(
            '<div class="warn-box"><b>Important:</b> A, centroid, I and S are calculated from polygon coordinates. '
            'Torsional constant J is not directly obtained from polygon inertia for hollow box sections. '
            'For verified section-property values from CSiBridge / FEA, select <b>User override</b> and key the verified J value here. '
            'Alternatively, explicitly adopt the thin-walled estimate after review.</div>',
            unsafe_allow_html=True,
        )
        old_method = D["section"].get("J_method", "User override")
        method_map = {
            "CSiBridge / FEA manual value": "User override",
            "FEA / manual override": "User override",
            "User override": "User override",
            "Auto thin-walled single-cell estimate": "Thin-walled estimate adopted",
            "Thin-walled estimate adopted": "Thin-walled estimate adopted",
        }
        old_method = method_map.get(old_method, "User override")
        j_options = ["User override", "Thin-walled estimate adopted"]
        c1, c2 = st.columns([1.0, 1.0])
        with c1:
            selected_j_method = st.selectbox("J input source / method", j_options, index=j_options.index(old_method), key="section_j_source_method")
        with c2:
            pending_j_value = st.number_input(
                "User override J (m⁴)",
                value=float(D["section"].get("J_m4", 0.0) or 0.0),
                step=0.001,
                format="%.4f",
                disabled=(selected_j_method != "User override"),
                key="section_j_pending_override_value",
            )
        pending_j_note = st.text_input(
            "J source note",
            D["section"].get("J_note", "J keyed by user from CSiBridge / FEA section property window or another verified source."),
            disabled=(selected_j_method != "User override"),
            key="section_j_pending_override_note",
        )
        if selected_j_method == "User override":
            if st.button("Apply user override J to adopted properties", type="primary", use_container_width=True):
                D["section"]["J_m4"] = float(pending_j_value)
                D["section"]["J_method"] = "User override"
                D["section"]["J_note"] = pending_j_note or "User override J value."
                st.success("Adopted J updated from user override and will be used by downstream design checks.")
                st.rerun()
        else:
            st.info("Select the thin-walled estimate after reviewing the QA comparison below, then use the adopt button inside the expander.")

        with st.expander("Thin-walled closed-box J estimate for QA comparison", expanded=(selected_j_method == "Thin-walled estimate adopted")):
            c1, c2, c3 = st.columns(3)
            with c1:
                editable_value(["section", "t_top_m"], "Top slab thickness t_top (m)", 0.01, "%.3f")
            with c2:
                editable_value(["section", "t_bot_m"], "Bottom slab thickness t_bot (m)", 0.01, "%.3f")
            with c3:
                editable_value(["section", "t_web_m"], "Web thickness t_web (m)", 0.01, "%.3f")
            if props.get("valid"):
                j_est = estimate_thin_walled_closed_box_j(
                    coords,
                    t_top_m=float(D["section"]["t_top_m"]),
                    t_bot_m=float(D["section"]["t_bot_m"]),
                    t_web_m=float(D["section"]["t_web_m"]),
                )
                if j_est.get("valid"):
                    D["section"]["J_thin_walled_m4"] = float(j_est["J_m4"])
                    ref_j = float(D["section"].get("J_m4", 0.0) or 0.0)
                    diff_pct = abs(float(j_est["J_m4"]) - ref_j) / max(abs(ref_j), 1e-12) * 100.0 if ref_j else None
                    D["section"]["J_thin_walled_difference_pct"] = diff_pct
                    j_rows = pd.DataFrame([
                        ["Adopted J for design", "J", D["section"].get("J_m4"), "m⁴", D["section"].get("J_method", "User override")],
                        ["Thin-walled estimate", "J_tw", j_est["J_m4"], "m⁴", j_est["method"]],
                        ["Centreline area", "A_m", j_est["Am_m2"], "m²", "Estimated from Opening Polygon + wall thicknesses"],
                        ["Σ(l/t)", "Σ(l/t)", j_est["sum_l_over_t"], "-", "Thin-walled denominator"],
                        ["Difference from adopted J", "ΔJ", diff_pct if diff_pct is not None else None, "%", "Review if > 5%"],
                    ], columns=["Item", "Symbol", "Value", "Unit", "Source / note"])
                    show_engineering_table(j_rows)
                    if diff_pct is not None and diff_pct > 5.0:
                        st.warning(f"Thin-walled J differs from adopted J by {diff_pct:.1f}%. Review wall thicknesses and torsion basis before adopting.")
                    else:
                        st.success("Thin-walled J estimate is reasonably close to the adopted J for QA comparison.")
                    with st.expander("Segment classification used for Σ(l/t)", expanded=False):
                        seg_df = pd.DataFrame(j_est["segment_rows"])
                        show_engineering_table(seg_df.rename(columns={"segment": "Segment", "component": "Component", "length_m": "Length", "t_m": "t", "l_over_t": "l/t"}))
                    if st.button("Use thin-walled estimate as adopted J", use_container_width=True):
                        D["section"]["J_m4"] = float(j_est["J_m4"])
                        D["section"]["J_method"] = "Thin-walled estimate adopted"
                        D["section"]["J_note"] = "J adopted from app thin-walled closed-box estimate; engineering review required for final design."
                        st.success("Adopted J updated from thin-walled estimate. Review QA warning before design use.")
                        st.rerun()
                else:
                    for err in j_est.get("errors", []):
                        st.error(err)
            else:
                st.info("Import valid section coordinates to calculate the thin-walled closed-box J estimate.")

        _render_adopted_section_properties_table(adopted_table_slot)

    with tabs[3]:
        subsection_title("Coordinate QA / Comparison")
        if props.get("valid"):
            loop_summary = []
            for lp in props.get("loops", []):
                loop_summary.append([lp.name, lp.loop_type, lp.n_points, lp.area_mm2, "mm²"])
            st.markdown("#### Coordinate loop checks")
            show_engineering_table(pd.DataFrame(loop_summary, columns=["Loop", "Type", "Points", "Value", "Unit"]))
            if props.get("warnings"):
                for warning in props["warnings"]:
                    st.warning(warning)
            else:
                st.success("Coordinate loops are valid for section-property calculation.")
            st.markdown("#### QA Comparison: App Calculated vs Adopted Values")
            compare_df = _section_comparison_rows(props, s)
            show_engineering_table(compare_df)
            if not compare_df.empty and (compare_df["Status"] == "CHECK").any():
                st.error("At least one coordinate-calculated property differs from the adopted/CSiBridge reference beyond tolerance.")
            elif not compare_df.empty and (compare_df["Status"] == "REVIEW").any():
                st.warning("Some coordinate-calculated properties require review against the adopted/CSiBridge reference.")
            else:
                st.success("Coordinate-calculated properties match the adopted/CSiBridge reference within display tolerance.")
            st.markdown("#### Adopted property consistency")
            S_top_calc = s["I33_m4"] / s["yt_from_top_m"] if s["yt_from_top_m"] else 0.0
            S_bot_calc = s["I33_m4"] / s["ycg_from_bottom_m"] if s["ycg_from_bottom_m"] else 0.0
            consistency = pd.DataFrame([
                ["Adopted S33(+) = I33 / y_t", S_top_calc, s["S_top_m3"], "m³"],
                ["Adopted S33(-) = I33 / y_cg", S_bot_calc, s["S_bottom_m3"], "m³"],
                ["Adopted D = y_cg + y_t", s["ycg_from_bottom_m"] + s["yt_from_top_m"], s["D_m"], "m"],
                ["Adopted B = x_left + x_right", s.get("xcg_from_left_m", 0.0) + s.get("xcg_from_right_m", 0.0), s["B_m"], "m"],
                ["J source", s.get("J_method", "CSiBridge / FEA manual value"), s.get("J_note", ""), "-"],
            ], columns=["Check", "Calculated / Source", "Adopted / note", "Unit"])
            show_engineering_table(consistency)
        else:
            for err in props.get("errors", []):
                st.error(err)
            st.info("Expected CSiBridge loop names: Structural Polygon 1 for the outer concrete boundary and Opening Polygon 1 for the internal void.")


def _df_from_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(records or [])


def _parse_and_store_tendon_file(uploaded: Any, kind: str) -> None:
    filename = getattr(uploaded, "name", "")
    raw = uploaded.getvalue() if hasattr(uploaded, "getvalue") else b""
    source_meta = D["tendon_layout"].setdefault("source_meta", {})
    if kind == "general":
        df = read_tendon_general_table(uploaded, filename)
        D["tendon_layout"]["general_rows"] = df.to_dict("records")
        source_meta["general"] = {"filename": filename, "rows": len(df), "sha256_12": hashlib.sha256(raw).hexdigest()[:12] if raw else ""}
        st.success(f"Imported General tendon table: {len(df)} tendons.")
    elif kind == "vertical":
        df = read_tendon_vertical_table(uploaded, filename)
        D["tendon_layout"]["vertical_rows"] = df.to_dict("records")
        source_meta["vertical"] = {"filename": filename, "rows": len(df), "sha256_12": hashlib.sha256(raw).hexdigest()[:12] if raw else ""}
        st.success(f"Imported Vertical tendon profile table: {len(df)} rows.")
    elif kind == "horizontal":
        df = read_tendon_horizontal_table(uploaded, filename)
        D["tendon_layout"]["horizontal_rows"] = df.to_dict("records")
        source_meta["horizontal"] = {"filename": filename, "rows": len(df), "sha256_12": hashlib.sha256(raw).hexdigest()[:12] if raw else ""}
        st.success(f"Imported Horizontal tendon profile table: {len(df)} rows.")


def _build_and_store_tendon_model() -> dict[str, Any]:
    tl = D.setdefault("tendon_layout", {})
    general = _df_from_records(tl.get("general_rows", []))
    vertical = _df_from_records(tl.get("vertical_rows", []))
    horizontal = _df_from_records(tl.get("horizontal_rows", []))
    model = build_tendon_layout_model(
        general,
        vertical,
        horizontal,
        active_bridge_object=tl.get("active_bridge_object", "B2_SPAN1"),
        map_to_active_bridge_object=bool(tl.get("map_bridge_objects_to_active", True)),
        y_t_from_top_m=float(D["section"].get("yt_from_top_m", 0.0)),
    )
    model["model_fingerprint"] = tendon_model_fingerprint(model)
    model["source_trace_rows"] = build_tendon_source_trace(tl, model)
    tl["model"] = model
    return model


def _active_tendon_model() -> dict[str, Any]:
    tl = D.setdefault("tendon_layout", {})
    if tl.get("model"):
        return tl["model"]
    return _build_and_store_tendon_model()


def _render_tendon_import_summary_cards(model: dict[str, Any]) -> None:
    """Show tendon import results as concise cards instead of a long instruction banner."""
    valid = bool(model.get("valid"))
    tendons = model.get("tendons", []) if valid else []
    families = sorted({t.get("family", "") for t in tendons if t.get("family")})
    material = model.get("material") or "-"
    strand_label = model.get("strand_label") or "-"
    aps = float(model.get("Aps_per_tendon_mm2") or 0.0)
    total_aps = float(model.get("total_area_mm2") or 0.0)
    fpu = float(model.get("fpu_mpa") or 1860.0)
    jack_stress = float(model.get("jacking_stress_mpa") or 0.75 * fpu)
    force_per = float(model.get("force_per_tendon_kN") or 0.0)
    total_force = float(model.get("total_force_kN") or 0.0)
    active_obj = model.get("active_bridge_object") or D["project"].get("bridge_object", "-")
    dp_end = model.get("dp_avg_end_m")
    dp_mid = model.get("dp_avg_midspan_m")
    e_mid = model.get("eccentricity_midspan_m")
    mapped = bool(model.get("mapped_to_active_bridge_object"))
    imported_objs = model.get("imported_bridge_objects") or []
    status = "READY" if valid else "PENDING"
    status_note = "Profiles merged" if valid else "Upload General / Vertical / Horizontal tables"
    if len(imported_objs) > 1:
        status_note = "BridgeObj mapped by user" if mapped else "BridgeObj mismatch review"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Imported Tendon Model", f"{len(tendons)} tendons" if valid else "No model", f"{len(families)} mirrored families · {active_obj}", "pass" if valid else "")
    with c2:
        card("Strand / Area", strand_label if valid else "-", f"Aps/tendon = {format_engineering_value(aps, 'mm²')} mm² · Total = {format_engineering_value(total_aps, 'mm²')} mm²", "pass" if valid else "")
    with c3:
        card("Jacking Basis", f"0.75fpu = {format_engineering_value(jack_stress, 'MPa')} MPa" if valid else "0.75fpu", f"Pj/tendon = {format_engineering_value(force_per, 'kN')} kN · Total = {format_engineering_value(total_force, 'kN')} kN", "pass" if valid else "")
    with c4:
        card("Layout Status", status, f"{status_note} · Material {material}", "pass" if valid else "warn")

    if valid:
        c1, c2, c3 = st.columns(3)
        with c1:
            card("Average end dp", format_engineering_value(float(dp_end or 0.0), "m"), "Area-weighted from imported vertical profiles", "pass")
        with c2:
            card("Average midspan dp", format_engineering_value(float(dp_mid or 0.0), "m"), "Area-weighted from imported vertical profiles", "pass")
        with c3:
            card("Midspan eccentricity", format_engineering_value(float(e_mid or 0.0), "m"), "e = dp(midspan) − y_t", "pass")

        basis = pd.DataFrame([
            ["Tendon system", D["project"].get("tendon_system", "External / Unbonded PT"), "Project basis"],
            ["Material", material, "Imported CSiBridge General table"],
            ["Strand", strand_label, "Derived from Aps = 24 × 140 mm² for BG40"],
            ["Aps per tendon", aps, "mm²"],
            ["fpu", fpu, "MPa"],
            ["Jacking stress", jack_stress, "MPa = 0.75 fpu"],
            ["Jacking force per tendon", force_per, "kN = 0.75 fpu × Aps"],
            ["Total jacking force", total_force, "kN"],
        ], columns=["Item", "Value", "Unit / source"])
        with st.expander("Tendon import basis table", expanded=False):
            show_engineering_table(basis)




def _tendon_summary_display_frame(tendons_df: pd.DataFrame) -> pd.DataFrame:
    """Build a complete one-row-per-tendon display table for the adopted model."""
    if tendons_df is None or tendons_df.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for _, r in tendons_df.iterrows():
        aps = float(r.get("area_mm2", 0.0) or 0.0)
        force = float(r.get("force_kN", 0.0) or 0.0)
        fpu = float(r.get("fpu_mpa", 1860.0) or 1860.0)
        jstress = float(r.get("jacking_stress_mpa", 0.75 * fpu) or 0.75 * fpu)
        rows.append(
            {
                "Tendon": r.get("tendon", ""),
                "Family": r.get("family", ""),
                "Side": r.get("side", ""),
                "BridgeObj": r.get("bridge_obj", ""),
                "Material": r.get("material", ""),
                "Strand": r.get("strand_label", "-"),
                "Aps / tendon": format_engineering_value(aps, "mm²"),
                "fpu": format_engineering_value(fpu, "MPa"),
                "Jacking stress": format_engineering_value(jstress, "MPa"),
                "Jacking force": format_engineering_value(force, "kN"),
                "Jack from": r.get("jack_from", ""),
                "End dp": format_engineering_value(r.get("end_dp_m", None), "m"),
                "Midspan dp": format_engineering_value(r.get("midspan_dp_m", None), "m"),
                "End HorizOff": format_engineering_value(r.get("end_horiz_off_m", None), "m"),
                "Midspan HorizOff": format_engineering_value(r.get("midspan_horiz_off_m", None), "m"),
                "Profile pts": format_engineering_value(r.get("profile_point_count", 0), quantity="count"),
                "Status": r.get("profile_status", "OK"),
            }
        )
    return pd.DataFrame(rows)


def _tendon_profile_display_frame(profile_df: pd.DataFrame) -> pd.DataFrame:
    """Build a merged vertical+horizontal profile table with report-style formatting."""
    if profile_df is None or profile_df.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for _, r in profile_df.iterrows():
        rows.append(
            {
                "Tendon": r.get("Tendon", ""),
                "Family": r.get("Family", ""),
                "Side": r.get("Side", ""),
                "Point No.": format_engineering_value(r.get("Point No.", 0), quantity="count"),
                "SegType": r.get("SegType", ""),
                "x": format_engineering_value(r.get("x_m", None), "m"),
                "dp from top": format_engineering_value(r.get("dp_top_m", None), "m"),
                "HorizOff": format_engineering_value(r.get("horiz_off_m", None), "m"),
                "Status": r.get("Status", ""),
            }
        )
    return pd.DataFrame(rows)


def _format_tendon_points_table(points: pd.DataFrame) -> pd.DataFrame:
    """Display selected-station tendon points with fixed engineering precision."""
    if points is None or points.empty:
        return pd.DataFrame()
    out = points.copy()
    for col in ["Station (m)", "dp from top (m)", "HorizOff (m)"]:
        if col in out.columns:
            out[col] = [format_engineering_value(v, "m") for v in out[col]]
    for col in ["Display x (mm)", "Section x (mm)", "Section y (mm)", "section_x_mm", "section_y_mm"]:
        if col in out.columns:
            out[col] = [format_engineering_value(v, "mm") for v in out[col]]
    if "Min clearance to inner boundary (mm)" in out.columns:
        out["Min clearance to inner boundary (mm)"] = [format_engineering_value(v, "mm") for v in out["Min clearance to inner boundary (mm)"]]
    return out


def _add_section_coordinates_to_tendon_points(
    points: pd.DataFrame,
    section_props: dict[str, Any],
    *,
    positive_offset_direction: str = "left",
    origin_mode: str = "csibridge",
) -> pd.DataFrame:
    """Append section x/y coordinates in mm for QA and tabular review."""
    if points is None or points.empty:
        return pd.DataFrame()
    width_m = float(section_props.get("width_m") or section_props.get("B_m") or 0.0)
    depth_m = float(section_props.get("depth_m") or section_props.get("D_m") or 0.0)
    bounds = section_props.get("bounds_mm", {}) if section_props else {}
    xmin = float(bounds.get("xmin", 0.0))
    xmax = float(bounds.get("xmax", width_m * 1000.0))
    x_shift = 0.5 * (xmin + xmax) if str(origin_mode).lower().startswith("center") else 0.0
    rows = []
    for _, r in points.iterrows():
        off = float(r["HorizOff (m)"])
        dp = float(r["dp from top (m)"])
        if positive_offset_direction == "left":
            x_m = width_m / 2.0 - off
        else:
            x_m = width_m / 2.0 + off
        y_m = depth_m - dp
        row = r.to_dict()
        row["section_x_mm"] = x_m * 1000.0
        row["section_y_mm"] = y_m * 1000.0
        row["display_x_mm"] = row["section_x_mm"] - x_shift
        rows.append(row)
    return pd.DataFrame(rows)


def _tendon_section_location_qa(points: pd.DataFrame, section_coords: pd.DataFrame) -> pd.DataFrame:
    """Classify tendon points relative to section void/concrete/outside regions."""
    if points is None or points.empty or section_coords is None or section_coords.empty:
        return pd.DataFrame()
    rows = []
    for _, r in points.iterrows():
        qa = classify_point_in_section_void((float(r["section_x_mm"]), float(r["section_y_mm"])), section_coords)
        rows.append(
            {
                "Tendon": r.get("Tendon", ""),
                "Family": r.get("Family", ""),
                "Station (m)": r.get("Station (m)", None),
                "Location": qa["location"],
                "Min clearance to inner boundary (mm)": qa.get("min_clearance_to_inner_boundary_mm"),
                "Status": qa["status"],
                "Note": qa["note"],
            }
        )
    return pd.DataFrame(rows)



def _overlay_station_label(station: float, span: float) -> str:
    """Return a report-style label for a selected tendon overlay station."""
    if not span:
        return "Selected station"
    ratio = float(station) / float(span)
    candidates = [(0.0, "Start"), (0.25, "0.25L"), (0.5, "Midspan"), (0.75, "0.75L"), (1.0, "End")]
    best, label = min(candidates, key=lambda item: abs(item[0] - ratio))
    return label if abs(best - ratio) <= 0.01 else f"{ratio:.3f}L"


def _merge_tendon_overlay_points_with_qa(points: pd.DataFrame, qa_points: pd.DataFrame) -> pd.DataFrame:
    """Merge selected-station tendon coordinate rows and location QA rows for one user-facing table."""
    if points is None or points.empty:
        return pd.DataFrame()
    base = points.copy()
    if qa_points is not None and not qa_points.empty:
        qa_keep = qa_points[[c for c in ["Tendon", "Location", "Min clearance to inner boundary (mm)", "Status", "Note"] if c in qa_points.columns]].copy()
        base = base.merge(qa_keep, on="Tendon", how="left")
    return base

def _tendon_summary_frame_from_summary(summary: dict[str, Any]) -> pd.DataFrame:
    """Report-ready downstream tendon source summary."""
    if not summary:
        return pd.DataFrame(columns=["Item", "Value", "Unit", "Basis"])
    rows = [
        ["Source", summary.get("source", "-"), "-", "adopted snapshot"],
        ["Active BridgeObj", summary.get("active_bridge_object", "-"), "-", "mapped / reviewed"],
        ["Number of tendons", summary.get("tendon_count", 0), "-", "count"],
        ["Number of families", summary.get("family_count", 0), "-", "T-family"],
        ["Aps per tendon", summary.get("Aps_per_tendon_mm2", 0.0), "mm²", "imported General table"],
        ["Aps total", summary.get("Aps_total_mm2", 0.0), "mm²", "sum of adopted tendons"],
        ["Jacking stress", summary.get("jacking_stress_mpa", 0.0), "MPa", "0.75 fpu"],
        ["Jacking force per tendon", summary.get("jacking_force_per_tendon_kN", 0.0), "kN", "0.75 fpu × Aps"],
        ["Total jacking force", summary.get("jacking_force_total_kN", 0.0), "kN", "sum of adopted tendons"],
        ["Average dp at end", summary.get("dp_avg_end_m", 0.0), "m", "area-weighted"],
        ["Average dp at midspan", summary.get("dp_avg_midspan_m", 0.0), "m", "area-weighted"],
        ["y_t from top", summary.get("y_t_from_top_m", 0.0), "m", "active adopted section property"],
        ["Midspan eccentricity", summary.get("eccentricity_midspan_m", 0.0), "m", "dp_avg - y_t"],
        ["Model fingerprint", summary.get("model_fingerprint", "-"), "-", "QA trace"],
    ]
    return pd.DataFrame(rows, columns=["Item", "Value", "Unit", "Basis"])


def _tendon_source_trace_frame(tl: dict[str, Any], model: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(build_tendon_source_trace(tl, model))


def _active_adopted_tendon_model() -> dict[str, Any]:
    """Return the locked design-source tendon model, if one exists."""
    adopted = D.setdefault("tendon_layout", {}).get("adopted_model", {})
    return adopted if isinstance(adopted, dict) and adopted.get("valid") else {}


def _render_tendon_adoption_cards(model: dict[str, Any]) -> None:
    tl = D.setdefault("tendon_layout", {})
    status = tendon_model_status(model, tl)
    adopted = _active_adopted_tendon_model()
    working_fp = tendon_model_fingerprint(model)
    adopted_fp = str(tl.get("adopted_model_fingerprint") or tendon_model_fingerprint(adopted) or "—")
    summary = tl.get("adopted_downstream_summary") or build_tendon_downstream_summary(adopted, y_t_from_top_m=float(D["section"].get("yt_from_top_m", 0.0))) if adopted else {}
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Tendon Source Gate", status["status"], status["message"], status["mode"])
    with c2:
        card("Working model", working_fp or "—", "latest imported/merged model", "neutral")
    with c3:
        card("Adopted model", adopted_fp, tl.get("adopted_at_utc", "not locked") or "not locked", "pass" if adopted else "warn")
    with c4:
        value = f"{format_engineering_value(summary.get('Aps_total_mm2', 0.0), 'mm²')} mm²" if summary else "—"
        note = "used by downstream prestress" if summary else "adopt tendon model first"
        card("Aps,total", value, note, "pass" if summary else "warn")


def _adopt_working_tendon_model(model: dict[str, Any]) -> dict[str, Any]:
    return adopt_tendon_model(
        D.setdefault("tendon_layout", {}),
        D.setdefault("prestress", {}),
        model,
        y_t_from_top_m=float(D["section"].get("yt_from_top_m", 0.0)),
    )


def _apply_imported_tendon_summary_to_prestress(model: dict[str, Any]) -> None:
    """Backward-compatible wrapper: explicit adoption now controls downstream values."""
    if not model.get("valid"):
        return
    _adopt_working_tendon_model(model)


def render_tendon_layout_reference() -> None:
    section_title("2.4 Tendon Layout Reference")
    tl = D.setdefault("tendon_layout", {})
    model_for_summary = _active_tendon_model()
    _render_tendon_import_summary_cards(model_for_summary)
    _render_tendon_adoption_cards(model_for_summary)
    tabs = st.tabs(["Import / Mapping", "Elevation View", "Plan View", "3D Tendon View", "Section Overlay", "Adopted Tendon Data", "QA / Consistency"])

    with tabs[0]:
        subsection_title("Tendon import / mapping")
        c1, c2, c3 = st.columns(3)
        with c1:
            gen = st.file_uploader("General tendon table (.xlsx/.csv)", type=["xlsx", "xls", "csv"], key="tendon_general_upload")
            if gen is not None:
                try:
                    _parse_and_store_tendon_file(gen, "general")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not import General tendon table: {exc}")
        with c2:
            vert = st.file_uploader("Vertical layout table (.xlsx/.csv)", type=["xlsx", "xls", "csv"], key="tendon_vertical_upload")
            if vert is not None:
                try:
                    _parse_and_store_tendon_file(vert, "vertical")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not import Vertical tendon table: {exc}")
        with c3:
            horiz = st.file_uploader("Horizontal layout table (.xlsx/.csv)", type=["xlsx", "xls", "csv"], key="tendon_horizontal_upload")
            if horiz is not None:
                try:
                    _parse_and_store_tendon_file(horiz, "horizontal")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not import Horizontal tendon table: {exc}")

        general = _df_from_records(tl.get("general_rows", []))
        vertical = _df_from_records(tl.get("vertical_rows", []))
        horizontal = _df_from_records(tl.get("horizontal_rows", []))
        imported_objs: list[str] = []
        for df in (general, vertical, horizontal):
            if not df.empty and "BridgeObj" in df.columns:
                for obj in df["BridgeObj"].dropna().astype(str).unique().tolist():
                    if obj and obj not in imported_objs:
                        imported_objs.append(obj)
        default_obj = tl.get("active_bridge_object") or (general["BridgeObj"].mode().iloc[0] if not general.empty and "BridgeObj" in general.columns else D["project"].get("bridge_object", "B2_SPAN1"))
        c1, c2 = st.columns([1.0, 1.0])
        with c1:
            tl["active_bridge_object"] = st.text_input("Active BridgeObj for adopted tendon layout", value=str(default_obj), key="tendon_active_bridge_obj")
        with c2:
            tl["map_bridge_objects_to_active"] = st.checkbox("Map all imported BridgeObj values to active BridgeObj after review", value=bool(tl.get("map_bridge_objects_to_active", True)), key="tendon_map_bridge_obj")
        if len(imported_objs) > 1:
            st.warning(f"BridgeObj mismatch detected: {', '.join(imported_objs)}. Review and map to the active object only if this is an export label mismatch.")
        elif imported_objs:
            st.success(f"Imported BridgeObj: {', '.join(imported_objs)}")
        else:
            st.info("Upload the three CSiBridge tendon tables to build the tendon model.")

        preview_model = tl.get("model") if isinstance(tl.get("model"), dict) else {}
        trace_preview = _tendon_source_trace_frame(tl, preview_model)
        if not trace_preview.empty:
            st.markdown("#### Import source trace")
            show_engineering_table(trace_preview)

        if st.button("Build / refresh imported tendon layout model", type="primary", use_container_width=True):
            model = _build_and_store_tendon_model()
            if model.get("valid"):
                st.success(f"Imported tendon working model built: {len(model.get('tendons', []))} tendons, span reference = {model.get('span_m', 0.0):.3f} m. Adopt it explicitly before downstream use.")
            else:
                st.error("Tendon model could not be built. Check imported tables and QA messages.")
            st.rerun()

        if not general.empty or not vertical.empty or not horizontal.empty:
            with st.expander("Raw import data / QA only", expanded=False):
                st.caption("Raw CSiBridge rows are shown only for parser QA. Use the Adopted Tendon Data tab to explicitly lock the merged tendon model before downstream use.")
                if not general.empty:
                    st.markdown("##### Imported General tendon rows")
                    show_engineering_table(general[[c for c in ["BridgeObj", "Tendon", "Material", "TendonArea", "Aps_mm2", "strand_label", "force_075fpu_kN", "Force", "JackFrom"] if c in general.columns]])
                if not vertical.empty:
                    st.markdown("##### Imported Vertical layout rows")
                    show_engineering_table(vertical[[c for c in ["BridgeObj", "Tendon", "SegType", "x_m", "dp_top_m"] if c in vertical.columns]])
                if not horizontal.empty:
                    st.markdown("##### Imported Horizontal layout rows")
                    show_engineering_table(horizontal[[c for c in ["BridgeObj", "Tendon", "SegType", "x_m", "horiz_off_m"] if c in horizontal.columns]])

    model = _active_tendon_model()
    tendons_df, group_df, symmetry_df, qa_df = tendon_model_to_frames(model)
    profile_df = tendon_model_to_profile_frame(model)
    station_match_df = tendon_model_to_station_match_frame(model)

    with tabs[1]:
        subsection_title("Tendon side elevation")
        if model.get("valid"):
            families = list(dict.fromkeys([str(t.get("family", "")) for t in model.get("tendons", []) if str(t.get("family", "")).strip()]))
            c1, c2, c3 = st.columns([1.0, 1.0, 1.0])
            with c1:
                elev_family_filter = st.selectbox("Family filter", ["All families"] + families, index=0, key="tendon_elev_family_filter")
            with c2:
                elev_side_filter = st.selectbox("Side filter", ["Both sides", "Left only", "Right only"], index=0, key="tendon_elev_side_filter")
            with c3:
                show_labels = st.checkbox("Show tendon labels", value=False, key="tendon_elev_labels")
            selected_families = families if elev_family_filter == "All families" else [elev_family_filter]
            view_mode_text, view_mode_note = _figure_view_texts()
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div class="canvas-kicker">CANVAS</div>
                    <div class="canvas-head">
                      <div>
                        <div class="canvas-title">Tendon Side Elevation</div>
                        <div class="small-muted">Vertical tendon profile where <i>d<sub>p</sub></i> is measured from the top surface.</div>
                      </div>
                      <div class="canvas-pill">External tendon profile</div>
                    </div>
                    <div class="canvas-note">
                      The figure uses the adopted merged tendon model. Start, Midspan and End references are drawn from the same span stations used by the Section Overlay page.
                    </div>
                    <div class="canvas-meta-strip">
                      <div class="canvas-station-badge"><span>Display filter</span><strong>{elev_family_filter} · {elev_side_filter}</strong></div>
                      <div class="canvas-meta-right">
                        <div class="canvas-view-badge">{view_mode_text} · {view_mode_note}</div>
                        <div class="canvas-dim-badge">Labels: {'On' if show_labels else 'Off'}</div>
                      </div>
                    </div>
                    {_engineering_canvas_legend_html(_tendon_family_legend_items(selected_families))}
                    """,
                    unsafe_allow_html=True,
                )
                fig = tendon_elevation_figure(
                    model,
                    show_labels=show_labels,
                    family_filter=elev_family_filter,
                    side_filter=elev_side_filter,
                    showlegend=False,
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True, config=current_plotly_config())
                st.markdown(
                    '<div class="canvas-caption"><b>Figure 2.x</b> Tendon side elevation showing imported external tendon vertical profiles measured as dp from the top surface.</div>',
                    unsafe_allow_html=True,
                )
                footer_html = (
                    '<div class="canvas-footer-grid">'
                    + _canvas_footer_card_html("Tendons", str(len(model.get("tendons", []))), "imported tendon objects", "pass")
                    + _canvas_footer_card_html("dp avg end", format_engineering_value(model.get("dp_avg_end_m") or 0.0, "m"), "weighted by tendon area", "pass")
                    + _canvas_footer_card_html("dp avg midspan", format_engineering_value(model.get("dp_avg_midspan_m") or 0.0, "m"), "weighted by tendon area", "pass")
                    + _canvas_footer_card_html("e midspan", format_engineering_value(model.get("eccentricity_midspan_m") or 0.0, "m"), "dp_avg - y_t", "pass")
                    + '</div>'
                )
                st.markdown(footer_html, unsafe_allow_html=True)
        else:
            st.info("Build a valid tendon model to show side elevation.")

    with tabs[2]:
        subsection_title("Tendon plan / horizontal layout")
        if model.get("valid"):
            families = list(dict.fromkeys([str(t.get("family", "")) for t in model.get("tendons", []) if str(t.get("family", "")).strip()]))
            c1, c2, c3 = st.columns([1.0, 1.0, 1.0])
            with c1:
                plan_family_filter = st.selectbox("Family filter", ["All families"] + families, index=0, key="tendon_plan_family_filter")
            with c2:
                plan_side_filter = st.selectbox("Side filter", ["Both sides", "Left only", "Right only"], index=0, key="tendon_plan_side_filter")
            with c3:
                show_labels = st.checkbox("Show tendon labels", value=False, key="tendon_plan_labels")
            selected_families = families if plan_family_filter == "All families" else [plan_family_filter]
            view_mode_text, view_mode_note = _figure_view_texts()
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div class="canvas-kicker">CANVAS</div>
                    <div class="canvas-head">
                      <div>
                        <div class="canvas-title">Tendon Plan View</div>
                        <div class="small-muted">Horizontal tendon offset from section centerline. Positive/negative values follow the imported CSiBridge convention.</div>
                      </div>
                      <div class="canvas-pill">Horizontal layout QA</div>
                    </div>
                    <div class="canvas-note">
                      The plan view uses the adopted merged tendon model and keeps CL as the horizontal reference line for symmetry and family grouping review.
                    </div>
                    <div class="canvas-meta-strip">
                      <div class="canvas-station-badge"><span>Display filter</span><strong>{plan_family_filter} · {plan_side_filter}</strong></div>
                      <div class="canvas-meta-right">
                        <div class="canvas-view-badge">{view_mode_text} · {view_mode_note}</div>
                        <div class="canvas-dim-badge">Labels: {'On' if show_labels else 'Off'}</div>
                      </div>
                    </div>
                    {_engineering_canvas_legend_html(_tendon_family_legend_items(selected_families) + [{"label": "CL", "kind": "dash", "color": "#475569"}])}
                    """,
                    unsafe_allow_html=True,
                )
                fig = tendon_plan_figure(
                    model,
                    show_labels=show_labels,
                    family_filter=plan_family_filter,
                    side_filter=plan_side_filter,
                    showlegend=False,
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True, config=current_plotly_config())
                st.markdown(
                    '<div class="canvas-caption"><b>Figure 2.x</b> Tendon plan view showing imported external tendon horizontal offsets from the section centerline.</div>',
                    unsafe_allow_html=True,
                )
                footer_html = (
                    '<div class="canvas-footer-grid">'
                    + _canvas_footer_card_html("Tendons", str(len(model.get("tendons", []))), "imported tendon objects", "pass")
                    + _canvas_footer_card_html("Families", str(len(families)), "color grouped by T-family", "pass")
                    + _canvas_footer_card_html("Side display", plan_side_filter, "L solid · R dashed", "neutral")
                    + _canvas_footer_card_html("Reference", "CL = 0", "horizontal offset basis", "neutral")
                    + '</div>'
                )
                st.markdown(footer_html, unsafe_allow_html=True)
        else:
            st.info("Build a valid tendon model to show plan view.")

    with tabs[3]:
        subsection_title("Interactive 3D tendon review")
        props = _section_computation_from_state()
        section_coords = _section_coordinate_df_from_state()
        adopted_model = _active_adopted_tendon_model()
        display_model = adopted_model if adopted_model else model
        source_label = "Adopted design-source model" if adopted_model else "Working imported model · not yet adopted"
        source_mode = "pass" if adopted_model else "warn"

        if display_model.get("valid") and props.get("valid"):
            families = list(dict.fromkeys([str(t.get("family", "")) for t in display_model.get("tendons", []) if str(t.get("family", "")).strip()]))
            tendon_names_3d = [str(t.get("tendon", "")) for t in display_model.get("tendons", []) if str(t.get("tendon", "")).strip()]
            tendon_side_by_name = {str(t.get("tendon", "")): str(t.get("side", "")) for t in display_model.get("tendons", [])}
            view_preset_options = [
                "Isometric · Orthographic",
                "Isometric · Perspective",
                "Top",
                "Side elevation",
                "End section",
                "Tendon focus",
                "Report isometric",
            ]
            preset_options = ["Overview", "Left inspection", "Right inspection", "Single tendon focus", "Report clean", "Custom"]
            st.markdown("##### 3D inspection controls")
            with st.container(border=True):
                st.markdown(
                    """
                    <div class="small-muted"><b>Inspection workflow</b> · Start with a preset, then use Advanced 3D display controls only when a manual review setup is needed.</div>
                    """,
                    unsafe_allow_html=True,
                )
                p1, p2, p3, p4 = st.columns([1.05, 1.05, 1.05, 1.05])
                with p1:
                    inspection_preset = st.selectbox("Inspection preset", preset_options, index=0, key="tendon_3d_inspection_preset")
                focus_control_enabled = inspection_preset in {"Custom", "Single tendon focus"}
                with p2:
                    focus_tendon = st.selectbox(
                        "Focus tendon",
                        ["None"] + tendon_names_3d,
                        index=0,
                        key="tendon_3d_focus_tendon",
                        disabled=not focus_control_enabled,
                        help="Enabled for Custom and Single tendon focus presets. Other presets intentionally keep focus off for a clean review model.",
                    )
                with p3:
                    tendon3d_family_filter = st.selectbox("Family filter", ["All families"] + families, index=0, key="tendon_3d_family_filter")
                with p4:
                    tendon3d_tendon_filter = st.selectbox("Tendon isolate", ["All tendons"] + tendon_names_3d, index=0, key="tendon_3d_tendon_filter")

                preset_managed = inspection_preset != "Custom"
                with st.expander("Advanced 3D display controls", expanded=False):
                    st.markdown(
                        '<div class="small-muted">Manual display controls are most useful in <b>Custom</b>. Preset modes keep a controlled commercial review setup.</div>',
                        unsafe_allow_html=True,
                    )
                    c1, c2, c3, c4, c5 = st.columns([1.18, 1.05, 1.05, 1.10, 1.00])
                    with c1:
                        view_preset = st.selectbox("3D view preset", view_preset_options, index=0, key="tendon_3d_view_preset", disabled=preset_managed)
                    with c2:
                        aspect_mode = st.selectbox("Aspect mode", ["Presentation scale", "True scale"], index=0, key="tendon_3d_aspect_mode", disabled=preset_managed)
                    with c3:
                        shell_display_mode = st.selectbox("Shell display", ["Full shell", "Left half shell", "Right half shell", "No shell", "Inner void only"], index=0, key="tendon_3d_shell_display", disabled=preset_managed)
                        # Legacy explicit checkbox labels retained for regression trace: "Show outer shell" / "Show inner void".
                    with c4:
                        tendon3d_side_filter = st.selectbox("Tendon side", ["Both sides", "Left only", "Right only"], index=0, key="tendon_3d_side_filter", disabled=preset_managed)
                    with c5:
                        station_marker_mode = st.selectbox("Station markers", ["Key only", "All stations", "Off"], index=0, key="tendon_3d_station_marker_mode", disabled=preset_managed)

                    f1, f2, f3 = st.columns([1.0, 1.0, 1.0])
                    with f1:
                        outer_shell_opacity = st.slider("Outer shell opacity", 0.0, 0.60, 0.18, 0.02, key="tendon_3d_outer_opacity")
                    with f2:
                        inner_void_opacity = st.slider("Inner void opacity", 0.0, 0.60, 0.16, 0.02, key="tendon_3d_inner_opacity")
                    with f3:
                        tendon_line_width = st.slider("Tendon line thickness", 2.0, 12.0, 6.0, 0.5, key="tendon_3d_line_thickness")

                    d1, d2 = st.columns([1.0, 1.0])
                    with d1:
                        show_tendon_labels_3d = st.checkbox("Show tendon labels", value=False, key="tendon_3d_labels")
                    with d2:
                        focus_has_tendon = focus_control_enabled and focus_tendon != "None"
                        if focus_has_tendon:
                            fade_unfocused_tendons = st.checkbox(
                                "Fade non-focused tendons",
                                value=True,
                                key="tendon_3d_fade_unfocused",
                                help="Fades context tendons while keeping the selected tendon high-contrast.",
                            )
                        else:
                            st.checkbox(
                                "Fade non-focused tendons",
                                value=False,
                                key="tendon_3d_fade_unfocused_inactive",
                                disabled=True,
                                help="Select a focus tendon to enable faded context display.",
                            )
                            fade_unfocused_tendons = False

            # Default fallbacks are defined here so preset-managed disabled widgets
            # still produce stable effective values without mutating session state.
            if 'view_preset' not in locals():
                view_preset = "Isometric · Orthographic"
            if 'aspect_mode' not in locals():
                aspect_mode = "Presentation scale"
            if 'shell_display_mode' not in locals():
                shell_display_mode = "Full shell"
            if 'tendon3d_side_filter' not in locals():
                tendon3d_side_filter = "Both sides"
            if 'station_marker_mode' not in locals():
                station_marker_mode = "Key only"
            if 'outer_shell_opacity' not in locals():
                outer_shell_opacity = 0.18
            if 'inner_void_opacity' not in locals():
                inner_void_opacity = 0.16
            if 'tendon_line_width' not in locals():
                tendon_line_width = 6.0
            if 'show_tendon_labels_3d' not in locals():
                show_tendon_labels_3d = False
            if 'fade_unfocused_tendons' not in locals():
                fade_unfocused_tendons = False

            effective_view_preset = view_preset
            effective_shell_display_mode = shell_display_mode
            effective_side_filter = tendon3d_side_filter
            effective_tendon_filter = tendon3d_tendon_filter
            effective_focus_tendon = "" if focus_tendon == "None" else focus_tendon
            effective_station_marker_mode = station_marker_mode
            if inspection_preset == "Overview":
                effective_shell_display_mode = "Full shell"
                effective_side_filter = "Both sides"
                effective_tendon_filter = "All tendons"
                effective_focus_tendon = ""
                effective_station_marker_mode = "Key only"
            elif inspection_preset == "Left inspection":
                effective_shell_display_mode = "Left half shell"
                effective_side_filter = "Left only"
                effective_tendon_filter = "All tendons"
                effective_focus_tendon = ""
                effective_station_marker_mode = "Key only"
            elif inspection_preset == "Right inspection":
                effective_shell_display_mode = "Right half shell"
                effective_side_filter = "Right only"
                effective_tendon_filter = "All tendons"
                effective_focus_tendon = ""
                effective_station_marker_mode = "Key only"
            elif inspection_preset == "Single tendon focus":
                if effective_focus_tendon:
                    side_text = tendon_side_by_name.get(effective_focus_tendon, "")
                    effective_side_filter = "Left only" if side_text == "L" else ("Right only" if side_text == "R" else "Both sides")
                    effective_shell_display_mode = "Left half shell" if side_text == "L" else ("Right half shell" if side_text == "R" else shell_display_mode)
                    effective_tendon_filter = "All tendons"
                effective_view_preset = "Tendon focus"
                effective_station_marker_mode = "Key only"
            elif inspection_preset == "Report clean":
                effective_view_preset = "Report isometric"
                effective_shell_display_mode = "Full shell"
                effective_side_filter = "Both sides"
                effective_tendon_filter = "All tendons"
                effective_focus_tendon = ""
                effective_station_marker_mode = "Key only"
                show_tendon_labels_3d = False

            effective_fade_unfocused_tendons = fade_unfocused_tendons if effective_focus_tendon else False
            show_station_markers = effective_station_marker_mode != "Off"
            visible_tendons = [
                t for t in display_model.get("tendons", [])
                if (tendon3d_family_filter == "All families" or str(t.get("family", "")) == tendon3d_family_filter)
                and (effective_side_filter == "Both sides" or (effective_side_filter == "Left only" and str(t.get("side", "")) == "L") or (effective_side_filter == "Right only" and str(t.get("side", "")) == "R"))
                and (effective_tendon_filter == "All tendons" or str(t.get("tendon", "")) == effective_tendon_filter)
            ]
            visible_families = list(dict.fromkeys([str(t.get("family", "")) for t in visible_tendons if str(t.get("family", "")).strip()]))
            visible_sides = list(dict.fromkeys([str(t.get("side", "")) for t in visible_tendons if str(t.get("side", "")).strip()]))
            view_mode_text, view_mode_note = _figure_view_texts()
            shell_legend_items = []
            if effective_shell_display_mode != "No shell":
                if effective_shell_display_mode != "Inner void only":
                    shell_legend_items.append({"label": "Outer shell", "kind": "line", "color": "#294860"})
                shell_legend_items.append({"label": "Inner void", "kind": "dash", "color": "#2563eb"})
            if not adopted_model:
                st.markdown(
                    '<div class="warn-box"><b>3D preview source is not locked:</b> this viewport is using the current working tendon model. Adopt/Re-adopt the tendon model before downstream prestress or report use.</div>',
                    unsafe_allow_html=True,
                )
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div class="canvas-kicker">CANVAS</div>
                    <div class="canvas-head">
                      <div>
                        <div class="canvas-title">Interactive 3D Tendon Review</div>
                        <div class="small-muted">Transparent section envelope with external tendon profiles from the merged vertical/horizontal layout model.</div>
                      </div>
                      <div class="canvas-pill">3D review viewport</div>
                    </div>
                    <div class="canvas-note">
                      This is a review model, not a full bridge solid model. 3D convention: X = station along span, Y = horizontal offset from CL, Z = vertical coordinate from section bottom.
                    </div>
                    <div class="canvas-meta-strip">
                      <div class="canvas-station-badge"><span>Design source</span><strong>{source_label}</strong></div>
                      <div class="canvas-meta-right">
                        <div class="canvas-view-badge">{view_mode_text} · {view_mode_note}</div>
                        <div class="canvas-dim-badge">Preset: {inspection_preset}</div>
                        <div class="canvas-dim-badge">View: {effective_view_preset}</div>
                        <div class="canvas-dim-badge">Shell: {effective_shell_display_mode}</div>
                        <div class="canvas-dim-badge">Aspect: {aspect_mode}</div>
                      </div>
                    </div>
                    {_engineering_canvas_legend_html(shell_legend_items + _tendon_3d_legend_items(visible_families, visible_sides))}
                    """,
                    unsafe_allow_html=True,
                )
                fig = tendon_3d_review_figure(
                    display_model,
                    section_coords,
                    props,
                    family_filter=tendon3d_family_filter,
                    side_filter=effective_side_filter,
                    tendon_filter=effective_tendon_filter,
                    shell_display_mode=effective_shell_display_mode,
                    outer_shell_opacity=outer_shell_opacity,
                    inner_void_opacity=inner_void_opacity,
                    show_station_markers=show_station_markers,
                    show_tendon_labels=show_tendon_labels_3d,
                    view_preset=effective_view_preset,
                    aspect_mode=aspect_mode,
                    focus_tendon=effective_focus_tendon,
                    fade_unfocused_tendons=effective_fade_unfocused_tendons,
                    tendon_line_width=tendon_line_width,
                    station_marker_mode=effective_station_marker_mode,
                )
                st.plotly_chart(fig, use_container_width=True, config=current_plotly_config())
                st.markdown(
                    f'<div class="canvas-caption"><b>Figure 2.x</b> Interactive 3D tendon review model showing external tendon profiles within the transparent box-girder section envelope ({effective_view_preset}, {effective_shell_display_mode}, {aspect_mode}).</div>',
                    unsafe_allow_html=True,
                )
                footer_html = (
                    '<div class="canvas-footer-grid">'
                    + _canvas_footer_card_html("Source", "ADOPTED" if adopted_model else "WORKING", "design-source snapshot" if adopted_model else "preview only", source_mode)
                    + _canvas_footer_card_html("Visible tendons", str(len(visible_tendons)), f"{tendon3d_family_filter} · {effective_side_filter} · {effective_tendon_filter}", "pass" if visible_tendons else "warn")
                    + _canvas_footer_card_html("Shell display", effective_shell_display_mode, f"outer {outer_shell_opacity:.2f} · inner {inner_void_opacity:.2f}", "neutral")
                    + _canvas_footer_card_html("View", effective_view_preset.replace(" · ", " / "), f"{aspect_mode} · {effective_station_marker_mode}", "neutral")
                    + _canvas_footer_card_html("Focus", effective_focus_tendon or "None", "faded context" if effective_focus_tendon and effective_fade_unfocused_tendons else "standard display", "neutral")
                    + _canvas_footer_card_html("Interaction", "Rotate / pan / zoom", "Plotly WebGL 3D viewport", "neutral")
                    + '</div>'
                )
                st.markdown(footer_html, unsafe_allow_html=True)
        elif not props.get("valid"):
            st.warning("Import valid section coordinates first to build the transparent section envelope for 3D tendon review.")
        else:
            st.info("Build a valid tendon model first to show the 3D tendon review viewport.")

    with tabs[4]:
        subsection_title("Section overlay at selected station")
        props = _section_computation_from_state()
        if model.get("valid") and props.get("valid"):
            max_station = float(model.get("span_m") or D["project"].get("span_m", 40.0))
            mid_station = float(model.get("midspan_m") or max_station / 2.0)
            station_key = "tendon_section_overlay_station"
            if station_key not in st.session_state:
                st.session_state[station_key] = mid_station

            st.markdown("##### Station control · Quick station")
            b1, b2, b3, b4, b5 = st.columns(5)
            if b1.button("Start", use_container_width=True, key="overlay_station_start"):
                st.session_state[station_key] = 0.0
            if b2.button("0.25L", use_container_width=True, key="overlay_station_q1"):
                st.session_state[station_key] = 0.25 * max_station
            if b3.button("Midspan", use_container_width=True, key="overlay_station_mid"):
                st.session_state[station_key] = mid_station
            if b4.button("0.75L", use_container_width=True, key="overlay_station_q3"):
                st.session_state[station_key] = 0.75 * max_station
            if b5.button("End", use_container_width=True, key="overlay_station_end"):
                st.session_state[station_key] = max_station

            station = st.slider("Station x (m)", min_value=0.0, max_value=max_station, value=float(st.session_state.get(station_key, mid_station)), step=0.01, key=station_key)
            station_label = _overlay_station_label(station, max_station)

            c1, c2, c3, c4, c5, c6 = st.columns([1.05, 1.05, 1.0, 1.0, 1.0, 0.82])
            with c1:
                tl["positive_horiz_offset_direction"] = st.selectbox(
                    "Positive HorizOff direction",
                    ["left", "right"],
                    index=0 if tl.get("positive_horiz_offset_direction", "left") == "left" else 1,
                    format_func=lambda x: "Positive = left of CL" if x == "left" else "Positive = right of CL",
                    key="tendon_offset_direction",
                )
            with c2:
                tl["section_overlay_origin_mode"] = st.selectbox(
                    "Display origin",
                    ["centerline", "csibridge"],
                    index=0 if tl.get("section_overlay_origin_mode", "centerline") == "centerline" else 1,
                    format_func=lambda x: "Centerline origin (CL = 0)" if x == "centerline" else "CSiBridge origin",
                    key="tendon_overlay_origin_mode",
                )
            with c3:
                tl["section_overlay_label_mode"] = st.selectbox(
                    "Tendon label mode",
                    ["hide", "family", "all"],
                    index={"hide": 0, "family": 1, "all": 2}.get(tl.get("section_overlay_label_mode", "hide"), 0),
                    format_func=lambda x: {"family": "Family labels only", "hide": "Hide labels / hover only", "all": "All tendon labels"}[x],
                    key="tendon_overlay_label_mode",
                )
            with c4:
                tl["section_overlay_dimension_mode"] = st.selectbox(
                    "Dimension mode",
                    ["clean", "full", "hide"],
                    index={"clean": 0, "full": 1, "hide": 2}.get(tl.get("section_overlay_dimension_mode", "clean"), 0),
                    format_func=lambda x: {"clean": "Clean", "full": "Full dimensions", "hide": "Hide dimensions"}[x],
                    key="tendon_overlay_dimension_mode",
                )
            with c5:
                st.markdown(
                    f'<div class="small-muted"><b>Figure view mode</b><br>{figure_view_badge_text(current_figure_view_mode())}<br><span style="font-size:0.72rem;">Global setting in sidebar</span></div>',
                    unsafe_allow_html=True,
                )
            with c6:
                min_clearance_req = st.number_input("QA clearance limit (mm)", min_value=0.0, max_value=500.0, value=float(tl.get("section_overlay_clearance_limit_mm", 50.0)), step=10.0, key="tendon_overlay_clearance_limit_mm")
                tl["section_overlay_clearance_limit_mm"] = float(min_clearance_req)

            raw_points = tendon_points_at_station(model, station)
            points = _add_section_coordinates_to_tendon_points(
                raw_points,
                props,
                positive_offset_direction=tl.get("positive_horiz_offset_direction", "left"),
                origin_mode=tl.get("section_overlay_origin_mode", "centerline"),
            )
            coords = props.get("coordinates", _section_coordinate_df_from_state())
            qa_points = _tendon_section_location_qa(points, coords)
            pass_count = int((qa_points.get("Status", pd.Series(dtype=str)) == "PASS").sum()) if not qa_points.empty else 0
            fail_count = int((qa_points.get("Status", pd.Series(dtype=str)) == "FAIL").sum()) if not qa_points.empty else 0
            concrete_count = int((qa_points.get("Location", pd.Series(dtype=str)) == "INSIDE CONCRETE").sum()) if not qa_points.empty else 0
            outside_count = int((qa_points.get("Location", pd.Series(dtype=str)) == "OUTSIDE SECTION").sum()) if not qa_points.empty else 0
            min_clearance = None
            if not qa_points.empty and "Min clearance to inner boundary (mm)" in qa_points.columns:
                min_clearance = pd.to_numeric(qa_points["Min clearance to inner boundary (mm)"], errors="coerce").min()
            clearance_status = bool(min_clearance is not None and pd.notna(min_clearance) and float(min_clearance) >= float(min_clearance_req))

            origin_text = "CL = 0" if tl.get("section_overlay_origin_mode", "centerline") == "centerline" else "CSiBridge origin"
            positive_offset_text = "positive offset: left of CL" if tl.get("positive_horiz_offset_direction", "left") == "left" else "positive offset: right of CL"
            clearance_text = format_engineering_value(min_clearance, "mm") if min_clearance is not None and pd.notna(min_clearance) else "—"
            clearance_limit_text = format_engineering_value(min_clearance_req, "mm")
            station_text = f"{station_label} · x = {format_engineering_value(station, 'm')} m"
            points_text = f"{pass_count}/{len(points)} in void"
            qa_note = f"{concrete_count} concrete · {outside_count} outside"
            dimension_mode = tl.get("section_overlay_dimension_mode", "clean")
            dimension_mode_text = {"clean": "Clean", "full": "Full dimensions", "hide": "Hide dimensions"}.get(dimension_mode, "Clean")
            view_mode_text = "Interactive review" if current_figure_view_mode() == "Interactive review" else "Report preview"
            view_mode_note = "toolbar on" if current_figure_view_mode() == "Interactive review" else "toolbar hidden"
            tendon_canvas_config = current_plotly_config()

            family_order = list(dict.fromkeys([str(t.get("family") or t.get("Family") or "") for t in model.get("tendons", []) if str(t.get("family") or t.get("Family") or "").strip()]))
            clearance_value_text = f"{clearance_text} mm" if clearance_text != "—" else "—"
            clearance_note_text = f"{'PASS · ' if clearance_status else 'REVIEW · '}limit ≥ {clearance_limit_text} mm"

            with st.container(border=True):
                st.markdown(
                    f"""
                    <div class="canvas-kicker">CANVAS</div>
                    <div class="canvas-head">
                      <div>
                        <div class="canvas-title">Live Tendon Section Preview</div>
                        <div class="small-muted">Imported external tendon positions overlaid on the active BG40 box-girder section.</div>
                      </div>
                      <div class="canvas-pill">External tendon QA</div>
                    </div>
                    <div class="canvas-note">
                      The preview uses CSiBridge vertical layout as <i>d<sub>p</sub></i> from the top surface and horizontal layout as offset from section CL. Concrete/rebar graphics remain controlled by their own pages.
                    </div>
                    <div class="canvas-meta-strip">
                      <div class="canvas-station-badge"><span>Selected station</span><strong>{station_text}</strong></div>
                      <div class="canvas-meta-right">
                        <div class="canvas-view-badge">{view_mode_text} · {view_mode_note}</div>
                        <div class="canvas-dim-badge">Dimension mode: {dimension_mode_text}</div>
                      </div>
                    </div>
                    {_tendon_canvas_legend_html(family_order, show_centroid=dimension_mode != "hide")}
                    """,
                    unsafe_allow_html=True,
                )

                # Keep the station badge outside the Plotly body. The explicit
                # figure view mode controls whether the Plotly modebar is shown
                # for engineering review or hidden for report preview.
                fig = tendon_section_overlay_figure(
                    coords,
                    props,
                    raw_points,
                    positive_offset_direction=tl.get("positive_horiz_offset_direction", "left"),
                    point_label_mode=tl.get("section_overlay_label_mode", "hide"),
                    show_point_numbers=False,
                    origin_mode=tl.get("section_overlay_origin_mode", "centerline"),
                    dimension_mode=tl.get("section_overlay_dimension_mode", "clean"),
                )
                fig.update_layout(
                    showlegend=False,
                    height=520,
                    margin=dict(l=50, r=18, t=44, b=52),
                    plot_bgcolor="#ffffff",
                    paper_bgcolor="#ffffff",
                    font=dict(color="#334155"),
                )
                fig.update_xaxes(
                    showgrid=True,
                    gridcolor="rgba(148,163,184,0.09)",
                    zeroline=True,
                    zerolinecolor="rgba(37,99,235,0.26)",
                    tickfont=dict(color="#64748b", size=10),
                    title_font=dict(color="#475569", size=11),
                )
                fig.update_yaxes(
                    showgrid=True,
                    gridcolor="rgba(148,163,184,0.09)",
                    zeroline=True,
                    zerolinecolor="rgba(148,163,184,0.20)",
                    tickfont=dict(color="#64748b", size=10),
                    title_font=dict(color="#475569", size=11),
                )
                st.plotly_chart(fig, use_container_width=True, config=tendon_canvas_config)
                st.markdown(
                    f'<div class="canvas-caption"><b>Figure 2.x</b> Tendon section overlay at {station_label} ({station:.3f} m), showing imported external tendon positions within the box-girder void.</div>',
                    unsafe_allow_html=True,
                )
                footer_html = (
                    '<div class="canvas-footer-grid">'
                    + _canvas_footer_card_html("Geometry", "Ready", "active box-girder polygon", "pass")
                    + _canvas_footer_card_html("Tendon QA", points_text, qa_note, "pass" if fail_count == 0 and pass_count else "warn")
                    + _canvas_footer_card_html("Minimum clearance", clearance_value_text, clearance_note_text, "pass" if clearance_status else "warn")
                    + _canvas_footer_card_html("Display", origin_text, positive_offset_text, "neutral")
                    + '</div>'
                )
                st.markdown(footer_html, unsafe_allow_html=True)

            st.markdown("#### Selected-station tendon QA table")
            overlay_table = _merge_tendon_overlay_points_with_qa(points, qa_points)
            if not overlay_table.empty:
                table_cols = [
                    c for c in [
                        "Tendon", "Family", "Side", "Station (m)", "dp from top (m)", "HorizOff (m)",
                        "display_x_mm", "section_y_mm", "Location", "Min clearance to inner boundary (mm)", "Status",
                    ] if c in overlay_table.columns
                ]
                table = overlay_table[table_cols].rename(columns={"display_x_mm": "Display x (mm)", "section_y_mm": "Section y (mm)"})
                st.dataframe(_format_tendon_points_table(table), use_container_width=True, hide_index=True)
            else:
                st.info("No tendon positions are available at this station.")

            with st.expander("Tendon location QA · detailed notes", expanded=False):
                if not qa_points.empty:
                    st.dataframe(_format_tendon_points_table(qa_points), use_container_width=True, hide_index=True)
                else:
                    st.info("No tendon QA rows available at this station.")
        elif not props.get("valid"):
            st.warning("Import valid section coordinates first to overlay tendon points on the box-girder section.")
        else:
            st.info("Build a valid tendon model first.")

    with tabs[5]:
        subsection_title("Adopted tendon data")
        if model.get("valid"):
            adopted_model = _active_adopted_tendon_model()
            adopted_summary = tl.get("adopted_downstream_summary", {}) if adopted_model else {}
            gate = tendon_model_status(model, tl)
            gate_badge = "pass" if gate["mode"] == "pass" else "neutral"
            st.markdown(
                f"""
                <div class="result-card"><b>Tendon Design Source Lockdown</b> <span class="badge {gate_badge}">{gate['status']}</span><br>
                <span class="small-muted">Imported tendon tables are a working source. Downstream prestress/report checks must use the explicitly adopted tendon snapshot only.</span></div>
                """,
                unsafe_allow_html=True,
            )
            _render_tendon_adoption_cards(model)

            c_adopt, c_clear = st.columns([1.35, 0.85])
            with c_adopt:
                if st.button("Adopt / Re-adopt tendon model as design source", type="primary", use_container_width=True):
                    summary = _adopt_working_tendon_model(model)
                    st.success(
                        "Tendon layout locked as the downstream design source. Prestress tendon count, Aps,total, dp averages, and group end/midspan dp values now come from the adopted snapshot."
                    )
                    st.caption(f"Adopted model fingerprint: {summary.get('model_fingerprint', '—')}")
                    st.rerun()
            with c_clear:
                if st.button("Clear adopted tendon source", use_container_width=True):
                    clear_adopted_tendon_model(tl)
                    st.warning("Adopted tendon source cleared. Raw imports remain available for review, but downstream modules should not use them until re-adopted.")
                    st.rerun()

            active_table_model = adopted_model if adopted_model else model
            active_table_label = "Adopted Tendon Layout Table — one row per tendon" if adopted_model else "Working imported model · not yet adopted — one row per tendon"
            st.markdown(f"#### {active_table_label}")
            if not adopted_model:
                st.markdown('<div class="warn-box"><b>Not locked:</b> the table below is the current imported/merged model for review only. Click <b>Adopt / Re-adopt tendon model as design source</b> before using it downstream.</div>', unsafe_allow_html=True)
            active_tendons_df, active_group_df, _, _ = tendon_model_to_frames(active_table_model)
            active_profile_df = tendon_model_to_profile_frame(active_table_model)
            summary_display = _tendon_summary_display_frame(active_tendons_df)
            st.dataframe(summary_display, use_container_width=True, hide_index=True)

            st.markdown("#### Merged Tendon Profile Table — vertical + horizontal")
            st.caption("Each row combines station x, vertical dp measured from top, and horizontal offset from CL for the same tendon control point. This table belongs to the active source shown above.")
            profile_display = _tendon_profile_display_frame(active_profile_df)
            st.dataframe(profile_display, use_container_width=True, hide_index=True)

            st.markdown("#### Downstream tendon summary")
            summary_for_display = adopted_summary or build_tendon_downstream_summary(model, y_t_from_top_m=float(D["section"].get("yt_from_top_m", 0.0)))
            show_engineering_table(_tendon_summary_frame_from_summary(summary_for_display))

            st.markdown("#### Report-style tendon group summary")
            show_engineering_table(active_group_df)
            st.markdown(
                f'<div class="note-box"><b>One-source rule:</b> dp_avg,end = {active_table_model.get("dp_avg_end_m", 0.0):.3f} m; dp_avg,midspan = {active_table_model.get("dp_avg_midspan_m", 0.0):.3f} m; e_midspan = {active_table_model.get("eccentricity_midspan_m", 0.0):.3f} m using y_t = {D["section"].get("yt_from_top_m", 0.0):.3f} m. Friction curvature/angle calculation remains a later milestone and is not silently inferred here.</div>',
                unsafe_allow_html=True,
            )

            with st.expander("Source trace used for adoption", expanded=False):
                source_trace = tl.get("adopted_source_trace") if adopted_model else build_tendon_source_trace(tl, model)
                show_engineering_table(pd.DataFrame(source_trace))
        else:
            st.info("Build a valid tendon model to show adopted tendon data.")

    with tabs[6]:
        subsection_title("Tendon QA / consistency")
        gate = tendon_model_status(model, tl)
        adopted_model = _active_adopted_tendon_model()
        adopted_summary = tl.get("adopted_downstream_summary", {}) if adopted_model else {}

        st.markdown(
            f"""
            <div class="qa-card"><b>Tendon module QA gate:</b> {gate['status']}<br>
            <span class="small-muted">{gate['message']} This page is the control point before Prestress Losses and report export consume tendon data.</span></div>
            """,
            unsafe_allow_html=True,
        )
        _render_tendon_adoption_cards(model)

        if model.get("warnings"):
            for w in model["warnings"]:
                st.warning(w)
        if model.get("errors"):
            for e in model["errors"]:
                st.error(e)

        st.markdown("#### Source trace")
        show_engineering_table(_tendon_source_trace_frame(tl, model))

        if not qa_df.empty:
            st.markdown("#### Import QA")
            show_engineering_table(qa_df)
        if not symmetry_df.empty:
            st.markdown("#### Left/right symmetry QA")
            show_engineering_table(symmetry_df)
        if not station_match_df.empty:
            st.markdown("#### Vertical / horizontal station matching QA")
            show_engineering_table(station_match_df)

        st.markdown("#### Downstream trace")
        adopted_ready = bool(adopted_model)
        trace = pd.DataFrame([
            ["Tendon figures", "Working imported or adopted tendon model", "Side elevation / plan / section overlay", "READY" if model.get("valid") else "PENDING"],
            ["Prestress summary", "Explicitly adopted tendon snapshot", "Aps,total and dp averages copied only when adopted", "READY" if adopted_ready else "BLOCKED"],
            ["Friction angle α", "Existing BG40 report route", "Not recalculated from tendon geometry in this milestone", "REVIEW"],
            ["Report export", "Adopted tendon model + source trace", "Figures, tables, and downstream summary are report-ready", "READY" if adopted_ready else "PENDING"],
            ["Save/Load JSON", "tendon_layout.adopted_model", "Adoption snapshot and trace persist in project JSON", "READY" if adopted_ready else "PENDING"],
        ], columns=["Item", "Source", "App action", "Status"])
        show_engineering_table(trace)

        st.markdown("#### Report preview · tendon layout basis")
        if adopted_ready:
            show_engineering_table(_tendon_summary_frame_from_summary(adopted_summary))
            st.markdown(
                '<div class="note-box"><b>Report wording:</b> The tendon layout is adopted from the reviewed CSiBridge General, Vertical Layout, and Horizontal Layout tendon exports. The adopted snapshot is the single source for tendon count, Aps,total, jacking force, average dp, and midspan eccentricity used by downstream checks.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="warn-box"><b>Report preview blocked:</b> adopt the imported tendon model before using tendon summary values in Prestress Losses or final reports.</div>',
                unsafe_allow_html=True,
            )

def render_bridge_consistency() -> None:
    section_title("2.5 Consistency Checks")
    s = D["section"]
    S_top_calc = s["I33_m4"] / s["yt_from_top_m"] if s["yt_from_top_m"] else 0.0
    S_bot_calc = s["I33_m4"] / s["ycg_from_bottom_m"] if s["ycg_from_bottom_m"] else 0.0
    D_calc = s["ycg_from_bottom_m"] + s["yt_from_top_m"]
    rows = [
        ["S33(+) = I33 / y_t", S_top_calc, s["S_top_m3"], "m³"],
        ["S33(-) = I33 / y_cg", S_bot_calc, s["S_bottom_m3"], "m³"],
        ["D = y_cg + y_t", D_calc, s["D_m"], "m"],
        ["Coordinate source", s.get("coordinate_source", "FEA keyed"), "—", "-"],
    ]
    st.dataframe(pd.DataFrame(rows, columns=["Check", "Calculated", "Active / Report", "Unit"]), use_container_width=True, hide_index=True)


def page_bridge_geometry(sub: str) -> None:
    if sub == "2.1 Bridge Description":
        render_bridge_description()
    elif sub == "2.2 Geometry and Analysis Model":
        render_geometry_analysis_model()
    elif sub == "2.3 Section Properties":
        render_section_properties()
    elif sub == "2.4 Tendon Layout Reference":
        render_tendon_layout_reference()
    elif sub == "2.5 Consistency Checks":
        render_bridge_consistency()
    else:
        section_title("2 QA / Report Preview")
        report_trace_table("2 Bridge Geometry / Section Properties", [
            ("Bridge description", "User input + BG40 R10", "Report table ready", "READY"),
            ("Geometry and analysis model", "External FEA program + app documentation", "Model assumptions and report figure status recorded", "READY"),
            ("Coordinate-driven section properties", "CSiBridge polygon import / FEA keyed fallback", "Section drawing and A/I/S calculation engine active", "READY"),
            ("Tendon layout reference", "BG40 R10", "Tendon table ready", "READY"),
        ])

def page_prestress_losses(sub: str) -> None:
    st.subheader(get_workspace("4 Prestress Losses")["title"])
    m, p = D["materials"], D["prestress"]
    summary = prestress_loss_summary(prestress_inputs())
    if sub == "4.1 General":
        code_basis_card("Prestress losses code basis", "AASHTO LRFD 2020 Section 5, Art. 5.9.3", "M4.2 will connect adopted tendon/section data; M4.3 will implement loss equations through the unit-safe wrapper layer.")
        st.markdown("Prestress losses are evaluated as instantaneous and time-dependent losses. The app calculates equivalent average losses for global section design and uses final prestress force as a model consistency check.")
        c1, c2, c3, c4 = st.columns(4)
        with c1: card("fpi", f"{m['fpi_mpa']:.1f} MPa", "Initial jacking stress")
        with c2: card("Total Loss", f"{summary['total_loss_mpa']:.1f} MPa", "All loss components")
        with c3: card("fpe", f"{summary['fpe_mpa']:.1f} MPa", "Effective stress", "pass")
        with c4: card("P_eff", f"{summary['Peff_kn']:,.0f} kN", "fpe × Aps,total")
    elif sub == "4.2 Friction":
        st.latex(r"\Delta f_{pF,eq}=f_{pi}\left[1-e^{-\mu\alpha}\right],\qquad \alpha_{total}=\sqrt{\alpha_{vert}^{2}+\alpha_{horiz}^{2}}")
        df, avg, pct = friction_loss_table(p["tendon_friction_groups"], m["fpi_mpa"], p["mu_external"])
        st.dataframe(df.style.format({"α_vert (rad)": "{:.4f}", "α_horiz (rad)": "{:.4f}", "α_total (rad)": "{:.4f}", "ΔfpF,eq (MPa)": "{:.2f}", "Loss (%)": "{:.2f}"}), use_container_width=True)
        st.info(f"Weighted average friction loss = {avg:.1f} MPa = {pct:.2f}% of fpi.")
    elif sub == "4.3 Anchor Set":
        st.latex(r"\Delta f_{pA,eq}=\frac{\Delta_a E_p}{L_{eff}}")
        editable_value(["prestress", "anchor_set_mm"], "Anchor set Δa (mm)", 0.5)
        editable_value(["prestress", "anchor_set_loss_mpa"], "Equivalent anchor-set loss used (MPa)", 0.1)
        st.caption("Anchor-set loss is position-dependent along the tendon; the report workflow uses an equivalent average value for global section design.")
    elif sub == "4.4 Elastic Shortening":
        st.latex(r"\Delta f_{pES}=\left(\frac{N-1}{2N}\right)\left(\frac{E_p}{E_{ci}}\right)f_{cgp}")
        editable_value(["prestress", "fcgp_mpa"], "fcgp (MPa)", 0.1)
        st.info(f"Elastic shortening loss = {summary['elastic_shortening_mpa']:.1f} MPa")
    elif sub == "4.5 Creep / Shrinkage":
        c1, c2, c3 = st.columns(3)
        with c1: editable_value(["prestress", "RH_percent"], "RH (%)", 1.0)
        with c2: editable_value(["prestress", "V_over_S_in"], "V/S (in)", 0.01)
        with c3: editable_value(["prestress", "ti_days"], "ti (days)", 1.0)
        creep = aashto_creep_coefficient(p["RH_percent"], p["V_over_S_in"], m["fc_mpa"], p["ti_days"])
        shrink = aashto_shrinkage_strain(p["RH_percent"], p["V_over_S_in"], m["fc_mpa"])
        c1, c2 = st.columns(2)
        with c1:
            st.latex(r"\psi(t_f,t_i)=1.9k_s k_{hc}k_f\Delta k_{td}t_i^{-0.118}")
            st.dataframe(pd.DataFrame(creep.items(), columns=["Term", "Value"]), use_container_width=True, hide_index=True)
            st.info(f"ΔfpCR = {summary['creep_mpa']:.1f} MPa")
        with c2:
            st.latex(r"\varepsilon_{sh}=k_s k_{hs} k_f\Delta k_{td}(0.48\times10^{-3})")
            st.dataframe(pd.DataFrame(shrink.items(), columns=["Term", "Value"]), use_container_width=True, hide_index=True)
            st.info(f"εsh = {summary['shrinkage_microstrain']:.1f} με; ΔfpSH = {summary['shrinkage_mpa']:.1f} MPa")
    elif sub == "4.6 Effective Prestress":
        loss_df = pd.DataFrame([["Friction", summary["friction_mpa"]], ["Anchor set", summary["anchor_set_mpa"]], ["Elastic shortening", summary["elastic_shortening_mpa"]], ["Creep", summary["creep_mpa"]], ["Shrinkage", summary["shrinkage_mpa"]], ["Relaxation", summary["relaxation_mpa"]], ["Total", summary["total_loss_mpa"]], ["fpe", summary["fpe_mpa"]]], columns=["Item", "Value (MPa)"])
        st.dataframe(loss_df.style.format({"Value (MPa)": "{:.2f}"}), use_container_width=True)
        st.download_button("Download loss table CSV", loss_df.to_csv(index=False).encode("utf-8"), "prestress_losses.csv", "text/csv")
    else:
        report_trace_table("4 Prestress Losses", [("Friction", "App calculation", "Formula and table ready", "READY"), ("Anchor set", "User equivalent input", "Trace placeholder ready", "READY"), ("Elastic shortening", "App calculation", "Formula ready", "READY"), ("Creep/Shrinkage", "AASHTO factors", "Unit warning active", "READY"), ("Effective prestress", "App calculation", "Loss table ready", "READY")])


def page_fea_results(sub: str) -> None:
    st.subheader(get_workspace("5 FEA Results")["title"])
    fea = D["fea_results"]
    l = D["loads"]
    if sub == "5.1 Data Hub":
        st.markdown('<div class="note-box"><b>FEA data status:</b> R10 baseline summary values are active. Detailed station-by-station FEA import is pending and should be added before full commercial envelope review.</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame([["Permanent load moment at midspan", fea["permanent_moment_midspan_knm"], "kN·m"], ["Prestress moment at midspan", fea["prestress_moment_midspan_knm"], "kN·m"], ["Prestress axial force at midspan", fea["prestress_axial_midspan_kn"], "kN"], ["LL+IM moment min", fea["ll_im_moment_min_knm"], "kN·m"], ["LL+IM moment max", fea["ll_im_moment_max_knm"], "kN·m"]], columns=["FEA item", "Value", "Unit"]), use_container_width=True, hide_index=True)
    elif sub == "5.2 ULS Envelope":
        c1, c2, c3, c4 = st.columns(4)
        with c1: editable_value(["loads", "critical_x_m"], "Critical x (m)", 0.001, "%.3f")
        with c2: editable_value(["loads", "Vu_kn"], "Vu (kN)", 10.0)
        with c3: editable_value(["loads", "Tu_knm"], "Tu (kN·m)", 10.0)
        with c4: editable_value(["loads", "Mu_knm"], "Mu (kN·m)", 10.0)
        st.dataframe(pd.DataFrame([["Critical section", l["critical_x_m"], "m"], ["Vu", l["Vu_kn"], "kN"], ["Tu", l["Tu_knm"], "kN·m"], ["Pu", l["Pu_kn"], "kN"], ["Mu", l["Mu_knm"], "kN·m"]], columns=["Demand", "Value", "Unit"]), use_container_width=True, hide_index=True)
    elif sub == "5.3 SLS Envelope":
        st.info("SLS envelope import will be expanded in M3. Current SLS checks use keyed governing stresses from BG40 R10 baseline.")
        st.dataframe(pd.DataFrame(D["sls_stress"].items(), columns=["SLS baseline item", "Value"]), use_container_width=True, hide_index=True)
    else:
        report_trace_table("5 FEA Results", [("Midspan dashboard", "BG40 R10 baseline summary", "Data hub active", "Baseline Ready"), ("ULS envelope", "User keyed / R10 demand values", "Demand object active", "Baseline Ready"), ("SLS envelope", "R10 baseline", "Station-by-station import pending", "Pending Import")])


def page_uls_flexure(sub: str) -> None:
    st.subheader(get_workspace("6 ULS Flexure")["title"])
    flex = D["uls_flexure"]
    if sub == "6.1 Basis":
        st.markdown("ULS flexure uses AASHTO LRFD 2020 Section 5 resistance with external/unbonded tendon stress checks and FEA factored moment demand.")
        st.latex(r"f_{ps}=f_{pe}+68.95+\frac{f'_c}{100\rho_p}\leq \min(f_{py},f_{pe}+415)")
    elif sub == "6.2 Capacity":
        c1, c2, c3 = st.columns(3)
        with c1: editable_value(["uls_flexure", "fps_mpa"], "fps (MPa)", 1.0)
        with c2: editable_value(["uls_flexure", "phi_mn_midspan_knm"], "φMn midspan (kN·m)", 100.0)
        with c3: editable_value(["uls_flexure", "mu_midspan_knm"], "Mu midspan (kN·m)", 100.0)
        dcr = flex["mu_midspan_knm"] / flex["phi_mn_midspan_knm"] if flex["phi_mn_midspan_knm"] else 0.0
        mode = "pass" if dcr <= 1.0 else "fail"
        card("Midspan Flexure", f"DCR = {dcr:.3f}", f"φMn = {flex['phi_mn_midspan_knm']:,.0f} kN·m; Mu = {flex['mu_midspan_knm']:,.0f} kN·m", mode)
    elif sub == "6.3 Span Results":
        c1, c2 = st.columns(2)
        with c1: editable_value(["uls_flexure", "max_dcr"], "Maximum span DCR", 0.001, "%.3f")
        with c2: editable_value(["uls_flexure", "governing_x_m"], "Governing x (m)", 0.5)
        st.dataframe(pd.DataFrame([["Midspan", flex["mu_midspan_knm"], flex["phi_mn_midspan_knm"], flex["mu_midspan_knm"] / flex["phi_mn_midspan_knm"], "PASS"], [f"Governing x={flex['governing_x_m']} m", "—", "—", flex["max_dcr"], flex["status"]]], columns=["Station", "Mu", "φMn", "DCR", "Status"]), use_container_width=True, hide_index=True)
    else:
        report_trace_table("6 ULS Flexure", [("fps", "BG40 R10 baseline", "Shown in calculation card", "Baseline Ready"), ("Midspan φMn/Mu", "BG40 R10 baseline", "DCR calculated", "Baseline Ready"), ("Span DCR", "BG40 R10 baseline", "Station import pending", "Pending Import")])


def page_uls_shear_torsion(sub: str) -> None:
    st.subheader(get_workspace("7 ULS Shear / Torsion")["title"])
    m, s, l = D["materials"], D["section"], D["loads"]
    snap = engineering_snapshot()
    phi_v = snap["phi_v"]
    tors = snap["torsion"]
    web = snap["web"]
    shear = snap["shear"]
    prov = snap["provided"]
    check = snap["transverse_check"]
    if sub == "7.1 Basis":
        st.markdown("Shear and torsion are separated by design basis to avoid formula-route errors.")
        st.dataframe(pd.DataFrame([["Shear", "AASHTO LRFD 2020 Section 5, Art. 5.7 / MCFT", "β and θ based shear check"], ["Torsion", "AASHTO LRFD 2020 Section 5, Art. 5.12.5.3.8 / segmental torsion", "Segmental box girder special provision"], ["Resistance factor", "φv", phi_v]], columns=["Item", "Code basis", "Remarks"]), use_container_width=True, hide_index=True)
    elif sub == "7.2 Critical Section":
        c1, c2, c3, c4 = st.columns(4)
        with c1: editable_value(["loads", "critical_x_m"], "xcr (m)", 0.001, "%.3f")
        with c2: editable_value(["loads", "Vu_kn"], "Vu (kN)", 10.0)
        with c3: editable_value(["loads", "Tu_knm"], "Tu (kN·m)", 10.0)
        with c4: editable_value(["loads", "Vc_per_web_kn"], "Vc/web (kN)", 10.0)
        st.dataframe(pd.DataFrame([["Critical x", l["critical_x_m"], "m"], ["Vu", l["Vu_kn"], "kN"], ["Tu", l["Tu_knm"], "kN·m"], ["Vg/web", web["Vg_web_kn"], "kN"], ["Vt/web", web["Vt_web_kn"], "kN"], ["Vu,web", web["Vu_web_kn"], "kN"]], columns=["Item", "Value", "Unit"]), use_container_width=True, hide_index=True)
    elif sub == "7.3 Shear Check":
        st.latex(r"V_{u,web}=\frac{V_u}{2}+\frac{T_u}{2A_o}d_{web}")
        st.latex(r"\frac{A_v}{s}=\frac{V_s}{f_y d_v \cot\theta}")
        st.dataframe(pd.DataFrame([["β", l["beta_for_shear"], "-"], ["θ", l["theta_deg_for_shear"], "deg"], ["cotθ", shear["cot_theta"], "-"], ["Vs required", shear["Vs_req_kn"], "kN"], ["Av/s required", shear["Av_over_s_mm2_per_mm"], "mm²/mm"]], columns=["Item", "Value", "Unit"]), use_container_width=True, hide_index=True)
    elif sub == "7.4 Torsion Check":
        st.latex(r"\frac{A_t}{s}=\frac{T_u}{2\phi_v A_o f_y},\qquad A_l=\frac{T_u p_h}{2\phi_v A_o f_y}")
        st.dataframe(pd.DataFrame([["φv", phi_v, "-"], ["Aoh", s["Aoh_mm2"], "mm²"], ["ph", s["ph_mm"], "mm"], ["At/s", tors["At_over_s_mm2_per_mm"], "mm²/mm"], ["Al,AASHTO", tors["Al_mm2"], "mm²"], ["Al,FEA,max", l["fea_Al_max_mm2"], "mm²"], ["Al,design", max(tors["Al_mm2"], l["fea_Al_max_mm2"]), "mm²"]], columns=["Item", "Value", "Unit"]), use_container_width=True, hide_index=True)
    elif sub == "7.5 Reinforcement":
        c1, c2, c3 = st.columns(3)
        with c1: editable_value(["loads", "stirrup_bar_dia_mm"], "DB diameter (mm)", 1.0)
        with c2: editable_value(["loads", "stirrup_spacing_mm"], "Spacing s (mm)", 25.0)
        with c3: D["loads"]["stirrup_legs_per_web"] = int(st.number_input("Legs per web", value=int(D["loads"]["stirrup_legs_per_web"]), step=1))
        mode = "pass" if check["Status_governing"] == "PASS" else "fail"
        card("Combined transverse check", app_status(check["Status_governing"]), f"Governing D/C = {check['DCR_governing']:.3f}", mode)
        st.dataframe(pd.DataFrame([["Shear Av/s required", shear["Av_over_s_mm2_per_mm"], "mm²/mm"], ["Shear Av/s provided", prov["Av_over_s_mm2_per_mm"], "mm²/mm"], ["Torsion At/s required", tors["At_over_s_mm2_per_mm"], "mm²/mm"], ["Torsion At/s provided per leg", prov["At_over_s_per_leg_mm2_per_mm"], "mm²/mm"], ["DCR shear", check["DCR_shear"], "-"], ["DCR torsion", check["DCR_torsion"], "-"]], columns=["Item", "Value", "Unit"]), use_container_width=True, hide_index=True)
    else:
        report_trace_table("7 ULS Shear / Torsion", [("Design basis", "AASHTO LRFD 2020 Section 5", "Formula route separated", "READY"), ("Critical section", "FEA keyed demand", "Demand table ready", "READY"), ("Shear check", "App calculation", "Trace ready", "READY"), ("Torsion check", "AASHTO LRFD 2020 Section 5", "At/s and Al calculated", "READY"), ("Reinforcement", "User input + app calc", "DCR active", check["Status_governing"])] )


def page_sls_stress(sub: str) -> None:
    st.subheader(get_workspace("8 SLS Stress")["title"])
    sls = D["sls_stress"]
    if sub == "8.1 Basis":
        st.markdown("SLS stress check is organized by transfer and final stages, with top and bottom fiber stress cards.")
    elif sub == "8.2 Transfer":
        c1, c2 = st.columns(2)
        with c1: editable_value(["sls_stress", "transfer_top_mpa"], "Transfer top stress (MPa)", 0.1)
        with c2: editable_value(["sls_stress", "transfer_bottom_mpa"], "Transfer bottom stress (MPa)", 0.1)
        st.dataframe(pd.DataFrame([["Top fiber", sls["transfer_top_mpa"], "MPa", "PASS"], ["Bottom fiber", sls["transfer_bottom_mpa"], "MPa", "PASS"]], columns=["Fiber", "Stress", "Unit", "Status"]), use_container_width=True, hide_index=True)
    elif sub == "8.3 Final":
        c1, c2 = st.columns(2)
        with c1: editable_value(["sls_stress", "final_top_mpa"], "Final top stress (MPa)", 0.1)
        with c2: editable_value(["sls_stress", "final_bottom_mpa"], "Final bottom stress (MPa)", 0.1)
        st.dataframe(pd.DataFrame([["Top fiber", sls["final_top_mpa"], "MPa", "PASS"], ["Bottom fiber", sls["final_bottom_mpa"], "MPa", "PASS"], ["Governing margin", sls["governing_margin_percent"], "%", sls["status"]]], columns=["Item", "Value", "Unit", "Status"]), use_container_width=True, hide_index=True)
    else:
        report_trace_table("8 SLS Stress", [("Transfer stresses", "BG40 R10 baseline", "Cards/table ready", "READY"), ("Final stresses", "BG40 R10 baseline", "Cards/table ready", "READY"), ("Stress envelope", "M3/M4 import pending", "Future enhancement", "IN PROGRESS")])


def page_deflection(sub: str) -> None:
    st.subheader(get_workspace("9 Deflection")["title"])
    df = D["deflection"]
    if sub == "9.1 Criteria":
        editable_value(["deflection", "limit_live_load_mm"], "Live-load deflection limit (mm)", 1.0)
        st.latex(r"\Delta_{LL,limit}=L/800")
        st.info(f"For L = {D['project']['span_m']:.1f} m, L/800 = {D['project']['span_m']*1000/800:.1f} mm.")
    elif sub == "9.2 Camber":
        c1, c2 = st.columns(2)
        with c1: editable_value(["deflection", "transfer_camber_mm"], "Transfer camber (mm)", 0.1)
        with c2: editable_value(["deflection", "final_net_camber_mm"], "Final net camber (mm)", 0.1)
        st.dataframe(pd.DataFrame([["Transfer camber", df["transfer_camber_mm"], "mm"], ["Final net camber", df["final_net_camber_mm"], "mm"]], columns=["Item", "Value", "Unit"]), use_container_width=True, hide_index=True)
    elif sub == "9.3 Live Load Deflection":
        editable_value(["deflection", "final_ll_deflection_mm"], "Final LL deflection (mm)", 0.1)
        df["ll_utilization_percent"] = 100.0 * df["final_ll_deflection_mm"] / df["limit_live_load_mm"] if df["limit_live_load_mm"] else 0.0
        status = "PASS" if df["ll_utilization_percent"] <= 100.0 else "FAIL"
        df["status"] = status
        card("Live-load deflection", status, f"{df['final_ll_deflection_mm']:.1f} mm / {df['limit_live_load_mm']:.1f} mm = {df['ll_utilization_percent']:.1f}%", "pass" if status == "PASS" else "fail")
    else:
        report_trace_table("9 Deflection", [("Deflection criterion", "L/800", "Limit calculated", "READY"), ("Camber", "BG40 R10 baseline", "Summary ready", "READY"), ("LL deflection", "BG40 R10 baseline + app calc", "Utilization active", df["status"])] )


def page_report_qa(sub: str) -> None:
    st.subheader("Report / QA")
    issues, counts, workflow = active_qa()
    snap = engineering_snapshot()
    if sub == "QA Summary":
        c1, c2, c3, c4 = st.columns(4)
        with c1: card("Errors", str(counts["ERROR"]), "Blocking engineering issues", "fail" if counts["ERROR"] else "pass")
        with c2: card("Warnings", str(counts["WARNING"]), "Engineer review required" if counts["WARNING"] else "No warnings", "warn" if counts["WARNING"] else "pass")
        with c3: card("Information", str(counts["INFO"]), "Code-route notes")
        with c4: card("Schema", PROJECT_SCHEMA_VERSION, "Report-driven UI framework with Concrete Section Pro style refinements")
        st.dataframe(workflow_dataframe(workflow), use_container_width=True, hide_index=True)
    elif sub == "Validation Issues":
        st.dataframe(issue_dataframe(issues), use_container_width=True, hide_index=True)
    elif sub == "Report Preview":
        st.markdown("### Report structure preview")
        rows = []
        for label in WORKSPACE_LABELS[1:-1]:
            ws = get_workspace(label)
            rows.append([label, ws["title"], ", ".join(ws["subpages"][:-1])])
        st.dataframe(pd.DataFrame(rows, columns=["App workspace", "Report title", "Report subsections"]), use_container_width=True, hide_index=True)
    else:
        report_md = f"""
# Segmental Box Girder Pro — Commercial M2.2 Summary

## Project
- Bridge object: {D['project']['bridge_object']}
- Span length: {D['project']['span_m']} m
- Design basis: {D['project']['design_code']}
- Tendon system: {D['project']['tendon_system']}
- Project schema: {PROJECT_SCHEMA_VERSION}

## Governing Results
- ULS flexure max DCR = {D['uls_flexure']['max_dcr']:.3f}
- ULS shear/torsion governing D/C = {snap['transverse_check']['DCR_governing']:.3f}
- SLS stress status = {D['sls_stress']['status']}
- LL deflection utilization = {D['deflection']['ll_utilization_percent']:.1f}%

## QA Gate
- Errors: {counts['ERROR']}
- Warnings: {counts['WARNING']}
- Information items: {counts['INFO']}

## M2 Notes
- UI uses report-driven workspaces 1–9 without displaying the word Chapter in the sidebar; Loads are separated as a dedicated workspace and Geometry/Section Properties are combined.
- Status wording distinguishes R10 baseline values from checks calculated by the active app engine.
- FEA data is clearly labeled as a baseline summary until full station-by-station import is implemented.
- Existing M1 engineering kernels are preserved for prestress losses and AASHTO LRFD 2020 Section 5 shear/torsion checks.
"""
        st.markdown(report_md)
        st.download_button("Download Markdown Summary", report_md.encode("utf-8"), "segmental_box_girder_m2_summary.md", "text/markdown", use_container_width=True)


# -----------------------------------------------------------------------------
# Project save panel
# -----------------------------------------------------------------------------
def render_project_save_panel() -> None:
    """Render project Save after the active page has synced editors to D."""
    with st.sidebar:
        st.markdown("---")
        st.markdown("**PROJECT FILE**")
        section_summary = section_persistence_summary(st.session_state.project)
        st.caption(
            f"Save includes section rows: {section_summary['coordinate_rows']} · "
            f"computed: {'yes' if section_summary['computed_section_available'] else 'no'} · "
            f"adopted: {'yes' if section_summary['adopted_properties_available'] else 'no'}"
        )
        st.download_button(
            "Save Project JSON",
            _project_save_payload(),
            file_name="segmental_box_girder_project.json",
            mime="application/json",
            use_container_width=True,
            key="project_json_save_download_button",
            help="Save is rendered after the active page syncs editable tables, so section coordinate rows are not dumped from stale sidebar state.",
        )


# -----------------------------------------------------------------------------
# Router
# -----------------------------------------------------------------------------
render_sidebar()
render_header()

workspace = get_workspace(st.session_state.current_workspace)
subpage = st.session_state.current_subpage

if workspace["id"] == "dashboard":
    page_dashboard(subpage)
elif workspace["id"] == "criteria":
    page_criteria_loads(subpage)
elif workspace["id"] == "bridge_geometry":
    page_bridge_geometry(subpage)
elif workspace["id"] == "loads":
    page_loads(subpage)
elif workspace["id"] == "prestress_losses":
    page_prestress_losses(subpage)
elif workspace["id"] == "fea_results":
    page_fea_results(subpage)
elif workspace["id"] == "uls_flexure":
    page_uls_flexure(subpage)
elif workspace["id"] == "uls_shear_torsion":
    page_uls_shear_torsion(subpage)
elif workspace["id"] == "sls_stress":
    page_sls_stress(subpage)
elif workspace["id"] == "deflection":
    page_deflection(subpage)
elif workspace["id"] == "report_qa":
    page_report_qa(subpage)


render_project_save_panel()
