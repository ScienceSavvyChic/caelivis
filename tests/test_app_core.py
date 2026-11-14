"""Basic behavior tests for synthetic data, comparisons, and local storage."""

import pandas as pd

from caelivis.data import generate_synthetic_data
from caelivis.insights import compare_to_baseline
from caelivis.storage import load_checkins, load_outbox, mark_outbox_delivered, queue_latest_summary, save_checkin


def test_synthetic_data_is_reproducible_and_labeled():
    first = generate_synthetic_data(days=10, seed=7)
    second = generate_synthetic_data(days=10, seed=7)
    pd.testing.assert_frame_equal(first, second)
    assert len(first) == 10
    assert set(first["data_source"]) == {"Synthetic demonstration"}


def test_comparison_uses_configurable_threshold():
    assert compare_to_baseline(115, 100, 15)["notable"]
    assert not compare_to_baseline(110, 100, 15)["notable"]
    assert compare_to_baseline(90, 100, 5)["direction"] == "lower"


def test_local_checkin_and_simulated_outbox_are_persisted(tmp_path, monkeypatch):
    monkeypatch.setenv("CAELIVIS_DATA_DIR", str(tmp_path))
    save_checkin({"date": "2026-01-01", "data_source": "Local check-in"})
    assert len(load_checkins()) == 1
    observations = pd.DataFrame([{
        "heart_rate_bpm": 65,
        "systolic_bp_mmhg": 118,
        "diastolic_bp_mmhg": 75,
        "sleep_hours": 7.0,
        "data_source": "Synthetic demonstration",
    }])
    queued = queue_latest_summary(observations)
    assert queued["status"] == "queued (simulation only)"
    assert len(load_outbox()) == 1
    assert mark_outbox_delivered(queued["id"])
    assert load_outbox()[0]["status"] == "delivered (simulated)"
