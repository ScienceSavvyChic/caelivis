# CAELIVIS

**Autonomous health intelligence for long-duration space exploration | ScienceSavvyChic Labs**

CAELIVIS is an offline-first, non-diagnostic research prototype for exploring astronaut health observations, personal trends, NASA human-spaceflight hazards, and delayed communications. It is for demonstration and education only—not clinical use, diagnosis, treatment, triage, or a replacement for qualified medical personnel.

> **Safety and provenance:** All records are demonstration data, never actual astronaut telemetry. Bundled records are synthetic; check-in entries are crew-entered demonstration records. Use demonstration values only. Local JSON is not encrypted or access-controlled. No health information is transmitted.

## Interactive astronaut digital twin

Mission Health Overview features an original inline-SVG spacesuit silhouette with keyboard-accessible Head / Chest / Body selection. Choosing a region highlights it and updates the adjacent panel with available recorded observations, units, timestamps, data provenance, and a preceding-record median where available. Region groups map only to existing CAELIVIS fields: wellbeing, mood, stress, sleep, fatigue, heart rate, blood pressure, temperature, exercise, and optional glucose. This is a conceptual data explorer—not an anatomical scan, connected sensor model, or actual astronaut digital twin.

An expandable signal/HUD panel displays a real stored heart-rate observation if available. The ECG-style trace is illustrative only because no ECG is collected; the HUD is a design preview, not hardware integration. The digital twin graphics and controls are local and do not depend on remote images, cloud rendering, or external services. Existing interface CSS may request a decorative font externally; a local system-font fallback remains available offline.

## Existing functionality

- Five Streamlit sections: Mission Health Overview, Daily Health Check-In, Personal Baseline & Trends, Health Insights & Alerts, and Privacy & Communications.
- Clearly identified **Synthetic demonstration data** and **Crew-entered demonstration data**.
- Check-in with user-selected observation date, units, entry guardrails, and blood-pressure consistency check. Guardrails are not medical limits.
- Interactive Plotly trend charts and configurable personal-median comparisons. These are descriptive display cues, not validated clinical thresholds.
- Educational discussion of NASA's five human-spaceflight hazards with limitations, appropriate follow-up, and source links.
- Local JSON storage validation with visible warnings and non-destructive handling of malformed records.
- Local outbox with observation/queue times, fixed 20-minute-14-second one-way delay and calculated simulated arrival. Queue status is **Queued — Not Transmitted**; there is no real communications path.

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

Streamlit prints the local URL (usually `http://localhost:8501`). No API keys, credentials, or cloud services are required. The core interface and digital twin are available without network access after dependencies are installed.

Check-ins and outbox records default to `data/local/`. To select another folder, set `CAELIVIS_DATA_DIR` before starting:

```bash
# macOS/Linux
CAELIVIS_DATA_DIR="$HOME/caelivis-local" streamlit run app.py
# Windows PowerShell
$env:CAELIVIS_DATA_DIR = "$HOME\\caelivis-local"; streamlit run app.py
```

## Demo walkthrough

1. Start the app and explore the five sidebar sections.
2. In Mission Health Overview, select Head, Chest, or Body beside the suit illustration; inspect the observed value, unit, date/source and preceding-record median. Expand Signals & astronaut HUD concept to inspect heart-rate context and the clearly illustrative ECG-style graphic.
3. In Daily Health Check-In, choose a historical date, enter demo values, and save locally.
4. Explore interactive trends and provenance in Personal Baseline & Trends. Review educational hazard content and source links in Health Insights & Alerts.
5. In Privacy & Communications, queue a local summary and inspect the simulated 20:14 arrival. No message is sent.

## Testing

```bash
python -m pytest -q
```

Core tests cover synthetic labels, comparison behavior, historical dates, malformed local records, outbox timing, trend figures, navigation, check-in flow, and digital-twin region mapping/source/baseline summaries. Automated tests do not replace browser-level responsive and accessibility review.

## Data, sources, and scientific limitations

`data/synthetic_health.csv` contains invented examples. It is not astronaut telemetry, a human-subjects dataset, or clinical source data. Hazard descriptions reference NASA resources:

- NASA Human Research Program: https://www.nasa.gov/hrp/
- NASA Human Research Roadmap: https://humanresearchroadmap.nasa.gov/

There is no radiation dosimeter, ECG signal, cabin-environment telemetry, validated behavioral-health instrument, authentication, encryption, or clinician workflow. Check-ins are simple self-reports. Comparisons are not medical thresholds; the app does not diagnose, triage, prescribe, or recommend treatment. Mission elapsed time and communications delay are static simulation values. For health concerns, follow mission protocols and qualified medical oversight.

## Project layout

```text
app.py                       Streamlit entry point and five-section navigation
caelivis/data.py             Synthetic and local observation loading
caelivis/digital_twin.py     Inline-SVG astronaut and interactive region explorer
caelivis/insights.py         Descriptive personal-baseline comparisons
caelivis/storage.py          Validated local JSON and simulated outbox
caelivis/views.py            Five-section views, hazard and trend displays
data/synthetic_health.csv   Clearly labeled synthetic demo data
tests/test_app_core.py       Existing core and AppTest coverage
tests/test_digital_twin.py   Digital-twin mapping/provenance coverage
requirements.txt             Existing runtime/test dependencies
```
