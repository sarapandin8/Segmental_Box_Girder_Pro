from __future__ import annotations

from math import sqrt
from typing import Any, Dict, Iterable, List

import pandas as pd


def sdl_totals(components: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    df = pd.DataFrame(list(components))
    if df.empty:
        return {"single_total": 0.0, "double_total": 0.0}
    include = df["Include"] if "Include" in df.columns else True
    df = df[include.astype(bool)] if not isinstance(include, bool) else df
    return {
        "single_total": float(df["Single Track (kN/m)"].sum()),
        "double_total": float(df["Double Track (kN/m)"].sum()),
    }


def en_dynamic_factor_standard_maintenance(L_left_m: float, L_right_m: float) -> Dict[str, float]:
    """EN 1991-2 dynamic factor used by the BG40 report for standard maintenance.

    Report form: phi = 2.16/(sqrt(L_phi) - 0.2) + 0.73, with
    L_phi = min(L_left, L_right). This reproduces BG40 value 1.1079 for L_phi = 35 m.
    """
    Lphi = min(float(L_left_m), float(L_right_m))
    if Lphi <= 0.04:
        phi = float("inf")
    else:
        phi = 2.16 / (sqrt(Lphi) - 0.20) + 0.73
    return {"Lphi_m": Lphi, "phi": phi}


def longitudinal_force_en1991(length_m: float, span_m: float, traction_rate_kn_m: float = 33.0, braking_rate_kn_m: float = 20.0, traction_cap_kn: float = 1000.0, braking_cap_kn: float = 6000.0) -> Dict[str, float]:
    q_lak_raw = traction_rate_kn_m * length_m
    q_lbk_raw = braking_rate_kn_m * length_m
    q_lak = min(q_lak_raw, traction_cap_kn)
    q_lbk = min(q_lbk_raw, braking_cap_kn)
    design = max(q_lak, q_lbk)
    return {
        "Qlak_raw_kn": q_lak_raw,
        "Qlak_kn": q_lak,
        "Qlbk_raw_kn": q_lbk_raw,
        "Qlbk_kn": q_lbk,
        "LF_design_kn": design,
        "LF_design_kn_m": design / span_m if span_m else 0.0,
    }


def hunting_force_en1991(qsk_kn: float = 100.0, alpha: float = 0.8, reduce_when_alpha_lt_1: bool = False) -> Dict[str, float | str]:
    """EN 1991-2 nosing/hunting force decision logic.

    Qsk is not reduced for alpha < 1 unless a project requirement explicitly permits it.
    """
    if alpha >= 1.0:
        adopted = alpha * qsk_kn
        basis = "α ≥ 1, Qsk amplified by α"
    elif reduce_when_alpha_lt_1:
        adopted = alpha * qsk_kn
        basis = "User override: α < 1 reduction allowed by project setting"
    else:
        adopted = qsk_kn
        basis = "α < 1 shown for vertical U20 load classification; Qsk is not reduced by default"
    return {"Qsk_kn": qsk_kn, "alpha": alpha, "HF_adopted_kn": adopted, "decision_basis": basis}


def wind_load_en1991_dpt(rho_air_kg_m3: float, vb_m_s: float, C_ws: float, C_ws_wl: float, dtot_ws_m: float, dtot_ws_wl_m: float, span_m: float) -> Dict[str, float]:
    q_pa = 0.5 * rho_air_kg_m3 * vb_m_s**2
    aref_ws = dtot_ws_m * span_m
    aref_wl = dtot_ws_wl_m * span_m
    ws_kn = q_pa * C_ws * aref_ws / 1000.0
    ws_wl_kn = q_pa * C_ws_wl * aref_wl / 1000.0
    return {
        "q_pa": q_pa,
        "Aref_ws_m2": aref_ws,
        "Aref_ws_wl_m2": aref_wl,
        "WSsuper_kn": ws_kn,
        "WSsuper_WL_kn": ws_wl_kn,
        "WSsuper_kn_m": ws_kn / span_m if span_m else 0.0,
        "WSsuper_WL_kn_m": ws_wl_kn / span_m if span_m else 0.0,
    }
