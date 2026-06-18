"""Deterministic mock-data generation for the ConMon dashboard.

All data is synthetic but internally consistent and reproducible: given the
same ``seed`` and ``as_of`` date the generated dataset is identical, which keeps
the dashboard visuals stable and lets the test-suite assert on exact shapes and
invariants.

The public entry point is :func:`generate_dataset`, which returns a
:class:`Dataset` bundling every table the dashboard and OSCAL export consume.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from conmon.models import (
    CONTROL_FAMILIES,
    POAM_STATUSES,
    SEVERITIES,
    severity_by_name,
)

# The simulated "now". Fixed so demo visuals and the test-suite are stable.
DEFAULT_AS_OF = date(2026, 6, 17)

# Length of the continuous-monitoring window shown across the dashboard.
WINDOW_WEEKS = 26  # ~6 months of weekly snapshots.

# A small roster of system owners for POA&M assignment.
OWNERS: tuple[str, ...] = (
    "A. Okafor (ISSO)",
    "M. Chen (SysAdmin)",
    "R. Delgado (DevSecOps)",
    "S. Patel (Cloud Eng)",
    "T. Nakamura (DBA)",
    "L. Brooks (Network)",
    "J. Rivera (AppSec)",
)

# Representative weakness titles keyed loosely by control family.
_WEAKNESS_TEMPLATES: tuple[tuple[str, str], ...] = (
    ("AC", "Stale privileged account not disabled within policy window"),
    ("AC", "Role-based access review overdue for production tenant"),
    ("AU", "Audit log retention below 90-day baseline on legacy host"),
    ("AU", "Log forwarding gap from container runtime to SIEM"),
    ("CM", "Unapproved configuration drift on web tier AMI"),
    ("CM", "Baseline hardening deviation on bastion host"),
    ("IA", "MFA not enforced for break-glass service account"),
    ("IA", "Password policy non-compliant on internal directory"),
    ("RA", "Authenticated vulnerability scan coverage gap"),
    ("SC", "TLS 1.0/1.1 still negotiable on edge load balancer"),
    ("SC", "Missing FIPS-validated module on data-in-transit path"),
    ("SI", "Critical OS patch past remediation SLA on app node"),
    ("SI", "Endpoint malware definitions stale on build runner"),
    ("CP", "Backup restoration test not performed this quarter"),
    ("IR", "Incident response tabletop exercise overdue"),
    ("SA", "Third-party library with known CVE in dependency tree"),
    ("SR", "Supplier SBOM not collected for new microservice"),
    ("PE", "Visitor access log incomplete at colocation facility"),
)


@dataclass(frozen=True)
class Dataset:
    """Bundle of every table consumed by the dashboard and OSCAL export.

    Attributes:
        as_of: The reporting "now" date.
        compliance_trend: Weekly overall compliance score and finding counts.
        control_health: Per-family Pass/Partial/Fail snapshot.
        vuln_trend: Weekly open-vulnerability counts by severity.
        remediation: Closed-finding records used for mean-time-to-remediate.
        poam: Open POA&M register.
    """

    as_of: date
    compliance_trend: pd.DataFrame
    control_health: pd.DataFrame
    vuln_trend: pd.DataFrame
    remediation: pd.DataFrame
    poam: pd.DataFrame

    @property
    def overall_score(self) -> float:
        """Controls-weighted overall compliance score (0-100).

        Equal to the most recent point on :attr:`compliance_trend`, which is
        pinned to the control-health-derived score during generation.
        """

        ch = self.control_health
        earned = (ch["pass"] + 0.5 * ch["partial"]).sum()
        return round(float(earned / ch["total"].sum() * 100), 1)

    @property
    def critical_open(self) -> int:
        """Count of open POA&M items at Critical or High severity."""

        open_items = self.poam[self.poam["status"] != "Risk Accepted"]
        return int(open_items["severity"].isin(["Critical", "High"]).sum())


def _week_index(as_of: date, weeks: int) -> list[date]:
    """Return ``weeks`` weekly snapshot dates ending on ``as_of`` (ascending)."""

    start = as_of - timedelta(weeks=weeks - 1)
    return [start + timedelta(weeks=i) for i in range(weeks)]


def _compliance_trend(
    rng: np.random.Generator, weeks: list[date], anchor_score: float
) -> pd.DataFrame:
    """Build the weekly overall-compliance trend with a realistic dip/recovery.

    The final snapshot is pinned to ``anchor_score`` (the control-health-derived
    score) so the headline KPI and the end of the trend line agree.
    """

    n = len(weeks)
    t = np.linspace(0, 1, n)
    # Start ~88%, dip near the middle (audit findings), recover toward today.
    base = 88 + (anchor_score - 88) * t - 5 * np.sin(np.pi * t)
    noise = rng.normal(0, 0.6, n)
    score = np.clip(base + noise, 70, 99).round(1)
    score[-1] = round(anchor_score, 1)  # pin endpoint to headline score

    # Critical findings shrink over time as remediation outpaces discovery.
    critical = np.clip((9 - 6 * t + rng.normal(0, 0.8, n)).round(), 0, None).astype(int)
    open_poam = np.clip((48 - 18 * t + rng.normal(0, 2.0, n)).round(), 0, None).astype(int)

    return pd.DataFrame(
        {
            "date": pd.to_datetime(weeks),
            "compliance_score": score,
            "critical_findings": critical,
            "open_poam": open_poam,
        }
    )


def _control_health(rng: np.random.Generator) -> pd.DataFrame:
    """Build the per-family Pass/Partial/Fail snapshot."""

    rows = []
    for fam in CONTROL_FAMILIES:
        total = fam.baseline_controls
        # Most controls pass; a minority are partial or failing.
        pass_rate = float(np.clip(rng.normal(0.84, 0.08), 0.55, 0.99))
        partial_rate = float(np.clip(rng.normal(0.10, 0.04), 0.0, 0.30))
        n_pass = int(round(total * pass_rate))
        n_partial = int(round(total * partial_rate))
        n_pass = min(n_pass, total)
        n_partial = min(n_partial, total - n_pass)
        n_fail = total - n_pass - n_partial

        score = round((n_pass + 0.5 * n_partial) / total * 100, 1)
        rows.append(
            {
                "family_id": fam.id,
                "family": fam.name,
                "total": total,
                "pass": n_pass,
                "partial": n_partial,
                "fail": n_fail,
                "score": score,
            }
        )
    return pd.DataFrame(rows)


def _vuln_trend(rng: np.random.Generator, weeks: list[date]) -> pd.DataFrame:
    """Build weekly open-vulnerability counts by severity (declining trend)."""

    n = len(weeks)
    t = np.linspace(0, 1, n)
    starts = {"Critical": 14, "High": 38, "Medium": 95, "Low": 140}
    ends = {"Critical": 2, "High": 12, "Medium": 60, "Low": 110}

    data: dict[str, object] = {"date": pd.to_datetime(weeks)}
    for sev in SEVERITIES:
        lo, hi = ends[sev.name], starts[sev.name]
        curve = hi + (lo - hi) * t
        noise = rng.normal(0, max(1.0, hi * 0.05), n)
        data[sev.name] = np.clip((curve + noise).round(), 0, None).astype(int)
    return pd.DataFrame(data)


def _remediation(rng: np.random.Generator, as_of: date) -> pd.DataFrame:
    """Build closed-finding records used for mean-time-to-remediate."""

    rows = []
    counts = {"Critical": 30, "High": 70, "Medium": 120, "Low": 90}
    for sev in SEVERITIES:
        # Remediation time scales with SLA but with realistic spread/overruns.
        mean_days = sev.sla_days * 0.7
        days = np.clip(
            rng.normal(mean_days, mean_days * 0.45, counts[sev.name]).round(),
            1,
            sev.sla_days * 2.5,
        ).astype(int)
        for d in days:
            closed = as_of - timedelta(days=int(rng.integers(0, 175)))
            opened = closed - timedelta(days=int(d))
            rows.append(
                {
                    "severity": sev.name,
                    "opened": pd.Timestamp(opened),
                    "closed": pd.Timestamp(closed),
                    "days_to_remediate": int(d),
                    "within_sla": bool(d <= sev.sla_days),
                }
            )
    df = pd.DataFrame(rows)
    return df.sort_values("closed").reset_index(drop=True)


def _poam(rng: np.random.Generator, as_of: date) -> pd.DataFrame:
    """Build the open POA&M register."""

    n_items = 42
    rows = []
    severity_pool = ["Critical"] * 3 + ["High"] * 10 + ["Medium"] * 18 + ["Low"] * 11
    rng.shuffle(severity_pool)

    for i in range(n_items):
        sev_name = severity_pool[i % len(severity_pool)]
        sev = severity_by_name(sev_name)
        fam_id, title = _WEAKNESS_TEMPLATES[int(rng.integers(len(_WEAKNESS_TEMPLATES)))]

        # Age weighted so some items are well past their SLA.
        days_open = int(np.clip(rng.gamma(shape=2.0, scale=sev.sla_days * 0.5), 3, 360))
        opened = as_of - timedelta(days=days_open)
        scheduled = opened + timedelta(days=sev.sla_days)
        past_due = as_of > scheduled

        status = str(rng.choice(POAM_STATUSES, p=[0.45, 0.45, 0.10]))

        # Risk score: severity weight amplified by age past SLA, capped at 100.
        overdue_factor = max(0.0, (days_open - sev.sla_days) / max(sev.sla_days, 1))
        risk_score = int(min(100, round(sev.weight * (1.0 + 0.9 * overdue_factor) + 8)))

        rows.append(
            {
                "poam_id": f"POAM-2026-{i + 1:03d}",
                "weakness": title,
                "control_family": fam_id,
                "severity": sev_name,
                "status": status,
                "owner": str(rng.choice(OWNERS)),
                "opened": pd.Timestamp(opened),
                "scheduled_completion": pd.Timestamp(scheduled),
                "days_open": days_open,
                "past_due": bool(past_due),
                "risk_score": risk_score,
            }
        )

    df = pd.DataFrame(rows)
    return df.sort_values("risk_score", ascending=False).reset_index(drop=True)


def generate_dataset(seed: int = 42, as_of: date | None = None) -> Dataset:
    """Generate a complete, reproducible :class:`Dataset`.

    Args:
        seed: Seed for the random generator; identical seeds yield identical data.
        as_of: Reporting "now"; defaults to :data:`DEFAULT_AS_OF`.

    Returns:
        A fully populated :class:`Dataset`.
    """

    as_of = as_of or DEFAULT_AS_OF
    rng = np.random.default_rng(seed)
    weeks = _week_index(as_of, WINDOW_WEEKS)

    # Control health is generated first so the trend line can be pinned to the
    # same headline score the KPI cards display.
    control_health = _control_health(rng)
    earned = (control_health["pass"] + 0.5 * control_health["partial"]).sum()
    anchor = round(float(earned / control_health["total"].sum() * 100), 1)

    return Dataset(
        as_of=as_of,
        compliance_trend=_compliance_trend(rng, weeks, anchor),
        control_health=control_health,
        vuln_trend=_vuln_trend(rng, weeks),
        remediation=_remediation(rng, as_of),
        poam=_poam(rng, as_of),
    )
