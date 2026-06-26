# Segmental Box Girder Pro — COMMERCIAL.M3H.1

Commercial report-driven design-review workspace for PT segmental box girder bridge checks.

This milestone fixes the top of `2.4 Tendon Layout Reference` by replacing the long import instruction banner with report-style tendon import summary cards. The cards show the imported tendon model, strand/area basis, jacking basis, and layout status using values merged from the CSiBridge General, Vertical Layout, and Horizontal Layout exports.

## M3H.1 changes

- Replaced the `CSiBridge tendon-layout import` text banner with summary cards.
- Added visible tendon-model summary:
  - active BridgeObj
  - number of imported tendons
  - mirrored tendon families
  - tendon material
  - strand label, e.g. `24-T15.2`
  - Aps per tendon and total Aps
- Added jacking-basis summary:
  - `fpu = 1860 MPa`
  - `0.75 fpu = 1395 MPa`
  - `Pj = 0.75 fpu × Aps`
  - jacking force per tendon and total jacking force
- Added layout design summary cards:
  - average end `dp`
  - average midspan `dp`
  - midspan eccentricity `e = dp(midspan) - y_t`
- Added tendon import basis expander table for traceability.
- Updated tendon model data to use the derived `0.75 fpu × Aps` jacking force as the adopted jacking basis while keeping imported force trace fields.
- Bumped schema to `0.4.6-commercial-m3h1-tendon-summary-cards`.

## Verification

```text
python -m compileall -q .
python -m pytest -q

65 passed
```

## Packaging

The released ZIP is packaged without generated Python/cache files:

```text
__pycache__/
.pytest_cache/
*.pyc
*.pyo
.streamlit/
.DS_Store
```
