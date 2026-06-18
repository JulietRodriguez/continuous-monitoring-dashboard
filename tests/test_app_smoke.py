"""Smoke tests that execute each Streamlit page end-to-end.

Uses Streamlit's headless ``AppTest`` harness to run each page script and
assert it renders without raising an exception.
"""

from __future__ import annotations

from pathlib import Path

import pytest

at = pytest.importorskip("streamlit.testing.v1")
AppTest = at.AppTest

ROOT = Path(__file__).resolve().parents[1]

PAGES = [
    ROOT / "app.py",
    ROOT / "pages" / "2_Control_Health.py",
    ROOT / "pages" / "3_Vulnerability_Trends.py",
    ROOT / "pages" / "4_POAM_Tracker.py",
]


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_page_runs_without_exception(page):
    app = AppTest.from_file(str(page), default_timeout=60)
    app.run()
    assert not app.exception, f"{page.name} raised: {app.exception}"
    # Every page should render at least one title/header.
    assert app.title or app.header or app.markdown
