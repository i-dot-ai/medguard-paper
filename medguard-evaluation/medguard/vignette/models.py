from pydantic import BaseModel
from enum import Enum
from typing import Optional
from medguard.evaluation.clinician.models import Stage2Data


class Sex(str, Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"
    UNKNOWN = "U"


class Prescription(BaseModel):
    active_at_review: bool
    days_since_start: int
    days_since_end: int
    description: Optional[str]
    dosage: Optional[str]
    units: Optional[str]
    is_repeat_medication: Optional[bool]


class ClinicalIssue(BaseModel):
    issue: str
    evidence: str
    intervention_required: bool


class PatientVignette(BaseModel):
    patient_id_hash: str
    age: int
    sex: Sex
    imd_percentile: float
    frailty_score: float
    qof_registers: list[str]
    frailty_deficit_list: list[str]
    prescriptions: list[Prescription]

    medguard_patient_review: str
    medguard_clinical_issues: list[ClinicalIssue]
    medguard_intervention: str
    medguard_intervention_required: bool
    medguard_intervention_probability: float


class PatientVignetteWithFeedback(PatientVignette):
    clinician_feedback: Stage2Data
