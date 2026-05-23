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
      🏠
      <span>Home</span>
    </button>

    <button
      class="${isActive("predict") || isActive("results") ? "nav-active" : ""}"
      onclick="goTo('predict.html')"
    >
      🎯
      <span>Predict</span>
    </button>

    <button
      class="${isActive("search") || isActive("college") ? "nav-active" : ""}"
      onclick="goTo('search.html')"
    >
      🔍
      <span>Search</span>
    </button>

    <button
      class="${isActive("shortlist") || isActive("compare") ? "nav-active" : ""}"
      onclick="goTo('shortlist.html')"
    >
      ❤️
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