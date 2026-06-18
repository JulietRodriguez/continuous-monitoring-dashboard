"""ConMon Dashboard — Page 2: Control Health.

NIST SP 800-53 control-family heatmap with Pass / Partial / Fail breakdown.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from conmon import metrics
from conmon.dashboard import kpi_row, page_setup, sidebar_meta
from conmon.theme import COMPLIANCE_SCALE, MUTED, STATUS_COLORS, plotly_layout

ds = page_setup("Control Health", icon="🧩")
sidebar_meta(ds)

st.title("🧩 Control Health")
st.caption(
    "Per-family assessment status across the NIST SP 800-53 Rev 5 control "
    "catalog. Scores weight partial implementations at 50%."
)

ch = ds.control_health.sort_values("score")
totals = metrics.control_status_totals(ds)
total_controls = sum(totals.values())

kpi_row(
    [
        ("Controls Assessed", str(total_controls), f"{len(ch)} families", MUTED),
        (
            "Passing",
            str(totals["Pass"]),
            f"{totals['Pass'] / total_controls:.0%}",
            STATUS_COLORS["Pass"],
        ),
        (
            "Partial",
            str(totals["Partial"]),
            f"{totals['Partial'] / total_controls:.0%}",
            STATUS_COLORS["Partial"],
        ),
        (
            "Failing",
            str(totals["Fail"]),
            f"{totals['Fail'] / total_controls:.0%}",
            STATUS_COLORS["Fail"],
        ),
    ]
)

st.write("")

# --- Family score heatmap -------------------------------------------------- #
st.subheader("Control Family Compliance Heatmap")
heat = ds.control_health.copy()
fig = go.Figure(
    go.Heatmap(
        x=heat["family_id"],
        y=["Compliance"],
        z=[heat["score"].tolist()],
        colorscale=COMPLIANCE_SCALE,
        zmin=50,
        zmax=100,
        text=[[f"{v:.0f}%" for v in heat["score"]]],
        texttemplate="%{text}",
        textfont={"size": 12, "color": "#e6edf6"},
        customdata=[heat["family"].tolist()],
        hovertemplate="<b>%{x}</b> — %{customdata}<br>Score %{z:.1f}%<extra></extra>",
        colorbar={"title": "Score %", "outlinewidth": 0},
    )
)
fig.update_layout(**plotly_layout(height=220, margin={"l": 90, "r": 20, "t": 30, "b": 40}))
st.plotly_chart(fig, use_container_width=True)

# --- Stacked status by family ---------------------------------------------- #
st.subheader("Pass / Partial / Fail by Family")
order = ds.control_health.sort_values("score", ascending=True)
fig = go.Figure()
for status, col in (("pass", "Pass"), ("partial", "Partial"), ("fail", "Fail")):
    fig.add_trace(
        go.Bar(
            y=order["family_id"],
            x=order[status],
            name=col,
            orientation="h",
            marker_color=STATUS_COLORS[col],
            hovertemplate=f"%{{y}}<br>{col}: %{{x}}<extra></extra>",
        )
    )
fig.update_layout(
    **plotly_layout(height=620, barmode="stack"),
    legend_orientation="h",
)
fig.update_xaxes(title="Controls")
st.plotly_chart(fig, use_container_width=True)

# --- Detail table ---------------------------------------------------------- #
st.subheader("Family Detail")
table = ds.control_health.rename(
    columns={
        "family_id": "Family",
        "family": "Name",
        "total": "Total",
        "pass": "Pass",
        "partial": "Partial",
        "fail": "Fail",
        "score": "Score %",
    }
).sort_values("Score %")

st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Score %": st.column_config.ProgressColumn(
            "Score %", min_value=0, max_value=100, format="%.1f%%"
        ),
    },
)

# Lowest-performing families call-out.
worst = ch.head(3)
st.warning(
    "Lowest-scoring families: "
    + ", ".join(f"**{r.family_id}** ({r.score:.0f}%)" for r in worst.itertuples()),
    icon="⚠️",
)
