"""
PINCER Filter Binary Classification Metrics (Level 1)

Evaluates the system's ability to detect ANY issue (Level 1) against PINCER filters.

Binary classification:
- TP = positive_gt_any_issue (PINCER flagged, System found issues)
- FP = negative_gt_any_issue (PINCER didn't flag, System found issues)
- TN = negative_gt_no_issue (PINCER didn't flag, System found no issues)
- FN = positive_gt_no_issue (PINCER flagged, System found no issues)

Section: 3.3.1 (Level 1 Performance)
"""

import matplotlib.pyplot as plt
import polars as pl
import numpy as np

from medguard.analysis.base import EvaluationAnalysisBase
from medguard.analysis.utils import setup_publication_plot


class PincerBinaryMetricsAnalysis(EvaluationAnalysisBase):
    """
    Calculate binary classification metrics for Level 1 (issue detection) against PINCER filters.

    Treats the task as: Does the system detect ANY issue when PINCER flags the case?
    """

    def __init__(self, evaluation, name: str = "pincer_binary_metrics"):
        super().__init__(evaluation, name=name)

    def execute(self) -> pl.DataFrame:
        """
        Execute analysis and return DataFrame with binary classification metrics.

        Returns DataFrame with columns:
        - metric: Name of the metric (TP, FP, TN, FN, Precision, Recall, F1, Accuracy, Specificity)
        - value: Value of the metric
        - description: Human-readable description
        """
        # Exclude data errors to match ground truth analysis
        evaluation = self.evaluation.exclude_data_errors()

        # Get filter performance metrics from the evaluation
        # These are already computed and stored
        metrics = evaluation.performance_metrics

        # Extract binary classification counts (using the properties)
        TP = metrics.TP  # positive_gt_any_issue
        FP = metrics.FP  # negative_gt_any_issue
        TN = metrics.TN  # negative_gt_no_issue
        FN = metrics.FN  # positive_gt_no_issue

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
                "description": "True Positives (PINCER flagged, System found issues)",
            },
            {
                "metric": "FP",
                "value": FP,
                "description": "False Positives (PINCER didn't flag, System found issues)",
            },
            {
                "metric": "TN",
                "value": TN,
                "description": "True Negatives (PINCER didn't flag, System found no issues)",
            },
            {
                "metric": "FN",
                "value": FN,
                "description": "False Negatives (PINCER flagged, System found no issues)",
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
        confusion_matrix = np.array([[tn, fp], [fn, tp]])
        labels = np.array(
            [["True Negative", "False Positive"], ["False Negative", "True Positive"]]
        )

        # Create figure
        fig, ax = setup_publication_plot(
            figsize=(8, 6), title="PINCER Filter Level 1: Confusion Matrix", xlabel="", ylabel=""
        )

        # Plot heatmap
        im = ax.imshow(confusion_matrix, cmap="Blues", alpha=0.7)

        # Set ticks and labels
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["PINCER: No Flag", "PINCER: Flag"])
        ax.set_yticklabels(["System: No Issue", "System: Issue"])

        # Add text annotations with labels
        for i in range(2):
            for j in range(2):
                value = confusion_matrix[i, j]
                label = labels[i, j]
                text = ax.text(
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
