"""Plotly figures for CSiBridge tendon-layout imports."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go



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

PLOTLY_TENDON_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToAdd": ["drawline", "drawrect", "eraseshape"],
    "toImageButtonOptions": {"format": "png", "filename": "tendon_layout", "height": 900, "width": 1500, "scale": 2},
}


def _style_layout(fig: go.Figure, title: str, x_title: str, y_title: str) -> go.Figure:
    fig.update_layout(
        title={"text": title, "x": 0.01, "xanchor": "left"},
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=50, r=24, t=60, b=55),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0),
        hovermode="closest",
        font=dict(size=12),
    )
    fig.update_xaxes(title_text=x_title, showgrid=True, gridcolor="#e5e7eb", zeroline=True, zerolinecolor="#94a3b8")
    fig.update_yaxes(title_text=y_title, showgrid=True, gridcolor="#e5e7eb", zeroline=True, zerolinecolor="#94a3b8")
    return fig


def tendon_elevation_figure(model: dict, *, show_labels: bool = False) -> go.Figure:
    fig = go.Figure()
    for t in model.get("tendons", []):
        prof = pd.DataFrame(t.get("vertical_profile", []))
        if prof.empty:
            continue
        text = [t.get("tendon", "") if show_labels else "" for _ in range(len(prof))]
        fig.add_trace(
            go.Scatter(
                x=prof["x_m"],
                y=prof["dp_top_m"],
                mode="lines+markers+text" if show_labels else "lines+markers",
                name=t.get("tendon", ""),
                text=text,
                textposition="top center",
                hovertemplate="%{fullData.name}<br>x = %{x:.3f} m<br>dp = %{y:.3f} m<extra></extra>",
                line=dict(width=2),
                marker=dict(size=6),
            )
        )
    span = float(model.get("span_m") or 0.0)
    mid = float(model.get("midspan_m") or span / 2.0)
    if span:
        fig.add_vline(x=0, line_dash="dot", line_color="#64748b", annotation_text="Start")
        fig.add_vline(x=mid, line_dash="dash", line_color="#dc2626", annotation_text="Midspan")
        fig.add_vline(x=span, line_dash="dot", line_color="#64748b", annotation_text="End")
    _style_layout(fig, "Tendon side elevation — dp measured from top surface", "Station x (m)", "dp from top (m)")
    fig.update_yaxes(autorange="reversed")
    return fig


def tendon_plan_figure(model: dict, *, show_labels: bool = False) -> go.Figure:
    fig = go.Figure()
    for t in model.get("tendons", []):
        prof = pd.DataFrame(t.get("horizontal_profile", []))
        if prof.empty:
            continue
        text = [t.get("tendon", "") if show_labels else "" for _ in range(len(prof))]
        fig.add_trace(
            go.Scatter(
                x=prof["x_m"],
                y=prof["horiz_off_m"],
                mode="lines+markers+text" if show_labels else "lines+markers",
                name=t.get("tendon", ""),
                text=text,
                textposition="top center",
                hovertemplate="%{fullData.name}<br>x = %{x:.3f} m<br>HorizOff = %{y:.3f} m<extra></extra>",
                line=dict(width=2),
                marker=dict(size=6),
            )
        )
    span = float(model.get("span_m") or 0.0)
    mid = float(model.get("midspan_m") or span / 2.0)
    if span:
        fig.add_vline(x=0, line_dash="dot", line_color="#64748b", annotation_text="Start")
        fig.add_vline(x=mid, line_dash="dash", line_color="#dc2626", annotation_text="Midspan")
        fig.add_vline(x=span, line_dash="dot", line_color="#64748b", annotation_text="End")
    fig.add_hline(y=0, line_dash="dash", line_color="#475569", annotation_text="CL")
    _style_layout(fig, "Tendon plan view — horizontal offset from CL", "Station x (m)", "HorizOff from CL (m)")
    return fig


def tendon_section_overlay_figure(
    section_coords: pd.DataFrame,
    section_props: dict,
    tendon_points: pd.DataFrame,
    *,
    positive_offset_direction: str = "left",
    point_label_mode: str = "family",
    show_point_numbers: bool = True,
    origin_mode: str = "csibridge",
) -> go.Figure:
    from visualization.section_figures import section_polygon_figure

    fig = section_polygon_figure(
        section_coords,
        section_props,
        point_label_mode="major" if show_point_numbers else "hide",
        show_dimensions=True,
        origin_mode=origin_mode,
    )
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
    fig.update_layout(title={"text": "Tendon section overlay at selected station", "x": 0.01, "xanchor": "left"})
    return fig
