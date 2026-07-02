# Segmental Box Girder Pro — COMMERCIAL.LOADS.26

This baseline carries forward the accepted commercial milestones and standards:
- COMMERCIAL.M3H.8
- COMMERCIAL.M3H.9
- COMMERCIAL.M3H.10
- COMMERCIAL.M3H.11
- COMMERCIAL.UI.1
- COMMERCIAL.UI.2
- COMMERCIAL.M4.1A
- COMMERCIAL.M4.1B
- COMMERCIAL.M4.1C
- COMMERCIAL.M4.1D
- COMMERCIAL.M4.1E
- COMMERCIAL.CODE.1
- COMMERCIAL.LOADS.1
- COMMERCIAL.LOADS.2
- COMMERCIAL.LOADS.3
- COMMERCIAL.LOADS.4
- COMMERCIAL.LOADS.5
- COMMERCIAL.LOADS.6
- COMMERCIAL.LOADS.7
- COMMERCIAL.LOADS.8
- COMMERCIAL.LOADS.9
- COMMERCIAL.LOADS.10
- COMMERCIAL.LOADS.11
- COMMERCIAL.LOADS.12
- COMMERCIAL.LOADS.13
- COMMERCIAL.LOADS.14
- COMMERCIAL.LOADS.15
- COMMERCIAL.LOADS.16
- COMMERCIAL.LOADS.17
- COMMERCIAL.LOADS.24
- COMMERCIAL.LOADS.25
- COMMERCIAL.LOADS.26

Display formatting rules
- Retain the commercial engineering figure system and canvas-card presentation.
- Shared figure helpers remain under `visualization/figure_system.py`.
- New figures must follow the existing UI.1 / UI.2 standards.
- One-source UI mode applies to Plotly figures, SVG components, source panels, and report-ready cards.

Retained basis / reference notes
- 1.3.7 Wind Load
- EN 1991-1-4
- Table 2.5
- DPT seismic database
- Bangkok Basin Zone 1–10
- AASHTO LRFD 2014 Table 3.10.7.1-1
- Full station-by-station FEA import remains pending
- Coordinate-driven section properties
- AASHTO LRFD Bridge Design Specifications, 9th Edition, 2020
- Structural Polygon 1
- Opening Polygon 1
- Orthographic Isometric

Current milestone focus
- Add explicit Single Track / Double Track selection for the 3.2 SDL page.
- Use the selected track configuration to control the SDL value sent to the FEA input summary.
- Keep both single-track and double-track component totals/adopted values visible and editable for report traceability.
- Preserve existing SDL component table logic and downstream load calculation behavior.

Clean release rule
- ZIP packages must not include `__pycache__/`, `.pytest_cache/`, `*.pyc`, `*.pyo`, `.streamlit/`, or `.DS_Store`.


Current milestone focus:
- Replace the grayscale/contrast-enhanced DPT wind map card asset with the user-approved clean color reference map.
- Keep province lookup as the authoritative adopted wind-group source.

- Replace the simplified lower z_e schematic in the wind factor C reference card with the user-provided four-pier bridge SVG reference.

- Split the wind factor C / z_e mixed reference into a compact Table 2.5 card plus a separate z_e bridge-profile card so the figure fits comfortably in the UI.

- Compact the separate z_e bridge-profile card using an embedded SVG image constrained to a fixed card height so the editable wind parameter table remains close to the input assistant.

- Remove duplicate right-side report images from the EN Factors tab; the tab now shows only the formula, Table 2.5 data, interpolation results, and a note that figures remain in Input Assistant cards.

- Polish the Wind Calculations tab with result cards, explicit q = 0.5ρvb² velocity pressure, and Pa→N→kN unit trace using Fw = q·C·Aref/1000.

- Replace the WS/WL wind application model card image with the user-provided refined bridge/train figure and enlarge the display height for better readability.

- Replace the bridge wind-direction reference card image with the user-provided refined EN Figure 8.2 style sketch and enlarge the display height for readability.
