# Ball We Cup Clipper

A live match-event logger for football: timestamp goals and highlights during a match, then export those timestamps so a source recording can be cut into individual clips using the standalone splitter tool.

## Architecture

- **Backend** — FastAPI 0.109+ REST API (Python 3.10+) serving clip metadata and team/player management. Stores data as JSON files in `backend/data/`. Exposes `/api/health`, `/api/dashboard`, `/api/recording-start`, `/api/teams`, `/api/events`, and `/api/export`.
- **Frontend** — Vanilla JS + Vite 5.2 single-page app (port 5173). Proxies `/api` to the backend on port 8000. Lets you manage rosters, log goals with scorer/assist, mark manual clips, set the recording start timestamp, and download the export JSON.
- **Splitter** — Standalone Python CLI (`splitter/split_clips.py`) that reads the backend's export JSON and a video file, then uses ffmpeg/ffprobe to cut clips. Does not talk to the backend directly.

## Prerequisites

- **Python** ≥ 3.10 (from `backend/pyproject.toml` `requires-python`)
- **Node.js** (Vite 5.2 requires a modern Node; no explicit engine field in `package.json`)
- **ffmpeg** + **ffprobe** on PATH (required by the splitter; `brew install ffmpeg` on macOS, `apt install ffmpeg` on Linux)

## Backend Setup & Running

```bash
cd backend
pip install -r requirements.txt
python run.py
```

The server starts on `http://0.0.0.0:8000` (see `pyproject.toml` `[tool.uvicorn]` and `run.py`).

## Frontend Setup & Running

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server starts on port 5173 and proxies `/api` to `http://localhost:8000` (see `vite.config.js`). Production build: `npm run build`.

## End-to-End Workflow

1. Start the backend: `cd backend && python run.py`
2. Start the frontend: `cd frontend && npm run dev`
3. Open the frontend (default `http://localhost:5173`)
4. Add team rosters (teams + players)
5. Click **Recording started now** (or set a manual date/time) to mark when the video recording began
6. During the match: click **Log goal at current time** (select team/scorer/assist) or use **Manual clip** for non-goal highlights
7. When done, click **Download event export** → saves `ball-we-cup-events.json`
8. Run the splitter against that JSON and the match video:
   ```bash
   cd splitter
   python split_clips.py --video /path/to/match.mp4 --clips /path/to/ball-we-cup-events.json --output ./clips
   ```

## Splitter CLI Usage

The splitter exists at `splitter/split_clips.py`. Exact flags from its `argparse` definition:

| Flag | Required | Description |
|------|----------|-------------|
| `--video` | yes | Source video file (any ffmpeg-readable format) |
| `--clips` | yes | Export JSON from the **Download event export** button |
| `--output` | yes | Output directory for clips (created if missing) |
| `--overwrite` | no | Re-cut and replace existing clip files |
| `--dry-run` | no | Print the cut plan without writing any files |

Examples:
```bash
# Normal run
python split_clips.py --video match.mp4 --clips export.json --output ./clips

# Re-cut existing clips
python split_clips.py --video match.mp4 --clips export.json --output ./clips --overwrite

# Preview what would be cut
python split_clips.py --video match.mp4 --clips export.json --output ./clips --dry-run
```

The tool validates ffmpeg/ffprobe are on PATH, the video exists, the JSON is valid, and the output directory is writable before cutting. Clips are named `{seq:03d}_{Goal|Clip}_{slug}.mp4` where the slug is sanitized from team/scorer (goals) or title (manual clips).

## Project Structure

```
clipper/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI routes
│   │   ├── models.py         # Pydantic models
│   │   ├── storage.py        # JSON file persistence
│   │   └── export.py         # Builds splitter export JSON
│   ├── data/                 # clips.json, match_start.json (created at runtime)
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── run.py                # uvicorn entry point
├── frontend/
│   ├── index.html
│   ├── src/
│   │   ├── main.js           # App entry + UI rendering
│   │   ├── api.js            # Fetch wrappers for /api/*
│   │   └── style.css
│   ├── package.json
│   └── vite.config.js        # Proxies /api to localhost:8000
└── splitter/
    ├── split_clips.py        # CLI entry point
    ├── core/
    │   ├── __init__.py
    │   ├── schema.py         # Load + validate export JSON
    │   ├── planner.py        # Resolve offsets/durations, build cut plan
    │   ├── naming.py         # Sanitize + build output filenames
    │   └── ffmpeg_runner.py  # ffprobe/ffmpeg subprocess wrappers
    └── README.md
```

## Troubleshooting

- **ffmpeg/ffprobe not found** — Install ffmpeg (`brew install ffmpeg` or `apt install ffmpeg`) and ensure both binaries are on PATH. The splitter exits with a clear error if either is missing.
- **Backend port 8000 already in use** — Stop the conflicting process or change the port in `backend/pyproject.toml` `[tool.uvicorn]` and `backend/run.py`.
- **Frontend port 5173 already in use** — Vite will auto-pick the next free port; check the terminal output.
- **CORS errors** — The backend allows `http://localhost:5173` and `http://127.0.0.1:5173` (see `main.py` CORS middleware). If you access the frontend via a different hostname, add it to `allow_origins`.
- **Export fails with "Mark when recording started before logging clips"** — You must set the recording start timestamp (via the UI button or manual form) before any clips can be exported.
- **Splitter "already exists" messages** — Re-run with `--overwrite` to replace existing clip files.