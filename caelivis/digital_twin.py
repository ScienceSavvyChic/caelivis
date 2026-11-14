"""Offline-first astronaut observation explorer using existing CAELIVIS fields."""

from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

REGION_FIELDS = {
    "Head": (
        ("Cognitive wellbeing", "cognitive_wellbeing_1_5", "self-rating / 5"),
        ("Mood", "mood_1_5", "self-rating / 5"),
        ("Stress", "stress_1_5", "self-rating / 5"),
        ("Sleep duration", "sleep_hours", "hours"),
        ("Fatigue", "fatigue_1_5", "self-rating / 5"),
    ),
    "Chest": (
        ("Heart rate", "heart_rate_bpm", "beats/min"),
        ("Systolic blood pressure", "systolic_bp_mmhg", "mmHg"),
        ("Diastolic blood pressure", "diastolic_bp_mmhg", "mmHg"),
    ),
    "Body": (
        ("Body temperature", "temperature_c", "°C"),
        ("Exercise / activity", "exercise_minutes", "minutes"),
        ("Blood glucose", "glucose_mg_dl", "mg/dL"),
    ),
}


def summarize_region(observations: pd.DataFrame, region: str, baseline_records: int = 7) -> list[dict]:
    """Return latest available field values and preceding-record medians."""
    if region not in REGION_FIELDS or observations.empty or "date" not in observations:
        return []
    ordered = observations.sort_values("date")
    result = []
    for label, field, unit in REGION_FIELDS[region]:
        if field not in ordered.columns:
            continue
        valid = ordered.dropna(subset=[field])
        if valid.empty:
            continue
        latest = valid.iloc[-1]
        previous = valid.iloc[:-1].tail(baseline_records)
        baseline = pd.to_numeric(previous[field], errors="coerce").median() if not previous.empty else None
        timestamp = latest.get("observation_timestamp")
        if timestamp is None or pd.isna(timestamp):
            timestamp = latest["date"]
        result.append({
            "label": label,
            "field": field,
            "value": float(latest[field]),
            "unit": unit,
            "baseline": float(baseline) if baseline is not None and math.isfinite(float(baseline)) else None,
            "source": str(latest.get("data_source", "Unspecified demonstration source")),
            "observed_at": str(timestamp),
        })
    return result


def astronaut_svg(active_region: str) -> str:
    """Original, local SVG silhouette with a visually selected body region."""
    if active_region not in REGION_FIELDS:
        active_region = "Chest"
    classes = {name: (" active" if name == active_region else "") for name in REGION_FIELDS}
    return f'''<div class="twin-shell">
    <svg class="astronaut-twin" viewBox="0 0 360 620" role="img" aria-labelledby="twin-title twin-desc" xmlns="http://www.w3.org/2000/svg">
      <title id="twin-title">Conceptual CAELIVIS astronaut digital twin</title>
      <desc id="twin-desc">Original spacesuit illustration; {active_region} observation region highlighted. This is not a scan or connected sensor model.</desc>
      <defs><linearGradient id="suit" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#d7f0f7"/><stop offset=".42" stop-color="#527c98"/><stop offset="1" stop-color="#193957"/></linearGradient><linearGradient id="visor" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#1a6983"/><stop offset=".55" stop-color="#102f50"/><stop offset="1" stop-color="#54d9e7"/></linearGradient><radialGradient id="aura"><stop stop-color="#48ddf0" stop-opacity=".2"/><stop offset="1" stop-color="#48ddf0" stop-opacity="0"/></radialGradient></defs>
      <ellipse cx="180" cy="315" rx="150" ry="285" fill="url(#aura)"/><ellipse cx="180" cy="590" rx="92" ry="12" fill="#48ddf0" opacity=".13"/>
      <path d="M118 176Q94 186 80 218L47 342Q42 365 61 372L78 377Q93 379 99 359L132 269L135 382L113 528Q110 546 129 551L151 554Q169 554 171 535L183 420L194 535Q196 554 215 554L237 551Q254 548 248 528L226 382L229 269L261 359Q267 379 284 376L302 371Q320 365 313 342L280 218Q266 186 242 176Z" fill="url(#suit)" stroke="#b8e4f2" stroke-width="3"/>
      <path d="M137 177Q180 161 223 177L231 211Q180 229 129 211Z" fill="#314f6b" stroke="#a9dff5" stroke-width="3"/><circle cx="180" cy="119" r="68" fill="#bedce7" stroke="#d5f7ff" stroke-width="5"/><ellipse cx="180" cy="120" rx="53" ry="46" fill="url(#visor)" stroke="#48ddf0" stroke-width="4"/><path d="M143 103Q176 76 215 99" fill="none" stroke="#c9f8ff" stroke-width="4" opacity=".6"/>
      <rect x="143" y="264" width="74" height="84" rx="16" fill="#183b58" stroke="#82ddea" stroke-width="3"/><rect x="155" y="278" width="50" height="19" rx="5" fill="#102a43" stroke="#48ddf0"/><circle cx="166" cy="319" r="7" fill="#48ddf0"/><circle cx="194" cy="319" r="7" fill="#ffc878"/>
      <path d="M137 386h86M133 399h94M119 210L88 326M241 210L272 326M135 445L124 522M225 445L236 522" stroke="#48ddf0" stroke-opacity=".55" stroke-width="3"/>
      <circle class="twin-region head{classes['Head']}" cx="180" cy="119" r="78" fill="none" stroke="#48ddf0" stroke-width="3" stroke-dasharray="5 8"/><rect class="twin-region chest{classes['Chest']}" x="116" y="222" width="128" height="149" rx="34" fill="none" stroke="#48ddf0" stroke-width="3" stroke-dasharray="6 8"/><path class="twin-region body{classes['Body']}" d="M105 374H255V558H105Z" fill="none" stroke="#48ddf0" stroke-width="3" stroke-dasharray="6 8"/>
      <text x="180" y="603" text-anchor="middle" class="twin-svg-label">ILLUSTRATIVE SUIT MODEL · NOT A SCAN</text>
    </svg><div class="twin-source-note">CONCEPTUAL BIOMETRIC MAP · DEMONSTRATION RECORDS ONLY</div></div>'''


def render_digital_twin(observations: pd.DataFrame) -> None:
    """Interactive region selection and data details, all available offline."""
    st.markdown('<div class="section-label">NEUROVIU · INTERACTIVE PHYSIOLOGICAL EXPLORER</div>', unsafe_allow_html=True)
    st.markdown("Select a body region to inspect existing demonstration observations. The anatomical illustration is conceptual, not a scan, sensor feed, or medical model.")
    controls, figure, details = st.columns([.82, 1.05, 1.45], gap="large")
    with controls:
        region = st.radio("Select astronaut region", tuple(REGION_FIELDS), index=1, key="digital_twin_region", help="Keyboard-accessible region selector changes the illustration and associated observations.")
        st.markdown('<div class="twin-status"><span class="twin-dot"></span>LOCAL DIGITAL-TWIN VIEW<br><small>No live sensors connected</small></div>', unsafe_allow_html=True)
    with figure:
        st.markdown(astronaut_svg(region), unsafe_allow_html=True)
    with details:
        st.markdown(f"#### {region} observations")
        records = summarize_region(observations, region)
        if not records:
            st.info("No observation values are available for this region yet.")
        for item in records:
            with st.container(border=True):
                st.markdown(f"**{item['label']}**")
                st.markdown(f"<div class='twin-reading'>{item['value']:g}<span> {item['unit']}</span></div>", unsafe_allow_html=True)
                st.caption(f"Recorded: {item['observed_at']} · {item['source']}")
                if item["baseline"] is None:
                    st.caption("Recent personal median unavailable; an earlier record is needed.")
                else:
                    st.caption(f"Recent personal median: {item['baseline']:g} {item['unit']} · descriptive reference only")
        st.caption("Synthetic and crew-entered demo records only; not astronaut telemetry. No medical thresholds are applied.")

    with st.expander("Signals & astronaut HUD concept", expanded=False):
        signal, hud = st.columns(2)
        with signal:
            st.markdown("**Physiological signal context**")
            heart = next((x for x in summarize_region(observations, "Chest") if x["field"] == "heart_rate_bpm"), None)
            if heart:
                st.metric("Latest recorded heart rate", f"{heart['value']:g} beats/min", help=f"{heart['source']} · {heart['observed_at']}")
            else:
                st.info("No heart-rate observation is available.")
            st.warning("Illustrative ECG-style trace only. CAELIVIS does not collect ECG signals; the trace below is not physiological data.")
            x = [i / 100 for i in range(501)]
            y = [.06 * math.sin(i / 11) + .62 * math.exp(-((i - 180) / 8) ** 2) - .22 * math.exp(-((i - 193) / 4) ** 2) + .12 * math.exp(-((i - 220) / 17) ** 2) for i in range(501)]
            chart = go.Figure(go.Scatter(x=x, y=y, mode="lines", line={"color": "#48DDF0", "width": 2}, hoverinfo="skip", name="Illustrative trace"))
            chart.update_layout(template="plotly_dark", height=170, margin={"l": 5, "r": 5, "t": 5, "b": 5}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis={"visible": False}, yaxis={"visible": False}, showlegend=False)
            st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False}, key="illustrative-ecg")
        with hud:
            st.markdown("**Spacesuit HUD · design demonstration**")
            st.markdown('<div class="hud-panel" role="img" aria-label="Conceptual astronaut HUD preview; no hardware integration"><span>CAELIVIS / LOCAL DEMO</span><b>VITAL OBSERVATIONS</b><div>♥ HEART RATE <strong>Recorded observation</strong></div><div>⌁ BLOOD PRESSURE <strong>Recorded observation</strong></div><div>◷ SLEEP / WELLBEING <strong>Self-report</strong></div><small>NO HARDWARE INTEGRATION · NO LIVE TELEMETRY</small></div>', unsafe_allow_html=True)


def region_names() -> tuple[str, ...]:
    """Stable region list for automated interaction coverage."""
    return tuple(REGION_FIELDS)
