"""CAELIVIS: offline-first health trend demonstration for spaceflight."""

from pathlib import Path

import streamlit as st

from caelivis.data import load_observations
from caelivis.insights import build_insights
from caelivis.storage import load_checkins_with_warnings, load_outbox_with_warnings, mark_outbox_delivered, queue_latest_summary
from caelivis.views import render_checkin, render_hazards, render_overview, render_privacy, render_trends

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="CAELIVIS | Crew Health Intelligence", page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { color-scheme: dark; }
.stApp { background: radial-gradient(ellipse at 60% -20%, #12334d 0%, #091b2d 40%, #071525 85%); color: #F3F7FB; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#0B1F35,#071525); border-right: 1px solid #24415a; }
[data-testid="stSidebar"] > div { padding-top: 1.1rem; }
.block-container { max-width: 1500px; padding-top: 1.5rem; padding-bottom: 3rem; }
h1,h2,h3 { color:#F3F7FB; letter-spacing:-.025em; font-family:Manrope,system-ui,sans-serif; }
h1 { font-size:clamp(2rem,4vw,3rem)!important; font-weight:800!important; margin-bottom:.25rem!important; }
h2 { font-size:1.55rem!important; }
h3 { font-size:1.15rem!important; }
p, label, [data-testid="stMarkdownContainer"] { color:#d5e0e9; }
.eyebrow,.section-label { color:#48DDF0; text-transform:uppercase; letter-spacing:.15em; font:500 .72rem 'DM Mono',monospace; margin:1.1rem 0 .45rem; }
.page-description { color:#A9DFF5; max-width:850px; margin:.1rem 0 1.3rem; font-size:1rem; }
[data-testid="stMetric"] { background:linear-gradient(145deg,rgba(18,43,67,.94),rgba(11,31,53,.86)); border:1px solid #294963; padding:1rem 1.1rem; border-radius:14px; box-shadow:0 10px 24px rgba(0,0,0,.12); }
[data-testid="stMetricLabel"] { color:#91A8BA; font:500 .74rem 'DM Mono',monospace; letter-spacing:.05em; }
[data-testid="stMetricValue"] { color:#F3F7FB; font-family:Manrope,system-ui,sans-serif; font-weight:750; }
div[data-testid="stForm"] { background:rgba(11,31,53,.56); padding:1.25rem; border:1px solid #294963; border-radius:18px; }
div[data-testid="stForm"] [data-testid="stVerticalBlockBorderWrapper"] { background:linear-gradient(145deg,rgba(18,43,67,.88),rgba(11,31,53,.7)); border-color:#294963!important; border-radius:15px; padding:.7rem; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color:#294963!important; border-radius:15px!important; }
.stAlert { border-radius:12px; }
.stButton button[kind="primary"] { background:linear-gradient(90deg,#087e9d,#19a9bb); border:1px solid #48DDF0; color:white; border-radius:10px; font-weight:700; }
.stButton button { border-radius:10px; }
.stRadio [role="radiogroup"] { gap:.25rem; }
.stRadio label { border-radius:8px; }
.stCaption,small { color:#91A8BA!important; }
a { color:#48DDF0!important; }
.mission-art,.comms-art { border:1px solid #294963; border-radius:18px; background:radial-gradient(ellipse at 45% 80%,rgba(19,67,93,.45),rgba(8,24,39,.78) 70%); overflow:hidden; padding:.3rem .8rem 0; margin:.8rem 0 1.2rem; }
.mission-art svg,.comms-art svg { width:100%; height:auto; display:block; }
.svg-label { fill:#A9DFF5; font:500 11px 'DM Mono',monospace; letter-spacing:2px; }
.svg-small { fill:#91A8BA; font:400 9px 'DM Mono',monospace; letter-spacing:1.3px; }
.mission-art-caption { display:flex; justify-content:space-between; color:#91A8BA; font:400 .67rem 'DM Mono',monospace; padding:.2rem .7rem .75rem; }
.vital-card { min-height:152px; padding:1rem 1.05rem; background:linear-gradient(145deg,rgba(18,43,67,.95),rgba(8,27,45,.95)); border:1px solid #294963; border-top:2px solid var(--accent); border-radius:15px; box-shadow:0 12px 26px rgba(0,0,0,.16); margin:.2rem 0 .6rem; }
.vital-top { display:flex; justify-content:space-between; align-items:center; }
.vital-icon { color:var(--accent); font-size:1.25rem; }
.vital-state,.chart-unit { color:#91A8BA; font:400 .62rem 'DM Mono',monospace; letter-spacing:.07em; }
.vital-label { color:#A9DFF5; margin-top:.8rem; font-size:.8rem; }
.vital-value { color:#F3F7FB; font:800 1.8rem Manrope,system-ui,sans-serif; line-height:1.15; }
.vital-value span { color:#91A8BA; font:500 .75rem 'DM Mono',monospace; margin-left:.35rem; }
.vital-context { color:#91A8BA; font-size:.68rem; margin-top:.45rem; }
.status-panel { border:1px solid #2a5366; background:rgba(10,44,57,.58); border-radius:12px; padding:.85rem 1rem; color:#A9DFF5; font:500 .72rem 'DM Mono',monospace; min-height:66px; margin:.2rem 0 .6rem; }
.status-panel small { font:400 .68rem Manrope,system-ui,sans-serif; }
.status-dot { width:8px; height:8px; border-radius:50%; display:inline-block; background:#79D9B3; box-shadow:0 0 10px #79D9B3; margin-right:.5rem; }
.provenance-row { display:flex; justify-content:space-between; padding:.6rem 0; border-bottom:1px solid rgba(145,168,186,.16); color:#A9DFF5; font-size:.82rem; gap:.5rem; }
.provenance-row b { color:#48DDF0; font-family:'DM Mono',monospace; }
.form-provenance { color:#91A8BA; border-top:1px solid #294963; margin-top:.8rem; padding:.75rem 0; font:400 .68rem 'DM Mono',monospace; letter-spacing:.07em; }
.hazard-kicker { display:flex; align-items:center; gap:.7rem; color:#91A8BA; font:500 .66rem 'DM Mono',monospace; letter-spacing:.12em; }
.hazard-icon { color:#48DDF0; font-size:1.3rem; }
.outbox-status { text-align:center; border:1px solid #d59b48; border-radius:9px; color:#FFD58C; background:rgba(91,62,20,.25); padding:.65rem; font:500 .72rem 'DM Mono',monospace; margin-top:.5rem; }
@media (max-width: 760px) { .block-container {padding-left:1rem;padding-right:1rem;} .mission-art-caption {font-size:.55rem;} .vital-card {min-height:130px;} }
</style>
""", unsafe_allow_html=True)

PAGES = ["Mission Health Overview", "Daily Health Check-In", "Personal Baseline & Trends", "Health Insights & Alerts", "Privacy & Communications"]
with st.sidebar:
    st.markdown('<div style="font:800 1.45rem Manrope,sans-serif;color:#F3F7FB;letter-spacing:.1em">CAELI<span style="color:#48DDF0">VIS</span></div><div style="font:500 .61rem DM Mono,monospace;color:#A9DFF5;letter-spacing:.12em;margin:.2rem 0 1rem">CREW HEALTH INTELLIGENCE<br>DEEP SPACE RESEARCH</div>', unsafe_allow_html=True)
    st.caption("NON-DIAGNOSTIC RESEARCH PROTOTYPE")
    page = st.radio("Mission console sections", PAGES, label_visibility="collapsed", key="navigation")
    st.divider()
    st.markdown('<div class="status-panel"><span class="status-dot"></span><b>LOCAL DEMO MODE</b><br><small>No live telemetry · no transmission</small></div>', unsafe_allow_html=True)
    st.metric("Mission elapsed", "Sol 184")
    st.metric("Earth one-way delay", "20:14")
    st.caption("Static illustrative mission values.")

checkins, checkin_warnings = load_checkins_with_warnings()
outbox, outbox_warnings = load_outbox_with_warnings()
for warning in checkin_warnings + outbox_warnings:
    st.warning(f"Local data notice: {warning}")
observations = load_observations(ROOT / "data" / "synthetic_health.csv", checkins)
insights = build_insights(observations)

if page == PAGES[0]:
    render_overview(observations, insights)
elif page == PAGES[1]:
    render_checkin()
elif page == PAGES[2]:
    render_trends(observations)
elif page == PAGES[3]:
    render_hazards(observations, insights)
else:
    render_privacy(observations, outbox, on_queue=lambda: queue_latest_summary(observations), on_deliver=mark_outbox_delivered)
