"""Domain models and constants for the continuous monitoring dashboard.

These describe the NIST SP 800-53 Rev 5 control families, vulnerability
severities, and the canonical FedRAMP-style risk bands used throughout the
data layer, metrics, and OSCAL export.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- NIST SP 800-53 Rev 5 control families -------------------------------- #


@dataclass(frozen=True)
class ControlFamily:
    """A NIST SP 800-53 control family.

    Attributes:
        id: Two-letter family identifier (e.g. ``AC``).
        name: Human-readable family name.
        baseline_controls: Number of controls assessed for this family in the
            simulated FedRAMP Moderate baseline.
    """

    id: str
    name: str
    baseline_controls: int


# Ordered to match the NIST SP 800-53 Rev 5 catalog. The control counts are a
# representative FedRAMP Moderate selection used for the simulation.
CONTROL_FAMILIES: tuple[ControlFamily, ...] = (
    ControlFamily("AC", "Access Control", 25),
    ControlFamily("AT", "Awareness and Training", 6),
    ControlFamily("AU", "Audit and Accountability", 16),
    ControlFamily("CA", "Assessment, Authorization, and Monitoring", 9),
    ControlFamily("CM", "Configuration Management", 14),
    ControlFamily("CP", "Contingency Planning", 13),
    ControlFamily("IA", "Identification and Authentication", 14),
    ControlFamily("IR", "Incident Response", 10),
    ControlFamily("MA", "Maintenance", 6),
    ControlFamily("MP", "Media Protection", 8),
    ControlFamily("PE", "Physical and Environmental Protection", 18),
    ControlFamily("PL", "Planning", 9),
    ControlFamily("PS", "Personnel Security", 8),
    ControlFamily("RA", "Risk Assessment", 10),
    ControlFamily("SA", "System and Services Acquisition", 22),
    ControlFamily("SC", "System and Communications Protection", 30),
    ControlFamily("SI", "System and Information Integrity", 20),
    ControlFamily("SR", "Supply Chain Risk Management", 11),
)

CONTROL_FAMILY_IDS: tuple[str, ...] = tuple(f.id for f in CONTROL_FAMILIES)


# --- Vulnerability severities --------------------------------------------- #


@dataclass(frozen=True)
class Severity:
    """A vulnerability/finding severity band.

    Attributes:
        name: Severity label.
        weight: Relative risk weight used in scoring (higher is worse).
        sla_days: FedRAMP remediation SLA in calendar days.
        color: Hex color used for charts.
    """

    name: str
    weight: int
    sla_days: int
    color: str


# FedRAMP remediation timeframes: High 30 days, Moderate 90 days, Low 180 days.
# "Critical" is carried separately for vendor scanners that distinguish it.
SEVERITIES: tuple[Severity, ...] = (
    Severity("Critical", weight=40, sla_days=15, color="#e5484d"),
    Severity("High", weight=20, sla_days=30, color="#f5a524"),
    Severity("Medium", weight=8, sla_days=90, color="#3b82f6"),
    Severity("Low", weight=2, sla_days=180, color="#22c55e"),
)

SEVERITY_NAMES: tuple[str, ...] = tuple(s.name for s in SEVERITIES)

# Control assessment statuses.
CONTROL_STATUSES: tuple[str, ...] = ("Pass", "Partial", "Fail")

# POA&M lifecycle statuses.
POAM_STATUSES: tuple[str, ...] = ("Open", "In Progress", "Risk Accepted")


def severity_by_name(name: str) -> Severity:
    """Return the :class:`Severity` whose name matches ``name``.

    Raises:
        KeyError: if no severity matches.
    """

    for severity in SEVERITIES:
        if severity.name == name:
            return severity
    raise KeyError(f"Unknown severity: {name!r}")


def control_family_by_id(family_id: str) -> ControlFamily:
    """Return the :class:`ControlFamily` whose id matches ``family_id``.

    Raises:
        KeyError: if no family matches.
    """

    for family in CONTROL_FAMILIES:
        if family.id == family_id:
            return family
    raise KeyError(f"Unknown control family: {family_id!r}")
