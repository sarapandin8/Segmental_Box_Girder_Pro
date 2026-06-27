from __future__ import annotations

import pandas as pd

from visualization.tendon_figures import tendon_section_overlay_figure


def _coords() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"loop_name": "Structural Polygon 1", "loop_type": "outer", "point_no": 1, "x_mm": 0.0, "y_mm": 0.0},
            {"loop_name": "Structural Polygon 1", "loop_type": "outer", "point_no": 2, "x_mm": 11200.0, "y_mm": 0.0},
            {"loop_name": "Structural Polygon 1", "loop_type": "outer", "point_no": 3, "x_mm": 11200.0, "y_mm": 2500.0},
            {"loop_name": "Structural Polygon 1", "loop_type": "outer", "point_no": 4, "x_mm": 0.0, "y_mm": 2500.0},
            {"loop_name": "Opening Polygon 1", "loop_type": "hole", "point_no": 1, "x_mm": 1000.0, "y_mm": 250.0},
            {"loop_name": "Opening Polygon 1", "loop_type": "hole", "point_no": 2, "x_mm": 10200.0, "y_mm": 250.0},
            {"loop_name": "Opening Polygon 1", "loop_type": "hole", "point_no": 3, "x_mm": 10200.0, "y_mm": 2050.0},
            {"loop_name": "Opening Polygon 1", "loop_type": "hole", "point_no": 4, "x_mm": 1000.0, "y_mm": 2050.0},
        ]
    )


def _props() -> dict:
    return {
        "valid": True,
        "width_m": 11.2,
        "depth_m": 2.5,
        "bounds_mm": {"xmin": 0.0, "xmax": 11200.0, "ymin": 0.0, "ymax": 2500.0},
        "cx_mm": 5600.0,
        "cy_mm": 1661.0,
        "ycg_from_bottom_m": 1.661,
        "yt_from_top_m": 0.839,
    }


def _points() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Tendon": "T1-L", "Family": "T1", "Station (m)": 19.975, "dp from top (m)": 2.15, "HorizOff (m)": 1.45},
            {"Tendon": "T1-R", "Family": "T1", "Station (m)": 19.975, "dp from top (m)": 2.15, "HorizOff (m)": -1.45},
        ]
    )


def _annotation_texts(fig) -> list[str]:
    return [str(a.text) for a in (fig.layout.annotations or [])]


def test_tendon_overlay_clean_dimension_mode_uses_essential_guides_only():
    fig = tendon_section_overlay_figure(_coords(), _props(), _points(), origin_mode="centerline", dimension_mode="clean")
    texts = _annotation_texts(fig)
    assert "B = 11200 mm" in texts
    assert "D = 2500 mm" in texts
    assert "CL" in texts
    assert "CG" in texts
    assert not any(t.startswith("y_cg =") for t in texts)
    assert not any(t.startswith("y_t =") for t in texts)


def test_tendon_overlay_full_and_hide_dimension_modes_are_distinct():
    full = tendon_section_overlay_figure(_coords(), _props(), _points(), origin_mode="centerline", dimension_mode="full")
    full_texts = _annotation_texts(full)
    assert "y_cg = 1661 mm" in full_texts
    assert "y_t = 839 mm" in full_texts

    hidden = tendon_section_overlay_figure(_coords(), _props(), _points(), origin_mode="centerline", dimension_mode="hide")
    hidden_texts = _annotation_texts(hidden)
    assert not any(t.startswith("B =") or t.startswith("D =") or t in {"CL", "CG"} for t in hidden_texts)
    assert "Centroid" not in {str(getattr(trace, "name", "")) for trace in hidden.data}


def test_tendon_overlay_viewport_opens_compact_without_scaleanchor_expansion():
    fig = tendon_section_overlay_figure(_coords(), _props(), _points(), origin_mode="centerline", dimension_mode="clean")
    x_range = list(fig.layout.xaxis.range)
    y_range = list(fig.layout.yaxis.range)
    assert x_range[0] > -7000
    assert x_range[1] < 7200
    assert y_range[0] > -350
    assert y_range[1] < 3300
    assert fig.layout.yaxis.autorange is False


def _model_3d() -> dict:
    return {
        "valid": True,
        "span_m": 40.0,
        "tendons": [
            {
                "tendon": "T1-L",
                "family": "T1",
                "side": "L",
                "vertical_profile": [
                    {"x_m": 0.0, "dp_top_m": 1.20},
                    {"x_m": 20.0, "dp_top_m": 2.15},
                    {"x_m": 40.0, "dp_top_m": 1.20},
                ],
                "horizontal_profile": [
                    {"x_m": 0.0, "horiz_off_m": 1.30},
                    {"x_m": 20.0, "horiz_off_m": 1.45},
                    {"x_m": 40.0, "horiz_off_m": 1.30},
                ],
            },
            {
                "tendon": "T1-R",
                "family": "T1",
                "side": "R",
                "vertical_profile": [
                    {"x_m": 0.0, "dp_top_m": 1.20},
                    {"x_m": 20.0, "dp_top_m": 2.15},
                    {"x_m": 40.0, "dp_top_m": 1.20},
                ],
                "horizontal_profile": [
                    {"x_m": 0.0, "horiz_off_m": -1.30},
                    {"x_m": 20.0, "horiz_off_m": -1.45},
                    {"x_m": 40.0, "horiz_off_m": -1.30},
                ],
            },
        ],
    }


def test_tendon_3d_review_uses_section_envelope_and_3d_tendon_lines():
    from visualization.tendon_figures import tendon_3d_review_figure

    fig = tendon_3d_review_figure(_model_3d(), _coords(), _props(), view_preset="Isometric")
    trace_types = [tr.type for tr in fig.data]
    assert "mesh3d" in trace_types
    assert "scatter3d" in trace_types
    assert fig.layout.scene.xaxis.title.text == "Station x (m)"
    assert fig.layout.scene.yaxis.title.text == "HorizOff / section Y (m)"
    assert fig.layout.scene.zaxis.title.text == "z from bottom (m)"
    assert fig.layout.uirevision == "tendon_3d_review"


def test_tendon_3d_review_filter_can_show_left_side_only():
    from visualization.tendon_figures import tendon_3d_review_figure

    fig = tendon_3d_review_figure(_model_3d(), _coords(), _props(), side_filter="Left only", show_outer_shell=False, show_inner_void=False, show_station_markers=False)
    tendon_names = {str(tr.name) for tr in fig.data if tr.type == "scatter3d"}
    assert "T1-L" in tendon_names
    assert "T1-R" not in tendon_names
