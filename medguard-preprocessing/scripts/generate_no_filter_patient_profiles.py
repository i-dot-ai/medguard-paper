"""
Generate patient profiles for patients who do NOT match any PINCER filters.

This script samples N patients who are not flagged by any of the 10 PINCER
medication safety filters, then builds their full patient profiles.
"""

from datetime import datetime

from medguard.data_processor import ModularPatientDataProcessor
from medguard.utils import export_pydantic_to_jsonl


def main():
    # Configuration
    n_patients = 1000  # Number of patients to sample

    processor = ModularPatientDataProcessor()

    print(f"Sampling {n_patients} patients who do NOT match any PINCER filters...")
    print("This will first run all 10 filters to identify patients to exclude...")

    # Sample patients who DON'T match any filters
    patient_ids = processor.get_patient_sample(
        sample_strategy="no_filter",
        limit=n_patients,
        offset=0,
        include_deceased=False,
        seed=0.42,
    )

    print(f"\nFound {len(patient_ids)} eligible patients")

    if not patient_ids:
        print("No patients found. Exiting.")
        return

    # Build patient profiles
    print("Building patient profiles...")
    profiles = processor.build_patient_profiles_from_ids(
        patient_ids=patient_ids,
        to_pydantic_model=True,
    )

    print(f"Built {len(profiles)} patient profiles")

    # Export to JSONL
    timestamp = datetime.now().strftime("%Y-%m-%d")
    actual_sample_size = len(profiles)
    output_path = (
        f"outputs/{timestamp}-patient_profiles_no_filter_n{actual_sample_size}.jsonl"
    )

    export_pydantic_to_jsonl(profiles, output_path=output_path)
    print(f"\nExported to: {output_path}")


if __name__ == "__main__":
    main()
