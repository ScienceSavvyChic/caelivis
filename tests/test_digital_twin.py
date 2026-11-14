"""Tests for the offline astronaut digital-twin data mapping."""

import pandas as pd

from caelivis.digital_twin import REGION_FIELDS, summarize_region, testable_region_names


def test_digital_twin_regions_map_existing_fields_without_invented_signals():
    assert testable_region_names() == ("Head", "Chest", "Body")
    fields = {field for definitions in REGION_FIELDS.values() for _, field, _ in definitions}
    assert fields == {
        "cognitive_wellbeing_1_5", "mood_1_5", "stress_1_5", "sleep_hours", "fatigue_1_5",
        "heart_rate_bpm", "systolic_bp_mmhg", "diastolic_bp_mmhg", "temperature_c",
        "exercise_minutes", "glucose_mg_dl",
    }
    assert not any("ecg" in field.lower() for field in fields)


def test_digital_twin_summary_uses_latest_provenance_and_prior_median():
    data = pd.DataFrame([
        {"date": "2026-01-01", "heart_rate_bpm": 60, "data_source": "Synthetic demonstration data"},
        {"date": "2026-01-02", "heart_rate_bpm": 70, "data_source": "Crew-entered demonstration data", "observation_timestamp": "2026-01-02T12:00:00+00:00"},
        {"date": "2026-01-03", "heart_rate_bpm": 80, "data_source": "Crew-entered demonstration data", "observation_timestamp": "2026-01-03T12:00:00+00:00"},
    ])
    result = summarize_region(data, "Chest")
    heart_rate = next(item for item in result if item["field"] == "heart_rate_bpm")
    assert heart_rate["value"] == 80
    assert heart_rate["baseline"] == 65
    assert heart_rate["unit"] == "beats/min"
    assert heart_rate["source"] == "Crew-entered demonstration data"
    assert heart_rate["observed_at"] == "2026-01-03T12:00:00+00:00"


def test_digital_twin_omits_missing_region_fields_and_handles_empty_data():
    frame = pd.DataFrame([{"date": "2026-01-01", "heart_rate_bpm": 64, "data_source": "Synthetic demonstration data"}])
    chest = summarize_region(frame, "Chest")
    assert [item["field"] for item in chest] == ["heart_rate_bpm"]
    assert summarize_region(pd.DataFrame(), "Head") == []
    assert summarize_region(frame, "Unknown") == []
