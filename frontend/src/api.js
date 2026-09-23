const BASE = '/api';

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || 'Something went wrong');
  return data;
}

const json = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

export const getDashboard = () => request('/dashboard');
export const setRecordingStart = (recording_started_at) => request('/recording-start', json('POST', { recording_started_at }));
export const clearRecordingStart = () => request('/recording-start', { method: 'DELETE' });
export const createTeam = (name) => request('/teams', json('POST', { name }));
export const updateTeam = (id, name) => request(`/teams/${id}`, json('PATCH', { name }));
export const deleteTeam = (id) => request(`/teams/${id}`, { method: 'DELETE' });
export const createPlayer = (teamId, name) => request(`/teams/${teamId}/players`, json('POST', { name }));
export const updatePlayer = (teamId, playerId, name) => request(`/teams/${teamId}/players/${playerId}`, json('PATCH', { name }));
export const deletePlayer = (teamId, playerId) => request(`/teams/${teamId}/players/${playerId}`, { method: 'DELETE' });
export const createEvent = (event) => request('/events', json('POST', event));
export const deleteEvent = (id) => request(`/events/${id}`, { method: 'DELETE' });
export const exportEvents = () => request('/export');
