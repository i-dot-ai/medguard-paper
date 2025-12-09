"""
One-off utility used to merge evaluation logs with patient profiles.

This script was used during data preparation to combine MedGuard analysis
outputs with original patient profiles. Requires access to internal
evaluation outputs and patient data.
"""

from medguard.evaluation.pipeline import (
    get_complete_patient_records,
    load_analysed_patient_records,
    load_patient_profiles,
)
from medguard.utils.parsing import save_pydantic_list_to_jsonl

if __name__ == "__main__":
    logs_path = "logs/2025-10-12T14-00-10+00-00_candm-augmented_BUT9ERsV6EUDwedyFnF75G.eval"
    patient_profiles_path = ".data/2025-10-12-patient-profiles-filters.jsonl"
    output_path = ".data/2025-10-12-complete-patient-records.jsonl"

    analysed_patient_records = load_analysed_patient_records(logs_path)
    patient_profiles = load_patient_profiles(patient_profiles_path)
    complete_patient_records = get_complete_patient_records(
        analysed_patient_records, patient_profiles
    )
    save_pydantic_list_to_jsonl(complete_patient_records, output_path)
