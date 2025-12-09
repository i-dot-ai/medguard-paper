"""
Reusable filter predicates for Evaluation analysis.

Similar to SQL templates in preprocessing repo, these filters can be
imported and reused across multiple analyses.

Usage:
    from medguard.analysis.filters import by_filter, agrees_with_rules

    # Get patient IDs matching filter 5
    ids = evaluation.filter_by_analysed_record(by_filter(5))

    # Get patient IDs where clinician agreed with rules
    ids = evaluation.filter_by_clinician_evaluation(agrees_with_rules())

    # Combine with set operations
    final_ids = ids_filter & ids_clinician
"""

from typing import Callable

from medguard.scorer.models import AnalysedPatientRecord
from medguard.evaluation.clinician.models import Stage2Data


# === Filters on AnalysedPatientRecord ===


def by_filter(filter_id: int) -> Callable[[AnalysedPatientRecord], bool]:
    """
    Filter to patients matching specific PINCER filter.

    Args:
        filter_id: PINCER filter ID (5, 6, 10, 16, 23, 26, 28, 33, 43, 55)

    Returns:
        Predicate function for use with filter_by_analysed_record()
    """

    def predicate(record: AnalysedPatientRecord) -> bool:
        active_filter = record.patient.get_active_filter()
        if active_filter is None:
            return False
        return active_filter.filter_id == filter_id

    return predicate


def by_positive_ground_truth() -> Callable[[AnalysedPatientRecord], bool]:
    """
    Filter to positive ground truth (has matched filters).

    Excludes filters 16 and 43 which were found to have implementation errors.

    Returns:
        Predicate function for use with filter_by_analysed_record()
    """

    def predicate(record: AnalysedPatientRecord) -> bool:
        if len(record.patient.matched_filters) == 0:
            return False
        # Exclude filters 16 and 43
        valid_filters = [f for f in record.patient.matched_filters if f.filter_id not in [16, 43]]
        return len(valid_filters) > 0

    return predicate


def by_negative_ground_truth() -> Callable[[AnalysedPatientRecord], bool]:
    """
    Filter to negative ground truth (no matched filters).

    Returns:
        Predicate function for use with filter_by_analysed_record()
    """

    def predicate(record: AnalysedPatientRecord) -> bool:
        return len(record.patient.matched_filters) == 0

    return predicate


def by_medguard_flagged() -> Callable[[AnalysedPatientRecord], bool]:
    """
    Filter to cases where MedGuard identified any clinical issue.

    Returns:
        Predicate function for use with filter_by_analysed_record()
    """

    def predicate(record: AnalysedPatientRecord) -> bool:
        return any(
            issue.intervention_required for issue in record.medguard_analysis.clinical_issues
        )

    return predicate


def by_medguard_not_flagged() -> Callable[[AnalysedPatientRecord], bool]:
    """
    Filter to cases where MedGuard did not identify any clinical issues.

    Returns:
        Predicate function for use with filter_by_analysed_record()
    """

    def predicate(record: AnalysedPatientRecord) -> bool:
        return not any(
            issue.intervention_required for issue in record.medguard_analysis.clinical_issues
        )

    return predicate


# === Filters on Stage2Data (Clinician Evaluations) ===


def agrees_with_rules() -> Callable[[Stage2Data], bool]:
    """
    Filter to clinician evaluations that agree with PINCER rules.

    Returns:
        Predicate function for use with filter_by_clinician_evaluation()
    """

    def predicate(evaluation: Stage2Data) -> bool:
        return evaluation.agrees_with_rules == "yes"

    return predicate


def disagrees_with_rules() -> Callable[[Stage2Data], bool]:
    """
    Filter to clinician evaluations that disagree with PINCER rules.

    Returns:
        Predicate function for use with filter_by_clinician_evaluation()
    """

    def predicate(evaluation: Stage2Data) -> bool:
        return evaluation.agrees_with_rules == "no"

    return predicate


def has_data_error() -> Callable[[Stage2Data], bool]:
    """
    Filter to clinician evaluations that flagged a data error.

    Returns:
        Predicate function for use with filter_by_clinician_evaluation()
    """

    def predicate(evaluation: Stage2Data) -> bool:
        return evaluation.data_error is True

    return predicate


def no_data_error() -> Callable[[Stage2Data], bool]:
    """
    Filter to clinician evaluations with no data error.

    Returns:
        Predicate function for use with filter_by_clinician_evaluation()
    """

    def predicate(evaluation: Stage2Data) -> bool:
        return evaluation.data_error is False

    return predicate


def medguard_identified_rule_issues() -> Callable[[Stage2Data], bool]:
    """
    Filter to cases where clinician agreed MedGuard identified the rule issues.

    Only applicable when agrees_with_rules == "yes".

    Returns:
        Predicate function for use with filter_by_clinician_evaluation()
    """

    def predicate(evaluation: Stage2Data) -> bool:
        return evaluation.medguard_identified_rule_issues == "yes"

    return predicate


def clinician_found_missed_issues() -> Callable[[Stage2Data], bool]:
    """
    Filter to cases where clinician found issues MedGuard missed.

    Returns:
        Predicate function for use with filter_by_clinician_evaluation()
    """

    def predicate(evaluation: Stage2Data) -> bool:
        return evaluation.missed_issues == "yes"

    return predicate


def clinician_found_any_issues() -> Callable[[Stage2Data], bool]:
    """
    Filter to cases where clinician found ANY issues (missed or agreed with any identified issues).

    This includes:
    - missed_issues == "yes" (expert found issues beyond what was identified)
    - Any issue_assessments == True (expert agreed with at least one identified issue)

    Returns:
        Predicate function for use with filter_by_clinician_evaluation()
    """

    def predicate(evaluation: Stage2Data) -> bool:
        found_missed = evaluation.missed_issues == "yes"
        agreed_with_any = any(evaluation.issue_assessments)
        return found_missed or agreed_with_any

    return predicate


def clinician_found_no_issues() -> Callable[[Stage2Data], bool]:
    """
    Filter to cases where clinician found NO issues (opposite of clinician_found_any_issues).

    Returns True when expert did NOT find any issues:
    - missed_issues != "yes" (no missed issues)
    - All issue_assessments == False (didn't agree with any identified issues)

    Returns:
        Predicate function for use with filter_by_clinician_evaluation()
    """

    def predicate(evaluation: Stage2Data) -> bool:
        found_missed = evaluation.missed_issues == "yes"
        agreed_with_any = any(evaluation.issue_assessments)
        return not (found_missed or agreed_with_any)

    return predicate


# === Helper Functions for Extracting Continuous Values ===
# These are not filters (don't return bool), but helper functions to extract
# continuous values for correlation/regression analyses


def get_medication_count(record: AnalysedPatientRecord) -> int:
    """Get number of active medications at analysis date."""
    return record.patient.count_number_active_medications(record.analysis_date)


def get_age(record: AnalysedPatientRecord) -> int | None:
    """Get patient age at analysis date."""
    return record.patient.get_age(record.analysis_date)


def get_qof_count(record: AnalysedPatientRecord) -> int:
    """Get number of QOF registers."""
    return record.patient.get_number_qof_registers()


def get_filter_id(record: AnalysedPatientRecord) -> int | None:
    """Get active filter ID, or None if no filter."""
    active_filter = record.patient.get_active_filter()
    return active_filter.filter_id if active_filter else None


def get_sex(record: AnalysedPatientRecord) -> str | None:
    """Get patient sex/gender."""
    if record.patient.sex is None:
        return None
    return record.patient.sex.value


# === Constants ===

# All PINCER filter IDs in the evaluation
# Filters 16 and 43 excluded due to implementation errors identified during analysis
# Filter 16: Temporal validation error (checked historical eGFR without verifying improvement)
# Filter 43: Temporal window mismatch (only checked monitoring before prescription start)
PINCER_FILTER_IDS = [5, 6, 10, 23, 26, 28, 33, 55]
