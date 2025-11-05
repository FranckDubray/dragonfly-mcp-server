// Shared, accessible modal component with animation and focus-trap
// Usage:
//   import { createModal } from './modal.js';
//   const modal = createModal({ title: 'Title', width: '720px' });
//   modal.body.append(...);
//   modal.footer.append(btnClose, btnOk);
//   modal.open();

export function createModal({ title='Modal', width='720px', closeOnEsc=true, closeOnBackdrop=true } = {}) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');

  const panel = document.createElement('div');
  panel.className = 'modal';
  panel.style.width = width;

  // Header
  const header = document.createElement('div');
  header.className = 'modal-header';
  const titleEl = document.createElement('h3');
  titleEl.className = 'modal-title';
  titleEl.textContent = title;
  // Link aria-labelledby to title
  const titleId = 'modal_title_' + Math.random().toString(36).slice(2);
  titleEl.id = titleId;
  overlay.setAttribute('aria-labelledby', titleId);

  const btnClose = document.createElement('button');
  btnClose.className = 'btn modal-close icon';
  btnClose.setAttribute('aria-label', 'Fermer');
  btnClose.type = 'button';
  btnClose.textContent = '✕';
  header.append(titleEl, btnClose);

  // Body + Footer
  const body = document.createElement('div');
  body.className = 'modal-body';
  const footer = document.createElement('div');
  footer.className = 'modal-footer';

  panel.append(header, body, footer);
  overlay.append(panel);

  function open() {
    document.body.appendChild(overlay);
    document.body.classList.add('modal-open');
    // sequential animations for smoother entrance
    requestAnimationFrame(() => {
      overlay.classList.add('show');
      requestAnimationFrame(() => panel.classList.add('open'));
    });
    // Ensure focus
    panel.setAttribute('tabindex', '-1');
    panel.focus();
  }
  function close() {
    panel.classList.remove('open');
    overlay.classList.remove('show');
    setTimeout(() => {
      try { overlay.remove(); } catch {}
      document.body.classList.remove('modal-open');
    }, 180);
  }

  // Close behaviors
  btnClose.addEventListener('click', close);
  if (closeOnBackdrop) {
    overlay.addEventListener('mousedown', (e) => { if (e.target === overlay) close(); });
  }
  if (closeOnEsc) {
    overlay.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });
  }
  // Focus trap
  overlay.addEventListener('keydown', (e) => {
    if (e.key !== 'Tab') return;
    const focusables = overlay.querySelectorAll(
      'a,button,textarea,input,select,[tabindex]:not([tabindex="-1"])'
    );
    if (!focusables.length) return;
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault(); last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault(); first.focus();
    }
  });

  return {
    overlay, panel, header, titleEl, body, footer,
    open, close,
    setTitle: (t) => { titleEl.textContent = t; },
    setWidth: (w) => { panel.style.width = w; },
  };
}
