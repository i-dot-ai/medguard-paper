import json
from pathlib import Path

from medguard.data_ingest.record_to_sample import load_profile_json_to_pydantic
from medguard.scorer.models import AnalysedPatientRecord


class CombinedDataStore:
    def __init__(self):
        self.records: list[AnalysedPatientRecord] = []
        self.records_by_patient_id: dict[int, AnalysedPatientRecord] = {}

    def load_data(self, file_path: Path) -> None:
        lines = file_path.read_text().splitlines()

        for line in lines:
            record_dict = json.loads(line)
            record = self.load_single_record(record_dict)
            self.records.append(record)
            self.records_by_patient_id[record.patient_link_id] = record

    def load_single_record(self, record_dict: dict) -> AnalysedPatientRecord:
        patient_record = record_dict["patient"]

        record_dict["patient"] = None
        record = AnalysedPatientRecord(**record_dict)
        record.patient = load_profile_json_to_pydantic(patient_record)

        return record

    def get_all_patient_ids(self) -> list[int]:
        """Get list of all patient IDs."""
        return list(self.records_by_patient_id.keys())

    def get_patient_record(self, patient_id: int) -> AnalysedPatientRecord | None:
        """Get a specific patient record by ID."""
        return self.records_by_patient_id.get(patient_id)


combined_data_store = CombinedDataStore()
