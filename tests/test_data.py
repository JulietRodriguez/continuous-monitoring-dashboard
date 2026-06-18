"""Tests for the mock-data generation layer."""

from __future__ import annotations

from datetime import date

import pandas as pd

from conmon.data import DEFAULT_AS_OF, WINDOW_WEEKS, generate_dataset
from conmon.models import CONTROL_FAMILIES, POAM_STATUSES, SEVERITY_NAMES


def test_dataset_is_deterministic():
    a = generate_dataset(seed=7)
    b = generate_dataset(seed=7)
    pd.testing.assert_frame_equal(a.poam, b.poam)
    pd.testing.assert_frame_equal(a.control_health, b.control_health)
    pd.testing.assert_frame_equal(a.compliance_trend, b.compliance_trend)


def test_different_seeds_differ():
    a = generate_dataset(seed=1)
    b = generate_dataset(seed=2)
    assert not a.poam.equals(b.poam)


def test_compliance_trend_spans_window(dataset):
    trend = dataset.compliance_trend
    assert len(trend) == WINDOW_WEEKS
    assert trend["date"].is_monotonic_increasing
    # Six months of weekly snapshots ending on the reporting date.
    assert trend["date"].iloc[-1].date() == DEFAULT_AS_OF
    span_days = (trend["date"].iloc[-1] - trend["date"].iloc[0]).days
    assert 170 <= span_days <= 185


def test_compliance_scores_in_range(dataset):
    s = dataset.compliance_trend["compliance_score"]
    assert s.between(0, 100).all()


def test_trend_endpoint_matches_overall_score(dataset):
    assert dataset.compliance_trend["compliance_score"].iloc[-1] == dataset.overall_score


def test_control_health_counts_sum_to_total(dataset):
    ch = dataset.control_health
    assert len(ch) == len(CONTROL_FAMILIES)
    assert (ch["pass"] + ch["partial"] + ch["fail"] == ch["total"]).all()
    assert (ch[["pass", "partial", "fail"]] >= 0).all().all()


def test_control_health_family_ids_unique(dataset):
    ids = dataset.control_health["family_id"]
    assert ids.is_unique
    assert set(ids) == {f.id for f in CONTROL_FAMILIES}


def test_vuln_trend_has_all_severities(dataset):
    vt = dataset.vuln_trend
    for name in SEVERITY_NAMES:
        assert name in vt.columns
        assert (vt[name] >= 0).all()
    assert len(vt) == WINDOW_WEEKS


def test_poam_register_shape_and_invariants(dataset):
    poam = dataset.poam
    assert len(poam) > 0
    assert poam["poam_id"].is_unique
    assert set(poam["status"]).issubset(set(POAM_STATUSES))
    assert set(poam["severity"]).issubset(set(SEVERITY_NAMES))
    assert (poam["days_open"] >= 0).all()
    assert poam["risk_score"].between(0, 100).all()


def test_poam_past_due_consistent_with_dates(dataset):
    poam = dataset.poam
    expected = poam["scheduled_completion"].dt.date < dataset.as_of
    assert (poam["past_due"] == expected).all()


def test_remediation_within_sla_flag(dataset):
    rem = dataset.remediation
    assert (rem["days_to_remediate"] >= 1).all()
    assert (rem["closed"] >= rem["opened"]).all()


def test_custom_as_of_date():
    custom = date(2025, 12, 31)
    ds = generate_dataset(as_of=custom)
    assert ds.as_of == custom
    assert ds.compliance_trend["date"].iloc[-1].date() == custom
