"""Dark SOC/GRC visual theme shared across the dashboard pages.

Centralizes the color palette, Plotly template, and injected CSS so every page
renders with a consistent professional security-operations look.
"""

from __future__ import annotations

from typing import Any

# Core palette -------------------------------------------------------------- #
BG = "#0b0f1a"
PANEL = "#121826"
PANEL_ALT = "#1a2234"
GRID = "#243049"
TEXT = "#e6edf6"
MUTED = "#8b97ad"
ACCENT = "#38bdf8"
ACCENT_2 = "#22d3ee"

STATUS_COLORS = {
    "Pass": "#22c55e",
    "Partial": "#f5a524",
    "Fail": "#e5484d",
}

SEVERITY_COLORS = {
    "Critical": "#e5484d",
    "High": "#f5a524",
    "Medium": "#3b82f6",
    "Low": "#22c55e",
}

# Continuous green->amber->red scale for heatmaps (0 = bad, 100 = good).
COMPLIANCE_SCALE = [
    [0.0, "#7f1d1d"],
    [0.5, "#b45309"],
    [0.75, "#a16207"],
    [0.9, "#3f6212"],
    [1.0, "#15803d"],
]


def plotly_layout(**overrides: Any) -> dict[str, Any]:
    """Return a base Plotly layout dict for the dark theme.

    Pass keyword overrides to merge/replace top-level layout keys.
    """

    layout: dict[str, Any] = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": TEXT, "family": "Inter, Segoe UI, system-ui, sans-serif"},
        "colorway": [ACCENT, ACCENT_2, "#a78bfa", "#f5a524", "#22c55e", "#e5484d"],
        "margin": {"l": 50, "r": 20, "t": 50, "b": 40},
        "xaxis": {"gridcolor": GRID, "zerolinecolor": GRID, "linecolor": GRID},
        "yaxis": {"gridcolor": GRID, "zerolinecolor": GRID, "linecolor": GRID},
        "legend": {"bgcolor": "rgba(0,0,0,0)"},
        "hoverlabel": {"bgcolor": PANEL_ALT, "font": {"color": TEXT}},
    }
    layout.update(overrides)
    return layout


def custom_css() -> str:
    """Return the global CSS injected on every page via ``st.markdown``."""

    return f"""
    <style>
      .stApp {{
        background: radial-gradient(1200px 600px at 20% -10%, #11203a 0%, {BG} 55%);
        color: {TEXT};
      }}
      section[data-testid="stSidebar"] {{
        background-color: {PANEL};
        border-right: 1px solid {GRID};
      }}
      h1, h2, h3, h4 {{ color: {TEXT}; letter-spacing: 0.2px; }}
      .conmon-kpi {{
        background: linear-gradient(160deg, {PANEL} 0%, {PANEL_ALT} 100%);
        border: 1px solid {GRID};
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset;
      }}
      .conmon-kpi .label {{
        color: {MUTED}; font-size: 0.78rem; text-transform: uppercase;
        letter-spacing: 1.2px; margin-bottom: 6px;
      }}
      .conmon-kpi .value {{ font-size: 2.0rem; font-weight: 700; line-height: 1.1; }}
      .conmon-kpi .delta {{ font-size: 0.85rem; margin-top: 4px; }}
      .conmon-badge {{
        display:inline-block; padding: 2px 10px; border-radius: 999px;
        font-size: 0.72rem; font-weight: 600; letter-spacing: 0.4px;
      }}
      div[data-testid="stMetricValue"] {{ color: {TEXT}; }}
      .stDataFrame {{ border: 1px solid {GRID}; border-radius: 10px; }}
    </style>
    """


def kpi_card(label: str, value: str, delta: str | None = None, delta_color: str = MUTED) -> str:
    """Return HTML for a styled KPI card."""

    delta_html = f'<div class="delta" style="color:{delta_color}">{delta}</div>' if delta else ""
    return (
        f'<div class="conmon-kpi"><div class="label">{label}</div>'
        f'<div class="value">{value}</div>{delta_html}</div>'
    )
