"""CAELIVIS: offline-first health trend demonstration for spaceflight."""

from pathlib import Path

import streamlit as st

from caelivis.data import load_observations
from caelivis.digital_twin import render_digital_twin
from caelivis.insights import build_insights
from caelivis.storage import load_checkins, load_outbox, queue_latest_summary, mark_outbox_delivered
from caelivis.views import render_checkin, render_hazards, render_overview, render_privacy, render_trends, render_nasa_research_explorer

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="CAELIVIS | Crew Health Intelligence", page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: radial-gradient(ellipse at 60% -20%, #12334d 0%, #091b2d 40%, #071525 85%); color: #F3F7FB; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#0B1F35,#071525); border-right: 1px solid #24415a; }
.block-container { max-width: 1500px; padding-top: 1.5rem; padding-bottom: 3rem; }
h1,h2,h3 { color:#F3F7FB; letter-spacing:-.025em; font-family:system-ui,sans-serif; }
h1 { font-size:clamp(2rem,4vw,3rem)!important; font-weight:800!important; }
.eyebrow,.section-label { color:#48DDF0; text-transform:uppercase; letter-spacing:.15em; font:500 .72rem ui-monospace,monospace; margin:1.1rem 0 .45rem; }
.page-description { color:#A9DFF5; max-width:850px; margin:.1rem 0 1.3rem; font-size:1rem; }
[data-testid="stMetric"] { background:linear-gradient(145deg,rgba(18,43,67,.94),rgba(11,31,53,.86)); border:1px solid #294963; padding:1rem 1.1rem; border-radius:14px; }
[data-testid="stMetricLabel"] { color:#91A8BA; }
div[data-testid="stForm"] { background:rgba(11,31,53,.56); padding:1.25rem; border:1px solid #294963; border-radius:18px; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color:#294963!important; border-radius:15px!important; }
.stAlert { border-radius:12px; } .stButton button { border-radius:10px; }
a { color:#48DDF0!important; }
.mission-art,.comms-art { border:1px solid #294963; border-radius:18px; background:radial-gradient(ellipse at 45% 80%,rgba(19,67,93,.45),rgba(8,24,39,.78) 70%); overflow:hidden; padding:.3rem .8rem 0; margin:.8rem 0 1.2rem; }
.mission-art svg,.comms-art svg { width:100%; height:auto; display:block; }
.svg-label { fill:#A9DFF5; font:500 11px ui-monospace,monospace; letter-spacing:2px; }
.svg-small { fill:#91A8BA; font:400 9px ui-monospace,monospace; letter-spacing:1.3px; }
.mission-art-caption { display:flex; justify-content:space-between; color:#91A8BA; font-size:.67rem; padding:.2rem .7rem .75rem; }
.vital-card { min-height:152px; padding:1rem; background:linear-gradient(145deg,rgba(18,43,67,.95),rgba(8,27,45,.95)); border:1px solid #294963; border-top:2px solid var(--accent); border-radius:15px; margin:.2rem 0 .6rem; }
.vital-top { display:flex; justify-content:space-between; }.vital-icon { color:var(--accent); font-size:1.25rem; }.vital-state,.chart-unit { color:#91A8BA; font-size:.62rem; letter-spacing:.07em; }
.vital-label { color:#A9DFF5; margin-top:.8rem; font-size:.8rem; }.vital-value { color:#F3F7FB; font-weight:800; font-size:1.8rem; }.vital-value span { color:#91A8BA; font-size:.75rem; margin-left:.35rem; }.vital-context { color:#91A8BA; font-size:.68rem; margin-top:.45rem; }
.status-panel,.twin-status { border:1px solid #2a5366; background:rgba(10,44,57,.58); border-radius:12px; padding:.85rem 1rem; color:#A9DFF5; font-size:.72rem; margin:.2rem 0 .6rem; }
.status-dot,.twin-dot { width:8px; height:8px; border-radius:50%; display:inline-block; background:#79D9B3; margin-right:.5rem; }.status-panel small,.twin-status small { color:#91A8BA; }
.provenance-row { display:flex; justify-content:space-between; padding:.6rem 0; border-bottom:1px solid rgba(145,168,186,.16); color:#A9DFF5; font-size:.82rem; }.provenance-row b { color:#48DDF0; }
.form-provenance { color:#91A8BA; border-top:1px solid #294963; margin-top:.8rem; padding:.75rem 0; font-size:.68rem; }
.hazard-kicker { display:flex; align-items:center; gap:.7rem; color:#91A8BA; font-size:.66rem; letter-spacing:.12em; }.hazard-icon { color:#48DDF0; font-size:1.3rem; }
.outbox-status { text-align:center; border:1px solid #d59b48; border-radius:9px; color:#FFD58C; background:rgba(91,62,20,.25); padding:.65rem; font-size:.72rem; margin-top:.5rem; }
.twin-shell { border:1px solid #2c536b; border-radius:18px; padding:.4rem .5rem .7rem; background:radial-gradient(ellipse at 50% 40%,rgba(30,99,131,.32),rgba(7,21,37,.9) 72%); box-shadow:inset 0 0 35px rgba(72,221,240,.05),0 15px 40px rgba(0,0,0,.25); }
.astronaut-twin { width:100%; height:auto; max-height:610px; display:block; }.twin-svg-label { fill:#91A8BA; font:9px system-ui,sans-serif; letter-spacing:1.2px; }.twin-source-note { text-align:center; color:#91A8BA; font-size:.62rem; letter-spacing:.08em; }
.twin-region { opacity:.15; transition:opacity .2s ease; }.twin-region.active { opacity:.95; filter:drop-shadow(0 0 7px #48DDF0); }
.twin-reading { color:#F3F7FB; font-weight:800; font-size:1.45rem; }.twin-reading span { font-size:.78rem; color:#A9DFF5; }
.hud-panel { display:flex; flex-direction:column; gap:.8rem; padding:1rem; border:1px solid #48DDF0; border-radius:14px; background:linear-gradient(145deg,rgba(14,48,70,.85),rgba(7,21,37,.95)); color:#A9DFF5; font-size:.67rem; }.hud-panel b { color:#48DDF0; }.hud-panel div { display:flex; justify-content:space-between; gap:.5rem; border-bottom:1px solid rgba(145,168,186,.2); padding-bottom:.45rem; }.hud-panel strong { color:#F3F7FB; }
@media (max-width:760px) { .block-container {padding-left:1rem;padding-right:1rem;} .mission-art-caption {font-size:.55rem;} .vital-card {min-height:130px;} }
@media (prefers-reduced-motion: reduce) { *,*::before,*::after { scroll-behavior:auto!important; transition:none!important; animation:none!important; } }
</style>
""", unsafe_allow_html=True)

PAGES = ["Mission Health Overview", "Daily Health Check-In", "Personal Baseline & Trends", "Health Insights & Alerts", "NASA Research Data Explorer", "Privacy & Communications"]
with st.sidebar:
    st.markdown('<div style="font:800 1.45rem system-ui,sans-serif;color:#F3F7FB;letter-spacing:.1em">CAELI<span style="color:#48DDF0">VIS</span></div><div style="font:500 .61rem ui-monospace,monospace;color:#A9DFF5;letter-spacing:.12em;margin:.2rem 0 1rem">CREW HEALTH INTELLIGENCE<br>DEEP SPACE RESEARCH</div>', unsafe_allow_html=True)
    st.caption("NON-DIAGNOSTIC RESEARCH PROTOTYPE")
    page = st.radio("Mission console sections", PAGES, label_visibility="collapsed", key="navigation")
    st.divider()
    st.markdown('<div class="status-panel"><span class="status-dot"></span><b>LOCAL DEMO MODE</b><br><small>No live telemetry · no transmission</small></div>', unsafe_allow_html=True)
    st.metric("Mission elapsed", "Sol 184")
    st.metric("Earth one-way delay", "20:14")
    st.caption("Static illustrative mission values.")

checkins = load_checkins()
observations = load_observations(ROOT / "data" / "synthetic_health.csv", checkins)
insights = build_insights(observations)
if page == PAGES[0]:
    render_digital_twin(observations)
    render_overview(observations, insights)
elif page == PAGES[1]:
    render_checkin()
elif page == PAGES[2]:
    render_trends(observations)
elif page == PAGES[3]:
    render_hazards(observations, insights)
elif page == PAGES[4]:
    render_nasa_research_explorer(ROOT / "data" / "nasa" / "LSDS-7_Complete_Blood_Count_CBC_TRANSFORMED.csv")
else:
    render_privacy(observations, load_outbox(), on_queue=lambda: queue_latest_summary(observations), on_deliver=mark_outbox_delivered)
