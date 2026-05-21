/**
 * app.js — CETSure shared utilities
 * Navbar injection, loading spinner, toasts, helpers.
 */

/* ── Navbar ─────────────────────────────────────────────────
   Reads current page from window.location to mark active tab.
   Call loadNavbar() at bottom of every page's <body>.
──────────────────────────────────────────────────────────── */
function loadNavbar() {
  const path = window.location.pathname.split('/').pop() || 'home.html';

  const nav = document.createElement('nav');
  nav.className = 'navbar';
  nav.id = 'main-nav';
  nav.innerHTML = `
    <a href="home.html" class="nav-item ${path === 'home.html' ? 'active' : ''}" id="nav-home">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round"
          d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
      </svg>
      Home
    </a>
    <a href="predict.html" class="nav-item ${path === 'predict.html' ? 'active' : ''}" id="nav-predict">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round"
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
      </svg>
      Predict
    </a>
    <a href="search.html" class="nav-item ${path === 'search.html' ? 'active' : ''}" id="nav-search">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round"
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
      </svg>
      Search
    </a>
    <a href="shortlist.html" class="nav-item ${path === 'shortlist.html' ? 'active' : ''}" id="nav-shortlist">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round"
          d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
      </svg>
      Shortlist
    </a>
  `;
  document.body.appendChild(nav);
}

/* ── Loading Overlay ─────────────────────────────────────── */
let _loadingOverlay = null;

function _ensureOverlay() {
  if (!_loadingOverlay) {
    _loadingOverlay = document.createElement('div');
    _loadingOverlay.className = 'loading-overlay';
    _loadingOverlay.id = 'loading-overlay';
    _loadingOverlay.innerHTML = `
      <div class="spinner"></div>
      <p class="loading-text" id="loading-text">Finding your colleges…</p>
    `;
    document.body.appendChild(_loadingOverlay);
  }
  return _loadingOverlay;
}

function showLoading(message = 'Finding your colleges…') {
  const overlay = _ensureOverlay();
  document.getElementById('loading-text').textContent = message;
  overlay.classList.add('visible');
}

function hideLoading() {
  const overlay = _ensureOverlay();
  overlay.classList.remove('visible');
}

/* ── Toast ───────────────────────────────────────────────── */
let _toastContainer = null;

function _ensureToastContainer() {
  if (!_toastContainer) {
    _toastContainer = document.createElement('div');
    _toastContainer.className = 'toast-container';
    _toastContainer.id = 'toast-container';
    document.body.appendChild(_toastContainer);
  }
  return _toastContainer;
}

/**
 * showToast(message, type)
 * type: 'success' | 'error' | 'info'
 */
function showToast(message, type = 'info') {
  const container = _ensureToastContainer();
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('out');
    toast.addEventListener('animationend', () => toast.remove());
  }, 3000);
}

/* ── Helpers ─────────────────────────────────────────────── */
function formatPercentile(value) {
  if (value === null || value === undefined || isNaN(value)) return '—';
  return parseFloat(value).toFixed(2);
}

function getBucketColor(bucket) {
  const map = { SAFE: 'var(--safe)', MODERATE: 'var(--moderate)', REACH: 'var(--reach)' };
  return map[(bucket || '').toUpperCase()] || 'var(--text-muted)';
}

function getTrendArrow(trend) {
  if (!trend) return { icon: '→', cls: 'stable' };
  const t = trend.toUpperCase();
  if (t === 'RISING')  return { icon: '↑', cls: 'rising'  };
  if (t === 'FALLING') return { icon: '↓', cls: 'falling' };
  return { icon: '→', cls: 'stable' };
}

/** Read a URL query param */
function getParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

/** Save to shortlist in localStorage */
function saveToShortlist(college) {
  const list = getShortlistLocal();
  const exists = list.find(
    c => c.college_code === college.college_code && c.branch_name === college.branch_name
  );
  if (!exists) {
    list.push(college);
    localStorage.setItem('cetsure_shortlist', JSON.stringify(list));
    return true;
  }
  return false; // already saved
}

function getShortlistLocal() {
  try {
    return JSON.parse(localStorage.getItem('cetsure_shortlist') || '[]');
  } catch { return []; }
}

function removeFromShortlist(college_code, branch_name) {
  const list = getShortlistLocal().filter(
    c => !(c.college_code === college_code && c.branch_name === branch_name)
  );
  localStorage.setItem('cetsure_shortlist', JSON.stringify(list));
}

function isInShortlist(college_code, branch_name) {
  return getShortlistLocal().some(
    c => c.college_code === college_code && c.branch_name === branch_name
  );
}

/** Get saved profile */
function getProfile() {
  try {
    return JSON.parse(localStorage.getItem('cetsure_profile') || 'null');
  } catch { return null; }
}

/** Get saved user */
function getUser() {
  try {
    return JSON.parse(localStorage.getItem('cetsure_user') || 'null');
  } catch { return null; }
}

/** CAP Round countdown — target date June 15 current year */
function getDaysUntilCAP() {
  const now  = new Date();
  const year = now.getFullYear();
  const cap  = new Date(year, 5, 15); // June 15
  if (now > cap) cap.setFullYear(year + 1);
  const diff = Math.ceil((cap - now) / (1000 * 60 * 60 * 24));
  return diff;
}
