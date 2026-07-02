# Segmental Box Girder Pro — COMMERCIAL.LOADS.14

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
- COMMERCIAL.LOADS.14

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

COMMERCIAL.LOADS.14 focus:
- Fix Loads subpage state consistency so header, sidebar, in-page selector, and active content agree after selecting 3.7 Wind.
- Remove the confusing disabled manual wind-group dropdown when province lookup governs.
- Keep DPT province lookup as the source for Group/V50/TF/vb0 recommendations unless Manual group selection is chosen.
- Add app-drawn overlay labels on the DPT wind map so Group 1, 2, 3, 4A, and 4B remain readable inside the card.
- Highlight the selected wind group on the map.
- Move Adopt / manual vb0 override controls directly under the recommendation cards.
- Update schema/status wording to the current milestone.
- Preserve existing DPT/EN wind calculation logic and one-source trace.
