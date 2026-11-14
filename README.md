# CAELIVIS

**Autonomous health intelligence for long-duration space exploration | ScienceSavvyChic Labs**

CAELIVIS is an offline-first, non-diagnostic research prototype for exploring astronaut health observations, personal trends, NASA human-spaceflight hazards, and delayed communications. It is for demonstration and education only—not clinical use, diagnosis, treatment, triage, or a replacement for qualified medical personnel.

> **Safety and provenance:** All records are demonstration data, never actual astronaut telemetry. Bundled records are synthetic; check-in entries are crew-entered demonstration records. Use demonstration values only. Local JSON is not encrypted or access-controlled. No health information is transmitted.

## Interface and features

The interface uses a dark aerospace palette, native Streamlit theme configuration, accessible original SVG mission-route and communications diagrams, responsive metric cards, and interactive Plotly trend charts. No external images or additional Python dependencies are required. The mission route, Earth/Mars symbols, and spacecraft illustrations are conceptual originals—not to scale, mission navigation, NASA imagery, or an endorsement.

- Five Streamlit sections: Mission Health Overview, Daily Health Check-In, Personal Baseline & Trends, Health Insights & Alerts, and Privacy & Communications.
- Clearly identified **Synthetic demonstration data** and **Crew-entered demonstration data** throughout overview and trends.
- Daily check-in with user-selected observation date, unit labels, data-entry bounds, and a blood-pressure consistency check. Bounds are not medical limits.
- Interactive Plotly charts with personal-median comparison and provenance in hover text. Display cues are not validated clinical thresholds.
- Educational discussion of NASA's five human-spaceflight hazards, including data limitations, safe follow-up language, and source links.
- Local JSON storage validation that surfaces warnings, isolates invalid records, and preserves original malformed records rather than silently replacing them.
- Local outbox showing observation timestamp, queue time, fixed 20-minute-14-second one-way delay, calculated simulated arrival, and **Queued — Not Transmitted** state. No actual communication is implemented.

## Installation and launch

Requires Python 3.10+ and pip. From the repository root:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints the local URL (usually `http://localhost:8501`). No API keys, credentials, or external services are needed. After dependencies are installed, the included sample data can be loaded locally.

By default, check-ins and outbox records are stored in `data/local/`. To select another directory, set `CAELIVIS_DATA_DIR` before starting:

```bash
# macOS/Linux
CAELIVIS_DATA_DIR="$HOME/caelivis-local" streamlit run app.py
# Windows PowerShell
$env:CAELIVIS_DATA_DIR = "$HOME\\caelivis-local"; streamlit run app.py
```

## Demo walkthrough

1. Start the app and explore the five pages from the sidebar.
2. On Mission Health Overview, review the conceptual Earth-to-Mars route, mission status, sample trend cards, and provenance counts.
3. In Daily Health Check-In, select a past date and enter illustrative values. Save to persist a crew-entered demonstration record locally.
4. Open Personal Baseline & Trends to inspect interactive chart tooltips and data-source counts. Differences are descriptive, not clinical alerts.
5. Review the hazard cards and NASA references on Health Insights & Alerts.
6. In Privacy & Communications, queue a local summary and inspect observation time, queue time, 20:14 delay, expected arrival, and not-transmitted status. No message is sent.

## Testing

```bash
python -m pytest -q
```

Tests cover synthetic-data labeling, comparison behavior, historical observation dates, malformed and invalid local records, non-destructive storage, chart construction for valid/empty data, delay arithmetic, outbox persistence, and (where supported by Streamlit) AppTest navigation and form flow.

## Synthetic data, references, and safety boundaries

`data/synthetic_health.csv` contains invented sample data for interface demonstration. It is not from astronauts, a human-subjects study, or a clinical source. Hazard content is educational and references:

- NASA Human Research Program: https://www.nasa.gov/hrp/
- NASA Human Research Roadmap: https://humanresearchroadmap.nasa.gov/

There is no radiation dosimeter, cabin-environment telemetry, validated behavioral-health instrument, authentication, encryption, or clinician workflow. Check-ins are simple self-reports. Comparison thresholds are user-configurable display choices, not medical rules. Mission elapsed time and the 20:14 delay are static simulation values, not live mission calculations. For medical concerns, follow mission protocols and qualified medical oversight.

## Project layout

```text
app.py                       Streamlit entry point, navigation, global styling
.streamlit/config.toml       Native Streamlit theme configuration
caelivis/data.py             Synthetic and local observation handling
caelivis/insights.py         Descriptive personal-baseline comparisons
caelivis/storage.py          Validated local JSON and simulated outbox
caelivis/views.py            Five-section UI, original inline SVG, Plotly charts
data/synthetic_health.csv   Clearly labeled synthetic demonstration records
tests/test_app_core.py       Core, storage, chart, and optional AppTest coverage
requirements.txt             Runtime and test dependencies
```
