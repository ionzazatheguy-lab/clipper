// === utils/toast.js — Toast Notification System ===

let toastTimer = null;

export function showToast(message, type = 'success') {
  const existing = document.querySelector('.__toast__');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = '__toast__';
  toast.style.cssText = `
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%) translateY(100px);
    background: #0e0e0e;
    border: 1px solid #ffb800;
    padding: 12px 24px;
    border-radius: 8px;
    color: #fafafa;
    font-size: 14px;
    z-index: 1000;
    min-width: 200px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    transition: transform 250ms ease-out;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);

  // Show
  requestAnimationFrame(() => {
    toast.style.transform = 'translateX(-50%) translateY(0)';
  });

  // Auto-dismiss
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.style.transform = 'translateX(-50%) translateY(100px)';
    setTimeout(() => toast.remove(), 250);
  }, 3000);
}