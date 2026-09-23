"""Data models for Ball We Cup Clipper."""

from datetime import datetime
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def utc_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str


class Team(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    players: list[Player] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class TeamCreate(BaseModel):
    name: str


class TeamUpdate(BaseModel):
    name: str


class PlayerCreate(BaseModel):
    name: str


class PlayerUpdate(BaseModel):
    name: str


class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: Literal["goal", "manual"]
    title: str
    event_time: str
    clip_start: str
    duration: int
    event_at: Optional[str] = None
    clip_start_at: Optional[str] = None
    team_id: Optional[str] = None
    scorer_id: Optional[str] = None
    assist_id: Optional[str] = None
    created_at: str = Field(default_factory=utc_now)


class EventCreate(BaseModel):
    type: Literal["goal", "manual"]
    title: str = ""
    event_time: str
    event_at: Optional[str] = None
    duration: int = Field(ge=1, le=3600)
    team_id: Optional[str] = None
    scorer_id: Optional[str] = None
    assist_id: Optional[str] = None

    @field_validator("event_time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        try:
            hours, minutes, seconds = (int(part) for part in value.split(":"))
        except ValueError as exc:
            raise ValueError("event_time must use HH:MM:SS") from exc
        if not (0 <= hours < 24 and 0 <= minutes < 60 and 0 <= seconds < 60):
            raise ValueError("event_time must use HH:MM:SS")
        return value

    @field_validator("event_at")
    @classmethod
    def validate_timestamp(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("event_at must be an ISO-8601 timestamp") from exc
        return value


class RecordingStart(BaseModel):
    recording_started_at: str

    @field_validator("recording_started_at")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("recording_started_at must be an ISO-8601 timestamp") from exc
        return value


class Clip(BaseModel):
    """Legacy clip schema retained so old data can be migrated safely."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    start_time: str
    duration: int
    end_time: str
    created_at: str = Field(default_factory=utc_now)
