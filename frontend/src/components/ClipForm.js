// === components/ClipForm.js — Mark a New Clip ===

export class ClipForm {
  constructor({ target, onSubmit, defaultStartTime }) {
    this.target = target;
    this.onSubmit = onSubmit;
    this.defaultStartTime = defaultStartTime || '00:00:00';
    this.render();
    this.bindEvents();
  }

  render() {
    this.target.innerHTML = `
      <div class="panel" style="padding:var(--space-5);">
        <div style="margin-bottom:var(--space-4);">
          <label style="font:600 var(--space-3)/1 var(--font-body); color:var(--fg-muted);">Clip name</label>
          <input
            type="text"
            id="clip-name"
            class="input"
            placeholder="e.g. Goal"
            aria-label="Clip name">
        </div>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:var(--space-3) var(--space-4); margin-bottom:var(--space-4);">
          <div>
            <label style="font:var(--space-3)/1 var(--font-body); color:var(--fg-muted);">Start time</label>
            <input
              type="text"
              id="clip-start"
              class="input"
              placeholder="HH:MM:SS"
              value="${this.defaultStartTime}"
              aria-label="Start time HH:MM:SS">
          </div>
          <div>
            <label style="font:var(--space-3)/1 var(--font-body); color:var(--fg-muted);">Duration</label>
            <input
              type="range"
              id="clip-duration"
              min="60"
              max="1200"
              step="60"
              value="600"
              aria-label="Duration in seconds">
            <span id="duration-value" style="font:var(--space-3)/1 var(--font-mono); color:var(--accent-amber);">10:00</span>
          </div>
        </div>
        <button class="btn btn--primary" id="mark-clip" style="width:100%; margin-top:var(--space-4);">
          Mark Clip
        </button>
      </div>
    `;
    this.bindEvents();
  }

  bindEvents() {
    const nameInput = document.getElementById('clip-name');
    const startInput = document.getElementById('clip-start');
    const durationInput = document.getElementById('clip-duration');
    const durationValue = document.getElementById('duration-value');
    const markBtn = document.getElementById('mark-clip');

    durationInput.addEventListener('input', (e) => {
      const minutes = Math.floor(e.target.value / 60);
      const seconds = e.target.value % 60;
      const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;
      durationValue.textContent = display;
    });

    startInput.addEventListener('input', (e) => {
      const val = e.target.value.replace(/[^0-9:]/g, '').substring(0, 8);
      e.target.value = val.length > 0 ? val : '';
    });

    markBtn.addEventListener('click', async () => {
      const name = nameInput.value.trim() || `Clip ${clips.length + 1}`;
      let startTime = startInput.value.trim();

      if (!startTime) {
        startTime = this.defaultStartTime;
      }

      const duration = parseInt(durationInput.value, 10);

      await this.onSubmit({ name, start_time: startTime, duration });
      this.target.innerHTML = '';
    });
  }
}