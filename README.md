# Segmental Box Girder Pro — COMMERCIAL.LOADS.37

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
- COMMERCIAL.LOADS.27
- COMMERCIAL.LOADS.28
- COMMERCIAL.LOADS.29
- COMMERCIAL.LOADS.30
- COMMERCIAL.LOADS.31
- COMMERCIAL.LOADS.32
- COMMERCIAL.LOADS.33
- COMMERCIAL.LOADS.34
- COMMERCIAL.LOADS.35
- COMMERCIAL.LOADS.36
- COMMERCIAL.LOADS.37
- COMMERCIAL.LOADS.38

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
- AASHTO LRFD 2020 Table 3.10.7.1-1
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

- Clarify the WS/WL wind application figure note so V is explicitly identified as an associated vertical reference effect, not wind velocity.

- Upgrade the 3.6 CF page from a factor-only calculator to a code-assisted input assistant with curvature condition, f/C result cards, explicit EN unit trace, project threshold, and FEA adoption status.

- Simplify CF track alignment condition to two modes: straight track/no horizontal curve and curved track/finite radius; large-radius cases are treated as finite-radius curved track with small-result assessment.

- Simplify CF alignment UI to two meaningful modes: Straight track / no horizontal curve and Curved track / finite radius, migrating old large-radius values into the finite-radius curved-track calculation.

- Split CF engineering assessment from FEA adoption status so threshold compliance remains visible even when CF is reported as factor-only/not adopted.

- COMMERCIAL.LOADS.32: Polished straight-track CF mode by hiding finite-radius inputs, threshold, FEA adoption checkbox, and Adopt span as Lf controls when straight track is selected; result cards and zero-force FEA trace remain visible.

- COMMERCIAL.LOADS.33: Upgraded 3.8 CR&SH to a minimal-input assistant with RH/age/drying-basis inputs, geometry-derived u_total, V/S and h0 trace, AASHTO unit conversion preview, and Prestress Losses handoff panel.

- COMMERCIAL.LOADS.34: Added CR&SH drying perimeter basis guidance for outer-only versus outer-plus-inner-void drying surfaces and displayed final design age in years while preserving existing derived-geometry and Prestress Losses handoff logic.

- COMMERCIAL.LOADS.35: Added EQ result summary cards, one-source trace, and FEA adoption panel for Cs/EQX/EQY coefficient export while updating bridge R-factor wording to AASHTO LRFD 9th Edition (2020).

- COMMERCIAL.LOADS.36: Polished EQ schema/status display, clarified coefficient-trace FEA adoption and numeric-force ownership, and wrapped the DPT response spectrum in a report-ready canvas figure without changing EQ formulas.

- COMMERCIAL.LOADS.37: Renamed 3.10 to FEA Load Input Summary and upgraded the page into a source-of-truth load handoff table for DL, SDL, LL+IM, LF/HF, CF, Wind, EQ coefficient trace, and CR&SH parameters.


- COMMERCIAL.LOADS.38: Polished 3.10 FEA Load Input Summary as a wrapped commercial handoff sheet with HANDOFF READY status, compact adopted value/basis wording, explicit quantity types, and row-level required FEA actions without changing load formulas.
