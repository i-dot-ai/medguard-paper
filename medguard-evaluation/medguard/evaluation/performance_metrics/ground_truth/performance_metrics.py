from medguard.evaluation.clinician.models import Stage2Data
from pydantic import BaseModel


class GroundTruthPerformanceMetrics(BaseModel):
    positive: int
    negative: int

    positive_any_issue: int
    positive_no_issue: int

    negative_any_issue: int
    negative_no_issue: int

    positive_all_correct: int
    positive_some_correct: int
    positive_no_correct: int

    all_correct_correct_intervention: int
    all_correct_partial_intervention: int
    all_correct_incorrect_intervention: int

    some_correct_correct_intervention: int
    some_correct_partial_intervention: int
    some_correct_incorrect_intervention: int


def analysis_data_to_performance_metrics(stage2: Stage2Data) -> GroundTruthPerformanceMetrics:
    positive = any(stage2.issue_assessments) or stage2.missed_issues == "yes"
    negative = not positive

    any_issue = len(stage2.issue_assessments) > 0

    positive_any_issue = positive and any_issue
    positive_no_issue = positive and not any_issue

    negative_any_issue = negative and any_issue
    negative_no_issue = negative and not any_issue

    positive_all_correct = (
        positive_any_issue and all(stage2.issue_assessments) and stage2.missed_issues == "no"
    )
    positive_some_correct = (
        positive_any_issue and any(stage2.issue_assessments) and not positive_all_correct
    )
    positive_no_correct = positive_any_issue and not any(stage2.issue_assessments)

    all_correct_correct_intervention = (
        positive_all_correct and stage2.medguard_specific_intervention == "yes"
    )
    all_correct_partial_intervention = (
        positive_all_correct and stage2.medguard_specific_intervention == "partial"
    )
    all_correct_incorrect_intervention = (
        positive_all_correct and stage2.medguard_specific_intervention == "no"
    )

    some_correct_correct_intervention = (
        positive_some_correct and stage2.medguard_specific_intervention == "yes"
    )
    some_correct_partial_intervention = (
        positive_some_correct and stage2.medguard_specific_intervention == "partial"
    )
    some_correct_incorrect_intervention = (
        positive_some_correct and stage2.medguard_specific_intervention == "no"
    )

    return GroundTruthPerformanceMetrics(
        positive=++positive,
        negative=++negative,
        positive_any_issue=++positive_any_issue,
        positive_no_issue=++positive_no_issue,
        negative_any_issue=++negative_any_issue,
        negative_no_issue=++negative_no_issue,
        positive_all_correct=++positive_all_correct,
        positive_some_correct=++positive_some_correct,
        positive_no_correct=++positive_no_correct,
        all_correct_correct_intervention=++all_correct_correct_intervention,
        all_correct_partial_intervention=++all_correct_partial_intervention,
        all_correct_incorrect_intervention=++all_correct_incorrect_intervention,
        some_correct_correct_intervention=++some_correct_correct_intervention,
        some_correct_partial_intervention=++some_correct_partial_intervention,
        some_correct_incorrect_intervention=++some_correct_incorrect_intervention,
    )


def get_full_performance_metrics(
    data: list[GroundTruthPerformanceMetrics],
) -> GroundTruthPerformanceMetrics:
    return GroundTruthPerformanceMetrics(
        positive=sum([x.positive for x in data]),
        negative=sum([x.negative for x in data]),
        positive_any_issue=sum([x.positive_any_issue for x in data]),
        positive_no_issue=sum([x.positive_no_issue for x in data]),
        negative_any_issue=sum([x.negative_any_issue for x in data]),
        negative_no_issue=sum([x.negative_no_issue for x in data]),
        positive_all_correct=sum([x.positive_all_correct for x in data]),
        positive_some_correct=sum([x.positive_some_correct for x in data]),
        positive_no_correct=sum([x.positive_no_correct for x in data]),
        all_correct_correct_intervention=sum([x.all_correct_correct_intervention for x in data]),
        all_correct_partial_intervention=sum([x.all_correct_partial_intervention for x in data]),
        all_correct_incorrect_intervention=sum(
            [x.all_correct_incorrect_intervention for x in data]
        ),
        some_correct_correct_intervention=sum([x.some_correct_correct_intervention for x in data]),
        some_correct_partial_intervention=sum([x.some_correct_partial_intervention for x in data]),
        some_correct_incorrect_intervention=sum(
            [x.some_correct_incorrect_intervention for x in data]
        ),
    )


def clinician_evaluations_to_performance_metrics(
    data: list[Stage2Data],
) -> GroundTruthPerformanceMetrics:
    data = get_full_performance_metrics([analysis_data_to_performance_metrics(x) for x in data])
    return data
