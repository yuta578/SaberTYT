/* ==========================================================================
   SIMULADOR DE CUESTIONARIOS SABER TyT - MAIN JS
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initRoleSwitcher();
  initModals();
  initDragAndDrop();
  initTablesSearch();
});

// Role Switcher (Estudiante / Profesor)
function initRoleSwitcher() {
  const btnEstudiante = document.getElementById('btnRoleEstudiante');
  const btnDocente = document.getElementById('btnRoleDocente');
  const navEstudiante = document.getElementById('navGroupEstudiante');
  const navDocente = document.getElementById('navGroupDocente');

  if (!btnEstudiante || !btnDocente) return;

  const currentPath = window.location.pathname;

  // Determine initial role
  let initialRole = 'estudiante';
  if (currentPath.startsWith('/docente/')) {
    initialRole = 'docente';
    localStorage.setItem('tyt_role', 'docente');
  } else if (currentPath.startsWith('/estudiante/')) {
    initialRole = 'estudiante';
    localStorage.setItem('tyt_role', 'estudiante');
  } else {
    initialRole = localStorage.getItem('tyt_role') || 'estudiante';
  }

  applyRole(initialRole, false);

  btnEstudiante.addEventListener('click', () => {
    applyRole('estudiante', true);
  });

  btnDocente.addEventListener('click', () => {
    applyRole('docente', true);
  });

  function applyRole(role, shouldNavigate) {
    localStorage.setItem('tyt_role', role);

    if (role === 'docente') {
      btnDocente.classList.add('active');
      btnEstudiante.classList.remove('active');
      if (navDocente) navDocente.style.display = 'flex';
      if (navEstudiante) navEstudiante.style.display = 'none';

      if (shouldNavigate && !window.location.pathname.startsWith('/docente/')) {
        window.location.href = '/docente/';
      }
    } else {
      btnEstudiante.classList.add('active');
      btnDocente.classList.remove('active');
      if (navEstudiante) navEstudiante.style.display = 'flex';
      if (navDocente) navDocente.style.display = 'none';

      if (shouldNavigate && !window.location.pathname.startsWith('/estudiante/')) {
        window.location.href = '/estudiante/';
      }
    }
  }
}

// Theme Management (Light / Dark)
function initThemeToggle() {
  const savedTheme = localStorage.getItem('tyt_theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);

  const toggleBtns = document.querySelectorAll('.theme-toggle-btn');
  toggleBtns.forEach(btn => {
    updateThemeIcon(btn, savedTheme);
    btn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('tyt_theme', next);
      updateThemeIcon(btn, next);
    });
  });
}

function updateThemeIcon(btn, theme) {
  if (!btn) return;
  if (theme === 'dark') {
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5"></circle>
        <line x1="12" y1="1" x2="12" y2="3"></line>
        <line x1="12" y1="21" x2="12" y2="23"></line>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
        <line x1="1" y1="12" x2="3" y2="12"></line>
        <line x1="21" y1="12" x2="23" y2="12"></line>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
      </svg>
    `;
    btn.setAttribute('title', 'Cambiar a Modo Claro');
  } else {
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
      </svg>
    `;
    btn.setAttribute('title', 'Cambiar a Modo Oscuro');
  }
}

// Modal Helpers
function initModals() {
  // Open modal buttons
  document.querySelectorAll('[data-modal-target]').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = trigger.getAttribute('data-modal-target');
      openModal(targetId);
    });
  });

  // Close modal buttons
  document.querySelectorAll('[data-modal-close]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const modal = btn.closest('.modal-backdrop');
      if (modal) closeModal(modal.id);
    });
  });

  // Click outside to close
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal(modal.id);
      }
    });
  });
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// Drag & Drop Upload Simulator
function initDragAndDrop() {
  const dropzone = document.getElementById('excelDropzone');
  const fileInput = document.getElementById('excelFileInput');
  const fileInfo = document.getElementById('uploadFileInfo');
  const fileName = document.getElementById('uploadFileName');

  if (!dropzone || !fileInput) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'var(--primary-600)';
      dropzone.style.backgroundColor = 'var(--primary-50)';
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'var(--border-medium)';
      dropzone.style.backgroundColor = 'var(--bg-subtle)';
    });
  });

  dropzone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      handleFileSelected(fileInput.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleFileSelected(fileInput.files[0]);
    }
  });

  function handleFileSelected(file) {
    if (fileName && fileInfo) {
      fileName.textContent = file.name + ' (' + (file.size / 1024).toFixed(1) + ' KB)';
      fileInfo.style.display = 'block';
    }
  }
}

// Table Search Filtering
function initTablesSearch() {
  const searchInput = document.getElementById('tableSearchInput');
  const table = document.getElementById('filterableTable');
  if (!searchInput || !table) return;

  searchInput.addEventListener('input', () => {
    const term = searchInput.value.toLowerCase();
    const cards = table.querySelectorAll('.card');

    cards.forEach(card => {
      const text = card.textContent.toLowerCase();
      card.style.display = text.includes(term) ? '' : 'none';
    });
  });
}

// Toast notification helper
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px;';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `badge badge-${type}`;
  toast.style.cssText = 'padding:10px 16px;font-size:0.85rem;box-shadow:var(--shadow-md);border-radius:8px;transition:opacity 200ms ease;';
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 250);
  }, 3000);
}
