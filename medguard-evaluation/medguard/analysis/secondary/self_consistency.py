"""
Self-Consistency Analysis

Analyzes score variability across multiple evaluation runs for the same patients.
This measures how consistent the model's predictions are when given the same input
multiple times.
"""

from collections import defaultdict
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from medguard.analysis.base import EvaluationAnalysisBase


class SelfConsistencyAnalysis(EvaluationAnalysisBase):
    """
    Calculate self-consistency metrics from multiple evaluation runs.

    Requires that evaluation.logs_path points to a log file with multiple runs per patient.
    """

    def __init__(
        self, evaluation, name: str = "self_consistency", bin_max: float = 0.5, bin_number: int = 11
    ):
        super().__init__(evaluation, name=name)

        self.bin_max = bin_max
        self.bin_number = bin_number

    def execute(self) -> pl.DataFrame:
        """
        Execute analysis and return DataFrame with self-consistency metrics.

        Returns DataFrame with columns:
        - patient_id: Patient identifier
        - n_runs: Number of evaluation runs for this patient
        - mean_score: Mean score across runs
        - std_dev: Standard deviation of scores
        - min_score: Minimum score
        - max_score: Maximum score
        - score_range: Max - min
        """
        # Get all samples including duplicates from all log files
        log_samples = self.evaluation.log_samples  # All samples including duplicates

        if not log_samples:
            raise ValueError("No log samples found. Ensure logs_path is set in the evaluation.")

        scores = defaultdict(list)

        for sample in log_samples:
            patient_id = sample.metadata["patient_id"]
            score = sample.scores["llm_as_a_judge"].value
            scores[patient_id].append(score)

        rows = []
        for patient_id, score_list in scores.items():
            if len(score_list) < 2:
                continue

            score_array = np.array(score_list)
            rows.append(
                {
                    "patient_id": patient_id,
                    "n_runs": len(score_list),
                    "mean_score": np.mean(score_array),
                    "std_dev": np.std(score_array, ddof=1),
                    "min_score": np.min(score_array),
                    "max_score": np.max(score_array),
                    "score_range": np.max(score_array) - np.min(score_array),
                }
            )

        return pl.DataFrame(rows).sort("std_dev", descending=True)

    def plot(self) -> List[tuple[plt.Figure, str]]:
        """
        Create visualizations of self-consistency metrics.

        Returns:
            List of (figure, suffix) tuples
        """
        df = self.load_df()

        plt.style.use("seaborn-v0_8-paper")
        plt.rcParams["font.size"] = 11

        figures = []

        # Histogram of standard deviations
        fig, ax = plt.subplots(figsize=(8, 6))

        stds = df["std_dev"].to_numpy()
        n_patients = len(stds)
        n_runs = df["n_runs"].to_list()[0]

        ax.hist(
            stds, bins=np.linspace(0, self.bin_max, self.bin_number), edgecolor="black", alpha=0.7
        )
        ax.axvline(
            np.mean(stds),
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Mean: {np.mean(stds):.3f}",
        )
        ax.axvline(
            np.median(stds),
            color="darkred",
            linestyle=":",
            linewidth=2,
            label=f"Median: {np.median(stds):.3f}",
        )

        ax.set_xlabel("Within-patient standard deviation", fontsize=12)
        ax.set_ylabel("Number of patients", fontsize=12)
        ax.set_title(
            f"Self-consistency: score variability (N={n_patients} patients, {n_runs} runs each)",
            fontsize=13,
        )
        ax.legend()

        plt.tight_layout()
        figures.append((fig, "_histogram"))

        return figures
