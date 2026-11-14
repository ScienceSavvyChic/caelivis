"""Offline-first interactive anatomical view using only recorded demo observations."""

from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Every displayed measure maps directly to fields already present in the CAELIVIS
# sample/check-in schema. These are associations for exploration, not diagnoses.
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
    """Return latest available field values and recent medians for one region."""
    if region not in REGION_FIELDS or observations.empty or "date" not in observations:
        return []
    ordered = observations.sort_values("date")
    summaries = []
    for label, field, unit in REGION_FIELDS[region]:
        if field not in ordered.columns:
            continue
        valid = ordered.dropna(subset=[field])
        if valid.empty:
            continue
        latest = valid.iloc[-1]
        previous = valid.iloc[:-1].tail(baseline_records)
        baseline = pd.to_numeric(previous[field], errors="coerce").median() if not previous.empty else None
        value = float(latest[field])
        source = str(latest.get("data_source", "Unspecified demonstration source"))
        observed_at = latest.get("observation_timestamp")
        if pd.isna(observed_at) if not isinstance(observed_at, str) else False:
            observed_at = None
        if not observed_at:
            observed_at = latest["date"]
        summaries.append({
            "label": label,
            "field": field,
            "value": value,
            "unit": unit,
            "baseline": float(baseline) if baseline is not None and math.isfinite(float(baseline)) else None,
            "source": source,
            "observed_at": str(observed_at),
        })
    return summaries


def _astronaut_svg(active_region: str) -> str:
    """Original, local SVG suit silhouette. Region changes follow keyboard control."""
    active = {name.lower(): (" active" if name == active_region else "") for name in REGION_FIELDS}
    return f'''<div class="twin-shell">
      <svg class="astronaut-twin" viewBox="0 0 360 620" role="img" aria-labelledby="twin-title twin-desc" xmlns="http://www.w3.org/2000/svg">
        <title id="twin-title">CAELIVIS conceptual astronaut digital twin</title>
        <desc id="twin-desc">Original front-facing spacesuit silhouette. The {active_region} observation region is highlighted. Choose Head, Chest, or Body with the adjacent keyboard-accessible control to inspect available demonstration observations.</desc>
        <defs>
          <linearGradient id="suit" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#d7f0f7"/><stop offset=".42" stop-color="#527c98"/><stop offset="1" stop-color="#193957"/></linearGradient>
          <linearGradient id="visor" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#1a6983"/><stop offset=".55" stop-color="#102f50"/><stop offset="1" stop-color="#54d9e7"/></linearGradient>
          <radialGradient id="aura"><stop stop-color="#48ddf0" stop-opacity=".2"/><stop offset="1" stop-color="#48ddf0" stop-opacity="0"/></radialGradient>
          <filter id="glow"><feGaussianBlur stdDeviation="5" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
        </defs>
        <ellipse cx="180" cy="315" rx="150" ry="285" fill="url(#aura)"/>
        <ellipse cx="180" cy="590" rx="92" ry="12" fill="#48ddf0" opacity=".13"/>
        <path d="M118 176 Q94 186 80 218 L47 342 Q42 365 61 372 L78 377 Q93 379 99 359 L132 269 L135 382 L113 528 Q110 546 129 551 L151 554 Q169 554 171 535 L183 420 L194 535 Q196 554 215 554 L237 551 Q254 548 248 528 L226 382 L229 269 L261 359 Q267 379 284 376 L302 371 Q320 365 313 342 L280 218 Q266 186 242 176 Z" fill="url(#suit)" stroke="#b8e4f2" stroke-width="3"/>
        <path d="M137 177 Q180 161 223 177 L231 211 Q180 229 129 211 Z" fill="#314f6b" stroke="#a9dff5" stroke-width="3"/>
        <circle cx="180" cy="119" r="68" fill="#bedce7" stroke="#d5f7ff" stroke-width="5"/>
        <ellipse cx="180" cy="120" rx="53" ry="46" fill="url(#visor)" stroke="#48ddf0" stroke-width="4"/>
        <path d="M143 103 Q176 76 215 99" fill="none" stroke="#c9f8ff" stroke-width="4" opacity=".6"/>
        <rect x="143" y="264" width="74" height="84" rx="16" fill="#183b58" stroke="#82ddea" stroke-width="3"/>
        <rect x="155" y="278" width="50" height="19" rx="5" fill="#102a43" stroke="#48ddf0"/>
        <circle cx="166" cy="319" r="7" fill="#48ddf0"/><circle cx="194" cy="319" r="7" fill="#ffc878"/>
        <path d="M137 386h86M133 399h94" stroke="#a9dff5" stroke-opacity=".45" stroke-width="3"/>
        <path d="M119 210 L88 326 M241 210 L272 326 M135 445 L124 522 M225 445 L236 522" stroke="#48ddf0" stroke-opacity=".6" stroke-width="3"/>
        <g class="region-head{active['head']}"><circle cx="180" cy="119" r="78" fill="none" stroke="#48ddf0" stroke-width="3" stroke-dasharray="5 8"/></g>
        <g class="region-chest{active['chest']}"><rect x="116" y="222" width="128" height="149" rx="34" fill="none" stroke="#48ddf0" stroke-width="3" stroke-dasharray="6 8"/></g>
        <g class="region-body{active['body']}"><path d="M105 374 L255 374 L255 558 L105 558 Z" fill="none" stroke="#48ddf0" stroke-width="3" stroke-dasharray="6 8"/></g>
        <text x="180" y="603" text-anchor="middle" class="twin-svg-label">ILLUSTRATIVE SUIT MODEL · NOT A SCAN</text>
      </svg>
      <div class="twin-source-note">CONCEPTUAL BIOMETRIC MAP · DEMONSTRATION RECORDS ONLY</div>
    </div>'''


def _baseline_text(item: dict) -> str:
    if item["baseline"] is None:
        return "Baseline unavailable · requires earlier record"
    return f"Recent personal median: {item['baseline']:g} {item['unit']} (descriptive reference)"


def render_digital_twin(observations: pd.DataFrame) -> None:
    """Present an interactive, offline-first astronaut data explorer."""
    st.markdown('<div class="section-label">NEUROVIU · INTERACTIVE PHYSIOLOGICAL EXPLORER</div>', unsafe_allow_html=True)
    st.markdown("Choose a body region to inspect the available labeled demonstration observations. The anatomical illustration is conceptual; it is not a scan, sensor feed, or medical model.")
    left, model, detail = st.columns([0.85, 1.1, 1.4], gap="large")
    with left:
        region = st.radio(
            "Select astronaut region", tuple(REGION_FIELDS), index=1,
            key="digital_twin_region", help="Keyboard-accessible region selector updates the highlighted suit area and observation panel.",
        )
        st.markdown('<div class="twin-status"><span class="twin-dot"></span>LOCAL DIGITAL-TWIN VIEW<br><small>No live sensors connected</small></div>', unsafe_allow_html=True)
        st.caption("Region choices group recorded self-report fields for exploration; they do not imply anatomical measurement.")
    with model:
        st.markdown(_astronaut_svg(region), unsafe_allow_html=True)
    with detail:
        st.markdown(f"#### {region} observations")
        records = summarize_region(observations, region)
        if not records:
            st.info("No observation values are available for this region yet.")
        for item in records:
            with st.container(border=True):
                st.markdown(f"**{item['label']}**")
                st.markdown(f"<div class='twin-reading'>{item['value']:g}<span> {item['unit']}</span></div>", unsafe_allow_html=True)
                st.caption(f"Recorded: {item['observed_at']} · {item['source']}")
                st.caption(_baseline_text(item))
        st.caption("All values are synthetic or crew-entered demonstration data—not astronaut telemetry. Comparisons are not clinical thresholds.")

    with st.expander("Signals & HUD concept", expanded=False):
        latest_records = summarize_region(observations, "Chest")
        heart = next((item for item in latest_records if item["field"] == "heart_rate_bpm"), None)
        signal_col, hud_col = st.columns(2)
        with signal_col:
            st.markdown("**Physiological signal context**")
            if heart:
                st.metric("Latest recorded heart rate", f"{heart['value']:g} beats/min", help=f"{heart['source']} · recorded {heart['observed_at']}")
            else:
                st.info("No heart-rate observation is available.")
            st.warning("Illustrative ECG-style waveform only. No ECG signal is collected or available; this trace is not physiological data.")
            waveform_x = [i / 100 for i in range(501)]
            waveform_y = [0.06 * math.sin(i / 11) + (0.62 * math.exp(-((i - 180) / 8) ** 2)) - (0.22 * math.exp(-((i - 193) / 4) ** 2)) + (0.12 * math.exp(-((i - 220) / 17) ** 2)) for i in range(501)]
            fig = go.Figure(go.Scatter(x=waveform_x, y=waveform_y, mode="lines", line={"color": "#48DDF0", "width": 2}, hoverinfo="skip", name="Illustrative waveform"))
            fig.update_layout(template="plotly_dark", height=170, margin={"l": 5, "r": 5, "t": 5, "b": 5}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis={"visible": False}, yaxis={"visible": False}, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="illustrative-ecg")
        with hud_col:
            st.markdown("**Spacesuit HUD · design demonstration**")
            st.markdown('<div class="hud-panel" role="img" aria-label="Conceptual spacesuit heads-up display, not connected to hardware"><span>CAELIVIS / LOCAL DEMO</span><b>VITAL OBSERVATIONS</b><div>♥ HEART RATE <strong>Recorded only</strong></div><div>⌁ BLOOD PRESSURE <strong>Recorded only</strong></div><div>◷ SLEEP / WELLBEING <strong>Self-report</strong></div><small>NO HARDWARE INTEGRATION · NO LIVE TELEMETRY</small></div>', unsafe_allow_html=True)


def testable_region_names() -> tuple[str, ...]:
    """Expose stable region labels for UI coverage without coupling tests to SVG markup."""
    return tuple(REGION_FIELDS)
