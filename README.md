# Segmental Box Girder Pro — COMMERCIAL.PSLOSS.22

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


- COMMERCIAL.LOADS.39: Added a FEA handoff status legend, transfer-control checklist, and print-safe handoff styling for 3.10 FEA Load Input Summary without changing load formulas.

- COMMERCIAL.LOADS.40: Closed the Loads workspace for the current load-source scope by adding a Loads closeout and Report/QA handoff panel to 3.10 FEA Load Input Summary, surfacing the same read-only Loads handoff snapshot in Report / QA, and preserving all load formulas.


- COMMERCIAL.PSLOSS.1: Added a source-gated Prestress Losses input handoff that reads locked adopted tendon data, adopted section properties, CR&SH parameters, and span/stage basis before detailed loss calculation; clarified that jacking force is tendon axial force and must not be doubled for two-end stressing.

- COMMERCIAL.PSLOSS.2: Added a tendon-adoption action panel, blocked prestress-input checklist, and explicit JackFrom / stressing-basis gate so future friction and anchor-set losses can distinguish one-end, two-end, mixed, or missing stressing traces without doubling total jacking force.


- COMMERCIAL.PSLOSS.3: Added an adopted-tendon readiness register, loss-component calculation-readiness register, and Report/QA readiness snapshot so future friction, anchor-set, elastic-shortening, creep/shrinkage, relaxation, and effective-prestress formulas remain source-gated before calculation.

- COMMERCIAL.PSLOSS.4: Reworked 4.2 Friction into a source-gated friction source model that reads only the adopted tendon profile and JackFrom/stressing trace, adds μ/K input trace and tendon-by-tendon preview gating, and keeps preview results out of final effective-prestress adoption.

- COMMERCIAL.TENDON.1: Polish 2.4 Tendon Layout Reference with JackFrom/stressing-basis auto-detection, force-policy trace, QA/adoption readiness rows, and a numeric section-overlay station control to avoid slider dynamic-import instability, without changing tendon geometry or force calculations.
- COMMERCIAL.TENDON.2: Add an explicit visible source note that the stressing basis is auto-detected from the General tendon table · JackFrom field, keeping it as a traced tendon-source value rather than a duplicate Prestress Losses input.

- COMMERCIAL.PSLOSS.5: Add friction formula trace and report-style calculation summary to 4.2 Friction, including variable definitions, governing-tendon walkthrough, tendon-by-tendon Kx/μα/exponent/ΔfpF/fpx trace, and Report/QA snapshot without adopting friction into effective prestress.
- COMMERCIAL.PSLOSS.6: Standardized 4.2 Friction with report-grade equation blocks using `st.latex`, a reusable loss-type result-summary card pattern at the top of the page, and source-gated substitution/result display without changing friction values or effective-prestress adoption.

- COMMERCIAL.PSLOSS.7: Polishes 4.2 Friction report trace by showing governing-tendon ties (for mirrored tendons with equal loss), adding full-tendon row-count notes and display height for tendon-by-tendon report tables, and keeping the PSLOSS.6 equation/summary pattern unchanged for future loss pages.


- COMMERCIAL.PSLOSS.9: Adds a position-dependent 4.3 Anchor Set distribution trace and friction-coupling preview while preserving equivalent anchor-set quick check and keeping final effective-prestress adoption blocked.


- COMMERCIAL.PSLOSS.10: Polishes 4.3 Anchor Set distribution wording and variable trace by separating the equivalent quick check from the position-dependent friction-coupled preview, documenting 2ΔfpF(s), ΔfpA,0, s_a, fpx,F+A(s), and the 1000 m-to-mm compatibility conversion without changing anchor-set results or effective-prestress adoption.

- COMMERCIAL.PSLOSS.11: Adds a source-gated 4.4 Elastic Shortening stage preview using adopted tendon count, Ep/Eci material source, engineer-reviewed f_cgp stage input, report-grade equation blocks, loss-summary cards, variable trace, and tendon-by-tendon sequence audit without adopting elastic shortening into final effective prestress.

- COMMERCIAL.PSLOSS.12: Polishes 4.4 Elastic Shortening summary consistency by separating average ES loss, fpx after average ES, maximum sequence ES loss, and minimum sequence stress; adds sequence-basis review wording while keeping formulas and effective-prestress adoption unchanged.
- COMMERCIAL.PSLOSS.13: Standardizes loss-percent interpretation across 4.2 Friction, 4.3 Anchor Set, and 4.4 Elastic Shortening by adding a shared component-loss / fpj basis note, non-cumulative warning, and report-summary rows without changing formulas or results.

- COMMERCIAL.PSLOSS.14: Cleans up active Prestress Losses headers and 4.1 next-step wording so the closed Friction, Anchor Set, and Elastic Shortening preview pages reflect the shared loss-percent basis standard and the workflow points to 4.5 Time-Dependent Losses next, without changing formulas or results.

- COMMERCIAL.PSLOSS.16–18: Completes the 4.5 Time-Dependent Losses source-gated preview package with a calculation-route selector, refined/time-step factor trace, approximate quick-check comparison, result-summary cards, effective-prestress handoff, editable segment age at transport defaulting to 30 days, editable span assembly duration before stressing, computed representative t_jack, and 3.8 ti reconciliation without adopting final time-dependent losses.
- COMMERCIAL.PSLOSS.20: Polishes 4.5 Time-Dependent Losses selected-age symbol consistency by using t_start for the selected time-step start age in equations, variable traces, and report rows, while retaining computed t_jack only in the construction-stage reconciliation and preserving all creep/shrinkage results.
- COMMERCIAL.PSLOSS.21: Adds a source-gated relaxation preview to 4.5 with method/stress-basis/steel-class selectors, AASHTO R1/R2 equation trace, low-relaxation quick-check comparison, and route-dependent 4.6 handoff while keeping final effective-prestress adoption blocked.

- COMMERCIAL.PSLOSS.22: Renames 4.5 to Time-Dependent Losses and splits the workflow into internal Overview, Creep, Shrinkage, Relaxation, and Handoff to 4.6 tabs while preserving creep, shrinkage, relaxation, route-selection, t_start, and handoff results.
