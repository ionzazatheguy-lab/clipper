// === components/Header.js — Header with Match Timer ===

export class Header {
  constructor({ target }) {
    this.target = target;
    this.render();
    this.bindEvents();
  }

  render() {
    const header = document.createElement('header');
    header.className = 'header';
    header.innerHTML = `
      <div class="header__inner">
        <h1 class="header__title">Ball We Cup Clipper</h1>
        <div class="header__status">
          <span class="status-dot" aria-hidden="true"></span>
          <span id="header-match-start" class="fg-muted" style="font-size:12px;"></span>
        </div>
      </div>
    `;
    this.target.insertBefore(header, this.target.firstChild);
    this.updateMatchStart();
  }

  bindEvents() {
    // Listen for match start changes via emit
    on('matchstart:update', (time) => this.updateMatchStart(time));
  }

  updateMatchStart(time) {
    const el = document.getElementById('header-match-start');
    if (time) {
      el.textContent = `Match start: ${time}`;
    } else {
      el.textContent = 'Match start: not set';
    }
  }
}