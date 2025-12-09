from pathlib import Path

from medguard.evaluation.evaluation import Evaluation, merge_evaluations
from medguard.utils.parsing import load_pydantic_from_json, save_pydantic_list_to_jsonl
from medguard.vignette.html_generator import save_vignette_html
from medguard.vignette.pipeline import generate_vignette


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

    print("\nGenerating vignettes...")
    vignettes = []
    for record in evaluation.analysed_records:
        if not record.patient.sample_date:
            record.patient.sample_date = record.analysis_date
        res = generate_vignette(record.patient, record.medguard_analysis)
        vignettes.append(res)

    print(f"\n✓ Generated {len(vignettes)} vignettes")

    # Save vignettes as JSONL
    output_dir = Path("outputs/vignettes")
    output_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = output_dir / "2025-10-29-vignettes.jsonl"
    save_pydantic_list_to_jsonl(vignettes, str(jsonl_path))
    print(f"✓ Saved JSONL to {jsonl_path}")

    # Save vignettes as HTML
    html_dir = output_dir / "html"
    html_dir.mkdir(parents=True, exist_ok=True)

    print("\nGenerating HTML files...")
    for i, vignette in enumerate(vignettes, 1):
        html_path = html_dir / f"{vignette.patient_id_hash[:16]}.html"
        save_vignette_html(vignette, html_path)

        if i % 50 == 0:
            print(f"  Generated {i}/{len(vignettes)} HTML files...")

    print(f"✓ Saved {len(vignettes)} HTML files to {html_dir}")


if __name__ == "__main__":
    main()
