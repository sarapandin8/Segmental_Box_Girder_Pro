# Segmental Box Girder Pro — Commercial M3E

Commercial, report-driven Streamlit design-review app for BG40 PT segmental box girder.

This milestone refines **1.3.7 Wind Load (WS)** into a full report-driven calculation page. It preserves the M3D Concrete Section Pro style alignment, DPT/AASHTO EQ route, one-source state discipline, and global engineering formatting rules.

## Current milestone: COMMERCIAL.M3E

### Added / refined

- Rebuilt `1.3.7 Wind Load (WS)` as a structured report-driven page with:
  - Overview
  - Inputs
  - EN Factors
  - Calculations
  - Figures
  - FEA Summary
- Added bundled wind reference figures cropped from the BG40 R10 PDF:
  - `Figure 1.2 Reference wind speed map of Thailand (DPT 1311-50)`
  - `Figure 1.3 Wind load directions on bridge (EN 1991-1-4 Fig. 8.2)`
  - Wind factor Table 2.5 / deck-height reference
  - WS/WL bridge cross-section loading schematic
- Added editable wind parameter table using one source of truth.
- Added DPT wind speed group selector:
  - Group 1: V50 = 25 m/s, TF = 1.00
  - Group 2: V50 = 27 m/s, TF = 1.00
  - Group 3: V50 = 29 m/s, TF = 1.00
  - Group 4A: V50 = 25 m/s, TF = 1.20
  - Group 4B: V50 = 25 m/s, TF = 1.08
- Added automatic wind calculation engine:
  - `vb = cdir cseason vb,0`
  - `q = 0.5 rho vb^2`
  - `b/dtot`
  - `CWS` and `CWS+WL` from EN 1991-1-4 Table 8.2 / BG40 R10 Table 2.5
  - `Aref,x = dtot L`
  - `FW,x = 0.5 rho vb^2 C Aref,x`
  - equivalent FEA line loads `WS` and `WS+WL`
- Added automatic linear interpolation for wind factor `C` when `0.5 < b/dtot < 4.0`, including `ze` interpolation where applicable.
- Updated global formatting rule for distributed line loads (`kN/m`) to display 2 decimal places in report/FEA summaries, matching BG40 wind results such as `7.01 kN/m` and `15.10 kN/m`.
- Updated schema version to `0.3.8-commercial-m3e`.
- Added regression tests for wind-factor interpolation, automatic BG40 wind calculation, wind UI/source guards, and engineering formatting.

## Display formatting rules

- Force/load resultants: no decimals.
- Moment/torque values: no decimals.
- Equivalent line/distributed loads in `kN/m`: 2 decimals.
- Stress in MPa: 2 decimals.
- Length in mm: no decimals.
- Length in m: 3 decimals.
- Area in mm²: no decimals.
- Area/section properties in m²/m³/m⁴: 3 decimals.
- Coefficients, factors, ratios, g-values, DCR/utilization: 3 decimals.

## DPT seismic database status

The app includes a curated DPT seismic database extracted from the uploaded DPT 1301/1302-61 Rev.1 standard. It includes national general-district rows, Bangkok Basin Zone 1–10 routing, equivalent-static zone spectrum tables, Fa/Fv tables, and seismic design category tables.

## Bridge seismic I/R basis

- DPT 1301/1302-61 supplies the Thai seismic spectrum and the equivalent-static `Cs = Sa(I/R)` calculation route used by the BG40 report criteria.
- AASHTO LRFD 2014 Table 3.10.7.1-1 is used to recommend the bridge substructure response modification factor `R` by operational category and substructure type.
- The importance factor `I` remains a project/DPT input. AASHTO operational category is not silently converted into `I`.
- Connection R-factors are kept as a separate reference table and are not substituted for the global substructure R used in the EQ load summary.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
python -m compileall -q .
python -m pytest -q
```

M3E targeted regression result: `47 passed`.

## Engineering limitations

- DPT 1301/1302-61 is a building seismic standard. In this bridge app it is used as Thai project seismic-parameter basis consistent with BG40 report criteria, not as a bridge-specific seismic design code.
- EN 1991-1-4 wind factor automation follows the simplified bridge wind calculation used by BG40 R10; project-specific National Annex or owner requirements can override parameters with trace.
- AASHTO operational category shall be confirmed by the owner / authority having jurisdiction.
- AASHTO R recommendation assumes the bridge substructure and detailing satisfy the applicable AASHTO seismic provisions; manual override requires engineering justification.
- Full station-by-station FEA import remains pending.
- Report export is still a structured preview, not a final Word/PDF generator.
