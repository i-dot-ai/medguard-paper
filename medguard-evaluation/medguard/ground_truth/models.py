from datetime import datetime
from pydantic import BaseModel


class GroundTruthAssessment(BaseModel):
    reasoning: str
    issues: list[str]
    intervention: list[str]
    notes: list[str]


class GroundTruthAssessmentFull(GroundTruthAssessment):
    internal_reasoning: str
    patient_id: str
    assessment_date: datetime
