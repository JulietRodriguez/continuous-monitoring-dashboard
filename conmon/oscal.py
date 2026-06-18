"""OSCAL 1.1.2 Assessment Results export.

Builds a NIST OSCAL `Assessment Results <https://pages.nist.gov/OSCAL/>`_
document from a :class:`~conmon.data.Dataset`. The output conforms to the
OSCAL 1.1.2 Assessment Results JSON model: a root ``assessment-results`` object
with ``metadata``, ``import-ap``, and one or more ``results`` containing
``observations``, ``risks``, and ``findings``.

UUIDs are derived deterministically (UUIDv5) from stable keys so repeated
exports of the same dataset are byte-stable and diff-friendly.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from conmon.data import Dataset

OSCAL_VERSION = "1.1.2"

# Stable namespace so derived UUIDs are reproducible across runs.
_NAMESPACE = uuid.UUID("6f3a9d1e-2b4c-4e8a-9f1d-7c2b5a0e3d44")

# Map our severity bands to OSCAL risk characterization scale values.
_RISK_SEVERITY = {
    "Critical": "high",
    "High": "high",
    "Medium": "moderate",
    "Low": "low",
}


def _uuid(*parts: str) -> str:
    """Return a deterministic UUIDv5 string from the given key parts."""

    return str(uuid.uuid5(_NAMESPACE, "::".join(parts)))


def _iso(dt: datetime | Any) -> str:
    """Return an OSCAL-compliant ISO-8601 timestamp with timezone offset."""

    if hasattr(dt, "to_pydatetime"):
        dt = dt.to_pydatetime()
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    # date -> midnight UTC
    return datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc).isoformat()


def _metadata(ds: Dataset) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "title": "Continuous Monitoring Assessment Results",
        "published": _iso(datetime(ds.as_of.year, ds.as_of.month, ds.as_of.day)),
        "last-modified": now,
        "version": "0.1.0",
        "oscal-version": OSCAL_VERSION,
        "roles": [
            {"id": "assessor", "title": "Security Control Assessor"},
            {"id": "isso", "title": "Information System Security Officer"},
        ],
        "parties": [
            {
                "uuid": _uuid("party", "csp"),
                "type": "organization",
                "name": "Cloud Service Provider (Demo)",
            }
        ],
    }


def _observations(ds: Dataset) -> list[dict[str, Any]]:
    """One observation per control family summarizing assessed status."""

    observations = []
    for _, row in ds.control_health.iterrows():
        fam = row["family_id"]
        observations.append(
            {
                "uuid": _uuid("observation", fam),
                "title": f"Control family {fam} assessment",
                "description": (
                    f"{row['family']} ({fam}): {row['pass']} pass, "
                    f"{row['partial']} partial, {row['fail']} fail "
                    f"of {row['total']} assessed (score {row['score']}%)."
                ),
                "methods": ["EXAMINE", "TEST"],
                "types": ["control-objective"],
                "collected": _iso(datetime(ds.as_of.year, ds.as_of.month, ds.as_of.day)),
            }
        )
    return observations


def _risks_and_findings(ds: Dataset) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build OSCAL risks and findings from the POA&M register."""

    risks: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    for _, item in ds.poam.iterrows():
        poam_id = item["poam_id"]
        risk_uuid = _uuid("risk", poam_id)
        status = "open" if item["status"] != "Risk Accepted" else "deviation-approved"

        risks.append(
            {
                "uuid": risk_uuid,
                "title": item["weakness"],
                "description": (
                    f"{item['weakness']} (control family {item['control_family']}, "
                    f"{item['severity']} severity)."
                ),
                "statement": (
                    f"Open {item['days_open']} day(s); scheduled completion "
                    f"{item['scheduled_completion'].date().isoformat()}."
                ),
                "status": status,
                "props": [
                    {
                        "name": "risk-score",
                        "value": str(item["risk_score"]),
                        "ns": "https://conmon.example/ns/oscal",
                    },
                    {
                        "name": "severity",
                        "value": _RISK_SEVERITY[item["severity"]],
                    },
                    {
                        "name": "days-open",
                        "value": str(item["days_open"]),
                        "ns": "https://conmon.example/ns/oscal",
                    },
                ],
                "characterizations": [
                    {
                        "origin": {
                            "actors": [
                                {"type": "assessment-platform", "actor-uuid": _uuid("platform")}
                            ]
                        },
                        "facets": [
                            {
                                "name": "impact",
                                "system": "https://conmon.example/ns/oscal",
                                "value": _RISK_SEVERITY[item["severity"]],
                            }
                        ],
                    }
                ],
                "deadline": _iso(item["scheduled_completion"]),
            }
        )

        findings.append(
            {
                "uuid": _uuid("finding", poam_id),
                "title": f"{poam_id}: {item['weakness']}",
                "description": (
                    f"POA&M {poam_id} for control family {item['control_family']} "
                    f"assigned to {item['owner']}; current status {item['status']}."
                ),
                "target": {
                    "type": "objective-id",
                    "target-id": item["control_family"],
                    "status": {
                        "state": "not-satisfied" if status == "open" else "satisfied",
                    },
                },
                "related-observations": [
                    {"observation-uuid": _uuid("observation", item["control_family"])}
                ],
                "related-risks": [{"risk-uuid": risk_uuid}],
            }
        )

    return risks, findings


def build_assessment_results(ds: Dataset) -> dict[str, Any]:
    """Return a complete OSCAL 1.1.2 Assessment Results document as a dict."""

    risks, findings = _risks_and_findings(ds)
    result = {
        "uuid": _uuid("result", ds.as_of.isoformat()),
        "title": "Continuous Monitoring Assessment Result",
        "description": (
            "Automated continuous-monitoring snapshot covering control health, "
            "vulnerability posture, and POA&M status."
        ),
        "start": _iso(datetime(ds.as_of.year, ds.as_of.month, ds.as_of.day)),
        "reviewed-controls": {
            "control-selections": [
                {
                    "description": "FedRAMP Moderate baseline (representative selection).",
                    "include-all": {},
                }
            ]
        },
        "observations": _observations(ds),
        "risks": risks,
        "findings": findings,
    }

    return {
        "assessment-results": {
            "uuid": _uuid("assessment-results", ds.as_of.isoformat()),
            "metadata": _metadata(ds),
            "import-ap": {"href": "./assessment-plan.oscal.json"},
            "results": [result],
        }
    }


def export_oscal(ds: Dataset, path: str | Path, indent: int = 2) -> Path:
    """Write the OSCAL Assessment Results JSON for ``ds`` to ``path``.

    Args:
        ds: The dataset to export.
        path: Destination file path.
        indent: JSON indentation.

    Returns:
        The :class:`pathlib.Path` written.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = build_assessment_results(ds)
    path.write_text(json.dumps(doc, indent=indent, default=str), encoding="utf-8")
    return path
