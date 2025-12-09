from pathlib import Path

from medguard.evaluation.evaluation import Evaluation, merge_evaluations
from medguard.utils.parsing import load_pydantic_from_json, save_pydantic_list_to_jsonl
from medguard.vignette.html_generator import save_vignette_with_feedback_html
from medguard.vignette.models import PatientVignetteWithFeedback
from medguard.vignette.pipeline import generate_vignette_with_feedback


def main():
    # Load and merge evaluations to get 300 patients
    print("Loading evaluations...")
    evaluation_200 = load_pydantic_from_json(
        Evaluation, "outputs/20251018/test-set/evaluation.json"
    )
    evaluation_100 = load_pydantic_from_json(
        Evaluation, "outputs/20251027/no-filters/evaluation.json"
    )
    print(f"   - Loaded {len(evaluation_200.patient_ids())} from test-set")
    print(f"   - Loaded {len(evaluation_100.patient_ids())} from no-filters")

    evaluation = merge_evaluations([evaluation_100, evaluation_200])
    print(f"   - Merged: {len(evaluation.patient_ids())} patients total")

    evaluation = evaluation.clean()
    print(f"   - After cleaning: {len(evaluation.patient_ids())} patients")

    # Get all patient IDs with ground truth
    all_patient_ids = evaluation.patient_ids()

    vignettes: list[PatientVignetteWithFeedback] = []

    for patient_id in all_patient_ids:
        # Get the last analysed record for this patient
        if patient_id not in evaluation.analysed_records_dict_last:
            print(f"Skipping patient {patient_id}: no analysed record")
            continue

        record = evaluation.analysed_records_dict_last[patient_id]

        # Get clinician feedback
        if patient_id not in evaluation.clinician_evaluations_dict:
            print(f"Skipping patient {patient_id}: no clinician feedback")
            continue

        clinician_feedback = evaluation.clinician_evaluations_dict[patient_id]

        # Get patient profile
        if not record.patient:
            print(f"Skipping patient {patient_id}: no patient profile in record")
            continue

        if not record.patient.sample_date:
            record.patient.sample_date = record.analysis_date

        # Generate vignette with feedback
        vignette = generate_vignette_with_feedback(
            record.patient, record.medguard_analysis, clinician_feedback
        )
        vignettes.append(vignette)

    print(f"\n✓ Generated {len(vignettes)} vignettes with feedback")

    # Save vignettes as JSONL
    output_dir = Path("outputs/vignettes")
    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = output_dir / "2025-11-06-vignettes-with-feedback.jsonl"
    save_pydantic_list_to_jsonl(vignettes, str(jsonl_path))
    print(f"✓ Saved JSONL to {jsonl_path}")

    # Save vignettes as HTML
    html_dir = output_dir / "html_with_feedback"
    html_dir.mkdir(parents=True, exist_ok=True)

    print("\nGenerating HTML files...")
    for i, vignette in enumerate(vignettes, 1):
        html_path = html_dir / f"{vignette.patient_id_hash[:16]}.html"
        save_vignette_with_feedback_html(vignette, html_path)

        if i % 50 == 0:
            print(f"  Generated {i}/{len(vignettes)} HTML files...")

    print(f"✓ Saved {len(vignettes)} HTML files to {html_dir}")


if __name__ == "__main__":
    main()
