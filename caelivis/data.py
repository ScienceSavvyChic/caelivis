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


NASA_CBC_METRICS = {
    "Absolute basophils": ("absolute_basophils_value_cells_per_microliter", "cells/µL"),
    "Absolute eosinophils": ("absolute_eosinophils_value_cells_per_microliter", "cells/µL"),
    "Absolute lymphocytes": ("absolute_lymphocytes_value_cells_per_microliter", "cells/µL"),
    "Absolute monocytes": ("absolute_monocytes_value_cells_per_microliter", "cells/µL"),
    "Absolute neutrophils": ("absolute_neutrophils_value_cells_per_microliter", "cells/µL"),
    "Basophils": ("basophils_value_percent", "%"),
    "Eosinophils": ("eosinophils_value_percent", "%"),
    "Hematocrit": ("hematocrit_value_percent", "%"),
    "Lymphocytes": ("lymphocytes_value_percent", "%"),
    "Mean corpuscular hemoglobin": ("mch_value_picogram", "pg"),
    "Mean corpuscular hemoglobin concentration": ("mchc_value_grams_per_deciliter", "g/dL"),
    "Mean corpuscular volume": ("mcv_value_femtoliter", "fL"),
    "Monocytes": ("monocytes_value_percent", "%"),
    "Mean platelet volume": ("mpv_value_femtoliter", "fL"),
    "Neutrophils": ("neutrophils_value_percent", "%"),
    "Platelet count": ("platelet_count_value_thousand_per_microliter", "thousand/µL"),
    "Red cell distribution width": ("rdw_value_percent", "%"),
    "Red blood cell count": ("red_blood_cell_count_value_million_per_microliter", "million/µL"),
    "White blood cell count": ("white_blood_cell_count_value_thousand_per_microliter", "thousand/µL"),
}

NASA_CBC_TIMEPOINT_ORDER = {
    "L-92": 0,
    "L-44": 1,
    "L-3": 2,
    "R+1": 3,
    "R+45": 4,
    "R+82": 5,
    "R+194": 6,
}


def load_nasa_cbc(path: Path) -> pd.DataFrame:
    """Load and validate the public NASA OSD-569 transformed CBC dataset."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"NASA CBC dataset not found: {path}")

    frame = pd.read_csv(path)
    required = {"Sample Name", *[column for column, _ in NASA_CBC_METRICS.values()]}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"NASA CBC dataset is missing required columns: {sorted(missing)}")

    identifiers = frame["Sample Name"].astype(str).str.extract(
        r"^(C\d+)_whole-blood_(L-\d+|R\+\d+)_cbc$"
    )
    if identifiers.isna().any(axis=None):
        raise ValueError("NASA CBC dataset contains an unrecognized sample identifier.")

    frame = frame.copy()
    frame["participant_id"] = identifiers[0]
    frame["timepoint"] = identifiers[1]
    frame["timepoint_order"] = frame["timepoint"].map(NASA_CBC_TIMEPOINT_ORDER)

    if frame["timepoint_order"].isna().any():
        raise ValueError("NASA CBC dataset contains an undocumented collection timepoint.")

    for column, _unit in NASA_CBC_METRICS.values():
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    return frame.sort_values(
        ["participant_id", "timepoint_order"]
    ).reset_index(drop=True)
