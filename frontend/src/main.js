// === main.js — App Entry Point (Vanilla JS, ES Modules) ===

import { listClips, createClip, deleteClip, clearClips, getClips, setMatchStart, getMatchStart, clearMatchStart } from './api.js';
import { on, off } from './utils/event.js';
import { formatTime, parseTime, formatDuration } from './utils/time.js';
import { showToast } from './utils/toast.js';
import { ClipListRenderer } from './components/ClipListRenderer.js';
import { ClipForm } from './components/ClipForm.js';
import { MatchStartPanel } from './components/MatchStartPanel.js';
import { ExportPanel } from './components/ExportPanel.js';
import { Header } from './components/Header.js';

// Initialize state
let clips = [];
let matchStart = null;
let ui = {
  selectedClipId: null,
  toastTimeout: null
};

// DOM elements
const html = document.documentElement;
const body = document.body;

// Bootstrap on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  // Initialize components
  const header = new Header({ target: document.body });
  const matchStartPanel = new MatchStartPanel({
    target: document.body,
    onSet: async (time) => await setMatchStart(time),
    onClear: async () => await clearMatchStart()
  });
  const clipForm = new ClipForm({
    target: document.body,
    defaultStartTime: matchStart || '00:00:00',
    onSubmit: async (data) => {
      const result = await createClip(data);
      if (result.clip) {
        clips.push(result.clip);
        ClipListRenderer.render(clips, body);
        showToast('Clip marked');
      }
    }
  });
  const exportPanel = new ExportPanel({
    target: document.body,
    onExport: async (videoPath) => {
      const result = await exportClips(videoPath);
      if (result.download) {
        showToast('Export ready');
      }
    }
  });

  // Load initial state
  loadInitialState();

  // Keyboard shortcuts (touch-friendly: Space to mark clip)
  document.addEventListener('keydown', handleKeydown);
});

// --- State Loading ---
async function loadInitialState() {
  // Load match start
  const ms = await getMatchStart();
  matchStart = ms.match_start || null;
  if (matchStartPanel.update) matchStartPanel.update(matchStart);

  // Load clips
  const allClips = await getClips();
  clips = allClips.map(c => ({
    id: c.id,
    name: c.name,
    start_time: c.start_time,
    duration: c.duration,
    end_time: c.end_time
  }));
  
  if (ClipListRenderer.render) {
    ClipListRenderer.render(clips, body);
  }
}

// --- Keydown Handler ---
function handleKeydown(e) {
  // Space key: mark clip at current match time (mobile-friendly)
  if (e.code === 'Space' && !e.repeat) {
    e.preventDefault();
    if (matchStart && clips.length < 20) {
      const clip = {
        id: Date.now().toString(),
        name: `Clip ${clips.length + 1}`,
        start_time: matchStart,
        duration: 600, // 10 minutes default
        end_time: formatTime(
          parseTime(matchStart) + 600
        )
      };
      clips.unshift(clip);
      ClipListRenderer.render(clips, body);
      showToast('Clip marked');
    }
  }

  // Delete key: delete selected clip
  if (e.code === 'Delete' && ui.selectedClipId) {
    deleteClip(ui.selectedClipId);
    clips = clips.filter(c => c.id !== ui.selectedClipId);
    ClipListRenderer.render(clips, body);
    showToast('Clip deleted');
    ui.selectedClipId = null;
  }
}

// --- Export Function ---
async function exportClips(videoPath) {
  if (!matchStart) {
    showToast('Set match start time first', 'error');
    return;
  }
  if (clips.length === 0) {
    showToast('No clips to export', 'error');
    return;
  }

  try {
    const { downloadExport } = await import('./api.js');
    const result = await downloadExport(videoPath);
    showToast('Export downloaded');
  } catch (err) {
    showToast('Export failed', 'error');
    console.error(err);
  }
}

// Export for use by other modules
export { clips, matchStart, ui };