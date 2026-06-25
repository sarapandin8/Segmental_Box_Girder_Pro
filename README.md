# Segmental Box Girder Pro — Commercial M3B-QA

Commercial, report-driven Streamlit design-review app for BG40 PT segmental box girder.

This milestone continues the detailed **1.3 Design Loads** implementation and corrects / verifies the DPT EQ workflow. It follows the Concrete Section Pro app discipline: engineering-first UI, one source of truth for inputs, visible formulas/code basis, editable report tables, Plotly engineering figures, QA guards, regression tests, and clean ZIP packaging.

## Current milestone: COMMERCIAL.M3B-QA

### Added / refined

- Corrected the **General Thailand DPT equivalent-static response spectrum** used for EQ / Cs:
  - Uses **DPT Fig. 1.4-1** when `SD1 ≤ SDS`.
  - Uses **DPT Fig. 1.4-2** when `SD1 > SDS`.
  - Does **not** use the dynamic-spectrum `0.4SDS` ramp from Fig. 1.4-3 / Fig. 1.4-4 for equivalent-static `Cs`.
- Added explicit spectrum figure/branch trace in the EQ output table.
- Added QA documentation for DPT database verification and remaining production cautions.
- Added regression tests for:
  - Fig. 1.4-1 equivalent-static plateau at `Sa = SDS` before `Ts`.
  - Fig. 1.4-2 equivalent-static `Sa = SDS` up to `T = 0.2 s`, linear branch from `0.2 s` to `1.0 s`, and `Sa = SD1/T` after `1.0 s`.
  - Updated schema version `0.3.5-commercial-m3b-qa`.

## DPT seismic database status

The app includes a curated DPT seismic database extracted from the uploaded **DPT 1301/1302-61 Rev.1** standard. It includes national general-district rows, Bangkok Basin Zone 1–10 routing, equivalent-static zone spectrum tables, Fa/Fv tables, and seismic design category tables.

Key database files:

- `general_ss_s1_by_district.csv` — 816 general Thailand province/district rows from DPT Table 1.4-1.
- `bangkok_basin_zone_map.csv` — Bangkok Basin Zone 1–10 routing from DPT Fig. 1.4-5.
- `bangkok_equiv_static_5p0_table_1_4_5.csv` — equivalent-static Bangkok Basin spectrum at 5% damping.
- `bangkok_equiv_static_2p5_table_1_4_4.csv` — equivalent-static Bangkok Basin spectrum at 2.5% damping.
- `fa_table_1_4_2.csv`, `fv_table_1_4_3.csv` — site coefficient tables.
- `seismic_design_category_tables_1_6.csv` — category ก/ข/ค/ง table data.

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

M3B-QA targeted regression result: `33 passed` after the equivalent-static spectrum correction and DPT QA guards.

## Engineering limitations

- DPT 1301/1302-61 is a building seismic standard. In this bridge app it is used as Thai project seismic-parameter basis consistent with BG40 report criteria, not as a bridge-specific seismic design code.
- Full station-by-station FEA import remains pending.
- DPT seismic database was extracted from the uploaded PDF; future production use should still include independent engineering spot-checks of critical project locations against official standard pages.
- Report export is still a structured preview, not a final Word/PDF generator.
