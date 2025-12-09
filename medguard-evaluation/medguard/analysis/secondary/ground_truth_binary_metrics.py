"""
Ground Truth Binary Classification Metrics (Level 1)

Evaluates the system's ability to detect ANY issue (Level 1) against ground truth.

Binary classification:
- TP = positive_any_issue (System flagged, clinician found issues)
- FP = positive_no_issue (System flagged, clinician found no issues)
- TN = negative_no_issue (System didn't flag, clinician found no issues)
- FN = negative_any_issue (System didn't flag, clinician found issues)

Section: 3.3.1 (Level 1 Performance)
"""

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from medguard.analysis.base import EvaluationAnalysisBase
from medguard.analysis.utils import setup_publication_plot
from medguard.evaluation.performance_metrics.ground_truth.performance_metrics import (
    clinician_evaluations_to_performance_metrics,
)


class GroundTruthBinaryMetricsAnalysis(EvaluationAnalysisBase):
    """
    Calculate binary classification metrics for Level 1 (issue detection).

    Treats the task as: Does the system detect ANY issue when there is a ground truth issue?
    """

    def __init__(self, evaluation, name: str = "ground_truth_binary_metrics"):
        super().__init__(evaluation, name=name)

    def execute(self) -> pl.DataFrame:
        """
        Execute analysis and return DataFrame with binary classification metrics.

        Returns DataFrame with columns:
        - metric: Name of the metric (TP, FP, TN, FN, Precision, Recall, F1, Accuracy, Specificity)
        - value: Value of the metric
        - description: Human-readable description
        """
        # Exclude data errors
        evaluation = self.evaluation.exclude_data_errors()

        # Get ground truth performance metrics
        metrics = clinician_evaluations_to_performance_metrics(evaluation.clinician_evaluations)

        # Extract binary classification counts
        # positive = Expert found issue, negative = Expert found no issue
        # any_issue = System flagged, no_issue = System didn't flag
        TP = metrics.positive_any_issue  # Expert YES, System YES
        FN = metrics.positive_no_issue  # Expert YES, System NO
        FP = metrics.negative_any_issue  # Expert NO, System YES
        TN = metrics.negative_no_issue  # Expert NO, System NO

        # Calculate derived metrics
        precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (TP + TN) / (TP + TN + FP + FN) if (TP + TN + FP + FN) > 0 else 0.0
        specificity = TN / (TN + FP) if (TN + FP) > 0 else 0.0

        # NPV and PPV
        ppv = precision  # Positive Predictive Value = Precision
        npv = TN / (TN + FN) if (TN + FN) > 0 else 0.0  # Negative Predictive Value

        rows = [
            {
                "metric": "TP",
                "value": TP,
                "description": "True Positives (System flagged, clinician found issues)",
            },
            {
                "metric": "FN",
                "value": FN,
                "description": "False Negatives (System didn't flag, clinician found issues)",
            },
            {
                "metric": "FP",
                "value": FP,
                "description": "False Positives (System flagged, clinician found no issues)",
            },
            {
                "metric": "TN",
                "value": TN,
                "description": "True Negatives (System didn't flag, clinician found no issues)",
            },
            {"metric": "Precision", "value": precision, "description": "TP / (TP + FP)"},
            {"metric": "Recall", "value": recall, "description": "TP / (TP + FN) - Sensitivity"},
            {"metric": "F1", "value": f1, "description": "Harmonic mean of Precision and Recall"},
            {"metric": "Accuracy", "value": accuracy, "description": "(TP + TN) / Total"},
            {"metric": "Specificity", "value": specificity, "description": "TN / (TN + FP)"},
            {
                "metric": "PPV",
                "value": ppv,
                "description": "Positive Predictive Value (same as Precision)",
            },
            {
                "metric": "NPV",
                "value": npv,
                "description": "Negative Predictive Value: TN / (TN + FN)",
            },
        ]

        return pl.DataFrame(rows)

    def plot(self) -> plt.Figure:
        """
        Create confusion matrix visualization.

        Returns:
            Matplotlib figure
        """
        df = self.load_df()

        # Extract counts
        tp = df.filter(pl.col("metric") == "TP")["value"][0]
        fp = df.filter(pl.col("metric") == "FP")["value"][0]
        tn = df.filter(pl.col("metric") == "TN")["value"][0]
        fn = df.filter(pl.col("metric") == "FN")["value"][0]

        # Create confusion matrix
        # Rows = Clinician, Columns = System
        # Row 0: Clinician No Issue, Row 1: Clinician Issue
        # Col 0: System No Flag, Col 1: System Flag
        confusion_matrix = np.array([[tn, fp], [fn, tp]])
        labels = np.array(
            [["True Negative", "False Positive"], ["False Negative", "True Positive"]]
        )

        # Create figure
        fig, ax = setup_publication_plot(
            figsize=(8, 6), title="Ground Truth Level 1: Confusion Matrix", xlabel="", ylabel=""
        )

        # Plot heatmap
        im = ax.imshow(confusion_matrix, cmap="Blues", alpha=0.7)

        # Set ticks and labels
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["System: No Issue", "System: Issue"])
        ax.set_yticklabels(["Clinician: No Issue", "Clinician: Issue"])

        # Add text annotations with labels
        for i in range(2):
            for j in range(2):
                value = confusion_matrix[i, j]
                label = labels[i, j]
                ax.text(
                    j,
                    i,
                    f"{label}\n{value}\n({value / (tp + fp + tn + fn) * 100:.1f}%)",
                    ha="center",
                    va="center",
                    color="black",
                    fontsize=12,
                    fontweight="bold",
                )

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Count", rotation=270, labelpad=20)

        plt.tight_layout()
        return fig
