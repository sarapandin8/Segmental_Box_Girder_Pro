# Segmental Box Girder Pro

Commercial-grade MVP foundation for independent PT segmental box-girder design review.

This app is built as a design-check and report-assist tool for bridge engineers. It does **not** replace the primary FEA model. FEA output from CSI/MIDAS or equivalent software must be imported or keyed in as design demand.

## Current milestone

**Commercial Architecture Foundation M1**

- Streamlit workspace with professional sidebar workflow
- Single-click workspace navigation using direct `st.session_state.current_page` binding
- Versioned project schema: `0.2.0-commercial-m1`
- Engineering validation layer with error/warning/info issue levels
- Workflow completeness summary
- AASHTO LRFD 2014 Article 5.8.6 shear/torsion checks
- EN 1991-2 centrifugal-force check
- AASHTO-style prestress loss calculations with unit notes
- JSON save/load with legacy schema upgrade
- Unit tests for core engineering calculations and schema validation

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Test

```bash
python -m pytest -q
```

## Engineering priority

1. Engineering correctness
2. Numerical consistency
3. Workflow completeness
4. QA robustness
5. UI/UX polish

Never sacrifice engineering correctness for UI polish.

## Internal units

- Forces: kN
- Geometry: m for general bridge dimensions; mm for section/torsion reinforcement checks
- Stress: MPa = N/mm²
- Moments/torsion: kN·m in UI, converted to N·mm internally

Important: AASHTO empirical creep/shrinkage factors use code-specified intermediate units. The app evaluates `V/S` in inches and concrete strength in ksi for those correction factors, then reports final losses in MPa.
