"""JSON export for clip splitter."""

from pathlib import Path
from typing import List

from .models import ExportData, Clip
from .storage import get_clips, get_match_start


def build_export(video_path: str) -> ExportData:
    """Build export data for the clip splitter."""
    match_start = get_match_start()
    clips = get_clips()

    if not match_start:
        raise ValueError("Match start time not set")

    clip_dicts = []
    for clip in clips:
        clip_dicts.append({
            "name": clip.name,
            "start_time": clip.start_time,
            "duration": clip.duration,
            "end_time": clip.end_time,
        })

    return ExportData(
        match_start=match_start.match_start,
        video_path=video_path,
        clips=clip_dicts,
    )


def export_to_file(video_path: str, output_path: str) -> None:
    """Export clips data to JSON file for splitter."""
    export_data = build_export(video_path)
    Path(output_path).write_text(export_data.model_dump_json(indent=2))