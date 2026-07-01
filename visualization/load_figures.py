from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from visualization.figure_system import PLOTLY_CONFIG, apply_engineering_figure_layout


def apply_engineering_layout(fig: go.Figure, title: str, x_title: str = "", y_title: str = "") -> go.Figure:
    """Backward-compatible wrapper for the global engineering figure system."""
    return apply_engineering_figure_layout(fig, title=title, x_title=x_title, y_title=y_title, height=520)


def u20_loading_diagram() -> go.Figure:
    fig = go.Figure()

    axle_load_kn = 200
    udl_knpm = 64
    axle_x = [0.8, 2.4, 4.0, 5.6]
    baseline_y = 0.0
    udl_y0 = 0.10
    udl_y1 = 0.48
    dim_y = -0.18

    # baseline / rail level
    fig.add_shape(type="line", x0=-6.8, x1=13.2, y0=baseline_y, y1=baseline_y, line=dict(color="#475467", width=2.6))
    fig.add_annotation(x=12.95, y=0.05, text="rail / load line", showarrow=False, xanchor="right", font=dict(size=11, color="#667085"), bgcolor="rgba(255,255,255,0.92)")

    # UDL blocks (0.8 x LM71)
    udl_fill = "rgba(23,92,211,0.10)"
    udl_line = dict(color="#175cd3", width=2.2)
    for x0, x1 in [(-6.4, 0.0), (6.4, 12.8)]:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=udl_y0, y1=udl_y1, line=udl_line, fillcolor=udl_fill)
        fig.add_annotation(x=(x0 + x1) / 2, y=0.61, text=f"UDL = {udl_knpm} kN/m", showarrow=False, font=dict(size=13, color="#092454"), bordercolor="#bfd4f2", borderwidth=1, bgcolor="rgba(255,255,255,0.96)", borderpad=4)
    fig.add_annotation(x=-3.2, y=-0.30, text="No limitation", showarrow=False, font=dict(size=12, color="#667085"))
    fig.add_annotation(x=9.6, y=-0.30, text="No limitation", showarrow=False, font=dict(size=12, color="#667085"))

    # axle loads with clear arrows and labels
    for i, x in enumerate(axle_x, start=1):
        fig.add_annotation(x=x, y=1.32, ax=x, ay=0.56, text=f"P{i}", showarrow=True, arrowhead=3, arrowsize=1.15, arrowwidth=2.2, arrowcolor="#0f172a", font=dict(size=13, color="#092454", family="Arial"))
        fig.add_annotation(x=x, y=1.40, text=f"{axle_load_kn} kN", showarrow=False, font=dict(size=11, color="#0f172a"), bgcolor="rgba(255,255,255,0.94)")
        fig.add_shape(type="circle", x0=x-0.06, x1=x+0.06, y0=0.50, y1=0.62, line=dict(color="#0f172a", width=1.6), fillcolor="#ffffff")

    fig.add_annotation(x=3.2, y=1.60, text="4 concentrated axle loads = 0.8 × 250 = 200 kN each", showarrow=False, font=dict(size=12, color="#344054"), bgcolor="rgba(255,255,255,0.95)", bordercolor="#d0d5dd", borderwidth=1, borderpad=4)

    # dimension chain below axle train
    dim_points = [0.0, 0.8, 2.4, 4.0, 5.6, 6.4]
    for x in dim_points:
        fig.add_shape(type="line", x0=x, x1=x, y0=baseline_y - 0.03, y1=baseline_y + 0.03, line=dict(color="#667085", width=1.3))
        fig.add_shape(type="line", x0=x, x1=x, y0=baseline_y, y1=dim_y + 0.03, line=dict(color="#98a2b3", width=1))

    for x0, x1, label in [(0.0, 0.8, "0.80"), (0.8, 2.4, "1.60"), (2.4, 4.0, "1.60"), (4.0, 5.6, "1.60"), (5.6, 6.4, "0.80")]:
        fig.add_annotation(x=x0, y=dim_y, ax=x1, ay=dim_y, text="", showarrow=True, arrowhead=2, startarrowhead=2, arrowsize=1, arrowwidth=1.4, arrowcolor="#667085")
        fig.add_annotation(x=(x0 + x1) / 2, y=dim_y - 0.06, text=label, showarrow=False, font=dict(size=12, color="#344054"), bgcolor="rgba(255,255,255,0.95)")

    # group width note and key summary note
    fig.add_annotation(x=3.2, y=dim_y - 0.22, text="Loaded axle train length = 6.40 m", showarrow=False, font=dict(size=12, color="#092454"), bgcolor="rgba(232,242,255,0.96)", bordercolor="#bfd4f2", borderwidth=1, borderpad=4)
    fig.add_annotation(x=12.75, y=1.60, xanchor="right", align="left", text="<b>U20 basis</b><br>0.8 × LM71<br>4 × 200 kN axle loads<br>UDL = 64 kN/m on both sides", showarrow=False, font=dict(size=11, color="#344054"), bgcolor="rgba(255,255,255,0.96)", bordercolor="#d0d5dd", borderwidth=1, borderpad=5)

    apply_engineering_figure_layout(fig, title="Figure 1.1 U20 train loading diagram (0.8 × LM71) — dimensions in metres", height=560, showlegend=False)
    fig.update_yaxes(visible=False, range=[-0.55, 1.78], showgrid=False, zeroline=False)
    fig.update_xaxes(visible=False, range=[-7.0, 13.5], showgrid=False, zeroline=False)
    return fig


def rail_horizontal_forces_diagram() -> go.Figure:
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, x1=40, y0=-0.25, y1=0.25, line=dict(color="#0b3b91"), fillcolor="rgba(23,92,211,0.08)")
    fig.add_annotation(x=20, y=0.45, text="Rail level / bridge axis", showarrow=False, bgcolor="rgba(255,255,255,0.92)")
    fig.add_annotation(x=8, y=0.0, ax=2, ay=0.0, text="LF", showarrow=True, arrowhead=3, arrowwidth=3, arrowcolor="#175cd3", font=dict(color="#175cd3", size=14))
    fig.add_annotation(x=24, y=1.2, ax=24, ay=0.28, text="HF = Qsk", showarrow=True, arrowhead=3, arrowwidth=3, arrowcolor="#b54708", font=dict(color="#b54708", size=14))
    fig.add_annotation(x=7, y=-0.55, text="Longitudinal force along bridge axis", showarrow=False, font=dict(size=12, color="#334155"), bgcolor="rgba(255,255,255,0.92)")
    fig.add_annotation(x=26, y=1.42, text="Hunting/nosing force normal to track", showarrow=False, font=dict(size=12, color="#334155"), bgcolor="rgba(255,255,255,0.92)")
    apply_engineering_figure_layout(fig, title="Rail horizontal actions — LF and HF application at rail level", x_title="x along bridge (m)", y_title="Transverse schematic", height=500, showlegend=False)
    fig.update_xaxes(range=[-2, 42])
    fig.update_yaxes(range=[-1, 1.65], showgrid=False, zeroline=False)
    return fig


def wind_bridge_direction_diagram() -> go.Figure:
    fig = go.Figure()
    x = [0, 40, 43, 3, 0]
    y = [0, 2, 3, 1, 0]
    fig.add_trace(go.Scatter(x=x, y=y, fill="toself", mode="lines", name="Deck plan / exposed length", line=dict(width=2, color="#294860"), fillcolor="rgba(90,124,155,0.18)"))
    fig.add_annotation(x=-4, y=1.4, ax=-9, ay=1.4, text="Wind", showarrow=True, arrowhead=3, arrowwidth=3, arrowcolor="#175cd3", font=dict(color="#175cd3"))
    fig.add_annotation(x=20, y=2.8, text="L", showarrow=False, bgcolor="rgba(255,255,255,0.92)")
    fig.add_annotation(x=41.5, y=3.2, text="b", showarrow=False, bgcolor="rgba(255,255,255,0.92)")
    apply_engineering_figure_layout(fig, title="Wind load directions on bridge — EN 1991-1-4 Fig. 8.2 style schematic", height=500, showlegend=True, equal_axis=True)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def response_spectrum_figure(points: pd.DataFrame, T: float, Sa: float, title: str = "DPT design response spectrum") -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=points["T (s)"], y=points["Sa (g)"], mode="lines", name="Sa(T)", hovertemplate="T=%{x:.3f}s<br>Sa=%{y:.4f}g", line=dict(width=2.4, color="#175cd3")))
    fig.add_trace(go.Scatter(x=[T], y=[Sa], mode="markers+text", text=[f"T={T:.3f}s<br>Sa={Sa:.4f}g"], textposition="top center", name="Input period", marker=dict(size=10, color="#be123c", line=dict(width=1.2, color="#0f172a"))))
    return apply_engineering_figure_layout(fig, title=title, x_title="Period T (s)", y_title="Spectral acceleration Sa (g)", height=520)
