"""Data loading and deterministic synthetic sample generation."""

from pathlib import Path

import numpy as np
import pandas as pd

from caelivis.storage import CREW_SOURCE, SYNTHETIC_SOURCE, validate_checkin

DATA_COLUMNS = [
    "date", "heart_rate_bpm", "systolic_bp_mmhg", "diastolic_bp_mmhg",
    "temperature_c", "glucose_mg_dl", "sleep_hours", "sleep_quality_1_5",
    "exercise_minutes", "mood_1_5", "stress_1_5", "cognitive_wellbeing_1_5",
    "fatigue_1_5", "data_source",
]


def generate_synthetic_data(days: int = 30, seed: int = 42) -> pd.DataFrame:
    """Return reproducible, illustrative data—not astronaut measurements."""
    if days < 2:
        raise ValueError("days must be at least 2")
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days, freq="D")
    drift = np.linspace(0, 1, days)
    return pd.DataFrame({
        "date": dates,
        "heart_rate_bpm": np.round(64 + drift * 1.8 + rng.normal(0, 3, days)).astype(int),
        "systolic_bp_mmhg": np.round(116 + drift + rng.normal(0, 4, days)).astype(int),
        "diastolic_bp_mmhg": np.round(75 + rng.normal(0, 3, days)).astype(int),
        "temperature_c": np.round(36.7 + rng.normal(0, .15, days), 1),
        "glucose_mg_dl": np.round(91 + rng.normal(0, 7, days)).astype(int),
        "sleep_hours": np.round(7.4 + rng.normal(0, .65, days), 1).clip(3, 12),
        "sleep_quality_1_5": rng.integers(2, 6, days),
        "exercise_minutes": rng.integers(25, 91, days),
        "mood_1_5": rng.integers(2, 6, days),
        "stress_1_5": rng.integers(1, 5, days),
        "cognitive_wellbeing_1_5": rng.integers(2, 6, days),
        "fatigue_1_5": rng.integers(1, 5, days),
        "data_source": SYNTHETIC_SOURCE,
    })[DATA_COLUMNS]


def load_observations(sample_path: Path, checkins: list[dict]) -> pd.DataFrame:
    """Load sample and only individually valid local observations."""
    if sample_path.exists():
        frame = pd.read_csv(sample_path, parse_dates=["date"])
        frame["data_source"] = frame["data_source"].replace({"Synthetic demonstration": SYNTHETIC_SOURCE})
    else:
        frame = generate_synthetic_data()
    valid_local = []
    for record in checkins:
        cleaned, issue = validate_checkin(record)
        if issue is None:
            cleaned["data_source"] = CREW_SOURCE
            valid_local.append(cleaned)
    if valid_local:
        local = pd.DataFrame(valid_local)
        local["date"] = pd.to_datetime(local["date"], errors="coerce")
        frame = pd.concat([frame, local], ignore_index=True, sort=False)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    return frame.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
