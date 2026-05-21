# save as inspect.py in backend/data_pipeline/
import pdfplumber
from pathlib import Path

pdf_path = Path("raw_pdfs/2023/2023ENGG_CAP1_CutOff.pdf")

with pdfplumber.open(pdf_path) as pdf:
    # check pages 1, 2, 3
    for page_num in [0, 1, 2]:
        page = pdf.pages[page_num]
        print(f"\n=== PAGE {page_num + 1} TEXT ===")
        print(page.extract_text()[:500])
        print(f"\n=== PAGE {page_num + 1} TABLE ===")
        tables = page.extract_tables()
        if tables:
            for t in tables:
                print(f"Rows: {len(t)}, Cols: {len(t[0])}")
                for row in t[:4]:
                    print(row)
        else:
            print("No table found")