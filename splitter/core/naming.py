"""Pure functions for sanitizing and building output filenames."""

import re
from .schema import Clip


def sanitize_slug(text: str) -> str:
    """
    Sanitize a string for use in a filename.

    - Strip whitespace
    - Replace every run of non-[A-Za-z0-9] with a single "-"
    - Strip leading/trailing "-"
    - Truncate to 60 characters
    - If empty, return "clip"
    """
    if not text:
        return "clip"

    # Strip whitespace
    text = text.strip()

    # Replace runs of non-alphanumeric with single "-"
    text = re.sub(r"[^A-Za-z0-9]+", "-", text)

    # Strip leading/trailing "-"
    text = text.strip("-")

    # Truncate to 60 characters
    text = text[:60]

    # If empty after sanitization, use "clip"
    if not text:
        return "clip"

    return text


def build_type_label(clip_type: str) -> str:
    """Return 'Goal' for goal clips, 'Clip' for everything else."""
    return "Goal" if clip_type == "goal" else "Clip"


def build_slug(clip: Clip) -> str:
    """
    Build the slug portion of the filename.

    For goal clips with both team and scorer: "{team}-{scorer}" (+ "-assist-{assist}" if assist)
    Otherwise: use the title
    Then sanitize.
    """
    if clip.type == "goal" and clip.team and clip.scorer:
        parts = [clip.team, clip.scorer]
        if clip.assist:
            parts.append(f"assist-{clip.assist}")
        slug = "-".join(parts)
    else:
        slug = clip.title

    return sanitize_slug(slug)


def build_filename(seq: int, clip: Clip) -> str:
    """
    Build the full output filename.

    Format: {seq:03d}_{type_label}_{slug}.mp4
    """
    type_label = build_type_label(clip.type)
    slug = build_slug(clip)
    return f"{seq:03d}_{type_label}_{slug}.mp4"