"""FastAPI application for Ball We Cup Clipper."""

from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .export import build_export
from .models import Event, EventCreate, Player, PlayerCreate, PlayerUpdate, RecordingStart, Team, TeamCreate, TeamUpdate
from .storage import (clear_recording_start, get_events, get_recording_start, get_teams,
                      materialize_events, save_events, save_teams, set_recording_start, _ensure_data_dir)

app = FastAPI(title="Ball We Cup Clipper API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def _seconds(value: str) -> int:
    hours, minutes, seconds = (int(part) for part in value.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def _time(value: int) -> str:
    value %= 24 * 60 * 60
    return f"{value // 3600:02d}:{(value % 3600) // 60:02d}:{value % 60:02d}"


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _team_or_404(team_id: str, teams: list[Team]) -> Team:
    team = next((item for item in teams if item.id == team_id), None)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


def _player_or_404(player_id: str, team: Team) -> Player:
    player = next((item for item in team.players if item.id == player_id), None)
    if not player:
        raise HTTPException(status_code=422, detail="Selected player is not on this team")
    return player


def _dashboard() -> dict:
    teams = get_teams()
    events = sorted(get_events(), key=lambda item: (item.event_time, item.created_at), reverse=True)
    totals = {team.id: {"score": 0, "players": {player.id: {"goals": 0, "assists": 0} for player in team.players}} for team in teams}
    for event in events:
        if event.type != "goal" or event.team_id not in totals:
            continue
        totals[event.team_id]["score"] += 1
        if event.scorer_id in totals[event.team_id]["players"]:
            totals[event.team_id]["players"][event.scorer_id]["goals"] += 1
        if event.assist_id in totals[event.team_id]["players"]:
            totals[event.team_id]["players"][event.assist_id]["assists"] += 1
    return {"recording_started_at": get_recording_start(), "teams": [{**team.model_dump(), "score": totals[team.id]["score"], "players": [{**player.model_dump(), **totals[team.id]["players"][player.id]} for player in team.players]} for team in teams], "events": [event.model_dump() for event in events]}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/dashboard")
async def dashboard():
    return _dashboard()


@app.get("/api/recording-start")
async def recording_start():
    return {"recording_started_at": get_recording_start()}


@app.post("/api/recording-start")
async def set_recording(payload: RecordingStart):
    set_recording_start(payload.recording_started_at)
    return payload


@app.delete("/api/recording-start")
async def clear_recording():
    clear_recording_start()
    return {"success": True}


@app.post("/api/teams", status_code=201)
async def create_team(payload: TeamCreate):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Team name is required")
    teams = get_teams()
    if any(team.name.casefold() == name.casefold() for team in teams):
        raise HTTPException(status_code=409, detail="A team with that name already exists")
    team = Team(name=name)
    teams.append(team)
    save_teams(teams)
    return team


@app.patch("/api/teams/{team_id}")
async def update_team(team_id: str, payload: TeamUpdate):
    teams = get_teams()
    team = _team_or_404(team_id, teams)
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Team name is required")
    if any(item.id != team_id and item.name.casefold() == name.casefold() for item in teams):
        raise HTTPException(status_code=409, detail="A team with that name already exists")
    team.name = name
    save_teams(teams)
    return team


@app.delete("/api/teams/{team_id}")
async def delete_team(team_id: str):
    teams = get_teams()
    _team_or_404(team_id, teams)
    if any(event.team_id == team_id for event in get_events()):
        raise HTTPException(status_code=409, detail="Delete this team's events before removing it")
    save_teams([team for team in teams if team.id != team_id])
    return {"success": True}


@app.post("/api/teams/{team_id}/players", status_code=201)
async def create_player(team_id: str, payload: PlayerCreate):
    teams = get_teams()
    team = _team_or_404(team_id, teams)
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Player name is required")
    if any(player.name.casefold() == name.casefold() for player in team.players):
        raise HTTPException(status_code=409, detail="This player already exists on the team")
    player = Player(name=name)
    team.players.append(player)
    save_teams(teams)
    return player


@app.patch("/api/teams/{team_id}/players/{player_id}")
async def update_player(team_id: str, player_id: str, payload: PlayerUpdate):
    teams = get_teams()
    player = _player_or_404(player_id, _team_or_404(team_id, teams))
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Player name is required")
    player.name = name
    save_teams(teams)
    return player


@app.delete("/api/teams/{team_id}/players/{player_id}")
async def delete_player(team_id: str, player_id: str):
    teams = get_teams()
    team = _team_or_404(team_id, teams)
    _player_or_404(player_id, team)
    if any(event.scorer_id == player_id or event.assist_id == player_id for event in get_events()):
        raise HTTPException(status_code=409, detail="Delete this player's events before removing them")
    team.players = [player for player in team.players if player.id != player_id]
    save_teams(teams)
    return {"success": True}


@app.post("/api/events", status_code=201)
async def create_event(payload: EventCreate):
    recording_started_at = get_recording_start()
    if not recording_started_at:
        raise HTTPException(status_code=409, detail="Mark when recording started before logging clips")
    if not payload.event_at:
        raise HTTPException(status_code=422, detail="An exact event timestamp is required")
    teams = get_teams()
    title = payload.title.strip()
    if payload.type == "goal":
        if not payload.team_id or not payload.scorer_id:
            raise HTTPException(status_code=422, detail="A goal needs a team and scorer")
        team = _team_or_404(payload.team_id, teams)
        scorer = _player_or_404(payload.scorer_id, team)
        if payload.assist_id:
            _player_or_404(payload.assist_id, team)
            if payload.assist_id == scorer.id:
                raise HTTPException(status_code=422, detail="A scorer cannot assist their own goal")
        title = title or "Goal"
    elif not title:
        raise HTTPException(status_code=422, detail="A manual clip title is required")
    event_at = _timestamp(payload.event_at)
    recording_at = _timestamp(recording_started_at)
    clip_start_at = max(event_at - timedelta(seconds=payload.duration), recording_at)
    actual_duration = max(0, int((event_at - clip_start_at).total_seconds()))
    event = Event(type=payload.type, title=title, event_time=payload.event_time,
                  clip_start=_time(_seconds(payload.event_time) - actual_duration), duration=actual_duration,
                  event_at=_iso(event_at), clip_start_at=_iso(clip_start_at),
                  team_id=payload.team_id if payload.type == "goal" else None,
                  scorer_id=payload.scorer_id if payload.type == "goal" else None,
                  assist_id=payload.assist_id if payload.type == "goal" else None)
    events = materialize_events()
    events.append(event)
    save_events(events)
    return event


@app.delete("/api/events/{event_id}")
async def delete_event(event_id: str):
    events = materialize_events()
    if not any(event.id == event_id for event in events):
        raise HTTPException(status_code=404, detail="Event not found")
    save_events([event for event in events if event.id != event_id])
    return {"success": True}


@app.get("/api/export")
async def export_events():
    try:
        return build_export()
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.on_event("startup")
async def startup():
    _ensure_data_dir()
