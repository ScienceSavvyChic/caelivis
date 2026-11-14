"""Streamlit presentation components for CAELIVIS."""

from datetime import date, datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from caelivis.insights import METRICS
from caelivis.storage import CREW_SOURCE, save_checkin

HAZARDS = [
    {"name": "Space radiation", "icon": "☀️", "description": "Beyond Earth's protective environment, radiation exposure is a mission hazard. This prototype has no radiation dosimeter feed, so health check-ins cannot measure exposure.", "connection": "No direct radiation observation is collected. Keep radiation monitoring and interpretation within mission systems and qualified flight-surgeon workflows.", "follow_up": "If a mission radiation alert is issued, follow the approved mission response and medical communication protocol."},
    {"name": "Isolation and confinement", "icon": "🧑‍🚀", "description": "A small crew living and working in a constrained environment can face behavioral-health and team challenges.", "connection": "Mood, stress, sleep, and cognitive well-being are self-reported context. A change is a prompt for conversation—not a diagnosis or proof of a hazard effect.", "follow_up": "Consider sharing persistent concerns with the crew medical officer or behavioral-health support team."},
    {"name": "Distance from Earth", "icon": "🌍", "description": "Long distances increase communication latency and constrain real-time support and resupply.", "connection": "The 20 min 14 sec one-way delay is a demonstration setting, not a live mission calculation. This app queues locally and does not send data.", "follow_up": "Use established onboard decision and escalation procedures; do not wait on this prototype for urgent care."},
    {"name": "Gravity fields", "icon": "🪐", "description": "Transitions between gravity environments and prolonged microgravity can affect human physiology and performance.", "connection": "Exercise minutes are logged as activity context only. This app does not measure gravitational exposure, balance, bone health, or countermeasure effectiveness.", "follow_up": "Discuss changes in function or exercise tolerance with the mission medical team under mission procedures."},
    {"name": "Hostile and closed environments", "icon": "🛰️", "description": "Spacecraft environments are engineered but can include environmental and operational hazards.", "connection": "The prototype does not ingest cabin atmosphere, acoustic, microbial, or equipment telemetry. Personal observations alone cannot identify an environmental exposure.", "follow_up": "Use dedicated environmental monitoring and report suspected cabin hazards through mission operations channels."},
]


def _header(kicker: str, title: str, description: str) -> None:
    st.markdown(f'<p class="eyebrow">{kicker}</p>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<p class="subtle">{description}</p>', unsafe_allow_html=True)


def render_overview(observations: pd.DataFrame, insights: list[dict]) -> None:
    _header("MISSION HEALTH / DEMONSTRATION", "Mission Health Overview", "A local view of self-reported observations and synthetic reference data. This is not a medical assessment.")
    st.info("Demonstration mode only: synthetic and crew-entered demonstration records are not astronaut telemetry.")
    if observations.empty:
        st.warning("No valid observations are available. Review local-data warnings or add a demonstration check-in.")
        return
    latest = observations.iloc[-1]
    cols = st.columns(4)
    cards = [("Heart rate", f"{int(latest['heart_rate_bpm'])} bpm"), ("Blood pressure", f"{int(latest['systolic_bp_mmhg'])}/{int(latest['diastolic_bp_mmhg'])} mmHg"), ("Sleep", f"{float(latest['sleep_hours']):.1f} h"), ("Exercise", f"{int(latest['exercise_minutes'])} min")]
    for col, (label, value) in zip(cols, cards):
        col.metric(label, value, help="Demonstration observation only; no clinical threshold is applied.")
    left, right = st.columns([1.45, 1])
    with left:
        st.subheader("Recent observations")
        display = observations.tail(7).copy()
        display["date"] = display["date"].dt.strftime("%b %d")
        display = display[["date", "heart_rate_bpm", "sleep_hours", "exercise_minutes", "mood_1_5", "data_source"]]
        st.dataframe(display.iloc[::-1], hide_index=True, use_container_width=True)
    with right:
        st.subheader("Monitoring status")
        local_count = int((observations["data_source"] == CREW_SOURCE).sum())
        st.metric("Records", len(observations))
        st.metric("Crew-entered demonstrations", local_count)
        st.caption(f"Latest record source: **{latest.get('data_source', 'Unknown')}**")
        st.caption("Data availability is not a clinical status.")
    st.subheader("Recent personal-baseline comparisons")
    if insights:
        for item in insights[:4]:
            st.warning(f"{item['metric']} is {abs(item['change_pct']):.0f}% {item['direction']} than its recent personal median ({item['baseline']:.1f} {item['unit']}). Descriptive signal only, not a medical threshold.")
    else:
        st.success("No configurable relative changes surfaced. This does not establish medical well-being.")
    st.caption("Mission day and Earth delay are static simulation values; no observation is actual astronaut telemetry.")


def render_checkin() -> None:
    _header("CREW SELF-REPORT", "Daily Health Check-In", "Record a demonstration observation. Input bounds are data-entry guardrails, not medical limits.")
    st.warning("Use demonstration values only. This is not a medical record or clinical tool. Follow mission protocols for urgent concerns.")
    with st.form("daily_checkin", clear_on_submit=False):
        observed_date = st.date_input("Observation date", value=date.today(), max_value=date.today(), key="checkin_date")
        a, b, c = st.columns(3)
        with a:
            hr = st.number_input("Heart rate (beats/min)", min_value=35, max_value=200, value=68, step=1)
            systolic = st.number_input("Blood pressure — systolic (mmHg)", min_value=60, max_value=250, value=118, step=1)
            diastolic = st.number_input("Blood pressure — diastolic (mmHg)", min_value=30, max_value=150, value=76, step=1)
            temp = st.number_input("Body temperature (°C)", min_value=30.0, max_value=43.0, value=36.7, step=0.1, format="%.1f")
            has_glucose = st.checkbox("Include optional blood glucose")
            glucose = st.number_input("Blood glucose (mg/dL)", min_value=20, max_value=600, value=90, step=1, disabled=not has_glucose)
        with b:
            sleep = st.number_input("Sleep duration (hours)", min_value=0.0, max_value=24.0, value=7.5, step=0.25)
            sleep_quality = st.slider("Sleep quality (self-rating)", 1, 5, 3, help="1 = very poor; 5 = very good. Personal rating only.")
            exercise = st.number_input("Exercise / physical activity (minutes)", min_value=0, max_value=360, value=45, step=5)
            mood = st.slider("Mood (self-rating)", 1, 5, 3, help="Personal demonstration rating; not a screening instrument.")
        with c:
            stress = st.slider("Stress (self-rating)", 1, 5, 3, help="Personal demonstration rating; not a validated clinical scale.")
            cognitive = st.slider("Cognitive well-being (self-rating)", 1, 5, 3, help="Personal rating; not a performance test.")
            fatigue = st.slider("Fatigue (self-rating)", 1, 5, 3)
        submitted = st.form_submit_button("Save check-in locally", type="primary")
    if submitted:
        if diastolic >= systolic:
            st.error("Please check blood pressure entry: diastolic must be lower than systolic in this form.")
        else:
            now = datetime.now(timezone.utc)
            record = {
                "date": observed_date.isoformat(), "observation_timestamp": now.isoformat(),
                "heart_rate_bpm": int(hr), "systolic_bp_mmhg": int(systolic),
                "diastolic_bp_mmhg": int(diastolic), "temperature_c": float(temp),
                "glucose_mg_dl": int(glucose) if has_glucose else None,
                "sleep_hours": float(sleep), "sleep_quality_1_5": int(sleep_quality),
                "exercise_minutes": int(exercise), "mood_1_5": int(mood),
                "stress_1_5": int(stress), "cognitive_wellbeing_1_5": int(cognitive),
                "fatigue_1_5": int(fatigue), "data_source": CREW_SOURCE,
            }
            try:
                save_checkin(record)
            except (OSError, ValueError, RuntimeError) as exc:
                st.error(f"Could not save this check-in safely: {exc}. Existing local data was not intentionally replaced.")
            else:
                st.success("Crew-entered demonstration record saved locally. It was not transmitted.")
                st.rerun()
    st.caption("The selected observation date is saved. Local demonstration records have no authentication or encryption.")


def build_trend_figure(observations: pd.DataFrame, column: str, label: str, unit: str, baseline: float | None = None):
    """Construct the Plotly trend chart, returning None when no data is drawable."""
    if observations.empty or column not in observations:
        return None
    valid = observations.dropna(subset=[column]).copy()
    if valid.empty:
        return None
    chart = go.Figure()
    chart.add_trace(go.Scatter(x=valid["date"], y=valid[column], mode="lines+markers", name=label, line={"color": "#43d7e8", "width": 3}, marker={"size": 7}, text=valid.get("data_source"), hovertemplate="%{x}<br>%{y} " + unit + "<br>%{text}<extra></extra>"))
    if baseline is not None:
        chart.add_hline(y=baseline, line_dash="dash", line_color="#f3bb59", annotation_text="Personal reference median")
    chart.update_layout(template="plotly_dark", height=390, margin={"l": 15, "r": 15, "t": 35, "b": 15}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,15,26,.55)", yaxis_title=unit, xaxis_title="Observation date", legend={"orientation": "h"})
    return chart


def render_trends(observations: pd.DataFrame) -> None:
    _header("PERSONAL REFERENCE", "Personal Baseline & Trends", "Explore a single measure over time against a configurable recent personal median.")
    st.info("Trend data consists only of labeled synthetic or crew-entered demonstrations—not astronaut telemetry. Relative changes are not clinical thresholds.")
    if observations.empty:
        st.info("No observations are available for the trend chart.")
        return
    metric_name = st.selectbox("Measure", list(METRICS))
    column, unit = METRICS[metric_name]
    valid = observations.dropna(subset=[column]).copy()
    if valid.empty:
        st.info("No valid observations are available for this measure.")
        return
    max_window = max(2, min(14, len(valid) - 1))
    controls1, controls2 = st.columns(2)
    with controls1:
        window = st.slider("Baseline window (prior records)", 2, max_window, min(7, max_window))
    with controls2:
        threshold = st.slider("Highlight relative change (%)", 5, 50, 15, help="Display preference only; not a medical threshold.")
    baseline = valid[column].iloc[:-1].tail(window).median() if len(valid) > 1 else float(valid[column].iloc[-1])
    latest = float(valid[column].iloc[-1])
    delta_pct = ((latest - baseline) / abs(baseline) * 100) if baseline else 0.0
    k1, k2, k3 = st.columns(3)
    k1.metric("Latest", f"{latest:g} {unit}")
    k2.metric(f"Recent median · {window} records", f"{baseline:.1f} {unit}")
    k3.metric("Relative difference", f"{delta_pct:+.1f}%", help="Descriptive comparison only; not clinical interpretation.")
    chart = build_trend_figure(valid, column, metric_name, unit, baseline)
    st.plotly_chart(chart, use_container_width=True)
    provenance = valid["data_source"].value_counts().to_dict()
    st.markdown("**Record provenance:** " + " · ".join(f"{key}: {value}" for key, value in provenance.items()))
    if abs(delta_pct) >= threshold:
        st.warning(f"The latest value differs from this selected personal reference by more than {threshold}%. Display cue only; consult qualified medical personnel for concerns.")
    st.caption("Baseline excludes the latest observation. The chart hover labels identify each record's demonstration source.")


def render_hazards(observations: pd.DataFrame, insights: list[dict]) -> None:
    _header("CONTEXT, NOT DIAGNOSIS", "Health Insights & Alerts", "NASA human-spaceflight hazards are explained alongside the limits of these demonstration observations.")
    st.error("This prototype cannot diagnose or triage. For urgent or concerning symptoms, follow mission medical escalation procedures and contact qualified medical personnel.")
    st.subheader("Descriptive personal-baseline signals")
    if insights:
        for item in insights:
            st.warning(f"**{item['metric']}**: {abs(item['change_pct']):.1f}% {item['direction']} than recent median ({item['baseline']:.1f} {item['unit']}). Source: {item['source']}. Descriptive comparison, not a clinical alert.")
    else:
        st.success("No relative changes exceeded the current display setting. This is not a health clearance.")
    st.markdown("### NASA human-spaceflight hazards")
    for hazard in HAZARDS:
        with st.expander(f"{hazard['icon']}  {hazard['name']}"):
            st.write(hazard["description"])
            st.markdown(f"**What this app can show:** {hazard['connection']}")
            st.markdown(f"**Appropriate follow-up:** {hazard['follow_up']}")
            st.markdown("**NASA references:** [NASA Human Research Program](https://www.nasa.gov/hrp/) · [NASA Human Research Roadmap](https://humanresearchroadmap.nasa.gov/)")
    st.caption(f"{len(observations)} demonstration records; all insight comparisons are descriptive and rule-based. No AI or clinical decision system is connected.")


def render_privacy(observations: pd.DataFrame, outbox: list[dict], on_queue, on_deliver) -> None:
    _header("LOCAL DATA / DELAY SIMULATION", "Privacy & Communications", "The demo stores observations on the machine running Streamlit. There is no outbound networking or real transmission.")
    st.info("One-way Earth communication delay: **20 minutes and 14 seconds** (simulated). This fixed value is not a live mission calculation.")
    st.markdown("#### Data handling")
    st.write("Check-ins are written to `data/local/checkins.json` by default. `CAELIVIS_DATA_DIR` can select another local folder. Sample observations are synthetic demonstrations. No health data is transmitted.")
    st.warning("Local JSON is not encrypted or access-controlled. Use demonstration values only; do not enter actual personal or astronaut health information.")
    if st.button("Queue latest summary for simulated transmission", type="primary", disabled=observations.empty):
        try:
            item = on_queue()
        except (OSError, RuntimeError, ValueError) as exc:
            st.error(f"Could not queue safely: {exc}")
        else:
            if item:
                st.success("Summary queued locally only. No communication occurred.")
                st.rerun()
    st.markdown("#### Local outbox · simulation only")
    if not outbox:
        st.caption("No messages are queued.")
    else:
        for item in reversed(outbox):
            with st.container(border=True):
                st.write(f"**Observation timestamp:** {item['observation_timestamp']}")
                st.write(f"**Queue time:** {item['queued_at']} UTC")
                st.write(f"**One-way delay:** {int(item['one_way_delay_seconds']) // 60} minutes {int(item['one_way_delay_seconds']) % 60} seconds")
                st.write(f"**Calculated simulated arrival:** {item['expected_arrival']} UTC")
                st.write(f"**Status:** {item['status']}")
                st.caption("Local simulation only. This record was not transmitted to Earth.")
                st.json(item["payload"])
                if item["status"] == "Queued — Not Transmitted" and st.button("Advance local simulation", key=f"deliver-{item['id']}"):
                    try:
                        on_deliver(item["id"])
                    except (OSError, RuntimeError):
                        st.error("Could not update the simulated local status.")
                    else:
                        st.rerun()
