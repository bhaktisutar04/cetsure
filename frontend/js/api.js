/**
 * api.js
 * Secured Backend API calls for CETSure
 */

// ---------------------------------------------------------------------------
// Auth Session & Token Helpers
// ---------------------------------------------------------------------------
function handleUnauthorized() {
    console.warn("Session invalid or expired. Redirecting to login...");
    try {
        if (typeof auth !== "undefined") {
            auth.signOut().catch(() => {});
        }
    } catch (e) {
        console.error("Error signing out from Firebase:", e);
    }
    // Clear user credentials from storage
    if (typeof STORAGE_KEYS !== "undefined" && STORAGE_KEYS.USER) {
        localStorage.removeItem(STORAGE_KEYS.USER);
    } else {
        localStorage.removeItem("cetsure_user");
    }
    // Redirect to landing / login page
    window.location.href = "index.html";
}

function getFirebaseToken() {
    return new Promise((resolve, reject) => {
        if (typeof auth === "undefined") {
            reject(new Error("Firebase auth client is not defined."));
            return;
        }

        const user = auth.currentUser;
        if (user) {
            user.getIdToken()
                .then(token => resolve(token))
                .catch(err => reject(err));
            return;
        }

        // Wait for Firebase Auth loading (async restore from IndexedDB)
        const unsubscribe = auth.onAuthStateChanged((user) => {
            unsubscribe();
            if (user) {
                user.getIdToken()
                    .then(token => resolve(token))
                    .catch(err => reject(err));
            } else {
                reject(new Error("Session expired"));
            }
        });
    });
}

// ---------------------------------------------------------------------------
// Predict colleges
// ---------------------------------------------------------------------------
async function predictColleges(payload) {
    const token = await getFirebaseToken().catch(() => null);
    if (!token) {
        handleUnauthorized();
        throw new Error("Session expired");
    }

    const response = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(payload),
    });

    if (response.status === 401) {
        handleUnauthorized();
        throw new Error("Session expired");
    }

    if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
            errorData?.detail || "Prediction failed. Please try again."
        );
    }

    return await response.json();
}

// ---------------------------------------------------------------------------
// Search colleges
// ---------------------------------------------------------------------------
async function searchColleges(query) {
    const token = await getFirebaseToken().catch(() => null);
    if (!token) {
        handleUnauthorized();
        throw new Error("Session expired");
    }

    const response = await fetch(
        `${API_BASE}/search?q=${encodeURIComponent(query)}`,
        {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        }
    );

    if (response.status === 401) {
        handleUnauthorized();
        throw new Error("Session expired");
    }

    if (!response.ok) {
        throw new Error("College search failed.");
    }

    return await response.json();
}

// ---------------------------------------------------------------------------
// Get college details
// ---------------------------------------------------------------------------
async function getCollegeDetails(collegeCode) {
    const token = await getFirebaseToken().catch(() => null);
    if (!token) {
        handleUnauthorized();
        throw new Error("Session expired");
    }

    const response = await fetch(
        `${API_BASE}/college/${encodeURIComponent(collegeCode)}`,
        {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        }
    );

    if (response.status === 401) {
        handleUnauthorized();
        throw new Error("Session expired");
    }

    if (!response.ok) {
        throw new Error("College details not found.");
    }

    return await response.json();
}