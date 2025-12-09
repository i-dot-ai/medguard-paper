from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from medguard.data_ingest.models.patient_profile import PatientProfile


class ClinicalIssue(BaseModel):
    issue: str
    evidence: str
    intervention_required: bool

    @property
    def prompt(self) -> str:
        res = f"Issue: {self.issue}"
        res += f"\n\nEvidence: {self.evidence}"
        return res


class MedGuardAnalysis(BaseModel):
    patient_review: str
    clinical_issues: list[ClinicalIssue]
    intervention: str
    intervention_required: bool
    intervention_probability: float

    @property
    def prompt(self) -> str:
        res = f"Patient Review: {self.patient_review}"
        res += "\n\nClinical Issues:\n"
        res += "\n" + self.clinical_issue_prompt
        res += f"\n\nIntervention: {self.intervention}"
        res += f"\n\nIntervention Required: {self.intervention_required}"
        res += f"\n\nIntervention Probability: {self.intervention_probability}"
        return res

    @property
    def clinical_issue_prompt(self) -> str:
        # Only include issues that required an intervention
        res = "Clinical Issues:\n"
        for i, clinical_issue in enumerate(self.clinical_issues):
            if clinical_issue.intervention_required:
                res += f"\n{i + 1}. {clinical_issue.prompt}"
        return res

    @property
    def issue(self) -> bool:
        return len(self.clinical_issues) > 0


class IssueClassification(BaseModel):
    reasoning: str
    correct: bool


class ClassificationMatch(BaseModel):
    reasoning: str
    correct: bool
    match_id: int | None


class InterventionList(BaseModel):
    interventions: list[str]


class AgreementType(Enum):
    TP = "true-positive"
    FP = "false-positive"
    FN = "false-negative"
    TN = "true-negative"


class FailureReason(Enum):
    HALLUCINATION = "hallucination"
    KNOWLEDGE_GAP = "knowledge_gap"
    SAFETY_CRITICAL_OMISSION = "safety_critical_omission"
    NON_CRITICAL_OMISSION = "non_critical_omission"
    INPUT_PROCESSING_ERROR = "input_processing_error"
    REASONING_ERROR = "reasoning_error"
    QUANTITATIVE_ERROR = "quantitative_error"
    CONFIDENCE_CALIBRATION_ERROR = "confidence_calibration_error"
    GUIDELINE_NON_ADHERENCE = "guideline_non_adherence"
    REASONING = "reasoning"
    FOCUS = "focus"
    INCORRECT_GROUND_TRUTH = "incorrect_ground_truth"
    SAFETY = "safety"
    FACTS = "facts"
    PARTIAL_IDENTIFICATION = "partial_identification"


class FailureAnalysis(BaseModel):
    reasoning: str
    reason: FailureReason


class FailureAnalysisList(BaseModel):
    failure_analysis: list[FailureAnalysis]


class EvaluationAnalysis(BaseModel):
    issue_correct: bool
    intervention_correct: bool
    agreement_type: AgreementType
    intervention_analysis: IssueClassification | None
    failure_analysis: list[FailureAnalysis] | None = None
    issue_correct_list: list[IssueClassification] | list[ClassificationMatch] | None = None
    intervention_correct_list: list[IssueClassification] | list[ClassificationMatch] | None = None
    issue_precision: float | None = None
    issue_recall: float | None = None
    intervention_precision: float | None = None
    intervention_recall: float | None = None


class AnalysedPatientRecord(BaseModel):
    patient_link_id: int
    analysis_date: datetime
    medguard_analysis: MedGuardAnalysis
    evaluation_analysis: EvaluationAnalysis
    patient: PatientProfile | None = Field(default=None)
