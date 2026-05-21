"""
02_parse.py — Parse MAHACET allotment PDFs and extract cutoff data.

Actual PDF structure (discovered via inspection):
- Page header text has college line '1002 - Govt College ...'
  and branch line '100219110 - Civil Engineering'
- Each page has 2–4 small tables, each with exactly 2 rows:
    Row 0 (headers): [None, 'GOPENS', 'GSCS', 'GSTS', ...]
    Row 1 (values):  ['I', '45820\n(80.7328826)', '54803\n(76.6166542)', ...]
- Values are in 'RANK\n(PERCENTILE)' format
- Quota is detected from page text (State Level / Home University → MH,
  All India → AI)
"""

import re
import logging
import pdfplumber
import pandas as pd
from pathlib import Path
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
RAW_PDFS_DIR = BASE_DIR / "raw_pdfs"
EXTRACTED_DIR = BASE_DIR / "extracted"
LOGS_DIR = BASE_DIR / "logs"
EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
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
# Header parsing
# ---------------------------------------------------------------------------
def parse_code_and_name(line: str) -> tuple:
    """
    Parse a line like '1002 - Government College of Engineering, Amravati'
    into (code, name). Returns (None, None) if pattern doesn't match.
    """
    match = re.match(r"^\s*(\d+)\s*[-–—]\s*(.+)$", line.strip())
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None


def extract_header_info(text: str) -> dict:
    """
    Extract college_code, college_name, branch_code, branch_name
    from the page text. First code-name line = college, second = branch.
    """
    info = {
        "college_code": None,
        "college_name": None,
        "branch_code": None,
        "branch_name": None,
    }

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    found = 0
    for line in lines:
        code, name = parse_code_and_name(line)
        if code is not None:
            if found == 0:
                info["college_code"] = code
                info["college_name"] = name
                found += 1
            elif found == 1:
                info["branch_code"] = code
                info["branch_name"] = name
                found += 1
                break
    return info


# ---------------------------------------------------------------------------
# Quota detection
# ---------------------------------------------------------------------------
def detect_quota(text: str) -> str:
    """
    Detect quota from page text.
    'All India' → AI, otherwise MH (State Level / Home University / default).
    """
    text_lower = text.lower()
    if "all india" in text_lower:
        return "AI"
    return "MH"


# ---------------------------------------------------------------------------
# Value parsing
# ---------------------------------------------------------------------------
def parse_rank_percentile(cell_value: str) -> tuple:
    """
    Parse a cell like '45820\\n(80.7328826)' into (rank, percentile).

    Formats handled:
    - '45820\\n(80.7328826)' → (45820, 80.7328826)
    - '45820(80.7328826)'    → (45820, 80.7328826)  (no newline)
    - '80.7328826'           → (None, 80.7328826)    (plain number)
    - '45820'                → (None, 45820.0)        (plain integer)
    - empty / None / '--'    → (None, None)
    """
    if cell_value is None:
        return None, None

    val = str(cell_value).strip()
    if not val or val in ("--", "-", "N/A", "NA", ""):
        return None, None

    # Try format: RANK\n(PERCENTILE) or RANK(PERCENTILE)
    match = re.match(r"^(\d+)\s*\n?\s*\((\d+\.?\d*)\)$", val)
    if match:
        rank = int(match.group(1))
        percentile = float(match.group(2))
        return rank, percentile

    # Try format: just (PERCENTILE)
    match = re.match(r"^\((\d+\.?\d*)\)$", val)
    if match:
        return None, float(match.group(1))

    # Try format: plain number (could be int or float)
    match = re.match(r"^(\d+\.?\d*)$", val)
    if match:
        return None, float(match.group(1))

    return None, None


# ---------------------------------------------------------------------------
# Table parsing (actual PDF structure)
# ---------------------------------------------------------------------------
def parse_tables_on_page(page) -> list[dict]:
    """
    Extract cutoff rows from all tables on a page.

    Each table has exactly 2 rows:
      Row 0 = headers: [None, 'GOPENS', 'GSCS', 'GSTS', ...]
      Row 1 = values:  ['I',  '45820\\n(80.7328826)', ...]

    Returns list of dicts with keys: category, closing_rank, closing_percentile.
    """
    tables = page.extract_tables()
    if not tables:
        return []

    rows_out = []
    for table in tables:
        if not table or len(table) < 2:
            continue

        headers = table[0]   # [None, 'GOPENS', 'GSCS', ...]
        values = table[1]    # ['I', '45820\n(80.7328826)', ...]

        if headers is None or values is None:
            continue

        # Iterate through columns, skipping the first (None / 'I') column
        for col_idx in range(1, min(len(headers), len(values))):
            category = headers[col_idx]
            cell = values[col_idx]

            if category is None or str(category).strip() == "":
                continue

            category = str(category).strip().upper()
            rank, percentile = parse_rank_percentile(cell)

            rows_out.append({
                "category": category,
                "closing_rank": rank,
                "closing_percentile": percentile,
            })

    return rows_out


# ---------------------------------------------------------------------------
# PDF processing
# ---------------------------------------------------------------------------
def parse_pdf(pdf_path: Path, year: int, cap_round: int) -> list[dict]:
    """Parse a single PDF file and return all cutoff rows."""
    all_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            try:
                text = page.extract_text() or ""
                header = extract_header_info(text)

                if not header["college_code"]:
                    logger.warning(
                        "  Page %d: Could not extract college code — skipping",
                        page_num,
                    )
                    continue

                quota = detect_quota(text)
                cutoff_rows = parse_tables_on_page(page)

                for row in cutoff_rows:
                    row["college_code"] = header["college_code"]
                    row["college_name"] = header["college_name"]
                    row["branch_code"] = header["branch_code"]
                    row["branch_name"] = header["branch_name"]
                    row["quota"] = quota
                    row["year"] = year
                    row["cap_round"] = cap_round

                all_rows.extend(cutoff_rows)

            except Exception as exc:
                logger.error(
                    "  Page %d ERROR: %s — continuing", page_num, exc
                )
                continue

    return all_rows


def extract_year_and_round(filename: str) -> tuple:
    """
    Extract year and cap round from filename like
    '2023ENGG_CAP2_CutOff.pdf'.
    """
    match = re.match(r"(\d{4})ENGG_CAP(\d+)_CutOff\.pdf", filename)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
# Column order for output CSV
CSV_COLUMNS = [
    "college_code",
    "college_name",
    "branch_code",
    "branch_name",
    "category",
    "quota",
    "year",
    "cap_round",
    "closing_rank",
    "closing_percentile",
]


def main() -> None:
    """Parse all PDFs in raw_pdfs/ and save extracted CSVs."""
    logger.info("=" * 60)
    logger.info("Starting PDF parsing")
    logger.info("=" * 60)

    pdf_files = sorted(RAW_PDFS_DIR.glob("**/*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in %s", RAW_PDFS_DIR)
        return

    logger.info("Found %d PDF files", len(pdf_files))

    for pdf_path in tqdm(pdf_files, desc="Parsing PDFs"):
        year, cap_round = extract_year_and_round(pdf_path.name)
        if year is None:
            logger.warning("Cannot extract year/round from %s — skipping", pdf_path.name)
            continue

        logger.info("Parsing %s ...", pdf_path.name)
        rows = parse_pdf(pdf_path, year, cap_round)

        if rows:
            df = pd.DataFrame(rows, columns=CSV_COLUMNS)
            out_file = EXTRACTED_DIR / f"{year}_cap{cap_round}_raw.csv"
            df.to_csv(out_file, index=False)
            logger.info("  Saved %d rows to %s", len(df), out_file.name)
        else:
            logger.warning("  No rows extracted from %s", pdf_path.name)

    logger.info("Parsing complete")


if __name__ == "__main__":
    main()
