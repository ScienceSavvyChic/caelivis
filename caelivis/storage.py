"""Local-only JSON storage for check-ins and simulated outbound messages."""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "local"
ONE_WAY_DELAY = timedelta(minutes=20, seconds=14)


def data_dir() -> Path:
    path = Path(os.environ.get("CAELIVIS_DATA_DIR", DEFAULT_DATA_DIR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read(name: str, default):
    path = data_dir() / name
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _write(name: str, value) -> None:
    path = data_dir() / name
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def load_checkins() -> list[dict]:
    return _read("checkins.json", [])


def save_checkin(record: dict) -> None:
    records = load_checkins()
    records.append(record)
    _write("checkins.json", records)


def load_outbox() -> list[dict]:
    return _read("outbox.json", [])


def queue_latest_summary(observations) -> dict | None:
    if observations.empty:
        return None
    row = observations.iloc[-1]
    created = datetime.now(timezone.utc)
    payload = {
        "heart_rate_bpm": int(row["heart_rate_bpm"]),
        "blood_pressure_mmhg": f"{int(row['systolic_bp_mmhg'])}/{int(row['diastolic_bp_mmhg'])}",
        "sleep_hours": float(row["sleep_hours"]),
        "data_source": str(row.get("data_source", "Unknown")),
    }
    item = {
        "id": created.strftime("%Y%m%dT%H%M%S%fZ"),
        "queued_at": created.isoformat(),
        "expected_arrival": (created + ONE_WAY_DELAY).isoformat(),
        "status": "queued (simulation only)",
        "payload": payload,
    }
    outbox = load_outbox()
    outbox.append(item)
    _write("outbox.json", outbox)
    return item


def mark_outbox_delivered(item_id: str) -> bool:
    outbox = load_outbox()
    for item in outbox:
        if item["id"] == item_id:
            item["status"] = "delivered (simulated)"
            item["simulated_delivered_at"] = datetime.now(timezone.utc).isoformat()
            _write("outbox.json", outbox)
            return True
    return False
