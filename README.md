# Segmental Box Girder Pro — COMMERCIAL.M3H.6

Commercial report-driven Streamlit workspace for PT segmental box-girder design review.

## COMMERCIAL.M3H.6 updates

- Replaces incomplete raw Vertical/Horizontal tendon table previews with a complete **Adopted Tendon Layout Table**: one row per tendon, including tendon/family/side, BridgeObj, material, strand label, Aps per tendon, fpu, jacking stress, jacking force, JackFrom, end/midspan dp, end/midspan horizontal offset, profile point count, and status.
- Adds a **Merged Tendon Profile Table** that combines CSiBridge Vertical and Horizontal layout rows into one control-point table with x, dp from top, and HorizOff in the same row.
- Moves raw General/Vertical/Horizontal import rows into a collapsed **Raw import data / QA only** expander.
- Adds per-tendon vertical/horizontal station matching QA and a merged profile row-count check.
- Schema: `0.4.13-commercial-m3h7-1-overlay-call-fix`.

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
