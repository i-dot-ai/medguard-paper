from pathlib import Path

from medguard.evaluation.utils import load_analysed_patient_records_from_jsonl
from medguard.scorer.models import AnalysedPatientRecord
from medguard.utils.parsing import save_pydantic_list_to_jsonl

from .patient_profile import sanitise_patient_profile


def sanitise_analysed_patient_record(record: AnalysedPatientRecord):
    if record.patient:
        record.patient = sanitise_patient_profile(record.patient)

    return record


def sanitise_analysed_patient_records(records: list[AnalysedPatientRecord]):
    return [sanitise_analysed_patient_record(x) for x in records]


def run_sanitise_analysed_patient_record(input_path: Path, output_path: Path):
    # Load the analysed patient records

    records = load_analysed_patient_records_from_jsonl(input_path)

    # Sanitise them
    sanitised_records = sanitise_analysed_patient_records(records)

    # Save it
    save_pydantic_list_to_jsonl(sanitised_records, output_path)
