import plotly.graph_objects as go
from pydantic import BaseModel, model_validator

from .sankey import generate_binary_sankey_figure, generate_full_sankey_figure
from medguard.scorer.models import AnalysedPatientRecord
from medguard.evaluation.clinician.models import Stage2Data


class FilterPerformanceMetrics(BaseModel):
    positive_gt: int

    positive_gt_any_issue: int
    positive_gt_no_issue: int

    positive_gt_correct_issue: int
    positive_gt_incorrect_issue: int

    positive_gt_correct_intervention: int
    positive_gt_incorrect_intervention: int

    negative_gt: int
    negative_gt_any_issue: int
    negative_gt_no_issue: int

    @property
    def TP(self) -> int:
        return self.positive_gt_any_issue

    @property
    def FP(self) -> int:
        return self.negative_gt_any_issue

    @property
    def TN(self) -> int:
        return self.negative_gt_no_issue

    @property
    def FN(self) -> int:
        return self.positive_gt_no_issue

    @model_validator(mode="after")
    def validate_sums(self) -> "FilterPerformanceMetrics":
        """Validate that parent values equal the sum of their children."""

        # Positive GT should equal the sum of any_issue and no_issue
        if self.positive_gt != self.positive_gt_any_issue + self.positive_gt_no_issue:
            raise ValueError(
                f"positive_gt ({self.positive_gt}) must equal "
                f"positive_gt_any_issue ({self.positive_gt_any_issue}) + "
                f"positive_gt_no_issue ({self.positive_gt_no_issue})"
            )

        # Positive GT any_issue should equal correct + incorrect issue
        if (
            self.positive_gt_any_issue
            != self.positive_gt_correct_issue + self.positive_gt_incorrect_issue
        ):
            raise ValueError(
                f"positive_gt_any_issue ({self.positive_gt_any_issue}) must equal "
                f"positive_gt_correct_issue ({self.positive_gt_correct_issue}) + "
                f"positive_gt_incorrect_issue ({self.positive_gt_incorrect_issue})"
            )

        # Positive GT correct_issue should equal correct + incorrect intervention
        if (
            self.positive_gt_correct_issue
            != self.positive_gt_correct_intervention + self.positive_gt_incorrect_intervention
        ):
            raise ValueError(
                f"positive_gt_correct_issue ({self.positive_gt_correct_issue}) must equal "
                f"positive_gt_correct_intervention ({self.positive_gt_correct_intervention}) + "
                f"positive_gt_incorrect_intervention ({self.positive_gt_incorrect_intervention})"
            )

        # Negative GT should equal the sum of any_issue and no_issue
        if self.negative_gt != self.negative_gt_any_issue + self.negative_gt_no_issue:
            raise ValueError(
                f"negative_gt ({self.negative_gt}) must equal "
                f"negative_gt_any_issue ({self.negative_gt_any_issue}) + "
                f"negative_gt_no_issue ({self.negative_gt_no_issue})"
            )

        return self

    def generate_full_sankey_figure(self) -> go.Figure:
        return generate_full_sankey_figure(self)

    def generate_binary_sankey_figure(self) -> go.Figure:
        return generate_binary_sankey_figure(self)


def get_performance_metrics_from_analysed_patient_record(
    record: AnalysedPatientRecord,
) -> FilterPerformanceMetrics:
    # Positive GT
    positive_gt = False if len(record.patient.matched_filters) == 0 else True

    # Positive GT Any Issue
    any_issue = (
        len(
            [
                issue
                for issue in record.medguard_analysis.clinical_issues
                if issue.intervention_required
            ]
        )
        > 0
    )
    positive_gt_any_issue = positive_gt and any_issue

    # Positive GT No Issue
    positive_gt_no_issue = positive_gt and not any_issue

    # Positive GT Correct Issue
    issue_correct = record.evaluation_analysis.issue_correct
    positive_gt_correct_issue = positive_gt and positive_gt_any_issue and issue_correct

    # Positive GT Incorrect Issue
    positive_gt_incorrect_issue = positive_gt and positive_gt_any_issue and not issue_correct

    # Positive GT Correct Intervention
    intervention_correct = record.evaluation_analysis.intervention_correct
    positive_gt_correct_intervention = (
        positive_gt and positive_gt_any_issue and positive_gt_correct_issue and intervention_correct
    )

    # Positive GT Incorrect Intervention
    positive_gt_incorrect_intervention = (
        positive_gt
        and positive_gt_any_issue
        and positive_gt_correct_issue
        and not intervention_correct
    )

    # Negative GT
    negative_gt = not positive_gt

    # Negative GT Any Issue
    negative_gt_any_issue = negative_gt and any_issue

    # Negative GT No Issue
    negative_gt_no_issue = negative_gt and not any_issue

    return FilterPerformanceMetrics(
        positive_gt=++positive_gt,
        positive_gt_any_issue=++positive_gt_any_issue,
        positive_gt_no_issue=++positive_gt_no_issue,
        positive_gt_correct_issue=++positive_gt_correct_issue,
        positive_gt_incorrect_issue=++positive_gt_incorrect_issue,
        positive_gt_correct_intervention=++positive_gt_correct_intervention,
        positive_gt_incorrect_intervention=++positive_gt_incorrect_intervention,
        negative_gt=++negative_gt,
        negative_gt_any_issue=++negative_gt_any_issue,
        negative_gt_no_issue=++negative_gt_no_issue,
    )


def analysed_patient_records_to_performance_metrics(
    analysed_patient_records: list[AnalysedPatientRecord],
) -> FilterPerformanceMetrics:
    individual_sankey_data = [
        get_performance_metrics_from_analysed_patient_record(record)
        for record in analysed_patient_records
    ]

    return FilterPerformanceMetrics(
        positive_gt=sum(record.positive_gt for record in individual_sankey_data),
        positive_gt_any_issue=sum(
            record.positive_gt_any_issue for record in individual_sankey_data
        ),
        positive_gt_no_issue=sum(record.positive_gt_no_issue for record in individual_sankey_data),
        positive_gt_correct_issue=sum(
            record.positive_gt_correct_issue for record in individual_sankey_data
        ),
        positive_gt_incorrect_issue=sum(
            record.positive_gt_incorrect_issue for record in individual_sankey_data
        ),
        positive_gt_correct_intervention=sum(
            record.positive_gt_correct_intervention for record in individual_sankey_data
        ),
        positive_gt_incorrect_intervention=sum(
            record.positive_gt_incorrect_intervention for record in individual_sankey_data
        ),
        negative_gt=sum(record.negative_gt for record in individual_sankey_data),
        negative_gt_any_issue=sum(
            record.negative_gt_any_issue for record in individual_sankey_data
        ),
        negative_gt_no_issue=sum(record.negative_gt_no_issue for record in individual_sankey_data),
    )


def get_performance_metrics_from_stage2data(
    stage2: Stage2Data,
) -> FilterPerformanceMetrics | None:
    # We're only interested in Positive GT cases with no data errors where Lauren agrees with the rules
    positive_gt = (
        any(stage2.issue_assessments) or stage2.missed_issues == "yes"
    ) and stage2.agrees_with_rules == "yes"
    no_data_errors = not stage2.data_error

    if not (no_data_errors):
        return None

    # Positive GT

    any_issue = len(stage2.issue_assessments) > 0

    positive_gt_any_issue = positive_gt and any_issue

    # Positive GT No Issue
    positive_gt_no_issue = positive_gt and not any_issue

    # Positive GT Correct Issue
    issue_correct = stage2.medguard_identified_rule_issues == "yes"
    positive_gt_correct_issue = positive_gt and positive_gt_any_issue and issue_correct

    # Positive GT Incorrect Issue
    positive_gt_incorrect_issue = positive_gt and positive_gt_any_issue and not issue_correct

    # Positive GT Correct Intervention
    intervention_correct = stage2.medguard_addressed_rule_issues == "yes"
    positive_gt_correct_intervention = (
        positive_gt and positive_gt_any_issue and positive_gt_correct_issue and intervention_correct
    )

    # Positive GT Incorrect Intervention
    positive_gt_incorrect_intervention = (
        positive_gt
        and positive_gt_any_issue
        and positive_gt_correct_issue
        and not intervention_correct
    )

    # Negative GT
    negative_gt = (
        len(stage2.issue_assessments) == 0 or all([not x for x in stage2.issue_assessments])
    ) and stage2.missed_issues == "no"

    # Negative GT Any Issue
    negative_gt_any_issue = negative_gt and any_issue

    # Negative GT No Issue
    negative_gt_no_issue = negative_gt and not any_issue

    return FilterPerformanceMetrics(
        positive_gt=++positive_gt,
        positive_gt_any_issue=++positive_gt_any_issue,
        positive_gt_no_issue=++positive_gt_no_issue,
        positive_gt_correct_issue=++positive_gt_correct_issue,
        positive_gt_incorrect_issue=++positive_gt_incorrect_issue,
        positive_gt_correct_intervention=++positive_gt_correct_intervention,
        positive_gt_incorrect_intervention=++positive_gt_incorrect_intervention,
        negative_gt=++negative_gt,
        negative_gt_any_issue=++negative_gt_any_issue,
        negative_gt_no_issue=++negative_gt_no_issue,
    )


def stage2datas_to_performance_metrics(
    stage2datas: list[Stage2Data],
) -> FilterPerformanceMetrics:
    individual_sankey_data = [
        result
        for record in stage2datas
        if (result := get_performance_metrics_from_stage2data(record)) is not None
    ]

    return FilterPerformanceMetrics(
        positive_gt=sum(record.positive_gt for record in individual_sankey_data),
        positive_gt_any_issue=sum(
            record.positive_gt_any_issue for record in individual_sankey_data
        ),
        positive_gt_no_issue=sum(record.positive_gt_no_issue for record in individual_sankey_data),
        positive_gt_correct_issue=sum(
            record.positive_gt_correct_issue for record in individual_sankey_data
        ),
        positive_gt_incorrect_issue=sum(
            record.positive_gt_incorrect_issue for record in individual_sankey_data
        ),
        positive_gt_correct_intervention=sum(
            record.positive_gt_correct_intervention for record in individual_sankey_data
        ),
        positive_gt_incorrect_intervention=sum(
            record.positive_gt_incorrect_intervention for record in individual_sankey_data
        ),
        negative_gt=sum(record.negative_gt for record in individual_sankey_data),
        negative_gt_any_issue=sum(
            record.negative_gt_any_issue for record in individual_sankey_data
        ),
        negative_gt_no_issue=sum(record.negative_gt_no_issue for record in individual_sankey_data),
    )
