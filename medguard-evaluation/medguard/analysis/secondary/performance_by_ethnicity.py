"""
Performance by Ethnicity Analysis

Evaluates whether medication safety assessment performance varies across
self-identified ethnicity groups (White, Asian, Black) as identified in the
Office for National Statistics (ONS) classification.

Evaluation approach:
- 200-patient test set stratified to include representation across major UK ethnicities
- 3 independent epochs per ethnicity group for robustness assessment
- Comparison of both mean performance and within-group variability

Section: 3.3.7 (Variation with Ethnicity)
"""

from pathlib import Path
import numpy as np
import polars as pl
import matplotlib.pyplot as plt
from medguard.evaluation.pipeline import read_eval_log_samples
from medguard.analysis.base import EvaluationAnalysisBase


class PerformanceByEthnicityAnalysis(EvaluationAnalysisBase):
    """
    Analyze system performance across ethnicity groups.

    Loads pre-computed ethnicity evaluation logs from inspect-ai runs
    and compares performance metrics.
    """

    def __init__(self, evaluation, name: str = "performance_by_ethnicity"):
        super().__init__(evaluation, name=name)

    def execute(self) -> pl.DataFrame:
        """
        Extract scores from ethnicity evaluation logs.

        Returns DataFrame with:
        - ethnicity: Ethnicity group
        - n_patients: Number of unique patients evaluated
        - n_evaluations: Total evaluations (patients × epochs)
        - mean_score: Mean LLM-as-a-judge score
        - std_dev: Standard deviation of scores
        - sem: Standard error of the mean
        - median_score: Median score
        - q25, q75: 25th and 75th percentiles
        """

        log_paths = {
            "White": Path("outputs/logs/2025-11-03T17-20-33+00-00_test-ethnicity-white.eval"),
            "Asian": Path("outputs/logs/2025-11-03T17-23-39+00-00_test-ethnicity-asian.eval"),
            "Black": Path("outputs/logs/2025-11-03T17-24-03+00-00_test-ethnicity-black.eval"),
        }

        rows = []

        for ethnicity, log_path in log_paths.items():
            # Read evaluation samples
            samples = read_eval_log_samples(log_path)

            # Extract scores
            scores = [s.scores["llm_as_a_judge"].value for s in samples]

            # Calculate statistics
            mean_score = float(np.mean(scores))
            std_dev = float(np.std(scores))
            sem = float(std_dev / np.sqrt(len(scores)))
            median_score = float(np.median(scores))
            q25 = float(np.percentile(scores, 25))
            q75 = float(np.percentile(scores, 75))

            rows.append(
                {
                    "ethnicity": ethnicity,
                    "n_patients": len(scores),  # Each unique patient
                    "n_evaluations": len(scores),  # Total evaluations (patients × epochs)
                    "mean_score": mean_score,
                    "std_dev": std_dev,
                    "sem": sem,
                    "median_score": median_score,
                    "q25": q25,
                    "q75": q75,
                }
            )

        return pl.DataFrame(rows)

    def plot(self) -> plt.Figure | None:
        """Create visualization comparing performance across ethnicities."""
        df = self.load_df()

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Plot 1: Mean scores with error bars
        ethnicities = df["ethnicity"].to_list()
        means = df["mean_score"].to_list()
        sems = df["sem"].to_list()

        ax1.bar(
            ethnicities,
            means,
            yerr=sems,
            capsize=5,
            alpha=0.7,
            color=["#1f77b4", "#ff7f0e", "#2ca02c"],
        )
        ax1.set_ylabel("Mean Score")
        ax1.set_xlabel("Ethnicity")
        ax1.set_ylim([0, 1])
        ax1.set_title("Mean Performance by Ethnicity")
        ax1.axhline(y=np.mean(means), color="r", linestyle="--", alpha=0.5, label="Overall Mean")
        ax1.legend()

        # Plot 2: Variability (std dev)
        std_devs = df["std_dev"].to_list()
        ax2.bar(ethnicities, std_devs, alpha=0.7, color=["#1f77b4", "#ff7f0e", "#2ca02c"])
        ax2.set_ylabel("Standard Deviation")
        ax2.set_xlabel("Ethnicity")
        ax2.set_title("Score Variability by Ethnicity")
        ax2.axhline(y=np.mean(std_devs), color="r", linestyle="--", alpha=0.5, label="Overall Mean")
        ax2.legend()

        plt.tight_layout()
        return fig
