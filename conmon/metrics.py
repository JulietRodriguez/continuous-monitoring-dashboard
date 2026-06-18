"""Derived metrics computed from a :class:`~conmon.data.Dataset`.

These functions are pure (no Streamlit / no plotting) so they can be unit
tested in isolation and reused by both the dashboard and the OSCAL export.
"""

from __future__ import annotations

import pandas as pd

from conmon.data import Dataset
from conmon.models import SEVERITY_NAMES

# POA&M aging buckets (days open) used in the Executive Summary chart.
AGING_BUCKETS: tuple[tuple[str, int, int], ...] = (
    ("0-30", 0, 30),
    ("31-60", 31, 60),
    ("61-90", 61, 90),
    ("91-180", 91, 180),
    ("180+", 181, 10_000),
)


def overall_compliance_score(ds: Dataset) -> float:
    """Return the controls-weighted overall compliance score (0-100)."""

    ch = ds.control_health
    earned = (ch["pass"] + 0.5 * ch["partial"]).sum()
    total = ch["total"].sum()
    return round(float(earned / total * 100), 1)


def compliance_drift(ds: Dataset, weeks: int = 4) -> float:
    """Return the change in compliance score over the last ``weeks`` snapshots.

    Positive means improving, negative means drifting out of compliance.
    """

    trend = ds.compliance_trend["compliance_score"]
    if len(trend) <= weeks:
        return round(float(trend.iloc[-1] - trend.iloc[0]), 1)
    return round(float(trend.iloc[-1] - trend.iloc[-(weeks + 1)]), 1)


def control_status_totals(ds: Dataset) -> dict[str, int]:
    """Return total Pass/Partial/Fail control counts across all families."""

    ch = ds.control_health
    return {
        "Pass": int(ch["pass"].sum()),
        "Partial": int(ch["partial"].sum()),
        "Fail": int(ch["fail"].sum()),
    }


def poam_aging(ds: Dataset, open_only: bool = True) -> pd.DataFrame:
    """Return POA&M counts bucketed by age.

    Args:
        ds: The dataset.
        open_only: Exclude ``Risk Accepted`` items when ``True``.

    Returns:
        DataFrame with ``bucket`` and ``count`` columns in age order.
    """

    poam = ds.poam
    if open_only:
        poam = poam[poam["status"] != "Risk Accepted"]

    rows = []
    for label, lo, hi in AGING_BUCKETS:
        count = int(((poam["days_open"] >= lo) & (poam["days_open"] <= hi)).sum())
        rows.append({"bucket": label, "count": count})
    return pd.DataFrame(rows)


def mean_time_to_remediate(ds: Dataset) -> pd.DataFrame:
    """Return mean-time-to-remediate (days) per severity with SLA-compliance.

    Returns:
        DataFrame indexed implicitly with columns ``severity``, ``mttr_days``,
        ``count`` and ``sla_compliance`` (fraction closed within SLA).
    """

    rem = ds.remediation
    grp = rem.groupby("severity")
    out = grp.agg(
        mttr_days=("days_to_remediate", "mean"),
        count=("days_to_remediate", "size"),
        sla_compliance=("within_sla", "mean"),
    ).reset_index()
    out["mttr_days"] = out["mttr_days"].round(1)
    out["sla_compliance"] = (out["sla_compliance"] * 100).round(1)

    # Keep canonical severity ordering (Critical -> Low).
    order = {name: i for i, name in enumerate(SEVERITY_NAMES)}
    out = out.sort_values("severity", key=lambda s: s.map(order)).reset_index(drop=True)
    return out


def overall_mttr(ds: Dataset) -> float:
    """Return the overall mean-time-to-remediate in days across all findings."""

    return round(float(ds.remediation["days_to_remediate"].mean()), 1)


def vuln_current_breakdown(ds: Dataset) -> dict[str, int]:
    """Return the most recent open-vulnerability count per severity."""

    latest = ds.vuln_trend.iloc[-1]
    return {name: int(latest[name]) for name in SEVERITY_NAMES}


def top_risks(ds: Dataset, n: int = 10) -> pd.DataFrame:
    """Return the ``n`` highest-risk open POA&M items."""

    poam = ds.poam[ds.poam["status"] != "Risk Accepted"]
    return poam.sort_values("risk_score", ascending=False).head(n).reset_index(drop=True)


def poam_summary(ds: Dataset) -> dict[str, int]:
    """Return headline POA&M counts for KPI cards."""

    poam = ds.poam
    open_items = poam[poam["status"] != "Risk Accepted"]
    return {
        "total": int(len(poam)),
        "open": int(len(open_items)),
        "past_due": int(open_items["past_due"].sum()),
        "risk_accepted": int((poam["status"] == "Risk Accepted").sum()),
    }
