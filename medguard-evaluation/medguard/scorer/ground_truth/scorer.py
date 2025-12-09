from inspect_ai.scorer import Score, Target, accuracy, scorer
from inspect_ai.model import get_model
from inspect_ai.solver import TaskState

from medguard.utils.parsing import read_jsonl
from medguard.scorer.utils import get_structured_output, get_medguard_analysis_from_state
from medguard.ground_truth.models import GroundTruthAssessmentFull
from medguard.ground_truth.utils import load_ground_truth_samples

from medguard.scorer.models import (
    AgreementType,
    AnalysedPatientRecord,
    IssueClassification,
    EvaluationAnalysis,
    FailureAnalysisList,
    MedGuardAnalysis,
    InterventionList,
    ClassificationMatch,
)

import logging

logger = logging.getLogger(__name__)

from .prompts import (
    ISSUE_CLASSIFICATION_PROMPT,
    INTERVENTION_CLASSIFICATION_PROMPT,
    FAILURE_CLASSIFICATION_PROMPT,
    INTERVENTION_SPLITTING_PROMPT,
)


def format_list(items: list[str]) -> str:
    return "\n".join([f"- {item}" for item in items])


def format_item(item: str) -> str:
    return f"- {item}"


def format_medguard_analysis_for_failure_analysis(medguard_analysis: MedGuardAnalysis) -> str:
    result = f"patient review:\n{medguard_analysis.patient_review}\n"

    issues_requiring_intervention = [
        issue for issue in medguard_analysis.clinical_issues if issue.intervention_required
    ]

    if len(issues_requiring_intervention) > 0:
        result += "\n\nissues that require an intervention:\n"
        for issue in issues_requiring_intervention:
            result += f"- {issue.issue}\n"

    issues_not_requiring_intervention = [
        issue for issue in medguard_analysis.clinical_issues if not issue.intervention_required
    ]

    if len(issues_not_requiring_intervention) > 0:
        result += "\n\nissues that do not require an intervention:\n"
        for issue in issues_not_requiring_intervention:
            result += f"- {issue.issue}\n"

    result += f"\n\nintervention: {medguard_analysis.intervention}\n"

    return result


def format_ground_truth_for_failure_analysis(ground_truth: GroundTruthAssessmentFull) -> str:
    if len(ground_truth.issues) > 0:
        result = f"issues that require an intervention:\n"
        for issue in ground_truth.issues:
            result += f"- {issue}\n"
    else:
        result = f"no issues required an intervention\n"

    if len(ground_truth.intervention) > 0:
        result += f"\n\nintervention:\n"
        for intervention in ground_truth.intervention:
            result += f"- {intervention}\n"
    else:
        result += f"\n\nno intervention required\n"

    if len(ground_truth.notes) > 0:
        result += f"\n\nnotes:\n"
        for note in ground_truth.notes:
            result += f"- {note}\n"

    return result


def calculate_f1_score(
    classifications: list[ClassificationMatch], ground_truth_count: int
) -> tuple[float, float, float]:
    """
    Calculate precision, recall, and F1 score for a list of classifications.

    Args:
        classifications: List of ClassificationMatch objects
        ground_truth_count: Number of items in the ground truth

    Returns:
        Tuple of (precision, recall, f1_score)
    """
    if not classifications:
        return 0.0, 0.0, 0.0

    # Precision: number of correct predictions over total predictions
    correct_count = sum(1 for c in classifications if c.correct)
    precision = correct_count / len(classifications)

    # Recall: number of distinct ground truth items matched over total ground truth items
    if ground_truth_count == 0:
        recall = 0.0
    else:
        matched_ids = {c.match_id for c in classifications if c.correct and c.match_id is not None}
        recall = len(matched_ids) / ground_truth_count

    # F1 score: harmonic mean of precision and recall
    if precision + recall == 0:
        f1_score = 0.0
    else:
        f1_score = 2 * (precision * recall) / (precision + recall)

    return precision, recall, f1_score


@scorer(metrics=[accuracy()])
def llm_as_a_judge():
    # Load the ground truth samples
    ground_truth_samples_dict = load_ground_truth_samples()

    async def score(state: TaskState, target: Target) -> Score:
        max_retries = 5
        last_exception = None

        for attempt in range(max_retries):
            try:
                model = get_model()

                # Get the initial object information
                patient_id = state.metadata["patient_id"]
                medguard_analysis = get_medguard_analysis_from_state(state)
                review_date = state.metadata["review_date"]
                ground_truth = ground_truth_samples_dict[patient_id]

                ground_truth_intervention_required = (
                    True if len(ground_truth.intervention) > 0 else False
                )
                medguard_intervention_required = medguard_analysis.intervention_required

                # True Negative
                if (
                    ground_truth_intervention_required == False
                    and medguard_intervention_required == False
                ):
                    return Score(
                        value=1.0,
                        explanation="TRUE NEGATIVE: The patient did not have an issue that needed an intervention, MedGuard correctly recommended no intervention.",
                        answer=state.output.completion,
                        metadata=AnalysedPatientRecord(
                            patient_link_id=state.metadata["patient_id"],
                            analysis_date=review_date,
                            medguard_analysis=medguard_analysis,
                            evaluation_analysis=EvaluationAnalysis(
                                issue_correct=True,
                                intervention_correct=True,
                                agreement_type=AgreementType.TN,
                                intervention_analysis=None,
                                failure_analysis=[],
                            ),
                        ).model_dump(),
                    )

                # Failure Analysis
                failure_analysis_prompt = FAILURE_CLASSIFICATION_PROMPT.format(
                    clinician_review=format_medguard_analysis_for_failure_analysis(
                        medguard_analysis
                    ),
                    ground_truth=format_ground_truth_for_failure_analysis(ground_truth),
                )
                parsed_failure_analysis = await get_structured_output(
                    model, failure_analysis_prompt, FailureAnalysisList
                )

                # False Negative
                if ground_truth_intervention_required and medguard_intervention_required == False:
                    return Score(
                        value=0.0,
                        explanation="FALSE NEGATIVE: The patient had an issue that needed an intervention, MedGuard incorrectly recommended no intervention.",
                        answer=state.output.completion,
                        metadata=AnalysedPatientRecord(
                            patient_link_id=state.metadata["patient_id"],
                            analysis_date=review_date,
                            medguard_analysis=medguard_analysis,
                            evaluation_analysis=EvaluationAnalysis(
                                issue_correct=False,
                                intervention_correct=False,
                                agreement_type=AgreementType.FN,
                                intervention_analysis=None,
                                failure_analysis=parsed_failure_analysis.failure_analysis,
                                issue_correct_list=None,
                                intervention_correct_list=None,
                            ),
                        ).model_dump(),
                    )

                # Now we know that medguard_intervention_required is True, so we can assess the issue and intervention accuracy.
                issue_classifications: list[ClassificationMatch] = []
                for issue in medguard_analysis.clinical_issues:
                    # Only assess issues that require an intervention
                    if not issue.intervention_required:
                        continue

                    issue_classification_prompt = ISSUE_CLASSIFICATION_PROMPT.format(
                        ground_truth_issues=format_list(ground_truth.issues),
                        issue=format_item(issue.issue),
                    )

                    parsed_issue_classification = await get_structured_output(
                        model, issue_classification_prompt, ClassificationMatch
                    )

                    issue_classifications.append(parsed_issue_classification)

                # Do the same for interventions, but in this case we need to make an interventions list first due to legacy model output
                intervention_splitting_prompt = INTERVENTION_SPLITTING_PROMPT.format(
                    clinician_intervention=medguard_analysis.intervention
                )
                interventions = await get_structured_output(
                    model, intervention_splitting_prompt, InterventionList
                )

                intervention_classifications: list[ClassificationMatch] = []
                for intervention in interventions.interventions:
                    intervention_classification_prompt = INTERVENTION_CLASSIFICATION_PROMPT.format(
                        ground_truth_interventions=format_list(ground_truth.intervention),
                        clinician_intervention=intervention,
                    )

                    parsed_intervention_classification = await get_structured_output(
                        model, intervention_classification_prompt, ClassificationMatch
                    )

                    intervention_classifications.append(parsed_intervention_classification)

                issue_correct_list = [
                    classification.correct for classification in issue_classifications
                ]
                intervention_correct_list = [
                    classification.correct for classification in intervention_classifications
                ]

                all_issue_correct = all(issue_correct_list)
                all_intervention_correct = all(intervention_correct_list)

                all_correct = all_issue_correct and all_intervention_correct

                issue_precision, issue_recall, issue_f1 = calculate_f1_score(
                    issue_classifications, len(ground_truth.issues)
                )

                intervention_precision, intervention_recall, intervention_f1 = calculate_f1_score(
                    intervention_classifications, len(ground_truth.intervention)
                )

                # Overall score is the mean of both F1 scores
                score = (issue_f1 + intervention_f1) / 2

                if all_correct:
                    return Score(
                        value=1.0,
                        explanation="TRUE POSITIVE: The patient had an issue that needed an intervention, MedGuard correctly identified both the issue and the intervention.",
                        answer=state.output.completion,
                        metadata=AnalysedPatientRecord(
                            patient_link_id=state.metadata["patient_id"],
                            analysis_date=review_date,
                            medguard_analysis=medguard_analysis,
                            evaluation_analysis=EvaluationAnalysis(
                                issue_correct=all_issue_correct,
                                intervention_correct=all_intervention_correct,
                                agreement_type=AgreementType.TP,
                                intervention_analysis=None,
                                failure_analysis=None,
                                issue_correct_list=issue_classifications,
                                intervention_correct_list=intervention_classifications,
                                issue_precision=issue_precision,
                                issue_recall=issue_recall,
                                intervention_precision=intervention_precision,
                                intervention_recall=intervention_recall,
                            ),
                        ).model_dump(),
                    )

                # Otherwise it's a false positive
                return Score(
                    value=score,
                    explanation="FALSE POSITIVE: The patient had an issue that needed an intervention, MedGuard did not correctly identify the issues and interventions.",
                    answer=state.output.completion,
                    metadata=AnalysedPatientRecord(
                        patient_link_id=state.metadata["patient_id"],
                        analysis_date=review_date,
                        medguard_analysis=medguard_analysis,
                        evaluation_analysis=EvaluationAnalysis(
                            issue_correct=all_issue_correct,
                            intervention_correct=all_intervention_correct,
                            agreement_type=AgreementType.TP,
                            intervention_analysis=None,
                            failure_analysis=parsed_failure_analysis.failure_analysis,
                            issue_correct_list=issue_classifications,
                            intervention_correct_list=intervention_classifications,
                            issue_precision=issue_precision,
                            issue_recall=issue_recall,
                            intervention_precision=intervention_precision,
                            intervention_recall=intervention_recall,
                        ),
                    ).model_dump(),
                )

            except Exception as e:
                last_exception = e
                logger.debug(
                    f"Error in score function (attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {str(e)}"
                )
                if attempt < max_retries - 1:
                    logger.debug(f"Retrying...")
                continue

        # If all retries failed, return a score of 0 with placeholder fields
        logger.debug(f"All {max_retries} attempts failed. Returning placeholder score of 0.")
        patient_id = state.metadata.get("patient_id", "unknown")
        review_date = state.metadata.get("review_date", "unknown")

        return Score(
            value=0.0,
            explanation=f"ERROR: Failed to score after {max_retries} attempts. Last error: {type(last_exception).__name__}: {str(last_exception)}",
            answer=state.output.completion if state.output else "N/A",
            metadata={
                "patient_link_id": patient_id,
                "analysis_date": review_date,
                "error": str(last_exception),
                "error_type": type(last_exception).__name__,
                "medguard_analysis": None,
                "evaluation_analysis": None,
            },
        )

    return score
