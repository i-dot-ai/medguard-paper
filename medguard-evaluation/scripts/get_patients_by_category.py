"""
Helper script to get patient IDs by failure mode category.

Usage:
    python scripts/get_patients_by_category.py --category "duplicate prescription errors"
    python scripts/get_patients_by_category.py --category "nuance/end-of-life"
    python scripts/get_patients_by_category.py --all
"""

import argparse
import polars as pl


def main():
    parser = argparse.ArgumentParser(description="Get patient IDs by failure mode category")
    parser.add_argument("--category", type=str, help="Category to filter by")
    parser.add_argument("--all", action="store_true", help="Show all categories with patient IDs")
    args = parser.parse_args()

    # Load CSV
    df = pl.read_csv(
        "outputs/failure_vignettes/vignettes_index_annotated.csv", encoding="utf8-lossy"
    )

    if args.all:
        # Show all categories
        categories = [
            "duplicate prescription errors",
            "too-aggressive",
            "too-aggressive/gradual-taper",
            "understanding-drug-context",
            "further-information",
            "further-information/iron-studies",
            "nuance",
            "nuance/end-of-life",
            "nuance/already-tolerated",
            "hallucination",
            "hallucination/drug-component",
            "clinician-context",
            "incorrect-understanding-guidelines",
            "missed-deprescription-opportunity",
            "missed-issue",
            "overly-cautious",
        ]

        for cat in categories:
            if cat in df.columns:
                patients = (
                    df.filter(pl.col(cat) == "Y")
                    .select("patient_id_hash")["patient_id_hash"]
                    .to_list()
                )
                if patients:
                    print(f"\n{cat} (n={len(patients)}):")
                    for p in patients:
                        print(f"  {p}")
    else:
        if not args.category:
            print("Error: Must specify --category or --all")
            return

        if args.category not in df.columns:
            print(f"Error: Category '{args.category}' not found")
            print(
                f"Available categories: {[c for c in df.columns if c not in ['patient_id_hash', 'failure_mode', 'level', 'dataset', 'category', 'description', 'Count']]}"
            )
            return

        patients = df.filter(pl.col(args.category) == "Y").select(
            ["patient_id_hash", "level", "description"]
        )
        print(f"\n{args.category} (n={patients.height}):")
        print(patients)


if __name__ == "__main__":
    main()
