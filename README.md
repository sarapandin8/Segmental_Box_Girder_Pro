# Segmental Box Girder Pro — COMMERCIAL.M3H.10

Commercial report-driven Streamlit workspace for PT segmental box-girder design review.

## COMMERCIAL.M3H.10 updates

- Hides the Plotly modebar in the normal Tendon Section Overlay canvas so the viewport reads as a report figure rather than a debug chart.
- Refines B/D/CL/CG dimension labels with stronger white label boxes, cleaner guide offsets, and less intrusive centroid callouts.
- Further reduces grid/axis dominance with softer grid colors, quieter zero lines, and report-ready canvas background.
- Preserves the M3H.9 Dimension mode control: Clean, Full dimensions, and Hide dimensions. Clean remains the default.
- Keeps the existing tendon QA logic unchanged: external tendon points are still checked against the active inner void and section polygon.
- Schema: `0.4.16-commercial-m3h10-viewport-report-polish`.

## Retained commercial app foundations

- Concrete Section Pro-style workspace/sidebar/card layout and Plotly figure conventions.
- Explicit Project JSON load button with pending-load rerun workflow to avoid Streamlit widget-state crashes.
- DPT seismic database and EQ workflow.
- 1.3 Loads engines for SDL, LL+IM, LF/HF/CF, wind, CR/SH, and EQ.
- Coordinate-driven section properties with CSiBridge XLSX/CSV import.
- CSiBridge tendon layout import and tendon summary cards.

## Display formatting rules

- Force/load and moment/torsion resultants: no decimals.
- Stress in MPa: 2 decimals.
- Length in mm: no decimals.
- Length in m: 3 decimals.
- Area and section properties in m²/m³/m⁴: 3 decimals.
- Coefficients, DCR, utilization, and spectrum factors: 3 decimals unless a report table specifies otherwise.

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Test:

```bash
python -m compileall -q .
python -m pytest -q
```

## Traceability notes retained for regression tests

- 1.3.7 Wind Load uses EN 1991-1-4, Table 2.5, DPT 1311-50 wind basis, report-style figures, and FEA summary trace.
- DPT seismic database includes General Thailand and Bangkok Basin Zone 1–10 routing.
- AASHTO LRFD 2014 Table 3.10.7.1-1 is used as bridge R-factor guidance for substructure system recommendation.
- Full station-by-station FEA import remains pending.
- Coordinate-driven section properties use Structural Polygon 1 and Opening Polygon 1 from CSiBridge exports.

## COMMERCIAL.M3H.6
- Polishes Tendon Section Overlay with centerline-origin display, quick station buttons, family/all/hidden label modes, family-colored tendon markers, inside-void QA, minimum clearance to inner-boundary reporting, formatted selected-station tables, and hover details.


## COMMERCIAL.M3H.7 — Tendon Overlay Canvas Polish

- Reworked the Section Overlay page toward the Concrete Section Pro canvas style.
- Added a CANVAS header, Live Tendon Section Preview wording, external tendon QA pill, and report-ready figure caption.
- Cleaned Plotly legend labels to Concrete / Inner void / Centroid / tendon families.
- Added station annotation directly inside the figure for report/export readability.
- Kept selected-station QA in concise cards below the canvas and preserved the merged tendon QA table.


M3H.7.1 fixes the tendon overlay figure call to avoid TypeError when app.py and visualization/tendon_figures.py are updated out of sync.


## COMMERCIAL.M3H.8 — Tendon Canvas Card Layout Alignment

- Reworks the Tendon Section Overlay into a Concrete Section Pro-style contained canvas card.
- Wraps CANVAS header, note, custom legend strip, Plotly drawing viewport, caption, and QA summary cards in one bordered card container.
- Hides the default Plotly legend and replaces it with a compact report-style legend strip for Concrete, Inner void, Centroid, and T1–T8 tendon families.
- Converts the lower overlay summary into a canvas footer grid and adds explicit mm units / PASS wording to the clearance status.
- Keeps the existing engineering QA logic unchanged: tendon points are still checked against the active inner void and section polygon.


## COMMERCIAL.M3H.9 — Engineering Dimension Guide and Station Badge Polish

- Moves the selected-station text out of the section plot and into a dedicated canvas badge.
- Adds Dimension mode options: Clean, Full dimensions, and Hide dimensions.
- Makes Clean mode show only essential B, D, CL, and centroid guides.
- Makes Full dimensions add y_cg and y_t fiber dimensions without changing tendon QA logic.
- Reduces raw chart appearance using muted guide colors, external dimension offsets, tick marks, and lighter grid lines.


## COMMERCIAL.M3H.10 — Tendon Overlay Viewport and Report Figure Polish

- Hides the Plotly modebar in the normal Section Overlay canvas using a dedicated canvas Plotly config.
- Polishes B/D/CL/CG dimension labels and offsets so Clean mode reads more like an engineering drawing.
- Moves the CG callout away from the right plot edge and makes centroid guide lines lighter.
- Reduces grid and axis visual dominance for a cleaner report-ready viewport.
- Keeps tendon location QA, selected-station table data, and minimum-clearance logic unchanged.
