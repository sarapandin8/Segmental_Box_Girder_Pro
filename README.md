# Segmental Box Girder Pro — COMMERCIAL.M3H.2

Commercial report-driven design-review workspace for PT segmental box girder bridge checks.

This milestone fixes project JSON loading stability. Earlier builds could appear to hang because the Streamlit `file_uploader` kept the uploaded project file present across reruns and the app loaded + reran automatically. M3H.2 changes the workflow to an explicit `Load uploaded project` action, validates/migrates the JSON safely, and prevents repeated load/rerun loops.

## M3H.2 changes

- Replaced automatic project JSON loading with an explicit `Load uploaded project` button.
- Added `core/project_io.py` for safe JSON decoding, size checks, schema migration, file fingerprinting, and user-facing load summaries.
- Added loaded-file fingerprint tracking so an already-loaded JSON is not repeatedly applied.
- Reset workspace/subpage safely after a successful project load.
- Added user-facing load status and clearer JSON error messages.
- Added regression tests for valid project migration, invalid JSON handling, fingerprinting, and the no-auto-rerun upload workflow.
- Bumped schema to `0.4.7-commercial-m3h2-json-load-stability`.

## Current capabilities retained from prior M3 milestones

- Display formatting rules aligned with Concrete Section Pro.
- `1.3.7 Wind Load` report-driven EN 1991-1-4 / DPT 1311-50 workflow with Table 2.5 factor logic.
- DPT seismic database with Bangkok Basin Zone 1–10 routing.
- AASHTO LRFD 2014 Table 3.10.7.1-1 bridge seismic R recommendation.
- Coordinate-driven section properties using CSiBridge `Structural Polygon 1` and `Opening Polygon 1` imports.
- CSiBridge tendon layout import and viewer with tendon summary cards.
- Full station-by-station FEA import remains pending.

## Verification

```text
python -m compileall -q .
python -m pytest -q

69 passed
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
