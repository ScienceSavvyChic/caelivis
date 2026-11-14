"""Local-only JSON storage with validation and non-destructive error handling."""

import json
import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "local"
ONE_WAY_DELAY = timedelta(minutes=20, seconds=14)
CREW_SOURCE = "Crew-entered demonstration data"
SYNTHETIC_SOURCE = "Synthetic demonstration data"
CHECKIN_NUMERIC_FIELDS = (
    "heart_rate_bpm", "systolic_bp_mmhg", "diastolic_bp_mmhg", "temperature_c",
    "sleep_hours", "sleep_quality_1_5", "exercise_minutes", "mood_1_5",
    "stress_1_5", "cognitive_wellbeing_1_5", "fatigue_1_5",
)
OPTIONAL_NUMERIC_FIELDS = ("glucose_mg_dl",)


class StorageError(Exception):
    """Raised when writing would risk replacing unreadable or invalid source data."""


def data_dir() -> Path:
    path = Path(os.environ.get("CAELIVIS_DATA_DIR", DEFAULT_DATA_DIR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_raw(name: str):
    path = data_dir() / name
    if not path.exists():
        return [], []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        return None, [f"Could not read {name} ({exc}); the original file was left untouched."]
    if not isinstance(raw, list):
        return None, [f"{name} must contain a JSON list; the original file was left untouched."]
    return raw, []


def _write(name: str, value) -> None:
    path = data_dir() / name
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)
    except OSError:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _finite_number(record: dict, key: str, optional: bool = False) -> bool:
    value = record.get(key)
    if optional and value is None:
        return True
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value))


def _canonical_source(value) -> str | None:
    if value in (SYNTHETIC_SOURCE, "Synthetic demonstration"):
        return SYNTHETIC_SOURCE
    if value in (CREW_SOURCE, "Local check-in", "Crew-entered demonstration"):
        return CREW_SOURCE
    return None


def validate_checkin(record) -> tuple[dict | None, str | None]:
    """Validate one record without changing the source file; return normalized copy."""
    if not isinstance(record, dict):
        return None, "record is not a JSON object"
    missing = [key for key in ("date", *CHECKIN_NUMERIC_FIELDS, "data_source") if key not in record]
    if missing:
        return None, "missing required fields: " + ", ".join(missing)
    try:
        parsed_date = datetime.fromisoformat(str(record["date"]).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None, "invalid observation date"
    if not all(_finite_number(record, key) for key in CHECKIN_NUMERIC_FIELDS):
        return None, "one or more required numeric fields are invalid"
    for key in OPTIONAL_NUMERIC_FIELDS:
        if key in record and not _finite_number(record, key, optional=True):
            return None, f"{key} must be a finite number or null"
    source = _canonical_source(record.get("data_source"))
    if source is None:
        return None, "data_source is missing or not an approved demonstration source"
    cleaned = dict(record)
    cleaned["date"] = parsed_date.date().isoformat()
    cleaned["data_source"] = source
    return cleaned, None


def _valid_outbox_item(item) -> bool:
    if not isinstance(item, dict):
        return False
    required = ("id", "queued_at", "expected_arrival", "status", "payload", "observation_timestamp")
    if any(key not in item for key in required):
        return False
    try:
        datetime.fromisoformat(str(item["queued_at"]))
        datetime.fromisoformat(str(item["expected_arrival"]))
        datetime.fromisoformat(str(item["observation_timestamp"]))
    except (TypeError, ValueError):
        return False
    return isinstance(item["payload"], dict)


def load_checkins_with_warnings() -> tuple[list[dict], list[str]]:
    raw, warnings = _read_raw("checkins.json")
    if raw is None:
        return [], warnings
    valid = []
    for index, record in enumerate(raw):
        cleaned, issue = validate_checkin(record)
        if issue:
            warnings.append(f"checkins.json record {index + 1} was not loaded: {issue}. Original data was preserved.")
        else:
            valid.append(cleaned)
    return valid, warnings


def load_checkins() -> list[dict]:
    return load_checkins_with_warnings()[0]


def save_checkin(record: dict) -> None:
    cleaned, issue = validate_checkin(record)
    if issue:
        raise ValueError(f"Invalid check-in: {issue}")
    raw, warnings = _read_raw("checkins.json")
    if raw is None or warnings:
        raise StorageError("Existing check-in file is unreadable; refusing to overwrite it.")
    # Keep every existing JSON record, including invalid records, so a save cannot
    # silently discard user data. Validation only controls what the app displays.
    raw.append(cleaned)
    _write("checkins.json", raw)


def load_outbox_with_warnings() -> tuple[list[dict], list[str]]:
    raw, warnings = _read_raw("outbox.json")
    if raw is None:
        return [], warnings
    valid = []
    for index, item in enumerate(raw):
        if _valid_outbox_item(item):
            valid.append(item)
        else:
            warnings.append(f"outbox.json record {index + 1} is incomplete or invalid; original data was preserved.")
    return valid, warnings


def load_outbox() -> list[dict]:
    return load_outbox_with_warnings()[0]


def queue_latest_summary(observations) -> dict | None:
    if observations.empty:
        return None
    row = observations.iloc[-1]
    queued_at = datetime.now(timezone.utc)
    date_value = row.get("date")
    if hasattr(date_value, "to_pydatetime"):
        date_value = date_value.to_pydatetime()
    if isinstance(date_value, datetime):
        observation_time = date_value
    else:
        observation_time = datetime.fromisoformat(str(date_value)).replace(tzinfo=timezone.utc)
    if observation_time.tzinfo is None:
        observation_time = observation_time.replace(tzinfo=timezone.utc)
    observation_time = observation_time.astimezone(timezone.utc)
    payload = {
        "heart_rate_bpm": int(row["heart_rate_bpm"]),
        "blood_pressure_mmhg": f"{int(row['systolic_bp_mmhg'])}/{int(row['diastolic_bp_mmhg'])}",
        "sleep_hours": float(row["sleep_hours"]),
        "data_source": _canonical_source(row.get("data_source")) or "Unknown demonstration source",
    }
    item = {
        "id": queued_at.strftime("%Y%m%dT%H%M%S%fZ"),
        "observation_timestamp": observation_time.isoformat(),
        "queued_at": queued_at.isoformat(),
        "one_way_delay_seconds": int(ONE_WAY_DELAY.total_seconds()),
        "expected_arrival": (queued_at + ONE_WAY_DELAY).isoformat(),
        "status": "Queued — Not Transmitted",
        "payload": payload,
    }
    raw, warnings = _read_raw("outbox.json")
    if raw is None or warnings:
        raise StorageError("Existing outbox file is unreadable; refusing to overwrite it.")
    raw.append(item)
    _write("outbox.json", raw)
    return item


def mark_outbox_delivered(item_id: str) -> bool:
    raw, warnings = _read_raw("outbox.json")
    if raw is None or warnings:
        raise StorageError("Existing outbox file is unreadable; refusing to overwrite it.")
    for item in raw:
        if _valid_outbox_item(item) and item["id"] == item_id:
            item["status"] = "Delivered (simulated; not transmitted)"
            item["simulated_delivered_at"] = datetime.now(timezone.utc).isoformat()
            _write("outbox.json", raw)
            return True
    return False
