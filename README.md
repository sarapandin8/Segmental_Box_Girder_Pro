# Segmental Box Girder Pro — Commercial M3F

Commercial, report-driven Streamlit design-review app for BG40 PT segmental box girder.

This milestone reorganizes the app workflow so the major workspaces better match the engineering workflow discussed with the reviewer: **Loads** is promoted to its own dedicated workspace, and **Bridge Geometry / Section Properties** combines bridge description, analysis-model documentation, and section properties. It preserves the M3E Wind Load engine, M3C AASHTO bridge I/R controls, M3B DPT seismic database, Concrete Section Pro style alignment, one-source state discipline, and global engineering display-formatting rules.

## Current milestone: COMMERCIAL.M3F

### Workspace reorganization

New sidebar workflow:

1. **Criteria**
2. **Bridge Geometry / Section Properties**
3. **Loads**
4. **Prestress Losses**
5. **FEA Results**
6. **ULS Flexure**
7. **ULS Shear / Torsion**
8. **SLS Stress**
9. **Deflection**
10. **Report / QA**

### Refined subpages

**1 Criteria**
- `1.1 Standards`
- `1.2 Materials`
- `1.3 Design Basis / Units`
- `QA / Report Preview`

**2 Bridge Geometry / Section Properties**
- `2.1 Bridge Description`
- `2.2 Geometry and Analysis Model`
- `2.3 Section Properties`
- `2.4 Tendon Layout Reference`
- `2.5 Consistency Checks`
- `QA / Report Preview`

**3 Loads**
- `3.1 Dead Load`
- `3.2 SDL`
- `3.3 LL + IM`
- `3.4 LF / HF`
- `3.6 CF`
- `3.7 Wind`
- `3.8 CR&SH`
- `3.9 EQ`
- `3.10 FEA Summary`
- `QA / Report Preview`

### Analysis model scope note

The app now explicitly states that the FEA model is created in an external FEA program, such as CSiBridge, MIDAS Civil, SAP2000, RM Bridge, or another analysis program. The app records geometry, analysis-model assumptions, support conditions, tendon representation, and report figures for design review and report generation only. It is not an FEA solver.

### Preserved M3E Wind Load work

The former report subsection `1.3.7 Wind Load` is now presented in the dedicated Loads workspace as `3.7 Wind`, while preserving report traceability.

The dedicated Loads workspace still includes the report-driven EN 1991-1-4 / DPT 1311-50 wind module:

- bundled BG40 R10 wind figures,
- editable one-source wind parameter table,
- DPT wind group dropdown,
- automatic `C`-factor interpolation from EN 1991-1-4 Table 8.2 / BG40 R10 Table 2.5,
- wind force and line-load calculations,
- FEA load summary integration,
- engineering display formatting and regression tests.

### Schema

- Updated schema version to `0.3.9-commercial-m3f`.
- Existing project JSON files are promoted through `ensure_project_schema()` while preserving engineering values.

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

M3F targeted regression result: `50 passed`.

## Engineering limitations

- DPT 1301/1302-61 is a building seismic standard. In this bridge app it is used as Thai project seismic-parameter basis consistent with BG40 report criteria, not as a bridge-specific seismic design code.
- EN 1991-1-4 wind factor automation follows the simplified bridge wind calculation used by BG40 R10; project-specific National Annex or owner requirements can override parameters with trace.
- AASHTO operational category shall be confirmed by the owner / authority having jurisdiction.
- AASHTO R recommendation assumes the bridge substructure and detailing satisfy the applicable AASHTO seismic provisions; manual override requires engineering justification.
- Full station-by-station FEA import remains pending.
- Report export is still a structured preview, not a final Word/PDF generator.
