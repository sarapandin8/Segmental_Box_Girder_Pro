from core.section_geometry import calculate_section_properties, normalize_coordinate_rows
import pandas as pd


def _rect_hole_rows():
    return pd.DataFrame([
        {"loop_name":"Structural Polygon 1","point_no":1,"x_mm":0,"y_mm":0},
        {"loop_name":"Structural Polygon 1","point_no":2,"x_mm":4000,"y_mm":0},
        {"loop_name":"Structural Polygon 1","point_no":3,"x_mm":4000,"y_mm":2000},
        {"loop_name":"Structural Polygon 1","point_no":4,"x_mm":0,"y_mm":2000},
        {"loop_name":"Opening Polygon 1","point_no":1,"x_mm":1000,"y_mm":500},
        {"loop_name":"Opening Polygon 1","point_no":2,"x_mm":3000,"y_mm":500},
        {"loop_name":"Opening Polygon 1","point_no":3,"x_mm":3000,"y_mm":1500},
        {"loop_name":"Opening Polygon 1","point_no":4,"x_mm":1000,"y_mm":1500},
    ])


def test_normalize_csibridge_alias_columns():
    raw = pd.DataFrame([
        {"Shape":"Structural Polygon 1","Point":1,"X":0,"Y":0},
        {"Shape":"Structural Polygon 1","Point":2,"X":1000,"Y":0},
        {"Shape":"Structural Polygon 1","Point":3,"X":0,"Y":1000},
    ])
    out = normalize_coordinate_rows(raw)
    assert list(out.columns) == ["loop_name", "loop_type", "point_no", "x_mm", "y_mm"]
    assert out.iloc[0]["loop_type"] == "outer"


def test_hollow_rectangle_properties_subtract_opening():
    props = calculate_section_properties(_rect_hole_rows())
    assert props["valid"] is True
    assert abs(props["A_m2"] - 6.0) < 1e-9
    assert abs(props["cx_mm"] - 2000.0) < 1e-9
    assert abs(props["cy_mm"] - 1000.0) < 1e-9
    assert abs(props["I33_m4"] - 2.5) < 1e-9
    assert abs(props["I22_m4"] - 10.0) < 1e-9
    assert abs(props["ycg_from_bottom_m"] - 1.0) < 1e-9
    assert abs(props["yt_from_top_m"] - 1.0) < 1e-9


def test_clockwise_loops_are_normalized_by_loop_type():
    rows = _rect_hole_rows()
    # Reverse each loop to simulate clockwise / counter-clockwise export variations.
    rows = pd.concat([
        rows[rows.loop_name == "Structural Polygon 1"].sort_values("point_no", ascending=False),
        rows[rows.loop_name == "Opening Polygon 1"].sort_values("point_no", ascending=False),
    ], ignore_index=True)
    props = calculate_section_properties(rows)
    assert props["valid"] is True
    assert abs(props["A_m2"] - 6.0) < 1e-9
