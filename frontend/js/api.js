/**
 * api.js
 * Backend API calls for CETSure
 */

// ------------------------------
// Predict colleges
// ------------------------------
async function predictColleges(payload) {
  const response = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(
      errorData?.detail || "Prediction failed. Please try again."
    );
  }

  return await response.json();
}

// ------------------------------
// Search colleges
// ------------------------------
async function searchColleges(query) {
  const response = await fetch(
    `${API_BASE}/search?q=${encodeURIComponent(query)}`
  );

  if (!response.ok) {
    throw new Error("College search failed.");
  }

  return await response.json();
}

// ------------------------------
// Get college details
// ------------------------------
async function getCollegeDetails(collegeCode) {
  const response = await fetch(
    `${API_BASE}/college/${encodeURIComponent(collegeCode)}`
  );

  if (!response.ok) {
    throw new Error("College details not found.");
  }

  return await response.json();
}