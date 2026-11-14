# CAELIVIS

**Autonomous health intelligence for long-duration space exploration | ScienceSavvyChic Labs**

CAELIVIS is an offline-first, non-diagnostic research prototype for exploring astronaut health self-reports, personal trends, NASA human-spaceflight hazards, and delayed communications. It is intended for demonstration and education only—not clinical use, diagnosis, treatment, triage, or as a replacement for qualified medical personnel.

> **Safety and data notice:** The checked-in sample is synthetic. Use demonstration values only; do not enter real personal or astronaut health information. Local JSON files are not encrypted or access-controlled. No health data is transmitted by this application.

## Features in this milestone

- Five-section Streamlit navigation: Mission Health Overview, Daily Health Check-In, Personal Baseline & Trends, Health Insights & Alerts, and Privacy & Communications.
- Clearly labeled synthetic sample observations plus locally stored check-ins.
- Input bounds, clear units, and a blood-pressure consistency check on the check-in form.
- Interactive Plotly trend chart and configurable recent-median comparison. Display cues are not clinical thresholds.
- Educational descriptions of NASA's five human-spaceflight hazards, with explicit limitations and source links.
- Local simulated message outbox with a fixed 20-minute, 14-second one-way delay demonstration. There is no network-send implementation.

## Requirements

- Python 3.10 or newer
- pip

## Setup and launch

From the repository root:

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints a local URL (usually `http://localhost:8501`). No API keys, credentials, or external services are required. The sample data is included, so the app can be explored without network access after dependencies are installed.

To use a different local folder for check-ins and the simulated outbox, set `CAELIVIS_DATA_DIR` before starting Streamlit:

```bash
# macOS / Linux
CAELIVIS_DATA_DIR="$HOME/caelivis-local" streamlit run app.py
# Windows PowerShell
$env:CAELIVIS_DATA_DIR = "$HOME\\caelivis-local"; streamlit run app.py
```

By default, local records are written to `data/local/`. That directory is ignored by git. Keep it private and do not use it for actual health information.

## Tests

```bash
python -m pytest -q
```

Tests cover deterministic labeling of synthetic data, configurable descriptive comparison logic, and local check-in/outbox persistence. They do not replace manual UI verification or clinical validation.

## Data sources and scientific boundaries

The sample CSV is generated demonstration content and is not an astronaut dataset. Hazard descriptions are educational summaries based on NASA program resources:

- NASA Human Research Program: https://www.nasa.gov/hrp/
- NASA Human Research Roadmap: https://humanresearchroadmap.nasa.gov/

The app has no radiation dosimeter, cabin-environment telemetry, validated behavioral-health instruments, authenticated user accounts, encryption, or clinician workflow. Its relative comparisons are configurable display aids, not medical alerts. For concerns, use mission procedures and qualified medical oversight. The displayed mission day and 20:14 communication delay are static simulation values, not live mission calculations.

## Project layout

```text
app.py                       Streamlit entry point and navigation
caelivis/data.py             Synthetic data generation and observation loading
caelivis/insights.py         Descriptive personal-baseline comparisons
caelivis/storage.py          Local JSON storage and simulated outbox
caelivis/views.py            Five-section Streamlit UI
 data/synthetic_health.csv   Clearly labeled demonstration observations
tests/test_app_core.py       Basic core behavior tests
requirements.txt             Runtime and test dependencies
```
