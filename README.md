# Segmental Box Girder Pro — COMMERCIAL.M3H.3

Commercial report-driven Streamlit workspace for PT segmental box-girder design review.

## COMMERCIAL.M3H.3 updates

- Fixes Project JSON load crash caused by modifying `st.session_state.current_workspace` after the sidebar radio widget was instantiated.
- Adds a pending-load handoff: the explicit **Load uploaded project** button stores the validated/migrated project in a private pending state, reruns once, and applies the project plus workspace/subpage reset before any widgets are created.
- Preserves the M3H.2 safety improvements: explicit load button, JSON decode/schema migration, fingerprint handling, and load status message.
- Schema: `0.4.8-commercial-m3h3-json-widget-state-fix`.

## Retained commercial app foundations

- Concrete Section Pro-style workspace/sidebar/card layout and Plotly figure conventions.
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
