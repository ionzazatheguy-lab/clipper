"""Pure functions for planning clip extraction: resolve offsets, durations, and build the execution plan."""

from dataclasses import dataclass
from typing import Optional
from .schema import Clip
from .naming import build_filename


@dataclass
class PlannedClip:
    """A clip that has been planned for extraction."""
    clip: Clip
    seq: int
    offset: float
    duration: float
    filename: str
    warnings: list[str]
    skip_reason: Optional[str] = None


def parse_hms_to_seconds(hms: str) -> int:
    """Parse HH:MM:SS to total seconds."""
    parts = hms.split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid time format: {hms}")
    hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def resolve_offset(clip: Clip, video_duration: float) -> tuple[float, list[str]]:
    """
    Resolve the video offset for a clip.

    Returns:
        (offset_seconds, warnings)

    Skip reasons (returned via warnings, caller checks for skip):
        - "no usable offset for this clip"
        - "starts after the end of the video"
    """
    warnings = []

    if clip.video_offset_seconds is not None:
        # Modern clip: use precomputed offset directly
        offset = float(clip.video_offset_seconds)
    elif clip.start_time:
        # Legacy clip: start_time is already video-relative
        try:
            offset = float(parse_hms_to_seconds(clip.start_time))
        except ValueError as e:
            warnings.append(f"invalid start_time: {e}")
            return 0.0, warnings
    else:
        # No usable offset
        warnings.append("no usable offset for this clip")
        return 0.0, warnings

    # Clamp negative to 0
    if offset < 0:
        warnings.append(f"negative offset {offset}, clamped to 0")
        offset = 0.0

    # Check if offset is beyond video end
    if offset >= video_duration:
        warnings.append("starts after the end of the video")
        return offset, warnings

    return offset, warnings


def resolve_duration(clip: Clip, offset: float, video_duration: float) -> tuple[float, list[str]]:
    """
    Resolve the duration for a clip, clamping to video end if needed.

    Returns:
        (duration_seconds, warnings)
    """
    warnings = []

    if clip.duration <= 0:
        warnings.append("zero/negative duration")
        return 0.0, warnings

    duration = float(clip.duration)

    # Trim if clip would extend past video end
    if offset + duration > video_duration:
        trimmed_duration = video_duration - offset
        if trimmed_duration <= 0:
            warnings.append("starts after the end of the video")
            return 0.0, warnings
        warnings.append(f"duration trimmed from {duration}s to {trimmed_duration:.1f}s (video end)")
        duration = trimmed_duration

    return duration, warnings


def plan_clips(clips: list[Clip], video_duration: float) -> list[PlannedClip]:
    """
    Plan all clips for extraction.

    - Resolves offset and duration for each clip
    - Filters out clips that should be skipped (with skip_reason set)
    - Sorts remaining clips by offset ascending
    - Assigns sequence numbers 1..N
    - Builds filenames

    Returns list of PlannedClip (including skipped ones with skip_reason set).
    """
    planned = []

    for clip in clips:
        all_warnings = []

        # Resolve offset
        offset, offset_warnings = resolve_offset(clip, video_duration)
        all_warnings.extend(offset_warnings)

        # Check if we should skip due to offset issues
        skip_reason = None
        if "no usable offset for this clip" in offset_warnings:
            skip_reason = "no usable offset for this clip"
        elif "starts after the end of the video" in offset_warnings:
            skip_reason = "starts after the end of the video"

        # Resolve duration (only if not already skipping)
        duration = 0.0
        if skip_reason is None:
            duration, duration_warnings = resolve_duration(clip, offset, video_duration)
            all_warnings.extend(duration_warnings)
            if "zero/negative duration" in duration_warnings:
                skip_reason = "zero/negative duration"

        planned.append(PlannedClip(
            clip=clip,
            seq=0,  # Will be assigned after sorting
            offset=offset,
            duration=duration,
            filename="",  # Will be built after sorting
            warnings=all_warnings,
            skip_reason=skip_reason,
        ))

    # Sort by offset ascending (only non-skipped clips get sequence numbers)
    # We need to sort all clips but only number the non-skipped ones
    # Actually, let's sort all clips by offset, then assign seq to non-skipped
    planned.sort(key=lambda p: p.offset)

    # Assign sequence numbers to non-skipped clips
    seq = 1
    for p in planned:
        if p.skip_reason is None:
            p.seq = seq
            p.filename = build_filename(seq, p.clip)
            seq += 1
        else:
            p.seq = 0
            p.filename = ""

    return planned