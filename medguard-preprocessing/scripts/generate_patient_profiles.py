from medguard.data_processor import ModularPatientDataProcessor
from medguard.utils import export_pydantic_to_jsonl
from datetime import datetime


def main():
    processor = ModularPatientDataProcessor()

    profiles = processor.build_patient_profiles(
        sample_strategy="balanced_smr_snomed",
        limit=100,
        to_pydantic_model=True,
    )

    export_pydantic_to_jsonl(
        profiles,
        output_path=f"outputs/{datetime.now().strftime('%Y-%m-%d')}-patient_sample_balanced_snomed.jsonl",
    )

    profiles = processor.build_patient_profiles(
        sample_strategy="balanced_smr_medication_changes",
        limit=100,
        to_pydantic_model=True,
    )

    export_pydantic_to_jsonl(
        profiles,
        output_path=f"outputs/{datetime.now().strftime('%Y-%m-%d')}-patient_sample_balanced_changes.jsonl",
    )


if __name__ == "__main__":
    main()
