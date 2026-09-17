// === components/ClipListRenderer.js — Broadcast-Style Clip List ===

import { deleteClip } from '../api.js';
import { formatTime, parseTime, formatDuration } from '../utils/time.js';
import { showToast } from '../utils/toast.js';

export class ClipListRenderer {
  static render(clips, target) {
    // Clear existing
    const existing = target.querySelector('.__clip-list__');
    if (existing) existing.remove();

    if (clips.length === 0) {
      const empty = document.createElement('div');
      empty.className = '__clip-list__ empty-state';
      empty.innerHTML = `
        <div class="empty-state__icon">⏱️</div>
        <h3 class="empty-state__title">No clips marked</h3>
        <p class="empty-state__desc">Mark clips using the form above</p>
      `;
      target.appendChild(empty);
      return;
    }

    const list = document.createElement('div');
    list.className = '__clip-list__';
    list.style.cssText = `
      margin-top: var(--space-4);
      max-height: 400px;
      overflow-y: auto;
      scrollbar-width: thin;
      scrollbar-color: var(--accent-amber) var(--bg-panel);
    `;

    // Webkit scrollbar
    list.style.setProperty('--webkit-scrollbar', '4px');
    list.style.setProperty('--webkit-scrollbar-track', 'var(--bg-panel)');
    list.style.setProperty('--webkit-scrollbar-thumb', 'var(--accent-amber)');
    list.style.setProperty('--webkit-scrollbar-thumb-hover', 'var(--accent-amber-dim)');

    let html = '';
    clips.forEach((clip, idx) => {
      const start = clip.start_time || '00:00:00';
      const duration = clip.duration || 600;
      const end = formatTime(parseTime(start) + duration);
      const isSelected = clip.id === (target.__selectedClipId || null);

      html += `
        <div class="clip-row" style="grid-template-columns: auto 1fr auto; gap:var(--space-3) var(--space-4);" 
             data-clip-id="${clip.id}" 
             role="button"
             tabindex="0"
             aria-label="Clip ${clip.name}, start ${start}, duration ${formatDuration(duration)}">
          <span class="clip-row__number">${idx + 1}</span>
          <div class="clip-row__info">
            <div class="clip-row__name" style="font:600 var(--space-4)/1 var(--font-display);">${clip.name || 'Unnamed'}</div>
            <div class="clip-row__time" style="font:var(--space-3)/1 var(--font-mono); color:var(--fg-muted);">${start} → ${end}</div>
          </div>
          <div class="clip-row__actions">
            <button class="clip-row__action-btn" aria-label="Delete clip" style="color:var(--signal-red);">×</button>
            <button class="clip-row__action-btn" aria-label="Copy start time">⏱</button>
          </div>
        </div>
      `;
    });

    list.innerHTML = html;
    target.appendChild(list);

    // Add event listeners after render
    this.bindRowEvents(list, clips);

    // Focus first row if none selected
    if (!target.__selectedClipId) {
      const firstRow = list.firstElementChild;
      if (firstRow) firstRow.focus();
    }
  }

  static bindRowEvents(list, clips) {
    const rows = list.querySelectorAll('.clip-row');

    rows.forEach((row, idx) => {
      const clipId = row.dataset.clipId;
      const deleteBtn = row.querySelector('.clip-row__action-btn:first-child');
      const copyBtn = row.querySelector('.clip-row__action-btn:last-child');

      // Click/tap on row
      row.addEventListener('click', (e) => {
        // Don't select if clicking buttons
        if (e.target === deleteBtn || e.target === copyBtn) return;
        
        // Deselect previously selected
        const prev = list.querySelector('.clip-row.selected');
        if (prev) prev.classList.remove('selected');
        
        // Select this one
        row.classList.add('selected');
        window.__selectedClipId = clipId;
      });

      // Delete button
      if (deleteBtn) {
        deleteBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          if (confirm('Delete this clip?')) {
            // Call backend
            deleteClip(clipId).then(() => {
              // Remove from local clips array
              const index = clips.findIndex(c => c.id === clipId);
              if (index > -1) clips.splice(index, 1);
              ClipListRenderer.render(clips, list.parentElement || document.body);
              showToast('Clip deleted');
            }).catch(() => {
              showToast('Failed to delete clip', 'error');
            });
          }
        });
      }

      // Copy start time button
      if (copyBtn) {
        copyBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          navigator.clipboard.writeText(clips[idx].start_time || '00:00:00');
          showToast('Start time copied');
        });
      }

      // Keyboard navigation
      row.setAttribute('role', 'button');
      row.setAttribute('tabindex', '0');
      row.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          row.click();
        }
      });
    });
  }
}