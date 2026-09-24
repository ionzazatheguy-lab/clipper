# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Ball We Cup Clipper** — Football video clipping tool with three components:
1. **Backend** — FastAPI REST API for clip management (port 8000)
2. **Frontend** — Mobile-compatible Vanilla JS + Vite web app (port 5173)
3. **Clip Splitter** — Standalone Python CLI tool using ffmpeg to split recordings

## Architecture

```
clipper/
├── backend/          # FastAPI API
│   ├── app/
│   │   ├── main.py           # FastAPI app, routes
│   │   ├── models.py         # Pydantic models
│   │   ├── storage.py        # JSON file persistence
│   │   └── export.py         # JSON export for splitter
│   ├── data/
│   │   ├── clips.json        # Clip metadata
│   │   └── match_start.json  # Match start time
│   ├── requirements.txt
│   └── run.py                # uvicorn entry point
├── frontend/         # Vanilla JS + Vite
│   ├── index.html
│   ├── src/
│   │   ├── main.js
│   │   ├── style.css
│   │   ├── api.js
│   │   ├── components/
│   │   └── utils/
│   ├── package.json
│   └── vite.config.js       # Proxy /api to backend:8000
└── splitter/         # Python CLI tool
    ├── split_clips.py        # CLI entry point
    ├── core/
    │   ├── __init__.py
    │   ├── schema.py          # load + validate export JSON
    │   ├── planner.py         # pure functions: resolve offset/duration, build plan
    │   ├── naming.py          # pure functions: sanitize + build filenames
    │   └── ffmpeg_runner.py   # ffprobe/ffmpeg subprocess wrappers
    └── README.md
```

## Key Commands

### Backend
```bash
cd backend && pip install -r requirements.txt
cd backend && python run.py              # Dev server on :8000
```

### Frontend
```bash
cd frontend && npm install
cd frontend && npm run dev               # Dev server on :5173 (proxies /api to :8000)
cd frontend && npm run build             # Production build
```

### Splitter
```bash
cd splitter && python split_clips.py --video match.mp4 --clips export.json --output ./clips
```

## Data Models

**Clip** (stored in `backend/data/clips.json`):
```json
{
  "id": "uuid",
  "name": "Goal",
  "start_time": "00:10:30",
  "duration": 600,
  "end_time": "00:20:30",
  "created_at": "2026-09-17T10:30:00Z"
}
```

**Match Start** (stored in `backend/data/match_start.json`):
```json
{"match_start": "10:30:00"}
```

**Splitter Export JSON** (from `GET /api/export`):
```json
{
  "generated_at": "2026-09-24T10:15:00Z",
  "recording_started_at": "2026-09-24T09:00:00Z",
  "clips": [
    {
      "id": "3f9a1e2b-...",
      "type": "goal",
      "title": "Goal",
      "event_time": "09:15:42",
      "start_time": "09:15:12",
      "event_at": "2026-09-24T09:15:42Z",
      "clip_start_at": "2026-09-24T09:15:12Z",
      "video_offset_seconds": 912,
      "duration": 30,
      "team": "Red Dragons",
      "scorer": "Aarav Singh",
      "assist": "Priya Nair"
    },
    {
      "id": "b21c...",
      "type": "manual",
      "title": "Great save",
      "event_time": "09:20:05",
      "start_time": "09:19:50",
      "event_at": "2026-09-24T09:20:05Z",
      "clip_start_at": "2026-09-24T09:19:50Z",
      "video_offset_seconds": 1190,
      "duration": 15,
      "team": null,
      "scorer": null,
      "assist": null
    },
    {
      "id": "old-1",
      "type": "manual",
      "title": "Legacy clip",
      "event_time": "00:20:30",
      "start_time": "00:10:30",
      "event_at": null,
      "clip_start_at": null,
      "video_offset_seconds": null,
      "duration": 600,
      "team": null,
      "scorer": null,
      "assist": null
    }
  ]
}
```

**Critical field semantics:**
- If `video_offset_seconds` is NOT null → modern clip: use `video_offset_seconds` directly (precomputed seconds into video). IGNORE `start_time`.
- If `video_offset_seconds` IS null → legacy clip: `start_time` (HH:MM:SS) IS ALREADY video-relative offset. Parse directly to seconds (H*3600 + M*60 + S). Do NOT combine with `recording_started_at`.

## Development Workflow

1. Start backend: `cd backend && python run.py`
2. Start frontend: `cd frontend && npm run dev`
3. Create clips via web UI → Export JSON (click "Download event export")
4. Run splitter: `cd splitter && python split_clips.py --video match.mp4 --clips export.json --output ./out`

## Important Notes

- Frontend proxies `/api` to `http://localhost:8000` via Vite config
- Clip durations are editable (default 30 seconds)
- Match start time captured via "Set Now" button or manual entry
- Splitter uses ffmpeg with `-c:v libx264 -c:a aac` for MP4 output
- Output clip names: `{seq:03d}_{Goal|Clip}_{slug}.mp4` where slug is sanitized team-scorer (for goals) or title (for manual clips)
- No authentication — public access
- ffmpeg must be installed on splitter machine
- No Python dependencies beyond stdlib (ffmpeg/ffprobe are external binaries)