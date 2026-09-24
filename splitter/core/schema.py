"""Load and validate the export JSON from the backend."""

from dataclasses import dataclass
from typing import Optional
import json


@dataclass
class Clip:
    """A clip from the export JSON."""
    id: str
    type: str  # "goal" or "manual"
    title: str
    event_time: str  # HH:MM:SS match clock time
    start_time: str  # HH:MM:SS clip start on match clock
    event_at: Optional[str]  # ISO-8601 timestamp
    clip_start_at: Optional[str]  # ISO-8601 timestamp
    video_offset_seconds: Optional[int]  # seconds from recording start, or None for legacy
    duration: int  # seconds
    team: Optional[str]
    scorer: Optional[str]
    assist: Optional[str]


@dataclass
class ExportData:
    """Full export data from GET /api/export."""
    generated_at: str
    recording_started_at: str
    clips: list[Clip]


def load_export(json_path: str) -> ExportData:
    """
    Load and validate the export JSON file.

    Args:
        json_path: Path to the export JSON file.

    Returns:
        ExportData with validated clips.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        json.JSONDecodeError: If the file is not valid JSON.
        ValueError: If the JSON structure is invalid (missing "clips" key or not a list).
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "clips" not in data:
        raise ValueError('Export JSON missing required "clips" key')
    if not isinstance(data["clips"], list):
        raise ValueError('"clips" must be a list')

    clips = []
    for i, clip_data in enumerate(data["clips"]):
        # Validate required fields
        required_fields = ["id", "type", "title", "event_time", "start_time", "duration"]
        for field in required_fields:
            if field not in clip_data:
                raise ValueError(f'Clip at index {i} missing required field: "{field}"')

        clip = Clip(
            id=clip_data["id"],
            type=clip_data["type"],
            title=clip_data["title"],
            event_time=clip_data["event_time"],
            start_time=clip_data["start_time"],
            event_at=clip_data.get("event_at"),
            clip_start_at=clip_data.get("clip_start_at"),
            video_offset_seconds=clip_data.get("video_offset_seconds"),
            duration=clip_data["duration"],
            team=clip_data.get("team"),
            scorer=clip_data.get("scorer"),
            assist=clip_data.get("assist"),
        )
        clips.append(clip)

    return ExportData(
        generated_at=data["generated_at"],
        recording_started_at=data["recording_started_at"],
        clips=clips,
    )