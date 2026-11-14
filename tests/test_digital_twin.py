"""Unit tests for local astronaut digital-twin data mapping."""

import pandas as pd

from caelivis.digital_twin import REGION_FIELDS, region_names, summarize_region


def test_regions_use_only_existing_observation_fields_and_no_ecg_measurement():
    assert region_names() == ("Head", "Chest", "Body")
    fields = {field for definitions in REGION_FIELDS.values() for _, field, _ in definitions}
    assert fields == {
        "cognitive_wellbeing_1_5", "mood_1_5", "stress_1_5", "sleep_hours", "fatigue_1_5",
        "heart_rate_bpm", "systolic_bp_mmhg", "diastolic_bp_mmhg", "temperature_c",
        "exercise_minutes", "glucose_mg_dl",
    }
    assert not any("ecg" in field.lower() for field in fields)


def test_region_summary_reports_latest_source_timestamp_and_prior_median():
    frame = pd.DataFrame([
        {"date": "2026-01-01", "heart_rate_bpm": 60, "data_source": "Synthetic demonstration data"},
        {"date": "2026-01-02", "heart_rate_bpm": 70, "data_source": "Crew-entered demonstration data", "observation_timestamp": "2026-01-02T12:00:00+00:00"},
        {"date": "2026-01-03", "heart_rate_bpm": 80, "data_source": "Crew-entered demonstration data", "observation_timestamp": "2026-01-03T12:00:00+00:00"},
    ])
    item = next(x for x in summarize_region(frame, "Chest") if x["field"] == "heart_rate_bpm")
    assert item["value"] == 80
    assert item["baseline"] == 65
    assert item["unit"] == "beats/min"
    assert item["source"] == "Crew-entered demonstration data"
    assert item["observed_at"] == "2026-01-03T12:00:00+00:00"


def test_region_summary_omits_missing_fields_and_handles_empty_or_unknown_region():
    frame = pd.DataFrame([{"date": "2026-01-01", "heart_rate_bpm": 64, "data_source": "Synthetic demonstration data"}])
    assert [x["field"] for x in summarize_region(frame, "Chest")] == ["heart_rate_bpm"]
    assert summarize_region(pd.DataFrame(), "Head") == []
    assert summarize_region(frame, "Unknown") == []
