// === api.js — Backend API Client ===

const BASE = '/api';

export async function listClips() {
  const res = await fetch(`${BASE}/clips`);
  return res.json();
}

export async function createClip({ name, start_time, duration }) {
  const res = await fetch(`${BASE}/clips`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, start_time, duration })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to create clip');
  return { clip: data };
}

export async function deleteClip(clipId) {
  const res = await fetch(`${BASE}/clips/${clipId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete clip');
}

export async function clearClips() {
  const res = await fetch(`${BASE}/clips`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to clear clips');
}

export async function getClips() {
  const res = await fetch(`${BASE}/clips`);
  return res.json();
}

export async function setMatchStart(time) {
  const res = await fetch(`${BASE}/match-start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ match_start: time })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to set match start');
  return data;
}

export async function getMatchStart() {
  const res = await fetch(`${BASE}/match-start`);
  return res.json();
}

export async function clearMatchStart() {
  const res = await fetch(`${BASE}/match-start`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to clear match start');
}

export async function exportClips(videoPath) {
  const res = await fetch(`${BASE}/export?video_path=${encodeURIComponent(videoPath)}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Export failed');
  }
  // Return the JSON body and a download helper
  const data = await res.json();
  return {
    data,
    download: () => {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'clips_export.json';
      a.click();
      URL.revokeObjectURL(url);
    }
  };
}

// Export helpers used by main.js
export { exportClips as downloadExport };