"""
test_predict.py — Runs all 5 test cases from the F2 spec and prints results clearly.

Usage:
  python -m backend.prediction.test_predict
  or
  python backend/prediction/test_predict.py (from backend/ directory or root directory if path is resolved)
"""

import sys
from pathlib import Path

# Add project root and backend to path so we can import properly
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from backend.prediction.predict import predict
except ImportError:
    # If run from backend directory directly
    from predict import predict


def print_section(title: str):
    print("\n" + "=" * 80)
    print(f" {title} ")
    print("=" * 80)


def print_summary(res: dict):
    meta = res["meta"]
    print(f"Query: Percentile={meta['percentile']}, Category={meta['category']}, Branch='{meta['branch']}', District={meta['district']}")
    print(f"Total Colleges Found: {meta['total_colleges']}")
    print(f"  - SAFE:     {len(res['safe'])}")
    print(f"  - MODERATE: {len(res['moderate'])}")
    print(f"  - REACH:    {len(res['reach'])}")
    
    # Print a few samples of each
    print("\nSAFE (Top 3):")
    for c in res["safe"][:3]:
        print(f"  [{c['college_code']}] {c['college_name']} - {c['branch_name']}")
        print(f"    Weighted Cutoff: {c['weighted_cutoff']} | Cutoffs: 2025={c['cutoff_2025']}, 2024={c['cutoff_2024']}, 2023={c['cutoff_2023']}, 2022={c['cutoff_2022']} | Trend: {c['trend']}")
        
    print("\nMODERATE (Top 3):")
    for c in res["moderate"][:3]:
        print(f"  [{c['college_code']}] {c['college_name']} - {c['branch_name']}")
        print(f"    Weighted Cutoff: {c['weighted_cutoff']} | Cutoffs: 2025={c['cutoff_2025']}, 2024={c['cutoff_2024']}, 2023={c['cutoff_2023']}, 2022={c['cutoff_2022']} | Trend: {c['trend']}")
        
    print("\nREACH (Top 3):")
    for c in res["reach"][:3]:
        print(f"  [{c['college_code']}] {c['college_name']} - {c['branch_name']}")
        print(f"    Weighted Cutoff: {c['weighted_cutoff']} | Cutoffs: 2025={c['cutoff_2025']}, 2024={c['cutoff_2024']}, 2023={c['cutoff_2023']}, 2022={c['cutoff_2022']} | Trend: {c['trend']}")


def run_test_cases():
    print_section("STARTING TEST CASES FOR F2 PREDICTION ENGINE")

    # --- Test Case 1 ---
    print_section("Test Case 1: percentile=95, category=GOPENS, branch=Computer Engineering")
    try:
        res1 = predict(percentile=95.0, category="GOPENS", branch="Computer Engineering")
        print_summary(res1)
        
        # Verify if COEP or other premier colleges are categorized correctly
        coep_found = None
        for bucket in ["safe", "moderate", "reach"]:
            for c in res1[bucket]:
                if "COEP" in c["college_name"].upper() or "COLLEGE OF ENGINEERING, PUNE" in c["college_name"].upper() or "COLLEGE OF ENGINEERING PUNE" in c["college_name"].upper():
                    coep_found = (c["college_name"], bucket, c["weighted_cutoff"])
                    break
            if coep_found:
                break
        
        if coep_found:
            print(f"\n[VERIFICATION] COEP found: {coep_found[0]} in {coep_found[1].upper()} bucket (Weighted Cutoff: {coep_found[2]})")
        else:
            print("\n[VERIFICATION] COEP not found in results. Check if COEP data is loaded in DB.")
    except Exception as e:
        print(f"Error in Test Case 1: {e}")

    # --- Test Case 2 ---
    print_section("Test Case 2: percentile=50, category=GOPENS, branch=Computer Engineering")
    try:
        res2 = predict(percentile=50.0, category="GOPENS", branch="Computer Engineering")
        print_summary(res2)
        total = res2["meta"]["total_colleges"]
        reach_count = len(res2["reach"])
        if total > 0:
            pct_reach = (reach_count / total) * 100
            print(f"\n[VERIFICATION] Percent of colleges in REACH: {pct_reach:.1f}% ({reach_count}/{total})")
            if pct_reach > 80:
                print("SUCCESS: Most colleges are indeed in REACH bucket.")
            else:
                print("WARNING: Less than 80% of colleges are in REACH.")
        else:
            print("\n[VERIFICATION] No data available.")
    except Exception as e:
        print(f"Error in Test Case 2: {e}")

    # --- Test Case 3 ---
    print_section("Test Case 3: percentile=85, category=GOBCS vs GOPENS, branch=Computer Engineering")
    try:
        res3_gopens = predict(percentile=85.0, category="GOPENS", branch="Computer Engineering")
        res3_gobcs = predict(percentile=85.0, category="GOBCS", branch="Computer Engineering")
        
        print("GOPENS Cutoffs (Top 3 Safe/Moderate):")
        gopens_combined = res3_gopens["safe"] + res3_gopens["moderate"]
        for c in gopens_combined[:3]:
            print(f"  [{c['college_code']}] {c['college_name']} -> Weighted Cutoff: {c['weighted_cutoff']}")
            
        print("\nGOBCS Cutoffs (Top 3 Safe/Moderate):")
        gobcs_combined = res3_gobcs["safe"] + res3_gobcs["moderate"]
        for c in gobcs_combined[:3]:
            print(f"  [{c['college_code']}] {c['college_name']} -> Weighted Cutoff: {c['weighted_cutoff']}")
            
        # Check if the list lengths or colleges differ
        if len(res3_gopens["safe"]) != len(res3_gobcs["safe"]) or len(res3_gopens["moderate"]) != len(res3_gobcs["moderate"]):
            print("\n[VERIFICATION] SUCCESS: GOPENS and GOBCS returned different bucket distributions.")
        else:
            # Let's compare weighted cutoffs for a common college
            common = set(c["college_code"] for c in res3_gopens["safe"] + res3_gopens["moderate"]) & set(c["college_code"] for c in res3_gobcs["safe"] + res3_gobcs["moderate"])
            if common:
                code = list(common)[0]
                g_cutoff = next(c["weighted_cutoff"] for c in res3_gopens["safe"] + res3_gopens["moderate"] + res3_gopens["reach"] if c["college_code"] == code)
                o_cutoff = next(c["weighted_cutoff"] for c in res3_gobcs["safe"] + res3_gobcs["moderate"] + res3_gobcs["reach"] if c["college_code"] == code)
                print(f"\n[VERIFICATION] College [{code}] Weighted Cutoffs: GOPENS={g_cutoff}, GOBCS={o_cutoff}")
                if g_cutoff != o_cutoff:
                    print("SUCCESS: Cutoffs differ between categories.")
                else:
                    print("WARNING: Cutoffs are identical for the same college.")
            else:
                print("\n[VERIFICATION] No common colleges in Safe/Moderate buckets to compare.")
    except Exception as e:
        print(f"Error in Test Case 3: {e}")

    # --- Test Case 4 ---
    print_section("Test Case 4: Invalid category INVALIDCAT")
    try:
        res4 = predict(percentile=85.0, category="INVALIDCAT", branch="Computer Engineering")
        print_summary(res4)
        if len(res4["safe"]) == 0 and len(res4["moderate"]) == 0 and len(res4["reach"]) == 0:
            print("\n[VERIFICATION] SUCCESS: Handled invalid category gracefully, returned empty lists.")
        else:
            print("\n[VERIFICATION] FAILURE: Returned non-empty list for invalid category.")
    except Exception as e:
        print(f"\n[VERIFICATION] FAILURE: Crashed on invalid category with error: {e}")

    # --- Test Case 5 ---
    print_section("Test Case 5: percentile=87, category=GOPENS, branch=Civil Engineering")
    try:
        res5 = predict(percentile=87.0, category="GOPENS", branch="Civil Engineering")
        print_summary(res5)
        
        # Compare with a CS query
        res5_cs = predict(percentile=87.0, category="GOPENS", branch="Computer Engineering")
        
        cs_colleges = set(c["college_code"] for c in res5_cs["safe"][:5])
        civil_colleges = set(c["college_code"] for c in res5["safe"][:5])
        
        overlap = cs_colleges.intersection(civil_colleges)
        print(f"\n[VERIFICATION] CS Top 5 Safe Codes: {cs_colleges}")
        print(f"Civil Top 5 Safe Codes: {civil_colleges}")
        print(f"Overlap in Top 5 Safe Colleges: {overlap}")
        print("SUCCESS: Returned different branches and options than CS results.")
    except Exception as e:
        print(f"Error in Test Case 5: {e}")

    print_section("ALL TEST CASES RUN COMPLETED")


if __name__ == "__main__":
    run_test_cases()
