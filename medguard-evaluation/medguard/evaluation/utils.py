"""Utility functions for loading patient records and profiles."""

import json

from medguard.data_ingest import PatientProfile, load_profile_json_to_pydantic
from medguard.scorer.models import AnalysedPatientRecord


def load_patient_profiles_from_jsonl(path: str) -> list[PatientProfile]:
    with open(path, "r") as f:
        lines = f.readlines()

    patient_profiles = []
    for line in lines:
        try:
            patient_profiles.append(load_profile_json_to_pydantic(json.loads(line)))
        except Exception as e:
            print(f"Error loading patient profile: {e}")

    return patient_profiles


def load_analysed_patient_records_from_jsonl(path: str) -> list[AnalysedPatientRecord]:
    with open(path, "r") as f:
        lines = f.readlines()

    analysed_patient_records = []

    for line in lines:
        record_dict = json.loads(line)
        patient_dict = record_dict["patient"]
        record_dict["patient"] = None
        analysed_patient_record = AnalysedPatientRecord.model_validate(record_dict)
        analysed_patient_record.patient = load_profile_json_to_pydantic(patient_dict)
        analysed_patient_records.append(analysed_patient_record)

    return analysed_patient_records
