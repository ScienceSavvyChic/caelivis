"""Non-diagnostic, descriptive comparisons for the research prototype."""

import pandas as pd


METRICS = {
    "Heart rate": ("heart_rate_bpm", "bpm"),
    "Systolic blood pressure": ("systolic_bp_mmhg", "mmHg"),
    "Diastolic blood pressure": ("diastolic_bp_mmhg", "mmHg"),
    "Body temperature": ("temperature_c", "°C"),
    "Sleep duration": ("sleep_hours", "hours"),
    "Exercise": ("exercise_minutes", "min"),
    "Mood": ("mood_1_5", "/ 5"),
    "Stress": ("stress_1_5", "/ 5"),
    "Cognitive well-being": ("cognitive_wellbeing_1_5", "/ 5"),
    "Fatigue": ("fatigue_1_5", "/ 5"),
}


def compare_to_baseline(value: float, baseline: float, threshold_pct: float = 15) -> dict:
    """Describe a configurable relative change; this is not a clinical limit."""
    if baseline == 0:
        return {"change_pct": None, "notable": False, "direction": "unavailable"}
    change = (value - baseline) / abs(baseline) * 100
    return {
        "change_pct": change,
        "notable": abs(change) >= threshold_pct,
        "direction": "higher" if change > 0 else "lower" if change < 0 else "unchanged",
    }


def build_insights(observations: pd.DataFrame, baseline_days: int = 7, threshold_pct: float = 15) -> list[dict]:
    """Return signals relative to a personal recent median, with cautious language."""
    if observations.empty or len(observations) < 2:
        return []
    history = observations.iloc[:-1].tail(baseline_days)
    latest = observations.iloc[-1]
    results = []
    for label, (column, unit) in METRICS.items():
        if column not in observations or pd.isna(latest.get(column)):
            continue
        baseline = pd.to_numeric(history[column], errors="coerce").median()
        if pd.isna(baseline):
            continue
        comparison = compare_to_baseline(float(latest[column]), float(baseline), threshold_pct)
        if comparison["notable"]:
            results.append({
                "metric": label,
                "value": float(latest[column]),
                "baseline": float(baseline),
                "unit": unit,
                **comparison,
                "source": latest.get("data_source", "Unknown"),
            })
    return results
