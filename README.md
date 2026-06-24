# Segmental Box Girder Pro

Streamlit MVP for PT segmental box girder design-review checks.

## Scope

This app is a design-check and report-assist workspace. It does **not** replace CSiBridge / SAP2000 / MIDAS FEA analysis.

The first MVP includes:

- BG40 default project data
- Project setup and JSON save/load
- Section/tendon inputs
- Prestress loss calculations
- EN 1991-2 centrifugal force reduction check
- AASHTO LRFD 2014 Article 5.8.6 torsion checks
- ULS shear/torsion dashboard
- Markdown calculation summary export

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Engineering Notes

- Internal units: kN, m, MPa, mm.
- AASHTO empirical prestress-loss factors use code-specified units for intermediate factors, e.g. V/S in inches and concrete strength in ksi.
- For normal-weight concrete segmental construction with external / unbonded tendons, `φv = 0.85` is used for shear/torsion resistance.
- FEA demands should be reviewed and imported/keyed in before final design issue.
