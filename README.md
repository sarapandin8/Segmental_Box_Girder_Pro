# Segmental Box Girder Pro — Commercial M3B

Commercial, report-driven Streamlit design-review app for BG40 PT segmental box girder.

This milestone starts the detailed **1.3 Design Loads** implementation. It follows the Concrete Section Pro app discipline: engineering-first UI, one source of truth for inputs, visible formulas/code basis, editable report tables, Plotly engineering figures, QA guards, regression tests, and clean ZIP packaging.

## Current milestone: COMMERCIAL.M3B

### Added / refined

- Detailed `1.3 Loads` workspace with the following sub-panels:
  - SDL editable table
  - LL+IM with U20 loading diagram and EN dynamic-factor trace
  - LF / HF with EN formulas and rail-level schematic
  - CF with EN centrifugal-force formula and trace
  - Wind load with EN/DPT formula and bridge wind-direction schematic
  - CR&SH parameter declaration for Chapter 4
  - EQ with DPT 1301/1302-61 curated location lookup, General Thailand and Bangkok Basin workflows, spectrum calculation, response-spectrum Plotly figure, and seismic design category ก/ข/ค/ง
  - FEA Load Input Summary table
- `st.data_editor` for SDL component data with **single-source-of-truth** storage.
- Code-basis cards for each load type.
- New pure calculation modules:
  - `core/load_models.py`
  - `core/dpt_seismic.py`
- New Plotly engineering figure helpers:
  - `visualization/load_figures.py`
- Version-controlled DPT seismic database files:
  - `data/dpt_1301_1302_61/general_ss_s1_by_district.csv`
  - `data/dpt_1301_1302_61/bangkok_basin_zone_map.csv`
  - `data/dpt_1301_1302_61/bangkok_equiv_static_5p0_table_1_4_5.csv`
  - `data/dpt_1301_1302_61/standard_meta.json`

### DPT seismic database status

M3B replaces the seed database with a curated DPT database extracted from the uploaded standard. It includes national general-district rows, Bangkok Basin Zone 1–10 routing, equivalent-static zone spectrum tables, Fa/Fv tables, and seismic design category tables.

Key database files:

- `general_ss_s1_by_district.csv` — 816 general Thailand province/district rows from DPT Table 1.4-1.
- `bangkok_basin_zone_map.csv` — Bangkok Basin Zone 1–10 routing from DPT Fig. 1.4-5.
- `bangkok_equiv_static_5p0_table_1_4_5.csv` — equivalent-static Bangkok Basin spectrum at 5% damping.
- `bangkok_equiv_static_2p5_table_1_4_4.csv` — equivalent-static Bangkok Basin spectrum at 2.5% damping.
- `fa_table_1_4_2.csv`, `fv_table_1_4_3.csv` — site coefficient tables.
- `seismic_design_category_tables_1_6.csv` — category ก/ข/ค/ง table data.

Remaining future QA work: deeper independent spot-checking of every extracted row and richer tambon-level autocomplete.

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

M3B targeted regression result: `31 passed` after new database and Bangkok Basin lookup tests.

## Engineering limitations

- DPT 1301/1302-61 is a building seismic standard. In this bridge app it is used as Thai project seismic-parameter basis consistent with BG40 report criteria, not as a bridge-specific seismic design code.
- Full station-by-station FEA import remains pending.
- DPT seismic database was extracted from the uploaded PDF; every future production use should include independent engineering spot-checks of critical project locations against the official standard pages.
- Report export is still a structured preview, not a final Word/PDF generator.
