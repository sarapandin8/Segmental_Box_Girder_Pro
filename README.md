# Segmental Box Girder Pro — COMMERCIAL.LOADS.17

This baseline carries forward the previously accepted commercial milestones and standards:
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

Display formatting rules:
- Retain the commercial engineering figure system and canvas-card presentation.
- Shared figure helpers remain under `visualization/figure_system.py`.
- New figures must follow the existing UI.1 / UI.2 standards.
- Orthographic Isometric 3D tendon review remains available.

Retained basis / reference notes:
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

Current milestone focus:
- Fix the Wind factor C and deck-height reference card so inline SVG is rendered as a vector figure, not escaped as raw SVG markup.
- Continue to show the Table 2.5 bridge wind-factor reference and lower deck-height `ze` schematic fully inside the Wind Input Assistant.
- Preserve the 3.4 LF / 3.5 HF numbering clarification from LOADS.16.
- Preserve all wind group lookup, V50 / TF / vb0, cdir / cseason, WS / WS+WL, LF/HF, and downstream load calculation logic.

Clean package rule:
- ZIP releases must not include `__pycache__/`, `.pytest_cache/`, `*.pyc`, `*.pyo`, `.streamlit/`, or `.DS_Store`.
