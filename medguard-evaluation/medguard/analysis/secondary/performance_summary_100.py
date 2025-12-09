from medguard.evaluation.clinician.utils import load_stage2_data_from_folder
from medguard.evaluation.performance_metrics.ground_truth.performance_metrics import (
    clinician_evaluations_to_performance_metrics,
)

from .base import TextAnalysisBase
from .performance_summary import ground_truth_performance_metrics_to_table


class PerformanceSummaryAnalysis100(TextAnalysisBase):
    """
    Generate formatted text summaries of performance metrics.

    Produces a ground truth performance summary.
    """

    def __init__(
        self,
        evaluation,
        path_to_evaluations: list[str] = ["outputs/evaluations/evaluations_test_100"],
        name: str = "performance_summary_100",
    ):
        super().__init__(evaluation, name=name)

        self.stage2datas = load_stage2_data_from_folder(path_to_evaluations).values()

    def execute(self) -> str:
        """
        Execute analysis and return formatted text summary.

        Returns:
            Formatted string with ground truth and filter performance metrics
        """
        # Compute metrics
        ground_truth_metrics = clinician_evaluations_to_performance_metrics(self.stage2datas)

        # Format output
        output = "=" * 80 + "\n"
        output += "GROUND TRUTH PERFORMANCE METRICS\n"
        output += "=" * 80 + "\n\n"
        output += ground_truth_performance_metrics_to_table(ground_truth_metrics)
        return output
