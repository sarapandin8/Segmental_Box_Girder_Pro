"""Report-driven workspace definitions for Segmental Box Girder Pro.

UI labels intentionally omit the word "Chapter" while keeping report numbering
for traceability to BG40 R10.
"""

from __future__ import annotations

WORKSPACES = [
    {
        "id": "dashboard",
        "label": "Project Dashboard",
        "title": "Project Dashboard",
        "subpages": ["Overview", "Workflow Status", "Governing Results", "Report Readiness"],
    },
    {
        "id": "criteria_loads",
        "label": "1 Criteria / Loads",
        "title": "1 Design Criteria, Design Loads and Load Combinations",
        "subpages": ["1.1 Standards", "1.2 Materials", "1.3 Loads", "1.4 Combinations", "QA / Report Preview"],
    },
    {
        "id": "bridge_model",
        "label": "2 Bridge Model",
        "title": "2 Structural System and Analysis Model",
        "subpages": ["2.1 Bridge Description", "2.2 FEA Model", "2.3 Supports", "2.4 Tendon Layout", "QA / Report Preview"],
    },
    {
        "id": "section_properties",
        "label": "3 Section Properties",
        "title": "3 Section Properties",
        "subpages": ["3.1 Cross-Section", "3.2 FEA Properties", "3.3 Consistency Checks", "QA / Report Preview"],
    },
    {
        "id": "prestress_losses",
        "label": "4 Prestress Losses",
        "title": "4 Prestress Losses",
        "subpages": ["4.1 General", "4.2 Friction", "4.3 Anchor Set", "4.4 Elastic Shortening", "4.5 Creep / Shrinkage", "4.6 Effective Prestress", "QA / Report Preview"],
    },
    {
        "id": "fea_results",
        "label": "5 FEA Results",
        "title": "5 Analysis Results",
        "subpages": ["5.1 Data Hub", "5.2 ULS Envelope", "5.3 SLS Envelope", "QA / Report Preview"],
    },
    {
        "id": "uls_flexure",
        "label": "6 ULS Flexure",
        "title": "6 ULS Flexural Design",
        "subpages": ["6.1 Basis", "6.2 Capacity", "6.3 Span Results", "QA / Report Preview"],
    },
    {
        "id": "uls_shear_torsion",
        "label": "7 ULS Shear / Torsion",
        "title": "7 ULS Shear and Torsion Design",
        "subpages": ["7.1 Basis", "7.2 Critical Section", "7.3 Shear Check", "7.4 Torsion Check", "7.5 Reinforcement", "QA / Report Preview"],
    },
    {
        "id": "sls_stress",
        "label": "8 SLS Stress",
        "title": "8 SLS Stress Check",
        "subpages": ["8.1 Basis", "8.2 Transfer", "8.3 Final", "QA / Report Preview"],
    },
    {
        "id": "deflection",
        "label": "9 Deflection",
        "title": "9 Deflection Check",
        "subpages": ["9.1 Criteria", "9.2 Camber", "9.3 Live Load Deflection", "QA / Report Preview"],
    },
    {
        "id": "report_qa",
        "label": "Report / QA",
        "title": "Report / QA",
        "subpages": ["QA Summary", "Validation Issues", "Report Preview", "Export"],
    },
]

WORKSPACE_BY_LABEL = {w["label"]: w for w in WORKSPACES}
WORKSPACE_BY_ID = {w["id"]: w for w in WORKSPACES}
WORKSPACE_LABELS = [w["label"] for w in WORKSPACES]


def get_workspace(label: str) -> dict:
    return WORKSPACE_BY_LABEL.get(label, WORKSPACES[0])
