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
    ├── split_clips.py
    ├── clipper/
    │   ├── parser.py
    │   ├── ffmpeg.py
    │   └── naming.py
    └── requirements.txt
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
cd splitter && pip install -r requirements.txt
cd splitter && python split_clips.py --video match.mp4 --clips clips.json --output ./clips
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

**Splitter Export JSON**:
```json
{
  "match_start": "10:30:00",
  "video_path": "/path/to/match.mp4",
  "clips": [{"name": "Goal", "start_time": "00:00:00", "duration": 600, "end_time": "00:10:00"}]
}
```

## Development Workflow

1. Start backend: `cd backend && python run.py`
2. Start frontend: `cd frontend && npm run dev`
3. Create clips via web UI → Export JSON
4. Run splitter: `cd splitter && python split_clips.py --video match.mp4 --clips export.json --output ./out`

## Important Notes

- Frontend proxies `/api` to `http://localhost:8000` via Vite config
- Clip durations are editable (default 10:00 minutes)
- Match start time captured via "Set Now" button or manual entry
- Splitter uses ffmpeg with `-c:v libx264 -c:a aac` for MP4 output
- Output clip names use custom names from JSON with `_1`, `_2` suffix for duplicates
- No authentication — public access
- ffmpeg must be installed on splitter machine