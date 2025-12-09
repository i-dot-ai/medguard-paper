"""
Evaluation Metrics Dump

Recalculates and saves EvaluationMetrics based on Ground Truth binary classification.

Uses the Level 1 definitions:
- TP = positive_any_issue (System flagged, clinician found issues)
- FP = positive_no_issue (System flagged, clinician found no issues)
- TN = negative_no_issue (System didn't flag, clinician found no issues)
- FN = negative_any_issue (System didn't flag, clinician found issues)
"""

from medguard.analysis.base import TextAnalysisBase
from medguard.evaluation.evaluation_metrics import EvaluationMetrics, calculate_evaluation_metrics
from medguard.evaluation.performance_metrics.ground_truth.performance_metrics import (
    clinician_evaluations_to_performance_metrics,
)


class EvaluationMetricsDumpAnalysis(TextAnalysisBase):
    """
    Recalculate and dump EvaluationMetrics based on Ground Truth binary classification.

    Recalculates metrics using the Level 1 TP/FP/TN/FN definitions from ground truth.
    """

    def __init__(self, evaluation, name: str = "evaluation_metrics_dump"):
        super().__init__(evaluation, name=name)

    def execute(self) -> str:
        """
        Execute analysis and return JSON dump of recalculated evaluation metrics.

        Returns:
            JSON string of evaluation metrics
        """
        # Exclude data errors
        evaluation = self.evaluation.exclude_data_errors()

        # Get ground truth performance metrics
        metrics = clinician_evaluations_to_performance_metrics(evaluation.clinician_evaluations)

        # Extract binary classification counts using Level 1 definitions
        TP = metrics.positive_any_issue
        FP = metrics.positive_no_issue
        TN = metrics.negative_no_issue
        FN = metrics.negative_any_issue

        # Recalculate evaluation metrics
        eval_metrics = calculate_evaluation_metrics(TP, TN, FP, FN)

        return eval_metrics.model_dump_json(indent=2)
