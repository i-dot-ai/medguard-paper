"""
Performance Summary Analysis

Generates formatted text summaries of performance metrics for both ground truth
and filter-based evaluations.
"""

from medguard.analysis.base import TextAnalysisBase
from medguard.evaluation.performance_metrics.ground_truth.performance_metrics import (
    GroundTruthPerformanceMetrics,
    clinician_evaluations_to_performance_metrics,
)


def ground_truth_performance_metrics_to_table(metrics: GroundTruthPerformanceMetrics) -> str:
    """Convert GroundTruthPerformanceMetrics to a formatted table string."""
    N_positive = metrics.positive
    A = metrics.positive_any_issue
    B = metrics.positive_no_issue
    C = metrics.positive_all_correct
    D = metrics.positive_some_correct
    E = metrics.positive_no_correct

    # Level 3 should ONLY evaluate cases where ALL issues were correct at Level 2
    F = metrics.all_correct_correct_intervention
    G = metrics.all_correct_partial_intervention
    H = metrics.all_correct_incorrect_intervention

    res = f"Positive Cases: {N_positive}\n"
    res += (
        f"Level 1: Any issue identified: {A}/{N_positive} - Cumulative Rate: {A / N_positive:.2%}\n"
    )
    res += f"Level 1: No issue identified: {B}/{N_positive}\n"

    res += f"Level 2: Issues correct: {C}/{A} - Cumulative Rate: {C / A:.2%}\n"
    res += f"Level 2: Issues partially correct: {D}/{A} - Cumulative Rate: {D / A:.2%}\n"
    res += (
        f"Level 2: Issues incorrect: {E}/{A} - Rate: {E / A:.2%} - Cumulative Rate: {E / A:.2%}\n"
    )

    res += f"Level 3: Intervention correct {F}/{C} - Cumulative Rate: {F / C:.2%}\n"
    res += f"Level 3: Intervention partially correct {G}/{C} - Cumulative Rate: {G / C:.2%}\n"
    res += f"Level 3: Intervention incorrect {H}/{C} - Cumulative Rate: {H / C:.2%}\n"

    N_negative = metrics.negative
    A = metrics.negative_any_issue
    B = metrics.negative_no_issue

    res += f"\nNegative Cases: {N_negative}\n"
    res += f"Level 1: True Negative (no issue): {B}/{N_negative} - Cumulative Rate: {B / N_negative:.2%}\n"
    res += f"Level 1: False Positive (issue): {N_negative - B}/{N_negative} - Cumulative Rate: {(N_negative - B) / N_negative:.2%}\n"

    return res


class PerformanceSummaryAnalysis(TextAnalysisBase):
    """
    Generate formatted text summaries of performance metrics.

    Produces both ground truth and filter-based performance summaries.
    """

    def __init__(self, evaluation, name: str = "performance_summary"):
        super().__init__(evaluation, name=name)

    def execute(self) -> str:
        """
        Execute analysis and return formatted text summary.

        Returns:
            Formatted string with ground truth and filter performance metrics
        """
        evaluation = self.evaluation.exclude_data_errors()
        # Compute metrics
        ground_truth_metrics = clinician_evaluations_to_performance_metrics(
            evaluation.clinician_evaluations
        )

        # Format output
        output = "=" * 80 + "\n"
        output += "GROUND TRUTH PERFORMANCE METRICS\n"
        output += "=" * 80 + "\n\n"
        output += ground_truth_performance_metrics_to_table(ground_truth_metrics)
        output += "\n\n"
        output += "=" * 80 + "\n"
        return output
