#!/usr/bin/env python3
"""CLI entry point for the video clip splitter."""

import argparse
import sys
import os
import shutil
import json
from pathlib import Path

from core.schema import load_export
from core.planner import plan_clips
from core.ffmpeg_runner import probe_duration, cut_clip


def format_offset(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def main():
    parser = argparse.ArgumentParser(
        description="Split a match recording into clips using an export JSON from Ball We Cup Clipper.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python split_clips.py --video match.mp4 --clips export.json --output ./clips
  python split_clips.py --video match.mp4 --clips export.json --output ./clips --overwrite
  python split_clips.py --video match.mp4 --clips export.json --output ./clips --dry-run
        """
    )
    parser.add_argument("--video", required=True, help="Source video file (any ffmpeg-readable format)")
    parser.add_argument("--clips", required=True, help="Export JSON from 'Download event export' button")
    parser.add_argument("--output", required=True, help="Output directory for clips")
    parser.add_argument("--overwrite", action="store_true", help="Re-cut and replace existing clips")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without cutting")

    args = parser.parse_args()

    # Startup checks (fail fast with clear errors)
    # a. ffmpeg on PATH
    if shutil.which("ffmpeg") is None:
        print("Error: ffmpeg not found on PATH. Please install ffmpeg.", file=sys.stderr)
        sys.exit(1)

    # b. ffprobe on PATH (required for video duration; optional for --dry-run)
    has_ffprobe = shutil.which("ffprobe") is not None
    if not has_ffprobe and not args.dry_run:
        print("Error: ffprobe not found on PATH. Please install ffmpeg.", file=sys.stderr)
        sys.exit(1)

    # c. --video path exists and readable by ffprobe
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: Video file not found: {args.video}", file=sys.stderr)
        sys.exit(1)

    # d. --clips path exists
    clips_path = Path(args.clips)
    if not clips_path.exists():
        print(f"Error: Clips JSON not found: {args.clips}", file=sys.stderr)
        sys.exit(1)

    # e. --clips is valid JSON
    try:
        export_data = load_export(args.clips)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in clips file: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # f. Already validated by load_export (has "clips" key as list)

    # g. --output can be created/written
    output_dir = Path(args.output)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        # Test write permission
        test_file = output_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
    except (OSError, PermissionError) as e:
        print(f"Error: Cannot create or write to output directory: {e}", file=sys.stderr)
        sys.exit(1)

    # Probe video duration once (required for non-dry-run, optional for dry-run)
    video_duration = None
    if has_ffprobe:
        try:
            video_duration = probe_duration(str(video_path))
        except RuntimeError as e:
            print(f"Error: Cannot read video file: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.dry_run:
        print("Warning: ffprobe not found; dry-run will show all clips but cannot clamp to video duration", file=sys.stderr)
        video_duration = float('inf')  # No clamping without video duration
    else:
        print("Error: ffprobe not found on PATH. Please install ffmpeg.", file=sys.stderr)
        sys.exit(1)

    # Handle empty clips list
    if not export_data.clips:
        print("No clips to process.")
        sys.exit(0)

    # Plan all clips
    planned = plan_clips(export_data.clips, video_duration)

    # Counters for summary
    created = 0
    already_existed = 0
    data_skipped = 0
    failed = 0

    # Process each planned clip
    total_clips = len([p for p in planned if p.skip_reason is None])

    for p in planned:
        if p.skip_reason:
            print(f"Warning: Skipping clip '{p.clip.title}' ({p.clip.id}): {p.skip_reason}", file=sys.stderr)
            data_skipped += 1
            continue

        output_path = output_dir / p.filename

        # Check if already exists
        if output_path.exists() and not args.overwrite:
            print(f"[{p.seq}/{total_clips}] {p.filename}  offset={format_offset(p.offset)} duration={p.duration:.0f}s  already exists (use --overwrite)")
            already_existed += 1
            continue

        # Dry run: just print plan
        if args.dry_run:
            print(f"[{p.seq}/{total_clips}] {p.filename}  offset={format_offset(p.offset)} duration={p.duration:.0f}s  dry-run")
            created += 1
            continue

        # Print progress
        print(f"[{p.seq}/{total_clips}] {p.filename}  offset={format_offset(p.offset)} duration={p.duration:.0f}s  cutting...", end=" ", flush=True)

        # Cut the clip
        success, stderr_tail = cut_clip(str(video_path), p.offset, p.duration, str(output_path))

        if success:
            print("done")
            created += 1
        else:
            print("FAILED")
            print(f"  ffmpeg error: {stderr_tail}", file=sys.stderr)
            failed += 1

    # Print summary
    if args.dry_run:
        print(f"\nDry run complete. {created} clips would be created.")
    else:
        print(f"\n{created} created, {already_existed} already existed (use --overwrite), {data_skipped} skipped (bad data), {failed} failed")

    # Exit with error code if any failed
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()