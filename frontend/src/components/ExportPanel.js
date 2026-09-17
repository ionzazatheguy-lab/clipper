// === components/ExportPanel.js — Export Clips as JSON ===

import { downloadExport } from '../api.js';

export class ExportPanel {
  constructor({ target, onExport }) {
    this.target = target;
    this.onExport = onExport;
    this.render();
    this.bindEvents();
  }

  render() {
    this.target.innerHTML = `
      <div class="export-panel">
        <label style="font:600 var(--space-3)/1 var(--font-body); color:var(--fg-muted);">Video file path</label>
        <input
          type="text"
          id="video-path"
          class="input"
          placeholder="/path/to/match.mp4"
          aria-label="Video file path">
        <div style="margin-top:var(--space-4);">
          <button class="btn btn--primary" id="export-btn" style="width:100%;">
            Generate JSON
          </button>
          <p style="font:var(--space-3)/1 var(--font-body); color:var(--fg-muted); margin-top:var(--space-3);">
            <span id="export-msg"></span>
          </p>
        </div>
      </div>
    `;
    this.bindEvents();
  }

  bindEvents() {
    const pathInput = document.getElementById('video-path');
    const exportBtn = document.getElementById('export-btn');
    const msgEl = document.getElementById('export-msg');

    pathInput.addEventListener('input', (e) => {
      e.target.value = e.target.value.replace(/[^\w\d\s\/\-\._]/g, '').trim();
    });

    exportBtn.addEventListener('click', async () => {
      const videoPath = pathInput.value.trim() || '/Users/avirana/Documents/Coding/clipper/match.mp4';

      if (!videoPath) {
        showToast('Enter a video path', 'error');
        return;
      }

      try {
        downloadExport(videoPath);
        msgEl.textContent = 'JSON downloaded → clips_export.json';
        msgEl.style.color = 'var(--signal-green)';
        setTimeout(() => msgEl.textContent = '', 3000);
      } catch (err) {
        msgEl.textContent = `Error: ${err.message}`;
        msgEl.style.color = 'var(--signal-red)';
        showToast('Export failed', 'error');
      }
    });
  }
}