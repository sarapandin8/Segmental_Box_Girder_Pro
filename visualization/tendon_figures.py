"""Plotly figures for CSiBridge tendon-layout imports."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from visualization.figure_system import (
    ENGINEERING_REPORT_CONFIG,
    ENGINEERING_REVIEW_CONFIG,
    apply_engineering_figure_layout,
)


FAMILY_COLORS = [
    "#2563eb", "#16a34a", "#d97706", "#7c3aed",
    "#0891b2", "#db2777", "#65a30d", "#dc2626",
]


def _family_index(family: str) -> int:
    import re
    m = re.search(r"(\d+)", str(family or ""))
    return (int(m.group(1)) - 1) if m else 0


def _family_color(family: str) -> str:
    return FAMILY_COLORS[_family_index(family) % len(FAMILY_COLORS)]


def _label_for_mode(row: dict, label_mode: str) -> str:
    mode = str(label_mode or "hide").lower()
    if mode.startswith("all"):
        return str(row.get("Tendon", row.get("tendon", "")))
    if mode.startswith("family"):
        return str(row.get("Family", row.get("family", "")))
    return ""

PLOTLY_TENDON_CONFIG = ENGINEERING_REVIEW_CONFIG

# Global figure system aliases retained for existing app imports/tests.
# Interactive review keeps the Plotly modebar for zoom/pan/reset/camera checks.
# Report preview hides the modebar so exported/report figures stay clean.
# Legacy explicit settings retained in comments for regression trace: "displayModeBar": True / "displayModeBar": False
PLOTLY_TENDON_REVIEW_CONFIG = ENGINEERING_REVIEW_CONFIG
PLOTLY_TENDON_REPORT_CONFIG = ENGINEERING_REPORT_CONFIG
PLOTLY_TENDON_CANVAS_CONFIG = PLOTLY_TENDON_REPORT_CONFIG



def _style_layout(fig: go.Figure, title: str, x_title: str, y_title: str, *, showlegend: bool = True) -> go.Figure:
    return apply_engineering_figure_layout(
        fig,
        title=title,
        x_title=x_title,
        y_title=y_title,
        height=520,
        showlegend=showlegend,
        margin=dict(l=56, r=26, t=56 if title else 34, b=54),
    )


def _tendon_passes_filter(tendon: dict, *, family_filter: str | None = None, side_filter: str | None = None) -> bool:
    fam = str(tendon.get("family") or tendon.get("Family") or "")
    side = str(tendon.get("side") or tendon.get("Side") or "")
    family_text = str(family_filter or "All families")
    side_text = str(side_filter or "Both sides")
    if family_text != "All families" and fam != family_text:
        return False
    if side_text in {"Left only", "L"} and side != "L":
        return False
    if side_text in {"Right only", "R"} and side != "R":
        return False
    return True


def _side_line_dash(side: str) -> str:
    return "solid" if str(side).upper() != "R" else "dot"


def tendon_elevation_figure(
    model: dict,
    *,
    show_labels: bool = False,
    family_filter: str | None = None,
    side_filter: str | None = None,
    showlegend: bool = False,
) -> go.Figure:
    fig = go.Figure()
    for t in model.get("tendons", []):
        if not _tendon_passes_filter(t, family_filter=family_filter, side_filter=side_filter):
            continue
        prof = pd.DataFrame(t.get("vertical_profile", []))
        if prof.empty:
            continue
        text = [t.get("tendon", "") if show_labels else "" for _ in range(len(prof))]
        family = str(t.get("family", ""))
        side = str(t.get("side", ""))
        fig.add_trace(
            go.Scatter(
                x=prof["x_m"],
                y=prof["dp_top_m"],
                mode="lines+markers+text" if show_labels else "lines+markers",
                name=t.get("tendon", ""),
                legendgroup=family,
                text=text,
                textposition="top center",
                hovertemplate="%{fullData.name}<br>x = %{x:.3f} m<br>dp = %{y:.3f} m<extra></extra>",
                line=dict(width=2.2, color=_family_color(family), dash=_side_line_dash(side)),
                marker=dict(size=6, color=_family_color(family), line=dict(width=0.8, color="#0f172a")),
            )
        )
    span = float(model.get("span_m") or 0.0)
    mid = float(model.get("midspan_m") or span / 2.0)
    if span:
        fig.add_vline(x=0, line_dash="dot", line_color="#64748b", annotation_text="Start")
        fig.add_vline(x=mid, line_dash="dash", line_color="#dc2626", annotation_text="Midspan")
        fig.add_vline(x=span, line_dash="dot", line_color="#64748b", annotation_text="End")
        fig.update_xaxes(range=[-0.02 * span, span * 1.02], autorange=False)
    _style_layout(fig, "", "Station x (m)", "dp from top (m)", showlegend=showlegend)
    fig.update_yaxes(autorange="reversed", gridcolor="rgba(148,163,184,0.09)")
    fig.update_xaxes(gridcolor="rgba(148,163,184,0.09)")
    return fig


def tendon_plan_figure(
    model: dict,
    *,
    show_labels: bool = False,
    family_filter: str | None = None,
    side_filter: str | None = None,
    showlegend: bool = False,
) -> go.Figure:
    fig = go.Figure()
    for t in model.get("tendons", []):
        if not _tendon_passes_filter(t, family_filter=family_filter, side_filter=side_filter):
            continue
        prof = pd.DataFrame(t.get("horizontal_profile", []))
        if prof.empty:
            continue
        text = [t.get("tendon", "") if show_labels else "" for _ in range(len(prof))]
        family = str(t.get("family", ""))
        side = str(t.get("side", ""))
        fig.add_trace(
            go.Scatter(
                x=prof["x_m"],
                y=prof["horiz_off_m"],
                mode="lines+markers+text" if show_labels else "lines+markers",
                name=t.get("tendon", ""),
                legendgroup=family,
                text=text,
                textposition="top center",
                hovertemplate="%{fullData.name}<br>x = %{x:.3f} m<br>HorizOff = %{y:.3f} m<extra></extra>",
                line=dict(width=2.2, color=_family_color(family), dash=_side_line_dash(side)),
                marker=dict(size=6, color=_family_color(family), line=dict(width=0.8, color="#0f172a")),
            )
        )
    span = float(model.get("span_m") or 0.0)
    mid = float(model.get("midspan_m") or span / 2.0)
    if span:
        fig.add_vline(x=0, line_dash="dot", line_color="#64748b", annotation_text="Start")
        fig.add_vline(x=mid, line_dash="dash", line_color="#dc2626", annotation_text="Midspan")
        fig.add_vline(x=span, line_dash="dot", line_color="#64748b", annotation_text="End")
        fig.update_xaxes(range=[-0.02 * span, span * 1.02], autorange=False)
    fig.add_hline(y=0, line_dash="dash", line_color="#475569", annotation_text="CL")
    _style_layout(fig, "", "Station x (m)", "HorizOff from CL (m)", showlegend=showlegend)
    fig.update_xaxes(gridcolor="rgba(148,163,184,0.09)")
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.09)")
    return fig




def _section_bounds_for_display(section_coords: pd.DataFrame, section_props: dict, origin_mode: str) -> dict[str, float]:
    """Return section bounds in the same display coordinates used by the overlay figure."""
    bounds = section_props.get("bounds_mm", {}) if section_props else {}
    xmin = float(bounds.get("xmin", section_coords["x_mm"].min() if section_coords is not None and not section_coords.empty else 0.0))
    xmax = float(bounds.get("xmax", section_coords["x_mm"].max() if section_coords is not None and not section_coords.empty else 0.0))
    ymin = float(bounds.get("ymin", section_coords["y_mm"].min() if section_coords is not None and not section_coords.empty else 0.0))
    ymax = float(bounds.get("ymax", section_coords["y_mm"].max() if section_coords is not None and not section_coords.empty else 0.0))
    x_shift = 0.5 * (xmin + xmax) if str(origin_mode).lower().startswith("center") else 0.0
    return {
        "xmin_raw": xmin,
        "xmax_raw": xmax,
        "xmin": xmin - x_shift,
        "xmax": xmax - x_shift,
        "ymin": ymin,
        "ymax": ymax,
        "x_shift": x_shift,
        "width": xmax - xmin,
        "depth": ymax - ymin,
    }


def _tick_shape(x0: float, y0: float, x1: float, y1: float, color: str) -> dict:
    return {"type": "line", "x0": x0, "y0": y0, "x1": x1, "y1": y1, "line": {"color": color, "width": 1.35}}


def _dimension_label(
    fig: go.Figure,
    *,
    x: float,
    y: float,
    text: str,
    textangle: int = 0,
    color: str = "#64748b",
    size: int = 12,
) -> None:
    fig.add_annotation(
        x=x,
        y=y,
        text=text,
        textangle=textangle,
        showarrow=False,
        align="center",
        bgcolor="rgba(255,255,255,0.96)",
        bordercolor="rgba(100,116,139,0.50)",
        borderwidth=1,
        borderpad=4,
        font={"color": color, "size": size},
    )


def _add_horizontal_dimension(
    fig: go.Figure,
    *,
    x0: float,
    x1: float,
    y: float,
    ext_to_y: float,
    label: str,
    color: str,
) -> None:
    tick = 52.0
    fig.add_shape(type="line", x0=x0, y0=ext_to_y, x1=x0, y1=y, line={"color": color, "width": 1.15})
    fig.add_shape(type="line", x0=x1, y0=ext_to_y, x1=x1, y1=y, line={"color": color, "width": 1.15})
    fig.add_shape(type="line", x0=x0, y0=y, x1=x1, y1=y, line={"color": color, "width": 1.45})
    fig.add_shape(**_tick_shape(x0 - tick, y - tick, x0 + tick, y + tick, color))
    fig.add_shape(**_tick_shape(x1 - tick, y - tick, x1 + tick, y + tick, color))
    _dimension_label(fig, x=0.5 * (x0 + x1), y=y + 88.0, text=label, color=color, size=12)


def _add_vertical_dimension(
    fig: go.Figure,
    *,
    x: float,
    y0: float,
    y1: float,
    ext_to_x: float,
    label: str,
    color: str,
    label_side: str = "left",
) -> None:
    tick = 52.0
    fig.add_shape(type="line", x0=ext_to_x, y0=y0, x1=x, y1=y0, line={"color": color, "width": 1.15})
    fig.add_shape(type="line", x0=ext_to_x, y0=y1, x1=x, y1=y1, line={"color": color, "width": 1.15})
    fig.add_shape(type="line", x0=x, y0=y0, x1=x, y1=y1, line={"color": color, "width": 1.45})
    fig.add_shape(**_tick_shape(x - tick, y0 - tick, x + tick, y0 + tick, color))
    fig.add_shape(**_tick_shape(x - tick, y1 - tick, x + tick, y1 + tick, color))
    dx = -112.0 if label_side == "left" else 112.0
    _dimension_label(fig, x=x + dx, y=0.5 * (y0 + y1), text=label, textangle=-90, color=color, size=12)


def _apply_tendon_overlay_viewport(
    fig: go.Figure,
    section_coords: pd.DataFrame,
    section_props: dict,
    *,
    origin_mode: str,
    include_dimensions: bool,
    full_dimensions: bool = False,
) -> go.Figure:
    """Apply a compact default viewport so the section opens large enough for review.

    The base section figure uses equal-axis scaling for geometric drawings.  In a
    very wide Streamlit canvas that can make the box girder look small.  The
    tendon overlay is a review/report viewport, so it uses an explicit compact
    range with fixed autorange disabled while preserving an approximately true
    engineering proportion.
    """
    if not section_props.get("valid"):
        return fig
    b = _section_bounds_for_display(section_coords, section_props, origin_mode)
    xmin = b["xmin"]
    xmax = b["xmax"]
    ymin = b["ymin"]
    ymax = b["ymax"]
    width = max(float(b["width"]), 1.0)
    depth = max(float(b["depth"]), 1.0)

    if include_dimensions:
        left_pad = max(620.0, 0.090 * width)
        right_pad = max(620.0, 0.090 * width) * (1.34 if full_dimensions else 1.08)
        top_pad = max(580.0, 0.245 * depth)
        bottom_pad = max(230.0, 0.090 * depth)
    else:
        left_pad = max(360.0, 0.050 * width)
        right_pad = max(360.0, 0.050 * width)
        top_pad = max(300.0, 0.130 * depth)
        bottom_pad = max(170.0, 0.070 * depth)

    fig.update_xaxes(range=[xmin - left_pad, xmax + right_pad], autorange=False)
    fig.update_yaxes(range=[ymin - bottom_pad, ymax + top_pad], autorange=False, scaleanchor=None, scaleratio=None)
    return fig


def _add_tendon_overlay_dimension_layer(
    fig: go.Figure,
    section_coords: pd.DataFrame,
    section_props: dict,
    *,
    origin_mode: str,
    dimension_mode: str = "clean",
) -> go.Figure:
    """Add report-style dimension guides for the tendon section overlay.

    Modes:
    - clean: B, D, CL, and centroid guides only.
    - full dimensions: clean plus y_cg and y_t fiber dimensions.
    - hide dimensions: no dimension guide layer.
    """
    mode = str(dimension_mode or "clean").strip().lower()
    if mode.startswith("hide") or not section_props.get("valid"):
        return _apply_tendon_overlay_viewport(
            fig,
            section_coords,
            section_props,
            origin_mode=origin_mode,
            include_dimensions=False,
        )

    b = _section_bounds_for_display(section_coords, section_props, origin_mode)
    xmin = b["xmin"]
    xmax = b["xmax"]
    ymin = b["ymin"]
    ymax = b["ymax"]
    width = max(float(b["width"]), 1.0)
    depth = max(float(b["depth"]), 1.0)
    cx = float(section_props.get("cx_mm", 0.5 * (b["xmin_raw"] + b["xmax_raw"]))) - b["x_shift"]
    cy = float(section_props.get("cy_mm", 0.5 * (ymin + ymax)))

    dim_color = "#66768c"
    cl_color = "#2563eb"
    cg_color = "#be123c"
    cg_line_color = "rgba(190,18,60,0.50)"
    top_offset = max(360.0, 0.17 * depth)
    left_offset = max(520.0, 0.075 * width)
    right_offset = max(520.0, 0.065 * width)
    y_dim = ymax + top_offset
    x_dim_left = xmin - left_offset
    x_dim_right = xmax + right_offset

    _add_horizontal_dimension(
        fig,
        x0=xmin,
        x1=xmax,
        y=y_dim,
        ext_to_y=ymax + 0.018 * depth,
        label=f"B = {width:.0f} mm",
        color=dim_color,
    )
    _add_vertical_dimension(
        fig,
        x=x_dim_left,
        y0=ymin,
        y1=ymax,
        ext_to_x=xmin - 0.018 * width,
        label=f"D = {depth:.0f} mm",
        color=dim_color,
        label_side="left",
    )

    # Centerline guide is part of the Clean view because the overlay is reviewed by horizontal offset from CL.
    if str(origin_mode).lower().startswith("center"):
        fig.add_shape(
            type="line",
            x0=0,
            y0=ymin - 0.06 * depth,
            x1=0,
            y1=ymax + 0.065 * depth,
            line={"color": "rgba(37,99,235,0.48)", "width": 1.05, "dash": "dash"},
        )
        _dimension_label(fig, x=0, y=ymax + 0.085 * depth, text="CL", color=cl_color, size=11)

    # Centroid guides are deliberately lighter than the tendon points to avoid visual competition.
    fig.add_shape(type="line", x0=xmin, y0=cy, x1=xmax, y1=cy, line={"color": cg_line_color, "width": 0.95, "dash": "dot"})
    fig.add_shape(type="line", x0=cx, y0=ymin, x1=cx, y1=ymax, line={"color": cg_line_color, "width": 0.95, "dash": "dot"})
    _dimension_label(fig, x=cx + 0.070 * width, y=cy + 0.055 * depth, text="CG", color=cg_color, size=11)

    if mode.startswith("full"):
        ycg_mm = float(section_props.get("ycg_from_bottom_m", cy / 1000.0)) * 1000.0
        yt_mm = float(section_props.get("yt_from_top_m", max(ymax - cy, 0.0) / 1000.0)) * 1000.0
        x_fiber = x_dim_right
        _add_vertical_dimension(
            fig,
            x=x_fiber,
            y0=ymin,
            y1=cy,
            ext_to_x=xmax + 0.018 * width,
            label=f"y_cg = {ycg_mm:.0f} mm",
            color=dim_color,
            label_side="right",
        )
        _add_vertical_dimension(
            fig,
            x=x_fiber + 0.34 * right_offset,
            y0=cy,
            y1=ymax,
            ext_to_x=xmax + 0.018 * width,
            label=f"y_t = {yt_mm:.0f} mm",
            color=dim_color,
            label_side="right",
        )

    # Give the external dimension layer breathing room, but keep the section large
    # enough for review when the canvas first opens.
    return _apply_tendon_overlay_viewport(
        fig,
        section_coords,
        section_props,
        origin_mode=origin_mode,
        include_dimensions=True,
        full_dimensions=mode.startswith("full"),
    )


def tendon_section_overlay_figure(
    section_coords: pd.DataFrame,
    section_props: dict,
    tendon_points: pd.DataFrame,
    *,
    positive_offset_direction: str = "left",
    point_label_mode: str = "family",
    show_point_numbers: bool = True,
    origin_mode: str = "csibridge",
    dimension_mode: str = "clean",
    station_label: str | None = None,
    station_m: float | None = None,
) -> go.Figure:
    from visualization.section_figures import section_polygon_figure

    fig = section_polygon_figure(
        section_coords,
        section_props,
        point_label_mode="major" if show_point_numbers else "hide",
        show_dimensions=False,
        origin_mode=origin_mode,
    )
    # Clean CSiBridge loop names into report-ready legend labels.
    hide_dimensions = str(dimension_mode or "clean").strip().lower().startswith("hide")
    for tr in fig.data:
        name = str(getattr(tr, "name", ""))
        if name.startswith("Structural Polygon"):
            tr.name = "Concrete"
            tr.legendgroup = "section"
        elif name.startswith("Opening Polygon"):
            tr.name = "Inner void"
            tr.legendgroup = "section"
        elif name == "Centroid":
            tr.legendgroup = "section"
            tr.mode = "markers"
            tr.text = [""]
    if hide_dimensions:
        fig.data = tuple(tr for tr in fig.data if str(getattr(tr, "name", "")) != "Centroid")

    if tendon_points is not None and not tendon_points.empty:
        width_m = float(section_props.get("width_m") or section_props.get("B_m") or 0.0)
        depth_m = float(section_props.get("depth_m") or section_props.get("D_m") or 0.0)
        bounds = section_props.get("bounds_mm", {}) if section_props else {}
        xmin = float(bounds.get("xmin", 0.0))
        xmax = float(bounds.get("xmax", width_m * 1000.0))
        x_shift = 0.0
        if str(origin_mode).lower().startswith("center"):
            x_shift = 0.5 * (xmin + xmax)

        for family, g in tendon_points.groupby("Family", sort=False):
            xs = []
            ys = []
            text = []
            hover = []
            for _, r in g.iterrows():
                off = float(r["HorizOff (m)"])
                dp = float(r["dp from top (m)"])
                if positive_offset_direction == "left":
                    x_m = width_m / 2.0 - off
                else:
                    x_m = width_m / 2.0 + off
                y_m = depth_m - dp
                x_mm = x_m * 1000.0 - x_shift
                y_mm = y_m * 1000.0
                xs.append(x_mm)
                ys.append(y_mm)
                label = _label_for_mode(r.to_dict(), point_label_mode)
                text.append(label)
                hover.append(
                    f"{r['Tendon']}<br>Family = {r['Family']}<br>Station = {float(r['Station (m)']):.3f} m"
                    f"<br>dp = {dp:.3f} m<br>HorizOff = {off:.3f} m"
                    f"<br>x(section) = {x_mm:.0f} mm<br>y(section) = {y_mm:.0f} mm"
                )
            show_text = any(str(t) for t in text)
            fig.add_trace(
                go.Scatter(
                    x=xs,
                    y=ys,
                    mode="markers+text" if show_text else "markers",
                    name=str(family),
                    text=text,
                    textposition="top center",
                    marker=dict(symbol="circle", size=10, color=_family_color(str(family)), line=dict(width=1.2, color="#0f172a")),
                    hovertemplate="%{customdata}<extra></extra>",
                    customdata=hover,
                )
            )
    # M3H.9: Station = ... is intentionally not drawn inside the Plotly body.
    # The app renders the selected station as a clear badge above the drawing viewport.
    fig = _add_tendon_overlay_dimension_layer(
        fig,
        section_coords,
        section_props,
        origin_mode=origin_mode,
        dimension_mode=dimension_mode,
    )

    apply_engineering_figure_layout(
        fig,
        title="",
        x_title="x (mm, CL = 0)" if str(origin_mode).lower().startswith("center") else "x (mm)",
        y_title="y (mm)",
        height=520,
        showlegend=True,
        margin=dict(l=50, r=18, t=44, b=52),
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.055, xanchor="center", x=0.5, font=dict(size=11)),
    )
    return fig
