# CAELIVIS

**Autonomous health intelligence for long-duration space exploration | ScienceSavvyChic Labs**

CAELIVIS is an offline-first, non-diagnostic research prototype for exploring astronaut health observations, personal trends, NASA human-spaceflight hazards, and delayed communications. It is for demonstration and education only—not clinical use, diagnosis, treatment, triage, or a replacement for qualified medical personnel.

> **Safety and provenance:** All records are demonstration data, never actual astronaut telemetry. Bundled records are synthetic; check-in entries are crew-entered demonstration records. Use demonstration values only. Local JSON is not encrypted or access-controlled. No health information is transmitted.

## Interactive astronaut digital twin

The Mission Health Overview now includes an original, locally rendered SVG spacesuit silhouette and a keyboard-accessible Head / Chest / Body selector. Selecting a region highlights that area and displays the newest available observations, units, recorded date/timestamp, provenance, and a recent-record median where available. Available fields are the existing CAELIVIS schema only: cognitive wellbeing, mood, stress, sleep and fatigue; heart rate and blood pressure; temperature, exercise, and optional glucose. This is a conceptual data explorer, not a scan, physiological model, connected sensor, or real astronaut digital twin.

The expandable Signals & HUD panel displays actual stored heart-rate observations when present. Its ECG-style trace is illustrative only because no ECG signal is collected. The suit HUD preview is a static design concept, not hardware integration. All core artwork is inline SVG/CSS; it does not fetch remote images or require a rendering service. (A previously existing remote font import in the app styling is decorative only; system font fallbacks remain available offline.)

## Existing functionality

- Five Streamlit sections: Mission Health Overview, Daily Health Check-In, Personal Baseline & Trends, Health Insights & Alerts, and Privacy & Communications.
- Clearly identified **Synthetic demonstration data** and **Crew-entered demonstration data**.
- Daily check-in with selected observation date, units, entry guardrails, and blood-pressure consistency check. Guardrails are not medical limits.
- Interactive Plotly trend charts and configurable personal-median comparisons. These are descriptive, not validated clinical thresholds.
- Educational discussion of NASA's five human-spaceflight hazards with limitations, appropriate follow-up, and source links.
- Local JSON storage validation with visible warnings and non-destructive handling of malformed records.
- Local outbox with observation/queue times, fixed 20-minute-14-second one-way delay and calculated simulated arrival. Queue status remains **Queued — Not Transmitted**; there is no real communications path.

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

Streamlit prints the local URL (usually `http://localhost:8501`). No API keys, credentials, or cloud services are required. The digital twin graphics and controls run locally.

By default, check-ins and outbox records are stored in `data/local/`. To select another directory, set `CAELIVIS_DATA_DIR` before starting:

```bash
# macOS/Linux
CAELIVIS_DATA_DIR="$HOME/caelivis-local" streamlit run app.py
# Windows PowerShell
$env:CAELIVIS_DATA_DIR = "$HOME\\caelivis-local"; streamlit run app.py
```

## Demo walkthrough

1. Start the app and explore five sections from the sidebar.
2. In Mission Health Overview, select Head, Chest, or Body beside the suit illustration. Review recorded values, source/date, and personal median. Expand Signals & HUD to inspect the recorded heart-rate context and explicitly illustrative ECG-style graphic.
3. In Daily Health Check-In, choose a historical date, add demonstration observations, and save locally.
4. Explore interactive trends and provenance in Personal Baseline & Trends; inspect the hazard cards and NASA references in Health Insights & Alerts.
5. Queue a local summary in Privacy & Communications and inspect the simulated 20:14 arrival details. No message is sent.

## Testing

```bash
python -m pytest -q
```

Tests cover synthetic labeling, baseline logic, date persistence, malformed local data, outbox timing, trend figures, navigation, and check-in flow. The UI test suite does not replace browser/manual layout and accessibility testing.

## Data, sources, and scientific limitations

`data/synthetic_health.csv` contains invented examples. It is not astronaut telemetry, a human-subjects dataset, or clinical source data. Hazard descriptions reference NASA resources:

- NASA Human Research Program: https://www.nasa.gov/hrp/
- NASA Human Research Roadmap: https://humanresearchroadmap.nasa.gov/

There is no radiation dosimeter, ECG, cabin-environment telemetry, validated behavioral-health instrument, authentication, encryption, or clinician workflow. Check-ins are simple self-reports. Comparisons are descriptive and not medical thresholds; the app does not diagnose, triage, prescribe or recommend treatment. Mission elapsed time and communications delay are static simulation values. For health concerns, follow mission protocols and qualified medical oversight.

## Project layout

```text
app.py                       Streamlit entry point and five-section navigation
caelivis/data.py             Synthetic and local observation loading
caelivis/digital_twin.py     Offline SVG astronaut and regional observation explorer
caelivis/insights.py         Descriptive personal-baseline comparisons
caelivis/storage.py          Validated local JSON and simulated outbox
caelivis/views.py            Five-section views, hazard and trend displays
data/synthetic_health.csv   Clearly labeled synthetic demo data
tests/test_app_core.py       Core and AppTest coverage
requirements.txt             Existing runtime/test dependencies
```
