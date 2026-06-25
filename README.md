# Segmental Box Girder Pro — Commercial M3A

Commercial, report-driven Streamlit design-review app for BG40 PT segmental box girder.

This milestone starts the detailed **1.3 Design Loads** implementation. It follows the Concrete Section Pro app discipline: engineering-first UI, one source of truth for inputs, visible formulas/code basis, editable report tables, Plotly engineering figures, QA guards, regression tests, and clean ZIP packaging.

## Current milestone: COMMERCIAL.M3A

### Added / refined

- Detailed `1.3 Loads` workspace with the following sub-panels:
  - SDL editable table
  - LL+IM with U20 loading diagram and EN dynamic-factor trace
  - LF / HF with EN formulas and rail-level schematic
  - CF with EN centrifugal-force formula and trace
  - Wind load with EN/DPT formula and bridge wind-direction schematic
  - CR&SH parameter declaration for Chapter 4
  - EQ with DPT 1301/1302-61 seed lookup engine, spectrum calculation, response-spectrum Plotly figure, and seismic design category ก/ข/ค/ง
  - FEA Load Input Summary table
- `st.data_editor` for SDL component data with **single-source-of-truth** storage.
- Code-basis cards for each load type.
- New pure calculation modules:
  - `core/load_models.py`
  - `core/dpt_seismic.py`
- New Plotly engineering figure helpers:
  - `visualization/load_figures.py`
- Initial version-controlled DPT seismic data scaffold:
  - `data/dpt_1301_1302_61/general_ss_s1_seed.csv`
  - `data/dpt_1301_1302_61/standard_meta.json`

### DPT seismic database status

M3A includes a **seed database** to prove the workflow and regression-test the lookup engine. It includes selected rows such as:

- อ.สะเดา จ.สงขลา: Ss = 0.079, S1 = 0.084
- อ.เมืองขอนแก่น จ.ขอนแก่น: Ss = 0.053, S1 = 0.030
- อ.เมืองหนองคาย จ.หนองคาย: Ss = 0.196, S1 = 0.048
- BG40 report baseline values: Ss = 0.176, S1 = 0.045

Full national DPT district database extraction and Bangkok Basin zone database remain a future QA milestone.

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

M3A targeted regression result: `26 passed`.

## Engineering limitations

- DPT 1301/1302-61 is a building seismic standard. In this bridge app it is used as Thai project seismic-parameter basis consistent with BG40 report criteria, not as a bridge-specific seismic design code.
- Full station-by-station FEA import remains pending.
- Full national DPT lookup database and Bangkok Basin zone 1–10 workflow remain pending.
- Report export is still a structured preview, not a final Word/PDF generator.
