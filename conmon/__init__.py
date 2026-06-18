"""Continuous Monitoring Dashboard (ConMon).

A FedRAMP-style continuous monitoring simulation that tracks control health,
POA&M aging, vulnerability trends, and compliance drift over time.
"""

from conmon.models import (
    CONTROL_FAMILIES,
    SEVERITIES,
    ControlFamily,
    Severity,
)

__version__ = "0.1.0"

__all__ = [
    "CONTROL_FAMILIES",
    "SEVERITIES",
    "ControlFamily",
    "Severity",
    "__version__",
]
