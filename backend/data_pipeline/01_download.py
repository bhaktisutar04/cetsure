"""
01_download.py — Download MAHACET provisional allotment PDFs.

Downloads CAP Round 1, 2, 3 cutoff PDFs for years 2022–2024
from fe2025.mahacet.org and saves them to raw_pdfs/{year}/.
"""

import os
import time
import logging
import requests
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
RAW_PDFS_DIR = BASE_DIR / "raw_pdfs"
LOGS_DIR = BASE_DIR / "logs"
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
BASE_URL = "http://fe2025.mahacet.org"
YEARS = [2022, 2023, 2024]
CAP_ROUNDS = [1, 2, 3]
DELAY_SECONDS = 1

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ---------------------------------------------------------------------------
# Download logic
# ---------------------------------------------------------------------------
def build_url(year: int, cap_round: int) -> str:
    """Build the PDF URL for a given year and CAP round."""
    return f"{BASE_URL}/{year}/{year}ENGG_CAP{cap_round}_CutOff.pdf"


def download_pdf(year: int, cap_round: int) -> None:
    """Download a single PDF, skipping if it already exists."""
    url = build_url(year, cap_round)
    dest_dir = RAW_PDFS_DIR / str(year)
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{year}ENGG_CAP{cap_round}_CutOff.pdf"
    dest_path = dest_dir / filename

    # Skip if already downloaded
    if dest_path.exists():
        logger.info("SKIP  %s — already exists", dest_path.name)
        return

    try:
        logger.info("GET   %s", url)
        response = requests.get(url, headers=HEADERS, timeout=60)
        response.raise_for_status()

        with open(dest_path, "wb") as f:
            f.write(response.content)

        size_kb = len(response.content) / 1024
        logger.info("SAVED %s  (%.1f KB)", dest_path.name, size_kb)

    except requests.RequestException as exc:
        logger.error("FAIL  %s — %s", url, exc)


def main() -> None:
    """Download all PDFs for all years and CAP rounds."""
    logger.info("=" * 60)
    logger.info("Starting PDF download")
    logger.info("=" * 60)

    total = 0
    for year in YEARS:
        for cap_round in CAP_ROUNDS:
            download_pdf(year, cap_round)
            total += 1
            time.sleep(DELAY_SECONDS)

    logger.info("Download complete — attempted %d files", total)


if __name__ == "__main__":
    main()
