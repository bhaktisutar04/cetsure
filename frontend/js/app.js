/**
 * app.js
 * Common reusable frontend helpers
 */

// -----------------------------
// Current User
// -----------------------------
function getLoggedInUserId() {
    const user = JSON.parse(localStorage.getItem(STORAGE_KEYS.USER));
    return user?.uid || "guest";
}

function userKey(key) {
    const uid = getLoggedInUserId();
    return `${key}_${uid}`;
}

// -----------------------------
// Navigation
// -----------------------------
function goTo(page) {
    window.location.href = page;
}

// -----------------------------
// Toast Message
// -----------------------------
function showMessage(message) {
    let toast = document.createElement("div");
    toast.className = "toast-message";
    toast.innerText = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("show");
    }, 100);

    setTimeout(() => {
        toast.classList.remove("show");

        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 2500);
}

// -----------------------------
// Profile
// -----------------------------
function saveProfile(profileData) {
    localStorage.setItem(
        userKey(STORAGE_KEYS.PROFILE),
        JSON.stringify(profileData)
    );
}

function getProfile() {
    const profile = localStorage.getItem(
        userKey(STORAGE_KEYS.PROFILE)
    );

    if (!profile) return null;

    try {
        return JSON.parse(profile);
    } catch {
        return null;
    }
}

function hasCompletedProfile() {
    return !!getProfile();
}

function requireProfile() {
    if (!hasCompletedProfile()) {
        goTo(ROUTES.PROFILE);
    }
}

// -----------------------------
// Percentile Formatting
// -----------------------------
function formatPercentile(value) {
    return Number(value).toFixed(2);
}

// -----------------------------
// Prediction Results
// -----------------------------
function savePredictionResults(results) {
    localStorage.setItem(
        userKey(STORAGE_KEYS.PREDICTION_RESULTS),
        JSON.stringify(results)
    );
}

function getPredictionResults() {
    const results = localStorage.getItem(
        userKey(STORAGE_KEYS.PREDICTION_RESULTS)
    );

    if (!results) return null;

    try {
        return JSON.parse(results);
    } catch {
        return null;
    }
}

// -----------------------------
// Shortlist
// -----------------------------
function getShortlistKey() {
    return userKey("cetsure_shortlist");
}

// -----------------------------
// Bottom Navbar
// -----------------------------
function renderBottomNavbar() {
    const currentPath = window.location.pathname;

    function isActive(page) {
        return currentPath.includes(page) ? "nav-active" : "";
    }

    const navbar = document.createElement("div");

    navbar.className = "bottom-navbar";

    navbar.innerHTML = `
    <button
      class="${isActive("home")}"
      onclick="goTo('home.html')"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
        <polyline points="9 22 9 12 15 12 15 22"/>
      </svg>
      <span>Home</span>
    </button>

    <button
      class="${isActive("predict") || isActive("results") ? "nav-active" : ""}"
      onclick="goTo('predict.html')"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <circle cx="12" cy="12" r="6"/>
        <circle cx="12" cy="12" r="2"/>
      </svg>
      <span>Predict</span>
    </button>

    <button
      class="${isActive("search") || isActive("college") ? "nav-active" : ""}"
      onclick="goTo('search.html')"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <span>Search</span>
    </button>

    <button
      class="${isActive("shortlist") || isActive("compare") ? "nav-active" : ""}"
      onclick="goTo('shortlist.html')"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
      </svg>
      <span>Shortlist</span>
    </button>
  `;

    document.body.appendChild(navbar);
}

// -----------------------------
// Auto Navbar Injection
// -----------------------------
window.addEventListener("DOMContentLoaded", () => {
    const currentPage = window.location.pathname;

    const allowedPages = [
        "home",
        "home.html",

        "predict",
        "predict.html",

        "results",
        "results.html",

        "search",
        "search.html",

        "college",
        "college.html",

        "shortlist",
        "shortlist.html",

        "compare",
        "compare.html"
    ];

    const shouldRender = allowedPages.some((page) =>
        currentPage.includes(page)
    );

    if (shouldRender) {
        renderBottomNavbar();
    }
});