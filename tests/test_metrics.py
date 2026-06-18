"""Tests for the derived-metrics layer."""

from __future__ import annotations

from conmon import metrics
from conmon.metrics import AGING_BUCKETS


def test_overall_score_matches_property(dataset):
    assert metrics.overall_compliance_score(dataset) == dataset.overall_score


def test_overall_score_in_range(dataset):
    assert 0 <= metrics.overall_compliance_score(dataset) <= 100


def test_control_status_totals_sum_to_assessed(dataset):
    totals = metrics.control_status_totals(dataset)
    assert sum(totals.values()) == int(dataset.control_health["total"].sum())
    assert set(totals) == {"Pass", "Partial", "Fail"}


def test_poam_aging_buckets_complete(dataset):
    aging = metrics.poam_aging(dataset)
    assert list(aging["bucket"]) == [b[0] for b in AGING_BUCKETS]
    # Sum of buckets equals number of open items.
    open_items = dataset.poam[dataset.poam["status"] != "Risk Accepted"]
    assert aging["count"].sum() == len(open_items)


def test_poam_aging_open_only_flag(dataset):
    all_items = metrics.poam_aging(dataset, open_only=False)
    assert all_items["count"].sum() == len(dataset.poam)


def test_mttr_has_all_severities_in_order(dataset):
    df = metrics.mean_time_to_remediate(dataset)
    assert list(df["severity"]) == ["Critical", "High", "Medium", "Low"]
    assert (df["mttr_days"] > 0).all()
    assert df["sla_compliance"].between(0, 100).all()


def test_critical_mttr_below_low_mttr(dataset):
    df = metrics.mean_time_to_remediate(dataset).set_index("severity")
    # Higher severity should be remediated faster on average.
    assert df.loc["Critical", "mttr_days"] < df.loc["Low", "mttr_days"]


def test_overall_mttr_positive(dataset):
    assert metrics.overall_mttr(dataset) > 0


def test_vuln_current_breakdown_matches_last_row(dataset):
    breakdown = metrics.vuln_current_breakdown(dataset)
    last = dataset.vuln_trend.iloc[-1]
    for name, value in breakdown.items():
        assert value == int(last[name])


def test_top_risks_sorted_and_open(dataset):
    top = metrics.top_risks(dataset, n=5)
    assert len(top) <= 5
    assert top["risk_score"].is_monotonic_decreasing
    assert (top["status"] != "Risk Accepted").all()


def test_poam_summary_consistency(dataset):
    s = metrics.poam_summary(dataset)
    assert s["total"] == len(dataset.poam)
    assert s["open"] + s["risk_accepted"] == s["total"]
    assert s["past_due"] <= s["open"]


def test_compliance_drift_sign(dataset):
    drift = metrics.compliance_drift(dataset)
    assert isinstance(drift, float)
