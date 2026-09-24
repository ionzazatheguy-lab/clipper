# Ball We Cup Clipper — Video Splitter

Install ffmpeg: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux).

Run the splitter:
```bash
python split_clips.py --video match.mp4 --clips export.json --output ./clips
```

Flags:
- `--overwrite` — re-cut and replace existing clips
- `--dry-run` — print plan without cutting