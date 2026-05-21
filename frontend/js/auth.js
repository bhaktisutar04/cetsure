/**
 * auth.js — CETSure Firebase authentication
 * 
 * Firebase SDK is loaded via CDN in each HTML page.
 * FIREBASE_CONFIG is defined in config.js.
 * 
 * Until Firebase is configured, auth uses localStorage
 * to store a mock user so the app flow can be tested.
 */

let _firebaseApp  = null;
let _firebaseAuth = null;
let _confirmResult = null; // for phone OTP

/* ── Init ─────────────────────────────────────────────────── */
function initFirebase() {
  if (_firebaseApp) return;
  // Only init if config keys are present
  if (!FIREBASE_CONFIG.apiKey) {
    console.warn('[auth] Firebase config not set — using localStorage mock auth.');
    return;
  }
  try {
    _firebaseApp  = firebase.initializeApp(FIREBASE_CONFIG);
    _firebaseAuth = firebase.auth();
    _firebaseAuth.onAuthStateChanged(_handleAuthStateChange);
  } catch (e) {
    console.error('[auth] Firebase init error:', e);
  }
}

function _handleAuthStateChange(user) {
  if (user) {
    const u = { uid: user.uid, name: user.displayName, email: user.email, photo: user.photoURL };
    localStorage.setItem('cetsure_user', JSON.stringify(u));
  }
}

/* ── Google Sign In ────────────────────────────────────────── */
async function signInWithGoogle() {
  if (!_firebaseAuth) {
    // Mock: store fake user, navigate to profile
    _mockSignIn('Google User');
    return;
  }
  const provider = new firebase.auth.GoogleAuthProvider();
  const result = await _firebaseAuth.signInWithPopup(provider);
  const user = result.user;
  const u = { uid: user.uid, name: user.displayName, email: user.email, photo: user.photoURL };
  localStorage.setItem('cetsure_user', JSON.stringify(u));
  return u;
}

/* ── Phone Sign In ─────────────────────────────────────────── */
async function signInWithPhone(phoneNumber, recaptchaContainerId = 'recaptcha-container') {
  if (!_firebaseAuth) {
    console.warn('[auth] Mock phone sign-in — OTP step skipped.');
    return 'MOCK';
  }
  if (!window.recaptchaVerifier) {
    window.recaptchaVerifier = new firebase.auth.RecaptchaVerifier(
      recaptchaContainerId,
      { size: 'invisible' }
    );
  }
  _confirmResult = await _firebaseAuth.signInWithPhoneNumber(phoneNumber, window.recaptchaVerifier);
  return _confirmResult;
}

async function verifyOTP(otp) {
  if (!_confirmResult) {
    // Mock: accept any 6-digit OTP
    _mockSignIn('Phone User');
    return;
  }
  const result = await _confirmResult.confirm(otp);
  const user = result.user;
  const u = { uid: user.uid, name: user.displayName || 'Student', email: user.email, photo: null };
  localStorage.setItem('cetsure_user', JSON.stringify(u));
  return u;
}

/* ── Get Current User ──────────────────────────────────────── */
function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem('cetsure_user') || 'null');
  } catch { return null; }
}

/* ── Logout ────────────────────────────────────────────────── */
async function logout() {
  localStorage.removeItem('cetsure_user');
  if (_firebaseAuth) await _firebaseAuth.signOut();
  window.location.href = 'index.html';
}

/* ── Protect Page ──────────────────────────────────────────── */
/**
 * Call at top of any protected page.
 * Redirects to signup.html if no user in localStorage.
 */
function protectPage() {
  if (!getCurrentUser()) {
    window.location.href = 'signup.html';
  }
}

/* ── Mock Helpers ──────────────────────────────────────────── */
function _mockSignIn(name) {
  const u = { uid: 'mock-' + Date.now(), name, email: '', photo: null };
  localStorage.setItem('cetsure_user', JSON.stringify(u));
}

// Auto-init Firebase when this script loads
initFirebase();
