"""Streamlit presentation components for CAELIVIS."""

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from caelivis.insights import METRICS, build_insights
from caelivis.storage import save_checkin

HAZARDS = [
    {
        "name": "Space radiation",
        "icon": "☀️",
        "description": "Beyond Earth's protective environment, radiation exposure is a mission hazard. This prototype has no radiation dosimeter feed, so health check-ins cannot measure exposure.",
        "connection": "No direct radiation observation is collected. Keep radiation monitoring and interpretation within mission systems and qualified flight-surgeon workflows.",
        "follow_up": "If a mission radiation alert is issued, follow the approved mission response and medical communication protocol.",
    },
    {
        "name": "Isolation and confinement",
        "icon": "🧑‍🚀",
        "description": "A small crew living and working in a constrained environment can face behavioral-health and team challenges.",
        "connection": "Mood, stress, sleep, and cognitive well-being are self-reported context. A change is a prompt for conversation—not a diagnosis or proof of a hazard effect.",
        "follow_up": "Consider sharing persistent concerns with the crew medical officer or behavioral-health support team.",
    },
    {
        "name": "Distance from Earth",
        "icon": "🌍",
        "description": "Long distances increase communication latency and constrain real-time support and resupply.",
        "connection": "The 20 min 14 sec one-way delay is a demonstration setting, not a live mission calculation. This app queues locally and does not send data.",
        "follow_up": "Use established onboard decision and escalation procedures; do not wait on this prototype for urgent care.",
    },
    {
        "name": "Gravity fields",
        "icon": "🪐",
        "description": "Transitions between gravity environments and prolonged microgravity can affect human physiology and performance.",
        "connection": "Exercise minutes are logged as activity context only. This app does not measure gravitational exposure, balance, bone health, or countermeasure effectiveness.",
        "follow_up": "Discuss changes in function or exercise tolerance with the mission medical team under mission procedures.",
    },
    {
        "name": "Hostile and closed environments",
        "icon": "🛰️",
        "description": "Spacecraft environments are engineered but can include environmental and operational hazards.",
        "connection": "The prototype does not ingest cabin atmosphere, acoustic, microbial, or equipment telemetry. Personal observations alone cannot identify an environmental exposure.",
        "follow_up": "Use dedicated environmental monitoring and report suspected cabin hazards through mission operations channels.",
    },
]


def _header(kicker: str, title: str, description: str) -> None:
    st.markdown(f'<p class="eyebrow">{kicker}</p>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<p class="subtle">{description}</p>', unsafe_allow_html=True)


def _latest(observations: pd.DataFrame) -> pd.Series:
    return observations.iloc[-1]


def render_overview(observations: pd.DataFrame, insights: list[dict]) -> None:
    _header("MISSION HEALTH / DEMONSTRATION", "Mission Health Overview", "A local view of self-reported observations and synthetic reference data. This is not a medical assessment.")
    st.info("Demonstration mode: synthetic sample observations are clearly labeled. User check-ins stay in local JSON files unless you manually manage those files.")
    latest = _latest(observations)
    cols = st.columns(4)
    cards = [
        ("Heart rate", f"{int(latest['heart_rate_bpm'])} bpm"),
        ("Blood pressure", f"{int(latest['systolic_bp_mmhg'])}/{int(latest['diastolic_bp_mmhg'])} mmHg"),
        ("Sleep", f"{float(latest['sleep_hours']):.1f} h"),
        ("Exercise", f"{int(latest['exercise_minutes'])} min"),
    ]
    for col, (label, value) in zip(cols, cards):
        col.metric(label, value, help="Observation display only; no clinical threshold is applied.")
    left, right = st.columns([1.45, 1])
    with left:
        st.subheader("Recent observations")
        display = observations.tail(7).copy()
        display["date"] = display["date"].dt.strftime("%b %d")
        display = display[["date", "heart_rate_bpm", "sleep_hours", "exercise_minutes", "mood_1_5", "data_source"]]
        st.dataframe(display.iloc[::-1], hide_index=True, use_container_width=True)
    with right:
        st.subheader("Monitoring status")
        local_count = int((observations["data_source"] == "Local check-in").sum()) if "data_source" in observations else 0
        st.metric("Records", len(observations), help="Includes synthetic sample rows and any locally saved check-ins.")
        st.metric("Saved check-ins", local_count)
        st.caption(f"Latest record source: **{latest.get('data_source', 'Unknown')}**")
        st.caption("Monitoring status means data is available in this prototype; it is not a clinical status.")
    st.subheader("Recent personal-baseline comparisons")
    if insights:
        for item in insights[:4]:
            st.warning(f"{item['metric']} is {abs(item['change_pct']):.0f}% {item['direction']} than its recent personal median ({item['baseline']:.1f} {item['unit']}). This descriptive signal is not a medical threshold.")
    else:
        st.success("No configurable relative changes surfaced in the latest comparison. This does not establish that the crew member is medically well.")
    st.caption("Mission day and Earth delay are static simulation values for this demo.")


def render_checkin() -> None:
    _header("CREW SELF-REPORT", "Daily Health Check-In", "Record a simulated daily observation. Numeric bounds prevent impossible entries; they are not medical limits.")
    st.warning("Enter demonstration values only. This prototype is not a medical record and does not provide diagnosis or treatment. Follow mission protocols for urgent concerns.")
    with st.form("daily_checkin", clear_on_submit=False):
        st.date_input("Observation date", value=date.today(), max_value=date.today())
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
            mood = st.slider("Mood (self-rating)", 1, 5, 3, help="1 = low; 5 = positive. Not a screening instrument.")
        with c:
            stress = st.slider("Stress (self-rating)", 1, 5, 3, help="1 = low; 5 = high. Not a validated clinical scale.")
            cognitive = st.slider("Cognitive well-being (self-rating)", 1, 5, 3, help="1 = struggling; 5 = doing well. Not a performance test.")
            fatigue = st.slider("Fatigue (self-rating)", 1, 5, 3, help="1 = low; 5 = high.")
        submitted = st.form_submit_button("Save check-in locally", type="primary")
    if submitted:
        if diastolic >= systolic:
            st.error("Please check blood pressure entry: diastolic must be lower than systolic in this form.")
        else:
            record = {
                "date": date.today().isoformat(),
                "heart_rate_bpm": int(hr),
                "systolic_bp_mmhg": int(systolic),
                "diastolic_bp_mmhg": int(diastolic),
                "temperature_c": float(temp),
                "glucose_mg_dl": int(glucose) if has_glucose else None,
                "sleep_hours": float(sleep),
                "sleep_quality_1_5": int(sleep_quality),
                "exercise_minutes": int(exercise),
                "mood_1_5": int(mood),
                "stress_1_5": int(stress),
                "cognitive_wellbeing_1_5": int(cognitive),
                "fatigue_1_5": int(fatigue),
                "data_source": "Local check-in",
            }
            save_checkin(record)
            st.success("Check-in saved to this device's local data folder. It was not transmitted.")
            st.rerun()
    st.caption("Check-in date is currently set to today. This first milestone stores a local self-report; there is no authentication or encryption layer.")


def render_trends(observations: pd.DataFrame) -> None:
    _header("PERSONAL REFERENCE", "Personal Baseline & Trends", "Explore a single measure over time against a configurable recent personal median.")
    st.info("Synthetic sample data is illustrative only. Relative changes are visual comparisons—not validated alert thresholds or clinical guidance.")
    metric_name = st.selectbox("Measure", list(METRICS))
    column, unit = METRICS[metric_name]
    max_window = max(2, min(14, len(observations) - 1))
    controls1, controls2 = st.columns(2)
    with controls1:
        window = st.slider("Baseline window (prior records)", 2, max_window, min(7, max_window))
    with controls2:
        threshold = st.slider("Highlight relative change (%)", 5, 50, 15, help="A visual preference only. This is not a medical threshold.")
    valid = observations.dropna(subset=[column]).copy()
    if valid.empty:
        st.info("No observations are available for this measure yet.")
        return
    baseline = valid[column].iloc[:-1].tail(window).median() if len(valid) > 1 else float(valid[column].iloc[-1])
    latest = float(valid[column].iloc[-1])
    delta_pct = ((latest - baseline) / abs(baseline) * 100) if baseline else 0.0
    k1, k2, k3 = st.columns(3)
    k1.metric("Latest", f"{latest:g} {unit}")
    k2.metric(f"Recent median · {window} records", f"{baseline:.1f} {unit}")
    k3.metric("Relative difference", f"{delta_pct:+.1f}%", help="Descriptive comparison only; not clinical interpretation.")
    chart = go.Figure()
    chart.add_trace(go.Scatter(x=valid["date"], y=valid[column], mode="lines+markers", name=metric_name, line={"color": "#43d7e8", "width": 3}, marker={"size": 7}))
    chart.add_hline(y=baseline, line_dash="dash", line_color="#f3bb59", annotation_text="Personal reference median")
    chart.update_layout(template="plotly_dark", height=390, margin={"l": 15, "r": 15, "t": 35, "b": 15}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,15,26,.55)", yaxis_title=unit, xaxis_title="Observation date", legend={"orientation": "h"})
    st.plotly_chart(chart, use_container_width=True)
    if abs(delta_pct) >= threshold:
        st.warning(f"The latest value differs from this selected personal reference by more than {threshold}%. This is a configurable display cue only; discuss concerns with qualified medical personnel.")
    st.caption("Baseline uses the preceding records in the selected window, excluding the latest value. Multiple observations on one day are not aggregated in this prototype.")


def render_hazards(observations: pd.DataFrame, insights: list[dict]) -> None:
    _header("CONTEXT, NOT DIAGNOSIS", "Health Insights & Alerts", "NASA human-spaceflight hazards are explained alongside the limits of the observations this prototype collects.")
    st.error("This prototype cannot diagnose or triage. If symptoms are urgent or concerning, follow mission medical escalation procedures and contact qualified medical personnel.")
    st.subheader("Descriptive personal-baseline signals")
    if insights:
        for item in insights:
            st.warning(f"**{item['metric']}**: {abs(item['change_pct']):.1f}% {item['direction']} than recent median ({item['baseline']:.1f} {item['unit']}). Source: {item['source']}. This is a simulated comparison, not an alert threshold.")
    else:
        st.success("No relative changes exceeded the current display setting. Absence of a displayed signal is not a health clearance.")
    st.markdown("### NASA human-spaceflight hazards")
    for hazard in HAZARDS:
        with st.expander(f"{hazard['icon']}  {hazard['name']}", expanded=False):
            st.write(hazard["description"])
            st.markdown(f"**What this app can show:** {hazard['connection']}")
            st.markdown(f"**Appropriate follow-up:** {hazard['follow_up']}")
            st.markdown("**NASA references:** [NASA Human Research Program](https://www.nasa.gov/hrp/) · [NASA Human Research Roadmap](https://humanresearchroadmap.nasa.gov/)")
    st.caption(f"Dataset contains {len(observations)} rows from synthetic examples and any locally entered check-ins. All insights are rule-based descriptions; no AI model or clinical decision system is connected.")


def render_privacy(observations: pd.DataFrame, outbox: list[dict], on_queue, on_deliver) -> None:
    _header("LOCAL DATA / DELAY SIMULATION", "Privacy & Communications", "The demo stores observations on the machine running Streamlit. There is no outbound networking or real transmission.")
    st.info("One-way Earth communication delay: **20 minutes 14 seconds** (simulated). This fixed value is for demonstration—not a live mission ephemeris.")
    st.markdown("#### Data handling")
    st.write("Check-ins are written to `data/local/checkins.json` by default. You can set `CAELIVIS_DATA_DIR` to choose another local folder. The sample dataset is synthetic. No API keys, cloud service, or health-data transmission are used.")
    st.warning("Local JSON is not encrypted, access-controlled, or suitable for real health information. Use demonstration values only. Do not enter actual personal or astronaut health information.")
    if st.button("Queue latest summary for simulated transmission", type="primary", disabled=observations.empty):
        item = on_queue()
        if item:
            st.success(f"Summary queued locally. Simulated one-way arrival: {item['expected_arrival']} (UTC). No message was sent.")
            st.rerun()
    st.markdown("#### Local outbox")
    if not outbox:
        st.caption("No messages are queued.")
    else:
        for item in reversed(outbox):
            with st.container(border=True):
                st.write(f"**Status:** {item['status']} · **Queued:** {item['queued_at']}")
                st.write(f"Simulated arrival: {item['expected_arrival']}")
                st.json(item["payload"])
                if item["status"] == "queued (simulation only)" and st.button("Advance simulation: mark delivered", key=f"deliver-{item['id']}"):
                    on_deliver(item["id"])
                    st.rerun()
    st.caption("Advancing the delivery simulation changes only a local status field; it does not wait 20:14 or contact Earth.")
