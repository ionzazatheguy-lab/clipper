"""JSON file persistence for Ball We Cup Clipper."""

import json
import os
from pathlib import Path
from typing import List, Optional
from threading import Lock

from .models import Clip, MatchStart

# File paths
DATA_DIR = Path(__file__).parent.parent / "data"
CLIPS_FILE = DATA_DIR / "clips.json"
MATCH_START_FILE = DATA_DIR / "match_start.json"

# File lock for thread safety
_file_lock = Lock()


def _ensure_data_dir() -> None:
    """Ensure data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(file_path: Path, default: any) -> any:
    """Read JSON file with default fallback."""
    _ensure_data_dir()
    if not file_path.exists():
        return default
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def _write_json(file_path: Path, data: any) -> None:
    """Write JSON file atomically."""
    _ensure_data_dir()
    temp_path = file_path.with_suffix(".tmp")
    with open(temp_path, "w") as f:
        json.dump(data, f, indent=2)
    temp_path.replace(file_path)


# Clip operations
def get_clips() -> List[Clip]:
    """Get all clips from storage."""
    with _file_lock:
        data = _read_json(CLIPS_FILE, [])
        return [Clip(**item) for item in data]


def add_clip(clip: Clip) -> Clip:
    """Add a new clip to storage."""
    with _file_lock:
        data = _read_json(CLIPS_FILE, [])
        clips = [Clip(**item) for item in data]
        clips.append(clip)
        _write_json(CLIPS_FILE, [c.model_dump() for c in clips])
    return clip


def delete_clip(clip_id: str) -> bool:
    """Delete a clip by ID. Returns True if deleted."""
    with _file_lock:
        data = _read_json(CLIPS_FILE, [])
        clips = [Clip(**item) for item in data]
        original_len = len(clips)
        clips = [c for c in clips if c.id != clip_id]
        if len(clips) < original_len:
            _write_json(CLIPS_FILE, [c.model_dump() for c in clips])
            return True
    return False


def clear_clips() -> None:
    """Clear all clips."""
    with _file_lock:
        _write_json(CLIPS_FILE, [])


# Match start operations
def get_match_start() -> Optional[MatchStart]:
    """Get match start time from storage."""
    with _file_lock:
        data = _read_json(MATCH_START_FILE, None)
        if data:
            return MatchStart(**data)
    return None


def set_match_start(match_start: MatchStart) -> MatchStart:
    """Set match start time in storage."""
    with _file_lock:
        _write_json(MATCH_START_FILE, match_start.model_dump())
    return match_start


def clear_match_start() -> None:
    """Clear match start time."""
    with _file_lock:
        if MATCH_START_FILE.exists():
            MATCH_START_FILE.unlink()