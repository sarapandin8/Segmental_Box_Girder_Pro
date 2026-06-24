from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

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

st.set_page_config(
    page_title="Segmental Box Girder Pro",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
:root {
  --brand: #1f66d1;
  --brand-dark: #073b70;
  --ink: #0f172a;
  --muted: #64748b;
  --line: #bfd4f2;
  --soft: #f5f8fc;
  --card: #ffffff;
  --pass-bg: #effcf5;
  --warn-bg: #fff7ed;
}
.block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1500px;}
[data-testid="stSidebar"] {background: linear-gradient(180deg, #eef6ff 0%, #f8fbff 100%);}
.app-title {font-size: 2.0rem; font-weight: 800; color: var(--brand-dark); margin-bottom: 0.1rem;}
.app-subtitle {font-size: 0.92rem; color: var(--muted); margin-bottom: 1.1rem;}
.hero-card {border: 1px solid var(--line); background: var(--card); border-radius: 16px; padding: 16px 18px; margin: 8px 0 18px 0; box-shadow: 0 6px 20px rgba(15, 23, 42, 0.05);}
.status-card {border: 1px solid #d5e6ff; background: #fff; border-radius: 14px; padding: 15px 17px; min-height: 106px; box-shadow: 0 5px 18px rgba(15, 23, 42, 0.06);}
.status-card.pass {background: var(--pass-bg); border-color: #b8edd0;}
.status-card.warn {background: var(--warn-bg); border-color: #fed7aa;}
.status-kicker {font-size: 0.72rem; letter-spacing: 0.08em; color: #315f96; font-weight: 800; text-transform: uppercase;}
.status-value {font-size: 1.18rem; color: #071b3a; font-weight: 800; margin-top: 0.25rem;}
.status-note {font-size: 0.78rem; color: var(--muted); margin-top: 0.35rem;}
.section-card {border: 1px solid #d5e6ff; background: #fff; border-radius: 16px; padding: 18px; margin: 10px 0 18px 0;}
.note-box {border-left: 5px solid var(--brand); background: #f2f7ff; padding: 12px 14px; border-radius: 12px; color: #173455; margin: 10px 0 16px 0;}
.small-muted {font-size: 0.80rem; color: var(--muted);}
.badge {display:inline-block; padding: 4px 10px; border-radius: 999px; font-weight: 800; font-size: 0.78rem;}
.badge.pass {background:#dffbe8; color:#126b37; border: 1px solid #a7e6bc;}
.badge.fail {background:#fee2e2; color:#991b1b; border: 1px solid #fecaca;}
.sidebar-card {border:1px solid #bcd3f5; border-radius:12px; padding:12px; background:#fff; margin-bottom:12px;}
.sidebar-title {font-weight:800; color:#0b376d; font-size:0.9rem;}
.sidebar-mini {font-size:0.76rem; color:#334155; margin-top:4px;}
hr {margin: 1rem 0;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------
if "project" not in st.session_state:
    st.session_state.project = deepcopy(BG40_DEFAULT)
if "current_page" not in st.session_state:
    st.session_state.current_page = "Setup"

D = st.session_state.project


def status_badge(status: str) -> str:
    cls = "pass" if status == "PASS" else "fail"
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


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-card">
              <div class="sidebar-title">Segmental Box Girder Pro</div>
              <div class="sidebar-mini">FEA-based design-review workspace for PT segmental box girders.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        pages = [
            "Setup",
            "Section / Tendon",
            "Prestress Losses",
            "FEA / Loads",
            "ULS Shear & Torsion",
            "Results Dashboard",
            "Report / QA",
        ]
        choice = st.radio("WORKSPACE", pages, index=pages.index(st.session_state.current_page), label_visibility="visible")
        st.session_state.current_page = choice
        st.markdown("---")
        st.markdown("**PROJECT STATUS**")
        st.success("Model Current")
        st.success("AASHTO 5.8.6 torsion active")
        st.info("MVP: BG40 defaults loaded")
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
                st.session_state.project = json.loads(uploaded.read().decode("utf-8"))
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not load JSON: {exc}")


def render_header() -> None:
    st.markdown('<div class="app-title">Segmental Box Girder Pro</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">PT segmental box girder design-review workspace · Internal units: kN, m, MPa, mm.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="hero-card">
          <b>{D['project']['name']}</b> · {D['project']['description']}<br>
          <span class="small-muted">Design basis: {D['project']['design_code']} · Tendon system: {D['project']['tendon_system']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_setup() -> None:
    st.subheader("Setup Workspace")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Model Status", "Current", "BG40 default data loaded", "pass")
    with c2:
        card("Design Code", "AASHTO LRFD 2014", "EN actions used for FEA demands", "pass")
    with c3:
        card("Tendon System", "External / Unbonded", "φv = 0.85 for segmental construction", "pass")
    with c4:
        card("Recommended Action", "Review inputs", "Then open ULS Shear & Torsion")

    st.markdown("### Project Data")
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            D["project"]["name"] = st.text_input("Project / Bridge name", D["project"]["name"])
            D["project"]["bridge_object"] = st.text_input("Bridge object / span", D["project"]["bridge_object"])
        with col2:
            D["project"]["span_m"] = st.number_input("Span length, L (m)", value=float(D["project"]["span_m"]), step=1.0)
            D["project"]["width_m"] = st.number_input("Total width, B (m)", value=float(D["project"]["width_m"]), step=0.1)
        with col3:
            D["project"]["depth_m"] = st.number_input("Section depth, D (m)", value=float(D["project"]["depth_m"]), step=0.1)
            D["project"]["tendon_system"] = st.selectbox(
                "Tendon system",
                ["External / Unbonded PT", "Fully bonded internal PT"],
                index=0 if "External" in D["project"]["tendon_system"] else 1,
            )

    st.markdown(
        """
        <div class="note-box">
        <b>Scope guard:</b> This MVP is a design-check and report-assist app. It does not replace the FEA model.
        FEA/CSI/MIDAS output should be imported or keyed in as design demand.
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_section_tendon() -> None:
    st.subheader("Section / Tendon")
    tab1, tab2, tab3 = st.tabs(["Materials", "Section Properties", "Tendon / Loss Inputs"])

    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            D["materials"]["fc_mpa"] = st.number_input("f′c (MPa)", value=float(D["materials"]["fc_mpa"]), step=1.0)
            D["materials"]["Ec_mpa"] = st.number_input("Ec (MPa)", value=float(D["materials"]["Ec_mpa"]), step=100.0)
        with col2:
            D["materials"]["fy_mpa"] = st.number_input("fy (MPa)", value=float(D["materials"]["fy_mpa"]), step=10.0)
            D["materials"]["Ep_mpa"] = st.number_input("Ep (MPa)", value=float(D["materials"]["Ep_mpa"]), step=1000.0)
        with col3:
            D["materials"]["fpi_mpa"] = st.number_input("fpi (MPa)", value=float(D["materials"]["fpi_mpa"]), step=5.0)
            D["materials"]["gamma_c_kn_m3"] = st.number_input("γc (kN/m³)", value=float(D["materials"]["gamma_c_kn_m3"]), step=0.1)

    with tab2:
        col1, col2, col3 = st.columns(3)
        with col1:
            D["section"]["Ac_m2"] = st.number_input("Ac (m²)", value=float(D["section"]["Ac_m2"]), step=0.001, format="%.3f")
            D["section"]["I33_m4"] = st.number_input("I33 (m⁴)", value=float(D["section"]["I33_m4"]), step=0.001, format="%.3f")
        with col2:
            D["section"]["S_top_m3"] = st.number_input("S_top (m³)", value=float(D["section"]["S_top_m3"]), step=0.001, format="%.3f")
            D["section"]["S_bottom_m3"] = st.number_input("S_bottom (m³)", value=float(D["section"]["S_bottom_m3"]), step=0.001, format="%.3f")
        with col3:
            D["section"]["Aoh_mm2"] = st.number_input("Aoh (mm²)", value=float(D["section"]["Aoh_mm2"]), step=1000.0)
            D["section"]["ph_mm"] = st.number_input("ph (mm)", value=float(D["section"]["ph_mm"]), step=10.0)
            D["section"]["tcr_knm"] = st.number_input("Tcr (kN·m)", value=float(D["section"]["tcr_knm"]), step=100.0)

    with tab3:
        col1, col2, col3 = st.columns(3)
        with col1:
            D["prestress"]["num_tendons"] = int(st.number_input("Number of tendons", value=int(D["prestress"]["num_tendons"]), step=1))
            D["prestress"]["Aps_total_mm2"] = st.number_input("Aps,total (mm²)", value=float(D["prestress"]["Aps_total_mm2"]), step=100.0)
        with col2:
            D["prestress"]["RH_percent"] = st.number_input("RH (%)", value=float(D["prestress"]["RH_percent"]), step=1.0)
            D["prestress"]["V_over_S_in"] = st.number_input("V/S (in)", value=float(D["prestress"]["V_over_S_in"]), step=0.01)
        with col3:
            D["prestress"]["fcgp_mpa"] = st.number_input("fcgp (MPa)", value=float(D["prestress"]["fcgp_mpa"]), step=0.1)
            D["prestress"]["relaxation_loss_mpa"] = st.number_input("Relaxation loss (MPa)", value=float(D["prestress"]["relaxation_loss_mpa"]), step=0.1)


def page_prestress() -> None:
    st.subheader("Prestress Losses")
    m = D["materials"]
    p = D["prestress"]
    inputs = {
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
    summary = prestress_loss_summary(inputs)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Total Loss", f"{summary['total_loss_mpa']:.1f} MPa", "Friction + ES + time-dependent + relaxation")
    with c2:
        card("Effective Stress", f"{summary['fpe_mpa']:.1f} MPa", "fpe = fpi − Σlosses", "pass")
    with c3:
        card("Effective Force", f"{summary['Peff_kn']:,.0f} kN", "P_eff = fpe Aps")
    with c4:
        card("Creep / SH", f"ψ={summary['creep_psi']:.3f}", f"εsh={summary['shrinkage_microstrain']:.1f} με")

    st.markdown("### Friction Loss")
    st.latex(r"\Delta f_{pF,eq}=f_{pi}\left[1-e^{-\mu\alpha}\right],\qquad \alpha_{total}=\sqrt{\alpha_{vert}^{2}+\alpha_{horiz}^{2}}")
    df, avg, pct = friction_loss_table(p["tendon_friction_groups"], m["fpi_mpa"], p["mu_external"])
    st.dataframe(df.style.format({
        "α_vert (rad)": "{:.4f}", "α_horiz (rad)": "{:.4f}", "α_total (rad)": "{:.4f}",
        "ΔfpF,eq (MPa)": "{:.1f}", "Loss (%)": "{:.2f}",
    }), use_container_width=True)
    st.caption(f"Weighted average friction loss = {avg:.1f} MPa = {pct:.2f}% of fpi.")

    st.markdown("### Time-dependent Losses")
    col1, col2 = st.columns(2)
    with col1:
        st.latex(r"\psi(t_f,t_i)=1.9k_s k_{hc}k_f\Delta k_{td}t_i^{-0.118}")
        creep = aashto_creep_coefficient(p["RH_percent"], p["V_over_S_in"], m["fc_mpa"], p["ti_days"])
        st.write({k: round(v, 4) for k, v in creep.items()})
        st.latex(r"\Delta f_{pCR}=n f_{cgp}\psi(t_f,t_i)")
        st.info(f"ΔfpCR = {summary['creep_mpa']:.1f} MPa")
    with col2:
        st.latex(r"\varepsilon_{sh}=k_s k_{hs} k_f\Delta k_{td}(0.48\times10^{-3})")
        shrink = aashto_shrinkage_strain(p["RH_percent"], p["V_over_S_in"], m["fc_mpa"])
        st.write({k: round(v, 6) for k, v in shrink.items()})
        st.latex(r"\Delta f_{pSH}=\varepsilon_{sh}E_p")
        st.info(f"εsh = {summary['shrinkage_microstrain']:.1f} με, ΔfpSH = {summary['shrinkage_mpa']:.1f} MPa")

    st.markdown("### Loss Summary")
    loss_df = pd.DataFrame(
        [
            ["Friction", summary["friction_mpa"]],
            ["Anchor set / seating", summary["anchor_set_mpa"]],
            ["Elastic shortening", summary["elastic_shortening_mpa"]],
            ["Creep", summary["creep_mpa"]],
            ["Shrinkage", summary["shrinkage_mpa"]],
            ["Relaxation", summary["relaxation_mpa"]],
            ["Total", summary["total_loss_mpa"]],
            ["fpe", summary["fpe_mpa"]],
        ],
        columns=["Item", "Value (MPa)"],
    )
    st.dataframe(loss_df.style.format({"Value (MPa)": "{:.1f}"}), use_container_width=True)
    st.caption("AASHTO empirical factors are evaluated with V/S in inches and concrete strength in ksi; final losses are reported in MPa.")


def page_loads() -> None:
    st.subheader("FEA / Loads")
    st.markdown("### Critical ULS Demand")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        D["loads"]["critical_x_m"] = st.number_input("Critical section x (m)", value=float(D["loads"]["critical_x_m"]), step=0.001, format="%.3f")
    with col2:
        D["loads"]["Vu_kn"] = st.number_input("Vu (kN)", value=float(D["loads"]["Vu_kn"]), step=10.0)
    with col3:
        D["loads"]["Tu_knm"] = st.number_input("Tu (kN·m)", value=float(D["loads"]["Tu_knm"]), step=10.0)
    with col4:
        D["loads"]["fea_Al_max_mm2"] = st.number_input("FEA max extra Al (mm²)", value=float(D["loads"]["fea_Al_max_mm2"]), step=100.0)

    st.markdown("### EN Centrifugal Force Check")
    col1, col2, col3 = st.columns(3)
    with col1:
        D["rail_loads"]["speed_kmh"] = st.number_input("V (km/h)", value=float(D["rail_loads"]["speed_kmh"]), step=10.0)
    with col2:
        D["rail_loads"]["radius_m"] = st.number_input("R (m)", value=float(D["rail_loads"]["radius_m"]), step=100.0)
    with col3:
        D["rail_loads"]["Lf_m"] = st.number_input("Lf (m)", value=float(D["rail_loads"]["Lf_m"]), step=1.0)
    cf = en_centrifugal_percentage(D["rail_loads"]["speed_kmh"], D["rail_loads"]["radius_m"], D["rail_loads"]["Lf_m"])
    st.latex(r"f=1-\frac{V-120}{1000}\left(\frac{814}{V}+1.75\right)\left(1-\sqrt{\frac{2.88}{L_f}}\right)\ge0.35")
    st.latex(r"C=f\frac{V^2}{127R}")
    c1, c2, c3 = st.columns(3)
    with c1:
        card("Reduction Factor", f"f = {cf['f']:.3f}", "EN 1991-2 Art. 6.5.1")
    with c2:
        card("Basic C", f"{100*cf['C_basic']:.2f}%", "Before reduction")
    with c3:
        card("Reduced C", f"{cf['C_percent']:.2f}%", "Applied to vertical live load", "pass")

    st.markdown("### Optional FEA CSV Import")
    uploaded = st.file_uploader("Upload CSiBridge / FEA envelope CSV", type=["csv"])
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        st.dataframe(df.head(30), use_container_width=True)
        st.info("MVP import preview only. Column mapping and automatic governing-section extraction can be added in the next milestone.")


def page_shear_torsion() -> None:
    st.subheader("ULS Shear & Torsion · AASHTO LRFD 2014 Article 5.8.6")
    m, s, l = D["materials"], D["section"], D["loads"]
    is_external = "External" in D["project"]["tendon_system"] or "Unbonded" in D["project"]["tendon_system"]
    phi_default = 0.85 if is_external else 0.90

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        phi_v = st.number_input("φv", value=float(phi_default), step=0.01, min_value=0.50, max_value=1.00)
    with col2:
        s["Aoh_mm2"] = st.number_input("Aoh (mm²)", value=float(s["Aoh_mm2"]), step=1000.0, key="st_Aoh")
    with col3:
        s["ph_mm"] = st.number_input("ph (mm)", value=float(s["ph_mm"]), step=10.0, key="st_ph")
    with col4:
        m["fy_mpa"] = st.number_input("fy (MPa)", value=float(m["fy_mpa"]), step=10.0, key="st_fy")

    tors = torsion_aashto_586(l["Tu_knm"], s["Aoh_mm2"], s["ph_mm"], m["fy_mpa"], phi_v)
    web = shear_torsion_web_components(l["Vu_kn"], l["Tu_knm"], s["Aoh_mm2"], s["dweb_mm"])
    shear = shear_reinforcement_required(web["Vu_web_kn"], l["Vc_per_web_kn"], phi_v, m["fy_mpa"], s["dv_mm"], l["theta_deg_for_shear"])
    prov = provided_stirrups(l["stirrup_bar_dia_mm"], l["stirrup_spacing_mm"], int(l["stirrup_legs_per_web"]))
    check = combined_transverse_check(shear["Av_over_s_mm2_per_mm"], tors["At_over_s_mm2_per_mm"], prov["Av_over_s_mm2_per_mm"], prov["At_over_s_per_leg_mm2_per_mm"])
    threshold = (1.0 / 3.0) * phi_v * s["tcr_knm"]
    torsion_required = l["Tu_knm"] > threshold
    Al_design = max(tors["Al_mm2"], l["fea_Al_max_mm2"])
    Al_rounded = 100.0 * round(Al_design / 100.0)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Torsion Demand", f"Tu = {l['Tu_knm']:,.0f} kN·m", f"Threshold = {threshold:,.0f} kN·m", "warn" if torsion_required else "pass")
    with c2:
        card("At/s Required", f"{tors['At_over_s_mm2_per_mm']:.3f} mm²/mm", "AASHTO 5.8.6.4")
    with c3:
        card("Al Required", f"{tors['Al_mm2']:,.0f} mm²", "Hand calc by AASHTO 5.8.6.4")
    with c4:
        card("Adopt Al", f"{Al_rounded:,.0f} mm²", "max(hand, FEA extra Al)", "pass")

    st.markdown("### Torsion Design Equations")
    st.latex(r"T_u>\frac{1}{3}\phi_v T_{cr}")
    st.latex(r"T_n=\frac{2A_oA_t f_y}{s}")
    st.latex(r"\frac{A_t}{s}=\frac{T_u}{2\phi_v A_o f_y},\qquad A_l=\frac{T_u p_h}{2\phi_v A_o f_y}")

    st.markdown("### Web Shear Components")
    st.latex(r"q=\frac{T_u}{2A_{oh}},\qquad V_{u,web}=\frac{V_u}{2}+q d_{web}")
    comp_df = pd.DataFrame(
        [
            ["Shear flow, q", web["q_N_per_mm"], "N/mm"],
            ["Gravity shear per web", web["Vg_web_kn"], "kN"],
            ["Torsion/web", web["Vt_web_kn"], "kN"],
            ["Design Vu,web", web["Vu_web_kn"], "kN"],
            ["Vc per web", l["Vc_per_web_kn"], "kN"],
            ["Vs required", shear["Vs_req_kn"], "kN"],
        ],
        columns=["Item", "Value", "Unit"],
    )
    st.dataframe(comp_df.style.format({"Value": "{:,.3f}"}), use_container_width=True)

    st.markdown("### Provided Transverse Reinforcement")
    col1, col2, col3 = st.columns(3)
    with col1:
        l["stirrup_bar_dia_mm"] = st.number_input("Closed stirrup diameter DB (mm)", value=float(l["stirrup_bar_dia_mm"]), step=1.0)
    with col2:
        l["stirrup_spacing_mm"] = st.number_input("Spacing s (mm)", value=float(l["stirrup_spacing_mm"]), step=25.0)
    with col3:
        l["stirrup_legs_per_web"] = int(st.number_input("Legs per web", value=int(l["stirrup_legs_per_web"]), step=1))

    prov = provided_stirrups(l["stirrup_bar_dia_mm"], l["stirrup_spacing_mm"], int(l["stirrup_legs_per_web"]))
    check = combined_transverse_check(shear["Av_over_s_mm2_per_mm"], tors["At_over_s_mm2_per_mm"], prov["Av_over_s_mm2_per_mm"], prov["At_over_s_per_leg_mm2_per_mm"])
    st.markdown(
        f"""
        <div class="note-box">
        <b>Transverse reinforcement check:</b><br>
        Shear Av/s required = {shear['Av_over_s_mm2_per_mm']:.3f} mm²/mm; provided = {prov['Av_over_s_mm2_per_mm']:.3f} mm²/mm → {status_badge(check['Status_shear'])}<br>
        Torsion At/s required = {tors['At_over_s_mm2_per_mm']:.3f} mm²/mm per leg; provided = {prov['At_over_s_per_leg_mm2_per_mm']:.3f} mm²/mm per leg → {status_badge(check['Status_torsion'])}<br>
        Governing D/C = {check['DCR_governing']:.3f} → {status_badge(check['Status_governing'])}
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_results() -> None:
    st.subheader("Results Dashboard")
    m, s, l, p = D["materials"], D["section"], D["loads"], D["prestress"]
    phi_v = 0.85 if "External" in D["project"]["tendon_system"] else 0.90
    tors = torsion_aashto_586(l["Tu_knm"], s["Aoh_mm2"], s["ph_mm"], m["fy_mpa"], phi_v)
    web = shear_torsion_web_components(l["Vu_kn"], l["Tu_knm"], s["Aoh_mm2"], s["dweb_mm"])
    shear = shear_reinforcement_required(web["Vu_web_kn"], l["Vc_per_web_kn"], phi_v, m["fy_mpa"], s["dv_mm"], l["theta_deg_for_shear"])
    prov = provided_stirrups(l["stirrup_bar_dia_mm"], l["stirrup_spacing_mm"], int(l["stirrup_legs_per_web"]))
    check = combined_transverse_check(shear["Av_over_s_mm2_per_mm"], tors["At_over_s_mm2_per_mm"], prov["Av_over_s_mm2_per_mm"], prov["At_over_s_per_leg_mm2_per_mm"])
    inputs = {
        "groups": p["tendon_friction_groups"], "fpi_mpa": m["fpi_mpa"], "mu": p["mu_external"], "RH_percent": p["RH_percent"],
        "V_over_S_in": p["V_over_S_in"], "fc_mpa": m["fc_mpa"], "ti_days": p["ti_days"], "Ep_mpa": m["Ep_mpa"],
        "Ec_mpa": m["Ec_mpa"], "fcgp_mpa": p["fcgp_mpa"], "num_tendons": p["num_tendons"],
        "anchor_set_loss_mpa": p["anchor_set_loss_mpa"], "relaxation_loss_mpa": p["relaxation_loss_mpa"],
        "Aps_total_mm2": p["Aps_total_mm2"],
    }
    ps = prestress_loss_summary(inputs)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Prestress fpe", f"{ps['fpe_mpa']:.1f} MPa", f"P_eff = {ps['Peff_kn']:,.0f} kN", "pass")
    with c2:
        card("ULS Torsion Al", f"{max(tors['Al_mm2'], l['fea_Al_max_mm2']):,.0f} mm²", "Adopt max(hand, FEA)", "pass")
    with c3:
        card("ULS Transverse", check["Status_governing"], f"D/C = {check['DCR_governing']:.3f}", "pass" if check["Status_governing"] == "PASS" else "warn")
    with c4:
        cf = en_centrifugal_percentage(D["rail_loads"]["speed_kmh"], D["rail_loads"]["radius_m"], D["rail_loads"]["Lf_m"])
        card("Centrifugal", f"{cf['C_percent']:.2f}% LL", f"f = {cf['f']:.3f}")

    dashboard = pd.DataFrame(
        [
            ["Prestress losses", "fpe", ps["fpe_mpa"], "MPa", "INFO"],
            ["Torsion threshold", "Tu", l["Tu_knm"], "kN·m", "CHECK"],
            ["Torsion At/s", "Required", tors["At_over_s_mm2_per_mm"], "mm²/mm", "CHECK"],
            ["Torsion Al", "AASHTO", tors["Al_mm2"], "mm²", "CHECK"],
            ["Torsion Al", "Adopted", max(tors["Al_mm2"], l["fea_Al_max_mm2"]), "mm²", "CHECK"],
            ["Shear Av/s", "Required", shear["Av_over_s_mm2_per_mm"], "mm²/mm", check["Status_shear"]],
            ["Provided stirrup", "Av/s", prov["Av_over_s_mm2_per_mm"], "mm²/mm", check["Status_governing"]],
        ],
        columns=["Check", "Item", "Value", "Unit", "Status"],
    )
    st.dataframe(dashboard.style.format({"Value": "{:,.3f}"}), use_container_width=True)


def page_report() -> None:
    st.subheader("Report / QA")
    m, s, l = D["materials"], D["section"], D["loads"]
    phi_v = 0.85 if "External" in D["project"]["tendon_system"] else 0.90
    tors = torsion_aashto_586(l["Tu_knm"], s["Aoh_mm2"], s["ph_mm"], m["fy_mpa"], phi_v)
    Al_design = max(tors["Al_mm2"], l["fea_Al_max_mm2"])
    report_md = f"""
# Segmental Box Girder Pro — Calculation Summary

## Project
- Bridge object: {D['project']['bridge_object']}
- Span length: {D['project']['span_m']} m
- Design basis: {D['project']['design_code']}
- Tendon system: {D['project']['tendon_system']}

## AASHTO LRFD 2014 Article 5.8.6 Torsion
- φv = {phi_v:.2f}
- Tu = {l['Tu_knm']:,.1f} kN·m
- Aoh = {s['Aoh_mm2']:,.0f} mm²
- ph = {s['ph_mm']:,.0f} mm
- fy = {m['fy_mpa']:,.0f} MPa
- At/s = {tors['At_over_s_mm2_per_mm']:.3f} mm²/mm
- Al,AASHTO = {tors['Al_mm2']:,.0f} mm²
- Al,FEA,max = {l['fea_Al_max_mm2']:,.0f} mm²
- Al,design = {Al_design:,.0f} mm²

## QA Notes
- The app is a calculation assistant, not an FEA replacement.
- Review all imported FEA demand values before final issue.
- AASHTO empirical loss factors require the code-specified units for intermediate factors.
"""
    st.markdown(report_md)
    st.download_button("Download Markdown Summary", report_md.encode("utf-8"), "segmental_box_girder_summary.md", "text/markdown", use_container_width=True)


render_sidebar()
render_header()

page = st.session_state.current_page
if page == "Setup":
    page_setup()
elif page == "Section / Tendon":
    page_section_tendon()
elif page == "Prestress Losses":
    page_prestress()
elif page == "FEA / Loads":
    page_loads()
elif page == "ULS Shear & Torsion":
    page_shear_torsion()
elif page == "Results Dashboard":
    page_results()
elif page == "Report / QA":
    page_report()
