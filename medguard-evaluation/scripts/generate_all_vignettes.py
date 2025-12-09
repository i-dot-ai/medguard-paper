"""
Generate HTML files for all patient vignettes.
"""

from pathlib import Path
from medguard.utils.parsing import load_pydantic_list_from_jsonl
from medguard.vignette.models import PatientVignette
from medguard.vignette.html_generator import save_vignette_html


def main():
    # Load vignettes
    vignettes_path = "outputs/vignettes/2025-10-29-vignettes.jsonl"
    print(f"Loading vignettes from {vignettes_path}...")
    vignettes = load_pydantic_list_from_jsonl(PatientVignette, vignettes_path)
    print(f"Loaded {len(vignettes)} vignettes")

    # Create output directory
    output_dir = Path("outputs/vignettes/html")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate HTML for all vignettes
    print(f"\nGenerating HTML files...")
    for i, vignette in enumerate(vignettes, 1):
        output_path = output_dir / f"vignette_{vignette.patient_id_hash[:8]}.html"
        save_vignette_html(vignette, output_path)

        if i % 10 == 0:
            print(f"  Generated {i}/{len(vignettes)} files...")

    print(f"\n✓ Successfully generated {len(vignettes)} HTML files")
    print(f"  Output directory: {output_dir.absolute()}")

    # Print some statistics
    print(f"\nStatistics:")
    intervention_required = sum(1 for v in vignettes if v.medguard_intervention_required)
    print(
        f"  Vignettes with intervention required: {intervention_required} ({intervention_required / len(vignettes) * 100:.1f}%)"
    )
    print(
        f"  Vignettes without intervention: {len(vignettes) - intervention_required} ({(len(vignettes) - intervention_required) / len(vignettes) * 100:.1f}%)"
    )


if __name__ == "__main__":
    main()
