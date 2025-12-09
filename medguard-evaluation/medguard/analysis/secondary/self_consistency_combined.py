"""
Self-Consistency Combined Analysis

Creates a single plot showing overlaid histograms of score variability for both:
1. Model self-consistency (multiple runs of the same model)
2. Scorer variation (multiple scorer runs on the same outputs)

Uses twin y-axes to handle different scales.
"""

from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import polars as pl

from medguard.analysis.base import EvaluationAnalysisBase


class SelfConsistencyCombinedAnalysis(EvaluationAnalysisBase):
    """
    Combined self-consistency analysis comparing model and scorer variability.

    Takes two evaluations:
    - Model self-consistency: Same model run multiple times
    - Scorer variation: Same outputs scored multiple times
    """

    def __init__(
        self,
        model_evaluation,
        scorer_evaluation,
        name: str = "self_consistency_combined",
    ):
        # Use first evaluation for base class initialization
        super().__init__(model_evaluation, name=name)
        self.model_evaluation = model_evaluation
        self.scorer_evaluation = scorer_evaluation

    def execute(self) -> pl.DataFrame:
        """
        Execute analysis and return DataFrame with both variability metrics.

        Returns DataFrame with columns:
        - patient_id: Patient identifier
        - model_n_runs: Number of model runs
        - model_std_dev: Standard deviation of model scores
        - scorer_n_runs: Number of scorer runs
        - scorer_std_dev: Standard deviation of scorer scores
        """
        # Calculate model variability
        model_scores = self._extract_scores(self.model_evaluation)
        model_stats = self._calculate_stats(model_scores)

        # Calculate scorer variability
        scorer_scores = self._extract_scores(self.scorer_evaluation)
        scorer_stats = self._calculate_stats(scorer_scores)

        # Combine into single dataframe
        rows = []
        all_patient_ids = set(model_stats.keys()) | set(scorer_stats.keys())

        for patient_id in all_patient_ids:
            row = {"patient_id": patient_id}

            if patient_id in model_stats:
                row.update(
                    {
                        "model_n_runs": model_stats[patient_id]["n_runs"],
                        "model_std_dev": model_stats[patient_id]["std_dev"],
                        "model_mean_score": model_stats[patient_id]["mean_score"],
                    }
                )
            else:
                row.update({"model_n_runs": 0, "model_std_dev": None, "model_mean_score": None})

            if patient_id in scorer_stats:
                row.update(
                    {
                        "scorer_n_runs": scorer_stats[patient_id]["n_runs"],
                        "scorer_std_dev": scorer_stats[patient_id]["std_dev"],
                        "scorer_mean_score": scorer_stats[patient_id]["mean_score"],
                    }
                )
            else:
                row.update({"scorer_n_runs": 0, "scorer_std_dev": None, "scorer_mean_score": None})

            rows.append(row)

        return pl.DataFrame(rows).sort("model_std_dev", descending=True)

    def _extract_scores(self, evaluation) -> dict[int, list[float]]:
        """Extract scores from evaluation log samples."""
        log_samples = evaluation.log_samples

        if not log_samples:
            return {}

        scores = defaultdict(list)
        for sample in log_samples:
            patient_id = sample.metadata["patient_id"]
            score = sample.scores["llm_as_a_judge"].value
            scores[patient_id].append(score)

        return scores

    def _calculate_stats(self, scores: dict[int, list[float]]) -> dict[int, dict]:
        """Calculate statistics for each patient's scores."""
        stats = {}
        for patient_id, score_list in scores.items():
            if len(score_list) < 2:
                continue

            score_array = np.array(score_list)
            stats[patient_id] = {
                "n_runs": len(score_list),
                "mean_score": np.mean(score_array),
                "std_dev": np.std(score_array, ddof=1),
            }

        return stats

    def plot(self) -> plt.Figure:
        """
        Create overlaid histograms of model and scorer variability.

        Returns:
            Single matplotlib figure with twin y-axes
        """
        df = self.load_df()

        # Set publication style
        plt.style.use("seaborn-v0_8-paper")
        plt.rcParams["font.size"] = 11
        plt.rcParams["axes.labelsize"] = 12
        plt.rcParams["axes.titlesize"] = 13

        # Create figure with twin axes
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax2 = ax1.twinx()

        # Extract data
        model_stds = df.filter(pl.col("model_std_dev").is_not_null())["model_std_dev"].to_numpy()
        scorer_stds = df.filter(pl.col("scorer_std_dev").is_not_null())["scorer_std_dev"].to_numpy()

        # Get run counts
        model_n_runs = df.filter(pl.col("model_n_runs") > 0)["model_n_runs"].to_list()[0]
        scorer_n_runs = df.filter(pl.col("scorer_n_runs") > 0)["scorer_n_runs"].to_list()[0]

        # Define bins (doubled granularity for model to match scorer)
        model_bins = np.linspace(0, 0.5, 21)
        scorer_bins = np.linspace(0, 0.3, 13)

        # Plot model histogram on ax1
        counts1, _, patches1 = ax1.hist(
            model_stds,
            bins=model_bins,
            edgecolor="black",
            alpha=0.6,
            color="#3498db",
            label=f"Model variability (n={len(model_stds)})",
        )

        # Plot scorer histogram on ax2
        counts2, _, patches2 = ax2.hist(
            scorer_stds,
            bins=scorer_bins,
            edgecolor="black",
            alpha=0.6,
            color="#e74c3c",
            label=f"Scorer variability (n={len(scorer_stds)})",
        )

        # Add mean lines
        model_mean = np.mean(model_stds)
        scorer_mean = np.mean(scorer_stds)

        ax1.axvline(
            model_mean,
            color="#2471a3",
            linestyle="--",
            linewidth=2,
            label=f"Model mean: {model_mean:.3f}",
        )

        ax1.axvline(
            scorer_mean,
            color="#c0392b",
            linestyle="--",
            linewidth=2,
            label=f"Scorer mean: {scorer_mean:.3f}",
        )

        # Labels and styling
        ax1.set_xlabel("Within-patient standard deviation", fontweight="bold")
        ax1.set_ylabel("Model: Number of patients", fontweight="bold", color="#3498db")
        ax2.set_ylabel("Scorer: Number of patients", fontweight="bold", color="#e74c3c")
        ax1.set_title(
            f"Self-consistency variability: Model ({model_n_runs} runs) vs Scorer ({scorer_n_runs} runs)",
            fontweight="bold",
            pad=20,
        )

        # Color y-axis labels to match histograms
        ax1.tick_params(axis="y", labelcolor="#3498db")
        ax2.tick_params(axis="y", labelcolor="#e74c3c")

        # Grid
        ax1.grid(axis="y", alpha=0.3, linestyle="--")

        # Combined legend from both axes
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

        plt.tight_layout()
        return fig


if __name__ == "__main__":
    from medguard.evaluation.evaluation import Evaluation
    from medguard.utils.parsing import load_pydantic_from_json

    print("Loading evaluations for self-consistency analysis...")

    print("\n1. Loading model self-consistency evaluation...")
    model_evaluation = load_pydantic_from_json(
        Evaluation, "outputs/20251104/gpt-oss-120b-medium/evaluation.json"
    )
    model_evaluation = model_evaluation.clean()
    print(f"   - Loaded {len(model_evaluation.patient_ids())} patients")

    print("\n2. Loading scorer variation evaluation...")
    scorer_evaluation = load_pydantic_from_json(
        Evaluation,
        "outputs/20251104/gpt-oss-120b-medium-fixed-output-test-scoring/evaluation.json",
    )
    scorer_evaluation = scorer_evaluation.clean()
    print(f"   - Loaded {len(scorer_evaluation.patient_ids())} patients")

    print("\nRunning combined analysis...")
    analysis = SelfConsistencyCombinedAnalysis(model_evaluation, scorer_evaluation)
    df, csv_path = analysis.run()
    print(f"Saved CSV to: {csv_path}")
    print(f"\nDataFrame preview:\n{df}")

    print("\nGenerating plot...")
    fig_path = analysis.run_figure()
    print(f"Saved figure to: {fig_path}")
    print("\n✓ Analysis complete!")
