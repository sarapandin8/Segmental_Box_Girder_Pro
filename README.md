# Segmental Box Girder Pro — Commercial M3D

Commercial, report-driven Streamlit design-review app for BG40 PT segmental box girder.

This milestone aligns the app UI system with the Concrete Section Pro style discipline and adds global engineering display-format rules. It preserves the M3C DPT/AASHTO EQ calculation route while standardizing cards, tables, formula blocks, Plotly chart styling, and numeric display behavior.

## Current milestone: COMMERCIAL.M3D

### Added / refined

- Added `core/formatting.py` for global engineering display formatting.
- Added app-wide display rules:
  - Force/load values: no decimals.
  - Moment/torque values: no decimals.
  - Stress in MPa: 2 decimals.
  - Length in mm: no decimals.
  - Length in m: 3 decimals.
  - Area in mm²: no decimals.
  - Area/section properties in m²/m³/m⁴: 3 decimals.
  - Coefficients, factors, ratios, g-values, DCR/utilization: 3 decimals.
- Added `show_engineering_table()` wrapper so read-only summary / QA / FEA tables use consistent engineering formatting.
- Added CSP-aligned CSS classes for:
  - input cards
  - calculation trace cards
  - result cards
  - QA cards
  - plot cards
  - table cards
- Began applying the formatting system to the 1.3 Design Loads / EQ / FEA summary outputs.
- Updated schema version to `0.3.7-commercial-m3d`.
- Added regression tests for formatting behavior and UI source guards.

## DPT seismic database status

The app includes a curated DPT seismic database extracted from the uploaded DPT 1301/1302-61 Rev.1 standard. It includes national general-district rows, Bangkok Basin Zone 1–10 routing, equivalent-static zone spectrum tables, Fa/Fv tables, and seismic design category tables.

Key database files:

- `general_ss_s1_by_district.csv` — 816 general Thailand province/district rows from DPT Table 1.4-1.
- `bangkok_basin_zone_map.csv` — Bangkok Basin Zone 1–10 routing from DPT Fig. 1.4-5.
- `bangkok_equiv_static_5p0_table_1_4_5.csv` — equivalent-static Bangkok Basin spectrum at 5% damping.
- `bangkok_equiv_static_2p5_table_1_4_4.csv` — equivalent-static Bangkok Basin spectrum at 2.5% damping.
- `fa_table_1_4_2.csv`, `fv_table_1_4_3.csv` — site coefficient tables.
- `seismic_design_category_tables_1_6.csv` — category ก/ข/ค/ง table data.

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

M3D targeted regression result: `42 passed`.

## Engineering limitations

- DPT 1301/1302-61 is a building seismic standard. In this bridge app it is used as Thai project seismic-parameter basis consistent with BG40 report criteria, not as a bridge-specific seismic design code.
- AASHTO operational category shall be confirmed by the owner / authority having jurisdiction.
- AASHTO R recommendation assumes the bridge substructure and detailing satisfy the applicable AASHTO seismic provisions; manual override requires engineering justification.
- Full station-by-station FEA import remains pending.
- DPT seismic database was extracted from the uploaded PDF; future production use should still include independent engineering spot-checks of critical project locations against official standard pages.
- Report export is still a structured preview, not a final Word/PDF generator.
