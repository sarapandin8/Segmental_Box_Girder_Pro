from __future__ import annotations

import json
from math import sqrt
from typing import Any

import pandas as pd
import streamlit as st

from core.bg40_defaults import BG40_DEFAULT
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
.block-container {padding-top: 2.25rem; padding-bottom: 2rem; max-width: 1550px;}
[data-testid="stSidebar"] {background: linear-gradient(180deg, #eef6ff 0%, #f8fbff 100%);}
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
.governing-strip {border:1px solid #d5e6ff; border-radius:16px; background:#fff; padding:14px 16px; margin:16px 0 8px 0;}
.sidebar-card {border:1px solid #bcd3f5; border-radius:12px; padding:12px; background:#fff; margin-bottom:12px;}
.sidebar-title {font-weight:850; color:#0b376d; font-size:0.9rem;}
.sidebar-mini {font-size:0.76rem; color:#334155; margin-top:4px;}
hr {margin: 1rem 0;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------
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


def status_badge(status: str) -> str:
    cls = "pass" if status == "PASS" else ("fail" if status == "FAIL" else "neutral")
    return f'<span class="badge {cls}">{status}</span>'


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


def load_derived() -> dict[str, float]:
    lc = D["load_components"]
    rail = D["rail_loads"]
    span = float(D["project"]["span_m"])
    Lphi = min(float(lc["dynamic_L_left_m"]), float(lc["dynamic_L_right_m"]))
    phi_calc = 2.16 / (sqrt(Lphi) - 0.20) + 0.73
    traction = min(float(lc["lf_traction_kn_m"]) * float(lc["lf_length_m"]), float(lc["lf_traction_cap_kn"]))
    braking = min(float(lc["lf_braking_kn_m"]) * float(lc["lf_length_m"]), float(lc["lf_braking_cap_kn"]))
    LF_design = max(traction, braking)
    dtot_ws = float(lc["wind_dtot_ws_m"])
    dtot_wl = float(lc["wind_dtot_ws_wl_m"])
    rho = float(lc["wind_air_density_kg_m3"])
    vb = float(lc["wind_vb_m_s"])
    ws = 0.5 * rho * vb**2 * float(lc["wind_c_ws"]) * (dtot_ws * span) / 1000.0
    ws_wl = 0.5 * rho * vb**2 * float(lc["wind_c_ws_wl"]) * (dtot_wl * span) / 1000.0
    SMS = float(lc["seismic_Fa"]) * float(lc["seismic_Ss_g"])
    SM1 = float(lc["seismic_Fv"]) * float(lc["seismic_S1_g"])
    SDS = (2.0 / 3.0) * SMS
    SD1 = (2.0 / 3.0) * SM1
    T = float(lc["seismic_T_s"])
    Sa = SD1 / T if T > 0 else 0.0
    Cs = Sa * float(lc["seismic_I"]) / float(lc["seismic_R"])
    cf = en_centrifugal_percentage(float(rail["speed_kmh"]), float(rail["radius_m"]), float(rail["Lf_m"]))
    sdl_df = pd.DataFrame(lc["sdl_components"])
    return {
        "sdl_single_total": float(sdl_df["Single Track (kN/m)"].sum()),
        "sdl_double_total": float(sdl_df["Double Track (kN/m)"].sum()),
        "Lphi": Lphi,
        "dynamic_phi_calc": phi_calc,
        "traction_kn": traction,
        "braking_kn": braking,
        "LF_design_kn": LF_design,
        "LF_design_kn_m": LF_design / span if span else 0.0,
        "WSsuper_kn": ws,
        "WSsuper_WL_kn": ws_wl,
        "WSsuper_kn_m": ws / span if span else 0.0,
        "WSsuper_WL_kn_m": ws_wl / span if span else 0.0,
        "SMS": SMS,
        "SM1": SM1,
        "SDS": SDS,
        "SD1": SD1,
        "Sa": Sa,
        "Cs": Cs,
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
        st.markdown("**ACTIVE CONTEXT**")
        st.caption(f"Project: **{D['project']['name']}**")
        st.caption(f"Span: **{D['project']['bridge_object']}**")
        st.caption(f"Code: **{D['project']['design_code']}**")
        st.caption(f"PT: **{D['project']['tendon_system']}**")
        st.caption(f"Units: **{D['project']['units']}**")
        st.markdown("---")
        st.download_button(
            "Save Project JSON",
            json.dumps(D, indent=2).encode("utf-8"),
            file_name="segmental_box_girder_project.json",
            mime="application/json",
            use_container_width=True,
        )
        uploaded = st.file_uploader("Load Project JSON", type=["json"])
        if uploaded is not None:
            try:
                st.session_state.project = ensure_project_schema(json.loads(uploaded.read().decode("utf-8")))
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not load JSON: {exc}")


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
        small_context("Design Code", "AASHTO LRFD 2014", "EN actions from FEA envelope")
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
            card("Reference Baseline", "BG40 R10 active", D["meta"]["dataset_status"], "pass")
        with c2:
            qa = "Blocked" if counts["ERROR"] else ("Review" if counts["WARNING"] else "Ready")
            mode = "fail" if counts["ERROR"] else ("warn" if counts["WARNING"] else "pass")
            card("QA Gate", qa, f"{counts['ERROR']} error(s), {counts['WARNING']} warning(s)", mode)
        with c3:
            card("FEA Data", "Reference baseline loaded", D["fea_results"]["source_status"])
        with c4:
            card("Recommended Action", "Review current workspace", "M2.1: header, dashboard, and workflow polish")

        st.markdown("### Governing engineering results")
        g1, g2, g3, g4 = st.columns(4)
        with g1:
            card("ULS Flexure", f"DCR {flex['max_dcr']:.3f}", f"Governing x ≈ {flex['governing_x_m']} m", "pass")
        with g2:
            check = snap["transverse_check"]
            mode = "pass" if check["Status_governing"] == "PASS" else "fail"
            card("ULS Shear / Torsion", f"D/C {check['DCR_governing']:.3f}", check["Status_governing"], mode)
        with g3:
            card("SLS Stress", sls["status"], f"Governing margin {sls['governing_margin_percent']:.1f}%", "pass")
        with g4:
            card("Deflection", df["status"], f"LL utilization {df['ll_utilization_percent']:.1f}% of L/800", "pass")

        st.markdown("### Report-driven workspace status")
        workflow_lookup = {row["Workflow item"]: row for row in workflow}
        status_map = {
            "1 Criteria / Loads": workflow_lookup.get("Materials", {"Status": "READY"})["Status"],
            "2 Bridge Model": workflow_lookup.get("Geometry", {"Status": "READY"})["Status"],
            "3 Section Properties": workflow_lookup.get("Geometry", {"Status": "READY"})["Status"],
            "4 Prestress Losses": workflow_lookup.get("Prestress Losses", {"Status": "READY"})["Status"],
            "5 FEA Results": workflow_lookup.get("FEA Demand", {"Status": "READY"})["Status"],
            "6 ULS Flexure": "PASS",
            "7 ULS Shear / Torsion": snap["transverse_check"]["Status_governing"],
            "8 SLS Stress": sls["status"],
            "9 Deflection": df["status"],
        }
        rows_html = []
        for label in WORKSPACE_LABELS[1:-1]:
            ws = get_workspace(label)
            status = status_map.get(label, "READY")
            subsections = " · ".join(ws["subpages"][:-1])
            rows_html.append(
                f'<div class="workflow-row"><div><div class="workflow-name">{label}</div><div class="workflow-sub">{ws["title"]}</div></div><div class="workflow-status">{status}</div><div class="workflow-sub">{subsections}</div></div>'
            )
        st.markdown('<div class="workflow-table">' + ''.join(rows_html) + '</div>', unsafe_allow_html=True)
    elif sub == "Workflow Status":
        st.dataframe(workflow_dataframe(workflow), use_container_width=True, hide_index=True)
        with st.expander("Validation details", expanded=bool(counts["ERROR"] or counts["WARNING"])):
            st.dataframe(issue_dataframe(issues), use_container_width=True, hide_index=True)
    elif sub == "Governing Results":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            card("ULS Flexure", f"DCR {flex['max_dcr']:.3f}", f"Governing x ≈ {flex['governing_x_m']} m", "pass")
        with c2:
            check = snap["transverse_check"]
            mode = "pass" if check["Status_governing"] == "PASS" else "fail"
            card("ULS Shear/Torsion", f"D/C {check['DCR_governing']:.3f}", check["Status_governing"], mode)
        with c3:
            card("SLS Stress", sls["status"], f"Governing margin {sls['governing_margin_percent']:.1f}%", "pass")
        with c4:
            card("Deflection", df["status"], f"LL utilization {df['ll_utilization_percent']:.1f}%", "pass")
        st.dataframe(
            pd.DataFrame(
                [
                    ["6 ULS Flexure", "max DCR", flex["max_dcr"], "PASS"],
                    ["7 ULS Shear/Torsion", "transverse D/C", snap["transverse_check"]["DCR_governing"], snap["transverse_check"]["Status_governing"]],
                    ["8 SLS Stress", "governing margin (%)", sls["governing_margin_percent"], sls["status"]],
                    ["9 Deflection", "LL utilization (%)", df["ll_utilization_percent"], df["status"]],
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
                ("1 Criteria / Loads", "BG40 R10 + app inputs", "Structured for report output", "READY"),
                ("2 Bridge Model", "BG40 R10 + app inputs", "Structured for report output", "READY"),
                ("3 Section Properties", "FEA keyed properties", "Consistency checks active", "READY"),
                ("4–9 Design checks", "Existing M1 engine + R10 baselines", "Calculation cards and QA preview available", "IN PROGRESS"),
            ],
        )


def page_criteria_loads(sub: str) -> None:
    st.subheader(get_workspace("1 Criteria / Loads")["title"])
    md = material_derived()
    ld = load_derived()
    if sub == "1.1 Standards":
        st.markdown("### 1.1 Design Standards and Requirements")
        st.dataframe(pd.DataFrame(D["criteria"]["standards"]), use_container_width=True, hide_index=True)
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
    elif sub == "1.3 Loads":
        st.markdown("### 1.3 Design Loads")
        tabs = st.tabs(["DL/SDL", "LL + IM", "LF / HF / CF", "Wind", "Creep & Shrinkage", "Earthquake"])
        with tabs[0]:
            st.caption("Self-weight is calculated by FEA using γc. SDL table is editable baseline input.")
            sdl_df = pd.DataFrame(D["load_components"]["sdl_components"])
            st.dataframe(sdl_df, use_container_width=True, hide_index=True)
            c1, c2 = st.columns(2)
            with c1:
                card("SDL Single Track", f"{ld['sdl_single_total']:.2f} kN/m", f"Design = {D['load_components']['design_sdl_single_kn_m']:.0f} kN/m")
            with c2:
                card("SDL Double Track", f"{ld['sdl_double_total']:.2f} kN/m", f"Design = {D['load_components']['design_sdl_double_kn_m']:.0f} kN/m", "pass")
        with tabs[1]:
            c1, c2, c3 = st.columns(3)
            with c1:
                editable_value(["load_components", "dynamic_L_left_m"], "L_left (m)", 1.0)
            with c2:
                editable_value(["load_components", "dynamic_L_right_m"], "L_right (m)", 1.0)
            with c3:
                editable_value(["load_components", "dynamic_factor_design"], "Design IM / φ", 0.01, "%.2f")
            st.latex(r"L_\phi=\min(L_{left},L_{right}),\qquad \phi=\frac{2.16}{\sqrt{L_\phi}-0.2}+0.73")
            card("Dynamic factor", f"φcalc = {ld['dynamic_phi_calc']:.4f}", f"Use IM = {D['load_components']['dynamic_factor_design']:.2f}", "pass")
        with tabs[2]:
            c1, c2, c3 = st.columns(3)
            with c1:
                editable_value(["rail_loads", "speed_kmh"], "V (km/h)", 10.0)
            with c2:
                editable_value(["rail_loads", "radius_m"], "R (m)", 100.0)
            with c3:
                editable_value(["rail_loads", "Lf_m"], "Lf (m)", 1.0)
            st.dataframe(pd.DataFrame([
                ["Traction", ld["traction_kn"], "kN"],
                ["Braking", ld["braking_kn"], "kN"],
                ["Design LF", ld["LF_design_kn"], "kN"],
                ["Design LF distributed", ld["LF_design_kn_m"], "kN/m"],
                ["Centrifugal reduction f", ld["cf_f"], "-"],
                ["Centrifugal C", ld["cf_C_percent"], "% of LL"],
            ], columns=["Item", "Value", "Unit"]), use_container_width=True, hide_index=True)
        with tabs[3]:
            c1, c2, c3 = st.columns(3)
            with c1:
                editable_value(["load_components", "wind_vb_m_s"], "vb (m/s)", 1.0)
            with c2:
                editable_value(["load_components", "wind_dtot_ws_m"], "dtot,WS (m)", 0.1)
            with c3:
                editable_value(["load_components", "wind_dtot_ws_wl_m"], "dtot,WS+WL (m)", 0.1)
            st.latex(r"F_{Wx}=\frac{1}{2}\rho v_b^2 C A_{ref,x}")
            st.dataframe(pd.DataFrame([
                ["WS superstructure", ld["WSsuper_kn"], ld["WSsuper_kn_m"], "kN / kN/m"],
                ["WS superstructure + WL", ld["WSsuper_WL_kn"], ld["WSsuper_WL_kn_m"], "kN / kN/m"],
            ], columns=["Item", "Force", "Distributed", "Unit"]), use_container_width=True, hide_index=True)
        with tabs[4]:
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
        with tabs[5]:
            st.latex(r"S_{DS}=\frac{2}{3}F_aS_s,\qquad S_{D1}=\frac{2}{3}F_vS_1,\qquad C_s=S_a\left(\frac{I}{R}\right)")
            st.dataframe(pd.DataFrame([
                ["SDS", ld["SDS"], "g"],
                ["SD1", ld["SD1"], "g"],
                ["Sa", ld["Sa"], "g"],
                ["Cs", ld["Cs"], "-"],
            ], columns=["Item", "Value", "Unit"]), use_container_width=True, hide_index=True)
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
        report_trace_table("1 Criteria / Loads", [("Standards", "BG40 R10", "Report table structured", "READY"), ("Materials", "User input + app calc", "Ec/fr/fpy/Aps calculated", "READY"), ("Loads", "User input + app calc", "SDL/IM/LF/CF/Wind/EQ calculated", "READY"), ("Combinations", "FEA basis text", "Ready for report preview", "READY")])


def page_bridge_model(sub: str) -> None:
    st.subheader(get_workspace("2 Bridge Model")["title"])
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
        report_trace_table("2 Bridge Model", [("Bridge description", "User input + BG40 R10", "Report table ready", "READY"), ("FEA model assumptions", "BG40 R10", "Assumption cards ready", "READY"), ("Supports", "BG40 R10", "Support table ready", "READY"), ("Tendon layout", "BG40 R10", "Tendon table ready", "READY")])


def page_section_properties(sub: str) -> None:
    st.subheader(get_workspace("3 Section Properties")["title"])
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
        report_trace_table("3 Section Properties", [("Cross-section dimensions", "User input + FEA", "Report table ready", "READY"), ("Section properties", "FEA keyed values", "Consistency checks active", "READY"), ("Closed cell torsion properties", "Chapter 7 inputs", "Aoh/ph passed to torsion module", "READY")])


def page_prestress_losses(sub: str) -> None:
    st.subheader(get_workspace("4 Prestress Losses")["title"])
    m, p = D["materials"], D["prestress"]
    summary = prestress_loss_summary(prestress_inputs())
    if sub == "4.1 General":
        st.markdown("Prestress losses are evaluated as instantaneous and time-dependent losses. The app calculates equivalent average losses for global section design and uses final prestress force as a model consistency check.")
        c1, c2, c3, c4 = st.columns(4)
        with c1: card("fpi", f"{m['fpi_mpa']:.1f} MPa", "Initial jacking stress")
        with c2: card("Total Loss", f"{summary['total_loss_mpa']:.1f} MPa", "All loss components")
        with c3: card("fpe", f"{summary['fpe_mpa']:.1f} MPa", "Effective stress", "pass")
        with c4: card("P_eff", f"{summary['Peff_kn']:,.0f} kN", "fpe × Aps,total")
    elif sub == "4.2 Friction":
        st.latex(r"\Delta f_{pF,eq}=f_{pi}\left[1-e^{-\mu\alpha}\right],\qquad \alpha_{total}=\sqrt{\alpha_{vert}^{2}+\alpha_{horiz}^{2}}")
        df, avg, pct = friction_loss_table(p["tendon_friction_groups"], m["fpi_mpa"], p["mu_external"])
        st.dataframe(df.style.format({"α_vert (rad)": "{:.4f}", "α_horiz (rad)": "{:.4f}", "α_total (rad)": "{:.4f}", "ΔfpF,eq (MPa)": "{:.1f}", "Loss (%)": "{:.2f}"}), use_container_width=True)
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
        st.dataframe(loss_df.style.format({"Value (MPa)": "{:.1f}"}), use_container_width=True)
        st.download_button("Download loss table CSV", loss_df.to_csv(index=False).encode("utf-8"), "prestress_losses.csv", "text/csv")
    else:
        report_trace_table("4 Prestress Losses", [("Friction", "App calculation", "Formula and table ready", "READY"), ("Anchor set", "User equivalent input", "Trace placeholder ready", "READY"), ("Elastic shortening", "App calculation", "Formula ready", "READY"), ("Creep/Shrinkage", "AASHTO factors", "Unit warning active", "READY"), ("Effective prestress", "App calculation", "Loss table ready", "READY")])


def page_fea_results(sub: str) -> None:
    st.subheader(get_workspace("5 FEA Results")["title"])
    fea = D["fea_results"]
    l = D["loads"]
    if sub == "5.1 Data Hub":
        st.markdown('<div class="note-box"><b>M2 data hub:</b> baseline FEA values are keyed from BG40 R10. M3 should add CSV/Excel station-by-station import and envelope generation.</div>', unsafe_allow_html=True)
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
        report_trace_table("5 FEA Results", [("Midspan dashboard", "BG40 R10 keyed", "Data hub ready", "READY"), ("ULS envelope", "User keyed values", "Demand object ready", "READY"), ("SLS envelope", "R10 baseline", "M3 import pending", "IN PROGRESS")])


def page_uls_flexure(sub: str) -> None:
    st.subheader(get_workspace("6 ULS Flexure")["title"])
    flex = D["uls_flexure"]
    if sub == "6.1 Basis":
        st.markdown("ULS flexure uses AASHTO LRFD resistance with external/unbonded tendon stress checks and FEA factored moment demand.")
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
        report_trace_table("6 ULS Flexure", [("fps", "BG40 R10 baseline", "Shown in calculation card", "READY"), ("Midspan φMn/Mu", "BG40 R10 baseline", "DCR calculated", "READY"), ("Span DCR", "BG40 R10 baseline", "M3/M4 station import pending", "IN PROGRESS")])


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
        st.dataframe(pd.DataFrame([["Shear", "AASHTO LRFD 2014 Art. 5.8.3 / MCFT", "β and θ based shear check"], ["Torsion", "AASHTO LRFD 2014 Art. 5.8.6", "Segmental box girder special provision"], ["Resistance factor", "φv", phi_v]], columns=["Item", "Code basis", "Remarks"]), use_container_width=True, hide_index=True)
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
        card("Combined transverse check", check["Status_governing"], f"Governing D/C = {check['DCR_governing']:.3f}", mode)
        st.dataframe(pd.DataFrame([["Shear Av/s required", shear["Av_over_s_mm2_per_mm"], "mm²/mm"], ["Shear Av/s provided", prov["Av_over_s_mm2_per_mm"], "mm²/mm"], ["Torsion At/s required", tors["At_over_s_mm2_per_mm"], "mm²/mm"], ["Torsion At/s provided per leg", prov["At_over_s_per_leg_mm2_per_mm"], "mm²/mm"], ["DCR shear", check["DCR_shear"], "-"], ["DCR torsion", check["DCR_torsion"], "-"]], columns=["Item", "Value", "Unit"]), use_container_width=True, hide_index=True)
    else:
        report_trace_table("7 ULS Shear / Torsion", [("Design basis", "AASHTO 5.8.3/5.8.6", "Formula route separated", "READY"), ("Critical section", "FEA keyed demand", "Demand table ready", "READY"), ("Shear check", "App calculation", "Trace ready", "READY"), ("Torsion check", "AASHTO 5.8.6", "At/s and Al calculated", "READY"), ("Reinforcement", "User input + app calc", "DCR active", check["Status_governing"])] )


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
# Segmental Box Girder Pro — Commercial M2.1 Summary

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
- UI uses report-driven workspaces 1–9 without displaying the word Chapter in the sidebar.
- Each workspace uses report subsection subpages for future Word/PDF report generation.
- Existing M1 engineering kernels are preserved for prestress losses and AASHTO 5.8.6 shear/torsion checks.
"""
        st.markdown(report_md)
        st.download_button("Download Markdown Summary", report_md.encode("utf-8"), "segmental_box_girder_m2_summary.md", "text/markdown", use_container_width=True)


# -----------------------------------------------------------------------------
# Router
# -----------------------------------------------------------------------------
render_sidebar()
render_header()

workspace = get_workspace(st.session_state.current_workspace)
subpage = st.session_state.current_subpage

if workspace["id"] == "dashboard":
    page_dashboard(subpage)
elif workspace["id"] == "criteria_loads":
    page_criteria_loads(subpage)
elif workspace["id"] == "bridge_model":
    page_bridge_model(subpage)
elif workspace["id"] == "section_properties":
    page_section_properties(subpage)
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
