"""Command-line entry point for exporting OSCAL Assessment Results.

Usage::

    conmon-export-oscal --out exports/assessment-results.oscal.json --seed 42
    python -m conmon.cli --out exports/ar.json
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

from conmon.data import DEFAULT_AS_OF, generate_dataset
from conmon.oscal import OSCAL_VERSION, export_oscal


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the OSCAL export CLI."""

    parser = argparse.ArgumentParser(
        prog="conmon-export-oscal",
        description=f"Export OSCAL {OSCAL_VERSION} Assessment Results from simulated ConMon data.",
    )
    parser.add_argument(
        "--out",
        "-o",
        default="exports/assessment-results.oscal.json",
        help="Output JSON path (default: %(default)s).",
    )
    parser.add_argument(
        "--seed", "-s", type=int, default=42, help="Data generation seed (default: %(default)s)."
    )
    parser.add_argument(
        "--as-of",
        type=_parse_date,
        default=DEFAULT_AS_OF,
        help=f"Reporting date YYYY-MM-DD (default: {DEFAULT_AS_OF.isoformat()}).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the OSCAL export CLI. Returns a process exit code."""

    args = build_parser().parse_args(argv)
    ds = generate_dataset(seed=args.seed, as_of=args.as_of)
    path = export_oscal(ds, args.out)
    findings = len(ds.poam)
    print(
        f"Wrote OSCAL {OSCAL_VERSION} Assessment Results to {path} "
        f"({findings} findings, as-of {ds.as_of.isoformat()})."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
