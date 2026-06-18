"""Shared pytest fixtures for the ConMon test-suite."""

from __future__ import annotations

import pytest

from conmon.data import Dataset, generate_dataset


@pytest.fixture(scope="session")
def dataset() -> Dataset:
    """A default seeded dataset shared across read-only tests."""

    return generate_dataset(seed=42)
