from inspect_ai.model import get_model
from inspect_ai.scorer import Score, Target, accuracy, scorer
from inspect_ai.solver import TaskState

from medguard.data_ingest.models.filters import (
    FilterMatch,
    FilterType,
    filter_descriptions,
    filter_factors,
    get_filter_description,
)
from medguard.scorer.models import (
    AgreementType,
    AnalysedPatientRecord,
    EvaluationAnalysis,
    FailureAnalysisList,
    IssueClassification,
)
from medguard.scorer.pincer_filters.prompts import (
    CLINICAL_ISSUE_CLASSIFICATION_PROMPT,
    FALSE_NEGATIVE_PROMPT,
    FALSE_POSITIVE_INCORRECT_INTERVENTION_PROMPT,
    FALSE_POSITIVE_INCORRECT_ISSUE_PROMPT,
    FALSE_POSITIVE_PROMPT,
    INTERVENTION_CLASSIFICATION_PROMPT,
)
from medguard.scorer.utils import get_medguard_analysis_from_state, get_structured_output


def get_matched_filters_from_state(state: TaskState) -> list[int]:
    matched_filters = state.metadata["matched_filters"]
    matched_filters = [FilterMatch.model_validate(filter_match) for filter_match in matched_filters]
    matched_filter_ids = [filter.filter_id for filter in matched_filters]

    return matched_filter_ids


def parse_clinical_issue_description(filter_types: list[int]) -> str:
    return "and ".join(
        [filter_descriptions[FilterType(filter_type)] for filter_type in filter_types]
    )


def parse_clinical_issue_factors(filter_types: list[int]) -> str:
    res = ""
    i = 1
    for filter_type in filter_types:
        for factor in filter_factors[FilterType(filter_type)]:
            res += f"{i}. {factor}\n"
            i += 1
    return res


@scorer(metrics=[accuracy()])
def llm_as_a_judge():
    categories = get_filter_description()

    async def score(state: TaskState, target: Target) -> Score:
        model = get_model()

        matched_filter_ids = get_matched_filters_from_state(state)
        medguard_analysis = get_medguard_analysis_from_state(state)
        review_date = state.metadata["review_date"]

        #  Step 1: Understand whether the clinical issue has been correctly identified (either true positive or true negative)
        ground_truth_intervention_required = True if len(matched_filter_ids) > 0 else False
        medguard_intervention_required = medguard_analysis.intervention_required

        # True Negative
        if ground_truth_intervention_required == False and medguard_intervention_required == False:
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

        # false positive is when MedGuard identifies an issue, but there wasn't one in the ground truth
        if not ground_truth_intervention_required and medguard_intervention_required:
            # now we're in the false positive case
            false_positive_prompt = FALSE_POSITIVE_PROMPT.format(
                patient_profile=state.input,
                patient_analysis=medguard_analysis.prompt,
            )
            parsed_false_positive_analysis = await get_structured_output(
                model, false_positive_prompt, FailureAnalysisList
            )
            return Score(
                value=0.0,
                explanation="FALSE POSITIVE: The patient did not have an issue that needed an intervention. MedGuard incorrectly identified the presence of an issue.",
                answer=state.output.completion,
                metadata=AnalysedPatientRecord(
                    patient_link_id=state.metadata["patient_id"],
                    analysis_date=review_date,
                    medguard_analysis=medguard_analysis,
                    evaluation_analysis=EvaluationAnalysis(
                        issue_correct=False,
                        intervention_correct=False,
                        agreement_type=AgreementType.FP,
                        intervention_analysis=None,
                        failure_analysis=parsed_false_positive_analysis.failure_analysis,
                    ),
                ).model_dump(),
            )

        # Classify clinical issue
        classification_prompt = CLINICAL_ISSUE_CLASSIFICATION_PROMPT.format(
            clinical_issue=parse_clinical_issue_description(matched_filter_ids),
            patient_summary=medguard_analysis.patient_review,
            medguard_issues=medguard_analysis.clinical_issue_prompt,
        )

        parsed_clinical_issue_classification = await get_structured_output(
            model, classification_prompt, IssueClassification
        )
        correct_issue = parsed_clinical_issue_classification.correct

        # Classify intervention
        intervention_prompt = INTERVENTION_CLASSIFICATION_PROMPT.format(
            clinical_issue=parse_clinical_issue_description(matched_filter_ids),
            patient_summary=medguard_analysis.patient_review,
            medguard_issues=medguard_analysis.clinical_issue_prompt,
            issue_reasoning=parsed_clinical_issue_classification.reasoning,
            intervention=medguard_analysis.intervention,
        )

        parsed_intervention_analysis = await get_structured_output(
            model, intervention_prompt, IssueClassification
        )
        correct_intervention = parsed_intervention_analysis.correct

        # True Positive. We don't need to check for ground truth intervention required because we've already covered that case
        if (
            ground_truth_intervention_required
            and medguard_intervention_required
            and correct_issue
            and correct_intervention
        ):
            return Score(
                value=1.0,
                explanation="TRUE POSITIVE: The patient has an issue that needed an intervention. MedGuard correctly identified both the issue and the intervention.",
                answer=state.output.completion,
                metadata=AnalysedPatientRecord(
                    patient_link_id=state.metadata["patient_id"],
                    analysis_date=review_date,
                    medguard_analysis=medguard_analysis,
                    evaluation_analysis=EvaluationAnalysis(
                        issue_correct=True,
                        intervention_correct=True,
                        agreement_type=AgreementType.TP,
                        intervention_analysis=parsed_intervention_analysis,
                        failure_analysis=[],
                    ),
                ).model_dump(),
            )

        # Step 2: We have already covered the TN and TP cases. Now we must cover the FP and FN cases

        # false positive when MedGuard identifies the correct issue, but the intervention is incorrect
        if (
            ground_truth_intervention_required
            and medguard_intervention_required
            and correct_issue
            and not correct_intervention
        ):
            false_positive_incorrect_intervention_prompt = (
                FALSE_POSITIVE_INCORRECT_INTERVENTION_PROMPT.format(
                    patient_profile=state.input,
                    patient_analysis=medguard_analysis.prompt,
                    flagged_clinical_issue=parse_clinical_issue_description(matched_filter_ids),
                )
            )

            parsed_false_positive_incorrect_intervention_analysis = await get_structured_output(
                model, false_positive_incorrect_intervention_prompt, FailureAnalysisList
            )
            return Score(
                value=0.0,
                explanation="FALSE POSITIVE: MedGuard correctly identified both the presence of an issue and the specific issue itself, but incorrectly identified the intervention that was required to address the issue.",
                answer=state.output.completion,
                metadata=AnalysedPatientRecord(
                    patient_link_id=state.metadata["patient_id"],
                    analysis_date=review_date,
                    medguard_analysis=medguard_analysis,
                    evaluation_analysis=EvaluationAnalysis(
                        issue_correct=True,
                        intervention_correct=False,
                        agreement_type=AgreementType.FP,
                        intervention_analysis=parsed_intervention_analysis,
                        failure_analysis=parsed_false_positive_incorrect_intervention_analysis.failure_analysis,
                    ),
                ).model_dump(),
            )

        # false positive is when MedGuard correctly identifies that there was an issue, but gets the wrong one
        if (
            ground_truth_intervention_required
            and medguard_intervention_required
            and not correct_issue
        ):
            false_positive_incorrect_issue_prompt = FALSE_POSITIVE_INCORRECT_ISSUE_PROMPT.format(
                patient_profile=state.input,
                patient_analysis=medguard_analysis.prompt,
                flagged_clinical_issue=parse_clinical_issue_description(matched_filter_ids),
            )
            parsed_false_positive_analysis = await get_structured_output(
                model, false_positive_incorrect_issue_prompt, FailureAnalysisList
            )
            return Score(
                value=0.0,
                explanation="FALSE POSITIVE: The patient has an issue that required an intervention. MedGuard identified an incorrect issue.",
                answer=state.output.completion,
                metadata=AnalysedPatientRecord(
                    patient_link_id=state.metadata["patient_id"],
                    analysis_date=review_date,
                    medguard_analysis=medguard_analysis,
                    evaluation_analysis=EvaluationAnalysis(
                        issue_correct=False,
                        intervention_correct=False,
                        agreement_type=AgreementType.FP,
                        intervention_analysis=None,
                        failure_analysis=parsed_false_positive_analysis.failure_analysis,
                    ),
                ).model_dump(),
            )

        # false negative is when MedGuard identifies no issue, but there was one in the ground truth
        if ground_truth_intervention_required and not medguard_intervention_required:
            false_negative_prompt = FALSE_NEGATIVE_PROMPT.format(
                patient_profile=state.input,
                patient_analysis=medguard_analysis.prompt,
                flagged_clinical_issue=parse_clinical_issue_description(matched_filter_ids),
            )
            parsed_false_negative_analysis = await get_structured_output(
                model, false_negative_prompt, FailureAnalysisList
            )
            return Score(
                value=0.0,
                explanation="FALSE NEGATIVE: The patient had an issue that needed an intervention. MedGuard incorrectly indicated that no issue was present.",
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
                        failure_analysis=parsed_false_negative_analysis.failure_analysis,
                    ),
                ).model_dump(),
            )

        # we should never get here, but just in case
        return Score(
            value=0.0,
            explanation="ERROR: We should never get here",
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
                    failure_analysis=[],
                ),
            ).model_dump(),
        )

    return score
