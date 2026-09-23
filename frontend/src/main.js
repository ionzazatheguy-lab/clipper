import { clearRecordingStart, createEvent, createPlayer, createTeam, deleteEvent, deletePlayer, deleteTeam, exportEvents, getDashboard, setRecordingStart, updatePlayer, updateTeam } from './api.js';

const root = document.querySelector('#root');
let state = { teams: [], events: [] };
let selectedTeamId = '';
let duration = 120;
let usingCustomDuration = false;

const escape = (value = '') => String(value).replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[char]);
const clockTime = (time) => {
  return [time.getHours(), time.getMinutes(), time.getSeconds()].map(value => String(value).padStart(2, '0')).join(':');
};
const now = () => clockTime(new Date());
const timestamp = () => new Date().toISOString();
const displayTimestamp = (value) => value ? new Date(value).toLocaleString([], { dateStyle: 'medium', timeStyle: 'medium' }) : '';
const datetimeLocalValue = (value) => {
  const date = value ? new Date(value) : new Date();
  const part = number => String(number).padStart(2, '0');
  return `${date.getFullYear()}-${part(date.getMonth() + 1)}-${part(date.getDate())}T${part(date.getHours())}:${part(date.getMinutes())}:${part(date.getSeconds())}`;
};
const selectedTeam = () => state.teams.find(team => team.id === selectedTeamId);
const playerName = (id) => state.teams.flatMap(team => team.players).find(player => player.id === id)?.name || 'Unknown player';

function toast(message, error = false) {
  document.querySelector('.toast')?.remove();
  const element = document.createElement('div');
  element.className = `toast${error ? ' error' : ''}`;
  element.textContent = message;
  document.body.append(element);
  setTimeout(() => element.remove(), 3200);
}

async function refresh() {
  state = await getDashboard();
  if (!state.teams.some(team => team.id === selectedTeamId)) selectedTeamId = state.teams[0]?.id || '';
  render();
}

function teamOptions(placeholder = 'Choose team') {
  return `<option value="">${placeholder}</option>${state.teams.map(team => `<option value="${team.id}" ${team.id === selectedTeamId ? 'selected' : ''}>${escape(team.name)}</option>`).join('')}`;
}

function playerOptions(team, placeholder, skip = '') {
  if (!team) return `<option value="">Choose a team first</option>`;
  return `<option value="">${placeholder}</option>${team.players.filter(player => player.id !== skip).map(player => `<option value="${player.id}">${escape(player.name)}</option>`).join('')}`;
}

function scoreboard() {
  if (!state.teams.length) return `<div class="score-card"><p class="team-name">No teams yet</p><div class="score">—</div><p class="score-meta">Add a roster below</p></div>`;
  return state.teams.map(team => `<article class="score-card"><p class="team-name">${escape(team.name)}</p><div class="score">${team.score}</div><p class="score-meta">${team.players.length} PLAYER${team.players.length === 1 ? '' : 'S'}</p></article>`).join('');
}

function eventFeed() {
  if (!state.events.length) return '<li class="empty">No events logged. The next goal starts the match log.</li>';
  const teams = new Map(state.teams.map(team => [team.id, team]));
  return state.events.map(event => {
    const team = teams.get(event.team_id);
    const isGoal = event.type === 'goal';
    const description = isGoal
      ? `${escape(team?.name || 'Unknown team')} · ${escape(playerName(event.scorer_id))}${event.assist_id ? ` · Assist: ${escape(playerName(event.assist_id))}` : ''}`
      : `Clip ${event.clip_start} → ${event.event_time} · ${event.duration}s`;
    return `<li><span class="feed-time">${event.event_time}</span><div><div class="feed-title">${isGoal ? '⚽ ' : '◉ '}${escape(event.title)}</div><div class="feed-sub">${description}</div></div><button class="danger" data-delete-event="${event.id}" aria-label="Delete ${escape(event.title)}">×</button></li>`;
  }).join('');
}

function teamManager() {
  const teams = state.teams.map((team, index) => `<details class="team" ${index === 0 ? 'open' : ''}><summary><strong>${escape(team.name)}</strong><span class="stat">${team.score} GOALS · ${team.players.length} PLAYERS</span></summary><div class="team-body">${team.players.length ? team.players.map(player => `<div class="player"><span>${escape(player.name)}</span><span class="stat">G ${player.goals} · A ${player.assists} <button class="ghost" data-rename-player="${team.id}:${player.id}" aria-label="Rename ${escape(player.name)}">Edit</button> <button class="danger" data-delete-player="${team.id}:${player.id}" aria-label="Remove ${escape(player.name)}">×</button></span></div>`).join('') : '<p class="small">No players yet—add the squad before logging a goal.</p>'}<form class="inline" data-player-form="${team.id}"><input required maxlength="60" placeholder="Add player" aria-label="Add a player to ${escape(team.name)}"><button class="ghost">Add</button></form><div class="inline"><button class="ghost" data-rename-team="${team.id}">Rename team</button><button class="danger" data-delete-team="${team.id}">Remove team</button></div></div></details>`).join('');
  return `${teams}<form class="add-team" id="team-form"><input required maxlength="60" placeholder="New team name" aria-label="New team name"><button class="ghost">Add team</button></form>`;
}

function durationPicker() {
  return `<div class="duration"><button type="button" data-duration="120" class="${usingCustomDuration ? '' : 'active'}">Last 120 seconds</button><label class="duration-custom ${usingCustomDuration ? 'active' : ''}" for="duration-custom"><span>Custom</span><input id="duration-custom" type="number" min="1" max="3600" step="1" inputmode="numeric" placeholder="Seconds" value="${usingCustomDuration ? duration : ''}" aria-label="Custom clip length in seconds"><em>s</em></label></div><p class="duration-note">Choose 1–3,600 seconds. The clip ends at the moment you log it.</p>`;
}

function render() {
  const team = selectedTeam();
  const recording = state.recording_started_at;
  root.innerHTML = `<main class="app"><header class="masthead"><div><p class="eyebrow">Live event logger</p><h1>Ball We Cup<br>Clipper</h1></div><div class="live"><i></i> Current time · ${now()}</div></header><section class="recording-control ${recording ? 'recording-control--active' : ''}"><div><p class="eyebrow">Video reference</p><strong>${recording ? `Recording began ${escape(displayTimestamp(recording))}` : 'Start the video, then mark its start here'}</strong><span>${recording ? 'All new clips export with an exact video offset.' : 'Clips remain locked until this timestamp is saved.'}</span></div><div class="recording-actions"><button id="recording-start" class="${recording ? 'ghost' : 'primary'}">${recording ? 'Reset recording start' : 'Recording started now'}</button><form id="recording-manual-form" class="recording-manual"><label for="recording-manual-time">Or set date & time</label><div><input id="recording-manual-time" type="datetime-local" step="1" required value="${datetimeLocalValue(recording)}"><button class="ghost">Set time</button></div></form></div></section><section class="scoreboard" aria-label="Scoreboard">${scoreboard()}</section><div class="layout"><div class="stack"><section class="panel"><div class="panel-head"><h2>Log a goal</h2><span>Captures the seconds before now</span></div><form id="goal-form" class="goal-form"><div class="field full"><label for="goal-team">Scoring team</label><select id="goal-team" required ${state.teams.length && recording ? '' : 'disabled'}>${teamOptions()}</select></div><div class="field"><label for="scorer">Goal scorer</label><select id="scorer" required ${team?.players.length && recording ? '' : 'disabled'}>${playerOptions(team, 'Choose scorer')}</select></div><div class="field"><label for="assist">Assist</label><select id="assist" ${team?.players.length && recording ? '' : 'disabled'}>${playerOptions(team, 'Unassisted')}</select></div><div class="field full"><label>Clip length</label>${durationPicker()}</div><div class="field full"><button class="primary" ${team?.players.length && recording ? '' : 'disabled'}>Log goal at current time</button></div></form></section><section class="panel"><div class="panel-head"><h2>Manual clip</h2><span>No score change</span></div><form id="manual-form" class="manual"><input required maxlength="100" placeholder="e.g. Great save, foul, highlight" aria-label="Manual clip name" ${recording ? '' : 'disabled'}><button class="primary" ${recording ? '' : 'disabled'}>Mark now</button></form></section><section class="panel"><div class="panel-head"><h2>Match log</h2><span>${state.events.length} event${state.events.length === 1 ? '' : 's'}</span></div><ul class="feed">${eventFeed()}</ul></section></div><aside class="stack"><section class="panel"><div class="panel-head"><h2>Team rosters</h2><span>Goals / assists</span></div><div class="teams">${teamManager()}</div></section></aside></div><div class="export"><button id="export" ${recording ? '' : 'disabled'}>Download event export</button></div></main>`;
  bind();
}

function bind() {
  document.querySelector('#goal-team')?.addEventListener('change', event => { selectedTeamId = event.target.value; render(); });
  document.querySelector('#scorer')?.addEventListener('change', event => {
    const assist = document.querySelector('#assist');
    if (assist) assist.innerHTML = playerOptions(selectedTeam(), 'Unassisted', event.target.value);
  });
  document.querySelectorAll('[data-duration]').forEach(button => button.addEventListener('click', () => { duration = Number(button.dataset.duration); usingCustomDuration = false; render(); }));
  document.querySelector('#duration-custom')?.addEventListener('input', event => {
    usingCustomDuration = event.target.value !== '';
    duration = usingCustomDuration ? Number(event.target.value) : 120;
    document.querySelector('[data-duration="120"]')?.classList.toggle('active', !usingCustomDuration);
    event.target.closest('.duration-custom')?.classList.toggle('active', usingCustomDuration);
  });
  document.querySelector('#recording-start')?.addEventListener('click', () => recordingStart());
  document.querySelector('#recording-manual-form')?.addEventListener('submit', setManualRecordingStart);
  document.querySelector('#goal-form')?.addEventListener('submit', submitGoal);
  document.querySelector('#manual-form')?.addEventListener('submit', submitManual);
  document.querySelector('#team-form')?.addEventListener('submit', async event => { event.preventDefault(); await action(() => createTeam(event.target.elements[0].value), 'Team added'); });
  document.querySelectorAll('[data-player-form]').forEach(form => form.addEventListener('submit', async event => { event.preventDefault(); await action(() => createPlayer(form.dataset.playerForm, form.elements[0].value), 'Player added'); }));
  document.querySelectorAll('[data-delete-event]').forEach(button => button.addEventListener('click', () => remove(() => deleteEvent(button.dataset.deleteEvent), 'Event deleted')));
  document.querySelectorAll('[data-delete-player]').forEach(button => button.addEventListener('click', () => { const [teamId, playerId] = button.dataset.deletePlayer.split(':'); remove(() => deletePlayer(teamId, playerId), 'Player removed'); }));
  document.querySelectorAll('[data-rename-team]').forEach(button => button.addEventListener('click', () => rename('Rename team', state.teams.find(team => team.id === button.dataset.renameTeam)?.name, name => updateTeam(button.dataset.renameTeam, name), 'Team renamed')));
  document.querySelectorAll('[data-rename-player]').forEach(button => button.addEventListener('click', () => { const [teamId, playerId] = button.dataset.renamePlayer.split(':'); rename('Rename player', playerName(playerId), name => updatePlayer(teamId, playerId, name), 'Player renamed'); }));
  document.querySelectorAll('[data-delete-team]').forEach(button => button.addEventListener('click', () => remove(() => deleteTeam(button.dataset.deleteTeam), 'Team removed')));
  document.querySelector('#export')?.addEventListener('click', downloadExport);
}

async function action(work, success) { try { await work(); await refresh(); toast(success); } catch (error) { toast(error.message, true); } }
function remove(work, success) { if (confirm('This cannot be undone. Continue?')) action(work, success); }
function rename(label, currentName, work, success) { const name = prompt(label, currentName); if (name?.trim()) action(() => work(name.trim()), success); }

async function submitGoal(event) {
  event.preventDefault();
  if (!validDuration()) return;
  const form = event.currentTarget;
  const occurredAt = new Date();
  await action(() => createEvent({ type: 'goal', event_time: clockTime(occurredAt), event_at: occurredAt.toISOString(), duration, team_id: selectedTeamId, scorer_id: form.querySelector('#scorer').value, assist_id: form.querySelector('#assist').value || null }), 'Goal logged and clip marked');
}

async function submitManual(event) {
  event.preventDefault();
  if (!validDuration()) return;
  const input = event.currentTarget.querySelector('input');
  const occurredAt = new Date();
  await action(() => createEvent({ type: 'manual', title: input.value, event_time: clockTime(occurredAt), event_at: occurredAt.toISOString(), duration }), 'Manual clip marked');
}

function validDuration() {
  if (Number.isInteger(duration) && duration >= 1 && duration <= 3600) return true;
  toast('Choose a clip length from 1 to 3,600 seconds', true);
  return false;
}

async function recordingStart() {
  if (state.recording_started_at) {
    if (!confirm('Clear the saved recording start? Clip logging will stay locked until you mark the next video start.')) return;
    await action(clearRecordingStart, 'Recording start reset');
    return;
  }
  await action(() => setRecordingStart(timestamp()), 'Recording start saved');
}

async function setManualRecordingStart(event) {
  event.preventDefault();
  const value = event.currentTarget.querySelector('#recording-manual-time').value;
  const selectedTime = new Date(value);
  if (Number.isNaN(selectedTime.getTime())) {
    toast('Choose a valid recording start date and time', true);
    return;
  }
  if (state.recording_started_at && !confirm('Replace the saved recording start with this date and time?')) return;
  await action(() => setRecordingStart(selectedTime.toISOString()), 'Recording start time saved');
}

async function downloadExport() {
  try {
    const data = await exportEvents();
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    const link = Object.assign(document.createElement('a'), { href: url, download: 'ball-we-cup-events.json' });
    link.click(); URL.revokeObjectURL(url); toast('Event export downloaded');
  } catch (error) { toast(error.message, true); }
}

refresh().catch(error => { root.innerHTML = `<main class="app"><section class="panel empty">Could not load the tracker: ${escape(error.message)}. Start the backend on port 8000 and refresh.</section></main>`; });
