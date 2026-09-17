"""Pydantic models for Ball We Cup Clipper."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class Clip(BaseModel):
    """Clip metadata model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    start_time: str  # "HH:MM:SS" relative to match start
    duration: int  # seconds
    end_time: str  # computed: start + duration
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ClipCreate(BaseModel):
    """Request model for creating a clip."""
    name: str
    start_time: str
    duration: int


class MatchStart(BaseModel):
    """Match start time model."""
    match_start: str  # "HH:MM:SS"


class MatchStartCreate(BaseModel):
    """Request model for setting match start time."""
    match_start: str


class ExportData(BaseModel):
    """Export format for clip splitter."""
    match_start: str
    video_path: str
    clips: list[dict]