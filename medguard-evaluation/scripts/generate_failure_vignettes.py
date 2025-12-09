#!/usr/bin/env python3
"""
Generate HTML and Markdown vignettes categorized by failure mode.

This script:
1. Loads evaluation data with clinician evaluations
2. Filters for patients with no data errors and ground truth
3. Categorizes each patient into one of 6 failure mode categories
4. Generates HTML vignettes with clinician feedback (individual files per patient)
5. Generates Markdown vignettes (individual files per patient)
6. Exports to category-specific folders
7. Creates a CSV index file

Usage:
    python scripts/generate_failure_vignettes.py --output-dir outputs/failure_vignettes
"""

import argparse
import csv
from pathlib import Path
from typing import Literal

from medguard.evaluation.evaluation import Evaluation, merge_evaluations
from medguard.evaluation.performance_metrics.ground_truth.performance_metrics import (
    GroundTruthPerformanceMetrics,
    analysis_data_to_performance_metrics,
)
from medguard.utils.parsing import load_pydantic_from_json
from medguard.vignette.html_generator import save_vignette_with_feedback_html
from medguard.vignette.markdown_generator import generate_markdown_from_vignette_with_feedback
from medguard.vignette.pipeline import generate_vignette_with_feedback

FailureCategory = Literal[
    "01_l1_false_negative",
    "02_l1_false_positive",
    "03_l2_issues_incorrect",
    "04_l2_issues_partially_correct",
    "05_l3_intervention_partially_correct",
    "06_l3_intervention_incorrect",
]


def categorize_patient(metrics: GroundTruthPerformanceMetrics) -> FailureCategory | None:
    """
    Categorize a patient into one of the 6 failure modes based on their metrics.

    Returns None if the patient doesn't fall into any failure category (e.g., success or TN).
    """
    # L1 False Negative: Positive GT, no issue identified
    if metrics.positive and metrics.positive_no_issue:
        return "01_l1_false_negative"

    # L1 False Positive: Negative GT, issue identified
    if metrics.negative and metrics.negative_any_issue:
        return "02_l1_false_positive"

    # L2 Issues Incorrect: Positive GT, any issue identified, no correct issues
    if metrics.positive and metrics.positive_any_issue and metrics.positive_no_correct:
        return "03_l2_issues_incorrect"

    # L2 Issues Partially Correct: Positive GT, some correct issues
    if metrics.positive and metrics.positive_some_correct:
        return "04_l2_issues_partially_correct"

    # L3 Intervention Partially Correct
    has_partial_intervention = (
        metrics.all_correct_partial_intervention or metrics.some_correct_partial_intervention
    )
    if has_partial_intervention:
        return "05_l3_intervention_partially_correct"

    # L3 Intervention Incorrect
    has_incorrect_intervention = (
        metrics.all_correct_incorrect_intervention or metrics.some_correct_incorrect_intervention
    )
    if has_incorrect_intervention:
        return "06_l3_intervention_incorrect"

    # Not a failure mode (success or true negative)
    return None


def get_category_description(category: FailureCategory) -> str:
    """Get a human-readable description for each failure category."""
    descriptions = {
        "01_l1_false_negative": "Level 1 False Negative",
        "02_l1_false_positive": "Level 1 False Positive",
        "03_l2_issues_incorrect": "Level 2 Issues Incorrect",
        "04_l2_issues_partially_correct": "Level 2 Issues Partially Correct",
        "05_l3_intervention_partially_correct": "Level 3 Intervention Partially Correct",
        "06_l3_intervention_incorrect": "Level 3 Intervention Incorrect",
    }
    return descriptions[category]


def main():
    parser = argparse.ArgumentParser(description="Generate failure vignettes by category")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/failure_vignettes"),
        help="Output directory for vignettes (default: outputs/failure_vignettes)",
    )

    args = parser.parse_args()

    evaluation_200 = load_pydantic_from_json(
        Evaluation, "outputs/20251018/test-set/evaluation.json"
    )
    evaluation_100 = load_pydantic_from_json(
        Evaluation, "outputs/20251027/no-filters/evaluation.json"
    )
    evaluation: Evaluation = merge_evaluations([evaluation_100, evaluation_200])
    evaluation = evaluation.clean()

    # Get patients with clinician evaluations (ground truth)
    all_patient_ids = evaluation.patient_ids()
    print(f"Found {len(all_patient_ids)} patients with clinician evaluations and no data errors")

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Create category directories
    category_dirs = {
        "01_l1_false_negative": args.output_dir / "01_l1_false_negative",
        "02_l1_false_positive": args.output_dir / "02_l1_false_positive",
        "03_l2_issues_incorrect": args.output_dir / "03_l2_issues_incorrect",
        "04_l2_issues_partially_correct": args.output_dir / "04_l2_issues_partially_correct",
        "05_l3_intervention_partially_correct": args.output_dir
        / "05_l3_intervention_partially_correct",
        "06_l3_intervention_incorrect": args.output_dir / "06_l3_intervention_incorrect",
    }

    for category_dir in category_dirs.values():
        category_dir.mkdir(parents=True, exist_ok=True)

    # Process each patient
    csv_rows = []
    category_counts = {cat: 0 for cat in category_dirs.keys()}

    print("\nProcessing patients...")
    for i, patient_id in enumerate(all_patient_ids, 1):
        if i % 10 == 0:
            print(f"  Processed {i}/{len(all_patient_ids)} patients...")

        # Get data for this patient (guaranteed to exist after filtering)
        record = evaluation.analysed_records_dict_last[patient_id]
        clinician_eval = evaluation.clinician_evaluations_dict[patient_id]
        patient_profile = record.patient

        # If the patient_profile doesn't have a sample date, add it
        if patient_profile.sample_date is None:
            patient_profile.sample_date = record.analysis_date

        # Get metrics for this patient
        metrics = analysis_data_to_performance_metrics(clinician_eval)

        # Categorize patient
        category = categorize_patient(metrics)

        if category is None:
            # Not a failure mode - skip (success or true negative)
            continue

        # Generate vignette with feedback
        vignette = generate_vignette_with_feedback(
            patient_profile, record.medguard_analysis, clinician_eval
        )

        # Save HTML to appropriate folder
        html_path = category_dirs[category] / f"{vignette.patient_id_hash[:16]}.html"
        save_vignette_with_feedback_html(vignette, html_path)

        # Save individual markdown file to appropriate folder
        md_path = category_dirs[category] / f"{vignette.patient_id_hash[:16]}.md"
        vignette_md = generate_markdown_from_vignette_with_feedback(vignette)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(vignette_md)

        # Add to CSV index
        csv_rows.append(
            {
                "patient_id": patient_id,
                "patient_id_hash": vignette.patient_id_hash[:16],
                "category": category,
                "description": get_category_description(category),
                "html_file": f"{category}/{vignette.patient_id_hash[:16]}.html",
                "markdown_file": f"{category}/{vignette.patient_id_hash[:16]}.md",
            }
        )

        category_counts[category] += 1

    # Save CSV index
    csv_path = args.output_dir / "vignettes_index.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "patient_id",
                "patient_id_hash",
                "category",
                "description",
                "html_file",
                "markdown_file",
            ],
        )
        writer.writeheader()
        writer.writerows(csv_rows)

    # Print summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total patients with ground truth (no data errors): {len(all_patient_ids)}")
    print(f"Failure vignettes generated: {len(csv_rows)}")
    print(f"Success/True Negative cases (not exported): {len(all_patient_ids) - len(csv_rows)}")
    print()
    print("Breakdown by failure category:")
    for category, count in category_counts.items():
        if count > 0:
            desc = get_category_description(category)
            print(f"  {category}: {count:3d} - {desc}")
    print()
    print(f"✓ Output directory: {args.output_dir.absolute()}")
    print(f"✓ CSV index: {csv_path.absolute()}")
    print(f"✓ Generated {len(csv_rows)} HTML and Markdown files (one per patient)")


if __name__ == "__main__":
    main()
