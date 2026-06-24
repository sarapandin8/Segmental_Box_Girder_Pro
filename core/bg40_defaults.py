"""BG40 default data for Segmental Box Girder Pro.

Internal units used by calculation functions:
- lengths for section/torsion checks: mm unless noted
- forces: kN for UI; converted to N internally where needed
- moments/torsion: kN·m for UI; converted to N·mm internally where needed
- stresses: MPa = N/mm²
"""

BG40_DEFAULT = {
    "meta": {
        "schema_version": "0.2.0-commercial-m1",
        "app_name": "Segmental Box Girder Pro",
        "dataset_status": "BG40 baseline dataset loaded",
        "schema_note": "Versioned project schema for commercial-grade QA and reproducibility.",
    },
    "project": {
        "name": "BG40",
        "description": "PT Segmental Box Girder · Track Doubling Project (Khon Kaen – Nong Khai)",
        "bridge_object": "B2_SPAN2",
        "span_m": 40.0,
        "width_m": 11.2,
        "depth_m": 2.5,
        "design_code": "AASHTO LRFD 2014 + EN Actions",
        "tendon_system": "External / Unbonded PT",
        "units": "kN, m, MPa, mm",
    },
    "materials": {
        "fc_mpa": 60.0,
        "fci_mpa": 60.0,
        "Ec_mpa": 36669.0,
        "fy_mpa": 390.0,
        "Ep_mpa": 197000.0,
        "fpu_mpa": 1861.6,
        "fpi_mpa": 1395.0,
        "gamma_c_kn_m3": 24.5,
    },
    "section": {
        "Ac_m2": 5.698,
        "I33_m4": 4.681,
        "I22_m4": 39.52,
        "J_m4": 8.846,
        "S_top_m3": 5.577,
        "S_bottom_m3": 2.819,
        "ycg_from_bottom_m": 1.661,
        "yt_from_top_m": 0.839,
        "Aoh_mm2": 24260000.0,
        "ph_mm": 26102.0,
        "bv_mm": 380.0,
        "dv_mm": 1867.5,
        "dweb_mm": 2245.0,
        "tcr_knm": 31185.0,
    },
    "prestress": {
        "num_tendons": 16,
        "strands_per_tendon": 24,
        "Aps_total_mm2": 53760.0,
        "mu_external": 0.15,
        "RH_percent": 75.0,
        "ti_days": 28.0,
        "tf_days": 27000.0,
        "V_over_S_in": 5.98,
        "fcgp_mpa": 36.26,
        "anchor_set_loss_mpa": 0.0,
        "relaxation_loss_mpa": 29.7,
        "tendon_friction_groups": [
            {"group": "T1–T2", "n": 4, "alpha_vert_rad": 0.0260, "alpha_horiz_rad": 0.0720},
            {"group": "T3–T4", "n": 4, "alpha_vert_rad": 0.0689, "alpha_horiz_rad": 0.0620},
            {"group": "T5–T6", "n": 4, "alpha_vert_rad": 0.1120, "alpha_horiz_rad": 0.0120},
            {"group": "T7–T8", "n": 4, "alpha_vert_rad": 0.1248, "alpha_horiz_rad": 0.0471},
        ],
    },
    "loads": {
        "critical_x_m": 38.133,
        "Vu_kn": 12153.0,
        "Tu_knm": 9211.9,
        "Pu_kn": -1108.0,
        "Mu_knm": 19266.0,
        "Vc_per_web_kn": 2145.0,
        "theta_deg_for_shear": 21.8,
        "beta_for_shear": 4.70,
        "fea_Al_max_mm2": 17381.0,
        "stirrup_bar_dia_mm": 25.0,
        "stirrup_spacing_mm": 250.0,
        "stirrup_legs_per_web": 2,
    },
    "rail_loads": {
        "speed_kmh": 160.0,
        "radius_m": 10000.0,
        "Lf_m": 40.0,
    },
}
