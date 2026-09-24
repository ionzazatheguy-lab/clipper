"""ffprobe/ffmpeg subprocess wrappers."""

import subprocess
import shutil
import os
import tempfile


def probe_duration(video_path: str) -> float:
    """
    Probe video duration using ffprobe.

    Args:
        video_path: Path to the video file.

    Returns:
        Duration in seconds as float.

    Raises:
        FileNotFoundError: If ffprobe is not on PATH.
        RuntimeError: If ffprobe fails to read the video.
    """
    if shutil.which("ffprobe") is None:
        raise FileNotFoundError("ffprobe not found on PATH. Please install ffmpeg.")

    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"ffprobe timed out reading {video_path}")

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")

    try:
        duration = float(result.stdout.strip())
    except ValueError:
        raise RuntimeError(f"ffprobe returned invalid duration: {result.stdout.strip()}")

    if duration <= 0:
        raise RuntimeError(f"Video has zero or negative duration: {duration}")

    return duration


def cut_clip(video_path: str, offset: float, duration: float, output_path: str) -> tuple[bool, str]:
    """
    Cut a clip from the video using ffmpeg.

    Uses a temp file + atomic replace to avoid leaving broken files.

    Args:
        video_path: Source video file.
        offset: Start offset in seconds.
        duration: Clip duration in seconds.
        output_path: Final output path.

    Returns:
        (success, stderr_tail) where stderr_tail is last ~10 lines of stderr on failure.
    """
    if shutil.which("ffmpeg") is None:
        return False, "ffmpeg not found on PATH"

    # Create temp file in same directory for atomic replace
    output_dir = os.path.dirname(output_path) or "."
    temp_fd, temp_path = tempfile.mkstemp(suffix=".mp4.part", dir=output_dir)
    os.close(temp_fd)

    try:
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", str(offset),
            "-i", video_path,
            "-t", str(duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-avoid_negative_ts", "make_zero",
            "-f", "mp4",
            temp_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            # Get last ~10 lines of stderr
            stderr_lines = result.stderr.strip().split("\n")
            stderr_tail = "\n".join(stderr_lines[-10:])
            return False, stderr_tail

        # Atomic replace
        os.replace(temp_path, output_path)
        return True, ""

    except subprocess.TimeoutExpired:
        return False, "ffmpeg timed out"
    except Exception as e:
        return False, str(e)
    finally:
        # Clean up temp file if it still exists
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except OSError:
            pass