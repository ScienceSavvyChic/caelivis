"""Basic behavior and regression tests for CAELIVIS core behavior."""

import json
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from caelivis.data import generate_synthetic_data, load_observations
from caelivis.insights import compare_to_baseline
from caelivis.storage import (
    CREW_SOURCE, ONE_WAY_DELAY, StorageError, load_checkins, load_checkins_with_warnings,
    load_outbox, load_outbox_with_warnings, mark_outbox_delivered, queue_latest_summary,
    save_checkin,
)
from caelivis.views import build_trend_figure


def valid_record(**updates):
    record = {
        "date": "2026-01-02", "heart_rate_bpm": 68, "systolic_bp_mmhg": 118,
        "diastolic_bp_mmhg": 76, "temperature_c": 36.7, "glucose_mg_dl": None,
        "sleep_hours": 7.5, "sleep_quality_1_5": 3, "exercise_minutes": 45,
        "mood_1_5": 3, "stress_1_5": 3, "cognitive_wellbeing_1_5": 3,
        "fatigue_1_5": 3, "data_source": CREW_SOURCE,
    }
    record.update(updates)
    return record


def test_synthetic_data_is_reproducible_and_labeled():
    first = generate_synthetic_data(days=10, seed=7)
    second = generate_synthetic_data(days=10, seed=7)
    pd.testing.assert_frame_equal(first, second)
    assert len(first) == 10
    assert set(first["data_source"]) == {"Synthetic demonstration data"}


def test_comparison_uses_configurable_threshold():
    assert compare_to_baseline(115, 100, 15)["notable"]
    assert not compare_to_baseline(110, 100, 15)["notable"]
    assert compare_to_baseline(90, 100, 5)["direction"] == "lower"


def test_local_checkin_and_simulated_outbox_are_persisted(tmp_path, monkeypatch):
    monkeypatch.setenv("CAELIVIS_DATA_DIR", str(tmp_path))
    save_checkin(valid_record())
    assert len(load_checkins()) == 1
    observations = pd.DataFrame([{
        "date": pd.Timestamp("2026-01-02"), "heart_rate_bpm": 65,
        "systolic_bp_mmhg": 118, "diastolic_bp_mmhg": 75, "sleep_hours": 7.0,
        "data_source": "Synthetic demonstration data",
    }])
    queued = queue_latest_summary(observations)
    assert queued["status"] == "Queued — Not Transmitted"
    assert queued["one_way_delay_seconds"] == 1214
    queued_at = datetime.fromisoformat(queued["queued_at"])
    arrival = datetime.fromisoformat(queued["expected_arrival"])
    assert arrival - queued_at == ONE_WAY_DELAY
    assert len(load_outbox()) == 1
    assert mark_outbox_delivered(queued["id"])
    assert load_outbox()[0]["status"] == "Delivered (simulated; not transmitted)"


def test_selected_historical_date_is_saved_and_loaded(tmp_path, monkeypatch):
    monkeypatch.setenv("CAELIVIS_DATA_DIR", str(tmp_path))
    chosen = "2024-02-29"
    save_checkin(valid_record(date=chosen))
    loaded = load_checkins()
    assert loaded[0]["date"] == chosen
    frame = load_observations(tmp_path / "missing.csv", loaded)
    assert chosen in set(frame["date"].dt.strftime("%Y-%m-%d"))


def test_malformed_json_is_warned_and_never_overwritten(tmp_path, monkeypatch):
    monkeypatch.setenv("CAELIVIS_DATA_DIR", str(tmp_path))
    path = tmp_path / "checkins.json"
    original = "{ definitely not json"
    path.write_text(original, encoding="utf-8")
    records, warnings = load_checkins_with_warnings()
    assert records == []
    assert warnings and "left untouched" in warnings[0]
    with pytest.raises(StorageError):
        save_checkin(valid_record())
    assert path.read_text(encoding="utf-8") == original


def test_invalid_record_does_not_hide_valid_record_or_get_discarded(tmp_path, monkeypatch):
    monkeypatch.setenv("CAELIVIS_DATA_DIR", str(tmp_path))
    records = [valid_record(), valid_record(date="not-a-date"), valid_record(heart_rate_bpm=float("nan")), {"date": "2026-01-01"}]
    path = tmp_path / "checkins.json"
    original = json.dumps(records)
    path.write_text(original, encoding="utf-8")
    loaded, warnings = load_checkins_with_warnings()
    assert len(loaded) == 1
    assert loaded[0]["date"] == "2026-01-02"
    assert len(warnings) == 3
    save_checkin(valid_record(date="2026-01-03"))
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert len(persisted) == 5
    assert persisted[1]["date"] == "not-a-date"


def test_unreadable_or_wrong_shape_outbox_warns(tmp_path, monkeypatch):
    monkeypatch.setenv("CAELIVIS_DATA_DIR", str(tmp_path))
    path = tmp_path / "outbox.json"
    path.write_text("{}", encoding="utf-8")
    outbox, warnings = load_outbox_with_warnings()
    assert outbox == [] and warnings


def test_trend_figure_valid_and_empty_data():
    frame = generate_synthetic_data(days=3)
    figure = build_trend_figure(frame, "heart_rate_bpm", "Heart rate", "bpm", 65.0)
    assert figure is not None and len(figure.data) == 1
    assert build_trend_figure(pd.DataFrame(), "heart_rate_bpm", "Heart rate", "bpm") is None
    assert build_trend_figure(frame.assign(heart_rate_bpm=float("nan")), "heart_rate_bpm", "Heart rate", "bpm") is None


# AppTest is optional for deployments using Streamlit releases without testing.v1.
def test_streamlit_navigation_and_checkin_submission(tmp_path, monkeypatch):
    pytest.importorskip("streamlit")
    try:
        from streamlit.testing.v1 import AppTest
    except ImportError:
        pytest.skip("This Streamlit version does not provide AppTest")
    monkeypatch.setenv("CAELIVIS_DATA_DIR", str(tmp_path))
    app_path = __import__("pathlib").Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    assert not app.exception
    expected_headings = {
        "Mission Health Overview": "Crew Health Overview",
        "Daily Health Check-In": "Daily Health Check-In",
        "Personal Baseline & Trends": "Personal Baseline & Trends",
        "Health Insights & Alerts": "Health Insights & Alerts",
        "Privacy & Communications": "Privacy & Communications",
    }
    for page, heading in expected_headings.items():
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception
        # _header renders each page's visible main heading with st.title().
        assert any(title.value == heading for title in app.title), f"Expected visible heading {heading!r} for navigation page {page!r}"
    app.sidebar.radio[0].set_value("Daily Health Check-In").run()
    app.date_input(key="checkin_date").set_value("2024-02-29")
    app.button(key="FormSubmitter:daily_checkin-Save check-in locally").click().run()
    saved, warnings = load_checkins_with_warnings()
    assert not warnings
    assert saved[-1]["date"] == "2024-02-29"


def test_trends_section_renders_plotly_chart(tmp_path, monkeypatch):
    pytest.importorskip("streamlit")
    try:
        from streamlit.testing.v1 import AppTest
    except ImportError:
        pytest.skip("This Streamlit version does not provide AppTest")
    monkeypatch.setenv("CAELIVIS_DATA_DIR", str(tmp_path))
    app_path = __import__("pathlib").Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run()
    app.sidebar.radio[0].set_value("Personal Baseline & Trends").run()
    assert not app.exception
    assert len(app.get("plotly_chart")) == 1


def test_digital_twin_regions_survive_navigation(tmp_path, monkeypatch):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("CAELIVIS_DATA_DIR", str(tmp_path))
    app_path = __import__("pathlib").Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()

    assert not app.exception

    for region in ("Head", "Chest", "Body"):
        app.radio[0].set_value(region).run()

        assert not app.exception
        assert app.radio[0].value == region
        assert app.session_state["digital_twin_region_preference"] == region

        app.sidebar.radio[0].set_value("Daily Health Check-In").run()
        assert not app.exception

        app.sidebar.radio[0].set_value("Mission Health Overview").run()
        assert not app.exception
        assert app.radio[0].value == region
        assert app.session_state["digital_twin_region_preference"] == region
