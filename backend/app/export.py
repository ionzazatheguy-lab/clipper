"""Build an event-aware clipping export."""

from datetime import datetime

from .storage import get_events, get_recording_start, get_teams


def build_export() -> dict:
    recording_started_at = get_recording_start()
    if not recording_started_at:
        raise ValueError("Mark when recording started before exporting clips")
    recording_at = datetime.fromisoformat(recording_started_at.replace("Z", "+00:00"))
    teams = {team.id: team for team in get_teams()}
    players = {player.id: player.name for team in teams.values() for player in team.players}
    clips = []
    for event in get_events():
        team = teams.get(event.team_id or "")
        offset = None
        if event.clip_start_at:
            offset = max(0, int((datetime.fromisoformat(event.clip_start_at.replace("Z", "+00:00")) - recording_at).total_seconds()))
        clips.append({"id": event.id, "type": event.type, "title": event.title,
                      "event_time": event.event_time, "start_time": event.clip_start,
                      "event_at": event.event_at, "clip_start_at": event.clip_start_at,
                      "video_offset_seconds": offset, "duration": event.duration, "team": team.name if team else None,
                      "scorer": players.get(event.scorer_id or ""), "assist": players.get(event.assist_id or "")})
    return {"generated_at": datetime.utcnow().isoformat() + "Z", "recording_started_at": recording_started_at, "clips": clips}
