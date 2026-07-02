# Segmental Box Girder Pro — COMMERCIAL.LOADS.13

This baseline carries forward the previously accepted commercial milestones and standards:
- COMMERCIAL.M3H.8
- COMMERCIAL.M3H.9
- COMMERCIAL.M3H.10
- COMMERCIAL.M3H.11
- COMMERCIAL.UI.1
- COMMERCIAL.UI.2
- COMMERCIAL.M4.1A
- COMMERCIAL.M4.1B
- COMMERCIAL.M4.1C
- COMMERCIAL.M4.1D
- COMMERCIAL.M4.1E
- COMMERCIAL.CODE.1
- COMMERCIAL.LOADS.1
- COMMERCIAL.LOADS.2
- COMMERCIAL.LOADS.3
- COMMERCIAL.LOADS.4
- COMMERCIAL.LOADS.5
- COMMERCIAL.LOADS.6
- COMMERCIAL.LOADS.7
- COMMERCIAL.LOADS.8
- COMMERCIAL.LOADS.9
- COMMERCIAL.LOADS.10
- COMMERCIAL.LOADS.11
- COMMERCIAL.LOADS.12
- COMMERCIAL.LOADS.13

Display formatting rules
- Retain the commercial engineering figure system and canvas-card presentation.
- Shared figure helpers remain under `visualization/figure_system.py`.
- New figures must follow the existing UI.1 / UI.2 standards.

Retained basis / reference notes
- 1.3.7 Wind Load
- EN 1991-1-4
- Table 2.5
- DPT seismic database
- Bangkok Basin Zone 1–10
- AASHTO LRFD 2014 Table 3.10.7.1-1
- Full station-by-station FEA import remains pending
- Coordinate-driven section properties
- AASHTO LRFD Bridge Design Specifications, 9th Edition, 2020
- Structural Polygon 1
- Opening Polygon 1
- Orthographic Isometric

Current milestone focus:
- Move wind report/reference figures from a separate Figures tab into compact Input Assistant cards.
- Add a DPT wind group lookup table next to the map-driven group selection workflow.
- Keep DPT/EN wind recommendation logic and WS/WS+WL calculation logic unchanged.


COMMERCIAL.LOADS.13 focus:
- Add a DPT 1311-50 / 1312-50 province-to-wind-group database.
- Let users select project province and district/area condition; the app recommends Group 1/2/3/4A/4B automatically.
- Preserve manual group selection for special project requirements.
- Preserve existing DPT/EN wind calculation logic and one-source trace.
