"""
predict.py — CETSure Prediction Engine
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Load environment
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
_ENV_PATHS = [
    _THIS_DIR / ".env",
    _THIS_DIR.parent / "data_pipeline" / ".env",
]

for _env in _ENV_PATHS:
    if _env.exists():
        load_dotenv(_env)
        break

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
YEAR_WEIGHTS = {
    2025: 0.60,
    2024: 0.25,
    2023: 0.10,
    2022: 0.05,
}

SAFE_THRESHOLD = 2
REACH_THRESHOLD = -2
TREND_STABLE_THRESHOLD = 0.5

BRANCH_ALIASES = {
    "computer engineering": [
        "Computer Engineering",
        "Computer Science and Engineering",
        "Computer Science",
        "Computer Technology",
        "Computer Science and Technology",
        "Computer Science and Information Technology",
    ],
    "civil engineering": [
        "Civil Engineering",
        "Civil and Infrastructure Engineering",
    ],
    "mechanical engineering": [
        "Mechanical Engineering",
        "Mechanical and Automation Engineering",
    ],
    "electronics engineering": [
        "Electronics Engineering",
        "Electronics and Telecommunication Engg",
        "Electronics & Telecommunication Engineering",
        "Electronics and Communication Engineering",
    ],
    "information technology": [
        "Information Technology",
        "Computer Science and Business Systems",
    ],
    "artificial intelligence": [
        "Artificial Intelligence",
        "Artificial Intelligence (AI) and Data Science",
        "Artificial Intelligence and Data Science",
        "AI & Data Science",
        "Artificial Intelligence and Machine Learning",
        "Computer Science and Engineering (Artificial Intelligence and Data Science)",
    ],
}


# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------
def _get_engine():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL not found. Set it in .env or environment.")
    return create_engine(database_url)


# ---------------------------------------------------------------------------
# Database query
# ---------------------------------------------------------------------------
def fetch_cutoff_data(
    category: str,
    branch: str,
    quota: str = "MH",
    district: str | None = None,
    cap_round: int = 1,
    engine=None,
) -> list[dict]:
    if engine is None:
        engine = _get_engine()

    branch_lower = branch.strip().lower()

    params = {
        "category": category.strip(),
        "quota": quota.strip(),
        "cap_round": cap_round,
    }

    if branch_lower in ("other", "all branches", "all"):
        branch_condition = ""
    else:
        matched_alias = BRANCH_ALIASES.get(branch_lower)

        if matched_alias:
            alias_params = {}
            placeholders = []

            for idx, alias in enumerate(matched_alias):
                key = f"alias_{idx}"
                alias_params[key] = alias.lower()
                placeholders.append(f":{key}")

            branch_condition = f"""
                AND LOWER(c.branch_name) IN ({", ".join(placeholders)})
            """

            params.update(alias_params)

        else:
            branch_condition = """
                AND LOWER(c.branch_name) LIKE LOWER(:branch)
            """
            params["branch"] = f"%{branch}%"

    district_condition = ""
    if district and district != "All Maharashtra":
        district_condition = """
            AND LOWER(cl.district) = LOWER(:district)
        """
        params["district"] = district.strip()

    query = text(f"""
        SELECT
            c.college_code,
            COALESCE(cl.college_name, c.college_name) AS college_name,
            cl.district,
            c.branch_name,
            c.year,
            c.closing_percentile
        FROM cutoffs c
        LEFT JOIN colleges cl
            ON c.college_code = cl.college_code
        WHERE c.category = :category
          AND c.quota = :quota
          AND c.cap_round = :cap_round
          AND c.closing_percentile IS NOT NULL
          {branch_condition}
          {district_condition}
        ORDER BY c.college_code, c.branch_name, c.year
        LIMIT 2000
    """)

    with engine.connect() as conn:
        result = conn.execute(query, params)
        return [dict(row._mapping) for row in result]


# ---------------------------------------------------------------------------
# Weighted cutoff calculation
# ---------------------------------------------------------------------------
def weighted_cutoff(year_percentiles: dict[int, float]) -> float:
    if not year_percentiles:
        return 0.0

    numerator = 0.0
    denominator = 0.0

    for year, percentile in year_percentiles.items():
        weight = YEAR_WEIGHTS.get(year, 0.0)
        if weight > 0 and percentile is not None:
            numerator += float(percentile) * weight
            denominator += weight

    if denominator == 0:
        return 0.0

    return round(numerator / denominator, 4)


# ---------------------------------------------------------------------------
# Bucket classification
# ---------------------------------------------------------------------------
def classify_bucket(student_percentile: float, w_cutoff: float) -> str:
    diff = student_percentile - w_cutoff

    if diff > SAFE_THRESHOLD:
        return "SAFE"
    if diff < REACH_THRESHOLD:
        return "REACH"
    return "MODERATE"


# ---------------------------------------------------------------------------
# Trend calculation
# ---------------------------------------------------------------------------
def get_trend(year_percentiles: dict[int, float]) -> str:
    if len(year_percentiles) < 2:
        return "INSUFFICIENT_DATA"

    sorted_years = sorted(year_percentiles.keys())
    earliest = year_percentiles[sorted_years[0]]
    latest = year_percentiles[sorted_years[-1]]

    diff = latest - earliest

    if abs(diff) < TREND_STABLE_THRESHOLD:
        return "STABLE"
    if diff > 0:
        return "RISING"
    return "FALLING"


# ---------------------------------------------------------------------------
# Chance score
# ---------------------------------------------------------------------------
def calculate_chance_score(student_percentile: float, w_cutoff: float) -> int:
    diff = student_percentile - w_cutoff

    if diff >= 15:
        return 95
    if diff >= 10:
        return 88
    if diff >= 5:
        return 78
    if diff >= 2:
        return 65
    if diff >= -2:
        return 50
    if diff >= -5:
        return 35
    if diff >= -10:
        return 20
    return 10


def build_reason(student_percentile: float, w_cutoff: float) -> str:
    diff = round(student_percentile - w_cutoff, 2)

    if diff > 0:
        return f"Your percentile is {diff} above the predicted cutoff."
    if diff < 0:
        return f"Your percentile is {abs(diff)} below the predicted cutoff."
    return "Your percentile is almost equal to the predicted cutoff."


# ---------------------------------------------------------------------------
# Group rows into college objects
# ---------------------------------------------------------------------------
def _group_by_college(rows: list[dict]) -> dict:
    colleges = {}

    for row in rows:
        key = (str(row["college_code"]), row["branch_name"])

        if key not in colleges:
            colleges[key] = {
                "college_code": str(row["college_code"]),
                "college_name": row["college_name"],
                "district": row.get("district"),
                "branch_name": row["branch_name"],
                "year_percentiles": {},
            }

        year = int(row["year"])
        percentile = row["closing_percentile"]

        if percentile is not None:
            colleges[key]["year_percentiles"][year] = float(percentile)

    return colleges


# ---------------------------------------------------------------------------
# Main predict function
# ---------------------------------------------------------------------------
def predict(
    percentile: float,
    category: str,
    branch: str,
    district: str | None = None,
    quota: str = "MH",
    cap_round: int = 1,
) -> dict:
    if percentile < 0 or percentile > 100:
        raise ValueError(f"Percentile must be between 0 and 100, got {percentile}")

    rows = fetch_cutoff_data(
        category=category,
        branch=branch,
        quota=quota,
        district=district,
        cap_round=cap_round,
    )

    college_groups = _group_by_college(rows)

    safe = []
    moderate = []
    reach = []

    for _key, college in college_groups.items():
        year_pcts = college["year_percentiles"]

        if not year_pcts:
            continue

        w_cutoff = weighted_cutoff(year_pcts)
        bucket = classify_bucket(percentile, w_cutoff)
        trend = get_trend(year_pcts)
        chance_score = calculate_chance_score(percentile, w_cutoff)

        college_obj = {
            "college_code": college["college_code"],
            "college_name": college["college_name"],
            "district": college.get("district"),
            "branch_name": college["branch_name"],
            "weighted_cutoff": round(w_cutoff, 2),
            "last_year_cutoff": year_pcts.get(2025) or year_pcts.get(2024),
            "cutoff_2022": year_pcts.get(2022),
            "cutoff_2023": year_pcts.get(2023),
            "cutoff_2024": year_pcts.get(2024),
            "cutoff_2025": year_pcts.get(2025),
            "trend": trend,
            "data_years": len(year_pcts),
            "chance_score": chance_score,
            "reason": build_reason(percentile, w_cutoff),
            "bucket": bucket,
        }

        if bucket == "SAFE":
            safe.append(college_obj)
        elif bucket == "MODERATE":
            moderate.append(college_obj)
        else:
            reach.append(college_obj)

    safe.sort(key=lambda c: c["weighted_cutoff"], reverse=True)
    moderate.sort(key=lambda c: c["weighted_cutoff"], reverse=True)
    reach.sort(key=lambda c: c["weighted_cutoff"], reverse=True)

    total_colleges = len(safe) + len(moderate) + len(reach)

    return {
        "safe": safe,
        "moderate": moderate,
        "reach": reach,
        "meta": {
            "percentile": percentile,
            "category": category,
            "branch": branch,
            "district": district,
            "quota": quota,
            "cap_round": cap_round,
            "total_colleges": total_colleges,
        },
    }