from __future__ import annotations

from dataclasses import dataclass
from math import inf
from pathlib import Path
from typing import Dict, List

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "dpt_1301_1302_61"

FA_TABLE = {
    "A": [0.8, 0.8, 0.8, 0.8, 0.8],
    "B": [1.0, 1.0, 1.0, 1.0, 1.0],
    "C": [1.2, 1.2, 1.1, 1.0, 1.0],
    "D": [1.6, 1.4, 1.2, 1.1, 1.0],
    "E": [2.5, 1.7, 1.2, 0.9, 0.9],
}
FV_TABLE = {
    "A": [0.8, 0.8, 0.8, 0.8, 0.8],
    "B": [1.0, 1.0, 1.0, 1.0, 1.0],
    "C": [1.7, 1.6, 1.5, 1.4, 1.3],
    "D": [2.4, 2.0, 1.8, 1.6, 1.5],
    "E": [3.5, 3.2, 2.8, 2.4, 2.4],
}
FA_X = [0.25, 0.50, 0.75, 1.00, 1.25]
FV_X = [0.10, 0.20, 0.30, 0.40, 0.50]
CATEGORY_RANK = {"ก": 0, "ข": 1, "ค": 2, "ง": 3}
CATEGORY_BY_RANK = {v: k for k, v in CATEGORY_RANK.items()}


def _interp(x: float, xs: List[float], ys: List[float]) -> float:
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            x0, x1 = xs[i - 1], xs[i]
            y0, y1 = ys[i - 1], ys[i]
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return ys[-1]


def site_coefficient_fa(soil_class: str, Ss: float) -> float:
    cls = soil_class.upper()
    if cls == "F":
        raise ValueError("Soil class F requires site-specific response analysis per DPT 1301/1302-61.")
    return _interp(float(Ss), FA_X, FA_TABLE[cls])


def site_coefficient_fv(soil_class: str, S1: float) -> float:
    cls = soil_class.upper()
    if cls == "F":
        raise ValueError("Soil class F requires site-specific response analysis per DPT 1301/1302-61.")
    return _interp(float(S1), FV_X, FV_TABLE[cls])


def load_general_location_database() -> pd.DataFrame:
    path = DATA_DIR / "general_ss_s1_seed.csv"
    return pd.read_csv(path)


def lookup_general_ss_s1(province: str, district: str) -> Dict[str, object]:
    df = load_general_location_database()
    province = province.replace("จังหวัด", "").strip()
    district = district.replace("อ.", "").replace("อำเภอ", "").strip()
    mask = (df["province_th"].str.strip() == province) & (df["district_th"].str.strip() == district)
    if not mask.any():
        return {"found": False, "province_th": province, "district_th": district}
    row = df[mask].iloc[0].to_dict()
    row["found"] = True
    return row


def dpt_general_spectrum(Ss: float, S1: float, soil_class: str, T_s: float, I: float, R: float) -> Dict[str, float | str]:
    Fa = site_coefficient_fa(soil_class, Ss)
    Fv = site_coefficient_fv(soil_class, S1)
    SMS = Fa * Ss
    SM1 = Fv * S1
    SDS = 2.0 / 3.0 * SMS
    SD1 = 2.0 / 3.0 * SM1
    Ts = SD1 / SDS if SDS else inf
    T0 = 0.2 * Ts
    T = float(T_s)
    if T <= 0:
        Sa = 0.0
        branch = "invalid T"
    elif T < T0:
        Sa = SDS * (0.4 + 0.6 * T / T0) if T0 else SDS
        branch = "0 < T < T0"
    elif T <= Ts:
        Sa = SDS
        branch = "T0 ≤ T ≤ Ts"
    else:
        Sa = SD1 / T
        branch = "T > Ts"
    Cs = Sa * I / R if R else inf
    Cs = max(Cs, 0.01)
    cat_sds = seismic_design_category_from_sds(SDS, importance_factor=I)
    cat_sd1 = seismic_design_category_from_sd1(SD1, importance_factor=I)
    governing = CATEGORY_BY_RANK[max(CATEGORY_RANK[cat_sds], CATEGORY_RANK[cat_sd1])]
    return {"Fa": Fa, "Fv": Fv, "SMS": SMS, "SM1": SM1, "SDS": SDS, "SD1": SD1, "T0": T0, "Ts": Ts, "Sa": Sa, "spectrum_branch": branch, "Cs": Cs, "category_sds": cat_sds, "category_sd1": cat_sd1, "category_governing": governing}


def _importance_group(I: float) -> str:
    if I >= 1.5:
        return "IV"
    if I >= 1.25:
        return "III"
    return "I_II"


def seismic_design_category_from_sds(SDS: float, importance_factor: float) -> str:
    group = _importance_group(importance_factor)
    if SDS < 0.167:
        return "ก"
    if SDS < 0.33:
        return "ค" if group == "IV" else "ข"
    if SDS < 0.50:
        return "ง" if group == "IV" else "ค"
    return "ง"


def seismic_design_category_from_sd1(SD1: float, importance_factor: float) -> str:
    group = _importance_group(importance_factor)
    if SD1 < 0.067:
        return "ก"
    if SD1 < 0.133:
        return "ค" if group == "IV" else "ข"
    if SD1 < 0.20:
        return "ง" if group == "IV" else "ค"
    return "ง"


def response_spectrum_points(SDS: float, SD1: float, t_max: float = 3.0, n: int = 90) -> pd.DataFrame:
    Ts = SD1 / SDS if SDS else 0.0
    T0 = 0.2 * Ts
    xs = [i * t_max / (n - 1) for i in range(n)]
    ys = []
    for T in xs:
        if T <= 0:
            Sa = 0.4 * SDS
        elif T < T0:
            Sa = SDS * (0.4 + 0.6 * T / T0) if T0 else SDS
        elif T <= Ts:
            Sa = SDS
        else:
            Sa = SD1 / T
        ys.append(Sa)
    return pd.DataFrame({"T (s)": xs, "Sa (g)": ys})
