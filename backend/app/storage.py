"""JSON-backed persistence for teams and clipping events."""

import json
from pathlib import Path
from threading import Lock

from .models import Clip, Event, Team

DATA_DIR = Path(__file__).parent.parent / "data"
CLIPS_FILE = DATA_DIR / "clips.json"
TEAMS_FILE = DATA_DIR / "teams.json"
EVENTS_FILE = DATA_DIR / "events.json"
RECORDING_FILE = DATA_DIR / "recording.json"
_file_lock = Lock()


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default):
    _ensure_data_dir()
    if not path.exists():
        return default
    try:
        with path.open() as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return default


def _write_json(path: Path, data) -> None:
    _ensure_data_dir()
    temporary = path.with_suffix(".tmp")
    with temporary.open("w") as file:
        json.dump(data, file, indent=2)
    temporary.replace(path)


def get_teams() -> list[Team]:
    with _file_lock:
        return [Team(**item) for item in _read_json(TEAMS_FILE, [])]


def save_teams(teams: list[Team]) -> None:
    with _file_lock:
        _write_json(TEAMS_FILE, [team.model_dump() for team in teams])


def _legacy_events() -> list[Event]:
    clips = [Clip(**item) for item in _read_json(CLIPS_FILE, [])]
    return [
        Event(id=clip.id, type="manual", title=clip.name or "Legacy clip", event_time=clip.end_time,
              clip_start=clip.start_time, duration=clip.duration, created_at=clip.created_at)
        for clip in clips
    ]


def get_events() -> list[Event]:
    with _file_lock:
        if EVENTS_FILE.exists():
            return [Event(**item) for item in _read_json(EVENTS_FILE, [])]
        return _legacy_events()


def save_events(events: list[Event]) -> None:
    with _file_lock:
        _write_json(EVENTS_FILE, [event.model_dump() for event in events])


def materialize_events() -> list[Event]:
    """Persist legacy clips as manual events before the first event mutation."""
    with _file_lock:
        if EVENTS_FILE.exists():
            return [Event(**item) for item in _read_json(EVENTS_FILE, [])]
        events = _legacy_events()
        _write_json(EVENTS_FILE, [event.model_dump() for event in events])
        return events


def get_recording_start() -> str | None:
    with _file_lock:
        return _read_json(RECORDING_FILE, {}).get("recording_started_at")


def set_recording_start(recording_started_at: str) -> None:
    with _file_lock:
        _write_json(RECORDING_FILE, {"recording_started_at": recording_started_at})


def clear_recording_start() -> None:
    with _file_lock:
        if RECORDING_FILE.exists():
            RECORDING_FILE.unlink()
