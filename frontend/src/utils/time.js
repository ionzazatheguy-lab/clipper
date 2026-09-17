// === utils/time.js — Time Formatting & Math ===

/**
 * Parse "HH:MM:SS" → total seconds
 */
export function parseTime(timeStr) {
  const parts = timeStr.split(':').map(Number);
  return parts[0] * 3600 + parts[1] * 60 + parts[2];
}

/**
 * Total seconds → "HH:MM:SS"
 */
export function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

/**
 * Parse duration (seconds) → human readable "10:00" or "1:20:00"
 */
export function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}`;
  }
  return `${m}:${s.toString().padStart(2, '0')}`; // simplified for short durations
}

/**
 * Format start_time from clip for display
 */
export function formatStartTime(timeStr) {
  return timeStr; // already "HH:MM:SS"
}