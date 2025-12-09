import random

from inspect_ai.log import read_eval_log_samples

from medguard.data_ingest import PatientProfile
from medguard.scorer.models import AnalysedPatientRecord


def load_analysed_patient_records_from_eval_log(
    path: str, n_negative: int | None = None, n_positive: int | None = None
) -> list[AnalysedPatientRecord]:
    results = read_eval_log_samples(path, all_samples_required=False)

    results = [
        result
        for result in results
        if result.scores.get("llm_as_a_judge").metadata["medguard_analysis"] is not None
    ]

    # If no filtering requested, return all records
    if n_negative is None and n_positive is None:
        return [
            AnalysedPatientRecord.model_validate(item.scores["llm_as_a_judge"].metadata)
            for item in results
            if item.scores.get("llm_as_a_judge", None) is not None
        ]

    # Separate records by score value
    negative_records = []
    positive_records = []

    for item in results:
        if item.scores.get("llm_as_a_judge", None) is not None:
            record = AnalysedPatientRecord.model_validate(item.scores["llm_as_a_judge"].metadata)
            if item.scores["llm_as_a_judge"].value == 0:
                negative_records.append(record)
            elif item.scores["llm_as_a_judge"].value == 1:
                positive_records.append(record)

    # Apply filtering
    filtered_records = []
    if n_negative is not None:
        filtered_records.extend(negative_records[:n_negative])
    else:
        filtered_records.extend(negative_records)

    if n_positive is not None:
        filtered_records.extend(positive_records[:n_positive])
    else:
        filtered_records.extend(positive_records)

    # Randomly shuffle the results
    random.shuffle(filtered_records)

    return filtered_records


def add_patient_profiles_to_analysed_patient_records(
    analysed_patient_records: list[AnalysedPatientRecord], patient_profiles: list[PatientProfile]
) -> list[AnalysedPatientRecord]:
    patient_profiles_by_id = {}

    for profile in patient_profiles:
        patient_profiles_by_id[profile.patient_link_id] = profile

    for record in analysed_patient_records:
        if record.patient_link_id in patient_profiles_by_id:
            record.patient = patient_profiles_by_id[record.patient_link_id]

    return analysed_patient_records
