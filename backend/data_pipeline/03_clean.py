"""
03_clean.py — Clean and standardise extracted cutoff data.

Loads all extracted CSVs, standardises college and branch names
using fuzzy matching (thefuzz, threshold 85), converts percentiles
to float (invalid → NULL), adds metadata columns, and combines
everything into cleaned/master_cutoffs.csv.
"""

import re
import logging
import pandas as pd
from pathlib import Path
from thefuzz import fuzz

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
EXTRACTED_DIR = BASE_DIR / "extracted"
CLEANED_DIR = BASE_DIR / "cleaned"
LOGS_DIR = BASE_DIR / "logs"
CLEANED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "pipeline.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
FUZZY_THRESHOLD = 85


# ---------------------------------------------------------------------------
# Fuzzy standardisation
# ---------------------------------------------------------------------------
def standardise_names(series: pd.Series, threshold: int = FUZZY_THRESHOLD) -> pd.Series:
    """
    Standardise a series of names using fuzzy matching.
    For each unique name, find the most common similar name
    (above the threshold) and map all variants to it.
    """
    unique_names = series.dropna().unique().tolist()
    if not unique_names:
        return series

    # Build canonical mapping: for each name, find the best match
    # among already-accepted canonical names
    canonical_map: dict[str, str] = {}
    canonical_list: list[str] = []

    for name in sorted(unique_names, key=lambda x: x.strip()):
        name_clean = name.strip()
        if not name_clean:
            continue

        matched = False
        for canonical in canonical_list:
            score = fuzz.token_sort_ratio(name_clean.lower(), canonical.lower())
            if score >= threshold:
                canonical_map[name] = canonical
                matched = True
                break

        if not matched:
            canonical_list.append(name_clean)
            canonical_map[name] = name_clean

    return series.map(lambda x: canonical_map.get(x, x) if pd.notna(x) else x)


# ---------------------------------------------------------------------------
# Metadata extraction from filename
# ---------------------------------------------------------------------------
def extract_metadata(filename: str) -> dict:
    """
    Extract year and cap_round from filename like '2023_cap2_raw.csv'.
    """
    match = re.match(r"(\d{4})_cap(\d+)_raw\.csv", filename)
    if match:
        return {
            "year": int(match.group(1)),
            "cap_round": int(match.group(2)),
        }
    return {"year": None, "cap_round": None}


# ---------------------------------------------------------------------------
# Percentile cleaning
# ---------------------------------------------------------------------------
def clean_percentile(value) -> float | None:
    """Convert a percentile value to float, return None if invalid."""
    if pd.isna(value):
        return None
    try:
        val = float(value)
        if val < 0 or val > 100:
            return None
        return val
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    """Load, clean, and combine all extracted CSVs."""
    logger.info("=" * 60)
    logger.info("Starting data cleaning")
    logger.info("=" * 60)

    csv_files = sorted(EXTRACTED_DIR.glob("*_raw.csv"))
    if not csv_files:
        logger.warning("No extracted CSV files found in %s", EXTRACTED_DIR)
        return

    logger.info("Found %d extracted CSV files", len(csv_files))

    all_frames = []
    for csv_path in csv_files:
        logger.info("Loading %s ...", csv_path.name)
        df = pd.read_csv(csv_path)

        # Add metadata columns
        meta = extract_metadata(csv_path.name)
        df["year"] = meta["year"]
        df["cap_round"] = meta["cap_round"]
        df["quota"] = "MH"  # All files are MH quota per spec

        all_frames.append(df)
        logger.info("  %d rows from %s (year=%s, round=%s)",
                     len(df), csv_path.name, meta["year"], meta["cap_round"])

    if not all_frames:
        logger.warning("No data loaded")
        return

    # Combine all data
    master = pd.concat(all_frames, ignore_index=True)
    logger.info("Combined total: %d rows", len(master))

    # Standardise college names using fuzzy matching
    logger.info("Standardising college names (threshold=%d) ...", FUZZY_THRESHOLD)
    original_colleges = master["college_name"].nunique()
    master["college_name"] = standardise_names(master["college_name"])
    new_colleges = master["college_name"].nunique()
    logger.info("  College names: %d → %d unique", original_colleges, new_colleges)

    # Standardise branch names using fuzzy matching
    logger.info("Standardising branch names (threshold=%d) ...", FUZZY_THRESHOLD)
    original_branches = master["branch_name"].nunique()
    master["branch_name"] = standardise_names(master["branch_name"])
    new_branches = master["branch_name"].nunique()
    logger.info("  Branch names: %d → %d unique", original_branches, new_branches)

    # Clean percentile values
    logger.info("Cleaning percentile values ...")
    master["closing_percentile"] = master["closing_percentile"].apply(clean_percentile)
    invalid_count = master["closing_percentile"].isna().sum()
    logger.info("  NULL percentiles: %d / %d", invalid_count, len(master))

    # Convert closing_rank to nullable int
    master["closing_rank"] = pd.to_numeric(master["closing_rank"], errors="coerce")
    master["closing_rank"] = master["closing_rank"].astype("Int64")  # nullable int

    # Log row counts per year
    logger.info("Row counts per year:")
    for year, count in master.groupby("year").size().items():
        logger.info("  %s: %d rows", year, count)

    # Save master CSV
    out_path = CLEANED_DIR / "master_cutoffs.csv"
    master.to_csv(out_path, index=False)
    logger.info("Saved %d rows to %s", len(master), out_path)
    logger.info("Cleaning complete")


if __name__ == "__main__":
    main()
