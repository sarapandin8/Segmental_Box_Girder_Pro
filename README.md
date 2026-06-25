# Segmental Box Girder Pro — Commercial M2.1

Commercial M2.1 converts the BG40 prototype into a report-driven engineering workspace. The UI follows the BG40 R10 report structure while intentionally omitting the word **Chapter** from the app sidebar for a more professional software feel.

## Milestone M2 Scope

- Reworked sidebar workspace into report-driven sections:
  - Project Dashboard
  - 1 Criteria / Loads
  - 2 Bridge Model
  - 3 Section Properties
  - 4 Prestress Losses
  - 5 FEA Results
  - 6 ULS Flexure
  - 7 ULS Shear / Torsion
  - 8 SLS Stress
  - 9 Deflection
  - Report / QA
- Added subsection navigation for each workspace, matching the report subsections such as 1.1 Standards, 1.2 Materials, 1.3 Loads, and 1.4 Combinations.
- Preserved M1 engineering kernels for prestress loss and AASHTO LRFD 2014 Art. 5.8.6 shear/torsion checks.
- Added a report schema definition in `core/report_schema.py`.
- Expanded BG40 R10 defaults to include materials, load components, bridge model assumptions, section properties, FEA baseline values, ULS flexure, SLS stress, and deflection defaults.
- Added project dashboard cards for governing ULS, SLS, deflection, QA status, and report readiness.
- Added report preview/trace sections to support future Word/PDF export.
- Preserved single-click workspace/subpage navigation using `st.session_state` keys.
- Clean no-cache package.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Test

```bash
python -m compileall -q .
python -m pytest -q
```

Expected result:

```text
6 passed
```

## Engineering Policy

Priority order:

1. Engineering correctness
2. Numerical consistency
3. Workflow completeness
4. QA robustness
5. UI/UX polish

Never sacrifice engineering correctness for UI polish.

## Notes

This application performs independent design checks and report-assist workflows based on user-defined inputs and imported/keyed FEA demand envelopes. It does not replace the primary structural analysis model.


## Commercial M2.1 UI Polish

- Applies Concrete Section Pro style skill: safer top header card, blue/green commercial cards, report-driven status table, professional wording, and dashboard governing-result visibility.
- Keeps one-source-of-truth Streamlit workspace/subpage state and preserves M1 engineering kernels.
