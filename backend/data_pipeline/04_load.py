import os
import logging
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent
CLEANED_DIR = BASE_DIR / "cleaned"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "pipeline.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 1000

def main():
    logger.info("=" * 60)
    logger.info("Starting database load")
    logger.info("=" * 60)

    database_url = os.getenv("DATABASE_URL")
    engine = create_engine(database_url)

    df = pd.read_csv(CLEANED_DIR / "master_cutoffs.csv")
    logger.info("Loaded %d rows", len(df))

    df["college_code"] = df["college_code"].astype(str)
    df["branch_code"] = df["branch_code"].astype(str)
    df["year"] = df["year"].astype(int)
    df["cap_round"] = df["cap_round"].astype(int)

    total = 0
    for i in range(0, len(df), BATCH_SIZE):
        batch = df.iloc[i:i + BATCH_SIZE]
        try:
            with engine.begin() as conn:
                for _, row in batch.iterrows():
                    conn.execute(text("""
                        INSERT INTO cutoffs 
                            (college_code, college_name, branch_code, branch_name,
                             category, quota, year, cap_round, 
                             closing_rank, closing_percentile)
                        VALUES 
                            (:college_code, :college_name, :branch_code, :branch_name,
                             :category, :quota, :year, :cap_round,
                             :closing_rank, :closing_percentile)
                        ON CONFLICT ON CONSTRAINT cutoffs_unique DO NOTHING
                    """), {
                        "college_code":       str(row["college_code"]),
                        "college_name":       row["college_name"],
                        "branch_code":        str(row["branch_code"]),
                        "branch_name":        row["branch_name"],
                        "category":           row["category"],
                        "quota":              row["quota"],
                        "year":               int(row["year"]),
                        "cap_round":          int(row["cap_round"]),
                        "closing_rank":       None if pd.isna(row["closing_rank"]) else int(row["closing_rank"]),
                        "closing_percentile": None if pd.isna(row["closing_percentile"]) else float(row["closing_percentile"]),
                    })
            total += len(batch)
            logger.info("  Committed batch %d-%d", i+1, i+len(batch))
        except Exception as e:
            logger.error("  FAILED batch %d-%d: %s", i+1, i+len(batch), str(e))
            continue

    logger.info("Done. Total rows processed: %d", total)

if __name__ == "__main__":
    main()