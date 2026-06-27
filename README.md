# Segmental Box Girder Pro — COMMERCIAL.M4.1D

Commercial report-driven Streamlit workspace for PT segmental box-girder design review.


## COMMERCIAL.M4.1D updates

- Adds 3D inspection presets for `3D Tendon View`: Custom, Overview, Left inspection, Right inspection, Single tendon focus, and Report clean.
- Auto-matches left/right inspection presets with the corresponding half-shell display and tendon side filter so the model opens as a true inspection view instead of a dense overview.
- Adds `Focus tendon` plus `Fade non-focused tendons` so a selected tendon can remain high-contrast while surrounding tendons stay as faint context.
- Adds `Tendon line thickness` and `Station markers` modes (`Key only`, `All stations`, `Off`) for clearer review/report snapshots.
- Keeps all 3D controls inside the UI.2 canvas standard and preserves adopted-source warning/gate behavior.
- Preserves all tendon geometry, section geometry, adopted-source behavior, QA, save/load persistence, and calculation logic; this milestone changes 3D inspection presentation only.
- Schema remains `0.4.20-commercial-bugfix1-section-save-load-persistence`; this milestone adds 3D inspection presets and focus controls only.

## COMMERCIAL.M4.1C updates

- Adds 3D shell display modes for `3D Tendon View`: Full shell, Left half shell, Right half shell, No shell, and Inner void only.
- Adds tendon isolation controls: family filter, side filter, and single-tendon isolate selector so dense 16-tendon views can be reduced to a readable inspection model.
- Adds independent outer shell and inner void opacity sliders for clearer review of tendon paths inside the transparent envelope.
- Clips section-envelope display at the centerline for left/right half-shell review without changing stored section coordinates, tendon geometry, or calculations.
- Keeps the UI.2 canvas figure standard, global Interactive review / Report preview behavior, CAD-style 3D view presets, and adopted-source warning/gate from previous milestones.
- Preserves all tendon geometry, adopted-source behavior, QA, section data, save/load persistence, and calculation logic.
- Schema remains `0.4.20-commercial-bugfix1-section-save-load-persistence`; this milestone adds 3D inspection controls only.

## COMMERCIAL.M4.1B updates

- Adds CAD-style 3D view presets for the `3D Tendon View`: Isometric · Orthographic, Isometric · Perspective, Top, Side elevation, End section, Tendon focus, and Report isometric.
- Defaults the 3D viewport to Orthographic Isometric so the first view reads more like an engineering/CAD review figure rather than a perspective-only Plotly scene.
- Adds `Aspect mode`: Presentation scale for readable review/report images and True scale for checking the real span/width/depth proportion.
- Adds camera projection control so orthographic/report/top/side/end views use orthographic projection while perspective review remains available for interactive exploration.
- Updates the 3D canvas badge, caption, and footer cards to disclose both view preset and aspect mode.
- Preserves all tendon geometry, adopted-source behavior, QA, section data, and calculation logic; this milestone is a 3D presentation/camera control improvement only.
- Schema remains `0.4.20-commercial-bugfix1-section-save-load-persistence`; this milestone adds visualization controls only.

## COMMERCIAL.M4.1A updates

- Adds a new `3D Tendon View` tab immediately after Tendon Plan View in `2.4 Tendon Layout Reference`.
- Builds an interactive Plotly WebGL 3D review viewport with rotate, pan, zoom, reset, and image export support through the global Interactive review / Report preview figure system.
- Displays the box-girder outer shell and inner void as transparent section envelopes extruded along the span.
- Displays external tendon profiles as 3D polylines using merged vertical dp and horizontal offset profile data.
- Adds view presets: Isometric, Top, Side, End, and Tendon focus. M4.1B extends these with orthographic/perspective/report isometric controls.
- Adds family/side filters, tendon label toggle, shell/void visibility toggles, and station marker toggle.
- Uses the adopted tendon design-source snapshot when locked; otherwise clearly marks the viewport as working preview only.
- Preserves all section geometry, tendon import/merge, tendon QA, adopted data, and prestress calculation logic.
- Schema remains `0.4.20-commercial-bugfix1-section-save-load-persistence`; this milestone adds visualization only.

## COMMERCIAL.M4.1 updates

- Locks the Tendon Layout Reference workflow into an explicit imported working model → adopted design-source snapshot process.
- Adds Adopt / Re-adopt tendon model as design source and Clear adopted tendon source controls so raw imports do not silently change downstream values.
- Adds source trace rows for General, Vertical, Horizontal, and BridgeObj mapping, including filename/row-status information where available.
- Adds adopted downstream tendon summary for num tendons, families, Aps per tendon, Aps,total, jacking stress/force, dp averages, y_t, eccentricity, and model fingerprint.
- Updates the Tendon QA / Consistency page with a source gate, downstream trace, report preview status, and Save/Load JSON persistence trace.
- Updates prestress summary fields only from the adopted tendon snapshot; friction curvature/angle remains a later milestone and is not silently inferred.
- Preserves all tendon geometry import, figure generation, location QA, section overlay, and UI.2 figure-system logic.
- Schema: `0.4.19-commercial-m4-1-tendon-adopted-qa-lockdown`.

## Retained COMMERCIAL.UI.2 updates

- Applies the canvas figure system to Section Properties Preview, Tendon Elevation, and Tendon Plan so the module no longer feels like separate Plotly prototypes.
- Adds Clean / Full dimensions / Hide dimensions mode to Section Properties Preview using the same B/D/CL/CG dimension grammar as the Tendon Section Overlay.
- Wraps Section Properties Preview, Tendon Elevation, and Tendon Plan in the same CANVAS header, info strip, meta badge, custom legend strip, report caption, and footer-card pattern.
- Replaces dense Plotly legends on Tendon Elevation and Tendon Plan with compact custom legend strips and adds family/side filters for clearer engineering review.
- Keeps the global Interactive review / Report preview toolbar behavior from the sidebar and preserves all calculation, geometry, tendon import, and QA logic.
- Schema: `0.4.18-commercial-ui2-canvas-figure-normalization`.

## Retained COMMERCIAL.UI.1 updates


- Adds a global engineering Plotly figure system so all app graphs share one visual language.
- Adds one-source sidebar Figure view mode for every Plotly figure: Interactive review or Report preview.
- Interactive review shows zoom/pan/reset/camera tools across all figures; Report preview hides the toolbar for clean report screenshots.
- Centralizes Plotly layout/configuration in `visualization/figure_system.py` for consistent axes, grid, margins, typography, background, modebar behavior, and export options.
- Applies the shared figure system to load diagrams, response spectrum plots, section-property preview, tendon elevation, tendon plan, and tendon section overlay.
- Preserves existing calculation logic and tendon QA logic; this milestone is a presentation/system refactor only.
- Schema: `0.4.17-commercial-ui1-global-figure-system`.

## Retained COMMERCIAL.M3H.10 / M3H.11 updates
- Hides the Plotly modebar in the normal Tendon Section Overlay canvas so the viewport reads as a report figure rather than a debug chart.
- Refines B/D/CL/CG dimension labels with stronger white label boxes, cleaner guide offsets, and less intrusive centroid callouts.
- Further reduces grid/axis dominance with softer grid colors, quieter zero lines, and report-ready canvas background.
- Preserves the M3H.9 Dimension mode control: Clean, Full dimensions, and Hide dimensions. Clean remains the default.
- Keeps the existing tendon QA logic unchanged: external tendon points are still checked against the active inner void and section polygon.

## Retained commercial app foundations

- Concrete Section Pro-style workspace/sidebar/card layout and Plotly figure conventions.
- Explicit Project JSON load button with pending-load rerun workflow to avoid Streamlit widget-state crashes.
- DPT seismic database and EQ workflow.
- 1.3 Loads engines for SDL, LL+IM, LF/HF/CF, wind, CR/SH, and EQ.
- Coordinate-driven section properties with CSiBridge XLSX/CSV import.
- CSiBridge tendon layout import and tendon summary cards.

## Display formatting rules

- Force/load and moment/torsion resultants: no decimals.
- Stress in MPa: 2 decimals.
- Length in mm: no decimals.
- Length in m: 3 decimals.
- Area and section properties in m²/m³/m⁴: 3 decimals.
- Coefficients, DCR, utilization, and spectrum factors: 3 decimals unless a report table specifies otherwise.

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Test:

```bash
python -m compileall -q .
python -m pytest -q
```

## Traceability notes retained for regression tests

- 1.3.7 Wind Load uses EN 1991-1-4, Table 2.5, DPT 1311-50 wind basis, report-style figures, and FEA summary trace.
- DPT seismic database includes General Thailand and Bangkok Basin Zone 1–10 routing.
- AASHTO LRFD 2014 Table 3.10.7.1-1 is used as bridge R-factor guidance for substructure system recommendation.
- Full station-by-station FEA import remains pending.
- Coordinate-driven section properties use Structural Polygon 1 and Opening Polygon 1 from CSiBridge exports.

## COMMERCIAL.M3H.6
- Polishes Tendon Section Overlay with centerline-origin display, quick station buttons, family/all/hidden label modes, family-colored tendon markers, inside-void QA, minimum clearance to inner-boundary reporting, formatted selected-station tables, and hover details.


## COMMERCIAL.M3H.7 — Tendon Overlay Canvas Polish

- Reworked the Section Overlay page toward the Concrete Section Pro canvas style.
- Added a CANVAS header, Live Tendon Section Preview wording, external tendon QA pill, and report-ready figure caption.
- Cleaned Plotly legend labels to Concrete / Inner void / Centroid / tendon families.
- Added station annotation directly inside the figure for report/export readability.
- Kept selected-station QA in concise cards below the canvas and preserved the merged tendon QA table.


M3H.7.1 fixes the tendon overlay figure call to avoid TypeError when app.py and visualization/tendon_figures.py are updated out of sync.


## COMMERCIAL.M3H.8 — Tendon Canvas Card Layout Alignment

- Reworks the Tendon Section Overlay into a Concrete Section Pro-style contained canvas card.
- Wraps CANVAS header, note, custom legend strip, Plotly drawing viewport, caption, and QA summary cards in one bordered card container.
- Hides the default Plotly legend and replaces it with a compact report-style legend strip for Concrete, Inner void, Centroid, and T1–T8 tendon families.
- Converts the lower overlay summary into a canvas footer grid and adds explicit mm units / PASS wording to the clearance status.
- Keeps the existing engineering QA logic unchanged: tendon points are still checked against the active inner void and section polygon.


## COMMERCIAL.M3H.9 — Engineering Dimension Guide and Station Badge Polish

- Moves the selected-station text out of the section plot and into a dedicated canvas badge.
- Adds Dimension mode options: Clean, Full dimensions, and Hide dimensions.
- Makes Clean mode show only essential B, D, CL, and centroid guides.
- Makes Full dimensions add y_cg and y_t fiber dimensions without changing tendon QA logic.
- Reduces raw chart appearance using muted guide colors, external dimension offsets, tick marks, and lighter grid lines.


## COMMERCIAL.M3H.10 — Tendon Overlay Viewport and Report Figure Polish

- Hides the Plotly modebar in the normal Section Overlay canvas using a dedicated canvas Plotly config.
- Polishes B/D/CL/CG dimension labels and offsets so Clean mode reads more like an engineering drawing.
- Moves the CG callout away from the right plot edge and makes centroid guide lines lighter.
- Reduces grid and axis visual dominance for a cleaner report-ready viewport.
- Keeps tendon location QA, selected-station table data, and minimum-clearance logic unchanged.

## COMMERCIAL.M3H.11 — Interactive Review / Report View Mode

- Adds an explicit Figure view mode to the Tendon Section Overlay: Interactive review and Report preview.
- Interactive review shows the Plotly modebar so users can zoom, pan, reset, and export while checking tendon/void/clearance details.
- Report preview hides the Plotly modebar so the same canvas remains clean for report-ready figures.
- Tightens the default overlay viewport so the box-girder section opens larger and does not waste the canvas with excessive left/right/top/bottom blank space.
- Keeps tendon location QA, selected-station table data, minimum-clearance logic, and adopted tendon data unchanged.


## COMMERCIAL.UI.1 — Global Engineering Figure System

- Creates `visualization/figure_system.py` as the shared Plotly presentation layer for the whole app.
- Adds one global sidebar Figure view mode so all Plotly figures behave consistently instead of each page controlling toolbar behavior independently.
- Standardizes axes, grid intensity, font, margins, legend placement, background, hover behavior, and export configuration across load diagrams, spectrum plots, section drawings, and tendon figures.
- Section Overlay now reads the same global Figure view mode badge while preserving its Section Overlay-specific Dimension mode.
- Replaces local tendon-overlay-only modebar control with a one-source global figure setting.
- Keeps engineering calculations, tendon position transformation, tendon QA, clearance checks, and adopted data untouched.

## COMMERCIAL.UI.2 — Canvas Figure Normalization

- Normalizes Section Properties Preview, Tendon Elevation, and Tendon Plan into the shared commercial canvas figure-card system.
- Keeps all future graphs tied to the common engineering figure standard: canvas card, global Interactive review / Report preview behavior, custom legends, captions, and footer cards.
- Preserves calculation logic and adopted data while improving visual consistency across the tendon/section module.

## COMMERCIAL.BUGFIX.1 — Project Save/Load Section Data Persistence

- Fixes the blocker where previously saved project JSON files could reopen with missing section coordinate table, missing Section Preview, and adopted section properties reverting/appearing lost.
- Adds section coordinate migration for legacy saved-project locations into the canonical `section.coordinate_rows` source.
- Adds a single `serialize_project_json_bytes()` save path that runs schema migration before JSON export and records a section persistence summary in project metadata.
- Moves the sidebar Save Project JSON control so it is rendered after the active page has synced editable tables, preventing stale sidebar state from being downloaded.
- Bumps a project widget epoch and clears stale section editor/file-upload widget cache after JSON load so old empty data-editor state cannot overwrite newly loaded `section.coordinate_rows`.
- Adds a Section Data Gate on the Section Properties page showing coordinate rows, computed section availability, and adopted properties availability.
- Adds regression tests for save/load preservation, legacy coordinate migration, widget-cache reset, save ordering, and the Section Data Gate.
