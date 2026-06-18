"""Tests for the OSCAL 1.1.2 Assessment Results export."""

from __future__ import annotations

import json
import uuid

from conmon.oscal import (
    OSCAL_VERSION,
    build_assessment_results,
    export_oscal,
)


def _strip_volatile(doc: dict) -> dict:
    """Return a copy of the doc with the volatile last-modified removed."""

    clone = json.loads(json.dumps(doc))
    clone["assessment-results"]["metadata"].pop("last-modified", None)
    return clone


def test_top_level_structure(dataset):
    doc = build_assessment_results(dataset)
    assert set(doc) == {"assessment-results"}
    ar = doc["assessment-results"]
    assert set(["uuid", "metadata", "import-ap", "results"]).issubset(ar)
    assert ar["metadata"]["oscal-version"] == OSCAL_VERSION
    assert "import-ap" in ar and "href" in ar["import-ap"]


def test_results_contain_findings_risks_observations(dataset):
    ar = build_assessment_results(dataset)["assessment-results"]
    result = ar["results"][0]
    assert len(result["findings"]) == len(dataset.poam)
    assert len(result["risks"]) == len(dataset.poam)
    assert len(result["observations"]) == len(dataset.control_health)
    assert "control-selections" in result["reviewed-controls"]


def test_all_uuids_are_valid(dataset):
    ar = build_assessment_results(dataset)["assessment-results"]
    result = ar["results"][0]
    candidates = [ar["uuid"], result["uuid"]]
    candidates += [f["uuid"] for f in result["findings"]]
    candidates += [r["uuid"] for r in result["risks"]]
    candidates += [o["uuid"] for o in result["observations"]]
    for value in candidates:
        uuid.UUID(value)  # raises if invalid


def test_findings_reference_existing_risks_and_observations(dataset):
    result = build_assessment_results(dataset)["assessment-results"]["results"][0]
    risk_ids = {r["uuid"] for r in result["risks"]}
    obs_ids = {o["uuid"] for o in result["observations"]}
    for finding in result["findings"]:
        assert finding["related-risks"][0]["risk-uuid"] in risk_ids
        assert finding["related-observations"][0]["observation-uuid"] in obs_ids


def test_uuids_stable_across_runs(dataset):
    from conmon.data import generate_dataset

    a = _strip_volatile(build_assessment_results(dataset))
    b = _strip_volatile(build_assessment_results(generate_dataset(seed=42)))
    assert a == b


def test_export_writes_valid_json(dataset, tmp_path):
    out = tmp_path / "ar.oscal.json"
    written = export_oscal(dataset, out)
    assert written == out
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["assessment-results"]["metadata"]["oscal-version"] == OSCAL_VERSION


def test_risk_props_include_score(dataset):
    result = build_assessment_results(dataset)["assessment-results"]["results"][0]
    first = result["risks"][0]
    prop_names = {p["name"] for p in first["props"]}
    assert {"risk-score", "severity", "days-open"}.issubset(prop_names)
