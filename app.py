"""ConMon Dashboard — Page 1: Executive Summary.

Run with::

    streamlit run app.py

This is the Streamlit entry point; the Control Health, Vulnerability Trends,
and POA&M Tracker pages live in ``pages/`` and appear in the sidebar nav.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from conmon import metrics
from conmon.dashboard import kpi_row, page_setup, sidebar_meta
from conmon.theme import MUTED, SEVERITY_COLORS, STATUS_COLORS, plotly_layout

ds = page_setup("Executive Summary", icon="📊")
sidebar_meta(ds)

st.title("📊 Executive Summary")
st.caption(
    "Authorization-boundary posture at a glance — compliance score, trend, "
    "critical findings, and POA&M aging."
)

# --- KPI row --------------------------------------------------------------- #
score = ds.overall_score
drift = metrics.compliance_drift(ds)
poam = metrics.poam_summary(ds)
mttr = metrics.overall_mttr(ds)

drift_color = "#22c55e" if drift >= 0 else "#e5484d"
drift_arrow = "▲" if drift >= 0 else "▼"

kpi_row(
    [
        (
            "Compliance Score",
            f"{score:.1f}%",
            f"{drift_arrow} {abs(drift):.1f} pts (4 wk)",
            drift_color,
        ),
        ("Critical / High Open", str(ds.critical_open), "POA&M severity", MUTED),
        ("Past-Due POA&Ms", str(poam["past_due"]), f"of {poam['open']} open", "#f5a524"),
        ("Mean Time to Remediate", f"{mttr:.0f} d", "all severities", MUTED),
    ]
)

st.write("")
left, right = st.columns([3, 2])

# --- Compliance trend ------------------------------------------------------ #
with left:
    st.subheader("Compliance Score Trend")
    trend = ds.compliance_trend
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=trend["date"],
            y=trend["compliance_score"],
            mode="lines",
            line={"color": "#38bdf8", "width": 3, "shape": "spline"},
            fill="tozeroy",
            fillcolor="rgba(56,189,248,0.12)",
            name="Compliance %",
            hovertemplate="%{x|%b %d}<br>%{y:.1f}%<extra></extra>",
        )
    )
    fig.add_hline(
        y=90,
        line_dash="dash",
        line_color="#22c55e",
        annotation_text="Target 90%",
        annotation_position="top left",
        annotation_font_color="#22c55e",
    )
    fig.update_layout(**plotly_layout(height=360, showlegend=False))
    fig.update_yaxes(range=[70, 100], title="Compliance %")
    st.plotly_chart(fig, use_container_width=True)

# --- Critical findings over time ------------------------------------------- #
with right:
    st.subheader("Critical Findings Over Time")
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=trend["date"],
            y=trend["critical_findings"],
            marker_color=SEVERITY_COLORS["Critical"],
            name="Critical findings",
            hovertemplate="%{x|%b %d}<br>%{y} critical<extra></extra>",
        )
    )
    fig.update_layout(**plotly_layout(height=360, showlegend=False))
    fig.update_yaxes(title="Open critical findings")
    st.plotly_chart(fig, use_container_width=True)

# --- POA&M aging + control status ------------------------------------------ #
st.write("")
c1, c2 = st.columns(2)

with c1:
    st.subheader("POA&M Aging")
    aging = metrics.poam_aging(ds)
    # Color ramps from green (fresh) to red (aged) across buckets.
    bucket_colors = ["#22c55e", "#84cc16", "#f5a524", "#fb923c", "#e5484d"]
    fig = go.Figure(
        go.Bar(
            x=aging["bucket"],
            y=aging["count"],
            marker_color=bucket_colors,
            text=aging["count"],
            textposition="outside",
            hovertemplate="%{x} days<br>%{y} items<extra></extra>",
        )
    )
    fig.update_layout(**plotly_layout(height=340, showlegend=False))
    fig.update_xaxes(title="Days open")
    fig.update_yaxes(title="Open POA&M items")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Control Status Mix")
    totals = metrics.control_status_totals(ds)
    fig = go.Figure(
        go.Pie(
            labels=list(totals.keys()),
            values=list(totals.values()),
            hole=0.62,
            marker={"colors": [STATUS_COLORS[k] for k in totals]},
            textinfo="label+percent",
            hovertemplate="%{label}<br>%{value} controls<extra></extra>",
        )
    )
    fig.update_layout(
        **plotly_layout(height=340, showlegend=False),
    )
    fig.add_annotation(
        text=f"{sum(totals.values())}<br>controls",
        showarrow=False,
        font={"size": 18, "color": "#e6edf6"},
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption(
    f"As-of {ds.as_of.isoformat()} · {poam['open']} open POA&Ms · "
    f"{poam['risk_accepted']} risk-accepted · synthetic demonstration data."
)
