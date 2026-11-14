"""Streamlit presentation components for CAELIVIS mission control."""

from datetime import date, datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from caelivis.insights import METRICS
from caelivis.storage import CREW_SOURCE, save_checkin

HAZARDS = [
    {"name": "Space radiation", "icon": "☀", "tag": "ENVIRONMENT", "description": "Beyond Earth's protective environment, radiation exposure is a mission hazard. This prototype has no radiation dosimeter feed, so health check-ins cannot measure exposure.", "connection": "No direct radiation observation is collected. Keep radiation monitoring and interpretation within mission systems and qualified flight-surgeon workflows.", "follow_up": "If a mission radiation alert is issued, follow the approved mission response and medical communication protocol."},
    {"name": "Isolation and confinement", "icon": "◉", "tag": "BEHAVIORAL HEALTH", "description": "A small crew living and working in a constrained environment can face behavioral-health and team challenges.", "connection": "Mood, stress, sleep, and cognitive well-being are self-reported context. A change is a prompt for conversation—not a diagnosis or proof of a hazard effect.", "follow_up": "Consider sharing persistent concerns with the crew medical officer or behavioral-health support team."},
    {"name": "Distance from Earth", "icon": "◎", "tag": "COMMUNICATIONS", "description": "Long distances increase communication latency and constrain real-time support and resupply.", "connection": "The 20 min 14 sec one-way delay is a demonstration setting, not a live mission calculation. This app queues locally and does not send data.", "follow_up": "Use established onboard decision and escalation procedures; do not wait on this prototype for urgent care."},
    {"name": "Gravity fields", "icon": "◌", "tag": "PHYSIOLOGY", "description": "Transitions between gravity environments and prolonged microgravity can affect human physiology and performance.", "connection": "Exercise minutes are logged as activity context only. This app does not measure gravitational exposure, balance, bone health, or countermeasure effectiveness.", "follow_up": "Discuss changes in function or exercise tolerance with the mission medical team under mission procedures."},
    {"name": "Hostile and closed environments", "icon": "⬡", "tag": "HABITAT", "description": "Spacecraft environments are engineered but can include environmental and operational hazards.", "connection": "The prototype does not ingest cabin atmosphere, acoustic, microbial, or equipment telemetry. Personal observations alone cannot identify an environmental exposure.", "follow_up": "Use dedicated environmental monitoring and report suspected cabin hazards through mission operations channels."},
]

PLOT_LAYOUT = {
    "template": "plotly_dark", "height": 265,
    "margin": {"l": 12, "r": 12, "t": 20, "b": 12},
    "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(8,24,39,.2)",
    "font": {"color": "#b5c7d7", "family": "Inter, system-ui, sans-serif", "size": 11},
    "xaxis": {"showgrid": False, "zeroline": False, "title": None},
    "yaxis": {"gridcolor": "rgba(145,168,186,.14)", "zeroline": False},
}


def _header(kicker: str, title: str, description: str) -> None:
    st.markdown(f'<p class="eyebrow">{kicker}</p>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<p class="page-description">{description}</p>', unsafe_allow_html=True)


def _mission_illustration() -> None:
    """Draw original accessible vector mission route; no external imagery."""
    st.markdown('''
    <div class="mission-art">
      <svg viewBox="0 0 920 270" role="img" aria-labelledby="route-title route-desc" xmlns="http://www.w3.org/2000/svg">
        <title id="route-title">Illustrative Earth-to-Mars mission route</title>
        <desc id="route-desc">Original vector diagram of Earth on the left, a spacecraft on a curved trajectory, and Mars on the right. Route is conceptual, not to scale.</desc>
        <defs>
          <linearGradient id="route-line" x1="0" x2="1"><stop offset="0" stop-color="#48DDF0"/><stop offset="1" stop-color="#F1A66B"/></linearGradient>
          <radialGradient id="earth-fill"><stop stop-color="#43C6D9"/><stop offset="1" stop-color="#145083"/></radialGradient>
          <radialGradient id="mars-fill"><stop stop-color="#F6B17E"/><stop offset="1" stop-color="#963F35"/></radialGradient>
        </defs>
        <path d="M108 176 C290 42 585 44 788 154" fill="none" stroke="url(#route-line)" stroke-width="2" stroke-dasharray="5 8" opacity=".8"/>
        <path d="M108 176 C290 42 585 44 788 154" fill="none" stroke="#48DDF0" stroke-width="14" opacity=".035"/>
        <circle cx="110" cy="176" r="47" fill="url(#earth-fill)" stroke="#82e9f4" stroke-opacity=".6"/>
        <path d="M77 160q16-14 28-2t19-2q12-15 28-4l-3 15q-16 5-18 17t-20 8q-8-13-24-9z" fill="#8ed2a9" opacity=".82"/>
        <path d="M65 190q25 12 49 7t43-6" fill="none" stroke="#b2eff6" stroke-opacity=".65" stroke-width="2"/>
        <circle cx="790" cy="154" r="39" fill="url(#mars-fill)" stroke="#ffd0a4" stroke-opacity=".72"/>
        <path d="M764 143q14-10 26-1t27-4M767 169q15-8 35-2" fill="none" stroke="#ffcf9c" stroke-opacity=".65" stroke-width="3"/>
        <g transform="translate(465 75) rotate(-8)" stroke="#bceef5" stroke-width="2" fill="#163d58">
          <path d="M-24 0 0-13 24 0 0 13z"/><path d="M-43-13h16v26h-16zM27-13h16v26H27z" fill="#246a8d"/><path d="M0-13v-16m-5 0h10"/>
          <circle cx="0" cy="0" r="4" fill="#48DDF0" stroke="none"/>
        </g>
        <circle cx="289" cy="92" r="2" fill="#e3f8ff"/><circle cx="653" cy="79" r="2" fill="#e3f8ff"/><circle cx="572" cy="206" r="1.5" fill="#e3f8ff"/>
        <text x="110" y="246" text-anchor="middle" class="svg-label">EARTH</text>
        <text x="465" y="38" text-anchor="middle" class="svg-label">CREWED DEEP-SPACE TRANSIT · CONCEPTUAL</text>
        <text x="790" y="216" text-anchor="middle" class="svg-label">MARS</text>
        <text x="465" y="112" text-anchor="middle" class="svg-small">MISSION ELAPSED · SOL 184 (SIMULATED)</text>
      </svg>
      <div class="mission-art-caption"><span>Earth departure</span><span>Not to scale · illustrative route only</span><span>Mars destination</span></div>
    </div>''', unsafe_allow_html=True)


def _source_name(value) -> str:
    if value in ("Synthetic demonstration", "Synthetic demonstration data"):
        return "Synthetic demonstration data"
    if value in ("Local check-in", "Crew-entered demonstration", CREW_SOURCE):
        return "Crew-entered demonstration data"
    return "Unspecified demonstration source"


def _sparkline(data: pd.DataFrame, column: str, label: str, color: str, unit: str) -> go.Figure | None:
    if data.empty or column not in data:
        return None
    frame = data.dropna(subset=[column]).tail(14)
    if frame.empty:
        return None
    fig = go.Figure(go.Scatter(
        x=frame["date"], y=frame[column], mode="lines+markers", name=label,
        line={"color": color, "width": 2.5}, marker={"size": 5, "color": color},
        text=frame["data_source"].map(_source_name) if "data_source" in frame else None,
        hovertemplate="%{x|%b %d}<br>%{y} " + unit + "<br>%{text}<extra></extra>",
    ))
    fig.update_layout(**PLOT_LAYOUT, height=180, showlegend=False, yaxis_title=unit)
    return fig


def render_overview(observations: pd.DataFrame, insights: list[dict]) -> None:
    _header("MISSION HEALTH / LIVE DEMONSTRATION", "Crew Health Overview", "Personal observations and synthetic reference data, presented for research demonstration—not medical assessment.")
    st.info("DEMO DATA · Synthetic and crew-entered demonstration records only. No observation is actual astronaut telemetry.")
    if observations.empty:
        st.warning("No valid observations are available. Review local-data warnings or add a demonstration check-in.")
        return
    _mission_illustration()
    latest = observations.iloc[-1]
    st.markdown('<div class="section-label">LATEST OBSERVATION · DISPLAY ONLY, NO CLINICAL THRESHOLDS</div>', unsafe_allow_html=True)
    metric_specs = [
        ("♥", "Heart rate", f"{int(latest['heart_rate_bpm'])}", "bpm", "Cardiovascular observation", "#48DDF0"),
        ("⌁", "Blood pressure", f"{int(latest['systolic_bp_mmhg'])}/{int(latest['diastolic_bp_mmhg'])}", "mmHg", "Systolic / diastolic", "#86B8FF"),
        ("◷", "Sleep", f"{float(latest['sleep_hours']):.1f}", "hours", "Self-reported duration", "#B9A6FF"),
        ("↗", "Activity", f"{int(latest['exercise_minutes'])}", "min", "Recorded exercise", "#79D9B3"),
    ]
    for row_start in (0,):
        cols = st.columns(4)
        for col, spec in zip(cols, metric_specs):
            icon, label, value, unit, context, accent = spec
            with col:
                st.markdown(f'<div class="vital-card" style="--accent:{accent}"><div class="vital-top"><span class="vital-icon">{icon}</span><span class="vital-state">OBSERVATION</span></div><div class="vital-label">{label}</div><div class="vital-value">{value}<span>{unit}</span></div><div class="vital-context">{context}</div></div>', unsafe_allow_html=True)
    status_cols = st.columns([1.2, 1, 1, 1])
    status_cols[0].markdown('<div class="status-panel"><span class="status-dot"></span><b>LOCAL / OFFLINE-FIRST</b><br><small>No network transmission</small></div>', unsafe_allow_html=True)
    status_cols[1].metric("Mission elapsed", "Sol 184", help="Static demonstration value.")
    status_cols[2].metric("One-way light-time", "20:14", help="Fixed communication simulation.")
    status_cols[3].metric("Records in view", len(observations), help="Synthetic sample and valid crew-entered demonstration records.")

    st.markdown('<div class="section-label">HEALTH TRENDS · RECENT DEMONSTRATION RECORDS</div>', unsafe_allow_html=True)
    chart_specs = [("Heart rate", "heart_rate_bpm", "#48DDF0", "bpm"), ("Blood pressure", "systolic_bp_mmhg", "#86B8FF", "mmHg · systolic"), ("Sleep", "sleep_hours", "#B9A6FF", "hours"), ("Exercise", "exercise_minutes", "#79D9B3", "minutes"), ("Mood & wellbeing", "mood_1_5", "#FFC878", "self-rating / 5")]
    for index in (0, 3):
        cols = st.columns(3 if index == 0 else 2)
        for col, (title, column, color, unit) in zip(cols, chart_specs[index:index + (3 if index == 0 else 2)]):
            with col, st.container(border=True):
                st.markdown(f"**{title}** <span class='chart-unit'>{unit}</span>", unsafe_allow_html=True)
                fig = _sparkline(observations, column, title, color, unit)
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=f"overview-{column}")
                else:
                    st.caption("No valid observations to chart.")
    left, right = st.columns([1.35, 1])
    with left, st.container(border=True):
        st.markdown("**Recent observations**")
        display = observations.tail(7).copy()
        display["date"] = display["date"].dt.strftime("%b %d")
        display["data_source"] = display["data_source"].map(_source_name)
        display = display[["date", "heart_rate_bpm", "sleep_hours", "exercise_minutes", "mood_1_5", "data_source"]]
        st.dataframe(display.iloc[::-1], hide_index=True, use_container_width=True)
    with right, st.container(border=True):
        st.markdown("**Observation provenance**")
        source_counts = observations["data_source"].map(_source_name).value_counts()
        for source in ("Synthetic demonstration data", "Crew-entered demonstration data"):
            st.markdown(f"<div class='provenance-row'><span>{source}</span><b>{int(source_counts.get(source, 0))}</b></div>", unsafe_allow_html=True)
        st.caption(f"Latest record · {_source_name(latest.get('data_source'))}")
        st.caption("Record availability is not a clinical status.")
    st.markdown('<div class="section-label">PERSONAL-BASELINE COMPARISONS · DESCRIPTIVE, NOT MEDICAL ALERTS</div>', unsafe_allow_html=True)
    if insights:
        for item in insights[:4]:
            st.warning(f"{item['metric']} is {abs(item['change_pct']):.0f}% {item['direction']} than its recent personal median ({item['baseline']:.1f} {item['unit']}). Descriptive signal only; not a medical threshold.")
    else:
        st.success("No configurable relative changes surfaced. This does not establish medical well-being.")
    st.caption("Mission elapsed and communication timing are static simulation values. Use mission procedures and qualified medical oversight for concerns.")


def render_checkin() -> None:
    _header("CREW SELF-REPORT / LOCAL ENTRY", "Daily Health Check-In", "Add an illustrative observation to this device. Form bounds are data-entry guardrails, not medical limits.")
    st.warning("Demonstration values only. This is not a medical record or clinical tool. For urgent concerns, follow mission protocols and seek qualified medical oversight.")
    with st.form("daily_checkin", clear_on_submit=False):
        st.markdown('<div class="section-label">01 / OBSERVATION CONTEXT</div>', unsafe_allow_html=True)
        observed_date = st.date_input("Observation date", value=date.today(), max_value=date.today(), key="checkin_date")
        first, second, third = st.columns(3)
        with first, st.container(border=True):
            st.markdown("**♥ Cardiovascular & temperature**")
            hr = st.number_input("Heart rate (beats/min)", min_value=35, max_value=200, value=68, step=1)
            systolic = st.number_input("Blood pressure — systolic (mmHg)", min_value=60, max_value=250, value=118, step=1)
            diastolic = st.number_input("Blood pressure — diastolic (mmHg)", min_value=30, max_value=150, value=76, step=1)
            temp = st.number_input("Body temperature (°C)", min_value=30.0, max_value=43.0, value=36.7, step=0.1, format="%.1f")
            has_glucose = st.checkbox("Include optional blood glucose")
            glucose = st.number_input("Blood glucose (mg/dL)", min_value=20, max_value=600, value=90, step=1, disabled=not has_glucose)
        with second, st.container(border=True):
            st.markdown("**◷ Rest & activity**")
            sleep = st.number_input("Sleep duration (hours)", min_value=0.0, max_value=24.0, value=7.5, step=0.25)
            sleep_quality = st.slider("Sleep quality (self-rating)", 1, 5, 3, help="Personal demonstration rating, not a validated instrument.")
            exercise = st.number_input("Exercise / physical activity (minutes)", min_value=0, max_value=360, value=45, step=5)
        with third, st.container(border=True):
            st.markdown("**◉ Mood & cognitive wellbeing**")
            mood = st.slider("Mood (self-rating)", 1, 5, 3, help="Personal demonstration rating; not a screening instrument.")
            stress = st.slider("Stress (self-rating)", 1, 5, 3, help="Personal demonstration rating; not a validated clinical scale.")
            cognitive = st.slider("Cognitive well-being (self-rating)", 1, 5, 3, help="Personal rating; not a performance test.")
            fatigue = st.slider("Fatigue (self-rating)", 1, 5, 3)
        st.markdown('<div class="form-provenance">SOURCE LABEL · Crew-entered demonstration data · Stored locally only</div>', unsafe_allow_html=True)
        submitted = st.form_submit_button("Save demonstration check-in locally", type="primary")
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
                st.success("Crew-entered demonstration record saved locally. No network transmission occurred.")
                st.rerun()
    st.caption("Historical observation date is preserved. Local records are not encrypted or access-controlled; never enter real health information.")


def build_trend_figure(observations: pd.DataFrame, column: str, label: str, unit: str, baseline: float | None = None):
    """Construct an accessible Plotly trend chart, or None if no values can be drawn."""
    if observations.empty or column not in observations:
        return None
    valid = observations.dropna(subset=[column]).copy()
    if valid.empty:
        return None
    sources = valid["data_source"].map(_source_name) if "data_source" in valid else pd.Series("Demonstration data", index=valid.index)
    chart = go.Figure()
    chart.add_trace(go.Scatter(
        x=valid["date"], y=valid[column], mode="lines+markers", name=label,
        line={"color": "#48DDF0", "width": 3}, marker={"size": 7, "color": "#A9DFF5"},
        text=sources, hovertemplate="%{x|%b %d, %Y}<br>%{y} " + unit + "<br>%{text}<extra></extra>",
    ))
    if baseline is not None:
        chart.add_hline(y=baseline, line_dash="dash", line_color="#FFC878", annotation_text="Personal reference median")
    chart.update_layout(**PLOT_LAYOUT, height=390, showlegend=False, yaxis_title=unit, xaxis_title="Observation date", hoverlabel={"bgcolor": "#122B43", "font": {"color": "#F3F7FB"}})
    chart.update_xaxes(showgrid=False)
    return chart


def render_trends(observations: pd.DataFrame) -> None:
    _header("PERSONAL REFERENCE / TREND EXPLORER", "Personal Baseline & Trends", "Explore a single measure over time against a configurable personal reference.")
    st.info("Trend data consists only of labeled synthetic or crew-entered demonstrations—not astronaut telemetry. Relative changes are descriptive display cues, not clinical thresholds.")
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
    control_a, control_b = st.columns(2)
    with control_a:
        window = st.slider("Personal reference window (prior records)", 2, max_window, min(7, max_window))
    with control_b:
        threshold = st.slider("Highlight relative difference (%)", 5, 50, 15, help="Visual preference only; not a medical threshold.")
    baseline = valid[column].iloc[:-1].tail(window).median() if len(valid) > 1 else float(valid[column].iloc[-1])
    latest = float(valid[column].iloc[-1])
    delta_pct = ((latest - baseline) / abs(baseline) * 100) if baseline else 0.0
    k1, k2, k3 = st.columns(3)
    k1.metric("Latest observation", f"{latest:g} {unit}")
    k2.metric(f"Recent median · {window} records", f"{baseline:.1f} {unit}")
    k3.metric("Relative difference", f"{delta_pct:+.1f}%", help="Descriptive comparison only; not clinical interpretation.")
    chart = build_trend_figure(valid, column, metric_name, unit, baseline)
    st.plotly_chart(chart, use_container_width=True, config={"displaylogo": False}, key="personal-trend-chart")
    provenance = valid["data_source"].map(_source_name).value_counts().to_dict()
    st.markdown('<div class="section-label">VISIBLE DATA PROVENANCE</div>', unsafe_allow_html=True)
    pcols = st.columns(2)
    for col, source in zip(pcols, ("Synthetic demonstration data", "Crew-entered demonstration data")):
        col.markdown(f"<div class='provenance-row'><span>{source}</span><b>{int(provenance.get(source, 0))}</b></div>", unsafe_allow_html=True)
    if abs(delta_pct) >= threshold:
        st.warning(f"The latest value differs from this selected personal reference by more than {threshold}%. Display cue only; consult qualified medical personnel for concerns.")
    st.caption("Chart descriptions include date, unit, and demonstration-data source. Baseline excludes the latest observation.")


def render_hazards(observations: pd.DataFrame, insights: list[dict]) -> None:
    _header("HAZARD CONTEXT / HUMAN OVERSIGHT", "Health Insights & Alerts", "Five NASA human-spaceflight hazard areas and what this demonstration can—and cannot—show.")
    st.error("This prototype cannot diagnose or triage. For urgent or concerning symptoms, follow mission medical escalation procedures and contact qualified medical personnel.")
    st.markdown('<div class="section-label">PERSONAL-BASELINE SIGNALS · INFORMATIONAL ONLY</div>', unsafe_allow_html=True)
    if insights:
        for item in insights:
            st.warning(f"{item['metric']}: {abs(item['change_pct']):.1f}% {item['direction']} than recent median ({item['baseline']:.1f} {item['unit']}). Source: {_source_name(item['source'])}. Descriptive comparison, not a clinical alert.")
    else:
        st.success("No relative changes exceeded the current display setting. This is not a health clearance.")
    st.markdown('<div class="section-label">NASA HUMAN-SPACEFLIGHT HAZARDS</div>', unsafe_allow_html=True)
    st.caption("Educational summaries; these cards do not estimate individual hazard exposure or predict health outcomes.")
    columns = st.columns(2)
    for index, hazard in enumerate(HAZARDS):
        with columns[index % 2], st.container(border=True):
            st.markdown(f"<div class='hazard-kicker'><span class='hazard-icon'>{hazard['icon']}</span><span>{hazard['tag']}</span></div>", unsafe_allow_html=True)
            st.markdown(f"### {hazard['name']}")
            st.write(hazard["description"])
            with st.expander("Observation context & appropriate follow-up"):
                st.markdown(f"**What this app can show:** {hazard['connection']}")
                st.markdown(f"**Appropriate follow-up:** {hazard['follow_up']}")
                st.markdown("**NASA references:** [NASA Human Research Program](https://www.nasa.gov/hrp/) · [NASA Human Research Roadmap](https://humanresearchroadmap.nasa.gov/)")
    st.caption(f"{len(observations)} demonstration records are available. All comparisons are descriptive and rule-based; no AI or clinical decision system is connected.")


def _communications_diagram() -> None:
    st.markdown('''
    <div class="comms-art">
      <svg viewBox="0 0 760 145" role="img" aria-labelledby="comms-title comms-desc" xmlns="http://www.w3.org/2000/svg">
        <title id="comms-title">Simulated local Earth communications path</title>
        <desc id="comms-desc">Illustrative Earth and spacecraft separated by a dotted one-way path. The message remains in a local simulation; no transmission occurs.</desc>
        <circle cx="100" cy="70" r="34" fill="#145083" stroke="#48DDF0" stroke-width="2"/><path d="M77 66q17-17 30-3t24-5l7 16q-12 5-14 16t-21 6q-8-15-23-8z" fill="#8ed2a9"/>
        <path d="M147 70H603" stroke="#48DDF0" stroke-width="2" stroke-dasharray="5 8" opacity=".8"/>
        <g transform="translate(380 70)" stroke="#A9DFF5" stroke-width="2" fill="#163d58"><path d="M-20 0 0-11 20 0 0 11z"/><path d="M-37-11h13v22h-13zM24-11h13v22H24z" fill="#246a8d"/><circle r="3" fill="#48DDF0" stroke="none"/></g>
        <text x="100" y="128" text-anchor="middle" class="svg-label">EARTH · CONCEPT</text><text x="380" y="128" text-anchor="middle" class="svg-label">LOCAL QUEUE · NOT TRANSMITTED</text><text x="652" y="128" text-anchor="middle" class="svg-label">SPACECRAFT · CONCEPT</text>
        <text x="380" y="47" text-anchor="middle" class="svg-small">ONE-WAY DELAY SIMULATION · 20 MIN 14 SEC</text>
      </svg>
    </div>''', unsafe_allow_html=True)


def render_privacy(observations: pd.DataFrame, outbox: list[dict], on_queue, on_deliver) -> None:
    _header("LOCAL DATA / COMMS SIMULATOR", "Privacy & Communications", "An offline-first demonstration of local storage and delayed communications. No actual transmission is implemented.")
    st.markdown('<div class="status-panel"><span class="status-dot"></span><b>OFFLINE-FIRST · LOCAL SIMULATION</b><br><small>There is no network connection or outbound message behavior in this feature.</small></div>', unsafe_allow_html=True)
    _communications_diagram()
    c1, c2, c3 = st.columns(3)
    c1.metric("One-way delay", "20 min 14 sec")
    c2.metric("Queue", "Local only")
    c3.metric("Transmission", "None")
    st.markdown("#### Data handling")
    st.write("Check-ins are written to `data/local/checkins.json` by default. `CAELIVIS_DATA_DIR` can select another local folder. Sample observations are synthetic demonstrations. No health data is transmitted.")
    st.warning("Local JSON is not encrypted or access-controlled. Use demonstration values only; do not enter actual personal or astronaut health information.")
    if st.button("Queue latest summary for simulation", type="primary", disabled=observations.empty):
        try:
            item = on_queue()
        except (OSError, RuntimeError, ValueError) as exc:
            st.error(f"Could not queue safely: {exc}")
        else:
            if item:
                st.success("Summary queued locally only. No communication occurred.")
                st.rerun()
    st.markdown('<div class="section-label">LOCAL OUTBOX · SIMULATION ONLY</div>', unsafe_allow_html=True)
    if not outbox:
        st.caption("No messages are queued.")
    else:
        for item in reversed(outbox):
            with st.container(border=True):
                left, right = st.columns([3, 1])
                with left:
                    st.markdown(f"**Observation timestamp:** {item['observation_timestamp']}")
                    st.markdown(f"**Queue time:** {item['queued_at']} UTC")
                    st.markdown(f"**One-way delay:** {int(item['one_way_delay_seconds']) // 60} minutes {int(item['one_way_delay_seconds']) % 60} seconds")
                    st.markdown(f"**Calculated simulated arrival:** {item['expected_arrival']} UTC")
                with right:
                    st.markdown(f"<div class='outbox-status'>{item['status']}</div>", unsafe_allow_html=True)
                st.caption("Local simulation only. This record was not transmitted to Earth.")
                st.json(item["payload"])
                if item["status"] == "Queued — Not Transmitted" and st.button("Advance local simulation", key=f"deliver-{item['id']}"):
                    try:
                        on_deliver(item["id"])
                    except (OSError, RuntimeError):
                        st.error("Could not update the simulated local status.")
                    else:
                        st.rerun()
'''
