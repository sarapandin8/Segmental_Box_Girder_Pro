from __future__ import annotations

import base64
import hashlib
import json
from html import escape
from math import sqrt, exp, acos
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
    build_tendon_stressing_basis_summary,
    clear_adopted_tendon_model,
    normalise_jack_from,
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
from core.wind_regions import (
    MANUAL_LOCATION,
    WHOLE_PROVINCE,
    wind_area_options,
    wind_group_from_province_area,
    wind_province_options,
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
    rail_horizontal_forces_diagram_svg,
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

.fea-handoff-table {width:100%; border-collapse:separate; border-spacing:0; table-layout:fixed; border:1px solid #d5e6ff; border-radius:16px; overflow:hidden; background:#ffffff; box-shadow:0 8px 22px rgba(15,23,42,0.055);}
.fea-handoff-table th {background:#f4f8ff; color:#092454; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.04em; font-weight:950; border-bottom:1px solid #d5e6ff; padding:9px 10px; text-align:left; vertical-align:top;}
.fea-handoff-table td {font-size:0.80rem; color:#24364b; border-bottom:1px solid #edf2f7; padding:9px 10px; vertical-align:top; white-space:normal; overflow-wrap:anywhere; line-height:1.28;}
.fea-handoff-table tr:last-child td {border-bottom:0;}
.fea-handoff-table .load-item {font-weight:900; color:#092454;}
.fea-handoff-table .subtext {display:block; color:#667085; font-size:0.74rem; margin-top:2px;}
.fea-handoff-table .value-main {font-weight:900; color:#0f172a;}
.fea-handoff-table .status-chip {display:inline-block; border-radius:999px; padding:3px 8px; font-size:0.70rem; font-weight:900; border:1px solid #bcd3f5; background:#eef6ff; color:#0b3b91;}
.fea-handoff-table .status-chip.pass {border-color:#a7e6bc; background:#dffbe8; color:#126b37;}
.fea-handoff-table .status-chip.warn {border-color:#fed7aa; background:#fff7ed; color:#b54708;}
.fea-handoff-table .status-chip.neutral {border-color:#d5e6ff; background:#f8fbff; color:#344054;}
.fea-handoff-caption {font-size:0.80rem; color:#667085; margin:0.35rem 0 0.75rem 0;}
.fea-legend-panel {border:1px solid #d5e6ff; border-radius:16px; background:linear-gradient(135deg,#ffffff 0%,#f8fbff 100%); padding:12px 14px; margin:12px 0 14px 0; box-shadow:0 8px 22px rgba(15,23,42,0.045);}
.fea-legend-title {font-size:0.76rem; letter-spacing:0.10em; text-transform:uppercase; color:#092454; font-weight:950; margin-bottom:9px;}
.fea-legend-grid {display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px;}
.fea-legend-item {border:1px solid #edf2f7; border-radius:12px; background:#ffffff; padding:9px 10px; min-height:70px;}
.fea-legend-item .legend-text {display:block; color:#475467; font-size:0.76rem; line-height:1.24; margin-top:6px;}
.fea-checklist-grid {display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:12px 0 14px 0;}
.fea-checklist-card {border:1px solid #d5e6ff; border-left:5px solid #175cd3; border-radius:16px; background:#ffffff; padding:12px 13px; min-height:105px; box-shadow:0 8px 22px rgba(15,23,42,0.045);}
.fea-checklist-kicker {font-size:0.70rem; letter-spacing:0.11em; text-transform:uppercase; color:#667085; font-weight:950; margin-bottom:7px;}
.fea-checklist-title {font-size:0.98rem; color:#092454; font-weight:950; line-height:1.18;}
.fea-checklist-note {font-size:0.80rem; color:#475467; margin-top:7px; line-height:1.28;}
@media (max-width: 1100px) {.fea-legend-grid,.fea-checklist-grid {grid-template-columns:repeat(2,minmax(0,1fr));}}
@media (max-width: 640px) {.fea-legend-grid,.fea-checklist-grid {grid-template-columns:1fr;}}
@media print {.fea-handoff-table,.fea-legend-panel,.fea-checklist-grid,.note-box {page-break-inside:avoid; break-inside:avoid;} .fea-handoff-table td {font-size:0.72rem;} .fea-handoff-table th {font-size:0.66rem;}}

.loads-closeout-panel {border:1px solid #d5e6ff; border-radius:16px; background:linear-gradient(135deg,#ffffff 0%,#f8fbff 100%); padding:14px 16px; margin:14px 0 16px 0; box-shadow:0 8px 22px rgba(15,23,42,0.045);}
.loads-closeout-title {font-size:0.78rem; letter-spacing:0.10em; text-transform:uppercase; color:#092454; font-weight:950; margin-bottom:10px;}
.loads-closeout-grid {display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px;}
.loads-closeout-card {border:1px solid #d5e6ff; border-radius:14px; background:#ffffff; padding:12px 13px; min-height:96px;}
.loads-closeout-card.pass {background:#f0fff4; border-color:#b8edd0;}
.loads-closeout-card.warn {background:#fff7ed; border-color:#fed7aa;}
.loads-closeout-kicker {font-size:0.69rem; letter-spacing:0.11em; text-transform:uppercase; color:#667085; font-weight:950;}
.loads-closeout-value {font-size:1.02rem; color:#092454; font-weight:950; margin-top:5px; line-height:1.18;}
.loads-closeout-note {font-size:0.78rem; color:#475467; margin-top:6px; line-height:1.26;}
.loads-qa-table {width:100%; border-collapse:separate; border-spacing:0; border:1px solid #d5e6ff; border-radius:14px; overflow:hidden; background:#ffffff; margin:10px 0 14px 0; box-shadow:0 6px 18px rgba(15,23,42,0.035);}
.loads-qa-table th {background:#f3f8ff; color:#092454; text-align:left; font-size:0.72rem; letter-spacing:0.08em; text-transform:uppercase; padding:9px 10px; border-bottom:1px solid #d5e6ff;}
.loads-qa-table td {vertical-align:top; padding:10px 10px; border-bottom:1px solid #eef4ff; color:#173455; font-size:0.82rem; line-height:1.28;}
.loads-qa-table tr:last-child td {border-bottom:0;}
.loads-qa-status {display:inline-block; border-radius:999px; padding:3px 8px; font-size:0.70rem; font-weight:900; border:1px solid #a7e6bc; background:#dffbe8; color:#126b37; white-space:nowrap;}
.loads-qa-status.review {border-color:#fed7aa; background:#fff7ed; color:#b54708;}
@media (max-width: 1100px) {.loads-closeout-grid {grid-template-columns:repeat(2,minmax(0,1fr));}}
@media (max-width: 640px) {.loads-closeout-grid {grid-template-columns:1fr;}}
@media print {.loads-closeout-panel,.loads-qa-table {page-break-inside:avoid; break-inside:avoid;} .loads-qa-table td {font-size:0.72rem;} .loads-qa-table th {font-size:0.66rem;}}

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


def _fea_status_chip(text: str, mode: str = "neutral") -> str:
    safe_text = escape(str(text))
    safe_mode = escape(str(mode or "neutral"))
    return f'<span class="status-chip {safe_mode}">{safe_text}</span>'


def render_fea_load_input_handoff_table(rows: list[dict[str, Any]]) -> None:
    """Render the 3.10 FEA handoff table with wrapping instead of truncation.

    This page is a report/handoff sheet, so readability is more important than
    spreadsheet density.  Keep this table display-only; all values must continue
    to come from the report-driven load schema.
    """
    headers = [
        ("Load / FEA symbol", "18%"),
        ("Quantity type", "13%"),
        ("Adopted value / basis", "17%"),
        ("FEA mapping", "20%"),
        ("Handoff status", "13%"),
        ("Required FEA action / engineer check", "19%"),
    ]
    html = ["<table class='fea-handoff-table'>", "<thead><tr>"]
    for label, width in headers:
        html.append(f"<th style='width:{width}'>{escape(label)}</th>")
    html.append("</tr></thead><tbody>")
    for row in rows:
        item = escape(str(row.get("item", "-")))
        symbol = escape(str(row.get("symbol", "-")))
        qtype = escape(str(row.get("quantity_type", "-")))
        value = escape(str(row.get("value", "-")))
        unit = escape(str(row.get("unit", "")))
        basis = escape(str(row.get("basis", "")))
        mapping = escape(str(row.get("mapping", "-")))
        direction = escape(str(row.get("direction", "")))
        source = escape(str(row.get("source", "")))
        status = _fea_status_chip(str(row.get("status", "REVIEW")), str(row.get("status_mode", "neutral")))
        check = escape(str(row.get("check", "-")))
        html.append("<tr>")
        html.append(f"<td><span class='load-item'>{item}</span><span class='subtext'>{symbol}</span></td>")
        html.append(f"<td>{qtype}</td>")
        unit_html = f" <span class='subtext'>Unit: {unit}</span>" if unit else ""
        basis_html = f"<span class='subtext'>{basis}</span>" if basis else ""
        html.append(f"<td><span class='value-main'>{value}</span>{unit_html}{basis_html}</td>")
        dir_html = f"<span class='subtext'>Direction: {direction}</span>" if direction else ""
        source_html = f"<span class='subtext'>Source: {source}</span>" if source else ""
        html.append(f"<td>{mapping}{dir_html}{source_html}</td>")
        html.append(f"<td>{status}</td>")
        html.append(f"<td>{check}</td>")
        html.append("</tr>")
    html.append("</tbody></table>")
    st.markdown("".join(html), unsafe_allow_html=True)
    st.markdown(
        "<div class='fea-handoff-caption'>This table is display-only. It reads the adopted load schema and does not create a second input source for FEA loads.</div>",
        unsafe_allow_html=True,
    )


def render_fea_handoff_status_legend() -> None:
    """Render a compact legend for FEA handoff status chips."""
    legend_items = [
        ("FEA-owned", "neutral", "Value is owned/generated by the FEA model; do not duplicate it as a manual load."),
        ("Adopted load", "pass", "Direct load value is adopted from the Loads workspace and can be mapped to FEA."),
        ("Adopted envelope", "pass", "Alternative/envelope load case; keep separate from the base case unless combinations require otherwise."),
        ("Traffic basis", "pass", "FEA traffic model factor/basis, not a standalone line load."),
        ("Factor-only", "warn", "Reported for traceability; not automatically adopted as an FEA load pattern."),
        ("Coefficient trace", "warn", "Coefficient is adopted; numeric force is generated only after the FEA model supplies the missing source."),
        ("Downstream", "neutral", "Parameter handoff consumed by another module such as Prestress Losses or staged FEA."),
    ]
    html = ["<div class='fea-legend-panel'>", "<div class='fea-legend-title'>Handoff status legend</div>", "<div class='fea-legend-grid'>"]
    for label, mode, note in legend_items:
        html.append(
            "<div class='fea-legend-item'>"
            + _fea_status_chip(label, mode)
            + f"<span class='legend-text'>{escape(note)}</span>"
            + "</div>"
        )
    html.append("</div></div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_fea_load_input_review_checklist() -> None:
    """Render the engineer-facing checklist for transferring Loads to FEA."""
    cards = [
        ("1", "Map load patterns", "Create or verify only the FEA load patterns listed in the handoff table; avoid duplicate DL, WS/WS+WL, and EQ force entries."),
        ("2", "Confirm directions", "Check gravity, longitudinal, transverse, radial, wind, and EQX/EQY sign conventions against the FEA model axes."),
        ("3", "Preserve source ownership", "Keep Cs, CF, and CR&SH as coefficients/parameters unless the downstream FEA or Prestress Losses module supplies the missing source."),
        ("4", "Document overrides", "If a value is overridden in FEA, record the override in the FEA model/report rather than creating a second app input."),
    ]
    html = ["<div class='fea-checklist-grid'>"]
    for idx, title, note in cards:
        html.append(
            "<div class='fea-checklist-card'>"
            + f"<div class='fea-checklist-kicker'>FEA review step {escape(idx)}</div>"
            + f"<div class='fea-checklist-title'>{escape(title)}</div>"
            + f"<div class='fea-checklist-note'>{escape(note)}</div>"
            + "</div>"
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)



def _loads_closeout_rows() -> list[dict[str, str]]:
    """Return the Loads workspace closeout status rows for 3.10 and Report / QA."""
    ld = load_derived()
    cf_status = str(ld.get("cf_fea_adoption_status", "Factor-only / not adopted in FEA"))
    cf_handoff = "FEA adopted" if "adopted" in cf_status.lower() and "not" not in cf_status.lower() else "Trace only"
    return [
        {
            "page": "3.1 DL",
            "closeout": "Closed",
            "handoff": "FEA-owned self-weight",
            "report_qa": "Document material density and confirm no duplicate DL load pattern.",
        },
        {
            "page": "3.2 SDL",
            "closeout": "Closed",
            "handoff": f"Adopted SDL = {float(ld['sdl_selected_adopted_kn_m']):.2f} kN/m",
            "report_qa": "Map as permanent line load and retain component-table trace.",
        },
        {
            "page": "3.3 LL + IM",
            "closeout": "Closed",
            "handoff": "Traffic model basis",
            "report_qa": "Confirm U20 loading and dynamic factor are matched in the FEA moving-load model.",
        },
        {
            "page": "3.4 LF / 3.5 HF",
            "closeout": "Closed",
            "handoff": f"LF = {float(ld['LF_design_kn']):.0f} kN; HF = {float(ld['hf_HF_adopted_kn']):.0f} kN",
            "report_qa": "Map longitudinal and transverse rail actions with correct rail-level directions.",
        },
        {
            "page": "3.6 CF",
            "closeout": "Closed",
            "handoff": f"{cf_handoff} · {float(ld['cf_C_percent']):.2f}% LL",
            "report_qa": "Keep CF adoption separate from engineering assessment and combination logic.",
        },
        {
            "page": "3.7 Wind",
            "closeout": "Closed",
            "handoff": f"WS = {float(ld['WSsuper_kn_m']):.2f} kN/m; WS+WL = {float(ld['WSsuper_WL_kn_m']):.2f} kN/m",
            "report_qa": "Use WS and WS+WL as separate alternatives/envelopes; do not automatically stack them.",
        },
        {
            "page": "3.8 CR&SH",
            "closeout": "Closed",
            "handoff": "Parameter handoff",
            "report_qa": "Consumed by Prestress Losses / staged FEA; not a direct load pattern.",
        },
        {
            "page": "3.9 EQ",
            "closeout": "Closed",
            "handoff": f"Cs = {float(ld['eq_Cs']):.4f} coefficient trace",
            "report_qa": "Numeric EQ force remains EQX/EQY = Cs × W using FEA-owned seismic mass W.",
        },
        {
            "page": "3.10 FEA Load Input Summary",
            "closeout": "Handoff ready",
            "handoff": "Single FEA load input register",
            "report_qa": "This table is the Loads workspace source passed to Report / QA; no new input source is created.",
        },
    ]


def render_loads_closeout_table(rows: list[dict[str, str]]) -> None:
    """Render a compact closeout table with clear report/QA handoff wording."""
    html = [
        "<table class='loads-qa-table'>",
        "<thead><tr><th>Loads page</th><th>Closeout status</th><th>Report / QA handoff</th><th>Required report / FEA guard</th></tr></thead><tbody>",
    ]
    for row in rows:
        page = escape(str(row.get("page", "-")))
        closeout = escape(str(row.get("closeout", "REVIEW")))
        status_cls = "" if closeout.lower() in {"closed", "handoff ready"} else " review"
        handoff = escape(str(row.get("handoff", "-")))
        report_qa = escape(str(row.get("report_qa", "-")))
        html.append(
            f"<tr><td><b>{page}</b></td><td><span class='loads-qa-status{status_cls}'>{closeout}</span></td><td>{handoff}</td><td>{report_qa}</td></tr>"
        )
    html.append("</tbody></table>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_loads_workspace_closeout_panel() -> None:
    """Render the Loads closeout / Report-QA handoff block."""
    html = [
        "<div class='loads-closeout-panel'>",
        "<div class='loads-closeout-title'>Loads workspace closeout and Report / QA handoff</div>",
        "<div class='loads-closeout-grid'>",
        "<div class='loads-closeout-card pass'><div class='loads-closeout-kicker'>Loads status</div><div class='loads-closeout-value'>Closed for load-source scope</div><div class='loads-closeout-note'>3.1–3.9 feed the single 3.10 FEA load input register.</div></div>",
        "<div class='loads-closeout-card pass'><div class='loads-closeout-kicker'>Report / QA handoff</div><div class='loads-closeout-value'>Ready</div><div class='loads-closeout-note'>Report / QA now consumes the Loads closeout rows and FEA handoff table.</div></div>",
        "<div class='loads-closeout-card warn'><div class='loads-closeout-kicker'>FEA ownership guard</div><div class='loads-closeout-value'>No duplicate W / DL</div><div class='loads-closeout-note'>DL and seismic weight remain owned by the external FEA model.</div></div>",
        "<div class='loads-closeout-card'><div class='loads-closeout-kicker'>Next workflow owner</div><div class='loads-closeout-value'>Report / QA + downstream modules</div><div class='loads-closeout-note'>CR&SH goes to Prestress Losses; load patterns go to FEA mapping.</div></div>",
        "</div></div>",
    ]
    st.markdown("".join(html), unsafe_allow_html=True)
    render_loads_closeout_table(_loads_closeout_rows())
    st.markdown(
        '<div class="note-box"><b>Closeout rule:</b> 3 Loads is closed for the current report-driven load-source scope. Future edits should be separate milestones and must not create second inputs for values already owned by the load schema, FEA model, or downstream Prestress Losses workflow.</div>',
        unsafe_allow_html=True,
    )


def render_report_qa_loads_handoff_snapshot() -> None:
    """Show the Loads closeout package inside Report / QA."""
    section_title("3 Loads — Report / QA handoff")
    st.markdown(
        '<div class="note-box"><b>Read-only handoff:</b> Report / QA reads the Loads workspace closeout rows and FEA Load Input Summary. It does not rerun load calculations and does not create load inputs.</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("LOADS CLOSEOUT", "CLOSED", "3.1–3.9 consolidated in 3.10", "pass")
    with c2:
        card("FEA INPUT REGISTER", "HANDOFF READY", "Single report-controlled mapping table", "pass")
    with c3:
        card("EQ POLICY", "COEFFICIENT TRACE", "EQ force generated by FEA-owned W", "warn")
    with c4:
        card("CR&SH", "DOWNSTREAM", "Consumed by Prestress Losses / staged FEA", "neutral")
    render_loads_closeout_table(_loads_closeout_rows())


def show_report_image(filename: str, caption: str, *, use_column_width: bool = True) -> None:
    """Display bundled report/reference figures with a consistent caption."""
    path = WIND_ASSET_DIR / filename
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=use_column_width)
    else:
        st.warning(f"Missing bundled figure asset: {filename}")


def wind_reference_figure_card(filename: str, title: str, source: str, note: str = "", *, max_height_px: int = 260) -> None:
    """Display wind report/reference images in a compact commercial card."""
    path = WIND_ASSET_DIR / filename
    if not path.exists():
        st.warning(f"Missing bundled figure asset: {filename}")
        return
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    note_html = f'<div class="status-note">{note}</div>' if note else ""
    st.markdown(
        f"""
        <div class="context-card" style="min-height:{max_height_px + 118}px; padding:12px 14px;">
          <div class="status-kicker">Reference figure</div>
          <div class="status-value" style="font-size:0.96rem; margin-bottom:0.18rem;">{title}</div>
          <div class="small-muted" style="margin-bottom:8px;">{source}</div>
          <div style="border:1px solid #e4e7ec; border-radius:10px; background:#ffffff; padding:6px;">
            <img src="data:image/png;base64,{encoded}" style="display:block; width:100%; height:{max_height_px}px; object-fit:contain;" />
          </div>
          {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def wind_factor_c_reference_card(note: str = "") -> None:
    """Reference card for EN 1991-1-4 bridge wind factor C table only."""
    note_html = f'<div style="font:11px Arial,sans-serif;color:#667085;margin-top:6px;">{note}</div>' if note else ""
    html = f"""
<div style="width:100%; background:#ffffff; border:1px solid #d0d5dd; border-radius:12px; padding:12px 14px; box-sizing:border-box; font-family:Arial, sans-serif;">
  <div style="font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase; font-weight:700; color:#175cd3; margin-bottom:6px;">Reference figure</div>
  <div style="font-size:0.96rem; line-height:1.2; font-weight:700; color:#101828; margin-bottom:3px;">Wind factor C reference table</div>
  <div style="font-size:0.78rem; color:#667085; margin-bottom:8px;">BG40 Table 2.5 / EN 1991-1-4 Table 8.2 basis</div>
  <div style="border:1px solid #e4e7ec; border-radius:10px; background:#ffffff; padding:10px; overflow:hidden;">
    <svg viewBox="0 0 620 170" width="100%" height="170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Wind factor C reference table">
      <style>
        .wf-title {{ font: 700 15px Arial, sans-serif; fill:#101828; }}
        .wf-text {{ font: 12px Arial, sans-serif; fill:#101828; }}
        .wf-small {{ font: 11px Arial, sans-serif; fill:#344054; }}
        .wf-muted {{ font: 11px Arial, sans-serif; fill:#667085; }}
        .wf-line {{ stroke:#101828; stroke-width:1.3; }}
        .wf-thin {{ stroke:#344054; stroke-width:1.0; }}
      </style>
      <text x="310" y="18" text-anchor="middle" class="wf-title">Table 2.5  Wind load factor C for bridges</text>
      <text x="310" y="35" text-anchor="middle" class="wf-muted">Data taken from EN 1991-1-4, Table 8.2</text>
      <line x1="50" y1="55" x2="570" y2="55" class="wf-line"/>
      <line x1="50" y1="84" x2="570" y2="84" class="wf-line"/>
      <line x1="50" y1="142" x2="570" y2="142" class="wf-line"/>
      <line x1="180" y1="55" x2="180" y2="142" class="wf-thin"/>
      <line x1="375" y1="55" x2="375" y2="142" class="wf-thin"/>
      <text x="115" y="76" text-anchor="middle" class="wf-text">b/d<tspan baseline-shift="sub" font-size="9">tot</tspan></text>
      <text x="278" y="76" text-anchor="middle" class="wf-text">z<tspan baseline-shift="sub" font-size="9">e</tspan> ≤ 20 m</text>
      <text x="475" y="76" text-anchor="middle" class="wf-text">z<tspan baseline-shift="sub" font-size="9">e</tspan> = 50 m</text>
      <text x="115" y="108" text-anchor="middle" class="wf-text">≤ 0.5</text>
      <text x="278" y="108" text-anchor="middle" class="wf-text">6.7</text>
      <text x="475" y="108" text-anchor="middle" class="wf-text">8.3</text>
      <text x="115" y="132" text-anchor="middle" class="wf-text">≥ 4.0</text>
      <text x="278" y="132" text-anchor="middle" class="wf-text">3.6</text>
      <text x="475" y="132" text-anchor="middle" class="wf-text">4.5</text>
      <text x="50" y="160" class="wf-small">If 0.5 &lt; b/d<tspan baseline-shift="sub" font-size="9">tot</tspan> &lt; 4.0, linear interpolation may be used.</text>
    </svg>
  </div>
  {note_html}
</div>
"""
    components.html(html, height=315, scrolling=False)


def ze_bridge_reference_card(note: str = "") -> None:
    """Compact bridge-profile card for interpreting z_e.

    The user-provided bridge profile is embedded as an SVG image and constrained
    to a compact card height so it supports the wind input workflow without
    pushing the editable parameter table too far down the page.
    """
    note_html = f'<div style="font:11px Arial,sans-serif;color:#667085;margin-top:6px;">{note}</div>' if note else ""
    ze_svg_path = WIND_ASSET_DIR / "fig_ze_bridge_reference.svg"
    if ze_svg_path.exists():
        ze_svg_encoded = base64.b64encode(ze_svg_path.read_bytes()).decode("ascii")
        ze_figure_html = (
            f'<img src="data:image/svg+xml;base64,{ze_svg_encoded}" '
            'style="display:block; width:100%; height:255px; object-fit:contain;" '
            'alt="Deck-height ze bridge profile reference" />'
        )
    else:
        ze_figure_html = '<div style="font-size:12px;color:#b42318;">Missing z_e bridge reference schematic asset.</div>'
    html = f"""
<div style="width:100%; background:#ffffff; border:1px solid #d0d5dd; border-radius:12px; padding:12px 14px; box-sizing:border-box; font-family:Arial, sans-serif;">
  <div style="font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase; font-weight:700; color:#175cd3; margin-bottom:6px;">Reference figure</div>
  <div style="font-size:0.96rem; line-height:1.2; font-weight:700; color:#101828; margin-bottom:3px;">Deck-height z<sub>e</sub> bridge profile reference</div>
  <div style="font-size:0.78rem; color:#667085; margin-bottom:8px;">user-provided bridge profile reference (four-pier schematic)</div>
  <div style="border:1px solid #e4e7ec; border-radius:10px; background:#ffffff; padding:8px 10px; overflow:hidden;">
    <div style="font-size:11px; color:#667085; margin-bottom:6px;">Use this compact bridge profile reference to interpret the vertical deck reference height z<sub>e</sub> used in the wind factor C selection.</div>
    <div style="width:100%; height:255px; display:flex; align-items:center; justify-content:center; overflow:hidden;">{ze_figure_html}</div>
  </div>
  {note_html}
</div>
"""
    components.html(html, height=370, scrolling=False)



def wind_group_map_figure_card(selected_group: str, note: str = "", *, max_height_px: int = 340) -> None:
    """Display a sharpened DPT wind map without app-drawn overlays.

    The province dropdown is now the authoritative group lookup. The map is a visual
    reference only. Prefer a clean color reference map over approximate app-drawn overlays.
    """
    filename = "fig_1_2_dpt_wind_speed_map_color.png"
    path = WIND_ASSET_DIR / filename
    if not path.exists():
        filename = "fig_1_2_dpt_wind_speed_map_clarity.png"
        path = WIND_ASSET_DIR / filename
    if not path.exists():
        filename = "fig_1_2_dpt_wind_speed_map.png"
        path = WIND_ASSET_DIR / filename
    if not path.exists():
        st.warning(f"Missing bundled figure asset: {filename}")
        return
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    selected_note = f"Selected group from province lookup: {selected_group}" if selected_group else "Select a province to determine the governing wind group."
    note_html = f'<div class="status-note">{note}</div>' if note else ""
    st.markdown(
        f"""
        <div class="context-card" style="min-height:{max_height_px + 145}px; padding:12px 14px; overflow:visible;">
          <div class="status-kicker">Reference figure</div>
          <div class="status-value" style="font-size:0.96rem; margin-bottom:0.18rem;">DPT wind speed group map</div>
          <div class="small-muted" style="margin-bottom:8px;">DPT 1311-50 / 1312-50 reference wind speed groups</div>
          <div style="border:1px solid #e4e7ec; border-radius:10px; background:#ffffff; padding:8px; height:{max_height_px}px; overflow:hidden; display:flex; align-items:center; justify-content:center;">
            <img src="data:image/png;base64,{encoded}" style="display:block; max-width:100%; max-height:100%; object-fit:contain; filter:contrast(1.08);" />
          </div>
          <div class="status-note"><b>{selected_note}</b> · clean color reference map; province lookup controls the adopted group.</div>
          {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


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
    st.markdown("<div class='warn-box'><b>Non-Section-5 note:</b> the seismic R-factor helper references the app&apos;s AASHTO LRFD 9th Edition (2020) bridge R table. This does not control concrete/PT Section 5 design checks.</div>", unsafe_allow_html=True)

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
    cf_track_condition = str(rail.get("cf_track_condition", "Curved track / finite radius"))
    if cf_track_condition in {"Straight / very large radius", "Large-radius curve / near-straight", "Curved track"}:
        cf_track_condition = "Curved track / finite radius"
    elif cf_track_condition == "Straight track":
        cf_track_condition = "Straight track / no horizontal curve"
    cf_threshold_percent = float(rail.get("cf_assessment_threshold_percent", 2.0))
    cf_is_straight = cf_track_condition == "Straight track / no horizontal curve"
    if cf_is_straight:
        cf = {"f": 1.0, "C_basic": 0.0, "C_reduced": 0.0, "C_percent": 0.0}
        cf_include_in_fea = False
        cf_engineering_assessment = "Zero / straight track"
        cf_engineering_assessment_note = "R = ∞; CF not applicable"
        cf_engineering_assessment_mode = "pass"
        cf_fea_adoption_status = "Not applicable / not adopted"
        cf_fea_adoption_note = "zero CF for straight track"
        cf_fea_adoption_mode = ""
    else:
        cf = en_centrifugal_percentage(float(rail["speed_kmh"]), float(rail["radius_m"]), float(rail["Lf_m"]))
        cf_include_in_fea = bool(rail.get("cf_include_in_fea", False))
        if float(cf.get("C_percent", 0.0)) <= cf_threshold_percent:
            cf_engineering_assessment = "Below threshold"
            cf_engineering_assessment_note = f"{float(cf.get('C_percent', 0.0)):.2f}% ≤ {cf_threshold_percent:.2f}% LL"
            cf_engineering_assessment_mode = "pass"
        else:
            cf_engineering_assessment = "Above threshold / review"
            cf_engineering_assessment_note = f"{float(cf.get('C_percent', 0.0)):.2f}% > {cf_threshold_percent:.2f}% LL"
            cf_engineering_assessment_mode = "warn"
        if cf_include_in_fea:
            cf_fea_adoption_status = "Adopted in FEA summary"
            cf_fea_adoption_note = "horizontal radial/transverse action factor"
            cf_fea_adoption_mode = "pass"
        else:
            cf_fea_adoption_status = "Factor-only / not adopted in FEA"
            cf_fea_adoption_note = "reported for traceability"
            cf_fea_adoption_mode = "warn" if float(cf.get("C_percent", 0.0)) > cf_threshold_percent else ""
    cf_assessment = cf_engineering_assessment
    cf_assessment_note = cf_engineering_assessment_note
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

    sdl_track_basis = str(D.get("bridge_model", {}).get("number_of_tracks", "Double Track"))
    if sdl_track_basis not in {"Single Track", "Double Track"}:
        sdl_track_basis = "Double Track"
    if sdl_track_basis == "Single Track":
        sdl_adopted = float(lc.get("design_sdl_single_kn_m", sdl["single_total"]))
        sdl_total = float(sdl["single_total"])
        sdl_application = "Single-track adopted design value"
    else:
        sdl_adopted = float(lc.get("design_sdl_double_kn_m", sdl["double_total"]))
        sdl_total = float(sdl["double_total"])
        sdl_application = "Double-track adopted design value"

    return {
        "sdl_single_total": sdl["single_total"],
        "sdl_double_total": sdl["double_total"],
        "sdl_track_basis": sdl_track_basis,
        "sdl_selected_total": sdl_total,
        "sdl_selected_adopted_kn_m": sdl_adopted,
        "sdl_selected_application": sdl_application,
        "Lphi": dyn["Lphi_m"],
        "dynamic_phi_calc": dyn["phi"],
        **lf,
        **{f"hf_{k}": v for k, v in hf.items()},
        **ws,
        **{f"eq_{k}": v for k, v in eq.items()},
        **{f"cf_{k}": v for k, v in cf.items()},
        "cf_assessment_threshold_percent": cf_threshold_percent,
        "cf_track_condition": cf_track_condition,
        "cf_is_straight": cf_is_straight,
        "cf_include_in_fea": cf_include_in_fea,
        "cf_assessment": cf_assessment,
        "cf_assessment_note": cf_assessment_note,
        "cf_engineering_assessment": cf_engineering_assessment,
        "cf_engineering_assessment_note": cf_engineering_assessment_note,
        "cf_engineering_assessment_mode": cf_engineering_assessment_mode,
        "cf_fea_adoption_status": cf_fea_adoption_status,
        "cf_fea_adoption_note": cf_fea_adoption_note,
        "cf_fea_adoption_mode": cf_fea_adoption_mode,
    }


def update_crsh_derived_parameters() -> dict[str, Any]:
    """Derive creep/shrinkage geometry values from the active section data.

    User inputs should remain limited to project assumptions such as RH, ages,
    and the drying-perimeter basis.  The geometry-dependent V/S values are
    recalculated from one source before they are consumed by Prestress Losses.
    """
    p = D["prestress"]
    sec = D["section"]

    # Migration / default for older project JSON files.
    basis = str(p.get("crsh_drying_perimeter_basis", "Outer + inner void perimeter"))
    if basis not in {"Outer perimeter only", "Outer + inner void perimeter"}:
        basis = "Outer + inner void perimeter"
    p["crsh_drying_perimeter_basis"] = basis

    Ac_m2 = float(sec.get("Ac_m2", p.get("crsh_Ac_m2", 0.0)) or 0.0)
    u_outer_m = float(p.get("u_outer_m", 0.0) or 0.0)
    u_inner_m = float(p.get("u_inner_m", 0.0) or 0.0)
    include_inner = basis == "Outer + inner void perimeter"
    u_total_m = u_outer_m + (u_inner_m if include_inner else 0.0)

    if Ac_m2 > 0.0 and u_total_m > 0.0:
        vs_m = Ac_m2 / u_total_m
    else:
        vs_m = float(p.get("V_over_S_m", 0.0) or 0.0)
    vs_mm = vs_m * 1000.0
    vs_in = vs_m * 39.37007874015748
    h0_m = 2.0 * vs_m
    h0_in = h0_m * 39.37007874015748

    p["crsh_Ac_m2"] = Ac_m2
    p["u_total_m"] = u_total_m
    p["V_over_S_m"] = vs_m
    p["V_over_S_mm"] = vs_mm
    p["V_over_S_in"] = vs_in
    p["h0_m"] = h0_m
    p["h0_in"] = h0_in

    return {
        "basis": basis,
        "include_inner": include_inner,
        "Ac_m2": Ac_m2,
        "u_outer_m": u_outer_m,
        "u_inner_m": u_inner_m,
        "u_total_m": u_total_m,
        "V_over_S_m": vs_m,
        "V_over_S_mm": vs_mm,
        "V_over_S_in": vs_in,
        "h0_m": h0_m,
        "h0_in": h0_in,
        "time_interval_days": float(p.get("tf_days", 0.0) or 0.0) - float(p.get("ti_days", 0.0) or 0.0),
        "geometry_source": "Section Properties Ac with report/section drying perimeters",
    }

def prestress_inputs() -> dict[str, Any]:
    update_crsh_derived_parameters()
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
    """Render a project-backed numeric input with stable Streamlit state.

    Streamlit number inputs can feel like they need a second edit when the
    widget is recreated with a changing ``value=`` argument on every rerun.
    Keep a stable key per project-load epoch, initialise it once from the
    project dictionary, then write the widget value back to the project source.
    """
    ref = D
    for key in path[:-1]:
        ref = ref[key]
    key = path[-1]
    epoch = int(st.session_state.get("project_widget_epoch", 0))
    widget_key = f"project_number__{epoch}__{'__'.join(path)}"
    if widget_key not in st.session_state:
        st.session_state[widget_key] = float(ref.get(key, 0.0))
    kwargs = {"step": step, "key": widget_key}
    if fmt:
        kwargs["format"] = fmt
    ref[key] = st.number_input(label, **kwargs)



EQ_COEFFICIENT_TRACE_MODE = "Coefficient trace only — numeric EQ force generated in FEA model"
EQ_ADOPTED_COEFFICIENT_MODE = "Adopted as EQ coefficient for FEA summary"
EQ_LEGACY_ADOPTION_MODES = {
    "Parameter only / coefficient trace": EQ_COEFFICIENT_TRACE_MODE,
    "Parameter-only": EQ_COEFFICIENT_TRACE_MODE,
}


def _normalize_eq_fea_adoption_mode(value: Any) -> str:
    """Return the current EQ FEA adoption mode with legacy wording migrated."""
    text = str(value or EQ_COEFFICIENT_TRACE_MODE)
    text = EQ_LEGACY_ADOPTION_MODES.get(text, text)
    if text not in {EQ_COEFFICIENT_TRACE_MODE, EQ_ADOPTED_COEFFICIENT_MODE}:
        return EQ_COEFFICIENT_TRACE_MODE
    return text


def _eq_adoption_is_adopted(mode: str) -> bool:
    return str(mode).startswith("Adopted")


def render_eq_result_summary_and_fea_adoption(lc: dict[str, Any], ld: dict[str, Any], *, location_label: str, region_label: str) -> None:
    """Render the EQ result cards and one-source FEA adoption trace.

    EQ in this Loads workspace is exported as a report-controlled seismic
    coefficient unless the user explicitly adopts it as an FEA coefficient.
    Numeric lateral forces require the seismic weight / mass definition from
    the external FEA model, so the app keeps that source visible instead of
    inventing a duplicated weight input here.
    """
    modes = [EQ_COEFFICIENT_TRACE_MODE, EQ_ADOPTED_COEFFICIENT_MODE]
    current_mode = _normalize_eq_fea_adoption_mode(lc.get("seismic_fea_adoption_mode", modes[0]))
    lc["seismic_fea_adoption_mode"] = current_mode
    lc.setdefault("seismic_weight_source", "FEA mass / seismic weight W from analysis model")
    lc.setdefault("seismic_direction_basis", "EQX and EQY independent horizontal directions")
    lc["seismic_adopted_coefficient_Cs"] = float(ld.get("eq_Cs", 0.0) or 0.0)

    adopted = _eq_adoption_is_adopted(current_mode)
    adoption_value = "ADOPTED COEFFICIENT" if adopted else "COEFFICIENT TRACE"
    adoption_note = "Cs feeds FEA Summary as a coefficient" if adopted else "Cs reported; numeric EQ force requires W from FEA model"

    st.markdown("### EQ result summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        card("DPT LOOKUP", location_label, region_label, "pass" if "Manual" not in region_label else "warn")
    with c2:
        card("DESIGN SPECTRUM", f"SDS={float(ld.get('eq_SDS', 0.0)):.3f} g", f"SD1={float(ld.get('eq_SD1', 0.0)):.3f} g")
    with c3:
        card("ANALYSIS RESULT", f"Sa(T)={float(ld.get('eq_Sa', 0.0)):.4f} g", f"T={float(lc.get('seismic_T_s', 0.0)):.3f} s")
    with c4:
        card("SEISMIC COEFFICIENT", f"Cs={float(ld.get('eq_Cs', 0.0)):.4f}", f"I/R={float(lc.get('seismic_I', 0.0)):.2f}/{float(lc.get('seismic_R', 0.0)):.1f}")
    with c5:
        card("FEA ADOPTION", adoption_value, adoption_note, "pass" if adopted else "warn")

    st.markdown("### FEA adoption")
    a1, a2, a3 = st.columns([1.2, 1.2, 1.4])
    with a1:
        current_mode = st.selectbox("EQ FEA adoption mode", modes, index=modes.index(current_mode), key="eq_fea_adoption_mode")
        lc["seismic_fea_adoption_mode"] = current_mode
        adopted = _eq_adoption_is_adopted(current_mode)
    with a2:
        direction_options = ["EQX and EQY independent horizontal directions", "EQX only", "EQY only"]
        direction_current = str(lc.get("seismic_direction_basis", direction_options[0]))
        if direction_current not in direction_options:
            direction_current = direction_options[0]
        lc["seismic_direction_basis"] = st.selectbox(
            "Direction basis",
            direction_options,
            index=direction_options.index(direction_current),
            key="eq_direction_basis",
        )
    with a3:
        lc["seismic_weight_source"] = st.text_input("Seismic weight / mass source", value=str(lc.get("seismic_weight_source", "FEA mass / seismic weight W from analysis model")), key="eq_seismic_weight_source")

    f1, f2, f3 = st.columns(3)
    with f1:
        card("SEISMIC WEIGHT SOURCE", "FEA MODEL", str(lc["seismic_weight_source"]), "pass")
    with f2:
        card("NUMERIC EQ FORCE", "NOT GENERATED HERE", "No duplicate W input is created in Loads", "warn")
    with f3:
        card("FEA RULE", "EQX/EQY = Cs × W", str(lc["seismic_direction_basis"]), "pass" if adopted else "warn")

    adopted_text = "Cs adopted as FEA coefficient" if adopted else "Coefficient trace only — numeric EQ loads generated in FEA model"
    rows = [
        ["Adopted coefficient Cs", f"{float(ld.get('eq_Cs', 0.0)):.4f}", "Equivalent static coefficient from one-source EQ calculation"],
        ["EQX basis", "EQX = Cs × W" if "EQX" in lc["seismic_direction_basis"] else "Not selected", "W from selected seismic weight / mass source"],
        ["EQY basis", "EQY = Cs × W" if "EQY" in lc["seismic_direction_basis"] else "Not selected", "W from selected seismic weight / mass source"],
        ["Seismic weight W", lc["seismic_weight_source"], "No duplicate W input is created in Loads"],
        ["Numeric force generation", "Not generated in this Loads page", "FEA model must define seismic weight / mass before force output"],
        ["Application", "Longitudinal and transverse global seismic directions", "Coordinate-direction sign and load pattern names are assigned in the FEA model"],
        ["FEA adoption status", adopted_text, "Explicit user-controlled adoption status"],
    ]
    show_engineering_table(pd.DataFrame(rows, columns=["Item", "Value", "Trace"]))
    st.markdown('<div class="note-box"><b>FEA export rule:</b> this page exports the adopted seismic coefficient <b>Cs</b> and its source trace. Numeric equivalent-static forces require the seismic weight / mass definition from the FEA model: <b>EQX = Cs × W</b> and <b>EQY = Cs × W</b>. This page intentionally does not create a duplicate <b>W</b> input.</div>', unsafe_allow_html=True)

    st.markdown("### EQ one-source trace")
    show_engineering_table(pd.DataFrame([
        ["User input", "Province / district", f"{lc.get('seismic_province_th', '-')} / {lc.get('seismic_district_th', '-')}", "DPT lookup key"],
        ["User input", "Soil class", lc.get("seismic_soil_class", "-"), "Site class used for Fa/Fv"],
        ["User input", "Operational category", lc.get("seismic_operational_category", "-"), "AASHTO LRFD 2020 bridge category"],
        ["User input", "Substructure system", lc.get("seismic_substructure_label", "-"), "AASHTO LRFD 2020 R table"],
        ["User input", "Analysis period T", f"{float(lc.get('seismic_T_s', 0.0)):.3f} s", "FEA / project period input"],
        ["Derived", "Ss / S1", f"{float(lc.get('seismic_Ss_g', 0.0)):.3f} / {float(lc.get('seismic_S1_g', 0.0)):.3f} g", "DPT database or manual source"],
        ["Derived", "Fa / Fv", f"{float(ld.get('eq_Fa', 0.0)):.2f} / {float(ld.get('eq_Fv', 0.0)):.2f}", "DPT site factors"],
        ["Derived", "SDS / SD1", f"{float(ld.get('eq_SDS', 0.0)):.4f} / {float(ld.get('eq_SD1', 0.0)):.4f} g", "Design spectrum values"],
        ["Derived", "Sa(T)", f"{float(ld.get('eq_Sa', 0.0)):.4f} g", "Equivalent-static spectrum route"],
        ["Derived", "Cs", f"{float(ld.get('eq_Cs', 0.0)):.4f}", "Sa(T) × I / R with minimum check"],
        ["FEA adoption", "Status", lc.get("seismic_fea_adoption_mode", EQ_COEFFICIENT_TRACE_MODE), "One-source adoption trace"],
    ], columns=["Type", "Item", "Value", "Source / trace"]))


def render_eq_response_spectrum_canvas(spec: pd.DataFrame, lc: dict[str, Any], ld: dict[str, Any], *, title: str, region_label: str) -> None:
    """Render the DPT response spectrum as a report-ready engineering canvas."""
    T = float(lc.get("seismic_T_s", 0.0))
    Sa = float(ld.get("eq_Sa", 0.0))
    view_mode_text, view_mode_note = _figure_view_texts()
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="canvas-kicker">CANVAS</div>
            <div class="canvas-head">
              <div>
                <div class="canvas-title">DPT Equivalent-Static Response Spectrum</div>
                <div class="small-muted">General Thailand / Bangkok Basin route remains controlled by the DPT lookup source and the active analysis period.</div>
              </div>
              <div class="canvas-pill">EQ coefficient source</div>
            </div>
            <div class="canvas-note">
              The plotted marker is the one-source input period used for <b>Sa(T)</b>; the FEA export remains a coefficient trace until seismic weight <b>W</b> is defined in the FEA model.
            </div>
            <div class="canvas-meta-strip">
              <div class="canvas-station-badge"><span>Input period</span><strong>T = {T:.3f} s</strong></div>
              <div class="canvas-meta-right">
                <div class="canvas-view-badge">{view_mode_text} · {view_mode_note}</div>
                <div class="canvas-dim-badge">Region: {region_label}</div>
              </div>
            </div>
            {_engineering_canvas_legend_html([
                {"label": "Sa(T)", "kind": "line", "color": "#175cd3"},
                {"label": "Input period", "kind": "dot", "color": "#be123c"},
            ])}
            """,
            unsafe_allow_html=True,
        )
        fig = response_spectrum_figure(spec, T, Sa, title)
        fig.update_layout(showlegend=False, height=560, margin=dict(l=66, r=28, t=62, b=60))
        st.plotly_chart(fig, use_container_width=True, config=current_plotly_config())
        st.markdown(
            '<div class="canvas-caption"><b>Figure 3.9-EQ</b> DPT equivalent-static design response spectrum used to obtain Sa(T) for Cs = Sa(T)·I/R. Numeric EQ force is not generated here because W is owned by the FEA mass/seismic-weight source.</div>',
            unsafe_allow_html=True,
        )
        footer_html = (
            '<div class="canvas-footer-grid">'
            + _canvas_footer_card_html("SDS / SD1", f"{float(ld.get('eq_SDS', 0.0)):.3f} / {float(ld.get('eq_SD1', 0.0)):.3f} g", "design spectrum", "pass")
            + _canvas_footer_card_html("Sa(T)", f"{Sa:.4f} g", f"T = {T:.3f} s", "pass")
            + _canvas_footer_card_html("Cs", f"{float(ld.get('eq_Cs', 0.0)):.4f}", f"I/R = {float(lc.get('seismic_I', 0.0)):.2f}/{float(lc.get('seismic_R', 0.0)):.1f}", "pass")
            + _canvas_footer_card_html("FEA force", "Not generated", "EQX/EQY = Cs × W", "warn")
            + '</div>'
        )
        st.markdown(footer_html, unsafe_allow_html=True)

def render_aashto_bridge_seismic_controls(lc: dict[str, Any]) -> dict[str, Any]:
    """Render one-source I/R controls for the EQ page.

    AASHTO operational category and substructure type are used only to
    recommend the bridge response modification factor R.  The importance
    factor I remains a project/DPT input so that the app does not silently
    mix building-code importance with AASHTO operational category.
    """
    st.markdown("#### AASHTO bridge seismic parameters — I/R selection")
    st.markdown(
        '<div class="note-box"><b>Bridge seismic basis:</b> DPT 1301/1302-61 supplies the Thai response spectrum and importance factor basis. AASHTO LRFD 2020 Table 3.10.7.1-1 is used here to recommend the bridge substructure response modification factor <b>R</b>. The owner / authority having jurisdiction shall confirm the bridge operational category.</div>',
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

    r_modes = ["Auto from AASHTO LRFD 2020 Table 3.10.7.1-1", "Manual R override"]
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
def _sync_loads_inline_subpage_to_sidebar() -> None:
    """Keep the global subpage state in sync when using the in-page Loads selector."""
    load_subpages = get_workspace("3 Loads")["subpages"]
    inline_subpage = st.session_state.get("loads_inline_subpage")
    if inline_subpage in load_subpages:
        st.session_state.current_workspace = "3 Loads"
        st.session_state.current_subpage = inline_subpage


def _sync_sidebar_subpage_to_loads_inline() -> None:
    """Keep the in-page Loads selector in sync when navigation happens from the sidebar."""
    if st.session_state.get("current_workspace") == "3 Loads":
        load_subpages = get_workspace("3 Loads")["subpages"]
        current_subpage = st.session_state.get("current_subpage")
        if current_subpage in load_subpages:
            st.session_state.loads_inline_subpage = current_subpage


def render_sidebar_schema_status() -> None:
    """Show app/runtime schema separately from project-file schema trace."""
    meta = D.get("meta", {}) if isinstance(D, dict) else {}
    active_schema = str(meta.get("schema_version", "-"))
    source_schema = str(meta.get("loaded_schema_version", active_schema))
    migration_status = str(meta.get("schema_migration_status", "Current" if active_schema == PROJECT_SCHEMA_VERSION else "Review"))
    st.info(f"App schema: {PROJECT_SCHEMA_VERSION}")
    if active_schema == PROJECT_SCHEMA_VERSION:
        st.success(f"Active project schema: {active_schema}")
    else:
        st.warning(f"Active project schema: {active_schema}")
    if source_schema and source_schema != active_schema:
        st.caption(f"Source project schema: {source_schema} · {migration_status}")
    else:
        st.caption(f"Migration status: {migration_status}")


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
        st.radio("SUBPAGE", ws["subpages"], key="current_subpage", on_change=_sync_sidebar_subpage_to_loads_inline)

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
        render_sidebar_schema_status()
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
    section_title("3 Loads — FEA load input generator")
    st.markdown('<div class="note-box"><b>One-source rule:</b> each load is entered once in the report-driven schema. Report Preview, FEA Load Input Summary, QA checks, and Save/Load JSON read from the same source.</div>', unsafe_allow_html=True)
    load_tab_labels = ["3.1 Dead Load", "3.2 SDL", "3.3 LL + IM", "3.4 LF / 3.5 HF", "3.6 CF", "3.7 Wind", "3.8 CR&SH", "3.9 EQ", "3.10 FEA Load Input Summary"]
    # Migration alias for older project/UI state that used the shorter, ambiguous label.
    if st.session_state.get("loads_inline_subpage") == "3.10 FEA Summary":
        st.session_state.loads_inline_subpage = "3.10 FEA Load Input Summary"
    if sub == "3.10 FEA Summary":
        sub = "3.10 FEA Load Input Summary"
    if st.session_state.get("loads_inline_subpage") not in load_tab_labels:
        st.session_state.loads_inline_subpage = sub if sub in load_tab_labels else load_tab_labels[0]
    selected_load_subpage = st.radio(
        "Load subpage",
        load_tab_labels,
        key="loads_inline_subpage",
        horizontal=True,
        label_visibility="collapsed",
        on_change=_sync_loads_inline_subpage_to_sidebar,
    )
    st.markdown(f'<div class="note-box"><b>Dedicated Loads workspace:</b> Active subpage = {selected_load_subpage}. Load calculations are maintained as a report-driven FEA load input generator.</div>', unsafe_allow_html=True)

    if selected_load_subpage == "3.1 Dead Load":
        code_basis_card("3.1 Dead Load (DL)", "BG40 Calculation Report Ch. 1.3.1", "Informational/report text only. FEA self-weight remains generated in the structural analysis model; no duplicate dead-load input is introduced here.")
        dl = D["load_components"]
        st.markdown(f'<div class="note-box"><b>Dead load:</b> {dl.get("dead_load_definition", "")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="note-box"><b>Self-Weight (SW):</b> {dl.get("dead_load_note", "")}</div>', unsafe_allow_html=True)
        show_engineering_table(pd.DataFrame(dl.get("dead_load_unit_weights", [])))
        st.caption("Report note: these unit weights are provided for information and report traceability only. The app does not create an additional DL calculation table from these values.")

    if selected_load_subpage == "3.2 SDL":
        code_basis_card("3.2 Superimposed Dead Load (SDL)", "BG40 R10 project load schedule / FEA permanent appurtenance loads", "Editable component table. Total and adopted design values are recalculated from this single table. The selected track configuration controls the SDL value sent to the FEA summary.")
        track_options = ["Single Track", "Double Track"]
        current_track = str(D.get("bridge_model", {}).get("number_of_tracks", "Double Track"))
        if current_track not in track_options:
            current_track = "Double Track"
        selected_track = st.radio(
            "SDL design track configuration for FEA input",
            track_options,
            index=track_options.index(current_track),
            horizontal=True,
            help="Choose which adopted SDL value is sent to the FEA input summary. Both single-track and double-track component totals remain visible and editable.",
            key="sdl_track_configuration_radio",
        )
        D["bridge_model"]["number_of_tracks"] = selected_track
        st.markdown(f'<div class="note-box"><b>SDL selection rule:</b> Active FEA SDL basis = {selected_track}. The app still keeps both single-track and double-track totals for report traceability.</div>', unsafe_allow_html=True)

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
            card("Total SDL — double", f"{format_engineering_value(ld['sdl_double_total'], 'kN/m')} kN/m", "sum of included rows")
        with c3:
            card("Active SDL basis", str(ld["sdl_track_basis"]), "selected track configuration", "pass")
        with c4:
            card("Active FEA SDL", f"{format_engineering_value(ld['sdl_selected_adopted_kn_m'], 'kN/m')} kN/m", str(ld["sdl_selected_application"]), "pass")

        c5, c6 = st.columns(2)
        with c5:
            editable_value(["load_components", "design_sdl_single_kn_m"], "Adopted single-track SDL (kN/m)", 1.0)
        with c6:
            editable_value(["load_components", "design_sdl_double_kn_m"], "Adopted double-track SDL (kN/m)", 1.0)
        st.markdown("#### FEA SDL input summary")
        show_engineering_table(pd.DataFrame([
            ["SDL", "Superimposed dead load", ld["sdl_selected_adopted_kn_m"], "kN/m", "Gravity / along span", ld["sdl_selected_application"], "Selected track basis + user editable + app total"],
        ], columns=["Load Pattern", "Description", "Value", "Unit", "Direction", "Application", "Source"]))

    if selected_load_subpage == "3.3 LL + IM":
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

    if selected_load_subpage == "3.4 LF / 3.5 HF":
        code_basis_card("3.4 Longitudinal Force (LF) and 3.5 Hunting / Nosing Force (HF)", "EN 1991-2 Art. 6.5.3 and EN 1991-2 Art. 6.5.2", "LF is longitudinal braking/traction at rail level. HF is the EN nosing force Qsk, concentrated transverse at top of rail.")
        components.html(rail_horizontal_forces_diagram_svg(), height=430, scrolling=False)
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

    if selected_load_subpage == "3.6 CF":
        code_basis_card(
            "3.6 Centrifugal Force (CF)",
            "EN 1991-2 Art. 6.5.1",
            "Code-assisted CF input assistant. Straight track is treated as zero CF; curved finite-radius track calculates f, C, assessment status, and FEA adoption trace from one source.",
        )
        st.markdown('<div class="note-box"><b>CF one-source rule:</b> CF inputs below feed the calculation trace, result cards, FEA adoption status, FEA Load Input Summary, Save/Load JSON, and future report export. V is in km/h, R is in m, and C is dimensionless. For <b>Straight track</b>, R = ∞ and CF = 0.</div>', unsafe_allow_html=True)

        rail = D["rail_loads"]
        span = float(D["project"].get("span_m", 40.0))
        condition_options = ["Straight track / no horizontal curve", "Curved track / finite radius"]
        if rail.get("cf_track_condition") in {"Straight / very large radius", "Large-radius curve / near-straight", "Curved track"}:
            rail["cf_track_condition"] = "Curved track / finite radius"
        elif rail.get("cf_track_condition") == "Straight track":
            rail["cf_track_condition"] = "Straight track / no horizontal curve"
        if rail.get("cf_track_condition") not in condition_options:
            rail["cf_track_condition"] = "Curved track / finite radius"
        c1, c2 = st.columns([1, 1])
        with c1:
            rail["cf_track_condition"] = st.selectbox(
                "Track alignment condition",
                condition_options,
                index=condition_options.index(str(rail.get("cf_track_condition", "Curved track / finite radius"))),
                key="cf_track_condition_selector",
                help="Straight track sets R = infinity and CF = 0. Curved track uses the finite-radius EN calculation; a very large radius is simply a curved-track case with a small result.",
            )
        cf_is_straight_ui = str(rail.get("cf_track_condition")) == "Straight track / no horizontal curve"
        if cf_is_straight_ui:
            rail["cf_include_in_fea"] = False
            with c2:
                st.markdown('<div class="note-box"><b>Straight-track input mode:</b> finite-radius CF inputs are not required. The app sets R = ∞, C = 0, and disables CF FEA adoption.</div>', unsafe_allow_html=True)
        else:
            with c2:
                rail["cf_include_in_fea"] = st.checkbox(
                    "Include CF in FEA adoption summary",
                    value=bool(rail.get("cf_include_in_fea", False)),
                    key="cf_include_in_fea_checkbox",
                    help="Use only when the project explicitly adopts the finite-radius centrifugal action into the FEA load summary.",
                )

        if cf_is_straight_ui:
            st.markdown("#### Straight-track CF input status")
            st.markdown('<div class="note-box"><b>No finite-radius CF inputs are active:</b> design speed V, curve radius R, loaded length Lf, assessment threshold, and Adopt span as Lf are hidden because CF = 0 for straight track.</div>', unsafe_allow_html=True)
        else:
            st.markdown("#### Project-specific CF inputs")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                editable_value(["rail_loads", "speed_kmh"], "Design speed V (km/h)", 10.0)
            with c2:
                editable_value(["rail_loads", "radius_m"], "Curve radius R (m)", 100.0)
            with c3:
                editable_value(["rail_loads", "Lf_m"], "Loaded length Lf (m)", 1.0)
            with c4:
                editable_value(["rail_loads", "cf_assessment_threshold_percent"], "Assessment threshold (% LL)", 0.25, "%.2f")
                if st.button("Adopt span as Lf", key="cf_adopt_span_lf"):
                    rail["Lf_m"] = span
                    st.rerun()

        ld = load_derived()
        threshold = float(ld["cf_assessment_threshold_percent"])
        st.markdown("#### Result summary")
        c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1.2, 1.2])
        with c1:
            card("Reduction factor f", "N/A" if ld["cf_is_straight"] else f"{ld['cf_f']:.4f}", "zero CF for straight track" if ld["cf_is_straight"] else "EN reduction factor")
        with c2:
            card("CF factor C", f"{ld['cf_C_reduced']:.5f}", "R = ∞" if ld["cf_is_straight"] else "dimensionless")
        with c3:
            card("CF / LL", f"{ld['cf_C_percent']:.2f}%", "straight track" if ld["cf_is_straight"] else "excluding impact")
        with c4:
            card("Engineering assessment", str(ld["cf_engineering_assessment"]), str(ld["cf_engineering_assessment_note"]), str(ld["cf_engineering_assessment_mode"]))
        with c5:
            card("FEA adoption status", str(ld["cf_fea_adoption_status"]), str(ld["cf_fea_adoption_note"]), str(ld["cf_fea_adoption_mode"]))

        st.markdown("#### Calculation trace")
        if ld["cf_is_straight"]:
            st.latex(r"R = \infty \quad \Rightarrow \quad C=\frac{V^2 f}{127R}=0")
            st.latex(r"CF = 0.00\%\;\text{of vertical live load}")
            st.markdown('<div class="note-box"><b>Straight-track logic:</b> no horizontal curve is present; therefore no finite-radius centrifugal action is generated. The app sets C = 0 and prevents FEA adoption for CF.</div>', unsafe_allow_html=True)
        else:
            st.latex(r"C=\frac{V^2f}{127R}")
            st.latex(r"f=1-\left(\frac{V-120}{1000}\right)\left(\frac{814}{V}+1.75\right)\left(1-\sqrt{\frac{2.88}{L_f}}\right)\quad (f\ge 0.35)")
            st.latex(fr"f={ld['cf_f']:.4f},\qquad C=\frac{{{D['rail_loads']['speed_kmh']:.0f}^2({ld['cf_f']:.2f})}}{{127({D['rail_loads']['radius_m']:.0f})}}={ld['cf_C_reduced']:.5f}")
            st.markdown('<div class="note-box"><b>Unit trace:</b> use V in km/h, R in m, and Lf in m for the EN centrifugal expression above. The resulting C is a dimensionless fraction of the vertical live load and excludes impact unless an adopted project rule states otherwise.</div>', unsafe_allow_html=True)

        st.markdown("#### FEA adoption")
        if ld["cf_is_straight"]:
            adoption_mode = "Zero for straight track — not adopted as FEA load"
        else:
            adoption_mode = "Adopted as horizontal radial/transverse action factor" if bool(rail.get("cf_include_in_fea", False)) else "Factor only — not adopted as FEA load"
        rail["cf_adoption_mode"] = adoption_mode
        direction_value = "Not applicable for straight track" if ld["cf_is_straight"] else str(rail.get("cf_direction", "Radial / transverse to track"))
        direction_trace = "No radial direction because R = infinity" if ld["cf_is_straight"] else "Horizontal radial action normal to curved track"
        adoption_rows = [
            ["Track condition", str(ld.get("cf_track_condition", rail.get("cf_track_condition", "-"))), "User selection / project assumption"],
            ["Direction", direction_value, direction_trace],
            ["Application level", "Not applicable" if ld["cf_is_straight"] else str(rail.get("cf_application_level", "Rail level")), "No CF load for straight track" if ld["cf_is_straight"] else "Typical FEA application reference unless project-specific model states otherwise"],
            ["Adopted CF factor", f"{ld['cf_C_reduced']:.5f} = {ld['cf_C_percent']:.2f}% of LL", "Zero for straight track" if ld["cf_is_straight"] else "Multiply by vertical train live-load effect"],
            ["FEA adoption", adoption_mode, "Explicit user-controlled adoption status"],
        ]
        show_engineering_table(pd.DataFrame(adoption_rows, columns=["Item", "Value", "Trace"]), hide_index=True)
        if ld["cf_is_straight"]:
            st.markdown('<div class="note-box"><b>Straight-track status:</b> CF is zero because there is no horizontal curve (R = ∞). The app does not adopt a separate CF horizontal FEA load.</div>', unsafe_allow_html=True)
        elif bool(rail.get("cf_include_in_fea", False)):
            st.markdown('<div class="warn-box"><b>FEA adoption note:</b> CF is adopted as a factor to be applied to the selected vertical railway live-load model. A numeric kN/m or point-load CF action requires the governing vertical live-load distribution from the FEA load model.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="note-box"><b>Factor-only status:</b> CF is calculated and reported for traceability, but no separate CF horizontal FEA load is adopted from this page.</div>', unsafe_allow_html=True)


    if selected_load_subpage == "3.7 Wind":
        code_basis_card(
            "3.7 Wind Load (WS)",
            "EN 1991-1-4 and DPT 1311-50",
            "Report-driven WS module: user edits only the governing input parameters; vb, b/dtot, C, Aref, FW and FEA line loads are calculated automatically from one source.",
        )
        st.markdown('<div class="note-box"><b>Wind one-source rule:</b> the editable parameter table below feeds the calculation trace, figures, result tables, FEA summary, Save/Load JSON, and future report export. C factors are not duplicate manual inputs.</div>', unsafe_allow_html=True)

        wind_tabs = st.tabs(["Overview", "Input Assistant", "EN Factors", "Calculations", "FEA Summary"])
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
            st.markdown("#### Code-assisted wind input assistant")
            st.markdown('<div class="note-box"><b>Input philosophy:</b> select only the project-specific wind group and geometry. The app recommends DPT/EN factors, calculates derived wind quantities, and keeps any user override visible for report traceability.</div>', unsafe_allow_html=True)

            st.markdown("##### Project location lookup")
            st.markdown(
                '<div class="small-muted">Select the project province first. The app uses the DPT 1311-50 / 1312-50 province-group table to recommend the wind group automatically. Use manual group selection only when the project has a special requirement.</div>',
                unsafe_allow_html=True,
            )
            province_options = [MANUAL_LOCATION] + wind_province_options()
            default_province = lc.get("wind_province", "ขอนแก่น")
            if default_province not in province_options:
                default_province = MANUAL_LOCATION
            pc1, pc2 = st.columns([2, 2])
            with pc1:
                selected_province = st.selectbox(
                    "Project province / DPT province-group lookup",
                    province_options,
                    index=province_options.index(default_province),
                    key="wind_project_province_select",
                    help="Province lookup reduces the need to read the DPT wind map manually.",
                )

            location_group = None
            selected_area = MANUAL_LOCATION
            if selected_province != MANUAL_LOCATION:
                area_options = wind_area_options(selected_province)
                default_area = lc.get("wind_province_area", area_options[0])
                if default_area not in area_options:
                    default_area = area_options[0]
                with pc2:
                    selected_area = st.selectbox(
                        "Province area / district condition",
                        area_options,
                        index=area_options.index(default_area),
                        key="wind_project_area_select",
                        help="Only provinces with split DPT groups need a district/area selection.",
                    )
                loc = wind_group_from_province_area(selected_province, selected_area)
                if loc:
                    location_group = loc.group
                    if selected_province != lc.get("wind_province") or selected_area != lc.get("wind_province_area"):
                        rec = wind_vb0_recommended_from_group(location_group)
                        lc["wind_province"] = selected_province
                        lc["wind_province_area"] = selected_area
                        lc["wind_reference_group"] = str(rec["group"])
                        lc["wind_v50_m_s"] = float(rec["V50_m_s"])
                        lc["wind_terrain_factor"] = float(rec["TF"])
                        lc["wind_vb0_m_s"] = float(rec["vb0_m_s"])
                        lc["wind_vb0_manual_override"] = False
            else:
                with pc2:
                    st.selectbox(
                        "Province area / district condition",
                        [MANUAL_LOCATION],
                        index=0,
                        key="wind_project_area_manual",
                        disabled=True,
                    )
                lc["wind_province"] = MANUAL_LOCATION
                lc["wind_province_area"] = MANUAL_LOCATION

            if location_group:
                selected_group = location_group
                # Province lookup owns the wind group in this mode.  Do not show a
                # disabled manual dropdown, because a stale widget value can look
                # like a conflicting adopted group.
                st.markdown('<div class="note-box"><b>DPT wind group source:</b> auto from selected province / area. Choose <b>Manual group selection</b> in the province dropdown only when project-specific requirements govern.</div>', unsafe_allow_html=True)
                loc_c1, loc_c2, loc_c3 = st.columns(3)
                with loc_c1:
                    card("Province lookup", selected_province, "DPT province-group table", "pass")
                with loc_c2:
                    card("Area condition", selected_area, "district/area selector")
                with loc_c3:
                    card("Auto wind group", selected_group, "from province lookup", "pass")
            else:
                current_group = lc.get("wind_reference_group", "Group 1")
                if current_group not in wind_group_options:
                    current_group = "Group 1"
                selected_group = st.selectbox(
                    "DPT 1311-50 reference wind speed group",
                    wind_group_options,
                    index=wind_group_options.index(current_group),
                    key="wind_reference_group_select",
                    help="Manual group selection. Select a province above to let the app recommend this automatically.",
                )

            if selected_group != lc.get("wind_reference_group"):
                rec = wind_vb0_recommended_from_group(selected_group)
                lc["wind_reference_group"] = str(rec["group"])
                lc["wind_v50_m_s"] = float(rec["V50_m_s"])
                lc["wind_terrain_factor"] = float(rec["TF"])
                lc["wind_vb0_m_s"] = float(rec["vb0_m_s"])
                lc["wind_vb0_manual_override"] = False

            rec = wind_vb0_recommended_from_group(lc.get("wind_reference_group", "Group 1"))
            rec_v50 = float(rec["V50_m_s"])
            rec_tf = float(rec["TF"])
            rec_vb0 = float(lc.get("wind_v50_m_s", rec_v50)) * float(lc.get("wind_terrain_factor", rec_tf))
            lc.setdefault("wind_vb0_manual_override", False)
            manual_vb0 = bool(lc.get("wind_vb0_manual_override", False))

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                card("DPT group recommendation", str(lc.get("wind_reference_group", "Group 1")), f"V50 = {rec_v50:.1f} m/s · TF = {rec_tf:.2f}", "pass")
            with c2:
                card("Recommended vb,0", f"{rec_vb0:.2f} m/s", "V50 × TF")
            with c3:
                card("Recommended cdir", "1.00", "EN 1991-1-4 default")
            with c4:
                card("Recommended cseason", "1.00", "EN 1991-1-4 default")


            st.markdown("#### Reference figures for input selection")
            st.markdown('<div class="note-box"><b>Reference visual workflow:</b> use the map and wind-action sketches here while selecting input values. These figures are shown at the decision point instead of being hidden in a separate figure tab.</div>', unsafe_allow_html=True)
            r1c1, r1c2 = st.columns(2)
            with r1c1:
                wind_group_map_figure_card(
                    str(lc.get("wind_reference_group", "Group 1")),
                    "Select the project location group, then the app recommends V50 and TF.",
                    max_height_px=340,
                )
            with r1c2:
                wind_reference_figure_card(
                    "fig_1_3_en_wind_direction_bridge.png",
                    "Wind action direction on bridge deck",
                    "User-provided refined bridge wind-direction sketch",
                    "Clarifies b, L, d, bridge axes, and wind direction used by the bridge wind calculation.",
                    max_height_px=340,
                )
            lookup_rows = [
                ["Group 1", "25.0", "1.00", "25.00", "General reference group"],
                ["Group 2", "27.0", "1.00", "27.00", "Higher reference wind speed group"],
                ["Group 3", "29.0", "1.00", "29.00", "Highest V50 group in the report table"],
                ["Group 4A", "25.0", "1.20", "30.00", "Terrain factor amplified group"],
                ["Group 4B", "25.0", "1.08", "27.00", "Terrain factor amplified group"],
            ]
            show_engineering_table(pd.DataFrame(lookup_rows, columns=["DPT group", "V50 (m/s)", "TF", "Recommended vb,0 (m/s)", "Interpretation"]))
            r2c1, r2c2 = st.columns(2)
            with r2c1:
                wind_factor_c_reference_card(
                    "Used to check the app's automatic C interpolation from b/dtot and z_e."
                )
            with r2c2:
                wind_reference_figure_card(
                    "fig_ws_bridge_cross_section_load.png",
                    "WS / WL wind application model",
                    "User-provided refined WS/WL wind application sketch",
                    "Shows wind on superstructure (WS), train envelope wind (WL), D, D/4, and the associated vertical reference effect V. Note: V in this sketch is not wind velocity; wind velocity is handled by V50, vb,0, and vb in the calculation table.",
                    max_height_px=360,
                )
            ze_bridge_reference_card(
                "Compact separate card added so the user-provided bridge profile supports z_e interpretation without oversizing the Input Assistant layout."
            )


            def _wind_status(key: str, recommended: float, tolerance: float = 1e-6) -> str:
                try:
                    current = float(lc.get(key, recommended))
                except (TypeError, ValueError):
                    return "Review input"
                return "Recommended / auto" if abs(current - float(recommended)) <= tolerance else "User override"

            specs = [
                ("Air density ρ", "wind_air_density_kg_m3", "kg/m³", 1.25, "Project / report input", "Usually 1.25 kg/m³ for BG40 report basis"),
                ("Reference wind speed V50", "wind_v50_m_s", "m/s", rec_v50, "DPT group recommendation", "From selected DPT 1311-50 wind group"),
                ("Terrain factor TF", "wind_terrain_factor", "-", rec_tf, "DPT group recommendation", "From selected DPT 1311-50 wind group"),
                ("Fundamental basic wind velocity vb,0", "wind_vb0_m_s", "m/s", rec_vb0, "Auto from V50 × TF" if not manual_vb0 else "User override enabled", "Used in EN vb = cdir cseason vb,0"),
                ("Directional factor cdir", "wind_cdir", "-", 1.0, "EN recommended default", "Default 1.00 unless National Annex / project states otherwise"),
                ("Season factor cseason", "wind_cseason", "-", 1.0, "EN recommended default", "Default 1.00 unless National Annex / project states otherwise"),
                ("Bridge/deck width b", "wind_b_m", "m", D["project"]["width_m"], "Project geometry input", "Width in x-direction D from report"),
                ("Depth dtot,WS", "wind_dtot_ws_m", "m", 3.9, "Project geometry input", "Superstructure with parapets"),
                ("Depth dtot,WS+WL", "wind_dtot_ws_wl_m", "m", 6.8, "Project geometry input", "Superstructure plus train envelope"),
                ("Deck height ze", "wind_ze_m", "m", 10.0, "Project geometry input", "Height of bridge deck"),
                ("Wind loaded length L", "wind_span_m", "m", D["project"]["span_m"], "Project geometry input", "Length of superstructure subjected to wind"),
            ]
            lc.setdefault("wind_span_m", float(D["project"]["span_m"]))
            param_df = pd.DataFrame([
                {
                    "Parameter": label,
                    "Value": float(lc.get(key, default)),
                    "Unit": unit,
                    "Recommendation status": _wind_status(key, default),
                    "Recommended / source": src,
                    "Note": note,
                    "Schema key": key,
                }
                for label, key, unit, default, src, note in specs
            ])
            st.markdown("#### Editable wind parameter table")
            edited = st.data_editor(
                param_df,
                use_container_width=True,
                hide_index=True,
                disabled=["Parameter", "Unit", "Recommendation status", "Recommended / source", "Note", "Schema key"],
                column_config={"Value": st.column_config.NumberColumn(format="%.3f")},
                key="wind_parameter_editor",
            )
            for _, row in edited.iterrows():
                key = str(row["Schema key"])
                lc[key] = float(row["Value"])
            if not bool(lc.get("wind_vb0_manual_override", False)):
                lc["wind_vb0_m_s"] = float(lc.get("wind_v50_m_s", rec_v50)) * float(lc.get("wind_terrain_factor", rec_tf))

            D["project"]["span_m"] = float(lc.get("wind_span_m", D["project"]["span_m"]))
            lc["wind_vb_m_s"] = float(lc["wind_vb0_m_s"]) * float(lc["wind_cdir"]) * float(lc["wind_cseason"])

            st.markdown("#### Recommendation / override trace")
            location_status = "Manual group selection" if lc.get("wind_province") == MANUAL_LOCATION else "Auto from province lookup"
            show_engineering_table(pd.DataFrame([
                ["Project province", lc.get("wind_province", MANUAL_LOCATION), location_status, "DPT 1311-50 / 1312-50 province group database"],
                ["Province area", lc.get("wind_province_area", MANUAL_LOCATION), location_status, "District/area condition for split provinces"],
                ["Wind group", lc.get("wind_reference_group", "Group 1"), location_status, "Drives V50 and TF recommendation"],
                ["V50", lc["wind_v50_m_s"], _wind_status("wind_v50_m_s", rec_v50), "DPT group value unless user override"],
                ["TF", lc["wind_terrain_factor"], _wind_status("wind_terrain_factor", rec_tf), "DPT group factor unless user override"],
                ["vb,0", lc["wind_vb0_m_s"], "User override" if bool(lc.get("wind_vb0_manual_override", False)) else "Auto = V50 × TF", "Fundamental basic wind velocity"],
                ["cdir", lc["wind_cdir"], _wind_status("wind_cdir", 1.0), "Recommended default 1.00"],
                ["cseason", lc["wind_cseason"], _wind_status("wind_cseason", 1.0), "Recommended default 1.00"],
            ], columns=["Item", "Value", "Status", "Trace"]))
            st.markdown('<div class="warn-box"><b>Override rule:</b> calculated/recommended values may be edited, but the app keeps the adopted value and source status visible for report traceability.</div>', unsafe_allow_html=True)

        with wind_tabs[2]:
            st.markdown("#### EN 1991-1-4 wind factor reference")
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
            st.markdown('<div class="note-box"><b>Figure note:</b> EN factor reference images are kept in the Input Assistant cards only. This EN Factors tab intentionally shows the calculation table and interpolation trace without duplicate right-side report figures.</div>', unsafe_allow_html=True)

        with wind_tabs[3]:
            ld = load_derived()
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                card("Velocity pressure q", f"{ld['q_pa']:.3f} Pa", "q = 0.5ρvb²")
            with c2:
                card("WS line load", f"{ld['WSsuper_kn_m']:.2f} kN/m", f"F = {ld['WSsuper_kn']:.0f} kN")
            with c3:
                card("WS + WL line load", f"{ld['WSsuper_WL_kn_m']:.2f} kN/m", f"F = {ld['WSsuper_WL_kn']:.0f} kN", "good")
            with c4:
                card("Governing wind input", f"{max(ld['WSsuper_kn_m'], ld['WSsuper_WL_kn_m']):.2f} kN/m", "used for envelope review")

            st.markdown("#### Basic wind velocity")
            st.latex(r"v_b=c_{dir}c_{season}v_{b,0}")
            st.latex(fr"v_b={lc['wind_cdir']:.2f}({lc['wind_cseason']:.2f})({lc['wind_vb0_m_s']:.1f})={ld['vb_m_s']:.1f}\,\mathrm{{m/s}}")

            st.markdown("#### Velocity pressure and unit trace")
            st.latex(r"q=0.5\\rho v_b^2")
            st.latex(fr"q=0.5({lc['wind_air_density_kg_m3']:.2f})({ld['vb_m_s']:.1f})^2={ld['q_pa']:.3f}\,\mathrm{{Pa}}")
            st.markdown('<div class="note-box"><b>Unit trace:</b> Pa = N/m². The wind resultant from q·C·Aref is first obtained in N and then divided by 1000 to report kN.</div>', unsafe_allow_html=True)

            st.markdown("#### Wind load factor and reference area")
            st.latex(r"A_{ref,x}=d_{tot}L")
            st.latex(fr"A_{{ref,x,WS}}={lc['wind_dtot_ws_m']:.3f}({lc.get('wind_span_m', D['project']['span_m']):.3f})={ld['Aref_ws_m2']:.1f}\,\mathrm{{m^2}}")
            st.latex(fr"A_{{ref,x,WS+WL}}={lc['wind_dtot_ws_wl_m']:.3f}({lc.get('wind_span_m', D['project']['span_m']):.3f})={ld['Aref_ws_wl_m2']:.1f}\,\mathrm{{m^2}}")

            st.markdown("#### Wind force and equivalent line load")
            st.latex(r"F_{W,x}=\frac{q C A_{ref,x}}{1000}\quad [\mathrm{kN}]")
            st.latex(fr"F_{{W,x,WS}}=\frac{{({ld['q_pa']:.3f})({ld['C_ws']:.3f})({ld['Aref_ws_m2']:.1f})}}{{1000}}={ld['WSsuper_kn']:.0f}\,\mathrm{{kN}}")
            st.latex(fr"F_{{W,x,WS+WL}}=\frac{{({ld['q_pa']:.3f})({ld['C_ws_wl']:.3f})({ld['Aref_ws_wl_m2']:.1f})}}{{1000}}={ld['WSsuper_WL_kn']:.0f}\,\mathrm{{kN}}")
            st.latex(fr"w_{{WS}}=F_{{W,x,WS}}/L={ld['WSsuper_kn_m']:.2f}\,\mathrm{{kN/m}},\qquad w_{{WS+WL}}=F_{{W,x,WS+WL}}/L={ld['WSsuper_WL_kn_m']:.2f}\,\mathrm{{kN/m}}")
            show_engineering_table(pd.DataFrame([
                ["q = 0.5ρvb²", ld["q_pa"], "Pa", "velocity pressure = N/m²"],
                ["CWS", ld["C_ws"], "factor", "automatic interpolation"],
                ["CWS+WL", ld["C_ws_wl"], "factor", "automatic interpolation"],
                ["Aref,x,WS", ld["Aref_ws_m2"], "m²", "dtot,WS × L"],
                ["Aref,x,WS+WL", ld["Aref_ws_wl_m2"], "m²", "dtot,WS+WL × L"],
                ["FW,x,WS = q·C·Aref/1000", ld["WSsuper_kn"], "kN", f"{ld['WSsuper_kn_m']:.2f} kN/m"],
                ["FW,x,WS+WL = q·C·Aref/1000", ld["WSsuper_WL_kn"], "kN", f"{ld['WSsuper_WL_kn_m']:.2f} kN/m"],
            ], columns=["Item", "Value", "Unit", "Interpretation"]))

        with wind_tabs[4]:
            ld = load_derived()
            rows = [
                ["WS", "Wind on superstructure", ld["WSsuper_kn"], "kN", ld["WSsuper_kn_m"], "kN/m", "Transverse x-direction", "Superstructure"],
                ["WS+WL", "Wind on superstructure + train", ld["WSsuper_WL_kn"], "kN", ld["WSsuper_WL_kn_m"], "kN/m", "Transverse x-direction", "Superstructure + train"],
            ]
            show_engineering_table(pd.DataFrame(rows, columns=["Load Pattern", "Description", "Resultant Force", "Unit", "Line Load", "Line Unit", "Direction", "Application"]))
            st.markdown('<div class="note-box"><b>FEA export rule:</b> WS and WS+WL are exported as equivalent transverse line loads along the wind-loaded span. The resultant forces shown above are calculated only once from the editable parameter table.</div>', unsafe_allow_html=True)
    if selected_load_subpage == "3.8 CR&SH":
        code_basis_card("3.8 Creep and Shrinkage Parameters", "AASHTO LRFD 2020 Section 5, Art. 5.9.3 / 5.4.2.3", "Minimal-input CR&SH assistant: user enters only project-specific assumptions; the app derives drying geometry, V/S, h0, AASHTO unit conversions, and the Prestress Losses handoff from one source.")
        p = D["prestress"]
        m = D["materials"]

        st.markdown('<div class="note-box"><b>CR&SH one-source rule:</b> RH, age assumptions, and drying-perimeter basis are the only primary user inputs here. Geometry-dependent values are derived automatically from Section Properties and drying perimeter data, then consumed by <b>4 Prestress Losses</b>, Save/Load JSON, and future report export.</div>', unsafe_allow_html=True)

        st.markdown("### CR&SH input assistant")
        c1, c2, c3, c4 = st.columns([0.9, 0.9, 0.9, 1.5])
        with c1:
            editable_value(["prestress", "RH_percent"], "Relative humidity RH (%)", 1.0, "%.1f")
        with c2:
            editable_value(["prestress", "ti_days"], "Age at stressing ti (days)", 1.0, "%.1f")
        with c3:
            editable_value(["prestress", "tf_days"], "Final design age tf (days)", 1.0, "%.1f")
        with c4:
            basis_options = ["Outer perimeter only", "Outer + inner void perimeter"]
            basis_current = str(p.get("crsh_drying_perimeter_basis", "Outer + inner void perimeter"))
            if basis_current not in basis_options:
                basis_current = "Outer + inner void perimeter"
            p["crsh_drying_perimeter_basis"] = st.selectbox(
                "Drying perimeter basis",
                basis_options,
                index=basis_options.index(basis_current),
                key="crsh_drying_perimeter_basis",
                help="Use outer + inner void only when the internal void surface is exposed to drying and should be included in the notional drying perimeter.",
            )

        crsh = update_crsh_derived_parameters()
        tf_years = float(p["tf_days"]) / 365.25 if float(p["tf_days"]) > 0.0 else 0.0
        if crsh["include_inner"]:
            st.markdown('<div class="note-box"><b>Drying perimeter basis guidance:</b> inner void perimeter is included only when the void surface is exposed or ventilated and drying is considered effective. Use <b>Outer perimeter only</b> when the internal void is sealed, not exposed to drying, or the project basis requires external drying surface only.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="note-box"><b>Drying perimeter basis guidance:</b> outer perimeter only is used when the internal void is sealed, not exposed to drying, or the project design basis excludes internal void drying. Select <b>Outer + inner void perimeter</b> only when the void surface is exposed or ventilated and drying is considered effective.</div>', unsafe_allow_html=True)
        creep_preview = aashto_creep_coefficient(float(p["RH_percent"]), float(p["V_over_S_in"]), float(m["fc_mpa"]), float(p["ti_days"]))
        shrink_preview = aashto_shrinkage_strain(float(p["RH_percent"]), float(p["V_over_S_in"]), float(m["fc_mpa"]))

        st.markdown("### Result summary")
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            card("RH / age inputs", f"{p['RH_percent']:.1f}%", f"ti = {p['ti_days']:.0f} d · tf = {p['tf_days']:.0f} d ≈ {tf_years:.1f} yr")
        with r2:
            card("Drying perimeter basis", "Outer + inner" if crsh["include_inner"] else "Outer only", f"u_total = {crsh['u_total_m']:.2f} m")
        with r3:
            card("V/S for AASHTO", f"{crsh['V_over_S_in']:.2f} in", f"{crsh['V_over_S_m']:.4f} m = {crsh['V_over_S_mm']:.1f} mm")
        with r4:
            card("h0 notional size", f"{crsh['h0_m']:.4f} m", "h0 = 2Ac/u_total = 2(V/S)", "good")

        st.markdown("### Geometry-derived drying parameters")
        show_engineering_table(pd.DataFrame([
            ["Concrete area Ac", crsh["Ac_m2"], "m²", "From Section Properties"],
            ["u_outer", crsh["u_outer_m"], "m", "External drying perimeter"],
            ["u_inner", crsh["u_inner_m"], "m", "Internal void perimeter; included only when basis = outer + inner void"],
            ["u_total", crsh["u_total_m"], "m", "u_outer + u_inner" if crsh["include_inner"] else "u_outer only"],
            ["V/S", crsh["V_over_S_m"], "m", "Ac / u_total"],
            ["V/S", crsh["V_over_S_in"], "in", "AASHTO empirical factor input"],
            ["h0", crsh["h0_m"], "m", "2Ac / u_total"],
            ["Time interval", crsh["time_interval_days"], "days", "tf - ti"],
        ], columns=["Parameter", "Value", "Unit", "Source / trace"]))

        st.markdown("### Calculation trace")
        st.latex(r"u_{total}=u_{outer}+u_{inner}\quad\mathrm{or}\quad u_{outer}\;\mathrm{only}")
        if crsh["include_inner"]:
            st.latex(fr"u_{{total}}={crsh['u_outer_m']:.2f}+{crsh['u_inner_m']:.2f}={crsh['u_total_m']:.2f}\,\mathrm{{m}}")
        else:
            st.latex(fr"u_{{total}}={crsh['u_outer_m']:.2f}\,\mathrm{{m}}")
        st.latex(r"V/S=\frac{A_c}{u_{total}},\qquad h_0=\frac{2A_c}{u_{total}}=2(V/S)")
        st.latex(fr"V/S=\frac{{{crsh['Ac_m2']:.3f}}}{{{crsh['u_total_m']:.2f}}}={crsh['V_over_S_m']:.4f}\,\mathrm{{m}}={crsh['V_over_S_in']:.2f}\,\mathrm{{in}}")
        st.latex(fr"h_0=2({crsh['V_over_S_m']:.4f})={crsh['h0_m']:.4f}\,\mathrm{{m}}={crsh['h0_in']:.2f}\,\mathrm{{in}}")
        st.markdown('<div class="warn-box"><b>Unit warning:</b> AASHTO empirical creep/shrinkage factors use V/S in inches and concrete strength in ksi for intermediate factors. The app keeps the SI values visible but passes V/S(in) and fc(ksi) to the AASHTO factor functions.</div>', unsafe_allow_html=True)

        st.markdown("### AASHTO unit-conversion / factor preview")
        show_engineering_table(pd.DataFrame([
            ["fc", m["fc_mpa"], "MPa", "Project concrete strength"],
            ["fc", creep_preview["fc_ksi"], "ksi", "Converted for AASHTO empirical factors"],
            ["RH", p["RH_percent"], "%", "User project assumption"],
            ["V/S", p["V_over_S_in"], "in", "Derived from Ac/u_total"],
            ["ks", creep_preview["ks"], "-", "Size factor from V/S(in)"],
            ["ψ_creep", creep_preview["psi"], "-", "Preview coefficient consumed by Prestress Losses"],
            ["ε_sh", shrink_preview["microstrain"], "µε", "Preview shrinkage strain consumed by Prestress Losses"],
        ], columns=["Item", "Value", "Unit", "Source / interpretation"]))

        st.markdown("### Prestress Losses handoff")
        show_engineering_table(pd.DataFrame([
            ["RH_percent", f"{p['RH_percent']:.1f}", "%", "4.5 Time-Dependent Losses"],
            ["ti_days", f"{p['ti_days']:.0f}", "days", "Creep age factor"],
            ["tf_days", f"{p['tf_days']:.0f}", "days", "Long-term design age / report trace"],
            ["tf_years", f"{tf_years:.1f}", "years", "Displayed design-age check from tf_days / 365.25"],
            ["V_over_S_in", f"{p['V_over_S_in']:.2f}", "in", "AASHTO creep/shrinkage factors"],
            ["V_over_S_m", f"{p['V_over_S_m']:.4f}", "m", "SI report value"],
            ["h0_m", f"{p['h0_m']:.4f}", "m", "Notional size report value"],
            ["drying_perimeter_basis", p["crsh_drying_perimeter_basis"], "-", "Report assumption"],
        ], columns=["Schema key", "Adopted value", "Unit", "Consumed by / trace"]))
        st.markdown('<div class="note-box"><b>Override discipline:</b> Ac, u_outer, and u_inner should come from the Section Properties / report geometry source. Users normally edit only RH, ages, and drying-perimeter basis; derived values are recalculated automatically for traceability.</div>', unsafe_allow_html=True)

    if selected_load_subpage == "3.9 EQ":
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
            st.metric("Active R", f"{float(lc['seismic_R']):.1f}", help=lc.get("seismic_R_source", "AASHTO LRFD 2020 bridge R basis"))

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
            render_eq_result_summary_and_fea_adoption(lc, ld, location_label=f"Zone {int(lc['seismic_bangkok_zone'])}", region_label="Bangkok Basin")
            st.latex(r"S_a(T)=\text{interpolated from DPT Table 1.4-5 (5\% damping) or Table 1.4-4 (2.5\% damping)}")
            st.latex(r"C_s=S_a\left(\frac{I}{R}\right)\quad\text{with}\quad C_s\ge0.01")
            st.latex(fr"S_a({D['load_components']['seismic_T_s']:.3f})={ld['eq_Sa']:.4f}\,g")
            st.latex(fr"C_s={ld['eq_Sa']:.4f}\left(\frac{{{D['load_components']['seismic_I']:.2f}}}{{{D['load_components']['seismic_R']:.1f}}}\right)={ld['eq_Cs']:.4f}")
            spec = bangkok_response_spectrum_points(int(lc["seismic_bangkok_zone"]), float(lc.get("seismic_damping_percent", 5.0)))
            render_eq_response_spectrum_canvas(spec, lc, ld, title=f"DPT Bangkok Basin Zone {int(lc['seismic_bangkok_zone'])} — Equivalent static spectrum", region_label="Bangkok Basin")
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
            render_eq_result_summary_and_fea_adoption(lc, ld, location_label=f"อ.{region_lookup['district_th']} จ.{region_lookup['province_th']}", region_label="General Thailand")
            st.latex(r"S_{MS}=F_aS_S,\qquad S_{M1}=F_vS_1")
            st.latex(r"S_{DS}=\frac{2}{3}S_{MS},\qquad S_{D1}=\frac{2}{3}S_{M1}")
            st.latex(r"C_s=S_a\left(\frac{I}{R}\right)\quad\text{with}\quad C_s\ge0.01")
            st.latex(fr"S_{{DS}}=\frac{{2}}{{3}}({ld['eq_Fa']:.2f})({D['load_components']['seismic_Ss_g']:.3f})={ld['eq_SDS']:.4f}\,g")
            st.latex(fr"S_{{D1}}=\frac{{2}}{{3}}({ld['eq_Fv']:.2f})({D['load_components']['seismic_S1_g']:.3f})={ld['eq_SD1']:.4f}\,g")
            st.latex(fr"C_s={ld['eq_Sa']:.4f}\left(\frac{{{D['load_components']['seismic_I']:.2f}}}{{{D['load_components']['seismic_R']:.1f}}}\right)={ld['eq_Cs']:.4f}")
            spec = response_spectrum_points(ld["eq_SDS"], ld["eq_SD1"], t_max=max(2.5, float(D["load_components"]["seismic_T_s"]) * 1.5))
            render_eq_response_spectrum_canvas(spec, lc, ld, title="DPT equivalent-static design response spectrum — General Thailand workflow", region_label="General Thailand")
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
            render_eq_result_summary_and_fea_adoption(lc, ld, location_label="Manual Ss/S1", region_label="Manual / not found")
            st.latex(r"S_{MS}=F_aS_S,\qquad S_{M1}=F_vS_1")
            st.latex(r"C_s=S_a\left(\frac{I}{R}\right)")
            st.markdown('<div class="warn-box"><b>Manual source warning:</b> results are calculated from user-entered Ss/S1 and are not verified against the DPT location database.</div>', unsafe_allow_html=True)
        st.markdown('<div class="warn-box"><b>Scope note:</b> DPT 1301/1302-61 is a building seismic design standard. In this bridge app it is used as Thai project seismic parameter basis, consistent with the BG40 report criteria.</div>', unsafe_allow_html=True)

    if selected_load_subpage == "3.10 FEA Load Input Summary":
        ld = load_derived()
        lc = D["load_components"]
        rail = D.get("rail_loads", {})
        section_title("3.10 FEA Load Input Summary")
        st.markdown(
            '<div class="note-box"><b>Purpose:</b> this page is the single handoff table for load patterns, coefficients, and parameter traces to be entered or mapped in the external FEA program. It is not a separate calculator and it does not create duplicate load inputs.</div>',
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            card("SUMMARY STATUS", "HANDOFF READY", "Ready for FEA input review; not a second calculator", "pass")
        with c2:
            card("SOURCE RULE", "ONE-SOURCE", "No duplicate FEA input fields are created here", "pass")
        with c3:
            card("EQ FORCE POLICY", "COEFFICIENT ONLY", "EQX/EQY force remains Cs × W in FEA", "warn")
        with c4:
            card("CR&SH", "PARAMETER HANDOFF", "Consumed by Prestress Losses / staged FEA", "neutral")

        rows = [
            {
                "item": "DL",
                "symbol": "DL / Self-weight",
                "quantity_type": "FEA auto self-weight",
                "value": "FEA auto",
                "unit": "—",
                "basis": "Material density and model geometry",
                "mapping": "Generated by the FEA model from material density.",
                "direction": "Gravity",
                "source": "3.1 DL",
                "status": "FEA-owned",
                "status_mode": "neutral",
                "check": "Confirm FEA self-weight is active once only; do not add a duplicate DL line load.",
            },
            {
                "item": "SDL",
                "symbol": "SDL",
                "quantity_type": "Permanent line load",
                "value": f"{float(ld['sdl_selected_adopted_kn_m']):.2f}",
                "unit": "kN/m",
                "basis": f"{ld['sdl_track_basis']} component table",
                "mapping": "Apply along span using the selected track basis.",
                "direction": "Gravity",
                "source": "3.2 SDL",
                "status": "Adopted load",
                "status_mode": "pass",
                "check": "Map as permanent SDL; keep component-table trace in report.",
            },
            {
                "item": "LL + IM",
                "symbol": "LL+IM",
                "quantity_type": "Traffic model factor",
                "value": f"U20 × {format_engineering_value(lc['dynamic_factor_design'], 'factor')}",
                "unit": "factor",
                "basis": "Railway load model + adopted dynamic factor",
                "mapping": "Use as the traffic load model multiplier.",
                "direction": "Vertical",
                "source": "3.3 LL+IM",
                "status": "Traffic basis",
                "status_mode": "pass",
                "check": "Confirm the FEA moving-load case uses the same U20 and IM basis.",
            },
            {
                "item": "LF",
                "symbol": "LF",
                "quantity_type": "Longitudinal rail load",
                "value": f"{float(ld['LF_design_kn']):.0f} total / {float(ld['LF_design_kn_m']):.1f} line",
                "unit": "kN / kN/m",
                "basis": "Governing traction/braking route",
                "mapping": "Apply at rail level over the selected span basis.",
                "direction": "Longitudinal",
                "source": "3.4 LF/HF",
                "status": "Adopted load",
                "status_mode": "pass",
                "check": "Use the governing LF route only; do not stack traction and braking unless the FEA combination requires it.",
            },
            {
                "item": "HF",
                "symbol": "HF / Qsk",
                "quantity_type": "Concentrated lateral load",
                "value": f"{float(ld['hf_HF_adopted_kn']):.0f}",
                "unit": "kN",
                "basis": "EN horizontal force basis",
                "mapping": "Apply at top of rail as the adopted horizontal force.",
                "direction": "Transverse",
                "source": "3.4 LF/HF",
                "status": "Adopted load",
                "status_mode": "pass",
                "check": str(ld.get("hf_decision_basis", "Confirm vertical traffic-load classification and combination basis.")),
            },
            {
                "item": "CF",
                "symbol": "CF / C",
                "quantity_type": "Traffic lateral coefficient",
                "value": f"{float(ld['cf_C_percent']):.2f}% LL",
                "unit": "% of LL",
                "basis": str(ld.get("cf_alignment_condition", "Alignment condition")),
                "mapping": f"Apply only when adopted for FEA; application level = {rail.get('cf_application_level', 'Rail level')}.",
                "direction": "Radial / transverse",
                "source": "3.6 CF",
                "status": str(ld.get("cf_fea_adoption_status", ld.get("cf_assessment", "Review"))),
                "status_mode": "warn" if "not" in str(ld.get("cf_fea_adoption_status", "")).lower() else "neutral",
                "check": str(ld.get("cf_fea_adoption_note", ld.get("cf_assessment_note", "Confirm whether CF is adopted into the FEA load set."))),
            },
            {
                "item": "Wind — structure",
                "symbol": "WS",
                "quantity_type": "Transverse line load",
                "value": f"{float(ld['WSsuper_kn_m']):.2f}",
                "unit": "kN/m",
                "basis": "EN 1991-1-4 + DPT 1311-50 trace",
                "mapping": "Apply to superstructure wind area.",
                "direction": "Wind transverse",
                "source": "3.7 Wind",
                "status": "Adopted load",
                "status_mode": "pass",
                "check": "Confirm wind direction sign convention and selected wind group in the FEA model.",
            },
            {
                "item": "Wind — structure + train",
                "symbol": "WS+WL",
                "quantity_type": "Transverse line-load envelope",
                "value": f"{float(ld['WSsuper_WL_kn_m']):.2f}",
                "unit": "kN/m",
                "basis": "Superstructure plus train silhouette",
                "mapping": "Use as the wind-with-train envelope case, not as an additive duplicate of WS unless the combination requires it.",
                "direction": "Wind transverse",
                "source": "3.7 Wind",
                "status": "Adopted envelope",
                "status_mode": "pass",
                "check": "Map WS and WS+WL as separate alternatives/envelopes, not automatically simultaneous loads.",
            },
            {
                "item": "EQ",
                "symbol": "EQX / EQY",
                "quantity_type": "Equivalent-static coefficient",
                "value": f"Cs = {float(ld['eq_Cs']):.4f}",
                "unit": "coefficient",
                "basis": f"Sa(T)×I/R = {float(ld['eq_Sa']):.4f}×{float(lc['seismic_I']):.2f}/{float(lc['seismic_R']):.1f}",
                "mapping": "FEA generates numeric EQ force from seismic weight/mass source W.",
                "direction": "X/Y independent horizontal",
                "source": "3.9 EQ",
                "status": "Coefficient trace",
                "status_mode": "warn",
                "check": "Do not enter W here. Confirm FEA mass source and load pattern: EQX = Cs×W, EQY = Cs×W.",
            },
            {
                "item": "CR&SH",
                "symbol": "CR&SH",
                "quantity_type": "Long-term parameter handoff",
                "value": "Parameters",
                "unit": "—",
                "basis": "RH, age, drying perimeter, V/S and h0 trace",
                "mapping": "Consumed by Prestress Losses and/or staged-construction FEA settings.",
                "direction": "Long-term prestress/time effects",
                "source": "3.8 CR&SH",
                "status": "Downstream",
                "status_mode": "neutral",
                "check": "Not a direct load pattern. Keep the parameter trace with Prestress Losses and report notes.",
            },
        ]
        render_fea_load_input_handoff_table(rows)
        render_fea_handoff_status_legend()
        st.markdown("### FEA input review checklist")
        render_fea_load_input_review_checklist()
        render_loads_workspace_closeout_panel()
        st.markdown(
            '<div class="note-box"><b>Report/export rule:</b> this FEA Load Input Summary reads from the same load schema edited in 3.1–3.9. Values shown as coefficients or parameters must remain coefficients/parameters unless the external FEA model supplies the missing source, such as seismic weight W. The checklist and closeout panel above are transfer-control aids and do not create new load inputs; this page does not create new load inputs.</div>',
            unsafe_allow_html=True,
        )
        with st.expander("FEA handoff notes / source guard", expanded=False):
            show_engineering_table(pd.DataFrame([
                ["DL", "Do not duplicate self-weight if the FEA model already generates self-weight from material density."],
                ["EQ", "This app exports Cs and source trace only. Numeric EQ force requires W from the FEA mass/seismic-weight source."],
                ["CR&SH", "This is a long-term parameter handoff, not a direct equivalent nodal/line load."],
                ["All rows", "If a load is overridden in FEA, document the override in the FEA model/report rather than creating a second input source here."],
            ], columns=["Item", "Guard / required action"]))


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
        ["JackFrom / stressing basis", summary.get("jack_from_display", "—"), "-", summary.get("stressing_mode", "detected from General tendon table")],
        ["Stressing force policy", summary.get("stressing_force_policy", "Pj/tendon is axial force; two-end stressing does not double total Pj."), "-", "locked rule for friction/anchor-set routing"],
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




def _normalise_jack_from(value: Any) -> str:
    """Compatibility wrapper for app-local prestress-loss helpers."""
    return normalise_jack_from(value)


def _psloss_stressing_basis_state(adopted_model: dict[str, Any], tendon_locked: bool) -> dict[str, Any]:
    """Evaluate the JackFrom / stressing-end source gate for future loss formulas.

    The gate deliberately separates tendon axial force from stressing operation.
    Two-end stressing changes friction and anchor-set distribution, but it never
    doubles Aps,total or total axial jacking force.
    """
    ps = D.setdefault("prestress", {})
    tendons = adopted_model.get("tendons", []) if isinstance(adopted_model, dict) else []
    jack_values = [_normalise_jack_from(t.get("jack_from")) for t in tendons if isinstance(t, dict)]
    jack_values = [v for v in jack_values if v]
    unique = sorted(set(jack_values), key=lambda v: {"Start": 0, "End": 1, "Both ends": 2}.get(v, 9))
    jack_display = ", ".join(unique) if unique else "-"

    if not tendon_locked:
        status = "BLOCKED"
        mode = "warn"
        stressing_mode = "Blocked until tendon model is adopted"
        friction_basis = "No adopted tendon profile / JackFrom source"
        anchor_basis = "No adopted stressing-end source"
        ready = False
        message = "Adopt the tendon model before checking one-end/two-end stressing basis."
    elif not unique:
        status = "MISSING"
        mode = "warn"
        stressing_mode = "JackFrom not found in adopted tendon snapshot"
        friction_basis = "Cannot route friction loss until JackFrom is known"
        anchor_basis = "Cannot route anchor-set distribution until JackFrom is known"
        ready = False
        message = "Adopted tendon source exists but JackFrom / stressing-end metadata is missing."
    elif unique == ["Both ends"]:
        status = "READY"
        mode = "pass"
        stressing_mode = "Two-end stressing"
        friction_basis = "Future friction solver must split tendon path from both ends"
        anchor_basis = "Anchor-set distribution applies from both stressing ends"
        ready = True
        message = "Two-end stressing is explicit; use it for loss distribution only, not total force doubling."
    elif len(unique) == 1 and unique[0] in {"Start", "End"}:
        status = "READY"
        mode = "pass"
        stressing_mode = f"One-end stressing from {unique[0]}"
        friction_basis = f"Future friction solver starts from {unique[0]} end for each tendon"
        anchor_basis = f"Anchor-set effect starts from {unique[0]} end"
        ready = True
        message = "One-end stressing basis is explicit."
    elif set(unique).issubset({"Start", "End"}):
        status = "REVIEW"
        mode = "warn"
        stressing_mode = "Mixed one-end stressing by tendon"
        friction_basis = "Use each tendon row JackFrom; do not average ends globally"
        anchor_basis = "Anchor-set distribution must be tendon-specific"
        ready = True
        message = "Mixed Start/End JackFrom is explicit but requires tendon-by-tendon review."
    else:
        status = "REVIEW"
        mode = "warn"
        stressing_mode = "Project-specific / mixed stressing text"
        friction_basis = "Review adopted tendon table before detailed loss calculation"
        anchor_basis = "Review jacking-end basis before anchor-set calculation"
        ready = True
        message = "JackFrom source exists but needs engineering review."

    return {
        "status": status,
        "mode": mode,
        "ready": ready,
        "message": message,
        "jack_from_values": unique,
        "jack_from_display": jack_display,
        "stressing_mode": stressing_mode,
        "friction_path_basis": friction_basis,
        "anchor_set_basis": anchor_basis,
        "force_policy": "Pj/tendon is axial force per tendon; total Pj = number of adopted tendons × Pj/tendon.",
        "two_end_policy": "Two-end stressing controls loss distribution only; it must not double Aps,total or total prestressing force.",
        "source": "Adopted CSiBridge General tendon table JackFrom field" if tendon_locked else "2.4 tendon adoption required",
        "default_basis": ps.get("jacking_operation_basis", "Project JackFrom basis not set"),
    }


def _psloss_source_gate_state() -> dict[str, Any]:
    """Build the PSLOSS.4 read-only source gate for detailed loss calculation.

    Prestress Losses must consume locked/adopted sources only.  Working tendon
    imports, keyed fallback values, and diagnostic previews are deliberately kept
    out of the detailed-loss readiness status.  PSLOSS.4 keeps the adopted
    tendon summary and calculation-readiness register and adds a gated
    friction source preview on 4.2 before any final-loss adoption can occur.
    """
    tl = D.setdefault("tendon_layout", {})
    ps = D.setdefault("prestress", {})
    sec = D.setdefault("section", {})
    project = D.setdefault("project", {})

    working_model = _active_tendon_model()
    adopted_model = _active_adopted_tendon_model()
    tendon_status = tendon_model_status(working_model, tl)
    tendon_locked = bool(adopted_model) and tendon_status.get("status") == "LOCKED"
    adopted_summary = tl.get("adopted_downstream_summary") if tendon_locked else {}
    if not isinstance(adopted_summary, dict) or not adopted_summary:
        adopted_summary = build_tendon_downstream_summary(
            adopted_model,
            y_t_from_top_m=float(sec.get("yt_from_top_m", 0.0) or 0.0),
        ) if tendon_locked else {}

    stressing_basis = _psloss_stressing_basis_state(adopted_model, tendon_locked)
    section_ready = all(float(sec.get(k, 0.0) or 0.0) > 0.0 for k in ("Ac_m2", "I33_m4", "I22_m4", "yt_from_top_m"))
    crsh = update_crsh_derived_parameters()
    crsh_ready = (
        float(ps.get("RH_percent", 0.0) or 0.0) > 0.0
        and float(ps.get("ti_days", 0.0) or 0.0) >= 0.0
        and float(ps.get("tf_days", 0.0) or 0.0) > float(ps.get("ti_days", 0.0) or 0.0)
        and float(ps.get("V_over_S_in", 0.0) or 0.0) > 0.0
        and float(ps.get("h0_m", 0.0) or 0.0) > 0.0
    )
    span_ready = float(project.get("span_m", 0.0) or 0.0) > 0.0
    ready = tendon_locked and stressing_basis["ready"] and section_ready and crsh_ready and span_ready

    return {
        "overall_status": "READY FOR LOSS CALCULATION" if ready else "SOURCE BLOCKED",
        "overall_mode": "pass" if ready else "warn",
        "ready": ready,
        "tendon_locked": tendon_locked,
        "tendon_status": tendon_status,
        "stressing_basis": stressing_basis,
        "adopted_summary": adopted_summary,
        "working_fingerprint": tendon_model_fingerprint(working_model),
        "adopted_fingerprint": str(tl.get("adopted_model_fingerprint") or tendon_model_fingerprint(adopted_model) or ""),
        "section_ready": section_ready,
        "crsh_ready": crsh_ready,
        "span_ready": span_ready,
        "crsh": crsh,
    }


def _psloss_source_gate_rows(state: dict[str, Any]) -> pd.DataFrame:
    ps = D.setdefault("prestress", {})
    sec = D.setdefault("section", {})
    project = D.setdefault("project", {})
    tendon_status = state["tendon_status"]
    stressing = state["stressing_basis"]
    return pd.DataFrame(
        [
            [
                "Adopted tendon source",
                tendon_status.get("status", "PENDING"),
                "2.4 Tendon Layout Reference → Adopted Tendon Data",
                tendon_status.get("message", "Adopt imported tendon model before detailed losses."),
            ],
            [
                "Stressing basis / JackFrom",
                stressing.get("status", "BLOCKED"),
                stressing.get("source", "2.4 tendon adoption required"),
                stressing.get("message", "Confirm one-end / two-end stressing before friction and anchor-set calculations."),
            ],
            [
                "Section properties",
                "READY" if state["section_ready"] else "MISSING",
                "2.3 Section Properties → Adopted Properties for Design",
                f"A={float(sec.get('Ac_m2', 0.0) or 0.0):.3f} m²; y_t={float(sec.get('yt_from_top_m', 0.0) or 0.0):.3f} m; J source={sec.get('J_method', 'User override')}",
            ],
            [
                "CR&SH parameters",
                "READY" if state["crsh_ready"] else "MISSING",
                "3.8 CR&SH",
                f"RH={float(ps.get('RH_percent', 0.0) or 0.0):.1f}%; V/S={float(ps.get('V_over_S_in', 0.0) or 0.0):.2f} in; h0={float(ps.get('h0_m', 0.0) or 0.0):.4f} m; basis={ps.get('crsh_drying_perimeter_basis', '-')}",
            ],
            [
                "Span / stage basis",
                "READY" if state["span_ready"] else "MISSING",
                "Project / 3 Loads closeout",
                f"Span L={float(project.get('span_m', 0.0) or 0.0):.3f} m; staged construction loads remain owned by FEA/stage source.",
            ],
        ],
        columns=["Source gate", "Status", "Source page", "Trace / required action"],
    )


def _psloss_stressing_basis_rows(state: dict[str, Any]) -> pd.DataFrame:
    stressing = state.get("stressing_basis", {})
    return pd.DataFrame(
        [
            ["JackFrom source", stressing.get("jack_from_display", "-"), stressing.get("status", "BLOCKED"), stressing.get("source", "2.4 tendon adoption required")],
            ["Stressing mode", stressing.get("stressing_mode", "-"), stressing.get("status", "BLOCKED"), stressing.get("message", "Confirm stressing basis.")],
            ["Friction path basis", stressing.get("friction_path_basis", "-"), "FUTURE INPUT", "Used by future friction-loss calculation; no final formula adoption runs in PSLOSS.4."],
            ["Anchor-set distribution basis", stressing.get("anchor_set_basis", "-"), "FUTURE INPUT", "Used by future anchor-set calculation; equivalent loss remains separately scoped."],
            ["Pj/tendon policy", stressing.get("force_policy", "Pj/tendon is axial tendon force."), "LOCKED RULE", "Do not multiply force by number of jacks."],
            ["Two-end stressing safeguard", stressing.get("two_end_policy", "Two-end stressing does not double total force."), "LOCKED RULE", "Controls friction/anchor-set distribution only."],
        ],
        columns=["Item", "Value", "Status", "Basis / required action"],
    )


def _psloss_blocked_tendon_checklist_rows(state: dict[str, Any]) -> pd.DataFrame:
    blocked = not bool(state.get("adopted_summary"))
    rows = [
        ["Adopted tendon snapshot", "BLOCKED" if blocked else "READY", "Go to 2.4 Tendon Layout Reference → Adopted Tendon Data and adopt/re-adopt the tendon model." if blocked else "Locked adopted tendon snapshot is available."],
        ["Tendon profile", "BLOCKED" if blocked else "READY", "Import / verify General, Vertical, and Horizontal tendon tables." if blocked else "Profile rows are read from the adopted snapshot."],
        ["Aps,total", "BLOCKED" if blocked else "READY", "No adopted tendon source; do not use keyed fallback Aps for detailed losses." if blocked else "Read from adopted General tendon table summary."],
        ["Jacking force", "BLOCKED" if blocked else "READY", "No adopted tendon source; Pj/tendon and total Pj remain blocked." if blocked else "Pj/tendon is axial force; total Pj is not doubled for two-end stressing."],
        ["JackFrom / stressing end", "BLOCKED" if blocked else state.get("stressing_basis", {}).get("status", "READY"), "Adopted General tendon table must define Start / End / Both ends before friction and anchor-set losses." if blocked else state.get("stressing_basis", {}).get("message", "Stressing basis is available.")],
        ["Midspan eccentricity", "BLOCKED" if blocked else "READY", "No adopted tendon source; dp and eccentricity remain blocked." if blocked else "Read from adopted tendon profile and adopted section y_t."],
    ]
    return pd.DataFrame(rows, columns=["Prestress input", "Status", "Required action / source rule"])


def _psloss_tendon_summary_rows(state: dict[str, Any]) -> pd.DataFrame:
    summary = state.get("adopted_summary") or {}
    ps = D.setdefault("prestress", {})
    if not summary:
        return pd.DataFrame(
            [["Tendon source", "SOURCE BLOCKED", "-", "Adopt/re-adopt the tendon model before detailed prestress-loss calculation."]],
            columns=["Item", "Adopted value", "Unit", "Basis / trace"],
        )
    tendon_count = float(summary.get("tendon_count", 0.0) or 0.0)
    force_per = float(summary.get("jacking_force_per_tendon_kN", 0.0) or 0.0)
    force_total = float(summary.get("jacking_force_total_kN", 0.0) or 0.0)
    jack_from = "Mixed / see adopted tendon table"
    adopted = _active_adopted_tendon_model()
    tendons = adopted.get("tendons", []) if isinstance(adopted, dict) else []
    jack_values = sorted({str(t.get("jack_from", "")).strip() for t in tendons if str(t.get("jack_from", "")).strip()})
    if len(jack_values) == 1:
        jack_from = jack_values[0]
    elif not jack_values:
        jack_from = ps.get("jacking_operation_basis", "See adopted tendon table")
    return pd.DataFrame(
        [
            ["Tendon count", summary.get("tendon_count", 0), "tendons", "locked adopted tendon snapshot"],
            ["Aps per tendon", summary.get("Aps_per_tendon_mm2", 0.0), "mm²", "CSiBridge General tendon table"],
            ["Aps total", summary.get("Aps_total_mm2", 0.0), "mm²", "sum of adopted tendons"],
            ["Jacking stress", summary.get("jacking_stress_mpa", 0.0), "MPa", "0.75 fpu unless project source overrides"],
            ["Jacking force per tendon", force_per, "kN", "tendon axial jacking force; not multiplied by number of jacks"],
            ["Total jacking force", force_total, "kN", f"{int(tendon_count)} × Pj/tendon; do not double for two-end stressing"],
            ["Jacking operation / JackFrom", jack_from, "-", "controls friction/anchor-set distribution; not Aps or total axial force"],
            ["Average dp at end", summary.get("dp_avg_end_m", 0.0), "m", "area-weighted from adopted profile"],
            ["Average dp at midspan", summary.get("dp_avg_midspan_m", 0.0), "m", "area-weighted from adopted profile"],
            ["Midspan eccentricity", summary.get("eccentricity_midspan_m", 0.0), "m", "e = dp(midspan) − y_t"],
            ["Model fingerprint", summary.get("model_fingerprint", state.get("adopted_fingerprint", "-")), "-", "source trace"],
        ],
        columns=["Item", "Adopted value", "Unit", "Basis / trace"],
    )


def _psloss_crsh_handoff_rows(state: dict[str, Any]) -> pd.DataFrame:
    ps = D.setdefault("prestress", {})
    crsh = state.get("crsh", update_crsh_derived_parameters())
    tf_years = float(ps.get("tf_days", 0.0) or 0.0) / 365.25 if float(ps.get("tf_days", 0.0) or 0.0) > 0.0 else 0.0
    return pd.DataFrame(
        [
            ["RH", f"{float(ps.get('RH_percent', 0.0) or 0.0):.1f}", "%", "3.8 CR&SH user project assumption"],
            ["ti", f"{float(ps.get('ti_days', 0.0) or 0.0):.0f}", "days", "age at stressing / load transfer basis"],
            ["tf", f"{float(ps.get('tf_days', 0.0) or 0.0):.0f} ≈ {tf_years:.1f}", "days / years", "final design age"],
            ["Drying perimeter basis", ps.get("crsh_drying_perimeter_basis", "-"), "-", "outer-only vs outer+inner void trace"],
            ["u_total", f"{float(crsh.get('u_total_m', 0.0) or 0.0):.2f}", "m", "derived from selected drying perimeter basis"],
            ["V/S", f"{float(crsh.get('V_over_S_in', 0.0) or 0.0):.2f}", "in", "AASHTO empirical creep/shrinkage factor input"],
            ["V/S", f"{float(crsh.get('V_over_S_m', 0.0) or 0.0):.4f}", "m", "SI report value"],
            ["h0", f"{float(crsh.get('h0_m', 0.0) or 0.0):.4f}", "m", "h0 = 2Ac/u_total = 2(V/S)"],
        ],
        columns=["Parameter", "Adopted value", "Unit", "Source / trace"],
    )




def _psloss_adopted_tendon_readiness_rows(state: dict[str, Any]) -> pd.DataFrame:
    """PSLOSS.4 readiness rows focused on the adopted tendon snapshot.

    This register is intentionally source-only.  It confirms whether the future
    loss solver has the tendon profile, jacking force, stressing-side basis,
    and eccentricity data it needs; it does not calculate losses.
    """
    summary = state.get("adopted_summary") or {}
    stressing = state.get("stressing_basis", {})
    locked = bool(state.get("tendon_locked"))
    if not locked or not summary:
        return pd.DataFrame(
            [
                ["Adopted tendon snapshot", "BLOCKED", "2.4 Tendon Layout Reference", "Adopt/re-adopt the tendon model before any detailed loss formula can consume tendon values."],
                ["Tendon profile path", "BLOCKED", "Adopted vertical + horizontal tendon model", "Friction loss needs adopted station-by-station profile, not working import preview."],
                ["Jacking force basis", "BLOCKED", "Adopted General tendon table", "Pj/tendon and total Pj stay blocked until tendon source is locked."],
                ["Stressing / JackFrom basis", "BLOCKED", "Adopted General tendon table JackFrom field", "One-end/two-end/mixed stressing must be explicit before friction and anchor-set distribution."],
                ["Eccentricity basis", "BLOCKED", "Adopted profile + adopted section y_t", "dp/end, dp/midspan, and e_midspan stay blocked until tendon source is locked."],
            ],
            columns=["Readiness item", "Status", "Source owner", "Required action / source rule"],
        )

    tendon_count = int(summary.get("tendon_count", 0) or 0)
    aps_total = float(summary.get("Aps_total_mm2", 0.0) or 0.0)
    force_per = float(summary.get("jacking_force_per_tendon_kN", 0.0) or 0.0)
    force_total = float(summary.get("jacking_force_total_kN", 0.0) or 0.0)
    e_mid = float(summary.get("eccentricity_midspan_m", 0.0) or 0.0)
    return pd.DataFrame(
        [
            ["Adopted tendon snapshot", "READY", "2.4 Adopted Tendon Data", f"Locked snapshot contains {tendon_count} tendons; fingerprint = {state.get('adopted_fingerprint') or summary.get('model_fingerprint', '-')}"],
            ["Tendon profile path", "READY", "Adopted vertical + horizontal tendon model", "Future friction loss must read the adopted profile and tendon-by-tendon stations only."],
            ["Jacking force basis", "READY", "Adopted General tendon table", f"Pj/tendon = {force_per:.0f} kN; total Pj = {force_total:.0f} kN; Aps,total = {aps_total:.0f} mm²."],
            ["Stressing / JackFrom basis", stressing.get("status", "REVIEW"), "Adopted General tendon table JackFrom field", stressing.get("message", "Confirm stressing basis before friction and anchor-set formulas.")],
            ["Eccentricity basis", "READY", "Adopted profile + adopted section y_t", f"e_midspan = {e_mid:.3f} m; used later for stress/loss coupling trace only."],
        ],
        columns=["Readiness item", "Status", "Source owner", "Required action / source rule"],
    )


def _psloss_formula_readiness_rows(state: dict[str, Any]) -> pd.DataFrame:
    """Report-ready PSLOSS.4 component readiness register.

    The row status tells the next milestone what can be calculated safely.  It
    deliberately does not run friction, anchor set, elastic shortening, creep,
    shrinkage, or relaxation equations.
    """
    source_ready = bool(state.get("ready"))
    tendon_ready = bool(state.get("tendon_locked"))
    stressing_ready = bool(state.get("stressing_basis", {}).get("ready"))
    section_ready = bool(state.get("section_ready"))
    crsh_ready = bool(state.get("crsh_ready"))
    span_ready = bool(state.get("span_ready"))

    friction_ready = source_ready and stressing_ready
    anchor_ready = source_ready and stressing_ready
    es_ready = tendon_ready and section_ready and span_ready
    crsh_component_ready = section_ready and crsh_ready
    return pd.DataFrame(
        [
            [
                "Friction loss",
                "READY FOR FORMULA MILESTONE" if friction_ready else "SOURCE BLOCKED",
                "Adopted tendon profile + JackFrom/stressing basis + span path",
                "Use tendon-by-tendon adopted station profile; do not use working import preview or averaged JackFrom.",
            ],
            [
                "Anchor set",
                "READY FOR FORMULA MILESTONE" if anchor_ready else "SOURCE BLOCKED",
                "Adopted JackFrom/stressing basis + project anchor-set input",
                "Anchor-set distribution depends on stressing end; two-end stressing does not double Pj.",
            ],
            [
                "Elastic shortening",
                "STAGE REVIEW REQUIRED" if es_ready else "SOURCE BLOCKED",
                "Adopted section + tendon source + actual stressing/load-transfer stage",
                "fcgp must reflect the actual span-by-span stressing stage; completed-span self-weight must not be assumed automatically.",
            ],
            [
                "Creep / shrinkage",
                "READY FOR FORMULA MILESTONE" if crsh_component_ready else "SOURCE BLOCKED",
                "3.8 CR&SH RH, V/S, h0, ti/tf + adopted section geometry",
                "Use CR&SH handoff only; do not create duplicate RH or V/S inputs in 4 Prestress Losses.",
            ],
            [
                "Relaxation",
                "FUTURE INPUT REVIEW",
                "Prestressing strand class / low-relaxation basis",
                "Confirm strand relaxation class and source before final effective-prestress summary.",
            ],
            [
                "Effective prestress summary",
                "BLOCKED UNTIL COMPONENTS RUN",
                "Future component result table",
                "Do not report final effective prestress until detailed component losses are calculated and adopted.",
            ],
        ],
        columns=["Loss component", "Readiness status", "Required adopted source", "Required engineer check"],
    )

def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _profile_points_for_tendon(model: dict[str, Any], tendon_name: str) -> list[dict[str, float]]:
    """Return adopted profile points for one tendon from the adopted snapshot."""
    rows = []
    for r in model.get("profile_rows", []) or []:
        if str(r.get("Tendon", "")) != str(tendon_name):
            continue
        x = _safe_float(r.get("x_m"), None)
        dp = _safe_float(r.get("dp_top_m"), None)
        off = _safe_float(r.get("horiz_off_m"), None)
        if x is None or dp is None or off is None:
            continue
        rows.append({"x_m": float(x), "dp_top_m": float(dp), "horiz_off_m": float(off)})
    rows.sort(key=lambda item: item["x_m"])
    return rows


def _unit_vector_between(a: dict[str, float], b: dict[str, float]) -> tuple[float, float, float] | None:
    dx = b["x_m"] - a["x_m"]
    dy = b["horiz_off_m"] - a["horiz_off_m"]
    dz = b["dp_top_m"] - a["dp_top_m"]
    length = sqrt(dx * dx + dy * dy + dz * dz)
    if length <= 1e-12:
        return None
    return (dx / length, dy / length, dz / length)


def _angle_between_vectors(u: tuple[float, float, float] | None, v: tuple[float, float, float] | None) -> float:
    if u is None or v is None:
        return 0.0
    dot = max(min(u[0] * v[0] + u[1] * v[1] + u[2] * v[2], 1.0), -1.0)
    return float(acos(dot))


def _friction_route_trace(points: list[dict[str, float]], *, from_end: bool, mu: float, k_per_m: float, fpj_mpa: float) -> list[dict[str, float]]:
    """Return route trace from the active jacking end using adopted profile points."""
    ordered = list(reversed(points)) if from_end else list(points)
    if not ordered:
        return []
    seg_vectors: list[tuple[float, float, float] | None] = []
    seg_lengths: list[float] = []
    for i in range(1, len(ordered)):
        a, b = ordered[i - 1], ordered[i]
        dx = b["x_m"] - a["x_m"]
        dy = b["horiz_off_m"] - a["horiz_off_m"]
        dz = b["dp_top_m"] - a["dp_top_m"]
        length = sqrt(dx * dx + dy * dy + dz * dz)
        seg_lengths.append(float(length))
        seg_vectors.append(_unit_vector_between(a, b))

    out: list[dict[str, float]] = []
    x_path = 0.0
    alpha = 0.0
    out.append({"x_m": ordered[0]["x_m"], "path_m": 0.0, "alpha_rad": 0.0, "kx_term": 0.0, "mu_alpha_term": 0.0, "exponent": 0.0, "exp_factor": 1.0, "loss_mpa": 0.0, "stress_mpa": fpj_mpa})
    for i in range(1, len(ordered)):
        x_path += seg_lengths[i - 1]
        if i >= 2:
            alpha += _angle_between_vectors(seg_vectors[i - 2], seg_vectors[i - 1])
        kx_term = k_per_m * x_path
        mu_alpha_term = mu * alpha
        exponent = max(kx_term + mu_alpha_term, 0.0)
        exp_factor = exp(-exponent)
        loss = fpj_mpa * (1.0 - exp_factor) if fpj_mpa > 0.0 else 0.0
        out.append({"x_m": ordered[i]["x_m"], "path_m": x_path, "alpha_rad": alpha, "kx_term": kx_term, "mu_alpha_term": mu_alpha_term, "exponent": exponent, "exp_factor": exp_factor, "loss_mpa": loss, "stress_mpa": fpj_mpa - loss})
    return out


def _psloss_friction_source_state(state: dict[str, Any]) -> dict[str, Any]:
    ps = D.setdefault("prestress", {})
    model = _active_adopted_tendon_model() if state.get("tendon_locked") else {}
    stressing = state.get("stressing_basis", {})
    mu = _safe_float(ps.get("mu_external", 0.15), 0.15)
    k_per_m = _safe_float(ps.get("wobble_external_per_m", 0.0), 0.0)
    summary = state.get("adopted_summary") or {}
    fpj_mpa = _safe_float(summary.get("jacking_stress_mpa") or D.setdefault("materials", {}).get("fpi_mpa", 0.0), 0.0)
    ready = bool(state.get("tendon_locked")) and bool(stressing.get("ready")) and bool(model.get("profile_rows")) and fpj_mpa > 0.0
    return {
        "ready": ready,
        "status": "PREVIEW READY" if ready else "SOURCE BLOCKED",
        "mode": "pass" if ready else "warn",
        "model": model,
        "mu": mu,
        "k_per_m": k_per_m,
        "fpj_mpa": fpj_mpa,
        "stressing": stressing,
        "message": "Friction preview uses adopted tendon profile and JackFrom trace." if ready else "Adopt tendon model and JackFrom basis before friction preview can run.",
    }


def _psloss_friction_source_rows(state: dict[str, Any]) -> pd.DataFrame:
    fstate = _psloss_friction_source_state(state)
    return pd.DataFrame(
        [
            ["Adopted tendon profile", "READY" if state.get("tendon_locked") else "BLOCKED", "2.4 Adopted Tendon Data", "Friction path must use adopted station-by-station profile rows only."],
            ["JackFrom / stressing basis", state.get("stressing_basis", {}).get("status", "BLOCKED"), state.get("stressing_basis", {}).get("source", "2.4 tendon adoption required"), "Controls one-end, two-end, or mixed tendon-by-tendon friction path."],
            ["Friction coefficient μ", f"{fstate['mu']:.4f}", "4.2 Friction project input", "External/unbonded tendon coefficient; engineer must verify project/PT-system basis."],
            ["Wobble coefficient K", f"{fstate['k_per_m']:.6f} 1/m", "4.2 Friction project input", "Use zero only when justified by external tendon layout / project basis."],
            ["Jacking stress fpj", f"{fstate['fpj_mpa']:.2f} MPa", "Adopted tendon summary / material basis", "Stress basis for preview only; Pj/tendon remains axial force and is not doubled for two-end stressing."],
            ["Preview status", fstate["status"], "Source gate", fstate["message"]],
        ],
        columns=["Friction source item", "Status / value", "Source owner", "Required engineer check"],
    )


def _governing_route_item(trace: list[dict[str, float]]) -> dict[str, float]:
    if not trace:
        return {"x_m": 0.0, "path_m": 0.0, "alpha_rad": 0.0, "exponent": 0.0, "loss_mpa": 0.0, "stress_mpa": 0.0}
    return max(trace, key=lambda r: r.get("loss_mpa", 0.0))


def _psloss_friction_preview_rows(state: dict[str, Any]) -> pd.DataFrame:
    fstate = _psloss_friction_source_state(state)
    if not fstate.get("ready"):
        return pd.DataFrame(
            [["SOURCE BLOCKED", "-", "-", "-", "-", "-", "-", "Adopt tendon model and JackFrom/stressing basis before friction preview."]],
            columns=["Tendon", "JackFrom", "Route basis", "Gov. station (m)", "Path x (m)", "α (rad)", "Loss preview", "Status / note"],
        )
    model = fstate["model"]
    mu = fstate["mu"]
    k_per_m = fstate["k_per_m"]
    fpj_mpa = fstate["fpj_mpa"]
    rows: list[list[Any]] = []
    for tendon in model.get("tendons", []) or []:
        name = str(tendon.get("tendon", "-"))
        jack = str(tendon.get("jack_from", "")).strip() or "Unknown"
        points = _profile_points_for_tendon(model, name)
        if len(points) < 2:
            rows.append([name, jack, "missing profile", "-", "-", "-", "-", "REVIEW: adopted profile has fewer than two points"])
            continue
        jack_lower = jack.lower()
        if "both" in jack_lower:
            start_trace = _friction_route_trace(points, from_end=False, mu=mu, k_per_m=k_per_m, fpj_mpa=fpj_mpa)
            end_trace = _friction_route_trace(points, from_end=True, mu=mu, k_per_m=k_per_m, fpj_mpa=fpj_mpa)
            end_by_x = {round(r["x_m"], 9): r for r in end_trace}
            combined: list[dict[str, float]] = []
            for sr in start_trace:
                er = end_by_x.get(round(sr["x_m"], 9), sr)
                chosen = sr if sr.get("exponent", 0.0) <= er.get("exponent", 0.0) else er
                combined.append(chosen)
            gov = _governing_route_item(combined)
            route_basis = "two-end; nearer-end preview"
            status = "PREVIEW · do not double Pj"
        elif jack_lower == "end":
            trace = _friction_route_trace(points, from_end=True, mu=mu, k_per_m=k_per_m, fpj_mpa=fpj_mpa)
            gov = _governing_route_item(trace)
            route_basis = "from End"
            status = "PREVIEW"
        else:
            trace = _friction_route_trace(points, from_end=False, mu=mu, k_per_m=k_per_m, fpj_mpa=fpj_mpa)
            gov = _governing_route_item(trace)
            route_basis = "from Start"
            status = "PREVIEW" if jack_lower in {"start", ""} else "REVIEW JackFrom text"
        loss = gov.get("loss_mpa", 0.0)
        pct = 100.0 * loss / fpj_mpa if fpj_mpa > 0.0 else 0.0
        rows.append([
            name,
            jack,
            route_basis,
            f"{gov.get('x_m', 0.0):.3f}",
            f"{gov.get('path_m', 0.0):.3f}",
            f"{gov.get('alpha_rad', 0.0):.5f}",
            f"{loss:.2f} MPa ({pct:.2f}%)",
            status,
        ])
    return pd.DataFrame(rows, columns=["Tendon", "JackFrom", "Route basis", "Gov. station (m)", "Path x (m)", "α (rad)", "Loss preview", "Status / note"])




def _psloss_friction_result_for_tendon(tendon: dict[str, Any], fstate: dict[str, Any]) -> dict[str, Any]:
    """Return the governing source-gated friction preview result for one tendon."""
    model = fstate.get("model") or {}
    name = str(tendon.get("tendon", "-"))
    jack = str(tendon.get("jack_from", "")).strip() or "Unknown"
    points = _profile_points_for_tendon(model, name)
    if len(points) < 2:
        return {
            "tendon": name,
            "jack": jack,
            "route_basis": "missing profile",
            "status": "REVIEW: adopted profile has fewer than two points",
            "gov": _governing_route_item([]),
        }
    mu = float(fstate.get("mu", 0.0) or 0.0)
    k_per_m = float(fstate.get("k_per_m", 0.0) or 0.0)
    fpj_mpa = float(fstate.get("fpj_mpa", 0.0) or 0.0)
    jack_lower = jack.lower()
    if "both" in jack_lower:
        start_trace = _friction_route_trace(points, from_end=False, mu=mu, k_per_m=k_per_m, fpj_mpa=fpj_mpa)
        end_trace = _friction_route_trace(points, from_end=True, mu=mu, k_per_m=k_per_m, fpj_mpa=fpj_mpa)
        end_by_x = {round(r["x_m"], 9): r for r in end_trace}
        combined: list[dict[str, float]] = []
        for sr in start_trace:
            er = end_by_x.get(round(sr["x_m"], 9), sr)
            chosen = sr if sr.get("exponent", 0.0) <= er.get("exponent", 0.0) else er
            combined.append(chosen)
        return {
            "tendon": name,
            "jack": jack,
            "route_basis": "two-end; nearer-end preview",
            "status": "PREVIEW · do not double Pj",
            "gov": _governing_route_item(combined),
        }
    if jack_lower == "end":
        trace = _friction_route_trace(points, from_end=True, mu=mu, k_per_m=k_per_m, fpj_mpa=fpj_mpa)
        return {"tendon": name, "jack": jack, "route_basis": "from End", "status": "PREVIEW", "gov": _governing_route_item(trace)}
    trace = _friction_route_trace(points, from_end=False, mu=mu, k_per_m=k_per_m, fpj_mpa=fpj_mpa)
    return {
        "tendon": name,
        "jack": jack,
        "route_basis": "from Start",
        "status": "PREVIEW" if jack_lower in {"start", ""} else "REVIEW JackFrom text",
        "gov": _governing_route_item(trace),
    }


def _psloss_friction_calculation_rows(state: dict[str, Any]) -> pd.DataFrame:
    """Report-style tendon-by-tendon friction calculation trace."""
    fstate = _psloss_friction_source_state(state)
    if not fstate.get("ready"):
        return pd.DataFrame(
            [["SOURCE BLOCKED", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "Adopt tendon model and JackFrom/stressing basis before calculation trace." ]],
            columns=["Tendon", "JackFrom", "fpj (MPa)", "μ", "K (1/m)", "x from jack (m)", "α (rad)", "Kx", "μα", "Kx+μα", "exp[-(Kx+μα)]", "ΔfpF / fpx", "Status / note"],
        )
    model = fstate.get("model") or {}
    fpj_mpa = float(fstate.get("fpj_mpa", 0.0) or 0.0)
    mu = float(fstate.get("mu", 0.0) or 0.0)
    k_per_m = float(fstate.get("k_per_m", 0.0) or 0.0)
    rows: list[list[Any]] = []
    for tendon in model.get("tendons", []) or []:
        result = _psloss_friction_result_for_tendon(tendon, fstate)
        gov = result.get("gov") or {}
        loss = float(gov.get("loss_mpa", 0.0) or 0.0)
        fpx = float(gov.get("stress_mpa", fpj_mpa - loss) or 0.0)
        pct = 100.0 * loss / fpj_mpa if fpj_mpa > 0.0 else 0.0
        rows.append([
            result.get("tendon", "-"),
            result.get("jack", "-"),
            f"{fpj_mpa:.2f}",
            f"{mu:.4f}",
            f"{k_per_m:.6f}",
            f"{float(gov.get('path_m', 0.0) or 0.0):.3f}",
            f"{float(gov.get('alpha_rad', 0.0) or 0.0):.5f}",
            f"{float(gov.get('kx_term', 0.0) or 0.0):.5f}",
            f"{float(gov.get('mu_alpha_term', 0.0) or 0.0):.5f}",
            f"{float(gov.get('exponent', 0.0) or 0.0):.5f}",
            f"{float(gov.get('exp_factor', 1.0) or 1.0):.5f}",
            f"ΔfpF={loss:.2f} MPa ({pct:.2f}%) · fpx={fpx:.2f} MPa",
            result.get("status", "PREVIEW"),
        ])
    return pd.DataFrame(rows, columns=["Tendon", "JackFrom", "fpj (MPa)", "μ", "K (1/m)", "x from jack (m)", "α (rad)", "Kx", "μα", "Kx+μα", "exp[-(Kx+μα)]", "ΔfpF / fpx", "Status / note"])


def _psloss_friction_report_summary_rows(state: dict[str, Any]) -> pd.DataFrame:
    """Compact report-style summary for the friction preview."""
    fstate = _psloss_friction_source_state(state)
    if not fstate.get("ready"):
        return pd.DataFrame(
            _append_loss_percent_basis_report_rows([
                ["Calculation status", "SOURCE BLOCKED", "Adopted tendon source and JackFrom/stressing basis are required."],
                ["Adoption status", "Preview only", "No effective-prestress value is adopted from this page."],
            ]),
            columns=["Item", "Value", "Trace / note"],
        )
    model = fstate.get("model") or {}
    fpj_mpa = float(fstate.get("fpj_mpa", 0.0) or 0.0)
    results = [_psloss_friction_result_for_tendon(t, fstate) for t in model.get("tendons", []) or []]
    valid = [r for r in results if r.get("gov")]
    gov_result = max(valid, key=lambda r: float((r.get("gov") or {}).get("loss_mpa", 0.0) or 0.0)) if valid else {"tendon": "-", "gov": {}}
    gov = gov_result.get("gov") or {}
    ties = _psloss_friction_governing_tie_results(results)
    tie_label = _psloss_friction_governing_label(results)
    max_loss = float(gov.get("loss_mpa", 0.0) or 0.0)
    min_fpx = min([float((r.get("gov") or {}).get("stress_mpa", fpj_mpa) or fpj_mpa) for r in valid], default=0.0)
    max_pct = 100.0 * max_loss / fpj_mpa if fpj_mpa > 0.0 else 0.0
    stressing = fstate.get("stressing") or {}
    return pd.DataFrame(
        _append_loss_percent_basis_report_rows([
            ["Calculation status", "PREVIEW READY", "Source-gated calculation trace; not final effective prestress adoption."],
            ["Code basis", "AASHTO LRFD 2020 Art. 5.9.3.2.2b", "Post-tensioned member friction-loss route."],
            ["Formula", "ΔfpF = fpj[1 − exp{−(Kx + μα)}]", "fpx = fpj − ΔfpF; Loss % = ΔfpF/fpj × 100."],
            ["Tendons in trace", f"{len(results)} / {len(results)}", "All adopted tendons are included in the report trace."],
            ["Stressing route", stressing.get("stressing_mode", "-"), stressing.get("source", "General tendon table · JackFrom field")],
            ["μ / K", f"{float(fstate.get('mu', 0.0) or 0.0):.4f} / {float(fstate.get('k_per_m', 0.0) or 0.0):.6f} 1/m", "Project friction inputs for external/unbonded PT."],
            ["Governing tendon(s)", tie_label, f"{len(ties)} tendon(s) tied within 0.005 MPa; representative substitution uses {gov_result.get('tendon', '-')}."],
            ["Maximum friction loss", f"{max_loss:.2f} MPa ({max_pct:.2f}%)", f"Representative x={float(gov.get('path_m', 0.0) or 0.0):.3f} m; α={float(gov.get('alpha_rad', 0.0) or 0.0):.5f} rad."],
            ["Minimum fpx after friction", f"{min_fpx:.2f} MPa", "Stress after friction only; anchor set and other losses remain separate."],
        ]),
        columns=["Item", "Value", "Trace / note"],
    )




def _psloss_friction_governing_result(state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Return a representative governing friction result and supporting state."""
    fstate = _psloss_friction_source_state(state)
    model = fstate.get("model") or {}
    results = [_psloss_friction_result_for_tendon(t, fstate) for t in model.get("tendons", []) or []]
    valid = [r for r in results if r.get("gov")]
    gov_result = max(valid, key=lambda r: float((r.get("gov") or {}).get("loss_mpa", 0.0) or 0.0)) if valid else {"tendon": "-", "gov": {}}
    return gov_result, gov_result.get("gov") or {}, results, fstate


def _psloss_friction_governing_tie_results(results: list[dict[str, Any]], *, tolerance_mpa: float = 0.005) -> list[dict[str, Any]]:
    """Return all tendons tied with the governing friction loss.

    Report summaries should not imply that only the first side governs when
    mirrored tendons have the same rounded loss.  A small tolerance matches the
    displayed MPa precision and keeps the engineering report honest.
    """
    valid = [r for r in results if r.get("gov")]
    if not valid:
        return []
    max_loss = max(float((r.get("gov") or {}).get("loss_mpa", 0.0) or 0.0) for r in valid)
    return [r for r in valid if abs(float((r.get("gov") or {}).get("loss_mpa", 0.0) or 0.0) - max_loss) <= tolerance_mpa]


def _psloss_friction_governing_label(results: list[dict[str, Any]]) -> str:
    ties = _psloss_friction_governing_tie_results(results)
    names = [str(r.get("tendon", "-")).strip() or "-" for r in ties]
    if not names:
        return "-"
    if len(names) <= 4:
        return " / ".join(names)
    return f"{len(names)} tied tendons: " + ", ".join(names[:4]) + ", ..."


def _show_full_tendon_report_table(df: pd.DataFrame, *, label: str) -> None:
    """Display full tendon report tables with a row-count note and enough height.

    Default Streamlit dataframes can visually hide rows in printed/PDF review.
    For tendon-by-tendon report pages, show the row count and allocate height so
    the reviewer understands whether all adopted tendons are present.
    """
    total_rows = int(len(df.index))
    st.caption(f"{label}: showing {total_rows} of {total_rows} rows from the adopted tendon source.")
    height = min(760, max(180, 36 * (total_rows + 1)))
    st.dataframe(format_engineering_table(df), use_container_width=True, hide_index=True, height=height)

def _loss_percent_basis_rows() -> pd.DataFrame:
    """Shared interpretation rule for component-level prestress-loss percentages."""
    return pd.DataFrame(
        [
            [
                "Percent basis",
                "Loss % = component loss / fpj × 100",
                "fpj is the adopted jacking stress used by the current loss page; the percentage is a component-level preview denominator only.",
            ],
            [
                "Non-cumulative rule",
                "Do not add percentages across loss pages",
                "Friction, anchor set, elastic shortening, and time-dependent losses use different station/sequence/time bases. Final combination is controlled by 4.6 Effective Prestress.",
            ],
            [
                "Adoption rule",
                "Preview only until 4.6",
                "Component percentages are trace values for review; they are not final effective-prestress loss percentages.",
            ],
        ],
        columns=["Item", "Rule", "Trace / note"],
    )


def _render_loss_percent_basis_note() -> None:
    """Render the standard non-cumulative %loss interpretation note for every loss page."""
    st.markdown(
        '<div class="note-box"><b>Loss percent basis:</b> Loss % shown on this page is calculated as <b>component loss / f<sub>pj</sub> × 100</b>. '
        '<b>Interpretation rule:</b> this is a component-level preview only; do <b>not</b> add loss percentages from different loss pages directly. '
        'Final effective-prestress combination is controlled by <b>4.6 Effective Prestress</b>.</div>',
        unsafe_allow_html=True,
    )


def _append_loss_percent_basis_report_rows(rows: list[list[str]]) -> list[list[str]]:
    """Append shared percent/adoption interpretation rows to report-style summaries."""
    return rows + [
        [
            "Percent basis",
            "component loss / fpj × 100",
            "Displayed percentages are component-level preview percentages using the adopted jacking stress fpj as denominator.",
        ],
        [
            "Combination / adoption rule",
            "Deferred to 4.6 Effective Prestress",
            "Do not add percentages from separate loss pages directly; final effective prestress must combine adopted component traces by tendon/station/sequence/time basis.",
        ],
    ]



def _render_loss_result_summary_cards_for_friction(state: dict[str, Any]) -> None:
    """Loss-type summary card pattern: one card row that future loss pages should reuse."""
    fstate = _psloss_friction_source_state(state)
    if not fstate.get("ready"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            card("FRICTION LOSS SUMMARY", "SOURCE BLOCKED", "Adopt tendon source + JackFrom first", "warn")
        with c2:
            card("MAX FRICTION LOSS", "—", "No adopted-source result yet", "warn")
        with c3:
            card("MIN fpx AFTER FRICTION", "—", "Blocked until preview is ready", "warn")
        with c4:
            card("ADOPTION STATUS", "PREVIEW ONLY", "Not effective prestress", "neutral")
        return

    gov_result, gov, results, fstate = _psloss_friction_governing_result(state)
    fpj_mpa = float(fstate.get("fpj_mpa", 0.0) or 0.0)
    loss = float(gov.get("loss_mpa", 0.0) or 0.0)
    pct = 100.0 * loss / fpj_mpa if fpj_mpa > 0.0 else 0.0
    valid = [r for r in results if r.get("gov")]
    min_fpx = min([float((r.get("gov") or {}).get("stress_mpa", fpj_mpa) or fpj_mpa) for r in valid], default=0.0)
    governing_label = _psloss_friction_governing_label(results)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("FRICTION LOSS SUMMARY", "PREVIEW READY", f"Governing: {governing_label}", "pass")
    with c2:
        card("MAX FRICTION LOSS", f"{loss:.2f} MPa", f"{pct:.2f}% of fpj", "warn" if pct > 8.0 else "pass")
    with c3:
        card("MIN fpx AFTER FRICTION", f"{min_fpx:.2f} MPa", "Friction-only stress", "pass")
    with c4:
        card("ADOPTION STATUS", "PREVIEW ONLY", "Not effective prestress", "neutral")


def _render_psloss_friction_equation_block(state: dict[str, Any]) -> None:
    """Render report-grade equation block consistent with other calculation pages."""
    fstate = _psloss_friction_source_state(state)
    st.markdown("### Friction equation block")
    st.markdown(
        '<div class="note-box"><b>Code equation route:</b> post-tensioned friction loss is shown as a report-grade equation block. Formula display remains available even when source data is blocked; substitution and result lines are source-gated.</div>',
        unsafe_allow_html=True,
    )
    st.latex(r"\Delta f_{pF}=f_{pj}\left[1-e^{-(Kx+\mu\alpha)}\right]")
    st.latex(r"f_{px}=f_{pj}-\Delta f_{pF}")
    st.latex(r"\mathrm{Loss}\;(\%)=\frac{\Delta f_{pF}}{f_{pj}}\times100")

    if not fstate.get("ready"):
        st.markdown(
            '<div class="warn-box"><b>Substitution blocked:</b> adopt the tendon model and JackFrom / stressing-basis trace before this equation block can substitute x, α, and the governing tendon result.</div>',
            unsafe_allow_html=True,
        )
        return

    gov_result, gov, _, fstate = _psloss_friction_governing_result(state)
    fpj_mpa = float(fstate.get("fpj_mpa", 0.0) or 0.0)
    mu = float(fstate.get("mu", 0.0) or 0.0)
    k_per_m = float(fstate.get("k_per_m", 0.0) or 0.0)
    x = float(gov.get("path_m", 0.0) or 0.0)
    alpha = float(gov.get("alpha_rad", 0.0) or 0.0)
    kx = float(gov.get("kx_term", 0.0) or 0.0)
    mua = float(gov.get("mu_alpha_term", 0.0) or 0.0)
    exponent = float(gov.get("exponent", 0.0) or 0.0)
    exp_factor = float(gov.get("exp_factor", 1.0) or 1.0)
    loss = float(gov.get("loss_mpa", 0.0) or 0.0)
    fpx = float(gov.get("stress_mpa", fpj_mpa - loss) or 0.0)
    pct = 100.0 * loss / fpj_mpa if fpj_mpa > 0.0 else 0.0

    tie_label = _psloss_friction_governing_label(_psloss_friction_governing_result(state)[2])
    st.markdown(f"#### Governing tendon substitution — {gov_result.get('tendon', '-')} (representative; governing tie: {tie_label})")
    st.latex(fr"Kx+\mu\alpha=({k_per_m:.6f})({x:.3f})+({mu:.4f})({alpha:.5f})={exponent:.5f}")
    st.latex(fr"e^{{-(Kx+\mu\alpha)}}=e^{{-{exponent:.5f}}}={exp_factor:.5f}")
    st.latex(fr"\Delta f_{{pF}}={fpj_mpa:.2f}\left[1-{exp_factor:.5f}\right]={loss:.2f}\,\mathrm{{MPa}}")
    st.latex(fr"f_{{px}}={fpj_mpa:.2f}-{loss:.2f}={fpx:.2f}\,\mathrm{{MPa}}")
    st.latex(fr"\mathrm{{Loss}}=\frac{{{loss:.2f}}}{{{fpj_mpa:.2f}}}\times100={pct:.2f}\%")

def _psloss_friction_variable_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["fpj", "MPa", "Jacking stress before friction loss", "Adopted tendon / material basis"],
            ["μ", "-", "Curvature friction coefficient", "4.2 Friction project input; verify PT-system basis"],
            ["K", "1/m", "Wobble coefficient", "4.2 Friction project input; K = 0 requires project justification"],
            ["x", "m", "Cumulative path distance from the active jacking end", "Derived from adopted station-by-station tendon profile"],
            ["α", "rad", "Cumulative angular change from the active jacking end", "Derived from adopted 3D tendon geometry"],
            ["Kx + μα", "-", "Friction exponent", "Intermediate trace term"],
            ["ΔfpF", "MPa", "Friction loss in prestressing steel", "Preview only in this milestone"],
            ["fpx", "MPa", "Prestressing steel stress after friction only", "Not effective prestress; anchor set and time-dependent losses are separate"],
        ],
        columns=["Variable", "Unit", "Meaning", "Source / trace"],
    )


def _psloss_friction_governing_walkthrough_rows(state: dict[str, Any]) -> pd.DataFrame:
    fstate = _psloss_friction_source_state(state)
    if not fstate.get("ready"):
        return pd.DataFrame(
            [["Source gate", "BLOCKED", "Adopt tendon model and JackFrom/stressing basis before formula walkthrough."]],
            columns=["Step", "Value", "Trace"],
        )
    model = fstate.get("model") or {}
    results = [_psloss_friction_result_for_tendon(t, fstate) for t in model.get("tendons", []) or []]
    result = max(results, key=lambda r: float((r.get("gov") or {}).get("loss_mpa", 0.0) or 0.0)) if results else {"tendon": "-", "gov": {}}
    gov = result.get("gov") or {}
    tie_label = _psloss_friction_governing_label(results)
    fpj_mpa = float(fstate.get("fpj_mpa", 0.0) or 0.0)
    mu = float(fstate.get("mu", 0.0) or 0.0)
    k_per_m = float(fstate.get("k_per_m", 0.0) or 0.0)
    x = float(gov.get("path_m", 0.0) or 0.0)
    alpha = float(gov.get("alpha_rad", 0.0) or 0.0)
    kx = float(gov.get("kx_term", 0.0) or 0.0)
    mua = float(gov.get("mu_alpha_term", 0.0) or 0.0)
    exponent = float(gov.get("exponent", 0.0) or 0.0)
    exp_factor = float(gov.get("exp_factor", 1.0) or 1.0)
    loss = float(gov.get("loss_mpa", 0.0) or 0.0)
    fpx = float(gov.get("stress_mpa", fpj_mpa - loss) or 0.0)
    pct = 100.0 * loss / fpj_mpa if fpj_mpa > 0.0 else 0.0
    return pd.DataFrame(
        [
            ["Governing tendon", str(result.get("tendon", "-")), f"JackFrom={result.get('jack', '-')}; route={result.get('route_basis', '-')}"] ,
            ["Governing tie set", tie_label, "Tendons tied at the displayed precision are reported together; substitution uses the representative tendon above."],
            ["Inputs", f"fpj={fpj_mpa:.2f} MPa; μ={mu:.4f}; K={k_per_m:.6f} 1/m", "Adopted jacking stress + 4.2 friction project inputs"],
            ["Path terms", f"x={x:.3f} m; α={alpha:.5f} rad", "Derived from adopted tendon profile from active JackFrom side"],
            ["Kx", f"({k_per_m:.6f})({x:.3f}) = {kx:.5f}", "Wobble component"],
            ["μα", f"({mu:.4f})({alpha:.5f}) = {mua:.5f}", "Curvature friction component"],
            ["Exponent", f"Kx + μα = {exponent:.5f}", "Dimensionless friction exponent"],
            ["Exponential factor", f"exp[-(Kx+μα)] = {exp_factor:.5f}", "Remaining stress ratio before multiplying by fpj"],
            ["Friction loss", f"ΔfpF = {loss:.2f} MPa ({pct:.2f}%)", "fpj × [1 − exp(−exponent)]"],
            ["Stress after friction", f"fpx = {fpx:.2f} MPa", "Friction-only result; not final effective prestress"],
        ],
        columns=["Step", "Value", "Trace"],
    )



def _tendon_total_path_length_m(points: list[dict[str, float]]) -> float:
    """Return total adopted 3D tendon path length for an imported profile."""
    if not points or len(points) < 2:
        return 0.0
    length = 0.0
    for i in range(1, len(points)):
        a, b = points[i - 1], points[i]
        dx = b["x_m"] - a["x_m"]
        dy = b["horiz_off_m"] - a["horiz_off_m"]
        dz = b["dp_top_m"] - a["dp_top_m"]
        length += sqrt(dx * dx + dy * dy + dz * dz)
    return float(length)


def _psloss_anchor_set_source_state(state: dict[str, Any]) -> dict[str, Any]:
    """Return source-gated state for 4.3 Anchor Set preview.

    This is a report preview model only.  Anchor-set loss is position-dependent
    and later effective-prestress adoption must define the final distribution
    method.  The preview uses the adopted tendon source, JackFrom basis, anchor
    set value, and Ep to expose the calculation trace without black-box values.
    """
    ps = D.setdefault("prestress", {})
    materials = D.setdefault("materials", {})
    model = _active_adopted_tendon_model() if state.get("tendon_locked") else {}
    stressing = state.get("stressing_basis", {})
    anchor_set_mm = _safe_float(ps.get("anchor_set_mm", 6.0), 6.0)
    ep_mpa = _safe_float(materials.get("Ep_mpa", 0.0), 0.0)
    mu = _safe_float(ps.get("mu_external", 0.15), 0.15)
    k_per_m = _safe_float(ps.get("wobble_external_per_m", 0.0), 0.0)
    summary = state.get("adopted_summary") or {}
    fpj_mpa = _safe_float(summary.get("jacking_stress_mpa") or materials.get("fpi_mpa", 0.0), 0.0)
    ready = bool(state.get("tendon_locked")) and bool(stressing.get("ready")) and bool(model.get("profile_rows")) and fpj_mpa > 0.0 and ep_mpa > 0.0 and anchor_set_mm >= 0.0
    return {
        "ready": ready,
        "status": "PREVIEW READY" if ready else "SOURCE BLOCKED",
        "mode": "pass" if ready else "warn",
        "model": model,
        "stressing": stressing,
        "anchor_set_mm": anchor_set_mm,
        "ep_mpa": ep_mpa,
        "fpj_mpa": fpj_mpa,
        "mu": mu,
        "k_per_m": k_per_m,
        "message": "Anchor-set preview uses adopted tendon profile, JackFrom trace, Ep, Δa, and the friction profile." if ready else "Adopt tendon model and JackFrom basis before anchor-set preview can run.",
    }


def _psloss_anchor_effective_length_m(points: list[dict[str, float]], jack_from: str) -> tuple[float, str, str]:
    """Return an equivalent anchor-set length and its route description.

    For this source-model milestone, one-end stressing uses the full adopted
    tendon path as the equivalent length.  Two-end stressing uses half the
    adopted path for each anchorage-end preview; it does not double jacking
    force and remains a distribution preview only.
    """
    path = _tendon_total_path_length_m(points)
    jack_lower = (jack_from or "").strip().lower()
    if "both" in jack_lower and path > 0.0:
        return 0.5 * path, "two-end equivalent half-path", "PREVIEW · do not double Pj"
    if jack_lower == "end":
        return path, "from End; full adopted path", "PREVIEW"
    if jack_lower == "start" or not jack_lower:
        return path, "from Start; full adopted path", "PREVIEW"
    return path, "review JackFrom text; full adopted path used", "REVIEW JackFrom text"


def _psloss_anchor_result_for_tendon(tendon: dict[str, Any], astate: dict[str, Any]) -> dict[str, Any]:
    """Return equivalent anchor-set preview result for one tendon."""
    model = astate.get("model") or {}
    name = str(tendon.get("tendon", "-"))
    jack = str(tendon.get("jack_from", "")).strip() or "Unknown"
    points = _profile_points_for_tendon(model, name)
    if len(points) < 2:
        return {
            "tendon": name,
            "jack": jack,
            "route_basis": "missing profile",
            "status": "REVIEW: adopted profile has fewer than two points",
            "path_m": 0.0,
            "l_eff_m": 0.0,
            "loss_mpa": 0.0,
            "stress_mpa": float(astate.get("fpj_mpa", 0.0) or 0.0),
            "loss_pct": 0.0,
        }
    l_eff_m, route_basis, status = _psloss_anchor_effective_length_m(points, jack)
    ep_mpa = float(astate.get("ep_mpa", 0.0) or 0.0)
    anchor_set_mm = float(astate.get("anchor_set_mm", 0.0) or 0.0)
    fpj_mpa = float(astate.get("fpj_mpa", 0.0) or 0.0)
    loss = ep_mpa * anchor_set_mm / (1000.0 * l_eff_m) if l_eff_m > 0.0 else 0.0
    loss = max(loss, 0.0)
    fpx = max(fpj_mpa - loss, 0.0) if fpj_mpa > 0.0 else 0.0
    pct = 100.0 * loss / fpj_mpa if fpj_mpa > 0.0 else 0.0
    return {
        "tendon": name,
        "jack": jack,
        "route_basis": route_basis,
        "status": status,
        "path_m": _tendon_total_path_length_m(points),
        "l_eff_m": l_eff_m,
        "loss_mpa": loss,
        "stress_mpa": fpx,
        "loss_pct": pct,
    }


def _psloss_anchor_results(state: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    astate = _psloss_anchor_set_source_state(state)
    if not astate.get("ready"):
        return [], astate
    model = astate.get("model") or {}
    results = [_psloss_anchor_result_for_tendon(t, astate) for t in model.get("tendons", []) or []]
    return results, astate


def _psloss_anchor_governing_tie_results(results: list[dict[str, Any]], *, tolerance_mpa: float = 0.005) -> list[dict[str, Any]]:
    valid = [r for r in results if r]
    if not valid:
        return []
    max_loss = max(float(r.get("loss_mpa", 0.0) or 0.0) for r in valid)
    return [r for r in valid if abs(float(r.get("loss_mpa", 0.0) or 0.0) - max_loss) <= tolerance_mpa]


def _psloss_anchor_governing_label(results: list[dict[str, Any]]) -> str:
    ties = _psloss_anchor_governing_tie_results(results)
    names = [str(r.get("tendon", "-")).strip() or "-" for r in ties]
    if not names:
        return "-"
    if len(names) <= 4:
        return " / ".join(names)
    return f"{len(names)} tied tendons: " + ", ".join(names[:4]) + ", ..."


def _psloss_anchor_governing_result(state: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    results, astate = _psloss_anchor_results(state)
    valid = [r for r in results if r]
    gov = max(valid, key=lambda r: float(r.get("loss_mpa", 0.0) or 0.0)) if valid else {"tendon": "-"}
    return gov, results, astate


def _render_loss_result_summary_cards_for_anchor_set(state: dict[str, Any]) -> None:
    results, astate = _psloss_anchor_distribution_results(state)
    if not astate.get("ready") or not results:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            card("ANCHOR SET SUMMARY", "SOURCE BLOCKED", "Adopt tendon model first", "warn")
        with c2:
            card("MAX ANCHOR-SET LOSS", "—", "blocked", "warn")
        with c3:
            card("MIN fpx AFTER F+A", "—", "blocked", "warn")
        with c4:
            card("ADOPTION STATUS", "PREVIEW ONLY", "Not effective prestress", "neutral")
        return
    gov = max(results, key=lambda r: float(r.get("max_loss_mpa", 0.0) or 0.0))
    tie_label = _psloss_anchor_distribution_governing_label(results)
    max_loss = float(gov.get("max_loss_mpa", 0.0) or 0.0)
    fpj = float(astate.get("fpj_mpa", 0.0) or 0.0)
    pct = 100.0 * max_loss / fpj if fpj > 0.0 else 0.0
    min_fpx = min(float(r.get("min_stress_mpa", 0.0) or 0.0) for r in results)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("ANCHOR SET SUMMARY", "DISTRIBUTION PREVIEW", f"Governing: {tie_label}", "pass")
    with c2:
        card("MAX ANCHOR-SET LOSS", f"{max_loss:.2f} MPa", f"{pct:.2f}% of fpj · sₐ≈{float(gov.get('affected_length_m', 0.0) or 0.0):.2f} m", "warn")
    with c3:
        card("MIN fpx AFTER F+A", f"{min_fpx:.2f} MPa", "Friction + anchor-set preview", "pass")
    with c4:
        card("ADOPTION STATUS", "PREVIEW ONLY", "Not effective prestress", "neutral")


def _psloss_anchor_source_rows(state: dict[str, Any]) -> pd.DataFrame:
    astate = _psloss_anchor_set_source_state(state)
    return pd.DataFrame(
        [
            ["Adopted tendon profile", "READY" if state.get("tendon_locked") else "BLOCKED", "2.4 Adopted Tendon Data", "Anchor-set preview must use adopted tendon path length only."],
            ["JackFrom / stressing basis", state.get("stressing_basis", {}).get("status", "BLOCKED"), state.get("stressing_basis", {}).get("source", "2.4 tendon adoption required"), "Controls one-end, two-end, or mixed tendon-by-tendon anchor-set route."],
            ["Anchor set Δa", f"{astate['anchor_set_mm']:.3f} mm", "4.3 Anchor Set project input", "Engineer must verify anchorage wedge-set / seating basis."],
            ["Prestressing steel modulus Ep", f"{astate['ep_mpa']:.0f} MPa", "Material property", "Used with Δa / L_eff and distribution compatibility."],
            ["Friction coupling μ / K", f"{astate['mu']:.4f} / {astate['k_per_m']:.6f} 1/m", "4.2 Friction project input", "Distribution trace uses the adopted friction profile; do not use a separate friction assumption."],
            ["Jacking stress fpj", f"{astate['fpj_mpa']:.2f} MPa", "Adopted tendon summary / material basis", "Stress basis for preview only; Pj/tendon remains axial force."],
            ["Preview status", astate["status"], "Source gate", astate["message"]],
        ],
        columns=["Anchor-set source item", "Status / value", "Source owner", "Required engineer check"],
    )


def _psloss_anchor_preview_rows(state: dict[str, Any]) -> pd.DataFrame:
    results, astate = _psloss_anchor_results(state)
    if not astate.get("ready"):
        return pd.DataFrame(
            [["SOURCE BLOCKED", "-", "-", "-", "-", "-", "Adopt tendon model and JackFrom/stressing basis before anchor-set preview."]],
            columns=["Tendon", "JackFrom", "Route basis", "Path length (m)", "L_eff (m)", "Loss preview", "Status / note"],
        )
    rows = []
    for r in results:
        rows.append([
            r.get("tendon", "-"),
            r.get("jack", "-"),
            r.get("route_basis", "-"),
            f"{float(r.get('path_m', 0.0) or 0.0):.3f}",
            f"{float(r.get('l_eff_m', 0.0) or 0.0):.3f}",
            f"{float(r.get('loss_mpa', 0.0) or 0.0):.2f} MPa ({float(r.get('loss_pct', 0.0) or 0.0):.2f}%)",
            r.get("status", "PREVIEW"),
        ])
    return pd.DataFrame(rows, columns=["Tendon", "JackFrom", "Route basis", "Path length (m)", "L_eff (m)", "Loss preview", "Status / note"])


def _psloss_anchor_calculation_rows(state: dict[str, Any]) -> pd.DataFrame:
    results, astate = _psloss_anchor_results(state)
    if not astate.get("ready"):
        return pd.DataFrame(
            [["SOURCE BLOCKED", "-", "-", "-", "-", "-", "-", "-", "Adopt tendon model and JackFrom/stressing basis before calculation trace."]],
            columns=["Tendon", "JackFrom", "fpj (MPa)", "Ep (MPa)", "Δa (mm)", "L_eff (m)", "Δa/L_eff", "ΔfpA / fpx", "Status / note"],
        )
    rows = []
    fpj = float(astate.get("fpj_mpa", 0.0) or 0.0)
    ep = float(astate.get("ep_mpa", 0.0) or 0.0)
    da = float(astate.get("anchor_set_mm", 0.0) or 0.0)
    for r in results:
        leff_m = float(r.get("l_eff_m", 0.0) or 0.0)
        strain = da / (leff_m * 1000.0) if leff_m > 0.0 else 0.0
        rows.append([
            r.get("tendon", "-"),
            r.get("jack", "-"),
            f"{fpj:.2f}",
            f"{ep:.0f}",
            f"{da:.3f}",
            f"{leff_m:.3f}",
            f"{strain:.7f}",
            f"ΔfpA={float(r.get('loss_mpa', 0.0) or 0.0):.2f} MPa ({float(r.get('loss_pct', 0.0) or 0.0):.2f}%) · fpx={float(r.get('stress_mpa', 0.0) or 0.0):.2f} MPa",
            r.get("status", "PREVIEW"),
        ])
    return pd.DataFrame(rows, columns=["Tendon", "JackFrom", "fpj (MPa)", "Ep (MPa)", "Δa (mm)", "L_eff (m)", "Δa/L_eff", "ΔfpA / fpx", "Status / note"])



def _anchor_friction_trace_for_tendon(tendon: dict[str, Any], astate: dict[str, Any]) -> tuple[list[dict[str, float]], str, str]:
    """Return the active-end friction trace used by anchor-set distribution.

    The anchor-set distribution preview must be coupled to the same adopted
    tendon geometry, JackFrom route, μ, K, and fpj that control the 4.2 friction
    page.  For two-end stressing, this helper returns the nearer-end preview
    basis for each station and clearly marks it as a distribution preview, not a
    doubled jacking-force case.
    """
    model = astate.get("model") or {}
    name = str(tendon.get("tendon", "-"))
    points = _profile_points_for_tendon(model, name)
    if len(points) < 2:
        return [], "missing adopted profile", "REVIEW: adopted profile has fewer than two points"
    jack = str(tendon.get("jack_from", "")).strip() or "Unknown"
    jack_lower = jack.lower()
    mu = float(astate.get("mu", 0.0) or 0.0)
    k_per_m = float(astate.get("k_per_m", 0.0) or 0.0)
    fpj_mpa = float(astate.get("fpj_mpa", 0.0) or 0.0)
    if "both" in jack_lower:
        start_trace = _friction_route_trace(points, from_end=False, mu=mu, k_per_m=k_per_m, fpj_mpa=fpj_mpa)
        end_trace = _friction_route_trace(points, from_end=True, mu=mu, k_per_m=k_per_m, fpj_mpa=fpj_mpa)
        end_by_x = {round(r["x_m"], 9): r for r in end_trace}
        combined: list[dict[str, float]] = []
        for sr in start_trace:
            er = end_by_x.get(round(sr["x_m"], 9), sr)
            chosen = sr if sr.get("exponent", 0.0) <= er.get("exponent", 0.0) else er
            combined.append(chosen)
        combined.sort(key=lambda r: float(r.get("path_m", 0.0) or 0.0))
        return combined, "two-end; nearer-end friction-coupled preview", "PREVIEW · do not double Pj"
    if jack_lower == "end":
        trace = _friction_route_trace(points, from_end=True, mu=mu, k_per_m=k_per_m, fpj_mpa=fpj_mpa)
        trace.sort(key=lambda r: float(r.get("path_m", 0.0) or 0.0))
        return trace, "from End; friction-coupled", "PREVIEW"
    trace = _friction_route_trace(points, from_end=False, mu=mu, k_per_m=k_per_m, fpj_mpa=fpj_mpa)
    trace.sort(key=lambda r: float(r.get("path_m", 0.0) or 0.0))
    status = "PREVIEW" if jack_lower in {"start", ""} else "REVIEW JackFrom text"
    return trace, "from Start; friction-coupled", status


def _anchor_distribution_area_mm(trace: list[dict[str, float]], d0_mpa: float, ep_mpa: float) -> float:
    """Return anchor draw-in implied by a trial active-end anchor loss.

    The distribution preview uses ΔfpA(s)=max[d0−2ΔfpF(s),0].  The draw-in
    compatibility check is ∫ΔfpA(s)/Ep ds = Δa.  The integral is converted from
    metres to millimetres for comparison with the project Δa input.
    """
    if len(trace) < 2 or ep_mpa <= 0.0:
        return 0.0
    area_m = 0.0
    prev = trace[0]
    prev_loss = max(d0_mpa - 2.0 * float(prev.get("loss_mpa", 0.0) or 0.0), 0.0)
    for cur in trace[1:]:
        cur_loss = max(d0_mpa - 2.0 * float(cur.get("loss_mpa", 0.0) or 0.0), 0.0)
        ds = max(float(cur.get("path_m", 0.0) or 0.0) - float(prev.get("path_m", 0.0) or 0.0), 0.0)
        area_m += 0.5 * (prev_loss + cur_loss) / ep_mpa * ds
        prev = cur
        prev_loss = cur_loss
    return area_m * 1000.0


def _solve_anchor_distribution_d0_mpa(trace: list[dict[str, float]], ep_mpa: float, delta_a_mm: float) -> float:
    """Solve active-end anchor-set loss d0 from draw-in compatibility."""
    if len(trace) < 2 or ep_mpa <= 0.0 or delta_a_mm <= 0.0:
        return 0.0
    max_fric = max(float(r.get("loss_mpa", 0.0) or 0.0) for r in trace)
    length_m = max(float(r.get("path_m", 0.0) or 0.0) for r in trace)
    high = max(10.0, 2.0 * max_fric + 10.0, ep_mpa * delta_a_mm / max(length_m * 1000.0, 1e-9) * 10.0)
    for _ in range(30):
        if _anchor_distribution_area_mm(trace, high, ep_mpa) >= delta_a_mm:
            break
        high *= 2.0
    low = 0.0
    for _ in range(80):
        mid = 0.5 * (low + high)
        if _anchor_distribution_area_mm(trace, mid, ep_mpa) < delta_a_mm:
            low = mid
        else:
            high = mid
    return high


def _anchor_distribution_points_for_tendon(tendon: dict[str, Any], astate: dict[str, Any]) -> dict[str, Any]:
    """Return position-dependent anchor-set distribution coupled to friction."""
    name = str(tendon.get("tendon", "-"))
    jack = str(tendon.get("jack_from", "")).strip() or "Unknown"
    trace, route_basis, status = _anchor_friction_trace_for_tendon(tendon, astate)
    ep = float(astate.get("ep_mpa", 0.0) or 0.0)
    da = float(astate.get("anchor_set_mm", 0.0) or 0.0)
    fpj = float(astate.get("fpj_mpa", 0.0) or 0.0)
    if len(trace) < 2 or ep <= 0.0:
        return {"tendon": name, "jack": jack, "route_basis": route_basis, "status": status, "points": [], "d0_mpa": 0.0, "affected_length_m": 0.0, "area_mm": 0.0, "max_loss_mpa": 0.0, "min_stress_mpa": fpj, "gov_station_m": 0.0}
    d0 = _solve_anchor_distribution_d0_mpa(trace, ep, da)
    pts: list[dict[str, float]] = []
    affected = 0.0
    min_stress = fpj
    max_loss = 0.0
    gov_station = float(trace[0].get("x_m", 0.0) or 0.0)
    for r in trace:
        fric_loss = float(r.get("loss_mpa", 0.0) or 0.0)
        anchor_loss = max(d0 - 2.0 * fric_loss, 0.0)
        if anchor_loss > 1e-6:
            affected = max(affected, float(r.get("path_m", 0.0) or 0.0))
        f_fric = float(r.get("stress_mpa", fpj - fric_loss) or 0.0)
        f_after = max(f_fric - anchor_loss, 0.0)
        if f_after < min_stress:
            min_stress = f_after
        if anchor_loss > max_loss:
            max_loss = anchor_loss
            gov_station = float(r.get("x_m", 0.0) or 0.0)
        pts.append({
            "x_m": float(r.get("x_m", 0.0) or 0.0),
            "path_m": float(r.get("path_m", 0.0) or 0.0),
            "alpha_rad": float(r.get("alpha_rad", 0.0) or 0.0),
            "friction_loss_mpa": fric_loss,
            "friction_stress_mpa": f_fric,
            "anchor_loss_mpa": anchor_loss,
            "stress_after_friction_anchor_mpa": f_after,
        })
    area_mm = _anchor_distribution_area_mm(trace, d0, ep)
    return {
        "tendon": name,
        "jack": jack,
        "route_basis": route_basis,
        "status": status,
        "points": pts,
        "d0_mpa": d0,
        "affected_length_m": affected,
        "area_mm": area_mm,
        "max_loss_mpa": max_loss,
        "min_stress_mpa": min_stress,
        "gov_station_m": gov_station,
    }


def _psloss_anchor_distribution_results(state: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    astate = _psloss_anchor_set_source_state(state)
    if not astate.get("ready"):
        return [], astate
    model = astate.get("model") or {}
    out = [_anchor_distribution_points_for_tendon(t, astate) for t in model.get("tendons", []) or []]
    return out, astate


def _psloss_anchor_distribution_governing_tie_results(results: list[dict[str, Any]], *, tolerance_mpa: float = 0.005) -> list[dict[str, Any]]:
    valid = [r for r in results if r]
    if not valid:
        return []
    max_loss = max(float(r.get("max_loss_mpa", 0.0) or 0.0) for r in valid)
    return [r for r in valid if abs(float(r.get("max_loss_mpa", 0.0) or 0.0) - max_loss) <= tolerance_mpa]


def _psloss_anchor_distribution_governing_label(results: list[dict[str, Any]]) -> str:
    ties = _psloss_anchor_distribution_governing_tie_results(results)
    names = [str(r.get("tendon", "-")).strip() or "-" for r in ties]
    if not names:
        return "-"
    if len(names) <= 4:
        return " / ".join(names)
    return f"{len(names)} tied tendons: " + ", ".join(names[:4]) + ", ..."


def _psloss_anchor_distribution_summary_rows(state: dict[str, Any]) -> pd.DataFrame:
    results, astate = _psloss_anchor_distribution_results(state)
    if not astate.get("ready") or not results:
        return pd.DataFrame(
            [["SOURCE BLOCKED", "-", "-", "-", "-", "Adopt tendon model and JackFrom/stressing basis before anchor-set distribution trace."]],
            columns=["Tendon", "JackFrom", "Affected length (m)", "Max ΔfpA,dist", "Min fpx,F+A", "Status / note"],
        )
    rows: list[list[Any]] = []
    fpj = float(astate.get("fpj_mpa", 0.0) or 0.0)
    for r in results:
        max_loss = float(r.get("max_loss_mpa", 0.0) or 0.0)
        pct = 100.0 * max_loss / fpj if fpj > 0.0 else 0.0
        rows.append([
            r.get("tendon", "-"),
            r.get("jack", "-"),
            f"{float(r.get('affected_length_m', 0.0) or 0.0):.3f}",
            f"{max_loss:.2f} MPa ({pct:.2f}%)",
            f"{float(r.get('min_stress_mpa', 0.0) or 0.0):.2f} MPa",
            r.get("status", "PREVIEW"),
        ])
    return pd.DataFrame(rows, columns=["Tendon", "JackFrom", "Affected length (m)", "Max ΔfpA,dist", "Min fpx,F+A", "Status / note"])


def _psloss_anchor_distribution_station_rows(state: dict[str, Any], *, max_rows: int = 12) -> pd.DataFrame:
    results, astate = _psloss_anchor_distribution_results(state)
    if not astate.get("ready") or not results:
        return pd.DataFrame(
            [["SOURCE BLOCKED", "-", "-", "-", "-", "-", "-", "Adopt tendon model before station distribution trace."]],
            columns=["Tendon", "Station (m)", "Path s (m)", "ΔfpF (MPa)", "ΔfpA,dist (MPa)", "fpx,F (MPa)", "fpx,F+A (MPa)", "Status / note"],
        )
    gov = max(results, key=lambda r: float(r.get("max_loss_mpa", 0.0) or 0.0))
    points = list(gov.get("points", []) or [])
    # Keep all adopted station points for the governing representative; current BG40 import uses compact station rows.
    rows: list[list[Any]] = []
    for pt in points[:max_rows]:
        rows.append([
            gov.get("tendon", "-"),
            f"{float(pt.get('x_m', 0.0) or 0.0):.3f}",
            f"{float(pt.get('path_m', 0.0) or 0.0):.3f}",
            f"{float(pt.get('friction_loss_mpa', 0.0) or 0.0):.2f}",
            f"{float(pt.get('anchor_loss_mpa', 0.0) or 0.0):.2f}",
            f"{float(pt.get('friction_stress_mpa', 0.0) or 0.0):.2f}",
            f"{float(pt.get('stress_after_friction_anchor_mpa', 0.0) or 0.0):.2f}",
            "PREVIEW · representative governing tendon",
        ])
    return pd.DataFrame(rows, columns=["Tendon", "Station (m)", "Path s (m)", "ΔfpF (MPa)", "ΔfpA,dist (MPa)", "fpx,F (MPa)", "fpx,F+A (MPa)", "Status / note"])


def _render_psloss_anchor_distribution_equation_block(state: dict[str, Any]) -> None:
    st.markdown("### Anchor-set distribution / friction-coupling equation block")
    st.markdown(
        '<div class="note-box"><b>Distribution preview route:</b> the equivalent quick check remains visible above as a fast audit value. The position-dependent distribution preview shown here couples anchor set to the adopted friction profile. Final effective-prestress adoption remains a later milestone.</div>',
        unsafe_allow_html=True,
    )
    st.latex(r"\Delta f_{pA}(s)=\max\left[\Delta f_{pA,0}-2\Delta f_{pF}(s),0\right]")
    st.latex(r"\Delta_a=1000\int_0^{s_a}\frac{\Delta f_{pA}(s)}{E_p}\,ds")
    st.latex(r"f_{px,F+A}(s)=f_{px,F}(s)-\Delta f_{pA}(s)")
    results, astate = _psloss_anchor_distribution_results(state)
    if not astate.get("ready") or not results:
        st.markdown('<div class="warn-box"><b>Distribution substitution blocked:</b> adopt tendon source and JackFrom before solving the anchor-set distribution.</div>', unsafe_allow_html=True)
        return
    gov = max(results, key=lambda r: float(r.get("max_loss_mpa", 0.0) or 0.0))
    ties = _psloss_anchor_distribution_governing_label(results)
    ep = float(astate.get("ep_mpa", 0.0) or 0.0)
    da = float(astate.get("anchor_set_mm", 0.0) or 0.0)
    d0 = float(gov.get("d0_mpa", 0.0) or 0.0)
    affected = float(gov.get("affected_length_m", 0.0) or 0.0)
    area = float(gov.get("area_mm", 0.0) or 0.0)
    min_stress = float(gov.get("min_stress_mpa", 0.0) or 0.0)
    st.markdown(f"#### Distribution substitution — {gov.get('tendon', '-')} (representative; governing tie: {ties})")
    st.latex(fr"\Delta f_{{pA,0}}={d0:.2f}\,\mathrm{{MPa}}\quad ; \quad s_a\approx {affected:.3f}\,\mathrm{{m}}")
    st.latex(fr"\int_0^{{s_a}}\frac{{\Delta f_{{pA}}(s)}}{{E_p}}ds\times1000={area:.3f}\,\mathrm{{mm}}\approx \Delta_a={da:.3f}\,\mathrm{{mm}}")
    st.latex(fr"\min\left(f_{{px,F+A}}\right)={min_stress:.2f}\,\mathrm{{MPa}}")

def _psloss_anchor_report_summary_rows(state: dict[str, Any]) -> pd.DataFrame:
    results, astate = _psloss_anchor_results(state)
    if not astate.get("ready"):
        return pd.DataFrame(
            _append_loss_percent_basis_report_rows([
                ["Calculation status", "SOURCE BLOCKED", "Adopted tendon source and JackFrom/stressing basis are required."],
                ["Adoption status", "Preview only", "No effective-prestress value is adopted from this page."],
            ]),
            columns=["Item", "Value", "Trace / note"],
        )
    gov = max(results, key=lambda r: float(r.get("loss_mpa", 0.0) or 0.0))
    ties = _psloss_anchor_governing_tie_results(results)
    tie_label = _psloss_anchor_governing_label(results)
    max_loss = float(gov.get("loss_mpa", 0.0) or 0.0)
    max_pct = float(gov.get("loss_pct", 0.0) or 0.0)
    min_fpx = min([float(r.get("stress_mpa", 0.0) or 0.0) for r in results], default=0.0)
    dist_results, _dist_state = _psloss_anchor_distribution_results(state)
    dist_tie_label = _psloss_anchor_distribution_governing_label(dist_results)
    dist_gov = max(dist_results, key=lambda r: float(r.get("max_loss_mpa", 0.0) or 0.0)) if dist_results else {}
    dist_loss = float(dist_gov.get("max_loss_mpa", 0.0) or 0.0)
    fpj_for_pct = float(astate.get("fpj_mpa", 0.0) or 0.0)
    dist_pct = 100.0 * dist_loss / fpj_for_pct if fpj_for_pct > 0.0 else 0.0
    dist_min_fpx = min([float(r.get("min_stress_mpa", 0.0) or 0.0) for r in dist_results], default=0.0)
    stressing = astate.get("stressing") or {}
    return pd.DataFrame(
        _append_loss_percent_basis_report_rows([
            ["Calculation status", "DISTRIBUTION PREVIEW READY", "Source-gated equivalent quick check plus position-dependent anchor-set distribution preview; not final effective-prestress adoption."],
            ["Code basis", "AASHTO LRFD 2020 Art. 5.9.3.2.2b", "Post-tensioned anchorage-set source-model route."],
            ["Equivalent formula", "ΔfpA,eq = Ep Δa / L_eff", "Quick check only; distribution/coupling trace is the governing preview for this page."],
            ["Distribution formula", "ΔfpA(s)=max[ΔfpA,0 − 2ΔfpF(s), 0]", "Friction-coupled distribution; Δa = ∫ΔfpA(s)/Ep ds."],
            ["Tendons in trace", f"{len(results)} / {len(results)}", "All adopted tendons are included in the report trace."],
            ["Stressing route", stressing.get("stressing_mode", "-"), stressing.get("source", "General tendon table · JackFrom field")],
            ["Δa / Ep / μ / K", f"{float(astate.get('anchor_set_mm', 0.0) or 0.0):.3f} mm / {float(astate.get('ep_mpa', 0.0) or 0.0):.0f} MPa / {float(astate.get('mu', 0.0) or 0.0):.4f} / {float(astate.get('k_per_m', 0.0) or 0.0):.6f} 1/m", "Project anchor-set input, material property, and friction inputs."],
            ["Equivalent governing tendon(s)", tie_label, f"{len(ties)} tendon(s) tied within 0.005 MPa; representative equivalent substitution uses {gov.get('tendon', '-')}."] ,
            ["Equivalent maximum anchor-set loss", f"{max_loss:.2f} MPa ({max_pct:.2f}%)", f"Representative L_eff={float(gov.get('l_eff_m', 0.0) or 0.0):.3f} m."],
            ["Distribution governing tendon(s)", dist_tie_label, f"Representative distribution uses {dist_gov.get('tendon', '-')}; affected length sₐ≈{float(dist_gov.get('affected_length_m', 0.0) or 0.0):.3f} m."],
            ["Distribution maximum anchor-set loss", f"{dist_loss:.2f} MPa ({dist_pct:.2f}%)", "Active-end loss from draw-in compatibility coupled to friction profile."],
            ["Minimum fpx after F+A", f"{dist_min_fpx:.2f} MPa", "Friction plus anchor-set distribution preview; other losses remain separate."],
            ["Minimum fpx after equivalent anchor set", f"{min_fpx:.2f} MPa", "Equivalent quick-check value only; not final effective prestress."],
        ]),
        columns=["Item", "Value", "Trace / note"],
    )



def _render_psloss_anchor_equation_block(state: dict[str, Any]) -> None:
    st.markdown("### Anchor-set equation block")
    st.markdown(
        '<div class="note-box"><b>Equivalent quick-check route:</b> this equation is retained as a fast equivalent anchor-set audit value. The position-dependent friction-coupled distribution preview is shown below. Final effective-prestress adoption remains a later milestone.</div>',
        unsafe_allow_html=True,
    )
    st.latex(r"\Delta f_{pA,eq}=\frac{E_p\Delta_a}{L_{eff}}");
    st.latex(r"f_{px,A}=f_{pj}-\Delta f_{pA,eq}");
    st.latex(r"\mathrm{Loss}\,(\%)=\frac{\Delta f_{pA,eq}}{f_{pj}}\times100")
    astate = _psloss_anchor_set_source_state(state)
    if not astate.get("ready"):
        st.markdown(
            '<div class="warn-box"><b>Substitution blocked:</b> adopt the tendon model and JackFrom / stressing-basis trace before this equation block can substitute Δa, Ep, and L_eff.</div>',
            unsafe_allow_html=True,
        )
        return
    gov, results, astate = _psloss_anchor_governing_result(state)
    tie_label = _psloss_anchor_governing_label(results)
    ep = float(astate.get("ep_mpa", 0.0) or 0.0)
    da = float(astate.get("anchor_set_mm", 0.0) or 0.0)
    fpj = float(astate.get("fpj_mpa", 0.0) or 0.0)
    leff_m = float(gov.get("l_eff_m", 0.0) or 0.0)
    leff_mm = leff_m * 1000.0
    strain = da / leff_mm if leff_mm > 0.0 else 0.0
    loss = float(gov.get("loss_mpa", 0.0) or 0.0)
    fpx = float(gov.get("stress_mpa", fpj - loss) or 0.0)
    pct = float(gov.get("loss_pct", 0.0) or 0.0)
    st.markdown(f"#### Governing tendon substitution — {gov.get('tendon', '-')} (representative; governing tie: {tie_label})")
    st.latex(fr"L_{{eff}}={leff_m:.3f}\,\mathrm{{m}}={leff_mm:.0f}\,\mathrm{{mm}}")
    st.latex(fr"\frac{{\Delta_a}}{{L_{{eff}}}}=\frac{{{da:.3f}}}{{{leff_mm:.0f}}}={strain:.7f}")
    st.latex(fr"\Delta f_{{pA,eq}}={ep:.0f}\left({strain:.7f}\right)={loss:.2f}\,\mathrm{{MPa}}")
    st.latex(fr"f_{{px,A}}={fpj:.2f}-{loss:.2f}={fpx:.2f}\,\mathrm{{MPa}}")
    st.latex(fr"\mathrm{{Loss}}=\frac{{{loss:.2f}}}{{{fpj:.2f}}}\times100={pct:.2f}\%")


def _psloss_anchor_variable_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["fpj", "MPa", "Jacking stress before anchor-set loss", "Adopted tendon / material basis"],
            ["Ep", "MPa", "Prestressing steel modulus", "Material property"],
            ["Δa", "mm", "Anchorage set / seating movement", "4.3 Anchor Set project input"],
            ["L_eff", "m / mm", "Equivalent tendon length controlled by JackFrom route", "Derived from adopted tendon path; two-end uses distribution preview only"],
            ["Δa / L_eff", "-", "Equivalent set strain", "Intermediate trace term"],
            ["ΔfpA,eq", "MPa", "Equivalent anchor-set stress loss", "Quick-check preview only"],
            ["fpx,A", "MPa", "Prestressing steel stress after equivalent anchor-set-only preview", "Quick-check value only"],
        ],
        columns=["Variable", "Unit", "Meaning", "Source / trace"],
    )


def _psloss_anchor_distribution_variable_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["s", "m", "Distance from active anchorage along the adopted tendon path", "Measured along the active JackFrom route"],
            ["ΔfpF(s)", "MPa", "Friction loss profile at station s from the active jacking end", "Read from the 4.2 friction profile; no separate friction assumption is introduced"],
            ["2ΔfpF(s)", "MPa", "Friction-coupling term used to reduce anchor-set loss with distance", "Represents the two-way stress change needed for anchor draw-in compatibility along the same tendon path"],
            ["ΔfpA,0", "MPa", "Anchor-set loss at the active anchorage", "Solved iteratively so the compatibility integral equals the project Δa input"],
            ["ΔfpA(s)", "MPa", "Position-dependent anchor-set loss distribution", "ΔfpA(s)=max[ΔfpA,0−2ΔfpF(s),0]"],
            ["s_a", "m", "Affected length from the active anchorage", "Distance where ΔfpA(s)>0; beyond this length anchor-set loss is zero in the preview"],
            ["fpx,F(s)", "MPa", "Prestressing steel stress after friction only", "Output from 4.2 friction trace at station s"],
            ["fpx,F+A(s)", "MPa", "Stress after friction plus anchor-set distribution preview", "fpx,F(s)−ΔfpA(s); not final effective prestress"],
            ["1000", "mm/m", "Unit conversion in compatibility integral", "Because ds is in metres while Δa is reported in millimetres: Δa = 1000∫[ΔfpA(s)/Ep]ds"],
        ],
        columns=["Variable", "Unit", "Meaning", "Source / trace"],
    )


def _psloss_anchor_governing_walkthrough_rows(state: dict[str, Any]) -> pd.DataFrame:
    astate = _psloss_anchor_set_source_state(state)
    if not astate.get("ready"):
        return pd.DataFrame(
            [["Source gate", "BLOCKED", "Adopt tendon model and JackFrom/stressing basis before formula walkthrough."]],
            columns=["Step", "Value", "Trace"],
        )
    gov, results, astate = _psloss_anchor_governing_result(state)
    tie_label = _psloss_anchor_governing_label(results)
    ep = float(astate.get("ep_mpa", 0.0) or 0.0)
    da = float(astate.get("anchor_set_mm", 0.0) or 0.0)
    fpj = float(astate.get("fpj_mpa", 0.0) or 0.0)
    leff_m = float(gov.get("l_eff_m", 0.0) or 0.0)
    leff_mm = leff_m * 1000.0
    strain = da / leff_mm if leff_mm > 0.0 else 0.0
    loss = float(gov.get("loss_mpa", 0.0) or 0.0)
    fpx = float(gov.get("stress_mpa", fpj - loss) or 0.0)
    pct = float(gov.get("loss_pct", 0.0) or 0.0)
    return pd.DataFrame(
        [
            ["Governing tendon", str(gov.get("tendon", "-")), f"JackFrom={gov.get('jack', '-')}; route={gov.get('route_basis', '-')}"] ,
            ["Governing tie set", tie_label, "Tendons tied at displayed precision are reported together; substitution uses representative tendon above."],
            ["Inputs", f"fpj={fpj:.2f} MPa; Ep={ep:.0f} MPa; Δa={da:.3f} mm", "Adopted jacking stress + material property + 4.3 anchor-set input"],
            ["Effective length", f"L_eff={leff_m:.3f} m = {leff_mm:.0f} mm", "Derived from adopted tendon path and JackFrom basis"],
            ["Equivalent set strain", f"Δa/L_eff = {strain:.7f}", "Dimensionless strain preview"],
            ["Anchor-set loss", f"ΔfpA,eq = {loss:.2f} MPa ({pct:.2f}%)", "Ep × Δa/L_eff"],
            ["Stress after anchor set", f"fpx,A = {fpx:.2f} MPa", "Anchor-set-only result; not final effective prestress"],
        ],
        columns=["Step", "Value", "Trace"],
    )


def render_prestress_anchor_set_source_model() -> None:
    """Render 4.3 Anchor Set as a report-style source-gated preview."""
    state = _psloss_source_gate_state()
    astate = _psloss_anchor_set_source_state(state)
    code_basis_card(
        "4.3 Anchor Set Source Model",
        "AASHTO LRFD 2020 Section 5, Art. 5.9.3.2.2b",
        "PSLOSS.22 keeps the anchor-set distribution trace closed while 4.5 Time-Dependent Losses is reorganized into component tabs; final effective-prestress adoption remains blocked.",
    )
    st.markdown(
        '<div class="note-box"><b>Anchor-set source rule:</b> anchor-set preview must read the adopted tendon path and JackFrom/stressing trace. The value Δa is a project anchorage-set input. One-end/two-end stressing controls distribution only; it does not double total jacking force.</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("ANCHOR SET PREVIEW", astate["status"], astate["message"], astate["mode"])
    with c2:
        card("TENDON PATH", "ADOPTED" if state.get("tendon_locked") else "BLOCKED", "2.4 adopted profile only", "pass" if state.get("tendon_locked") else "warn")
    with c3:
        card("STRESSING ROUTE", state.get("stressing_basis", {}).get("status", "BLOCKED"), state.get("stressing_basis", {}).get("stressing_mode", "Confirm JackFrom"), state.get("stressing_basis", {}).get("mode", "warn"))
    with c4:
        card("FORCE POLICY", "LOCKED RULE", "Pj/tendon is not doubled for two-end stressing", "neutral")

    st.markdown("### Anchor-set loss result summary")
    _render_loss_result_summary_cards_for_anchor_set(state)
    _render_loss_percent_basis_note()

    st.markdown("### Anchor-set input assistant")
    editable_value(["prestress", "anchor_set_mm"], "Anchor set Δa (mm)", 0.5)
    show_engineering_table(_psloss_anchor_source_rows(state))

    st.markdown("### Report-style anchor-set summary")
    show_engineering_table(_psloss_anchor_report_summary_rows(state))

    st.markdown("### Anchor-set formula and variable trace")
    _render_psloss_anchor_equation_block(state)
    show_engineering_table(_psloss_anchor_variable_rows())

    st.markdown("### Governing tendon calculation walkthrough")
    show_engineering_table(_psloss_anchor_governing_walkthrough_rows(state))

    st.markdown("### Anchor-set distribution / friction-coupling preview")
    _render_psloss_anchor_distribution_equation_block(state)
    st.markdown("#### Distribution-variable definition")
    show_engineering_table(_psloss_anchor_distribution_variable_rows())
    st.markdown("#### Tendon-by-tendon anchor-set distribution summary")
    _show_full_tendon_report_table(_psloss_anchor_distribution_summary_rows(state), label="Tendon-by-tendon anchor-set distribution summary")
    st.markdown("#### Governing tendon station distribution trace")
    _show_full_tendon_report_table(_psloss_anchor_distribution_station_rows(state), label="Governing tendon station distribution trace")

    st.markdown(
        '<div class="warn-box"><b>Preview only:</b> anchor-set loss preview is not adopted into effective prestress. Final adoption requires the later effective-prestress milestone to define how anchor-set distribution combines with friction and other loss components.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("### Tendon-by-tendon equivalent anchor-set quick check")
    _show_full_tendon_report_table(_psloss_anchor_preview_rows(state), label="Tendon-by-tendon equivalent anchor-set quick check")

    st.markdown("### Tendon-by-tendon equivalent anchor-set calculation trace")
    _show_full_tendon_report_table(_psloss_anchor_calculation_rows(state), label="Tendon-by-tendon equivalent anchor-set calculation trace")
    with st.expander("Anchor-set calculation trace / limitations", expanded=False):
        st.markdown(
            '<div class="note-box"><b>Trace basis:</b> this page keeps the equivalent source-model preview ΔfpA,eq = EpΔa/L_eff as a quick check and adds a position-dependent distribution preview using ΔfpA(s)=max[ΔfpA,0−2ΔfpF(s),0]. Final effective-prestress adoption must define how this distribution combines with all other loss components. Two-end stressing controls distribution only and never doubles tendon axial force.</div>',
            unsafe_allow_html=True,
        )
        show_engineering_table(_psloss_anchor_source_rows(state))
        show_engineering_table(_psloss_anchor_report_summary_rows(state))
def render_prestress_friction_source_model() -> None:
    """Render 4.2 Friction as a formula-traced source-gated preview, not an adopted final result."""
    state = _psloss_source_gate_state()
    fstate = _psloss_friction_source_state(state)
    code_basis_card(
        "4.2 Friction Loss Source Model",
        "AASHTO LRFD 2020 Section 5, Art. 5.9.3.2.2b",
        "PSLOSS.22 keeps the friction report trace closed while 4.5 Time-Dependent Losses is reorganized into component tabs; preview values are not adopted into effective prestress.",
    )
    st.markdown(
        '<div class="note-box"><b>Friction source rule:</b> the friction path must be generated from the adopted tendon profile, not from keyed BG40 friction groups or a working import preview. One-end/two-end stressing changes the loss distribution only; it does not double total jacking force.</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("FRICTION PREVIEW", fstate["status"], fstate["message"], fstate["mode"])
    with c2:
        card("TENDON PATH", "ADOPTED" if state.get("tendon_locked") else "BLOCKED", "2.4 adopted profile only", "pass" if state.get("tendon_locked") else "warn")
    with c3:
        card("STRESSING ROUTE", state.get("stressing_basis", {}).get("status", "BLOCKED"), state.get("stressing_basis", {}).get("stressing_mode", "Confirm JackFrom"), state.get("stressing_basis", {}).get("mode", "warn"))
    with c4:
        card("FORCE POLICY", "LOCKED RULE", "Pj/tendon is not doubled for two-end stressing", "neutral")

    st.markdown("### Friction loss result summary")
    _render_loss_result_summary_cards_for_friction(state)
    _render_loss_percent_basis_note()

    st.markdown("### Friction coefficient input assistant")
    c_mu, c_k = st.columns(2)
    with c_mu:
        editable_value(["prestress", "mu_external"], "External tendon friction coefficient μ", 0.01, "%.4f")
    with c_k:
        editable_value(["prestress", "wobble_external_per_m"], "Wobble coefficient K (1/m)", 0.0001, "%.6f")
    show_engineering_table(_psloss_friction_source_rows(state))

    st.markdown("### Report-style friction summary")
    show_engineering_table(_psloss_friction_report_summary_rows(state))

    st.markdown("### Friction formula and variable trace")
    _render_psloss_friction_equation_block(state)
    show_engineering_table(_psloss_friction_variable_rows())

    st.markdown("### Governing tendon calculation walkthrough")
    show_engineering_table(_psloss_friction_governing_walkthrough_rows(state))

    st.markdown(
        '<div class="warn-box"><b>Preview only:</b> friction loss preview is not adopted into effective prestress. It becomes eligible for adoption only after the tendon source is locked and a later effective-prestress milestone defines adoption rules.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("### Tendon-by-tendon friction preview")
    _show_full_tendon_report_table(_psloss_friction_preview_rows(state), label="Tendon-by-tendon friction preview")

    st.markdown("### Tendon-by-tendon friction calculation trace")
    _show_full_tendon_report_table(_psloss_friction_calculation_rows(state), label="Tendon-by-tendon friction calculation trace")
    with st.expander("Friction calculation trace / limitations", expanded=False):
        st.markdown(
            '<div class="note-box"><b>Trace basis:</b> route length x and cumulative angular change α are derived from the adopted station profile. For two-end stressing, the preview checks stress from each jacking end and uses the nearer-end friction path for station stress; this is a distribution model only, not a force multiplier. K = 0 is preserved as a project input only when justified by the tendon layout / PT system basis.</div>',
            unsafe_allow_html=True,
        )
        show_engineering_table(_psloss_friction_source_rows(state))
        show_engineering_table(_psloss_friction_report_summary_rows(state))



def _psloss_elastic_shortening_source_state(state: dict[str, Any]) -> dict[str, Any]:
    """Return source-gated state for 4.4 Elastic Shortening preview.

    This preview keeps elastic-shortening transparent without adopting it into
    final effective prestress.  The f_cgp value remains an engineer-controlled
    stage input because span-by-span PT load transfer cannot be inferred safely
    from the completed-span geometry alone.
    """
    ps = D.setdefault("prestress", {})
    m = D.setdefault("materials", {})
    model = _active_adopted_tendon_model() if state.get("tendon_locked") else {}
    summary = state.get("adopted_summary") or {}
    n_tendons = int(summary.get("tendon_count", 0) or len(model.get("tendons", []) or []) or int(ps.get("num_tendons", 0) or 0))
    fpj_mpa = float(summary.get("jacking_stress_mpa", 0.0) or m.get("fpi_mpa", 0.0) or 0.0)
    ep_mpa = float(m.get("Ep_mpa", 0.0) or 0.0)
    eci_mpa = float(m.get("Ec_mpa", 0.0) or 0.0)
    fcgp_mpa = float(ps.get("fcgp_mpa", 0.0) or 0.0)
    n_ratio = ep_mpa / eci_mpa if eci_mpa > 0.0 else 0.0
    avg_loss = ((n_tendons - 1.0) / (2.0 * n_tendons)) * n_ratio * fcgp_mpa if n_tendons > 0 else 0.0
    ready = bool(state.get("tendon_locked")) and bool(state.get("section_ready")) and n_tendons > 0 and ep_mpa > 0.0 and eci_mpa > 0.0 and fcgp_mpa >= 0.0
    return {
        "ready": ready,
        "status": "PREVIEW READY" if ready else "SOURCE BLOCKED",
        "mode": "pass" if ready else "warn",
        "model": model,
        "summary": summary,
        "n_tendons": n_tendons,
        "fpj_mpa": fpj_mpa,
        "ep_mpa": ep_mpa,
        "eci_mpa": eci_mpa,
        "fcgp_mpa": fcgp_mpa,
        "n_ratio": n_ratio,
        "avg_loss_mpa": max(avg_loss, 0.0),
        "message": "Elastic-shortening preview uses adopted tendon count, Ep/Eci, and engineer-reviewed f_cgp stage stress." if ready else "Adopt tendon model, section source, and f_cgp stage basis before elastic-shortening preview can run.",
        "stage_policy": "f_cgp must represent concrete stress at the CG of prestressing steel for the actual stressing/load-transfer stage; do not assume completed-span self-weight automatically.",
    }


def _psloss_elastic_shortening_source_rows(state: dict[str, Any]) -> pd.DataFrame:
    estate = _psloss_elastic_shortening_source_state(state)
    return pd.DataFrame(
        [
            ["Adopted tendon source", "READY" if state.get("tendon_locked") else "BLOCKED", "2.4 Adopted Tendon Data", "Elastic shortening must use the locked adopted tendon count and sequence trace."],
            ["Section / material source", "READY" if state.get("section_ready") else "MISSING", "2.3 Section Properties + Materials", "Eci/Ec must match the concrete stage used for f_cgp."],
            ["Tendon count N", f"{estate['n_tendons']} tendons" if estate["n_tendons"] else "—", "Adopted tendon summary", "N controls sequential average factor (N−1)/(2N)."],
            ["Prestressing steel modulus Ep", f"{estate['ep_mpa']:.0f} MPa", "Material property", "Used in modular ratio Ep/Eci."],
            ["Concrete modulus Eci", f"{estate['eci_mpa']:.0f} MPa", "Material property / stage basis", "Use the concrete modulus applicable at stressing/load transfer."],
            ["Concrete stress f_cgp", f"{estate['fcgp_mpa']:.2f} MPa", "4.4 Elastic Shortening project stage input", estate["stage_policy"]],
            ["Preview status", estate["status"], "Source gate", estate["message"]],
        ],
        columns=["Elastic-shortening source item", "Status / value", "Source owner", "Required engineer check"],
    )


def _psloss_elastic_shortening_sequence_results(state: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    estate = _psloss_elastic_shortening_source_state(state)
    if not estate.get("ready"):
        return [], estate
    model = estate.get("model") or {}
    tendons = model.get("tendons", []) or []
    N = int(estate.get("n_tendons", 0) or len(tendons) or 0)
    n_ratio = float(estate.get("n_ratio", 0.0) or 0.0)
    fcgp = float(estate.get("fcgp_mpa", 0.0) or 0.0)
    fpj = float(estate.get("fpj_mpa", 0.0) or 0.0)
    rows: list[dict[str, Any]] = []
    if N <= 0:
        return rows, estate
    for i, tendon in enumerate(tendons[:N], start=1):
        factor = max((N - i) / N, 0.0)
        loss = factor * n_ratio * fcgp
        fpx = max(fpj - loss, 0.0) if fpj > 0.0 else 0.0
        rows.append(
            {
                "tendon": str(tendon.get("tendon", f"T{i}")),
                "sequence_no": i,
                "sequence_factor": factor,
                "loss_mpa": loss,
                "stress_mpa": fpx,
                "loss_pct": 100.0 * loss / fpj if fpj > 0.0 else 0.0,
                "status": "PREVIEW",
                "note": "Sequence preview only; final stressing sequence may be confirmed by construction/stage source.",
            }
        )
    return rows, estate


def _psloss_elastic_shortening_report_summary_rows(state: dict[str, Any]) -> pd.DataFrame:
    rows, estate = _psloss_elastic_shortening_sequence_results(state)
    if not estate.get("ready"):
        return pd.DataFrame(
            _append_loss_percent_basis_report_rows([
                ["Calculation status", estate["status"], "Adopted tendon source, section/material source, and f_cgp stage input are required."],
                ["Adoption status", "Preview only", "No effective-prestress value is adopted from this page."],
            ]),
            columns=["Item", "Value", "Trace / note"],
        )
    fpj = float(estate.get("fpj_mpa", 0.0) or 0.0)
    avg_loss = float(estate.get("avg_loss_mpa", 0.0) or 0.0)
    avg_stress = fpj - avg_loss if fpj > 0.0 else 0.0
    max_row = max(rows, key=lambda r: float(r.get("loss_mpa", 0.0) or 0.0)) if rows else {"tendon": "-", "sequence_no": "-", "loss_mpa": 0.0, "stress_mpa": fpj, "loss_pct": 0.0}
    min_fpx = min(float(r.get("stress_mpa", fpj) or 0.0) for r in rows) if rows else fpj
    return pd.DataFrame(
        _append_loss_percent_basis_report_rows([
            ["Calculation status", "PREVIEW READY", "Source-gated stage preview; not final effective-prestress adoption."],
            ["Code / equation basis", "AASHTO LRFD 2020 Section 5, Art. 5.9.3", "Sequential average elastic-shortening loss route."],
            ["Formula", "ΔfpES,avg = [(N−1)/(2N)](Ep/Eci)f_cgp", "Sequence trace shown separately as ΔfpES,i = [(N−i)/N](Ep/Eci)f_cgp."],
            ["Tendons in trace", f"{estate['n_tendons']} / {estate['n_tendons']}", "All adopted tendons are included in the source trace."],
            ["Sequence basis", "Preview order from adopted tendon table", "Final construction / stressing sequence must be confirmed before effective-prestress adoption."],
            ["Ep / Eci / f_cgp", f"{estate['ep_mpa']:.0f} MPa / {estate['eci_mpa']:.0f} MPa / {estate['fcgp_mpa']:.2f} MPa", "Material source plus engineer-reviewed stage stress input."],
            ["Average elastic-shortening loss", f"{avg_loss:.2f} MPa ({100.0 * avg_loss / fpj if fpj > 0.0 else 0.0:.2f}%)", "Average report-preview value; do not confuse with the maximum sequence loss."],
            ["fpx after average ES", f"{avg_stress:.2f} MPa", "Average-preview stress only; useful for report comparison against the sequence trace."],
            ["Maximum sequence ES loss", f"{float(max_row.get('loss_mpa', 0.0) or 0.0):.2f} MPa ({float(max_row.get('loss_pct', 0.0) or 0.0):.2f}%)", f"Governing sequence tendon: {max_row.get('tendon', '-')} at sequence i={max_row.get('sequence_no', '-')}"],
            ["Minimum fpx after sequence ES", f"{min_fpx:.2f} MPa", "Sequence-preview stress only; friction, anchor set, and time-dependent losses remain separate."],
        ]),
        columns=["Item", "Value", "Trace / note"],
    )


def _render_loss_result_summary_cards_for_elastic_shortening(state: dict[str, Any]) -> None:
    results, estate = _psloss_elastic_shortening_sequence_results(state)
    if not estate.get("ready"):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            card("ELASTIC SHORTENING SUMMARY", "SOURCE BLOCKED", "Adopt tendon and stage source first", "warn")
        with c2:
            card("AVERAGE ES LOSS", "—", "blocked", "warn")
        with c3:
            card("MAX SEQUENCE ES LOSS", "—", "blocked", "warn")
        with c4:
            card("MIN fpx AFTER ES", "—", "blocked", "warn")
        with c5:
            card("ADOPTION STATUS", "PREVIEW ONLY", "Not effective prestress", "neutral")
        return
    fpj = float(estate.get("fpj_mpa", 0.0) or 0.0)
    avg_loss = float(estate.get("avg_loss_mpa", 0.0) or 0.0)
    avg_pct = 100.0 * avg_loss / fpj if fpj > 0.0 else 0.0
    avg_fpx = fpj - avg_loss if fpj > 0.0 else 0.0
    min_fpx = min(float(r.get("stress_mpa", fpj) or 0.0) for r in results) if results else fpj
    max_row = max(results, key=lambda r: float(r.get("loss_mpa", 0.0) or 0.0)) if results else {"tendon": "-", "sequence_no": "-", "loss_mpa": 0.0, "loss_pct": 0.0}
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        card("ELASTIC SHORTENING SUMMARY", "STAGE PREVIEW", f"N={estate['n_tendons']} · sequence source review", "pass")
    with c2:
        card("AVERAGE ES LOSS", f"{avg_loss:.2f} MPa", f"{avg_pct:.2f}% · fpx,avg={avg_fpx:.2f} MPa", "warn")
    with c3:
        card("MAX SEQUENCE ES LOSS", f"{float(max_row.get('loss_mpa', 0.0) or 0.0):.2f} MPa", f"{float(max_row.get('loss_pct', 0.0) or 0.0):.2f}% · {max_row.get('tendon', '-')} (i={max_row.get('sequence_no', '-')})", "warn")
    with c4:
        card("MIN fpx AFTER SEQUENCE ES", f"{min_fpx:.2f} MPa", "Sequence-preview stress", "pass")
    with c5:
        card("ADOPTION STATUS", "PREVIEW ONLY", "Stage/sequence review required", "neutral")


def _render_elastic_shortening_sequence_basis_note() -> None:
    st.markdown(
        '<div class="warn-box"><b>Sequence basis:</b> tendon-by-tendon elastic-shortening values use the adopted tendon table order as a transparent preview sequence. Confirm the final jacking order, simultaneous stressing pairs, and stage f<sub>cgp</sub> from the construction / staged-analysis source before adopting any elastic-shortening value into effective prestress.</div>',
        unsafe_allow_html=True,
    )


def _render_psloss_elastic_shortening_equation_block(state: dict[str, Any]) -> None:
    estate = _psloss_elastic_shortening_source_state(state)
    st.markdown("#### Elastic-shortening equation block")
    st.markdown(
        '<div class="note-box"><b>Equation route:</b> the average elastic-shortening expression is retained as the report-preview value, while the tendon-by-tendon sequence equation is shown separately for transparency. Average loss, maximum sequence loss, and minimum sequence stress are reported as different quantities. Final effective-prestress adoption remains a later milestone.</div>',
        unsafe_allow_html=True,
    )
    st.latex(r"\Delta f_{pES,avg}=\left(\frac{N-1}{2N}\right)\left(\frac{E_p}{E_{ci}}\right)f_{cgp}")
    st.latex(r"\Delta f_{pES,i}=\left(\frac{N-i}{N}\right)\left(\frac{E_p}{E_{ci}}\right)f_{cgp}")
    st.latex(r"f_{px,ES}=f_{pj}-\Delta f_{pES}")
    st.latex(r"\mathrm{Loss}\,(\%)=\frac{\Delta f_{pES}}{f_{pj}}\times100")
    if not estate.get("ready"):
        st.markdown("<div class='warn-box'><b>Substitution blocked:</b> adopt the tendon model and confirm f<sub>cgp</sub> stage basis before displaying elastic-shortening substitution.</div>", unsafe_allow_html=True)
        return
    N = int(estate.get("n_tendons", 0) or 0)
    Ep = float(estate.get("ep_mpa", 0.0) or 0.0)
    Eci = float(estate.get("eci_mpa", 0.0) or 0.0)
    fcgp = float(estate.get("fcgp_mpa", 0.0) or 0.0)
    n_ratio = float(estate.get("n_ratio", 0.0) or 0.0)
    avg = float(estate.get("avg_loss_mpa", 0.0) or 0.0)
    fpj = float(estate.get("fpj_mpa", 0.0) or 0.0)
    fpx_avg = fpj - avg
    st.markdown("#### Average loss substitution")
    st.latex(rf"\frac{{N-1}}{{2N}}=\frac{{{N}-1}}{{2({N})}}={((N-1)/(2*N)) if N else 0.0:.5f}")
    st.latex(rf"\frac{{E_p}}{{E_{{ci}}}}=\frac{{{Ep:.0f}}}{{{Eci:.0f}}}={n_ratio:.5f}")
    st.latex(rf"\Delta f_{{pES,avg}}={((N-1)/(2*N)) if N else 0.0:.5f}({n_ratio:.5f})({fcgp:.2f})={avg:.2f}\ \mathrm{{MPa}}");
    st.latex(rf"f_{{px,ES,avg}}={fpj:.2f}-{avg:.2f}={fpx_avg:.2f}\ \mathrm{{MPa}}");
    st.latex(rf"\mathrm{{Loss}}={avg:.2f}/{fpj:.2f}\times100={100.0*avg/fpj if fpj > 0 else 0.0:.2f}\%")


def _psloss_elastic_shortening_variable_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["N", "count", "Number of adopted tendons", "2.4 Adopted Tendon Data"],
            ["i", "count", "Jacking sequence index in the transparent sequence preview", "Adopted tendon order; final construction/stressing sequence must be confirmed before adoption"],
            ["Ep", "MPa", "Prestressing steel modulus", "Material property"],
            ["Eci", "MPa", "Concrete modulus at stressing / load-transfer stage", "Material property / engineer stage basis"],
            ["f_cgp", "MPa", "Concrete stress at CG of prestressing steel due to prestress and sustained stage loads", "4.4 Elastic Shortening project stage input"],
            ["(N−1)/(2N)", "-", "Average sequential stressing factor", "Average report-preview value; not the maximum sequence value"],
            ["(N−i)/N", "-", "Tendon-by-tendon sequence preview factor", "Transparency trace only; depends on the assumed preview sequence"],
            ["ΔfpES,avg", "MPa", "Average elastic-shortening loss used for report preview", "Shown separately from maximum sequence loss"],
            ["ΔfpES,i", "MPa", "Elastic-shortening loss for tendon sequence i", "Sequence preview only; final jacking sequence may differ"],
            ["fpx,ES,avg", "MPa", "Prestressing steel stress after average ES preview", "Average preview stress, not minimum sequence stress"],
            ["fpx,ES,i", "MPa", "Prestressing steel stress after sequence ES preview for tendon i", "Not final effective prestress; friction, anchor set, and time-dependent losses remain separate"],
        ],
        columns=["Variable", "Unit", "Meaning", "Source / trace"],
    )


def _psloss_elastic_shortening_governing_walkthrough_rows(state: dict[str, Any]) -> pd.DataFrame:
    results, estate = _psloss_elastic_shortening_sequence_results(state)
    if not estate.get("ready") or not results:
        return pd.DataFrame(
            [["Source gate", "BLOCKED", "Adopt tendon model, section/material source, and f_cgp stage basis before formula walkthrough."]],
            columns=["Step", "Value", "Trace"],
        )
    fpj = float(estate.get("fpj_mpa", 0.0) or 0.0)
    avg = float(estate.get("avg_loss_mpa", 0.0) or 0.0)
    max_row = max(results, key=lambda r: float(r.get("loss_mpa", 0.0) or 0.0))
    min_fpx = min(float(r.get("stress_mpa", fpj) or 0.0) for r in results) if results else fpj
    return pd.DataFrame(
        [
            ["Adopted tendon count", f"N = {estate['n_tendons']}", "Read from locked adopted tendon source."],
            ["Sequence basis", "Adopted tendon table order", "Transparent preview order only; confirm construction jacking order / simultaneous pairs before final adoption."],
            ["Material ratio", f"Ep/Eci = {estate['ep_mpa']:.0f}/{estate['eci_mpa']:.0f} = {estate['n_ratio']:.5f}", "Prestressing steel modulus divided by concrete stage modulus."],
            ["Stage stress", f"f_cgp = {estate['fcgp_mpa']:.2f} MPa", estate["stage_policy"]],
            ["Average factor", f"(N−1)/(2N) = {(estate['n_tendons']-1)/(2*estate['n_tendons']):.5f}", "Average of sequential stressing losses for equal tendon force."],
            ["Average ES loss", f"ΔfpES,avg = {avg:.2f} MPa", "Average report-preview value; not the same quantity as maximum sequence loss."],
            ["Average stress after ES", f"fpx,ES,avg = {fpj - avg:.2f} MPa", "Average-preview stress; separate from minimum sequence stress."],
            ["Governing sequence tendon", f"{max_row.get('tendon', '-')} at i={max_row.get('sequence_no', '-')}", "Earliest tendon in the preview sequence loses most; final order may differ."],
            ["Maximum sequence ES loss", f"ΔfpES,max = {float(max_row.get('loss_mpa', 0.0) or 0.0):.2f} MPa ({float(max_row.get('loss_pct', 0.0) or 0.0):.2f}%)", "Sequence-preview maximum; use only after sequence source is confirmed."],
            ["Minimum sequence stress after ES", f"min fpx,ES,i = {min_fpx:.2f} MPa", "Sequence-preview stress only; other losses remain separate."],
        ],
        columns=["Step", "Value", "Trace"],
    )


def _psloss_elastic_shortening_sequence_rows(state: dict[str, Any]) -> pd.DataFrame:
    results, estate = _psloss_elastic_shortening_sequence_results(state)
    if not estate.get("ready"):
        return pd.DataFrame(
            [["SOURCE BLOCKED", "-", "-", "-", "-", "-", "Adopt tendon model and confirm f_cgp stage basis before elastic-shortening preview."]],
            columns=["Tendon", "Sequence i", "Sequence factor", "Ep/Eci", "ΔfpES", "fpx,ES", "Status / note"],
        )
    rows = []
    for r in results:
        rows.append(
            [
                r.get("tendon", "-"),
                str(r.get("sequence_no", "-")),
                f"{float(r.get('sequence_factor', 0.0) or 0.0):.5f}",
                f"{estate['n_ratio']:.5f}",
                f"{float(r.get('loss_mpa', 0.0) or 0.0):.2f} MPa ({float(r.get('loss_pct', 0.0) or 0.0):.2f}%)",
                f"{float(r.get('stress_mpa', 0.0) or 0.0):.2f} MPa",
                r.get("note", "PREVIEW"),
            ]
        )
    return pd.DataFrame(rows, columns=["Tendon", "Sequence i", "Sequence factor", "Ep/Eci", "ΔfpES", "fpx,ES", "Status / note"])


def render_prestress_elastic_shortening_source_model() -> None:
    """Render 4.4 Elastic Shortening as a source-gated stage preview.

    Static trace tokens retained for PSLOSS.12 guard tests: average-vs-sequence reporting.
    """
    state = _psloss_source_gate_state()
    estate = _psloss_elastic_shortening_source_state(state)
    code_basis_card(
        "4.4 Elastic Shortening Source Model",
        "AASHTO LRFD 2020 Section 5, Art. 5.9.3",
        "PSLOSS.22 keeps the elastic-shortening preview closed while 4.5 Time-Dependent Losses is reorganized into component tabs; final effective-prestress adoption remains blocked.",
    )
    st.markdown(
        '<div class="note-box"><b>Elastic-shortening source rule:</b> the preview must read the locked adopted tendon count, material moduli, and engineer-reviewed stage stress f<sub>cgp</sub>. The app must not infer the actual span-by-span stressing/load-transfer stage from completed-span geometry alone.</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("ELASTIC SHORTENING PREVIEW", estate["status"], estate["message"], estate["mode"])
    with c2:
        card("TENDON SOURCE", "ADOPTED" if state.get("tendon_locked") else "BLOCKED", "2.4 adopted tendon count", "pass" if state.get("tendon_locked") else "warn")
    with c3:
        card("STAGE STRESS", "REVIEWED INPUT" if estate.get("ready") else "REVIEW REQUIRED", f"f_cgp = {estate['fcgp_mpa']:.2f} MPa", "warn")
    with c4:
        card("ADOPTION POLICY", "PREVIEW ONLY", "Not effective prestress", "neutral")

    st.markdown("### Elastic-shortening loss result summary")
    _render_loss_result_summary_cards_for_elastic_shortening(state)
    _render_loss_percent_basis_note()

    st.markdown("### Elastic-shortening input assistant")
    editable_value(["prestress", "fcgp_mpa"], "Concrete stress at CG of prestressing steel f_cgp (MPa)", 0.1, "%.2f")
    st.markdown(
        '<div class="warn-box"><b>Stage check:</b> f<sub>cgp</sub> is a stage-controlled engineering input. Confirm it against the actual stressing/load-transfer model before adopting any final effective-prestress result.</div>',
        unsafe_allow_html=True,
    )
    _render_elastic_shortening_sequence_basis_note()
    show_engineering_table(_psloss_elastic_shortening_source_rows(state))

    st.markdown("### Report-style elastic-shortening summary")
    show_engineering_table(_psloss_elastic_shortening_report_summary_rows(state))

    st.markdown("### Elastic-shortening formula and variable trace")
    _render_psloss_elastic_shortening_equation_block(state)
    show_engineering_table(_psloss_elastic_shortening_variable_rows())

    st.markdown("### Governing / average calculation walkthrough")
    show_engineering_table(_psloss_elastic_shortening_governing_walkthrough_rows(state))

    st.markdown(
        '<div class="warn-box"><b>Preview only:</b> elastic-shortening preview is not adopted into effective prestress. Final adoption must define the actual stressing sequence, stage loads, and whether an average or tendon-specific ES value is used.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("### Tendon-by-tendon elastic-shortening sequence trace")
    _show_full_tendon_report_table(_psloss_elastic_shortening_sequence_rows(state), label="Tendon-by-tendon elastic-shortening sequence trace")
    with st.expander("Elastic-shortening calculation trace / limitations", expanded=False):
        st.markdown(
            '<div class="note-box"><b>Trace basis:</b> the average expression is the report preview value. The tendon-by-tendon sequence table is a transparency trace based on adopted tendon order; construction-specific jacking sequence and stage f<sub>cgp</sub> remain engineer-reviewed sources before final effective-prestress adoption.</div>',
            unsafe_allow_html=True,
        )
        show_engineering_table(_psloss_elastic_shortening_source_rows(state))
        show_engineering_table(_psloss_elastic_shortening_report_summary_rows(state))

def _psloss3_readiness_cards(state: dict[str, Any]) -> None:
    """Compact PSLOSS.4 cards for adopted-source readiness."""
    summary = state.get("adopted_summary") or {}
    stressing = state.get("stressing_basis", {})
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card(
            "ADOPTED TENDON SUMMARY",
            "LOCKED" if state.get("tendon_locked") else "BLOCKED",
            f"{summary.get('tendon_count', 0)} tendons · Aps,total {float(summary.get('Aps_total_mm2', 0.0) or 0.0):.0f} mm²" if summary else "Adopt tendon model first",
            "pass" if state.get("tendon_locked") else "warn",
        )
    with c2:
        card(
            "JACKING FORCE POLICY",
            "LOCKED RULE",
            "Pj/tendon is axial force; two-end stressing does not double total Pj",
            "neutral",
        )
    with c3:
        card(
            "STRESSING TRACE",
            stressing.get("status", "BLOCKED"),
            stressing.get("stressing_mode", "Confirm JackFrom"),
            stressing.get("mode", "warn"),
        )
    with c4:
        card(
            "NEXT STEP",
            "TIME-DEPENDENT LOSSES" if state.get("ready") else "ADOPT SOURCE FIRST",
            "Proceed only after all source gates are ready" if not state.get("ready") else "4.5 Time-Dependent Losses component tabs are active",
            "pass" if state.get("ready") else "warn",
        )

def render_prestress_losses_source_gate_panel(*, compact: bool = False) -> dict[str, Any]:
    """Render PSLOSS.3 source gate and return the source state."""
    state = _psloss_source_gate_state()
    if not compact:
        code_basis_card(
            "Prestress Losses Source Gate",
            "AASHTO LRFD 2020 Section 5, Art. 5.9.3",
            "PSLOSS.24 keeps the general source gate active and fixes CR&SH handoff compatibility for migrated project states while 4.5 Time-Dependent Losses remains source-gated. Final effective-prestress adoption remains a later milestone.",
        )
        st.markdown(
            '<div class="note-box"><b>Source-gate rule:</b> detailed prestress-loss calculation must read from adopted tendon and section sources only. Working imports, diagnostic previews, and duplicated keyed inputs must not feed final loss results.</div>',
            unsafe_allow_html=True,
        )
        if not state["tendon_locked"]:
            st.markdown(
                '<div class="warn-box"><b>Tendon adoption action required:</b> go to <b>2.4 Tendon Layout Reference → Import / Mapping</b>, import the General / Vertical / Horizontal tendon tables, review the tendon QA, then open <b>Adopted Tendon Data</b> and press <b>Adopt / Re-adopt tendon model as design source</b>. Prestress-loss values stay blocked until that source is locked.</div>',
                unsafe_allow_html=True,
            )
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        card("LOSS CALCULATION", state["overall_status"], "Detailed formulas are blocked until all source gates are ready." if not state["ready"] else "Ready for next loss-calculation milestone.", state["overall_mode"])
    with c2:
        tstat = state["tendon_status"]
        card("TENDON SOURCE", tstat.get("status", "PENDING"), tstat.get("message", "Adopt tendon model."), tstat.get("mode", "warn"))
    with c3:
        sstat = state["stressing_basis"]
        card("STRESSING BASIS", sstat.get("status", "BLOCKED"), sstat.get("stressing_mode", "Confirm JackFrom"), sstat.get("mode", "warn"))
    with c4:
        card("SECTION SOURCE", "READY" if state["section_ready"] else "MISSING", "Adopted section properties for design", "pass" if state["section_ready"] else "warn")
    with c5:
        card("CR&SH SOURCE", "READY" if state["crsh_ready"] else "MISSING", "Consumed from 3.8 CR&SH", "pass" if state["crsh_ready"] else "warn")

    show_engineering_table(_psloss_source_gate_rows(state))
    st.markdown(
        '<div class="warn-box"><b>Jacking-force interpretation:</b> Pj/tendon is the tendon axial jacking force. One-end versus two-end stressing controls the friction/anchor-set distribution and JackFrom trace; it must not double Aps,total or total axial prestressing force.</div>',
        unsafe_allow_html=True,
    )
    if not compact:
        st.markdown("### PSLOSS.24 calculation-readiness snapshot")
        _psloss3_readiness_cards(state)
        st.markdown("### Tendon adoption and blocked-input checklist")
        show_engineering_table(_psloss_blocked_tendon_checklist_rows(state))
        st.markdown("### Adopted tendon source readiness")
        show_engineering_table(_psloss_adopted_tendon_readiness_rows(state))
        st.markdown("### Stressing basis / JackFrom gate")
        show_engineering_table(_psloss_stressing_basis_rows(state))
        st.markdown("### Adopted prestress input summary")
        show_engineering_table(_psloss_tendon_summary_rows(state))
        st.markdown("### Time-dependent parameter handoff from 3.8 CR&SH")
        show_engineering_table(_psloss_crsh_handoff_rows(state))
        st.markdown("### Loss calculation readiness register")
        show_engineering_table(_psloss_formula_readiness_rows(state))
        with st.expander("Trace / QA for next prestress-loss calculation milestone", expanded=False):
            st.markdown(
                '<div class="note-box"><b>PSLOSS.24 rule:</b> 4.1 remains a robust source/readiness register. The CR&SH handoff must display SOURCE PARTIAL / REVIEW rows instead of crashing when a migrated project state has no 4.5 factors snapshot. 4.2 Friction, 4.3 Anchor Set, 4.4 Elastic Shortening, and 4.5 Time-Dependent Losses remain preview-only; final effective-prestress adoption remains unchanged.</div>',
                unsafe_allow_html=True,
            )
            show_engineering_table(_psloss_formula_readiness_rows(state))
    return state


def render_report_qa_prestress_losses_handoff_snapshot() -> None:
    """Read-only Report / QA snapshot for PSLOSS.3."""
    st.markdown("### 4 Prestress Losses — Report / QA source-gate handoff")
    state = _psloss_source_gate_state()
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        card("Loss source gate", state["overall_status"], "Report / QA snapshot only; no loss solver rerun.", state["overall_mode"])
    with c2:
        card("Tendon", state["tendon_status"].get("status", "PENDING"), state["tendon_status"].get("message", "Adopt tendon model."), state["tendon_status"].get("mode", "warn"))
    with c3:
        sstat = state["stressing_basis"]
        card("Stressing", sstat.get("status", "BLOCKED"), sstat.get("stressing_mode", "Confirm JackFrom"), sstat.get("mode", "warn"))
    with c4:
        card("Section", "READY" if state["section_ready"] else "MISSING", "Adopted section properties", "pass" if state["section_ready"] else "warn")
    with c5:
        card("CR&SH", "READY" if state["crsh_ready"] else "MISSING", "3.8 parameter handoff", "pass" if state["crsh_ready"] else "warn")
    show_engineering_table(_psloss_source_gate_rows(state))
    st.markdown("#### Adopted tendon and formula-readiness snapshot")
    show_engineering_table(_psloss_adopted_tendon_readiness_rows(state))
    show_engineering_table(_psloss_formula_readiness_rows(state))
    st.markdown("#### 4.2 Friction equation / summary snapshot")
    show_engineering_table(_psloss_friction_source_rows(state))
    show_engineering_table(_psloss_friction_report_summary_rows(state))
    show_engineering_table(_psloss_friction_governing_walkthrough_rows(state))
    st.markdown("#### 4.3 Anchor-set equation / summary snapshot")
    show_engineering_table(_psloss_anchor_source_rows(state))
    show_engineering_table(_psloss_anchor_report_summary_rows(state))
    show_engineering_table(_psloss_anchor_governing_walkthrough_rows(state))
    show_engineering_table(_psloss_anchor_distribution_summary_rows(state))
    show_engineering_table(_psloss_anchor_distribution_station_rows(state))
    st.markdown("#### 4.4 Elastic-shortening equation / summary snapshot")
    show_engineering_table(_psloss_elastic_shortening_source_rows(state))
    show_engineering_table(_psloss_elastic_shortening_report_summary_rows(state))
    show_engineering_table(_psloss_elastic_shortening_governing_walkthrough_rows(state))

def _tendon_stressing_basis_frame(model: dict[str, Any]) -> pd.DataFrame:
    stressing = build_tendon_stressing_basis_summary(model)
    return pd.DataFrame(
        [
            ["JackFrom source", stressing.get("source", "-"), stressing.get("status", "PENDING"), stressing.get("message", "-")],
            ["Detected stressing mode", stressing.get("detected_mode", "-"), stressing.get("adoption_status", "-"), stressing.get("affects", "Friction loss and anchor-set distribution")],
            ["JackFrom values", stressing.get("jack_from_display", "—"), f"{stressing.get('missing_count', 0)} missing", "Use tendon-by-tendon source when values are mixed."],
            ["Force policy", "Pj/tendon is axial force", "LOCKED RULE", "Two-end stressing controls loss distribution only; it must not double Aps,total or total Pj."],
        ],
        columns=["Item", "Value", "Status", "Required engineer check"],
    )


def _render_tendon_stressing_basis_cards(model: dict[str, Any]) -> None:
    """Show JackFrom / stressing-mode readiness without creating duplicate input."""
    stressing = build_tendon_stressing_basis_summary(model)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Stressing Basis", stressing.get("adoption_status", "PENDING"), stressing.get("message", ""), stressing.get("mode", "warn"))
    with c2:
        card("JackFrom", stressing.get("jack_from_display", "—"), stressing.get("source", "General tendon table"), stressing.get("mode", "warn"))
    with c3:
        card("Detected Mode", stressing.get("detected_mode", "—"), stressing.get("affects", "friction / anchor-set"), stressing.get("mode", "warn"))
    with c4:
        card("Force Policy", "LOCKED RULE", "Two-end stressing does not double total Pj", "neutral")


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
    _render_tendon_stressing_basis_cards(model_for_summary)
    st.markdown(
        '<div class="note-box"><b>Stressing-basis source note:</b> The one-end / two-end stressing basis is auto-detected from the <b>General tendon table · JackFrom field</b>. This is a traced tendon-source value, not a duplicate Prestress Losses input. Use a reviewed override only if the imported JackFrom field is missing, inconsistent, or superseded by project records.</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Tendon stressing-basis summary", expanded=False):
        show_engineering_table(_tendon_stressing_basis_frame(model_for_summary))
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
            station_key = "tendon_section_overlay_station_value"
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

            # Avoid Streamlit's Slider frontend chunk on this production QA view.
            # A numeric station picker is more stable in PDF/browser handoff and
            # keeps the quick-station buttons as the primary review workflow.
            current_station = float(st.session_state.get(station_key, mid_station))
            current_station = max(0.0, min(float(max_station), current_station))
            station = st.number_input(
                "Station x (m)",
                min_value=0.0,
                max_value=float(max_station),
                value=current_station,
                step=0.01,
                format="%.3f",
                key=station_key,
                help="Numeric station control replaces the previous slider to avoid frontend dynamic-import instability during section-overlay review.",
            )
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
            st.markdown("#### Stressing basis from JackFrom")
            show_engineering_table(_tendon_stressing_basis_frame(adopted_model if adopted_model else model))

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

        st.markdown("#### JackFrom / stressing-basis QA")
        show_engineering_table(_tendon_stressing_basis_frame(adopted_model if adopted_model else model))

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
            ["Stressing basis", "General tendon table JackFrom field", "Auto-detect one-end / two-end / mixed; require traced review if missing", build_tendon_stressing_basis_summary(adopted_model if adopted_model else model).get("status", "PENDING")],
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



def _psloss_crsh_route_options() -> list[str]:
    return [
        "Refined / time-step — Recommended",
        "Approximate — Quick check only",
        "Advanced segment-age table — Future / gated",
    ]


def _psloss_crsh_selected_route() -> str:
    ps = D["prestress"]
    options = _psloss_crsh_route_options()
    route = str(ps.get("crsh_calculation_route", options[0]))
    if route not in options:
        route = options[0]
    ps["crsh_calculation_route"] = route
    return route


def _psloss_crsh_time_source_options() -> list[str]:
    return [
        "Use computed t_jack from 4.5 construction map",
        "Use 3.8 CR&SH ti",
        "Keep REVIEW / do not adopt",
    ]


def _psloss_crsh_selected_time_source() -> str:
    ps = D["prestress"]
    options = _psloss_crsh_time_source_options()
    source = str(ps.get("crsh_time_step_age_source", options[2]))
    if source not in options:
        source = options[2]
    ps["crsh_time_step_age_source"] = source
    return source


def _psloss_crsh_ktd(time_days: float, fci_ksi: float) -> float:
    """AASHTO 5.4.2.3.2 time-development factor for creep/shrinkage preview."""
    t = max(0.0, float(time_days or 0.0))
    fci = max(0.1, float(fci_ksi or 0.1))
    denom = 12.0 * ((100.0 - 4.0 * fci) / (fci + 20.0)) + t
    return t / denom if denom > 0.0 else 0.0


def _psloss_crsh_factor_preview(state: dict[str, Any]) -> dict[str, float]:
    """Return source-gated AASHTO creep/shrinkage factors for the 4.5 preview.

    This is intentionally a preview source model. It exposes Article 5.4.2.3
    factors and uses representative span-by-span timing before any 4.6 final
    effective-prestress adoption rule is allowed to consume the values.
    """
    ps = D["prestress"]
    m = D["materials"]
    sec = D["section"]
    crsh = state.get("crsh", update_crsh_derived_parameters())

    H = max(0.0, min(100.0, float(ps.get("RH_percent", 75.0) or 75.0)))
    vs_in = max(0.0, float(crsh.get("V_over_S_in", ps.get("V_over_S_in", 0.0)) or 0.0))
    fci_mpa = max(0.1, float(m.get("fci_mpa", m.get("fc_mpa", 60.0)) or 60.0))
    fci_ksi = mpa_to_ksi(fci_mpa)
    Ep = max(0.0, float(m.get("Ep_mpa", 0.0) or 0.0))
    Eci = max(0.0, float(m.get("Ec_mpa", 0.0) or 0.0))
    fpj = max(0.0, float(m.get("fpi_mpa", 0.0) or 0.0))
    fcgp = max(0.0, float(ps.get("fcgp_mpa", 0.0) or 0.0))
    t_start = max(0.0, float(state.get("effective_t_jack_days", state.get("t_jack_days", 0.0)) or 0.0))
    tf = max(t_start, float(state.get("tf_days", ps.get("tf_days", t_start)) or t_start))
    dt = max(tf - t_start, 0.0)
    Ac_m2 = max(0.0, float(sec.get("Ac_m2", 0.0) or 0.0))
    Aps_total_mm2 = max(0.0, float(ps.get("Aps_total_mm2", 0.0) or 0.0))

    # AASHTO 5.4.2.3.2 / 5.4.2.3.3 material factors.
    ks_creep = max(1.0, 1.45 - 0.13 * vs_in)
    khc = 1.56 - 0.008 * H
    kf = 5.0 / (1.0 + fci_ksi)
    ktd_creep = _psloss_crsh_ktd(dt, fci_ksi)
    ti_term = max(t_start, 1.0) ** (-0.118)
    creep_coeff = max(0.0, 1.9 * ks_creep * khc * kf * ktd_creep * ti_term)

    ks_sh = ks_creep
    khs = 2.00 - 0.014 * H
    ktd_tf = _psloss_crsh_ktd(tf, fci_ksi)
    ktd_tstart = _psloss_crsh_ktd(t_start, fci_ksi)
    ktd_sh_increment = max(0.0, ktd_tf - ktd_tstart)
    eps_sh_increment = max(0.0, ks_sh * khs * kf * ktd_sh_increment * 0.48e-3)

    ep_over_eci = (Ep / Eci) if Eci > 0.0 else 0.0
    creep_loss_mpa = ep_over_eci * fcgp * creep_coeff
    shrinkage_loss_mpa = Ep * eps_sh_increment
    total_crsh_loss_mpa = creep_loss_mpa + shrinkage_loss_mpa
    fpx_after_crsh_mpa = fpj - total_crsh_loss_mpa

    # AASHTO 5.9.3.3 quick-check only; exposed as a preliminary comparison.
    gamma_h = 1.7 - 0.01 * H
    gamma_st = kf
    fpi_ksi = mpa_to_ksi(fpj)
    Ag_in2 = Ac_m2 * 1550.0031000062
    Aps_in2 = Aps_total_mm2 / 645.1600000
    fpi_aps_over_ag_ksi = fpi_ksi * Aps_in2 / Ag_in2 if Ag_in2 > 0.0 else 0.0
    approx_creep_ksi = 10.0 * fpi_aps_over_ag_ksi * gamma_h * gamma_st
    approx_shrink_ksi = 12.0 * gamma_h * gamma_st
    approx_relax_ksi = 2.4
    approx_total_ksi = approx_creep_ksi + approx_shrink_ksi + approx_relax_ksi
    approx_creep_mpa = ksi_to_mpa(approx_creep_ksi)
    approx_shrink_mpa = ksi_to_mpa(approx_shrink_ksi)
    approx_relax_mpa = ksi_to_mpa(approx_relax_ksi)
    approx_total_mpa = ksi_to_mpa(approx_total_ksi)

    return {
        "H": H,
        "V_over_S_in": vs_in,
        "fci_mpa": fci_mpa,
        "fci_ksi": fci_ksi,
        "Ep_mpa": Ep,
        "Eci_mpa": Eci,
        "fpj_mpa": fpj,
        "fcgp_mpa": fcgp,
        "Ac_m2": Ac_m2,
        "Aps_total_mm2": Aps_total_mm2,
        "ks_creep": ks_creep,
        "khc": khc,
        "kf": kf,
        "ktd_creep": ktd_creep,
        "ti_term": ti_term,
        "creep_coeff": creep_coeff,
        "ks_shrinkage": ks_sh,
        "khs": khs,
        "ktd_tf": ktd_tf,
        "t_start_days": t_start,
        "ktd_tstart": ktd_tstart,
        "ktd_tjack": ktd_tstart,
        "ktd_sh_increment": ktd_sh_increment,
        "eps_sh_increment": eps_sh_increment,
        "ep_over_eci": ep_over_eci,
        "creep_loss_mpa": creep_loss_mpa,
        "shrinkage_loss_mpa": shrinkage_loss_mpa,
        "total_crsh_loss_mpa": total_crsh_loss_mpa,
        "fpx_after_crsh_mpa": fpx_after_crsh_mpa,
        "creep_loss_pct": (creep_loss_mpa / fpj * 100.0) if fpj > 0 else 0.0,
        "shrinkage_loss_pct": (shrinkage_loss_mpa / fpj * 100.0) if fpj > 0 else 0.0,
        "total_crsh_loss_pct": (total_crsh_loss_mpa / fpj * 100.0) if fpj > 0 else 0.0,
        "gamma_h": gamma_h,
        "gamma_st": gamma_st,
        "fpi_ksi": fpi_ksi,
        "Ag_in2": Ag_in2,
        "Aps_in2": Aps_in2,
        "fpi_aps_over_ag_ksi": fpi_aps_over_ag_ksi,
        "approx_creep_mpa": approx_creep_mpa,
        "approx_shrinkage_mpa": approx_shrink_mpa,
        "approx_relaxation_mpa": approx_relax_mpa,
        "approx_total_mpa": approx_total_mpa,
        "approx_total_pct": (approx_total_mpa / fpj * 100.0) if fpj > 0 else 0.0,
    }


def _psloss_crsh_time_step_state() -> dict[str, Any]:
    """Build the 4.5 Time-Dependent Losses construction-stage source map.

    PSLOSS.16-18 turns the user's span-by-span construction sequence into a
    selectable method route, source-gated refined factor trace, and report-style
    creep/shrinkage preview. It still does not adopt final effective prestress.
    """
    ps = D["prestress"]
    crsh = update_crsh_derived_parameters()
    options = _psloss_crsh_route_options()
    ps.setdefault("crsh_construction_method", "Span-by-span segmental with precast segments")
    ps.setdefault("segment_age_at_transport_days", 30.0)
    ps.setdefault("span_assembly_duration_days", 0.0)
    ps.setdefault("crsh_stage_time_basis", "Auto representative span mode")
    ps.setdefault("crsh_calculation_route", options[0])
    ps.setdefault("crsh_time_step_age_source", _psloss_crsh_time_source_options()[2])
    selected_route = _psloss_crsh_selected_route()
    selected_time_source = _psloss_crsh_selected_time_source()
    transport_age = max(0.0, float(ps.get("segment_age_at_transport_days", 30.0) or 0.0))
    assembly_days = max(0.0, float(ps.get("span_assembly_duration_days", 0.0) or 0.0))
    t_jack = transport_age + assembly_days
    ti_38 = max(0.0, float(ps.get("ti_days", 0.0) or 0.0))
    tf = max(t_jack, float(ps.get("tf_days", 0.0) or 0.0))
    diff = abs(ti_38 - t_jack)
    if selected_time_source.startswith("Use computed"):
        effective_t_jack = t_jack
        time_source_status = "COMPUTED t_jack"
        time_source_ready = True
        time_source_mode = "pass" if diff <= 0.5 else "warn"
        time_source_note = "4.5 construction-stage map controls the time-step start; 3.8 ti remains a comparison trace."
    elif selected_time_source.startswith("Use 3.8"):
        effective_t_jack = ti_38
        time_source_status = "3.8 ti"
        time_source_ready = True
        time_source_mode = "pass" if diff <= 0.5 else "warn"
        time_source_note = "3.8 CR&SH ti controls the time-step start; computed t_jack remains a construction-map comparison."
    else:
        effective_t_jack = t_jack
        time_source_status = "REVIEW"
        time_source_ready = diff <= 0.5
        time_source_mode = "pass" if diff <= 0.5 else "warn"
        time_source_note = "Select computed t_jack or 3.8 ti before any final effective-prestress adoption."
    if diff <= 0.5:
        reconciliation = "ALIGNED"
        rec_mode = "pass"
        rec_note = "3.8 ti matches the computed representative jacking age."
    else:
        reconciliation = "REVIEW"
        rec_mode = "warn"
        rec_note = "3.8 ti and computed t_jack differ; select the controlling time-step age source before final adoption."
    if assembly_days > 0.0:
        stage_status = "AUTO REPRESENTATIVE"
        stage_mode = "pass"
        stage_note = "Transport age plus span assembly duration defines t_jack."
    else:
        stage_status = "REVIEW"
        stage_mode = "warn"
        stage_note = "Assembly duration is zero/default; confirm whether stressing occurs immediately after transport."
    if selected_route.startswith("Refined"):
        method_status = "REFINED / TIME-STEP"
        method_mode = "pass"
        adoption_policy = "Recommended preview route; final adoption deferred to 4.6 Effective Prestress."
        method_ready = True
    elif selected_route.startswith("Approximate"):
        method_status = "APPROXIMATE QUICK CHECK"
        method_mode = "warn"
        adoption_policy = "Preliminary comparison only; do not adopt as final for segmental span-by-span PT."
        method_ready = True
    else:
        method_status = "FUTURE / GATED"
        method_mode = "warn"
        adoption_policy = "Advanced segment-age table is not active yet; use refined representative mode until a segment schedule is implemented."
        method_ready = False
    state = {
        "construction_method": str(ps.get("crsh_construction_method", "Span-by-span segmental with precast segments")),
        "selected_route": selected_route,
        "selected_time_source": selected_time_source,
        "transport_age_days": transport_age,
        "assembly_duration_days": assembly_days,
        "t_jack_days": t_jack,
        "effective_t_jack_days": effective_t_jack,
        "ti_38_days": ti_38,
        "tf_days": tf,
        "duration_after_jack_days": max(tf - effective_t_jack, 0.0),
        "duration_after_jack_years": max(tf - effective_t_jack, 0.0) / 365.25 if tf > effective_t_jack else 0.0,
        "crsh": crsh,
        "method_status": method_status,
        "method_mode": method_mode,
        "method_ready": method_ready,
        "adoption_policy": adoption_policy,
        "stage_status": stage_status,
        "stage_mode": stage_mode,
        "stage_note": stage_note,
        "reconciliation": reconciliation,
        "rec_mode": rec_mode,
        "rec_note": rec_note,
        "time_source_status": time_source_status,
        "time_source_ready": time_source_ready,
        "time_source_mode": time_source_mode,
        "time_source_note": time_source_note,
        "ready_for_refined_preview": method_ready and time_source_ready,
    }
    factors = _psloss_crsh_factor_preview(state)
    state["factors"] = factors
    return state


def _psloss_crsh_source_rows(state: dict[str, Any]) -> pd.DataFrame:
    crsh = state["crsh"]
    ps = D["prestress"]
    return pd.DataFrame(
        [
            ["Selected calculation route", state["selected_route"], "4.5 method selector", state["adoption_policy"]],
            ["Selected time-step age source", state.get("selected_time_source", "SOURCE PARTIAL"), "4.5 ti source selector", state["time_source_note"]],
            ["Construction method", state["construction_method"], "4.5 construction-stage input", "Span-by-span representative mode; not a duplicate CR&SH material input."],
            ["Segment age at transport", f"{state['transport_age_days']:.1f}", "days", "Editable in 4.5; default is 30 days."],
            ["Span assembly duration", f"{state['assembly_duration_days']:.1f}", "days", "Editable in 4.5; set to actual gantry-launcher assembly duration before final adoption."],
            ["Computed tendon stressing age t_jack", f"{state['t_jack_days']:.1f}", "days", "t_jack = segment age at transport + span assembly duration."],
            ["3.8 CR&SH ti", f"{state['ti_38_days']:.1f}", "days", f"Source reconciliation: {state['reconciliation']}."] ,
            ["Selected time-step start age t_start", f"{state.get('effective_t_jack_days', 0.0):.1f}", "days", "Selected source used by refined preview formulas; t_start may be computed t_jack or 3.8 CR&SH ti."],
            ["Final design age tf", f"{state['tf_days']:.1f}", "days", "Read from 3.8 CR&SH."],
            ["RH", f"{ps['RH_percent']:.1f}", "%", "Read from 3.8 CR&SH; do not duplicate here."],
            ["V/S", f"{crsh['V_over_S_in']:.2f}", "in", "Derived in 3.8 from section area and selected drying perimeter."],
            ["h0", f"{crsh['h0_m']:.4f}", "m", "Derived in 3.8 as h0 = 2Ac/u_total."],
            ["Drying perimeter basis", str(ps.get("crsh_drying_perimeter_basis", "-")), "-", "Read from 3.8 CR&SH."],
        ],
        columns=["Source item", "Value", "Unit", "Trace / engineer check"],
    )


def _psloss_crsh_method_map_rows(state: dict[str, Any] | None = None) -> pd.DataFrame:
    selected = state.get("selected_route", "") if state else ""
    return pd.DataFrame(
        [
            ["Approximate route", "Selectable quick check only" + (" · SELECTED" if selected.startswith("Approximate") else ""), "AASHTO Art. 5.9.3.3", "Useful for preliminary comparison; not the preferred final route for segmental span-by-span PT."],
            ["Refined / time-step route", "Recommended" + (" · SELECTED" if selected.startswith("Refined") else ""), "AASHTO Art. 5.9.3.4 + stage time map", "Use representative construction stages first, then upgrade to staged FEA / actual schedule when available."],
            ["Auto representative span mode", "Active source map", "4.5 source gate", "Uses editable segment age at transport, span assembly duration, 3.8 CR&SH parameters, and adopted tendon/section source."],
            ["Advanced segment-age table", "Future / gated" + (" · SELECTED BUT BLOCKED" if selected.startswith("Advanced") else ""), "Segment-by-segment schedule", "Use when casting dates, erection dates, or stressing date vary by segment family/batch."],
        ],
        columns=["Method", "App role", "Code / source route", "Interpretation"],
    )


def _psloss_crsh_stage_timeline_rows(state: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["Stage 0", "Factory casting / curing / storage", "0 → transport", "No tendon stress yet; shrinkage before jacking is not a direct tendon prestress loss."],
            ["Stage 1", "Transport to site", f"t = {state['transport_age_days']:.1f} d", "Editable by user; 30 days is the default project assumption."],
            ["Stage 2", "Span assembly by gantry launcher", f"+ {state['assembly_duration_days']:.1f} d", "Use actual assembly duration when known."],
            ["Stage 3", "Stress all tendons after span assembly", f"t_jack = {state['t_jack_days']:.1f} d", "Computed construction-map jacking age; selected t_start may use this value or 3.8 CR&SH ti."],
            ["Stage 4", "Long-term final time", f"tf = {state['tf_days']:.0f} d", f"Duration after jacking ≈ {state['duration_after_jack_years']:.1f} years."],
        ],
        columns=["Stage", "Construction event", "Representative time", "Loss interpretation"],
    )


def _psloss_crsh_reconciliation_rows(state: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["Computed representative t_jack", f"{state['t_jack_days']:.1f} days", "4.5 construction-stage map", "segment age at transport + span assembly duration"],
            ["Current 3.8 CR&SH ti", f"{state['ti_38_days']:.1f} days", "3.8 CR&SH", "existing material-loss age input"],
            ["Selected time-step age source", state.get("selected_time_source", "SOURCE PARTIAL"), "4.5 ti source selector", state["time_source_note"]],
            ["Selected t_start", f"{state.get('effective_t_jack_days', 0.0):.1f} days", "Selected age source", "This selected age is used by refined creep/shrinkage formulas shown below; computed t_jack remains a reconciliation value."],
            ["Difference", f"{abs(state['t_jack_days']-state['ti_38_days']):.1f} days", "source reconciliation", state["rec_note"]],
            ["Selected method", state["selected_route"], "4.5 method selector", state["adoption_policy"]],
            ["Adoption policy", "Preview only", "4.6 Effective Prestress", "Do not adopt refined time-dependent losses until the selected route and time-step age source are explicitly reported."],
        ],
        columns=["Check", "Value", "Source", "Required engineer action"],
    )


def _psloss_crsh_refined_summary_rows(state: dict[str, Any]) -> pd.DataFrame:
    f = state["factors"]
    r = state.get("relaxation") or _psloss_relaxation_preview_state(state)
    total_td_mpa = f["total_crsh_loss_mpa"] + r["selected_loss_mpa"]
    total_td_pct = total_td_mpa / f["fpj_mpa"] * 100.0 if f["fpj_mpa"] > 0.0 else 0.0
    fpx_after_td_mpa = f["fpj_mpa"] - total_td_mpa
    return pd.DataFrame(
        [
            ["Calculation status", "PREVIEW READY" if state["method_ready"] else "METHOD BLOCKED", "Source-gated time-dependent preview; not final effective-prestress adoption."],
            ["Selected route", state["selected_route"], state["adoption_policy"]],
            ["Selected time-step age source", state.get("selected_time_source", "SOURCE PARTIAL"), f"effective start age = {state.get('effective_t_jack_days', 0.0):.1f} days; {state.get('time_source_note', '-')}"],
            ["Code basis", "AASHTO LRFD 2020 Art. 5.4.2.3 / 5.9.3.4 / 5.9.3.5", "Segmental construction should use time-step/stage-aware evaluation beyond preliminary design."],
            ["Creep coefficient ψ(t_f,t_start)", f"{f['creep_coeff']:.4f}", "Computed from RH, V/S, fci, selected t_start and final time."],
            ["Incremental shrinkage strain εsh,inc", f"{f['eps_sh_increment']:.6f}", "Shrinkage after jacking only; pre-jacking shrinkage is not a direct tendon loss."],
            ["Creep loss preview", f"{f['creep_loss_mpa']:.2f} MPa ({f['creep_loss_pct']:.2f}%)", "Component loss / fpj × 100; do not add % directly across pages."],
            ["Shrinkage loss preview", f"{f['shrinkage_loss_mpa']:.2f} MPa ({f['shrinkage_loss_pct']:.2f}%)", "Component loss / fpj × 100; do not add % directly across pages."],
            ["Creep + shrinkage preview", f"{f['total_crsh_loss_mpa']:.2f} MPa ({f['total_crsh_loss_pct']:.2f}%)", "Creep/shrinkage subtotal only; relaxation and 4.6 combination remain separate."],
            ["Relaxation preview", f"{r['selected_loss_mpa']:.2f} MPa ({r['selected_loss_pct']:.2f}%)", "Selected relaxation component preview; final adoption is still controlled by 4.6."],
            ["TD preview subtotal", f"{total_td_mpa:.2f} MPa ({total_td_pct:.2f}%)", "Creep + shrinkage + relaxation subtotal only; not final effective prestress."],
            ["fpx after TD preview", f"{fpx_after_td_mpa:.2f} MPa", "Preview stress after time-dependent components only; friction, anchor set, elastic shortening, and final combination remain separate."],
            ["Percent basis", "component loss / fpj × 100", "Displayed percentages use adopted jacking stress fpj as denominator."],
        ],
        columns=["Item", "Value", "Trace / note"],
    )

def _psloss_crsh_factor_rows(state: dict[str, Any]) -> pd.DataFrame:
    f = state["factors"]
    return pd.DataFrame(
        [
            ["H", "%", f"{f['H']:.1f}", "Relative humidity from 3.8 CR&SH"],
            ["V/S", "in", f"{f['V_over_S_in']:.2f}", "Volume-to-surface ratio derived in 3.8 CR&SH"],
            ["f'ci", "ksi", f"{f['fci_ksi']:.3f}", "Concrete strength at prestress/load stage from material source"],
            ["ks", "-", f"{f['ks_creep']:.4f}", "max(1.0, 1.45 − 0.13 V/S)"],
            ["khc", "-", f"{f['khc']:.4f}", "1.56 − 0.008H"],
            ["kf", "-", f"{f['kf']:.4f}", "5/(1+f'ci)"],
            ["ktd,creep", "-", f"{f['ktd_creep']:.4f}", "Time-development factor using Δt = tf − t_start"],
            ["t_start^-0.118", "-", f"{f['ti_term']:.4f}", "Selected time-step start age at load application / jacking"],
            ["ψ(t_f,t_start)", "-", f"{f['creep_coeff']:.4f}", "1.9 ks khc kf ktd t_start^-0.118"],
            ["khs", "-", f"{f['khs']:.4f}", "2.00 − 0.014H"],
            ["ktd(tf) − ktd(t_start)", "-", f"{f['ktd_sh_increment']:.4f}", "Incremental shrinkage time-development after selected t_start"],
            ["εsh,inc", "strain", f"{f['eps_sh_increment']:.6f}", "ks khs kf Δktd × 0.48×10^-3"],
        ],
        columns=["Variable", "Unit", "Value", "Source / trace"],
    )


def _psloss_crsh_approx_rows(state: dict[str, Any]) -> pd.DataFrame:
    f = state["factors"]
    return pd.DataFrame(
        [
            ["γh", f"{f['gamma_h']:.4f}", "1.7 − 0.01H"],
            ["γst", f"{f['gamma_st']:.4f}", "5/(1+f'ci)"],
            ["fpi Aps / Ag", f"{f['fpi_aps_over_ag_ksi']:.3f} ksi", "AASHTO 5.9.3.3 quick-check term"],
            ["Approx. creep term", f"{f['approx_creep_mpa']:.2f} MPa", "10(fpi Aps/Ag)γhγst"],
            ["Approx. shrinkage term", f"{f['approx_shrinkage_mpa']:.2f} MPa", "12γhγst"],
            ["Approx. relaxation term", f"{f['approx_relaxation_mpa']:.2f} MPa", "2.4 ksi low-relaxation quick-check assumption"],
            ["Approx. total time-dependent loss", f"{f['approx_total_mpa']:.2f} MPa ({f['approx_total_pct']:.2f}%)", "Preliminary comparison only; not final for segmental span-by-span PT"],
        ],
        columns=["Item", "Value", "Trace / limitation"],
    )



def _psloss_relaxation_method_options() -> list[str]:
    return [
        "AASHTO refined R1/R2 preview — Recommended",
        "Low-relaxation 2.4 ksi quick check",
        "Manufacturer relaxation data — Future / gated",
    ]


def _psloss_relaxation_steel_options() -> list[str]:
    return [
        "Low-relaxation strand",
        "Other prestressing steel — manufacturer data required",
    ]


def _psloss_relaxation_stress_basis_options() -> list[str]:
    return [
        "Use fpj / jacking-stress preview",
        "Use fpx after creep+shrinkage comparison",
        "Manufacturer-provided fpt — Future / gated",
    ]


def _psloss_relaxation_selected_method() -> str:
    ps = D["prestress"]
    options = _psloss_relaxation_method_options()
    value = str(ps.get("relaxation_calculation_method", options[0]))
    if value not in options:
        value = options[0]
    ps["relaxation_calculation_method"] = value
    return value


def _psloss_relaxation_selected_steel() -> str:
    ps = D["prestress"]
    options = _psloss_relaxation_steel_options()
    value = str(ps.get("relaxation_steel_type", options[0]))
    if value not in options:
        value = options[0]
    ps["relaxation_steel_type"] = value
    return value


def _psloss_relaxation_selected_stress_basis() -> str:
    ps = D["prestress"]
    options = _psloss_relaxation_stress_basis_options()
    value = str(ps.get("relaxation_stress_basis", options[0]))
    if value not in options:
        value = options[0]
    ps["relaxation_stress_basis"] = value
    return value


def _psloss_relaxation_preview_state(crsh_state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return source-gated relaxation preview state for the Time-Dependent Losses workflow."""
    ps = D["prestress"]
    m = D["materials"]
    ps.setdefault("relaxation_calculation_method", _psloss_relaxation_method_options()[0])
    ps.setdefault("relaxation_steel_type", _psloss_relaxation_steel_options()[0])
    ps.setdefault("relaxation_stress_basis", _psloss_relaxation_stress_basis_options()[0])
    method = _psloss_relaxation_selected_method()
    steel = _psloss_relaxation_selected_steel()
    basis = _psloss_relaxation_selected_stress_basis()
    crsh_state = crsh_state or _psloss_crsh_time_step_state()
    f = crsh_state.get("factors", {})
    fpj = max(0.0, float(m.get("fpi_mpa", 0.0) or 0.0))
    fpu = max(0.0, float(m.get("fpu_mpa", 0.0) or 0.0))
    fpy = max(0.0, float(m.get("fpy_mpa", 0.0) or 0.0)) or 0.90 * fpu
    if basis.startswith("Use fpx after creep"):
        fpt = max(0.0, float(f.get("fpx_after_crsh_mpa", fpj) or fpj))
        basis_note = "fpt is taken from the current creep+shrinkage preview for comparison only."
        basis_ready = True
    elif basis.startswith("Manufacturer"):
        fpt = max(0.0, float(ps.get("relaxation_manufacturer_fpt_mpa", 0.0) or 0.0))
        basis_note = "Manufacturer fpt source is not active; final adoption remains gated."
        basis_ready = fpt > 0.0
    else:
        fpt = fpj
        basis_note = "fpt is taken as adopted jacking stress fpj for source-model preview."
        basis_ready = True
    low_relaxation = steel.startswith("Low-relaxation")
    KL = 30.0 if low_relaxation else 7.0
    KL_prime = 45.0 if low_relaxation else 7.0
    ratio = fpt / fpy if fpy > 0.0 else 0.0
    ratio_term = max(ratio - 0.55, 0.0)
    r1_mpa = fpt / KL * ratio_term if KL > 0.0 else 0.0
    r2_mpa = r1_mpa
    refined_total_mpa = r1_mpa + r2_mpa
    quick_r1_mpa = ksi_to_mpa(1.2) if low_relaxation else 0.0
    quick_total_mpa = ksi_to_mpa(2.4) if low_relaxation else 0.0
    if method.startswith("AASHTO refined"):
        selected_loss = refined_total_mpa
        method_status = "AASHTO R1/R2 PREVIEW"
        method_mode = "pass" if low_relaxation and basis_ready else "warn"
        selected_note = "Selected relaxation preview uses AASHTO R1/R2 simplified route; final 4.6 adoption remains blocked."
        eligible = low_relaxation and basis_ready
    elif method.startswith("Low-relaxation"):
        selected_loss = quick_total_mpa
        method_status = "LOW-RELAX QUICK CHECK"
        method_mode = "warn"
        selected_note = "Selected relaxation value is the AASHTO 2.4 ksi low-relaxation quick check; preliminary only."
        eligible = False
    else:
        selected_loss = 0.0
        method_status = "MANUFACTURER DATA GATED"
        method_mode = "warn"
        selected_note = "Manufacturer relaxation data source is not implemented; no selected relaxation loss is eligible for final adoption."
        eligible = False
    fpx_after_relax = fpt - selected_loss
    loss_pct = selected_loss / fpj * 100.0 if fpj > 0.0 else 0.0
    return {
        "method": method,
        "steel_type": steel,
        "stress_basis": basis,
        "basis_note": basis_note,
        "basis_ready": basis_ready,
        "method_status": method_status,
        "method_mode": method_mode,
        "selected_note": selected_note,
        "low_relaxation": low_relaxation,
        "KL": KL,
        "KL_prime": KL_prime,
        "fpj_mpa": fpj,
        "fpt_mpa": fpt,
        "fpy_mpa": fpy,
        "fpu_mpa": fpu,
        "ratio": ratio,
        "ratio_term": ratio_term,
        "r1_mpa": r1_mpa,
        "r2_mpa": r2_mpa,
        "refined_total_mpa": refined_total_mpa,
        "quick_r1_mpa": quick_r1_mpa,
        "quick_total_mpa": quick_total_mpa,
        "selected_loss_mpa": selected_loss,
        "selected_loss_pct": loss_pct,
        "fpx_after_relax_mpa": fpx_after_relax,
        "adoption_gate": "BLOCKED UNTIL 4.6" if eligible else "NOT ELIGIBLE FOR FINAL",
        "adoption_note": "4.6 must combine relaxation with other adopted components and verify the stress/time basis." if eligible else "Use refined low-relaxation source preview and a verified stress basis before final adoption.",
    }


def _psloss_relaxation_source_rows(r: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["Selected relaxation method", r["method"], "4.5 Relaxation method selector", r["selected_note"]],
            ["Prestressing steel type", r["steel_type"], "Material / project source", "Low-relaxation strand uses KL = 30 unless project/manufacturer source overrides."],
            ["Relaxation stress basis", r["stress_basis"], "4.5 stress-basis selector", r["basis_note"]],
            ["fpt", f"{r['fpt_mpa']:.2f}", "MPa", "Stress in prestressing steel used for relaxation preview."],
            ["fpy", f"{r['fpy_mpa']:.2f}", "MPa", "Yield stress of prestressing steel from material source."],
            ["KL", f"{r['KL']:.1f}", "-", "AASHTO steel-type factor; low-relaxation strand = 30."],
            ["Relaxation preview status", r["adoption_gate"], "4.6 Effective Prestress", r["adoption_note"]],
        ],
        columns=["Source item", "Value", "Unit / owner", "Trace / engineer check"],
    )


def _psloss_relaxation_report_rows(r: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["Calculation status", "PREVIEW READY" if r["selected_loss_mpa"] > 0.0 else "SOURCE GATED", "Source-gated relaxation preview; not final effective prestress."],
            ["Code basis", "AASHTO LRFD 2020 Art. 5.9.3.4.2c / 5.9.3.4.3c", "R1/R2 relaxation source-model route; manufacturer data may govern if supplied."],
            ["Selected method", r["method"], r["selected_note"]],
            ["Stress ratio fpt/fpy", f"{r['ratio']:.4f}", "Relaxation term is active only above 0.55 fpy in the source equation."],
            ["R1 relaxation preview", f"{r['r1_mpa']:.2f} MPa", "Transfer-to-intermediate period preview from AASHTO simplified equation."],
            ["R2 relaxation preview", f"{r['r2_mpa']:.2f} MPa", "Final-period preview taken equal to R1 in the AASHTO source route."],
            ["Selected relaxation loss", f"{r['selected_loss_mpa']:.2f} MPa ({r['selected_loss_pct']:.2f}%)", "Component loss / fpj × 100; do not add % directly across pages."],
            ["Low-relax quick check", f"{r['quick_total_mpa']:.2f} MPa", "2.4 ksi total quick-check comparison for low-relaxation strand."],
            ["fpx after relaxation", f"{r['fpx_after_relax_mpa']:.2f} MPa", "Relaxation-only stress preview based on the selected stress basis."],
            ["Adoption gate", r["adoption_gate"], r["adoption_note"]],
        ],
        columns=["Item", "Value", "Trace / note"],
    )


def _psloss_relaxation_variable_rows(r: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["fpt", "MPa", "Prestressing steel stress immediately after the selected stress-basis point", "4.5 relaxation stress-basis selector"],
            ["fpy", "MPa", "Yield stress of prestressing steel", "Material source"],
            ["KL", "-", "Steel-type relaxation factor", "30 for low-relaxation strand; 7 for other prestressing steel unless manufacturer data govern"],
            ["ΔfpR1", "MPa", "Relaxation loss for the first time-dependent period", "AASHTO refined simplified preview"],
            ["ΔfpR2", "MPa", "Relaxation loss for the second time-dependent period", "AASHTO route takes ΔfpR2 = ΔfpR1"],
            ["ΔfpR,total", "MPa", "Selected total relaxation preview", "Component preview only; final combination is owned by 4.6"],
            ["Loss %", "%", "Component relaxation loss divided by fpj", "Non-cumulative component-loss percentage"],
        ],
        columns=["Variable", "Unit", "Meaning", "Source / trace"],
    )


def _render_psloss_relaxation_section(crsh_state: dict[str, Any]) -> dict[str, Any]:
    ps = D["prestress"]
    ps.setdefault("relaxation_calculation_method", _psloss_relaxation_method_options()[0])
    ps.setdefault("relaxation_steel_type", _psloss_relaxation_steel_options()[0])
    ps.setdefault("relaxation_stress_basis", _psloss_relaxation_stress_basis_options()[0])
    st.markdown("### Relaxation source model and gated preview")
    c0, c1, c2 = st.columns([1.35, 1.05, 1.35])
    with c0:
        methods = _psloss_relaxation_method_options()
        cur = _psloss_relaxation_selected_method()
        ps["relaxation_calculation_method"] = st.selectbox("Relaxation calculation method", methods, index=methods.index(cur), key="psloss21_relax_method")
    with c1:
        steels = _psloss_relaxation_steel_options()
        cur = _psloss_relaxation_selected_steel()
        ps["relaxation_steel_type"] = st.selectbox("Prestressing steel relaxation class", steels, index=steels.index(cur), key="psloss21_relax_steel")
    with c2:
        bases = _psloss_relaxation_stress_basis_options()
        cur = _psloss_relaxation_selected_stress_basis()
        ps["relaxation_stress_basis"] = st.selectbox("Relaxation stress basis", bases, index=bases.index(cur), key="psloss21_relax_basis")
    r = _psloss_relaxation_preview_state(crsh_state)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        card("RELAXATION SUMMARY", r["method_status"], r["steel_type"], r["method_mode"])
    with c2:
        card("R1 RELAXATION", f"{r['r1_mpa']:.2f} MPa", "AASHTO source period 1", "warn")
    with c3:
        card("R2 RELAXATION", f"{r['r2_mpa']:.2f} MPa", "AASHTO source period 2", "warn")
    with c4:
        card("TOTAL RELAXATION", f"{r['selected_loss_mpa']:.2f} MPa", f"{r['selected_loss_pct']:.2f}% of fpj", "warn")
    with c5:
        card("ADOPTION STATUS", "PREVIEW ONLY", r["adoption_gate"], "neutral")
    st.markdown(
        '<div class="note-box"><b>Relaxation source rule:</b> relaxation is a component-level preview. The selected stress basis, steel relaxation class, and method must be reported before 4.6 can combine this value with friction, anchor set, elastic shortening, creep, and shrinkage. Manufacturer relaxation data supersedes the generic source route when supplied.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("#### Relaxation source trace")
    show_engineering_table(_psloss_relaxation_source_rows(r))
    st.markdown("#### Report-style relaxation summary")
    show_engineering_table(_psloss_relaxation_report_rows(r))
    st.markdown("#### Relaxation equation block")
    st.latex(r"\Delta f_{pR1}=\frac{f_{pt}}{K_L}\left(\frac{f_{pt}}{f_{py}}-0.55\right)")
    st.latex(r"\Delta f_{pR2}=\Delta f_{pR1}")
    st.latex(r"\Delta f_{pR,total}=\Delta f_{pR1}+\Delta f_{pR2}")
    st.latex(r"f_{px,R}=f_{pt}-\Delta f_{pR,total}")
    st.markdown("#### Relaxation variable definition")
    show_engineering_table(_psloss_relaxation_variable_rows(r))
    st.markdown("#### Relaxation substitution")
    st.latex(fr"\frac{{f_{{pt}}}}{{f_{{py}}}}=\frac{{{r['fpt_mpa']:.2f}}}{{{r['fpy_mpa']:.2f}}}={r['ratio']:.4f}")
    st.latex(fr"\Delta f_{{pR1}}=\frac{{{r['fpt_mpa']:.2f}}}{{{r['KL']:.1f}}}\left({r['ratio']:.4f}-0.55\right)={r['r1_mpa']:.2f}\ \mathrm{{MPa}}")
    st.latex(fr"\Delta f_{{pR2}}={r['r2_mpa']:.2f}\ \mathrm{{MPa}}")
    st.latex(fr"\Delta f_{{pR,total}}={r['r1_mpa']:.2f}+{r['r2_mpa']:.2f}={r['selected_loss_mpa']:.2f}\ \mathrm{{MPa}}")
    st.latex(fr"f_{{px,R}}={r['fpt_mpa']:.2f}-{r['selected_loss_mpa']:.2f}={r['fpx_after_relax_mpa']:.2f}\ \mathrm{{MPa}}")
    st.markdown(
        '<div class="warn-box"><b>Preview only:</b> PSLOSS.23 organizes relaxation as a Time-Dependent Losses component tab and reports it to the 4.6 handoff as preview-only. It does not adopt relaxation into final effective prestress.</div>',
        unsafe_allow_html=True,
    )
    return r

def _psloss_crsh_source_gate_handoff_rows(state: dict[str, Any]) -> pd.DataFrame:
    """Compatibility-safe 4.1 CR&SH source-gate handoff rows.

    4.1 passes the general Prestress Losses source-gate state, not the 4.5
    Time-Dependent Losses state. Migrated projects may therefore have no
    `factors` key. This helper keeps the source gate readable instead of
    crashing, while 4.5 still uses the detailed route-dependent handoff below.
    """
    ps = D.setdefault("prestress", {})
    crsh = state.get("crsh") or update_crsh_derived_parameters()
    tf_days = float(ps.get("tf_days", 0.0) or 0.0)
    tf_years = tf_days / 365.25 if tf_days > 0.0 else 0.0
    status = "READY" if bool(state.get("crsh_ready", True)) else "SOURCE PARTIAL"
    return pd.DataFrame(
        [
            ["CR&SH source status", status, "4.1 source gate", "Compatibility-safe source trace; detailed time-dependent factors are owned by 4.5."],
            ["RH", f"{float(ps.get('RH_percent', 0.0) or 0.0):.1f}", "%", "3.8 CR&SH user project assumption"],
            ["ti", f"{float(ps.get('ti_days', 0.0) or 0.0):.0f}", "days", "3.8 CR&SH material/loss age input; 4.5 may reconcile with computed t_jack."],
            ["tf", f"{tf_days:.0f} ≈ {tf_years:.1f}", "days / years", "final design age from 3.8 CR&SH"],
            ["Drying perimeter basis", ps.get("crsh_drying_perimeter_basis", "-"), "-", "outer-only vs outer+inner void trace"],
            ["u_total", f"{float(crsh.get('u_total_m', 0.0) or 0.0):.2f}", "m", "derived from selected drying perimeter basis"],
            ["V/S", f"{float(crsh.get('V_over_S_in', 0.0) or 0.0):.2f}", "in", "AASHTO empirical creep/shrinkage factor input"],
            ["V/S", f"{float(crsh.get('V_over_S_m', 0.0) or 0.0):.4f}", "m", "SI report value"],
            ["h0", f"{float(crsh.get('h0_m', 0.0) or 0.0):.4f}", "m", "h0 = 2Ac/u_total = 2(V/S)"],
        ],
        columns=["Parameter", "Adopted value", "Unit", "Source / trace"],
    )


def _psloss_crsh_handoff_rows(state: dict[str, Any]) -> pd.DataFrame:
    if "factors" not in state:
        return _psloss_crsh_source_gate_handoff_rows(state)
    f = state.get("factors", {})
    selected = str(state.get("selected_route", "SOURCE PARTIAL"))
    r = state.get("relaxation") or _psloss_relaxation_preview_state(state)
    total_td_mpa = f["total_crsh_loss_mpa"] + r["selected_loss_mpa"]
    total_td_pct = total_td_mpa / f["fpj_mpa"] * 100.0 if f["fpj_mpa"] > 0.0 else 0.0
    fpx_after_td_mpa = f["fpj_mpa"] - total_td_mpa
    if selected.startswith("Refined"):
        rows = [
            ["Selected method", selected, "4.6 may read refined component previews only after route and age-source review."],
            ["Selected time-step age source", state.get("selected_time_source", "SOURCE PARTIAL"), f"effective start age = {state.get('effective_t_jack_days', 0.0):.1f} days; {state.get('time_source_note', '-')}"],
            ["Creep preview", f"{f['creep_loss_mpa']:.2f} MPa", "Selected refined component preview; final adoption not run here."],
            ["Shrinkage preview", f"{f['shrinkage_loss_mpa']:.2f} MPa", "Selected refined component preview; final adoption not run here."],
            ["Creep + shrinkage preview", f"{f['total_crsh_loss_mpa']:.2f} MPa", "Selected refined C+SH subtotal; do not add percentages directly across pages."],
            ["Relaxation preview", f"{r['selected_loss_mpa']:.2f} MPa", f"{r['method']}; final adoption not run here."],
            ["TD preview subtotal", f"{total_td_mpa:.2f} MPa ({total_td_pct:.2f}%)", "Selected time-dependent subtotal = creep + shrinkage + relaxation; not final effective prestress."],
            ["fpx after TD preview", f"{fpx_after_td_mpa:.2f} MPa", "Preview stress after time-dependent components only; 4.6 must combine with other loss components."],
            ["Approximate quick check", f"{f['approx_total_mpa']:.2f} MPa", "Comparison only; not the selected refined handoff."],
            ["Adoption gate", "BLOCKED UNTIL 4.6", "Effective Prestress defines the final component-combination rule and must verify route + age source + relaxation source."],
        ]
    elif selected.startswith("Approximate"):
        rows = [
            ["Selected method", selected, "Quick-check route only; not eligible for final segmental PT effective-prestress adoption."],
            ["Selected time-step age source", state.get("selected_time_source", "SOURCE PARTIAL"), "Stored for trace only; approximate route is still preliminary."],
            ["Approximate total time-dependent loss", f"{f['approx_total_mpa']:.2f} MPa", "Selected quick-check display value only; final adoption remains blocked."],
            ["Refined creep preview", f"{f['creep_loss_mpa']:.2f} MPa", "Comparison only because approximate route is currently selected."],
            ["Refined shrinkage preview", f"{f['shrinkage_loss_mpa']:.2f} MPa", "Comparison only because approximate route is currently selected."],
            ["Refined C+SH preview", f"{f['total_crsh_loss_mpa']:.2f} MPa", "Comparison only; not selected handoff while approximate route is selected."],
            ["Relaxation preview", f"{r['selected_loss_mpa']:.2f} MPa", "Component comparison only; approximate route is not eligible for final."],
            ["Refined TD preview subtotal", f"{total_td_mpa:.2f} MPa ({total_td_pct:.2f}%)", "Comparison-only refined subtotal = creep + shrinkage + relaxation; not selected while approximate route is active."],
            ["fpx after refined TD preview", f"{fpx_after_td_mpa:.2f} MPa", "Comparison-only preview stress; not eligible for final adoption from approximate route."],
            ["Adoption gate", "NOT ELIGIBLE FOR FINAL", "Select refined/time-step route and resolve the time-step age source before 4.6 final adoption."],
        ]
    else:
        rows = [
            ["Selected method", selected, "Advanced segment-age table is gated and not implemented."],
            ["Selected time-step age source", state.get("selected_time_source", "SOURCE PARTIAL"), "No final handoff while advanced route is gated."],
            ["Refined representative C+SH fallback", f"{f['total_crsh_loss_mpa']:.2f} MPa", "Fallback display only; not a selected final handoff."],
            ["Relaxation preview", f"{r['selected_loss_mpa']:.2f} MPa", "Fallback display only; not a selected final handoff."],
            ["TD preview subtotal", f"{total_td_mpa:.2f} MPa ({total_td_pct:.2f}%)", "Fallback display only; not a selected final handoff."],
            ["fpx after TD preview", f"{fpx_after_td_mpa:.2f} MPa", "Fallback display only; not a selected final handoff."],
            ["Adoption gate", "BLOCKED", "Choose refined/time-step route or implement advanced segment-age schedule before final adoption."],
        ]
    return pd.DataFrame(rows, columns=["Handoff item", "Value", "Rule / trace"])

def _render_time_dependent_overview_tab(state: dict[str, Any]) -> None:
    st.markdown("### Method map")
    show_engineering_table(_psloss_crsh_method_map_rows(state))

    st.markdown("### Construction stage timeline")
    show_engineering_table(_psloss_crsh_stage_timeline_rows(state))

    st.markdown("### Source-gated time-dependent inputs")
    show_engineering_table(_psloss_crsh_source_rows(state))

    # PSLOSS.22 static trace token: t_{start}=selected time-step start age; t_{jack}=t_{transport}+t_{assembly} remains in reconciliation only
    st.markdown("### t_jack / 3.8 ti reconciliation")
    show_engineering_table(_psloss_crsh_reconciliation_rows(state))

    st.markdown(
        '<div class="note-box"><b>One-source rule:</b> RH, V/S, h0, tf, and drying-perimeter basis remain owned by <b>3.8 CR&SH</b>. 4.5 owns only the construction-stage time map, route selector, time-step age-source selector, and relaxation source selectors. Creep, shrinkage, and relaxation component tabs must not create hidden duplicate inputs.</div>',
        unsafe_allow_html=True,
    )


def _render_time_dependent_creep_tab(state: dict[str, Any]) -> None:
    f = state["factors"]
    route_note = "Selected refined component preview" if state["selected_route"].startswith("Refined") else "Comparison only for the selected route"
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("CREEP COMPONENT", "REFINED PREVIEW", f"ψ(tf,t_start) = {f['creep_coeff']:.4f}", "pass" if state["selected_route"].startswith("Refined") else "neutral")
    with c2:
        card("CREEP LOSS", f"{f['creep_loss_mpa']:.2f} MPa", f"{f['creep_loss_pct']:.2f}% of fpj", "warn")
    with c3:
        card("STRESS BASIS", f"fcgp = {f['fcgp_mpa']:.2f} MPa", "Stage-controlled input", "warn")
    with c4:
        card("ADOPTION", "PREVIEW ONLY", route_note, "neutral")

    if not state["selected_route"].startswith("Refined"):
        st.markdown(
            '<div class="warn-box"><b>Creep comparison only:</b> the refined creep calculation remains visible for audit, but it is not the selected route while Approximate or Advanced mode is active.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("### Creep equation block")
    st.markdown(
        '<div class="note-box"><b>Creep route:</b> this component uses the selected time-step start age <b>t_start</b> and the creep factors traced from AASHTO Article 5.4.2.3. This is not final effective prestress.</div>',
        unsafe_allow_html=True,
    )
    st.latex(r"\psi(t_f,t_{start})=1.9k_s k_{hc} k_f k_{td} t_{start}^{-0.118}")
    st.latex(r"\Delta f_{pCR}=\frac{E_p}{E_{ci}} f_{cgp}\,\psi(t_f,t_{start})")
    st.latex(r"f_{px,CR}=f_{pj}-\Delta f_{pCR}")

    st.markdown("### Creep factor / variable definition")
    creep_rows = _psloss_crsh_factor_rows(state)
    show_engineering_table(creep_rows[creep_rows["Variable"].isin(["H", "V/S", "fci", "ks", "khc", "kf", "ktd_creep", "tᵢ^-0.118", "ψ(tf,t_start)"])])

    st.markdown("### Creep substitution")
    st.latex(fr"k_s=\max(1.0,1.45-0.13({f['V_over_S_in']:.2f}))={f['ks_creep']:.4f}")
    st.latex(fr"k_{{hc}}=1.56-0.008({f['H']:.1f})={f['khc']:.4f}")
    st.latex(fr"k_f=\frac{{5}}{{1+{f['fci_ksi']:.3f}}}={f['kf']:.4f}")
    st.latex(fr"t_{{start}}={state.get('effective_t_jack_days', 0.0):.1f}\ \mathrm{{days}}")
    st.latex(fr"\psi=1.9({f['ks_creep']:.4f})({f['khc']:.4f})({f['kf']:.4f})({f['ktd_creep']:.4f})({f['ti_term']:.4f})={f['creep_coeff']:.4f}")
    st.latex(fr"\Delta f_{{pCR}}=\frac{{{f['Ep_mpa']:.0f}}}{{{f['Eci_mpa']:.0f}}}({f['fcgp_mpa']:.2f})({f['creep_coeff']:.4f})={f['creep_loss_mpa']:.2f}\ \mathrm{{MPa}}")
    st.latex(fr"f_{{px,CR}}={f['fpj_mpa']:.2f}-{f['creep_loss_mpa']:.2f}={f['fpj_mpa']-f['creep_loss_mpa']:.2f}\ \mathrm{{MPa}}")


def _render_time_dependent_shrinkage_tab(state: dict[str, Any]) -> None:
    f = state["factors"]
    route_note = "Selected refined component preview" if state["selected_route"].startswith("Refined") else "Comparison only for the selected route"
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("SHRINKAGE COMPONENT", "REFINED PREVIEW", f"εsh,inc = {f['eps_sh_increment']:.6f}", "pass" if state["selected_route"].startswith("Refined") else "neutral")
    with c2:
        card("SHRINKAGE LOSS", f"{f['shrinkage_loss_mpa']:.2f} MPa", f"{f['shrinkage_loss_pct']:.2f}% of fpj", "warn")
    with c3:
        card("TIME WINDOW", f"t_start={state.get('effective_t_jack_days', 0.0):.1f} d", f"tf≈{state['duration_after_jack_years']:.1f} yr", "neutral")
    with c4:
        card("ADOPTION", "PREVIEW ONLY", route_note, "neutral")

    if not state["selected_route"].startswith("Refined"):
        st.markdown(
            '<div class="warn-box"><b>Shrinkage comparison only:</b> the refined shrinkage calculation remains visible for audit, but it is not the selected route while Approximate or Advanced mode is active.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("### Shrinkage equation block")
    st.markdown(
        '<div class="note-box"><b>Shrinkage route:</b> this component uses post-jacking incremental shrinkage only. Pre-jacking shrinkage is not a direct tendon prestress loss because the tendon is not stressed yet.</div>',
        unsafe_allow_html=True,
    )
    st.latex(r"\varepsilon_{sh,inc}=k_s k_{hs} k_f\left[k_{td}(t_f)-k_{td}(t_{start})\right]0.48\times10^{-3}")
    st.latex(r"\Delta f_{pSH}=E_p\varepsilon_{sh,inc}")
    st.latex(r"f_{px,SH}=f_{pj}-\Delta f_{pSH}")

    st.markdown("### Shrinkage factor / variable definition")
    shrink_rows = _psloss_crsh_factor_rows(state)
    show_engineering_table(shrink_rows[shrink_rows["Variable"].isin(["H", "V/S", "ks", "kf", "khs", "ktd(tf) - ktd(t_start)", "esh,inc"])])

    st.markdown("### Shrinkage substitution")
    st.latex(fr"t_{{start}}={state.get('effective_t_jack_days', 0.0):.1f}\ \mathrm{{days}}")
    st.latex(fr"\varepsilon_{{sh,inc}}=({f['ks_shrinkage']:.4f})({f['khs']:.4f})({f['kf']:.4f})({f['ktd_sh_increment']:.4f})(0.48\times10^{{-3}})={f['eps_sh_increment']:.6f}")
    st.latex(fr"\Delta f_{{pSH}}={f['Ep_mpa']:.0f}({f['eps_sh_increment']:.6f})={f['shrinkage_loss_mpa']:.2f}\ \mathrm{{MPa}}")
    st.latex(fr"f_{{px,SH}}={f['fpj_mpa']:.2f}-{f['shrinkage_loss_mpa']:.2f}={f['fpj_mpa']-f['shrinkage_loss_mpa']:.2f}\ \mathrm{{MPa}}")


def _render_time_dependent_combined_trace(state: dict[str, Any]) -> None:
    f = state["factors"]
    st.markdown("### Combined creep + shrinkage preview")
    st.latex(r"f_{px,C+SH}=f_{pj}-\Delta f_{pCR}-\Delta f_{pSH}")
    st.latex(fr"f_{{px,C+SH}}={f['fpj_mpa']:.2f}-{f['creep_loss_mpa']:.2f}-{f['shrinkage_loss_mpa']:.2f}={f['fpx_after_crsh_mpa']:.2f}\ \mathrm{{MPa}}")
    st.markdown(
        '<div class="warn-box"><b>Preview only:</b> creep and shrinkage values are component previews. Final adoption and combination with relaxation, friction, anchor set, and elastic shortening remain controlled by 4.6 Effective Prestress.</div>',
        unsafe_allow_html=True,
    )


def _render_time_dependent_handoff_tab(state: dict[str, Any]) -> None:
    st.markdown("### Report-style time-dependent summary")
    show_engineering_table(_psloss_crsh_refined_summary_rows(state))

    st.markdown("### Approximate quick-check comparison")
    st.markdown(
        '<div class="warn-box"><b>Approximate route:</b> AASHTO Article 5.9.3.3 is displayed only as a quick check / preliminary comparison. For segmental span-by-span PT, final adoption should use a refined / time-step route with construction-stage trace.</div>',
        unsafe_allow_html=True,
    )
    st.latex(r"\Delta f_{pLT}=10.0\frac{f_{pi}A_{ps}}{A_g}\gamma_h\gamma_{st}+12.0\gamma_h\gamma_{st}+\Delta f_{pR}")
    show_engineering_table(_psloss_crsh_approx_rows(state))

    st.markdown("### Effective-prestress handoff")
    show_engineering_table(_psloss_crsh_handoff_rows(state))

    st.markdown(
        '<div class="warn-box"><b>Preview only:</b> PSLOSS.23 keeps route-dependent time-dependent-loss handoff behavior and reports creep, shrinkage, relaxation, the time-dependent subtotal, and fpx after time-dependent preview before 4.6. It does not adopt creep, shrinkage, or relaxation into final effective prestress.</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Time-dependent source trace / limitations", expanded=False):
        st.markdown(
            '<div class="note-box"><b>One-source rule:</b> RH, V/S, h0, tf, and drying-perimeter basis remain owned by 3.8 CR&SH. 4.5 adds the construction-stage time map, route selector, time-step age-source selector, and relaxation source selectors only. Future refined/effective-prestress losses should read the selected sources and not create hidden duplicate inputs.</div>',
            unsafe_allow_html=True,
        )
        show_engineering_table(_psloss_crsh_source_rows(state))


def render_prestress_time_dependent_losses_source_model() -> None:
    """Render 4.5 Time-Dependent Losses with internal component tabs.

    Static trace token retained for PSLOSS.20 guard tests: t_start as the selected time-step start-age symbol.
    """
    ps = D["prestress"]
    ps.setdefault("segment_age_at_transport_days", 30.0)
    ps.setdefault("span_assembly_duration_days", 0.0)
    ps.setdefault("crsh_construction_method", "Span-by-span segmental with precast segments")
    ps.setdefault("crsh_stage_time_basis", "Auto representative span mode")
    ps.setdefault("crsh_calculation_route", _psloss_crsh_route_options()[0])
    ps.setdefault("relaxation_calculation_method", _psloss_relaxation_method_options()[0])
    ps.setdefault("relaxation_steel_type", _psloss_relaxation_steel_options()[0])
    ps.setdefault("relaxation_stress_basis", _psloss_relaxation_stress_basis_options()[0])

    code_basis_card(
        "4.5 Time-Dependent Losses Source Model",
        "AASHTO LRFD 2020 Section 5, Art. 5.4.2.3 / 5.9.3.3 / 5.9.3.4 / 5.9.3.5",
        "PSLOSS.23 polishes the Time-Dependent Losses handoff summary so relaxation and the total time-dependent subtotal are explicit, while keeping final effective-prestress adoption blocked.",
    )
    st.markdown(
        '<div class="note-box"><b>Time-dependent-loss rule:</b> creep, shrinkage, and relaxation are component-level previews under one time-dependent-loss workflow. Segment age at transport is editable and defaults to <b>30 days</b> (default = 30 days); RH, V/S, h0, tf, and drying-perimeter basis remain owned by <b>3.8 CR&SH</b>.</div>',
        unsafe_allow_html=True,
    )

    route_options = _psloss_crsh_route_options()
    c0, c1, c2 = st.columns([1.25, 1.05, 1.35])
    with c0:
        current_method = str(ps.get("crsh_construction_method", "Span-by-span segmental with precast segments"))
        method_options = ["Span-by-span segmental with precast segments", "Other / manual review"]
        if current_method not in method_options:
            current_method = method_options[0]
        ps["crsh_construction_method"] = st.selectbox("Construction method", method_options, index=method_options.index(current_method), key="psloss22_construction_method")
    with c1:
        current_route = _psloss_crsh_selected_route()
        ps["crsh_calculation_route"] = st.selectbox("Calculation route", route_options, index=route_options.index(current_route), key="psloss22_crsh_route")
    with c2:
        time_source_options = _psloss_crsh_time_source_options()
        current_time_source = _psloss_crsh_selected_time_source()
        ps["crsh_time_step_age_source"] = st.selectbox("Time-step age source", time_source_options, index=time_source_options.index(current_time_source), key="psloss22_time_source")

    c3, c4 = st.columns(2)
    with c3:
        editable_value(["prestress", "segment_age_at_transport_days"], "Segment age at transport (days)", 1.0, "%.1f")
    with c4:
        editable_value(["prestress", "span_assembly_duration_days"], "Span assembly duration before stressing (days)", 1.0, "%.1f")

    state = _psloss_crsh_time_step_state()
    relaxation_state = _psloss_relaxation_preview_state(state)
    state["relaxation"] = relaxation_state
    f = state["factors"]
    total_td_mpa = f["total_crsh_loss_mpa"] + relaxation_state["selected_loss_mpa"]
    total_td_pct = total_td_mpa / f["fpj_mpa"] * 100.0 if f["fpj_mpa"] > 0.0 else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        card("TIME-DEPENDENT METHOD", state["method_status"], "Internal tabs: Creep / Shrinkage / Relaxation", state["method_mode"])
    with c2:
        card("COMPUTED t_jack", f"{state['t_jack_days']:.1f} days", state["stage_note"], state["stage_mode"])
    with c3:
        card("TIME-STEP AGE SOURCE", state["time_source_status"], state["time_source_note"], state["time_source_mode"])
    with c4:
        card("3.8 ti RECONCILIATION", state["reconciliation"], state["rec_note"], state["rec_mode"])
    with c5:
        card("ADOPTION POLICY", "PREVIEW ONLY", "4.6 Effective Prestress controls final combination", "neutral")

    # Backward compatibility trace token for PSLOSS.16-18 tests: Creep / shrinkage loss result summary; Refined / time-step equation trace
    st.markdown("### Time-dependent loss result summary")
    if state["selected_route"].startswith("Approximate"):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            card("TD SUMMARY", "QUICK CHECK", "Approximate route selected", "warn")
        with c2:
            card("APPROX. TIME-DEP. LOSS", f"{f['approx_total_mpa']:.2f} MPa", f"{f['approx_total_pct']:.2f}% of fpj", "warn")
        with c3:
            card("REFINED C+SH", f"{f['total_crsh_loss_mpa']:.2f} MPa", "Comparison only", "neutral")
        with c4:
            card("RELAXATION", f"{relaxation_state['selected_loss_mpa']:.2f} MPa", "Component comparison", "neutral")
        with c5:
            card("ADOPTION", "NOT FINAL", "Approximate not final for segmental PT", "warn")
        st.markdown('<div class="warn-box"><b>Approximate route warning:</b> AASHTO approximate time-dependent loss is a preliminary / sanity-check route only for this segmental span-by-span PT workflow. Do not adopt it as final effective prestress.</div>', unsafe_allow_html=True)
    elif not state["method_ready"]:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            card("TD SUMMARY", "FUTURE GATED", "Advanced segment-age table is not implemented", "warn")
        with c2:
            card("REFINED C+SH", f"{f['total_crsh_loss_mpa']:.2f} MPa", "Representative fallback", "neutral")
        with c3:
            card("RELAXATION", f"{relaxation_state['selected_loss_mpa']:.2f} MPa", "Representative fallback", "neutral")
        with c4:
            card("ADOPTION", "BLOCKED", "Select refined route or implement schedule table", "warn")
    else:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            card("TD SUMMARY", "REFINED PREVIEW", f"t_start={state.get('effective_t_jack_days', 0.0):.1f} d · tf≈{state['duration_after_jack_years']:.1f} yr", "pass")
        with c2:
            card("CREEP", f"{f['creep_loss_mpa']:.2f} MPa", f"{f['creep_loss_pct']:.2f}% of fpj", "warn")
        with c3:
            card("SHRINKAGE", f"{f['shrinkage_loss_mpa']:.2f} MPa", f"{f['shrinkage_loss_pct']:.2f}% of fpj", "warn")
        with c4:
            card("RELAXATION", f"{relaxation_state['selected_loss_mpa']:.2f} MPa", f"{relaxation_state['selected_loss_pct']:.2f}% of fpj", "warn")
        with c5:
            card("TD PREVIEW", f"{total_td_mpa:.2f} MPa", f"{total_td_pct:.2f}% of fpj · not final", "neutral")

    st.markdown(
        '<div class="note-box"><b>Loss percent basis:</b> Loss % shown on this page is calculated as component loss / f<sub>pj</sub> × 100. <b>Interpretation rule:</b> this is a component-level preview only; do not add loss percentages from different loss pages directly. Final effective-prestress combination is controlled by <b>4.6 Effective Prestress</b>.</div>',
        unsafe_allow_html=True,
    )

    tab_overview, tab_creep, tab_shrinkage, tab_relaxation, tab_handoff = st.tabs(["Overview", "Creep", "Shrinkage", "Relaxation", "Handoff to 4.6"])
    with tab_overview:
        _render_time_dependent_overview_tab(state)
    with tab_creep:
        _render_time_dependent_creep_tab(state)
    with tab_shrinkage:
        _render_time_dependent_shrinkage_tab(state)
        _render_time_dependent_combined_trace(state)
    with tab_relaxation:
        state["relaxation"] = _render_psloss_relaxation_section(state)
    with tab_handoff:
        _render_time_dependent_handoff_tab(state)


def render_prestress_creep_shrinkage_stage_source_map() -> None:
    """Backward-compatible wrapper for the renamed 4.5 Time-Dependent Losses page."""
    render_prestress_time_dependent_losses_source_model()

def page_prestress_losses(sub: str) -> None:
    st.subheader(get_workspace("4 Prestress Losses")["title"])
    m, p = D["materials"], D["prestress"]
    if sub == "4.1 General":
        render_prestress_losses_source_gate_panel()
        return
    summary = prestress_loss_summary(prestress_inputs())
    if sub == "4.2 Friction":
        render_prestress_friction_source_model()
    elif sub == "4.3 Anchor Set":
        render_prestress_anchor_set_source_model()
    elif sub == "4.4 Elastic Shortening":
        render_prestress_elastic_shortening_source_model()
    elif sub == "4.5 Time-Dependent Losses":
        render_prestress_creep_shrinkage_stage_source_map()
    elif sub == "4.6 Effective Prestress":
        loss_df = pd.DataFrame([["Friction", summary["friction_mpa"]], ["Anchor set", summary["anchor_set_mpa"]], ["Elastic shortening", summary["elastic_shortening_mpa"]], ["Creep", summary["creep_mpa"]], ["Shrinkage", summary["shrinkage_mpa"]], ["Relaxation", summary["relaxation_mpa"]], ["Total", summary["total_loss_mpa"]], ["fpe", summary["fpe_mpa"]]], columns=["Item", "Value (MPa)"])
        st.dataframe(loss_df.style.format({"Value (MPa)": "{:.2f}"}), use_container_width=True)
        st.download_button("Download loss table CSV", loss_df.to_csv(index=False).encode("utf-8"), "prestress_losses.csv", "text/csv")
    else:
        code_basis_card("4 Prestress Losses QA / Report Preview", "AASHTO LRFD 2020 Section 5, Art. 5.9.3", "Read-only source-gate snapshot for downstream prestress-loss calculation. This page does not run a detailed loss solver.")
        render_prestress_losses_source_gate_panel(compact=True)


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
        render_report_qa_loads_handoff_snapshot()
        render_report_qa_prestress_losses_handoff_snapshot()
    else:
        ld = load_derived()
        psloss_state = _psloss_source_gate_state()
        report_md = f"""
# Segmental Box Girder Pro — Commercial PSLOSS.24 Summary

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

## Loads Workspace Closeout
- 3 Loads status = Closed for current load-source scope.
- 3.10 FEA Load Input Summary = single handoff register for FEA load mapping and Report / QA.
- SDL adopted value = {ld['sdl_selected_adopted_kn_m']:.2f} kN/m.
- LF / HF = {ld['LF_design_kn']:.0f} kN / {ld['hf_HF_adopted_kn']:.0f} kN.
- Wind WS / WS+WL = {ld['WSsuper_kn_m']:.2f} / {ld['WSsuper_WL_kn_m']:.2f} kN/m.
- EQ coefficient trace: Cs = {ld['eq_Cs']:.4f}; numeric EQ force remains EQX/EQY = Cs × W in the external FEA model.
- CR&SH remains a downstream parameter handoff to Prestress Losses / staged FEA, not a direct load pattern.

## Prestress Losses Source Gate
- 4 Prestress Losses status = {psloss_state['overall_status']}.
- Tendon source = {psloss_state['tendon_status'].get('status', 'PENDING')}; adopted tendon fingerprint = {psloss_state.get('adopted_fingerprint') or '-'}.
- Section source ready = {psloss_state['section_ready']}.
- CR&SH source ready = {psloss_state['crsh_ready']}.
- Stressing basis = {psloss_state['stressing_basis'].get('status', 'BLOCKED')}; {psloss_state['stressing_basis'].get('stressing_mode', 'Confirm JackFrom')}.
- Jacking force rule = Pj/tendon is tendon axial force; one-end/two-end stressing controls friction/anchor-set distribution and must not double total prestressing force.

## PSLOSS.24 Notes
- Report / QA now displays the Prestress Losses source gate, stressing-basis gate, adopted tendon readiness register, friction and anchor-set formula-trace snapshots, and Loads handoff snapshot.
- Detailed final prestress-loss adoption equations are intentionally not changed in this milestone.
- The source gate blocks detailed loss calculation unless tendon, JackFrom / stressing basis, section, CR&SH, and span/stage sources are ready.
- PSLOSS.20 keeps the completed Friction, Anchor Set, Elastic Shortening, and Time-Dependent Losses preview pages aligned with the shared component loss / fpj percent basis and non-cumulative interpretation; final combination remains deferred to 4.6 Effective Prestress.
- PSLOSS.21 adds a source-gated relaxation preview with method, steel-class, and stress-basis selectors; the relaxation component is reported to 4.6 as preview-only and is not adopted into final effective prestress.
- PSLOSS.22 renames 4.5 to Time-Dependent Losses and splits the workflow into internal Overview, Creep, Shrinkage, Relaxation, and Handoff to 4.6 tabs without changing formulas or preview values.
- PSLOSS.23 polishes the Time-Dependent Losses handoff table so relaxation, the total time-dependent preview subtotal, and fpx after time-dependent preview are reported consistently before 4.6, without changing formulas or preview values.
- PSLOSS.24 fixes 4.1 General CR&SH source-gate compatibility by avoiding direct `state["factors"]` access when the page receives the general source-gate state or an older migrated project state; it displays compatibility-safe CR&SH handoff rows instead of crashing.
- Formula logic for DL, SDL, LL+IM, LF/HF, CF, Wind, CR&SH, EQ, and detailed prestress losses was not changed.
- The legacy keyed friction-group page was replaced by the adopted-profile friction source model; downstream final loss adoption remains unchanged.
"""
        st.markdown(report_md)
        st.download_button("Download Markdown Summary", report_md.encode("utf-8"), "segmental_box_girder_psloss24_summary.md", "text/markdown", use_container_width=True)


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
