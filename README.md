# Segmental Box Girder Pro — Commercial M3C

Commercial, report-driven Streamlit design-review app for BG40 PT segmental box girder.

This milestone continues the detailed **1.3 Design Loads** implementation and adds AASHTO bridge seismic I/R guidance for the EQ workflow. It follows the Concrete Section Pro app discipline: engineering-first UI, one source of truth for inputs, visible formulas/code basis, editable report tables, Plotly engineering figures, QA guards, regression tests, and clean ZIP packaging.

## Current milestone: COMMERCIAL.M3C

### Added / refined

- Added **AASHTO Bridge Seismic Parameters** card in `1.3.9 Earthquake (EQ)`.
- Added dropdowns for:
  - AASHTO operational category: `Critical`, `Essential`, `Other`.
  - Substructure / lateral system.
  - R selection mode: automatic from AASHTO table or manual override.
  - Importance factor `I` preset: ordinary, BG40/project default, critical, or manual override.
- Added reference database files:
  - `data/aashto_lrfd_2014/response_modification_factors_substructures_3_10_7_1_1.csv`
  - `data/aashto_lrfd_2014/response_modification_factors_connections_3_10_7_1_2.csv`
  - `data/aashto_lrfd_2014/bridge_importance_factor_presets.csv`
- Added `core/aashto_seismic.py` for traceable AASHTO R recommendations and I preset handling.
- Changed EQ page so `I` and `R` are controlled once from the AASHTO bridge seismic card, then reused by General Thailand, Bangkok Basin, manual lookup, and FEA summary outputs.
- EQ output tables now report AASHTO operational category, substructure R basis, and importance-factor source.
- Updated schema version to `0.3.6-commercial-m3c`.
- Added regression tests for AASHTO R values, I presets, reference data files, and UI source guards.

## DPT seismic database status

The app includes a curated DPT seismic database extracted from the uploaded **DPT 1301/1302-61 Rev.1** standard. It includes national general-district rows, Bangkok Basin Zone 1–10 routing, equivalent-static zone spectrum tables, Fa/Fv tables, and seismic design category tables.

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

M3C targeted regression result: `37 passed`.

## Engineering limitations

- DPT 1301/1302-61 is a building seismic standard. In this bridge app it is used as Thai project seismic-parameter basis consistent with BG40 report criteria, not as a bridge-specific seismic design code.
- AASHTO operational category shall be confirmed by the owner / authority having jurisdiction.
- AASHTO R recommendation assumes the bridge substructure and detailing satisfy the applicable AASHTO seismic provisions; manual override requires engineering justification.
- Full station-by-station FEA import remains pending.
- DPT seismic database was extracted from the uploaded PDF; future production use should still include independent engineering spot-checks of critical project locations against official standard pages.
- Report export is still a structured preview, not a final Word/PDF generator.
