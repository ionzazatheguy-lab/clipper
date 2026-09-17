"""FastAPI application for Ball We Cup Clipper."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import os

from .models import Clip, ClipCreate, MatchStart, MatchStartCreate, ExportData
from .storage import (
    get_clips, add_clip, delete_clip, clear_clips,
    get_match_start, set_match_start, clear_match_start
)
from .export import build_export

app = FastAPI(title="Ball We Cup Clipper API", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Clip endpoints
@app.get("/api/clips")
async def list_clips():
    """List all clips."""
    clips = get_clips()
    return [clip.model_dump() for clip in clips]


@app.post("/api/clips")
async def create_clip(clip_create: ClipCreate):
    """Create a new clip."""
    # Compute end_time from start_time + duration
    start_parts = clip_create.start_time.split(":")
    start_seconds = int(start_parts[0]) * 3600 + int(start_parts[1]) * 60 + int(start_parts[2])
    end_seconds = start_seconds + clip_create.duration
    end_h = end_seconds // 3600
    end_m = (end_seconds % 3600) // 60
    end_s = end_seconds % 60
    end_time = f"{end_h:02d}:{end_m:02d}:{end_s:02d}"

    clip = Clip(
        name=clip_create.name,
        start_time=clip_create.start_time,
        duration=clip_create.duration,
        end_time=end_time,
    )
    add_clip(clip)
    return clip.model_dump()


@app.delete("/api/clips/{clip_id}")
async def delete_clip_endpoint(clip_id: str):
    """Delete a clip by ID."""
    success = delete_clip(clip_id)
    if not success:
        raise HTTPException(status_code=404, detail="Clip not found")
    return {"success": True}


@app.delete("/api/clips")
async def clear_all_clips():
    """Clear all clips."""
    clear_clips()
    return {"success": True}


# Match start endpoints
@app.get("/api/match-start")
async def get_match_start_endpoint():
    """Get match start time."""
    match_start = get_match_start()
    if match_start:
        return match_start.model_dump()
    return {"match_start": None}


@app.post("/api/match-start")
async def set_match_start_endpoint(match_start_create: MatchStartCreate):
    """Set match start time."""
    match_start = MatchStart(match_start=match_start_create.match_start)
    set_match_start(match_start)
    return match_start.model_dump()


@app.delete("/api/match-start")
async def clear_match_start_endpoint():
    """Clear match start time."""
    clear_match_start()
    return {"success": True}


# Export endpoint
@app.get("/api/export")
async def export_clips(video_path: str = Query(..., description="Path to the video file")):
    """Export clips data for splitter."""
    try:
        export_data = build_export(video_path)
        return export_data.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/export/download")
async def download_export(video_path: str = Query(..., description="Path to the video file")):
    """Download export as JSON file."""
    try:
        export_data = build_export(video_path)
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(export_data.model_dump_json(indent=2))
            temp_path = f.name
        return FileResponse(
            temp_path,
            media_type='application/json',
            filename='clips_export.json'
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Initialize data files on startup
@app.on_event("startup")
async def startup():
    from .storage import _ensure_data_dir
    _ensure_data_dir()