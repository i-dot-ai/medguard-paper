from pydantic import BaseModel


class Stage1Data(BaseModel):
    determination_possible: bool
    determination_possible_reasoning: str


class Stage2Data(BaseModel):
    data_error: bool
    data_error_explanation: str | None

    agrees_with_rules: str | None
    rules_assessment_reasoning: str | None
    medguard_identified_rule_issues: str | None
    medguard_addressed_rule_issues: str | None

    issue_assessments: list[bool]
    issue_reasoning: list[str]

    missed_issues: str
    missed_issues_detail: str

    medguard_specific_intervention: str
    medguard_specific_intervention_reasoning: str

    intervention_should_be: str
    failure_modes: list[str]
    failure_mode_explanations: dict[str, str]

    @property
    def issue(self) -> bool:
        return any(self.issue_assessments) or self.missed_issues == "yes"

    @property
    def score_issue_precision(self) -> float:
        return (
            sum(self.issue_assessments) / len(self.issue_assessments)
            if len(self.issue_assessments) > 0
            else 1
        )

    @property
    def score_issue_recall(self) -> float:
        # Return 1 if no missed issues, otherwise 0.5 if missed issues but have correct issues, otherwise 0
        if self.missed_issues == "no":
            return 1.0
        elif self.missed_issues == "yes" and any(self.issue_assessments):
            return 0.4
        else:
            return 0

    @property
    def score_intervention(self) -> float:
        # We cannot distinguish between intervention precision and recall, so choose to return the intervention score based on the overall agreement
        if self.medguard_specific_intervention == "yes":
            return 1.0
        elif self.medguard_specific_intervention == "partial":
            return 0.4
        else:
            return 0.0

    @property
    def score(self) -> float:
        f1_score = (
            2
            * self.score_issue_precision
            * self.score_issue_recall
            / (self.score_issue_precision + self.score_issue_recall)
            if (self.score_issue_precision + self.score_issue_recall) > 0
            else None
        )

        if f1_score:
            return 0.5 * (self.score_intervention + f1_score)
        else:
            return self.score_intervention


class AnalysisData(BaseModel):
    patient_id: int
    stage1: Stage1Data
    stage2: Stage2Data | None
