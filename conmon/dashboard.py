"""Shared Streamlit helpers used by every dashboard page.

Keeps page modules thin: they import :func:`page_setup` to apply the theme and
:func:`get_dataset` for the cached dataset, then focus on their own charts.
"""

from __future__ import annotations

import streamlit as st

from conmon.data import Dataset, generate_dataset
from conmon.theme import custom_css, kpi_card


@st.cache_data(show_spinner=False)
def get_dataset(seed: int = 42) -> Dataset:
    """Return the cached simulated dataset for the dashboard session."""

    return generate_dataset(seed=seed)


def page_setup(title: str, icon: str = "🛡️") -> Dataset:
    """Configure the page, inject theme CSS, and return the dataset.

    Args:
        title: Browser/page title for this page.
        icon: Page emoji icon.

    Returns:
        The shared :class:`~conmon.data.Dataset`.
    """

    st.set_page_config(
        page_title=f"ConMon · {title}",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(custom_css(), unsafe_allow_html=True)
    return get_dataset()


def kpi_row(cards: list[tuple[str, str, str | None, str]]) -> None:
    """Render a row of KPI cards.

    Args:
        cards: List of ``(label, value, delta, delta_color)`` tuples.
    """

    cols = st.columns(len(cards))
    for col, (label, value, delta, color) in zip(cols, cards, strict=False):
        with col:
            st.markdown(kpi_card(label, value, delta, color), unsafe_allow_html=True)


def sidebar_meta(ds: Dataset) -> None:
    """Render shared sidebar context (reporting date, baseline, posture)."""

    with st.sidebar:
        st.markdown("### 🛰️ ConMon Dashboard")
        st.caption("FedRAMP Continuous Monitoring — simulated demo data")
        st.divider()
        st.metric("Reporting date", ds.as_of.isoformat())
        st.metric("Baseline", "FedRAMP Moderate")
        st.metric("Monitoring window", "26 weeks")
        st.divider()
        st.caption(
            "All figures are synthetic and generated deterministically for "
            "demonstration. Export OSCAL via `conmon-export-oscal`."
        )
