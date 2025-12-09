"""
Issue-Level Precision Distribution for Partially Correct Cases

Analyzes the distribution of issue-level precision among cases where MedGuard
identified issues but did not achieve 100% correctness. This helps characterize
the "partially correct" cases from Level 2 evaluation.

Section: 3.3.2 (Level 2 Performance - Partial Correctness Analysis)
"""

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from medguard.analysis.base import EvaluationAnalysisBase
from medguard.analysis.utils import setup_publication_plot


class IssuePrecisionDistributionAnalysis(EvaluationAnalysisBase):
    """
    Calculate and visualize issue-level precision for partially correct cases.

    For each patient where MedGuard identified issues, calculates:
    precision = (# correct issues) / (# total issues identified)

    Analysis focuses on partial correctness (0% < precision < 100%).
    """

    def __init__(self, evaluation, name: str = "issue_precision_distribution"):
        super().__init__(evaluation, name=name)

    def execute(self) -> pl.DataFrame:
        """
        Execute analysis and return DataFrame with precision distribution.

        Returns DataFrame with columns:
        - precision_bin: Bin label (e.g., "0-20%", "20-40%")
        - count: Number of patients in this bin
        - percentage: Percentage of partial-correct patients in this bin
        - bin_min: Lower bound of bin
        - bin_max: Upper bound of bin
        """
        # Get clinician evaluations (already filtered for data errors)
        clinician_evals = self.evaluation.clinician_evaluations_dict

        # Calculate issue-level precision for each patient
        issue_precisions = []
        for patient_id, stage2 in clinician_evals.items():
            # Skip if no issues were identified by MedGuard
            if len(stage2.issue_assessments) == 0:
                continue

            # Calculate proportion of issues that were correct
            n_correct = sum(stage2.issue_assessments)
            n_total = len(stage2.issue_assessments)
            precision = n_correct / n_total if n_total > 0 else 0

            issue_precisions.append(
                {
                    "patient_id": patient_id,
                    "n_issues_identified": n_total,
                    "n_issues_correct": n_correct,
                    "precision": precision,
                }
            )

        # Filter to partial correctness only (exclude 0% and 100%)
        partial_correct = [p for p in issue_precisions if 0 < p["precision"] < 1.0]

        total_partial = len(partial_correct)

        # Create bins (10 bins of 10% each)
        bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        bin_labels = [
            "0-10%",
            "10-20%",
            "20-30%",
            "30-40%",
            "40-50%",
            "50-60%",
            "60-70%",
            "70-80%",
            "80-90%",
            "90-100%",
        ]

        # Calculate histogram
        precisions = [p["precision"] for p in partial_correct]
        counts, _ = np.histogram(precisions, bins=bins)

        # Build result DataFrame
        rows = []
        for i, (label, count) in enumerate(zip(bin_labels, counts)):
            percentage = (count / total_partial * 100) if total_partial > 0 else 0
            rows.append(
                {
                    "precision_bin": label,
                    "count": int(count),
                    "percentage": percentage,
                    "bin_min": bins[i],
                    "bin_max": bins[i + 1],
                }
            )

        # Add summary statistics
        if total_partial > 0:
            rows.append(
                {
                    "precision_bin": "SUMMARY: Mean",
                    "count": total_partial,
                    "percentage": np.mean(precisions) * 100,
                    "bin_min": None,
                    "bin_max": None,
                }
            )
            rows.append(
                {
                    "precision_bin": "SUMMARY: Median",
                    "count": total_partial,
                    "percentage": np.median(precisions) * 100,
                    "bin_min": None,
                    "bin_max": None,
                }
            )

        return pl.DataFrame(rows)

    def plot(self) -> plt.Figure:
        """
        Create histogram of issue precision distribution.

        Returns:
            Matplotlib figure
        """
        df = self.load_df()

        # Filter out summary rows
        plot_df = df.filter(~pl.col("precision_bin").str.contains("SUMMARY"))

        # Extract data
        bins = plot_df["precision_bin"].to_list()
        counts = plot_df["count"].to_list()
        percentages = plot_df["percentage"].to_list()

        # Create figure
        fig, ax = setup_publication_plot(
            figsize=(14, 6),
            title="Issue-Level Precision Distribution for Partial Correctness Cases",
            xlabel="Issue-Level Precision",
            ylabel="Number of Patients",
        )

        # Create bar plot
        x = np.arange(len(bins))
        bars = ax.bar(x, counts, color="steelblue", alpha=0.7, edgecolor="black")

        # Add percentage labels on bars (skip zero counts)
        for i, (bar, pct) in enumerate(zip(bars, percentages)):
            if counts[i] > 0:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    f"{int(counts[i])}\n({pct:.1f}%)",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold",
                )

        # Set x-axis labels
        ax.set_xticks(x)
        ax.set_ylim([0, 25])
        ax.set_xticklabels(bins, rotation=45, ha="right")

        # Add summary text
        summary_df = df.filter(pl.col("precision_bin").str.contains("SUMMARY"))
        if len(summary_df) > 0:
            total = summary_df.filter(pl.col("precision_bin") == "SUMMARY: Mean")["count"][0]
            mean = summary_df.filter(pl.col("precision_bin") == "SUMMARY: Mean")["percentage"][0]
            median = summary_df.filter(pl.col("precision_bin") == "SUMMARY: Median")["percentage"][
                0
            ]

            summary_text = (
                f"Partial Correctness Cases: n={total}\n"
                f"Mean Precision: {mean:.1f}%\n"
                f"Median Precision: {median:.1f}%"
            )
            ax.text(
                0.98,
                0.97,
                summary_text,
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment="top",
                horizontalalignment="right",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
            )

        plt.tight_layout()
        return fig


if __name__ == "__main__":
    from medguard.evaluation.evaluation import Evaluation, merge_evaluations
    from medguard.utils.parsing import load_pydantic_from_json

    print("Loading 300-patient cohort (200 + 100 merged)...")
    evaluation_200 = load_pydantic_from_json(
        Evaluation, "outputs/20251018/test-set/evaluation.json"
    )
    evaluation_100 = load_pydantic_from_json(
        Evaluation, "outputs/20251027/no-filters/evaluation.json"
    )
    print(f"  - Loaded {len(evaluation_200.patient_ids())} from test-set")
    print(f"  - Loaded {len(evaluation_100.patient_ids())} from no-filters")

    evaluation = merge_evaluations([evaluation_100, evaluation_200])
    print(f"  - Merged: {len(evaluation.patient_ids())} patients total")

    evaluation = evaluation.clean()
    print(f"  - After clean(): {len(evaluation.patient_ids())} evaluable patients")

    print("\nRunning issue precision distribution analysis...")
    analysis = IssuePrecisionDistributionAnalysis(evaluation)
    df, csv_path = analysis.run()
    print(f"Saved CSV to: {csv_path}")
    print(f"\nDataFrame preview:\n{df}")

    print("\nGenerating plot...")
    fig_path = analysis.run_figure()
    print(f"Saved figure to: {fig_path}")
    print("\n✓ Analysis complete!")
