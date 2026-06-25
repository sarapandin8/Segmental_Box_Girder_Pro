from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

PLOTLY_SECTION_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}


def _closed_xy(g: pd.DataFrame) -> tuple[list[float], list[float]]:
    xs = g["x_mm"].astype(float).tolist()
    ys = g["y_mm"].astype(float).tolist()
    if xs and ys and (xs[0] != xs[-1] or ys[0] != ys[-1]):
        xs.append(xs[0])
        ys.append(ys[0])
    return xs, ys


def section_polygon_figure(coords: pd.DataFrame, props: dict, *, show_points: bool = True, show_dimensions: bool = True) -> go.Figure:
    fig = go.Figure()
    if coords is None or coords.empty:
        fig.update_layout(title="No section coordinates loaded")
        return fig

    # Outer loops first, then holes.
    for loop_name, g in coords.groupby("loop_name", sort=False):
        loop_type = str(g["loop_type"].iloc[0]) if "loop_type" in g else "unknown"
        xs, ys = _closed_xy(g)
        fill = "toself" if loop_type == "outer" else "toself"
        fillcolor = "rgba(90, 124, 155, 0.28)" if loop_type == "outer" else "rgba(255, 255, 255, 0.96)"
        linecolor = "#294860" if loop_type == "outer" else "#294860"
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines+markers" if show_points else "lines",
                fill=fill,
                fillcolor=fillcolor,
                line=dict(color=linecolor, width=2.5),
                marker=dict(size=6),
                name=str(loop_name),
                hovertemplate="%{x:.0f}, %{y:.0f} mm<extra>" + str(loop_name) + "</extra>",
            )
        )
        if show_points:
            fig.add_trace(
                go.Scatter(
                    x=g["x_mm"],
                    y=g["y_mm"],
                    mode="text",
                    text=g["point_no"].astype(str),
                    textposition="top center",
                    textfont=dict(size=10, color="#7c2d12"),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    if props.get("valid"):
        cx = props["cx_mm"]
        cy = props["cy_mm"]
        fig.add_trace(
            go.Scatter(
                x=[cx],
                y=[cy],
                mode="markers+text",
                text=["Centroid"],
                textposition="top center",
                marker=dict(size=12, symbol="cross", color="#be123c"),
                name="Centroid",
                hovertemplate="Centroid<br>x=%{x:.1f} mm<br>y=%{y:.1f} mm<extra></extra>",
            )
        )
        b = props.get("bounds_mm", {})
        xmin, xmax, ymin, ymax = b.get("xmin"), b.get("xmax"), b.get("ymin"), b.get("ymax")
        if show_dimensions and None not in {xmin, xmax, ymin, ymax}:
            y_dim = ymax + max(150.0, 0.10 * (ymax - ymin))
            x_dim = xmin - max(150.0, 0.04 * (xmax - xmin))
            fig.add_annotation(x=(xmin + xmax) / 2, y=y_dim, text=f"B = {(xmax - xmin):.0f} mm", showarrow=False, font=dict(color="#9a3412", size=12))
            fig.add_shape(type="line", x0=xmin, y0=y_dim - 55, x1=xmax, y1=y_dim - 55, line=dict(color="#c2410c", width=1.5))
            fig.add_annotation(x=x_dim, y=(ymin + ymax) / 2, text=f"D = {(ymax - ymin):.0f} mm", textangle=-90, showarrow=False, font=dict(color="#9a3412", size=12))
            fig.add_shape(type="line", x0=x_dim + 55, y0=ymin, x1=x_dim + 55, y1=ymax, line=dict(color="#c2410c", width=1.5))
            fig.add_shape(type="line", x0=xmin, y0=cy, x1=xmax, y1=cy, line=dict(color="#be123c", width=1, dash="dot"))
            fig.add_shape(type="line", x0=cx, y0=ymin, x1=cx, y1=ymax, line=dict(color="#be123c", width=1, dash="dot"))
            fig.add_annotation(x=cx, y=ymin, text=f"y_cg = {props['ycg_from_bottom_m']*1000:.0f} mm", showarrow=True, arrowhead=2, ax=55, ay=-35, font=dict(color="#9a3412", size=11))
            fig.add_annotation(x=cx, y=ymax, text=f"y_t = {props['yt_from_top_m']*1000:.0f} mm", showarrow=True, arrowhead=2, ax=55, ay=35, font=dict(color="#9a3412", size=11))

    fig.update_layout(
        height=540,
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(title="x (mm)", showgrid=True, gridcolor="#e5e7eb", zeroline=True, zerolinecolor="#94a3b8"),
        yaxis=dict(title="y (mm)", showgrid=True, gridcolor="#e5e7eb", zeroline=True, zerolinecolor="#94a3b8", scaleanchor="x", scaleratio=1),
    )
    return fig
