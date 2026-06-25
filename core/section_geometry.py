from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from typing import Iterable, Any

import pandas as pd


OUTER_ALIASES = {"outer", "structural", "structural polygon", "structural polygon 1", "concrete", "boundary"}
HOLE_ALIASES = {"hole", "opening", "void", "opening polygon", "opening polygon 1", "inner"}


@dataclass(frozen=True)
class LoopProperties:
    loop_type: str
    name: str
    n_points: int
    area_mm2: float
    cx_mm: float
    cy_mm: float
    ixx_o_mm4: float
    iyy_o_mm4: float
    ixy_o_mm4: float
    perimeter_mm: float


def _as_float(value: Any) -> float:
    if value is None:
        raise ValueError("empty numeric value")
    if isinstance(value, (int, float)):
        v = float(value)
    else:
        v = float(str(value).strip().replace(",", ""))
    if not isfinite(v):
        raise ValueError("non-finite numeric value")
    return v


def canonical_loop_type(loop_name: str) -> str:
    name = str(loop_name or "").strip().lower()
    if name in OUTER_ALIASES or name.startswith("structural"):
        return "outer"
    if name in HOLE_ALIASES or name.startswith("opening"):
        return "hole"
    # Sensible fallback: first/unknown loops are treated as outer only by UI after QA warning.
    return "unknown"


def normalize_coordinate_rows(rows: Iterable[dict[str, Any]] | pd.DataFrame) -> pd.DataFrame:
    """Normalize CSiBridge-style section coordinate rows.

    Supported aliases include Shape/loop_name, Point/point_no, X/x_mm, Y/y_mm.
    The input coordinates are expected in millimetres.
    """
    df = rows.copy() if isinstance(rows, pd.DataFrame) else pd.DataFrame(list(rows))
    if df.empty:
        return pd.DataFrame(columns=["loop_name", "loop_type", "point_no", "x_mm", "y_mm"])

    colmap = {}
    normalized_names = {str(c).strip().lower(): c for c in df.columns}
    for target, aliases in {
        "loop_name": ["loop_name", "loop", "shape", "polygon", "polygon_name", "loop id", "loop_id"],
        "point_no": ["point_no", "point", "point_id", "point no", "point_no.", "point number"],
        "x_mm": ["x_mm", "x", "x coordinate", "x-coordinate", "x (mm)", "x_mm.", "xcoord"],
        "y_mm": ["y_mm", "y", "y coordinate", "y-coordinate", "y (mm)", "y_mm.", "ycoord"],
    }.items():
        for alias in aliases:
            if alias in normalized_names:
                colmap[target] = normalized_names[alias]
                break
    missing = [c for c in ["loop_name", "point_no", "x_mm", "y_mm"] if c not in colmap]
    if missing:
        raise ValueError(f"Missing required coordinate column(s): {', '.join(missing)}")

    out = pd.DataFrame(
        {
            "loop_name": df[colmap["loop_name"]].ffill().astype(str).str.strip(),
            "point_no": df[colmap["point_no"]],
            "x_mm": df[colmap["x_mm"]],
            "y_mm": df[colmap["y_mm"]],
        }
    )
    out = out[out["point_no"].astype(str).str.strip().ne("")]
    out = out[out["x_mm"].astype(str).str.strip().ne("") & out["y_mm"].astype(str).str.strip().ne("")]
    out["point_no"] = out["point_no"].apply(lambda v: int(float(str(v).strip())))
    out["x_mm"] = out["x_mm"].apply(_as_float)
    out["y_mm"] = out["y_mm"].apply(_as_float)
    out["loop_type"] = out["loop_name"].apply(canonical_loop_type)
    out = out.sort_values(["loop_name", "point_no"], kind="stable").reset_index(drop=True)
    return out[["loop_name", "loop_type", "point_no", "x_mm", "y_mm"]]


def _signed_area(points: list[tuple[float, float]]) -> float:
    total = 0.0
    n = len(points)
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        total += x0 * y1 - x1 * y0
    return 0.5 * total


def _loop_properties(points: list[tuple[float, float]], loop_type: str, name: str) -> LoopProperties:
    if len(points) < 3:
        raise ValueError(f"Loop {name!r} has fewer than 3 points")
    # Normalize to counter-clockwise for positive geometric properties.
    if _signed_area(points) < 0:
        points = list(reversed(points))

    a2 = 0.0
    cx_num = 0.0
    cy_num = 0.0
    ixx_num = 0.0
    iyy_num = 0.0
    ixy_num = 0.0
    perimeter = 0.0
    n = len(points)
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        a2 += cross
        cx_num += (x0 + x1) * cross
        cy_num += (y0 + y1) * cross
        ixx_num += (y0 * y0 + y0 * y1 + y1 * y1) * cross
        iyy_num += (x0 * x0 + x0 * x1 + x1 * x1) * cross
        ixy_num += (2 * x0 * y0 + x0 * y1 + x1 * y0 + 2 * x1 * y1) * cross
        perimeter += sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)

    area = 0.5 * a2
    if abs(area) < 1e-9:
        raise ValueError(f"Loop {name!r} has near-zero area")
    cx = cx_num / (6.0 * area)
    cy = cy_num / (6.0 * area)
    ixx = ixx_num / 12.0
    iyy = iyy_num / 12.0
    ixy = ixy_num / 24.0
    return LoopProperties(loop_type, name, n, area, cx, cy, ixx, iyy, ixy, perimeter)


def _segment_intersection(p1, p2, p3, p4) -> bool:
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def on_segment(a, b, c):
        return min(a[0], b[0]) - 1e-9 <= c[0] <= max(a[0], b[0]) + 1e-9 and min(a[1], b[1]) - 1e-9 <= c[1] <= max(a[1], b[1]) + 1e-9

    o1 = orient(p1, p2, p3)
    o2 = orient(p1, p2, p4)
    o3 = orient(p3, p4, p1)
    o4 = orient(p3, p4, p2)
    if o1 * o2 < -1e-9 and o3 * o4 < -1e-9:
        return True
    if abs(o1) <= 1e-9 and on_segment(p1, p2, p3):
        return True
    if abs(o2) <= 1e-9 and on_segment(p1, p2, p4):
        return True
    if abs(o3) <= 1e-9 and on_segment(p3, p4, p1):
        return True
    if abs(o4) <= 1e-9 and on_segment(p3, p4, p2):
        return True
    return False


def loop_self_intersects(points: list[tuple[float, float]]) -> bool:
    n = len(points)
    if n < 4:
        return False
    for i in range(n):
        a1 = points[i]
        a2 = points[(i + 1) % n]
        for j in range(i + 1, n):
            # Adjacent segments share endpoints and should not count.
            if j in {i, (i - 1) % n, (i + 1) % n}:
                continue
            if i == 0 and j == n - 1:
                continue
            b1 = points[j]
            b2 = points[(j + 1) % n]
            if _segment_intersection(a1, a2, b1, b2):
                return True
    return False


def point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def calculate_section_properties(df: pd.DataFrame) -> dict[str, Any]:
    """Calculate hollow-section properties from normalized coordinate rows in mm."""
    coords = normalize_coordinate_rows(df)
    if coords.empty:
        return {"valid": False, "errors": ["No coordinate rows available"], "warnings": []}

    errors: list[str] = []
    warnings: list[str] = []
    loop_props: list[LoopProperties] = []
    outer_polygons: list[list[tuple[float, float]]] = []
    hole_polygons: list[list[tuple[float, float]]] = []

    for loop_name, g in coords.groupby("loop_name", sort=False):
        loop_type = str(g["loop_type"].iloc[0])
        points = list(zip(g["x_mm"].astype(float), g["y_mm"].astype(float)))
        if loop_type == "unknown":
            warnings.append(f"Loop {loop_name!r} has unknown type; use loop name Structural Polygon 1 or Opening Polygon 1.")
            continue
        if loop_self_intersects(points):
            errors.append(f"Loop {loop_name!r} appears to self-intersect.")
        try:
            props = _loop_properties(points, loop_type, str(loop_name))
            loop_props.append(props)
            if loop_type == "outer":
                outer_polygons.append(points)
            elif loop_type == "hole":
                hole_polygons.append(points)
        except ValueError as exc:
            errors.append(str(exc))

    if not any(p.loop_type == "outer" for p in loop_props):
        errors.append("No outer / Structural Polygon loop found.")
    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings, "coordinates": coords}

    # Check hole vertices inside at least one outer polygon.
    for h in hole_polygons:
        if outer_polygons and not all(any(point_in_polygon(pt, outer) for outer in outer_polygons) for pt in h):
            warnings.append("At least one opening polygon point is outside the structural polygon.")

    # Composite properties about origin. Holes are subtracted regardless of loop orientation.
    A = Cx_num = Cy_num = Ixx_o = Iyy_o = Ixy_o = 0.0
    for p in loop_props:
        sign = 1.0 if p.loop_type == "outer" else -1.0
        A += sign * p.area_mm2
        Cx_num += sign * p.area_mm2 * p.cx_mm
        Cy_num += sign * p.area_mm2 * p.cy_mm
        Ixx_o += sign * p.ixx_o_mm4
        Iyy_o += sign * p.iyy_o_mm4
        Ixy_o += sign * p.ixy_o_mm4
    if A <= 0:
        errors.append("Composite section area is not positive after subtracting openings.")
        return {"valid": False, "errors": errors, "warnings": warnings, "coordinates": coords}

    cx = Cx_num / A
    cy = Cy_num / A
    Ixx_c = Ixx_o - A * cy * cy
    Iyy_c = Iyy_o - A * cx * cx
    Ixy_c = Ixy_o - A * cx * cy

    xmin = float(coords["x_mm"].min())
    xmax = float(coords["x_mm"].max())
    ymin = float(coords["y_mm"].min())
    ymax = float(coords["y_mm"].max())
    y_top = ymax - cy
    y_bottom = cy - ymin
    x_left = cx - xmin
    x_right = xmax - cx
    S_top = Ixx_c / y_top if y_top > 0 else 0.0
    S_bottom = Ixx_c / y_bottom if y_bottom > 0 else 0.0
    S_left = Iyy_c / x_left if x_left > 0 else 0.0
    S_right = Iyy_c / x_right if x_right > 0 else 0.0

    return {
        "valid": True,
        "errors": errors,
        "warnings": warnings,
        "coordinates": coords,
        "loops": loop_props,
        "A_mm2": A,
        "A_m2": A / 1e6,
        "cx_mm": cx,
        "cy_mm": cy,
        "Ixx_mm4": Ixx_c,
        "Iyy_mm4": Iyy_c,
        "Ixy_mm4": Ixy_c,
        "I33_m4": Ixx_c / 1e12,
        "I22_m4": Iyy_c / 1e12,
        "Ixy_m4": Ixy_c / 1e12,
        "S_top_m3": S_top / 1e9,
        "S_bottom_m3": S_bottom / 1e9,
        "S_left_m3": S_left / 1e9,
        "S_right_m3": S_right / 1e9,
        "ycg_from_bottom_m": y_bottom / 1000.0,
        "yt_from_top_m": y_top / 1000.0,
        "width_m": (xmax - xmin) / 1000.0,
        "depth_m": (ymax - ymin) / 1000.0,
        "bounds_mm": {"xmin": xmin, "xmax": xmax, "ymin": ymin, "ymax": ymax},
        "mapping_note": "App x/y coordinates are read from CSiBridge section X/Y. I33 is reported from Ixx about the horizontal centroidal axis and I22 from Iyy about the vertical centroidal axis for BG40 review mapping.",
    }


def default_coordinate_template() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"loop_name": "Structural Polygon 1", "point_no": 1, "x_mm": 0.0, "y_mm": 0.0},
            {"loop_name": "Structural Polygon 1", "point_no": 2, "x_mm": 4000.0, "y_mm": 0.0},
            {"loop_name": "Structural Polygon 1", "point_no": 3, "x_mm": 4000.0, "y_mm": 2000.0},
            {"loop_name": "Structural Polygon 1", "point_no": 4, "x_mm": 0.0, "y_mm": 2000.0},
            {"loop_name": "Opening Polygon 1", "point_no": 1, "x_mm": 1000.0, "y_mm": 500.0},
            {"loop_name": "Opening Polygon 1", "point_no": 2, "x_mm": 3000.0, "y_mm": 500.0},
            {"loop_name": "Opening Polygon 1", "point_no": 3, "x_mm": 3000.0, "y_mm": 1500.0},
            {"loop_name": "Opening Polygon 1", "point_no": 4, "x_mm": 1000.0, "y_mm": 1500.0},
        ]
    )
