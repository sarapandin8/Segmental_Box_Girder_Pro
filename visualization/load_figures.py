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
    track_y = 0.0
    udl_y0 = 0.12
    udl_y1 = 0.46
    dim_y = -0.16
    scheme_color = "#111827"
    label_color = "#0f172a"
    muted = "#475467"

    # Track / load line
    fig.add_shape(type="line", x0=-6.8, x1=13.2, y0=track_y, y1=track_y, line=dict(color=scheme_color, width=2.6))

    # UDL blocks
    for x0, x1 in [(-6.4, 0.0), (6.4, 12.8)]:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=udl_y0, y1=udl_y1, line=dict(color=scheme_color, width=1.8), fillcolor="rgba(17,24,39,0.03)")
        fig.add_annotation(x=(x0+x1)/2, y=0.57, text=f"{udl_knpm} kN/m", showarrow=False, font=dict(size=14, color=label_color, family="Arial Black"))

    # Point loads as vertical arrows (report-style)
    arrow_top = 1.14
    arrow_tip = 0.50
    for x in axle_x:
        fig.add_annotation(x=x, y=arrow_top, ax=x, ay=arrow_tip, text="P", showarrow=True, arrowhead=3, arrowsize=1.0, arrowwidth=1.9, arrowcolor=scheme_color, font=dict(size=15, color=label_color, family="Arial Black"))
        fig.add_annotation(x=x, y=1.25, text=f"{axle_load_kn} kN", showarrow=False, font=dict(size=11, color=muted), bgcolor="rgba(255,255,255,0.85)")

    # Extension lines from track to dimension chain
    chain_points = [-6.4, 0.0, 0.8, 2.4, 4.0, 5.6, 6.4, 12.8]
    for x in chain_points:
        top = track_y if x not in (-6.4, 12.8) else udl_y0
        fig.add_shape(type="line", x0=x, x1=x, y0=top, y1=dim_y+0.02, line=dict(color=muted, width=1.1))

    # Dimension chain segments with double arrows
    segments = [(-6.4, 0.0, "NO LIMITATION"), (0.0, 0.8, "0.80"), (0.8, 2.4, "1.60"), (2.4, 4.0, "1.60"), (4.0, 5.6, "1.60"), (5.6, 6.4, "0.80"), (6.4, 12.8, "NO LIMITATION")]
    for x0, x1, txt in segments:
        fig.add_annotation(x=x0, y=dim_y, ax=x1, ay=dim_y, text="", showarrow=True, arrowhead=2, startarrowhead=2, arrowsize=0.95, arrowwidth=1.4, arrowcolor=scheme_color)
        fig.add_annotation(x=(x0+x1)/2, y=dim_y-0.09, text=txt, showarrow=False, font=dict(size=12 if txt.replace('.', '').isdigit() else 13, color=label_color if txt.replace('.', '').isdigit() else scheme_color, family="Arial Black" if 'NO' in txt else "Arial"), bgcolor="rgba(255,255,255,0.92)")

    # Small tie line at dimension chain level for continuity impression
    fig.add_shape(type="line", x0=-6.4, x1=12.8, y0=dim_y, y1=dim_y, line=dict(color="rgba(0,0,0,0)", width=1))

    # Key load model note — compact and non-dominant
    fig.add_annotation(x=12.85, y=1.36, xanchor="right", align="left", text="<b>U20 basis</b><br>0.8 × LM71<br>4 × 200 kN point loads", showarrow=False, font=dict(size=11, color="#344054"), bgcolor="rgba(255,255,255,0.94)", bordercolor="#d0d5dd", borderwidth=1, borderpad=4)

    apply_engineering_figure_layout(fig, title="Figure 1.1 U20 train loading diagram (0.8 × LM71) — dimensions in metres", height=500, showlegend=False)
    fig.update_yaxes(visible=False, range=[-0.42, 1.45], showgrid=False, zeroline=False)
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
