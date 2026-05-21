/**
 * api.js — CETSure backend API calls
 * All fetch() calls to the FastAPI backend.
 * Reads API_BASE from config.js (must be loaded first).
 */

/**
 * predictColleges — POST /predict
 * @param {number} percentile
 * @param {string} category   e.g. "GOOPENS"
 * @param {string} branch     e.g. "computer engineering"
 * @param {string|null} district e.g. "Pune"
 * @param {string} quota      "MH" | "AI"
 * @returns {Promise<{safe:[], moderate:[], reach:[], meta:{}}>}
 */
async function predictColleges(percentile, category, branch, district = null, quota = 'MH') {
  const body = { percentile, category, branch, quota };
  if (district && district !== 'All Maharashtra') body.district = district;

  const res = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Prediction failed (${res.status})`);
  }
  return res.json();
}

/**
 * getCollegeDetail — GET /college/{code}
 * @param {string} collegeCode
 * @returns {Promise<{college_code, college_name, cutoffs:[]}>}
 */
async function getCollegeDetail(collegeCode) {
  const res = await fetch(`${API_BASE}/college/${encodeURIComponent(collegeCode)}`);
  if (!res.ok) {
    throw new Error(`College not found (${res.status})`);
  }
  return res.json();
}

/**
 * searchColleges — GET /search?q=query
 * @param {string} query
 * @returns {Promise<{results: [{college_code, college_name}]}>}
 */
async function searchColleges(query) {
  if (!query || query.trim().length < 2) return { results: [] };
  const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query.trim())}`);
  if (!res.ok) {
    throw new Error(`Search failed (${res.status})`);
  }
  return res.json();
}
