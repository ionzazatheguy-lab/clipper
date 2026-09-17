// === components/MatchStartPanel.js — Set Match Start Time ===

export class MatchStartPanel {
  constructor({ target, onSet, onClear }) {
    this.target = target;
    this.onSet = onSet;
    this.onClear = onClear;
    this.render();
    this.bindEvents();
  }

  render() {
    const panel = document.createElement('section');
    panel.className = 'main';
    panel.innerHTML = `
      <div class="export-panel" style="margin-top:0; padding:var(--space-4);">
        <div style="display:flex; gap:var(--space-3); align-items:center; margin-bottom:var(--space-4);">
          <label style="font:600 var(--space-3)/1 var(--font-body); color:var(--fg-muted);">Match start time</label>
          <button class="btn btn--secondary" id="clear-match-start">Clear</button>
        </div>
        <div style="display:flex; gap:var(--space-3); flex-wrap:wrap;">
          <input 
            type="text" 
            id="match-start-input" 
            class="input" 
            placeholder="HH:MM:SS"
            value="${this.getSavedMatchStart() || ''}"
            aria-label="Match start time HH:MM:SS">
          <button class="btn btn--primary" id="set-match-start">Set Now</button>
        </div>
      </div>
    `;
    this.target.innerHTML = '';
    this.target.appendChild(panel);
    this.bindInputEvents();
  }

  getSavedMatchStart() {
    // Try to read from localStorage or return null
    return localStorage.getItem('match_start') || '';
  }

  bindInputEvents() {
    const input = document.getElementById('match-start-input');
    const setBtn = document.getElementById('set-match-start');
    const clearBtn = document.getElementById('clear-match-start');

    // Input validation
    input.addEventListener('input', (e) => {
      const val = e.target.value.replace(/[^0-9:]/g, '').substring(0, 8);
      e.target.value = val.length > 0 ? val : '';
    });

    setBtn.addEventListener('click', async () => {
      const val = input.value.trim();
      if (val && /^\d{2}:\d{2}:\d{2}$/.test(val)) {
        // If "Now", use current time
        const now = new Date();
        const h = String(now.getHours()).padStart(2, '0');
        const m = String(now.getMinutes()).padStart(2, '0');
        const s = String(now.getSeconds()).padStart(2, '0');
        const currentTime = `${h}:${m}:${s}`;
        
        await this.onSet(currentTime);
        showToast('Match start set');
        input.value = currentTime;
      } else {
        await this.onSet(val);
        showToast('Match start set');
      }
    });

    clearBtn.addEventListener('click', async () => {
      await this.onClear();
      showToast('Match start cleared');
      input.value = '';
    });
  }
}