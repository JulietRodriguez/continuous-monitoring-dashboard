"""Tests for the OSCAL export CLI."""

from __future__ import annotations

import json

from conmon.cli import main


def test_cli_writes_export(tmp_path, capsys):
    out = tmp_path / "ar.json"
    code = main(["--out", str(out), "--seed", "5"])
    assert code == 0
    assert out.exists()
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert "assessment-results" in doc
    captured = capsys.readouterr()
    assert "Wrote OSCAL" in captured.out


def test_cli_respects_as_of(tmp_path):
    out = tmp_path / "ar.json"
    main(["--out", str(out), "--as-of", "2025-12-31"])
    doc = json.loads(out.read_text(encoding="utf-8"))
    published = doc["assessment-results"]["metadata"]["published"]
    assert published.startswith("2025-12-31")
