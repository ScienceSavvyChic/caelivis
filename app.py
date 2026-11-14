"""CAELIVIS: offline-first health trend demonstration for spaceflight."""

from pathlib import Path

import streamlit as st

from caelivis.data import load_observations
from caelivis.insights import build_insights
from caelivis.storage import (
    load_checkins_with_warnings,
    load_outbox_with_warnings,
    mark_outbox_delivered,
    queue_latest_summary,
)
from caelivis.views import render_checkin, render_hazards, render_overview, render_privacy, render_trends

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="CAELIVIS | Mission Health", page_icon="🛰️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: radial-gradient(ellipse at 20% 0%, #102c48 0%, #071321 47%, #050c16 100%); }
[data-testid="stSidebar"] { background: #091827; border-right: 1px solid #173b56; }
h1, h2, h3 { color: #e8f5ff; letter-spacing: .01em; }
.eyebrow { color: #4bd7e8; text-transform: uppercase; letter-spacing: .16em; font-size: .75rem; font-weight: 700; }
.subtle { color: #a9bfd1; }
[data-testid="stMetric"] { background: rgba(15, 39, 59, .82); border: 1px solid #1c4966; padding: 1rem; border-radius: 12px; }
[data-testid="stMetricLabel"] { color: #b7cfdf; }
div[data-testid="stForm"] { background: rgba(12, 31, 48, .72); padding: 1.2rem; border: 1px solid #1c4966; border-radius: 14px; }
.stAlert { border-radius: 10px; }
a { color: #58d5ec !important; }
</style>
""", unsafe_allow_html=True)

PAGES = ["Mission Health Overview", "Daily Health Check-In", "Personal Baseline & Trends", "Health Insights & Alerts", "Privacy & Communications"]
with st.sidebar:
    st.markdown('<p class="eyebrow">CAELIVIS · CREW HEALTH</p>', unsafe_allow_html=True)
    st.title("Mission Console")
    st.caption("Offline-first research prototype · demonstration data only")
    page = st.radio("Navigate", PAGES, label_visibility="collapsed", key="navigation")
    st.divider()
    st.metric("Mission elapsed", "Sol 184")
    st.metric("Earth one-way light-time", "20 min 14 sec")
    st.caption("Static communication simulation; no network transmission is enabled.")

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
