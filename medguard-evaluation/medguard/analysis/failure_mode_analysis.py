"""
Failure Mode Analysis

Analyzes the distribution of failure modes identified by clinicians in their evaluations.
"""

from collections import defaultdict

import matplotlib.pyplot as plt
import polars as pl

from medguard.analysis.base import EvaluationAnalysisBase
from medguard.analysis.filters import no_data_error


class FailureModeAnalysis(EvaluationAnalysisBase):
    """Analyze failure mode frequencies from clinician evaluations."""

    def __init__(self, evaluation, name: str = "failure_mode_analysis"):
        super().__init__(evaluation, name=name)

    def execute(self) -> pl.DataFrame:
        """
        Execute analysis and return DataFrame.

        Returns DataFrame with:
        - failure_mode: Name of the failure mode
        - count: Number of occurrences
        """
        # Filter to evaluations with no data errors
        ids_no_error = self.evaluation.filter_by_clinician_evaluation(no_data_error())
        filtered_eval = self.evaluation.filter_by_patient_ids(ids_no_error)

        # Count failure modes
        failure_modes = defaultdict(int)
        for eval in filtered_eval.clinician_evaluations:
            for failure_mode in eval.failure_modes:
                failure_modes[failure_mode] += 1

        # Convert to list of dicts sorted by count
        rows = [
            {"failure_mode": mode, "count": count}
            for mode, count in sorted(failure_modes.items(), key=lambda x: x[1], reverse=True)
        ]

        return pl.DataFrame(rows)

    def plot(self) -> plt.Figure:
        """Create bar chart of failure mode frequencies."""
        df = self.load_df()

        plt.style.use("seaborn-v0_8-paper")
        plt.rcParams["font.size"] = 11

        fig, ax = plt.subplots(figsize=(12, 6))

        failure_modes = df["failure_mode"].to_list()
        counts = df["count"].to_list()
        x = range(len(failure_modes))

        bars = ax.bar(x, counts, color="#e74c3c", alpha=0.8, edgecolor="black", linewidth=0.5)

        # Format failure mode labels (replace underscores with spaces, capitalize)
        labels = [mode.replace("_", " ").title() for mode in failure_modes]

        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_ylabel("Number of Occurrences", fontweight="bold")
        ax.set_xlabel("Failure Mode", fontweight="bold")
        ax.set_title(
            "Distribution of Failure Modes in Clinician Evaluations", fontweight="bold", pad=20
        )
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.set_ylim(0, 45)

        # Add count labels on top of bars
        max_count = max(counts) if counts else 0
        for i, count in enumerate(counts):
            ax.text(
                i,
                count + max_count * 0.02,
                str(count),
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )

        plt.tight_layout()
        return fig
