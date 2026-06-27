from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from visualization.figure_system import PLOTLY_CONFIG, apply_engineering_figure_layout


def apply_engineering_layout(fig: go.Figure, title: str, x_title: str = "", y_title: str = "") -> go.Figure:
    """Backward-compatible wrapper for the global engineering figure system."""
    return apply_engineering_figure_layout(fig, title=title, x_title=x_title, y_title=y_title, height=520)


def u20_loading_diagram() -> go.Figure:
    fig = go.Figure()
    # distributed loads
    fig.add_shape(type="rect", x0=-6.4, x1=0.0, y0=0.08, y1=0.45, line=dict(color="#0b3b91"), fillcolor="rgba(23,92,211,0.08)")
    fig.add_shape(type="rect", x0=6.4, x1=12.8, y0=0.08, y1=0.45, line=dict(color="#0b3b91"), fillcolor="rgba(23,92,211,0.08)")
    fig.add_annotation(x=-3.2, y=0.57, text="64 kN/m", showarrow=False, font=dict(size=13, color="#092454"), bgcolor="rgba(255,255,255,0.92)")
    fig.add_annotation(x=9.6, y=0.57, text="64 kN/m", showarrow=False, font=dict(size=13, color="#092454"), bgcolor="rgba(255,255,255,0.92)")
    # axle loads and dimensions
    axles = [0.8, 2.4, 4.0, 5.6]
    for x in axles:
        fig.add_annotation(x=x, y=1.25, ax=x, ay=0.52, text="P", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="#0f172a", font=dict(color="#092454"))
    fig.add_shape(type="line", x0=-6.8, x1=13.2, y0=0, y1=0, line=dict(color="#0f172a", width=2))
    for x in [0, 0.8, 2.4, 4.0, 5.6, 6.4]:
        fig.add_shape(type="line", x0=x, x1=x, y0=-0.06, y1=0.06, line=dict(color="#0f172a", width=1))
    for x, txt in [(0.4, "0.80"), (1.6, "1.60"), (3.2, "1.60"), (4.8, "1.60"), (6.0, "0.80")]:
        fig.add_annotation(x=x, y=-0.18, text=txt, showarrow=False, font=dict(size=12, color="#334155"))
    fig.add_annotation(x=-3.2, y=-0.18, text="No limitation", showarrow=False, font=dict(size=12, color="#334155"))
    fig.add_annotation(x=9.6, y=-0.18, text="No limitation", showarrow=False, font=dict(size=12, color="#334155"))
    apply_engineering_figure_layout(fig, title="Figure 1.1 U20 train loading diagram (0.8 × LM71) — dimensions in metres", height=500, showlegend=False)
    fig.update_yaxes(visible=False, range=[-0.35, 1.45])
    fig.update_xaxes(visible=False, range=[-7, 13.5])
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
