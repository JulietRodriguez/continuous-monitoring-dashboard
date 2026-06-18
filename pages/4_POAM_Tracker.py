"""ConMon Dashboard — Page 4: POA&M Tracker.

Filterable register of open Plan of Action & Milestones items with days open,
risk score, and owner, plus an OSCAL Assessment Results export button.
"""

from __future__ import annotations

import json

import streamlit as st

from conmon import metrics
from conmon.dashboard import kpi_row, page_setup, sidebar_meta
from conmon.oscal import OSCAL_VERSION, build_assessment_results
from conmon.theme import MUTED, SEVERITY_COLORS

ds = page_setup("POA&M Tracker", icon="📋")
sidebar_meta(ds)

st.title("📋 POA&M Tracker")
st.caption(
    "Plan of Action & Milestones register — open weaknesses ranked by risk, "
    "with aging and ownership. Export to OSCAL for ConMon submission."
)

summary = metrics.poam_summary(ds)

kpi_row(
    [
        ("Total POA&Ms", str(summary["total"]), "lifetime register", MUTED),
        ("Open", str(summary["open"]), "active items", "#38bdf8"),
        ("Past Due", str(summary["past_due"]), "beyond SLA", SEVERITY_COLORS["Critical"]),
        ("Risk Accepted", str(summary["risk_accepted"]), "approved deviations", MUTED),
    ]
)

st.write("")

# --- Filters --------------------------------------------------------------- #
f1, f2, f3 = st.columns([1, 1, 2])
with f1:
    sev_filter = st.multiselect(
        "Severity", options=list(SEVERITY_COLORS.keys()), default=list(SEVERITY_COLORS.keys())
    )
with f2:
    status_filter = st.multiselect(
        "Status",
        options=sorted(ds.poam["status"].unique().tolist()),
        default=sorted(ds.poam["status"].unique().tolist()),
    )
with f3:
    owner_filter = st.multiselect(
        "Owner",
        options=sorted(ds.poam["owner"].unique().tolist()),
        default=sorted(ds.poam["owner"].unique().tolist()),
    )
past_due_only = st.checkbox("Show past-due only", value=False)

view = ds.poam[
    ds.poam["severity"].isin(sev_filter)
    & ds.poam["status"].isin(status_filter)
    & ds.poam["owner"].isin(owner_filter)
]
if past_due_only:
    view = view[view["past_due"]]

# --- Table ----------------------------------------------------------------- #
display = view.rename(
    columns={
        "poam_id": "POA&M ID",
        "weakness": "Weakness",
        "control_family": "Family",
        "severity": "Severity",
        "status": "Status",
        "owner": "Owner",
        "opened": "Opened",
        "scheduled_completion": "Scheduled",
        "days_open": "Days Open",
        "risk_score": "Risk",
        "past_due": "Past Due",
    }
)[
    [
        "POA&M ID",
        "Weakness",
        "Family",
        "Severity",
        "Status",
        "Owner",
        "Opened",
        "Scheduled",
        "Days Open",
        "Risk",
        "Past Due",
    ]
].copy()
display["Opened"] = display["Opened"].dt.date
display["Scheduled"] = display["Scheduled"].dt.date

st.caption(f"Showing {len(display)} of {len(ds.poam)} POA&M items.")
st.dataframe(
    display,
    use_container_width=True,
    hide_index=True,
    height=460,
    column_config={
        "Risk": st.column_config.ProgressColumn("Risk", min_value=0, max_value=100, format="%d"),
        "Days Open": st.column_config.NumberColumn("Days Open", format="%d d"),
    },
)

# --- Exports --------------------------------------------------------------- #
st.subheader("Exports")
e1, e2 = st.columns(2)
with e1:
    csv = display.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download POA&M (CSV)",
        data=csv,
        file_name="poam_register.csv",
        mime="text/csv",
        use_container_width=True,
    )
with e2:
    oscal_doc = build_assessment_results(ds)
    oscal_json = json.dumps(oscal_doc, indent=2, default=str).encode("utf-8")
    st.download_button(
        f"⬇️ Export OSCAL {OSCAL_VERSION} Assessment Results",
        data=oscal_json,
        file_name="assessment-results.oscal.json",
        mime="application/json",
        use_container_width=True,
    )

with st.expander("Preview OSCAL Assessment Results (metadata + first finding)"):
    preview = {
        "assessment-results": {
            "uuid": oscal_doc["assessment-results"]["uuid"],
            "metadata": oscal_doc["assessment-results"]["metadata"],
            "results[0].findings[0]": oscal_doc["assessment-results"]["results"][0]["findings"][0],
        }
    }
    st.json(preview)
