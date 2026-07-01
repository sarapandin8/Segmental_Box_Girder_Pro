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


def u20_loading_diagram_svg() -> str:
    """Report-style SVG schematic for the U20 = 0.8 × LM71 railway live-load figure.
    Uses explicit arrows and dimension chain so it remains stable and crisp in Streamlit.
    """
    return """
<div style='width:100%; background:#ffffff; border:1px solid #d0d5dd; border-radius:12px; padding:18px 18px 10px 18px; box-sizing:border-box;'>
  <div style='font-family:Arial, sans-serif; font-size:18px; font-weight:700; color:#101828; margin-bottom:8px;'>Figure 1.1 U20 train loading diagram (0.8 × LM71) — dimensions in metres</div>
  <svg viewBox='0 0 1120 310' width='100%' height='310' xmlns='http://www.w3.org/2000/svg'>
    <defs>
      <marker id='arrowDown' markerWidth='10' markerHeight='10' refX='5' refY='5' orient='auto' markerUnits='strokeWidth'>
        <path d='M1,1 L9,5 L1,9 z' fill='#111827'/>
      </marker>
      <marker id='arrowDimEnd' markerWidth='8' markerHeight='8' refX='7' refY='4' orient='auto' markerUnits='strokeWidth'>
        <path d='M8,4 L0,0 L0,8 z' fill='#111827'/>
      </marker>
      <marker id='arrowDimStart' markerWidth='8' markerHeight='8' refX='1' refY='4' orient='auto' markerUnits='strokeWidth'>
        <path d='M0,4 L8,0 L8,8 z' fill='#111827'/>
      </marker>
    </defs>

    <!-- note box -->
    <rect x='960' y='10' width='130' height='58' fill='#fff' stroke='#d0d5dd'/>
    <text x='970' y='28' font-size='11' font-family='Arial' fill='#111827' font-weight='700'>U20 basis</text>
    <text x='970' y='42' font-size='10' font-family='Arial' fill='#344054'>0.8 × LM71</text>
    <text x='970' y='55' font-size='10' font-family='Arial' fill='#344054'>4 × 200 kN point loads</text>

    <!-- UDL blocks -->
    <rect x='40' y='122' width='330' height='48' fill='none' stroke='#111827' stroke-width='2'/>
    <rect x='710' y='122' width='330' height='48' fill='none' stroke='#111827' stroke-width='2'/>
    <text x='205' y='109' text-anchor='middle' font-family='Arial' font-size='15' font-weight='700' fill='#111827'>64 kN/m</text>
    <text x='875' y='109' text-anchor='middle' font-family='Arial' font-size='15' font-weight='700' fill='#111827'>64 kN/m</text>

    <!-- track / load line -->
    <line x1='20' y1='188' x2='1060' y2='188' stroke='#111827' stroke-width='2.2'/>

    <!-- point load arrows and labels -->
    <g font-family='Arial' fill='#111827' text-anchor='middle'>
      <line x1='420' y1='76' x2='420' y2='178' stroke='#111827' stroke-width='2'/>
      <polygon points='414,178 426,178 420,188' fill='#111827'/>
      <text x='420' y='60' font-size='13'>200 kN</text>
      <text x='420' y='77' font-size='18' font-weight='700'>P</text>

      <line x1='500' y1='76' x2='500' y2='178' stroke='#111827' stroke-width='2'/>
      <polygon points='494,178 506,178 500,188' fill='#111827'/>
      <text x='500' y='60' font-size='13'>200 kN</text>
      <text x='500' y='77' font-size='18' font-weight='700'>P</text>

      <line x1='580' y1='76' x2='580' y2='178' stroke='#111827' stroke-width='2'/>
      <polygon points='574,178 586,178 580,188' fill='#111827'/>
      <text x='580' y='60' font-size='13'>200 kN</text>
      <text x='580' y='77' font-size='18' font-weight='700'>P</text>

      <line x1='660' y1='76' x2='660' y2='178' stroke='#111827' stroke-width='2'/>
      <polygon points='654,178 666,178 660,188' fill='#111827'/>
      <text x='660' y='60' font-size='13'>200 kN</text>
      <text x='660' y='77' font-size='18' font-weight='700'>P</text>
    </g>

    <!-- extension lines -->
    <g stroke='#475467' stroke-width='1.2'>
      <line x1='40' y1='170' x2='40' y2='208'/>
      <line x1='370' y1='170' x2='370' y2='208'/>
      <line x1='420' y1='188' x2='420' y2='208'/>
      <line x1='500' y1='188' x2='500' y2='208'/>
      <line x1='580' y1='188' x2='580' y2='208'/>
      <line x1='660' y1='188' x2='660' y2='208'/>
      <line x1='710' y1='170' x2='710' y2='208'/>
      <line x1='1040' y1='170' x2='1040' y2='208'/>
    </g>

    <!-- dimension chain -->
    <g stroke='#111827' stroke-width='1.4' fill='none'>
      <line x1='40' y1='210' x2='370' y2='210' marker-start='url(#arrowDimStart)' marker-end='url(#arrowDimEnd)'/>
      <line x1='370' y1='210' x2='420' y2='210' marker-start='url(#arrowDimStart)' marker-end='url(#arrowDimEnd)'/>
      <line x1='420' y1='210' x2='500' y2='210' marker-start='url(#arrowDimStart)' marker-end='url(#arrowDimEnd)'/>
      <line x1='500' y1='210' x2='580' y2='210' marker-start='url(#arrowDimStart)' marker-end='url(#arrowDimEnd)'/>
      <line x1='580' y1='210' x2='660' y2='210' marker-start='url(#arrowDimStart)' marker-end='url(#arrowDimEnd)'/>
      <line x1='660' y1='210' x2='710' y2='210' marker-start='url(#arrowDimStart)' marker-end='url(#arrowDimEnd)'/>
      <line x1='710' y1='210' x2='1040' y2='210' marker-start='url(#arrowDimStart)' marker-end='url(#arrowDimEnd)'/>
    </g>

    <!-- dimension labels -->
    <g font-family='Arial' text-anchor='middle'>
      <text x='205' y='236' font-size='13' font-weight='700' fill='#111827'>NO LIMITATION</text>
      <text x='395' y='236' font-size='13' fill='#111827'>0.80</text>
      <text x='460' y='236' font-size='13' fill='#111827'>1.60</text>
      <text x='540' y='236' font-size='13' fill='#111827'>1.60</text>
      <text x='620' y='236' font-size='13' fill='#111827'>1.60</text>
      <text x='685' y='236' font-size='13' fill='#111827'>0.80</text>
      <text x='875' y='236' font-size='13' font-weight='700' fill='#111827'>NO LIMITATION</text>
    </g>
  </svg>
</div>
"""


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


def rail_horizontal_forces_diagram_svg() -> str:
    """SVG isometric rail schematic showing LF along track and HF normal to track."""
    return """
<div style='width:100%; background:#ffffff; border:1px solid #d0d5dd; border-radius:12px; padding:18px 18px 10px 18px; box-sizing:border-box;'>
  <div style='font-family:Arial, sans-serif; font-size:18px; font-weight:700; color:#101828; margin-bottom:8px;'>Figure 1.2 Rail horizontal actions — LF along track axis and HF normal to track</div>
  <svg viewBox='0 0 1120 360' width='100%' height='360' xmlns='http://www.w3.org/2000/svg'>
    <defs>
      <linearGradient id='railGrad' x1='0' y1='0' x2='1' y2='1'>
        <stop offset='0%' stop-color='#aeb4bc'/>
        <stop offset='50%' stop-color='#e5e7eb'/>
        <stop offset='100%' stop-color='#7f8791'/>
      </linearGradient>
      <marker id='arrowBlue' markerWidth='10' markerHeight='10' refX='8' refY='5' orient='auto' markerUnits='strokeWidth'>
        <path d='M0,0 L10,5 L0,10 z' fill='#175cd3'/>
      </marker>
      <marker id='arrowOrange' markerWidth='10' markerHeight='10' refX='8' refY='5' orient='auto' markerUnits='strokeWidth'>
        <path d='M0,0 L10,5 L0,10 z' fill='#c2410c'/>
      </marker>
      <filter id='shadow' x='-20%' y='-20%' width='140%' height='140%'>
        <feDropShadow dx='0.8' dy='1.2' stdDeviation='1.2' flood-color='#000000' flood-opacity='0.15'/>
      </filter>
    </defs>

    <!-- light note box -->
    <rect x='902' y='18' width='190' height='70' fill='#fff' stroke='#d0d5dd'/>
    <text x='914' y='36' font-size='12' font-family='Arial' fill='#111827' font-weight='700'>Action interpretation</text>
    <text x='914' y='54' font-size='11' font-family='Arial' fill='#344054'>LF = longitudinal force along x</text>
    <text x='914' y='69' font-size='11' font-family='Arial' fill='#344054'>HF = Qsk hunting/nosing force</text>
    <text x='914' y='84' font-size='11' font-family='Arial' fill='#344054'>HF acts normal to track (y)</text>

    <!-- isometric track body -->
    <g filter='url(#shadow)'>
      <!-- sleepers -->
      <g fill='#d9d4cb' stroke='#c1baaf' stroke-width='0.6'>
        <polygon points='120,88 154,105 140,127 106,110'/>
        <polygon points='170,100 204,117 190,139 156,122'/>
        <polygon points='220,112 254,129 240,151 206,134'/>
        <polygon points='270,124 304,141 290,163 256,146'/>
        <polygon points='320,136 354,153 340,175 306,158'/>
        <polygon points='370,148 404,165 390,187 356,170'/>
        <polygon points='420,160 454,177 440,199 406,182'/>
        <polygon points='470,172 504,189 490,211 456,194'/>
        <polygon points='520,184 554,201 540,223 506,206'/>
        <polygon points='570,196 604,213 590,235 556,218'/>
        <polygon points='620,208 654,225 640,247 606,230'/>
        <polygon points='670,220 704,237 690,259 656,242'/>
        <polygon points='720,232 754,249 740,271 706,254'/>
        <polygon points='770,244 804,261 790,283 756,266'/>
        <polygon points='820,256 854,273 840,295 806,278'/>
        <polygon points='870,268 904,285 890,307 856,290'/>
      </g>

      <!-- rails -->
      <g stroke='url(#railGrad)' stroke-width='7' stroke-linecap='round'>
        <line x1='108' y1='82' x2='904' y2='272'/>
        <line x1='148' y1='58' x2='944' y2='248'/>
      </g>
      <g stroke='#7f8791' stroke-width='1.4' opacity='0.9'>
        <line x1='108' y1='88' x2='904' y2='278'/>
        <line x1='148' y1='64' x2='944' y2='254'/>
      </g>

      <!-- fasteners hint -->
      <g fill='#b9aca6' stroke='#8f857e' stroke-width='0.5'>
        <circle cx='165' cy='78' r='3'/><circle cx='205' cy='88' r='3'/><circle cx='245' cy='98' r='3'/><circle cx='285' cy='108' r='3'/><circle cx='325' cy='118' r='3'/><circle cx='365' cy='128' r='3'/><circle cx='405' cy='138' r='3'/><circle cx='445' cy='148' r='3'/><circle cx='485' cy='158' r='3'/><circle cx='525' cy='168' r='3'/><circle cx='565' cy='178' r='3'/><circle cx='605' cy='188' r='3'/><circle cx='645' cy='198' r='3'/><circle cx='685' cy='208' r='3'/><circle cx='725' cy='218' r='3'/><circle cx='765' cy='228' r='3'/><circle cx='805' cy='238' r='3'/><circle cx='845' cy='248' r='3'/>
        <circle cx='125' cy='102' r='3'/><circle cx='165' cy='112' r='3'/><circle cx='205' cy='122' r='3'/><circle cx='245' cy='132' r='3'/><circle cx='285' cy='142' r='3'/><circle cx='325' cy='152' r='3'/><circle cx='365' cy='162' r='3'/><circle cx='405' cy='172' r='3'/><circle cx='445' cy='182' r='3'/><circle cx='485' cy='192' r='3'/><circle cx='525' cy='202' r='3'/><circle cx='565' cy='212' r='3'/><circle cx='605' cy='222' r='3'/><circle cx='645' cy='232' r='3'/><circle cx='685' cy='242' r='3'/><circle cx='725' cy='252' r='3'/><circle cx='765' cy='262' r='3'/><circle cx='805' cy='272' r='3'/>
      </g>
    </g>

    <!-- action arrows -->
    <line x1='445' y1='112' x2='680' y2='168' stroke='#175cd3' stroke-width='6' marker-end='url(#arrowBlue)'/>
    <text x='514' y='108' font-size='18' font-family='Arial' fill='#175cd3' font-weight='700'>LF</text>
    <text x='480' y='94' font-size='12' font-family='Arial' fill='#344054'>Longitudinal force</text>
    <text x='488' y='79' font-size='12' font-family='Arial' fill='#344054'>along track / bridge axis (x)</text>

    <line x1='572' y1='156' x2='528' y2='82' stroke='#c2410c' stroke-width='6' marker-end='url(#arrowOrange)'/>
    <text x='492' y='84' font-size='18' font-family='Arial' fill='#c2410c' font-weight='700'>HF</text>
    <text x='622' y='108' font-size='12' font-family='Arial' fill='#344054'>HF = Qsk hunting / nosing force</text>
    <text x='622' y='123' font-size='12' font-family='Arial' fill='#344054'>Normal to track (y)</text>

    <!-- local axes -->
    <g>
      <line x1='130' y1='282' x2='195' y2='297' stroke='#475467' stroke-width='2.5' marker-end='url(#arrowBlue)'/>
      <line x1='130' y1='282' x2='97' y2='226' stroke='#475467' stroke-width='2.5' marker-end='url(#arrowOrange)'/>
      <text x='203' y='303' font-size='13' font-family='Arial' fill='#175cd3' font-weight='700'>x</text>
      <text x='86' y='222' font-size='13' font-family='Arial' fill='#c2410c' font-weight='700'>y</text>
      <text x='130' y='320' font-size='11' font-family='Arial' fill='#667085'>Local action axes at rail level</text>
    </g>

    <!-- small labels -->
    <text x='715' y='286' font-size='11' font-family='Arial' fill='#667085'>rail level</text>
    <text x='756' y='298' font-size='11' font-family='Arial' fill='#667085'>bridge / track axis</text>
  </svg>
</div>
"""


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
