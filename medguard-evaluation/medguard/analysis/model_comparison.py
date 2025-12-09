"""
Model Comparison Analysis

Compares multiple models across key metrics by analyzing their evaluation logs.
"""

from typing import List

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from inspect_ai.log import EvalSample

from medguard.analysis.base import EvaluationAnalysisBase
from medguard.evaluation.evaluation import Evaluation


def sample_to_values(sample: EvalSample) -> list[float]:
    issue_precision = sample.scores["llm_as_a_judge"].value
    issue_recall = sample.scores["llm_as_a_judge"].value
    intervention_precision = sample.scores["llm_as_a_judge"].value
    intervention_recall = sample.scores["llm_as_a_judge"].value
    score = sample.scores["llm_as_a_judge"].value
    if sample.scores["llm_as_a_judge"].metadata["evaluation_analysis"] is None:
        return [
            score,
            issue_precision,
            issue_recall,
            intervention_precision,
            intervention_recall,
        ]
    return [
        sample.scores["llm_as_a_judge"].value,
        sample.scores["llm_as_a_judge"].metadata["evaluation_analysis"]["issue_precision"]
        or issue_precision,
        sample.scores["llm_as_a_judge"].metadata["evaluation_analysis"]["issue_recall"]
        or issue_recall,
        sample.scores["llm_as_a_judge"].metadata["evaluation_analysis"]["intervention_precision"]
        or intervention_precision,
        sample.scores["llm_as_a_judge"].metadata["evaluation_analysis"]["intervention_recall"]
        or intervention_recall,
    ]


def get_model_data(
    name: str, samples_dict: dict[int, list[EvalSample]]
) -> tuple[str, list[float], list[float]]:
    """
    Calculate mean and SEM for each metric using combined variance (Approach 3).

    Accounts for both between-patient and within-patient variance:
    - Between-patient: How much do different patients differ?
    - Within-patient: How much does the model vary across runs for the same patient?

    Formula: SEM = sqrt(σ²_between/n_patients + σ²_within_pooled/(n_patients × n_runs))

    Args:
        name: Model name
        samples_dict: dict[patient_id, list[EvalSample]] with all runs per patient

    Returns:
        (name, means, sems) where means and sems are lists of 5 values:
        [score, issue_precision, issue_recall, intervention_precision, intervention_recall]
    """
    # For each patient, calculate mean and variance across runs
    patient_means = []
    patient_variances = []
    total_runs = 0

    for patient_id, patient_samples in samples_dict.items():
        # Get values for all runs of this patient
        patient_values = np.array([sample_to_values(sample) for sample in patient_samples])

        # Average across runs for this patient
        patient_mean = np.mean(patient_values, axis=0)
        patient_means.append(patient_mean)

        # Variance across runs for this patient (ddof=1 for sample variance)
        if len(patient_samples) > 1:
            patient_var = np.var(patient_values, axis=0, ddof=1)
        else:
            patient_var = np.zeros_like(patient_mean)  # No variance with single sample
        patient_variances.append(patient_var)

        total_runs += len(patient_samples)

    # Convert to arrays: rows = patients, columns = metrics
    patient_means_array = np.array(patient_means)
    patient_variances_array = np.array(patient_variances)

    # Calculate grand means
    means = [float(x) for x in list(np.mean(patient_means_array, axis=0))]

    # Calculate between-patient variance
    between_patient_var = np.var(patient_means_array, axis=0, ddof=1)

    # Calculate pooled within-patient variance (average across patients)
    pooled_within_var = np.mean(patient_variances_array, axis=0)

    # Combined variance of the grand mean
    n_patients = len(patient_means)
    avg_runs_per_patient = total_runs / n_patients

    # Var(grand_mean) = σ²_between/n_patients + σ²_within/(n_patients × avg_runs)
    var_of_grand_mean = between_patient_var / n_patients + pooled_within_var / (
        n_patients * avg_runs_per_patient
    )

    # SEM = sqrt(Var(grand_mean))
    sems = [float(np.sqrt(v)) for v in var_of_grand_mean]

    return (name, means, sems)


class ModelComparisonAnalysis(EvaluationAnalysisBase):
    """
    Compare multiple models across key performance metrics.

    Requires a list of (name, evaluation) tuples.
    """

    def __init__(self, evaluations: List[tuple[str, Evaluation]], name: str = "model_comparison"):
        # Use the first evaluation as the base for compatibility
        super().__init__(evaluations[0][1], name=name)
        self.evaluations = evaluations

    def execute(self) -> pl.DataFrame:
        """
        Execute analysis and return DataFrame with model comparison metrics.

        SEM calculation accounts for hierarchical data structure (multiple runs per patient)
        using combined variance approach:
        - Between-patient variance: How much do different patients differ?
        - Within-patient variance: How much does the model vary across runs?
        Formula: SEM = sqrt(σ²_between/n_patients + σ²_within/(n_patients × n_runs))

        Returns DataFrame with columns:
        - model_name: Name of the model
        - score: Average score
        - score_sem: SEM for score (combined variance)
        - issue_precision: Average issue precision
        - issue_precision_sem: SEM for issue precision (combined variance)
        - issue_recall: Average issue recall
        - issue_recall_sem: SEM for issue recall (combined variance)
        - intervention_precision: Average intervention precision
        - intervention_precision_sem: SEM for intervention precision (combined variance)
        - intervention_recall: Average intervention recall
        - intervention_recall_sem: SEM for intervention recall (combined variance)
        """
        model_data = []

        for name, evaluation in self.evaluations:
            samples_dict = evaluation.log_samples_dict  # dict[patient_id, list[samples]]
            data = get_model_data(name, samples_dict)
            model_data.append(data)

        df = pl.DataFrame(
            {
                "model_name": [d[0] for d in model_data],
                "score": [d[1][0] for d in model_data],
                "score_sem": [d[2][0] for d in model_data],
                "issue_precision": [d[1][1] for d in model_data],
                "issue_precision_sem": [d[2][1] for d in model_data],
                "issue_recall": [d[1][2] for d in model_data],
                "issue_recall_sem": [d[2][2] for d in model_data],
                "intervention_precision": [d[1][3] for d in model_data],
                "intervention_precision_sem": [d[2][3] for d in model_data],
                "intervention_recall": [d[1][4] for d in model_data],
                "intervention_recall_sem": [d[2][4] for d in model_data],
            }
        )

        return df

    def plot(self) -> List[tuple[plt.Figure, str]]:
        """
        Create visualizations of model comparison metrics.

        Returns:
            List of (figure, suffix) tuples
        """
        df = self.load_df()

        # MedGuard style guide colors
        COLORS = {
            "neutral_dark": "#4A4A4A",
        }

        # Model colors grouped by family (blue spectrum for GPT-OSS 120B, grey for 20B, purple for Gemma)
        MODEL_COLORS = {
            "gpt-oss-120b-low": "#6BAED6",
            "gpt-oss-120b-medium": "#2171B5",
            "gpt-oss-120b-high": "#08306B",
            "gpt-oss-20b-medium": "#737373",
            "gemma": "#9E9AC8",
            "medgemma": "#54278F",
        }

        # Apply MedGuard style
        plt.rcParams.update(
            {
                "font.family": "sans-serif",
                "font.sans-serif": ["Source Sans Pro", "Arial", "Helvetica"],
                "font.size": 8,
                "axes.titlesize": 10,
                "axes.labelsize": 9,
                "legend.fontsize": 7,
                "xtick.labelsize": 8,
                "ytick.labelsize": 8,
                "font.weight": "regular",
                "axes.labelweight": "medium",
                "axes.titleweight": "semibold",
                "axes.spines.top": False,
                "axes.spines.right": False,
                "axes.linewidth": 0.8,
                "axes.edgecolor": COLORS["neutral_dark"],
                "grid.alpha": 0.3,
                "grid.linewidth": 0.5,
                "legend.frameon": False,
                "legend.borderpad": 0.4,
                "figure.facecolor": "white",
                "axes.facecolor": "white",
            }
        )

        figures = []

        # Extract data for plotting
        model_names = df["model_name"].to_list()
        metrics = {
            "Score": df["score"].to_list(),
            "Issue Precision": df["issue_precision"].to_list(),
            "Issue Recall": df["issue_recall"].to_list(),
            "Intervention Precision": df["intervention_precision"].to_list(),
            "Intervention Recall": df["intervention_recall"].to_list(),
        }
        sems = {
            "Score": df["score_sem"].to_list(),
            "Issue Precision": df["issue_precision_sem"].to_list(),
            "Issue Recall": df["issue_recall_sem"].to_list(),
            "Intervention Precision": df["intervention_precision_sem"].to_list(),
            "Intervention Recall": df["intervention_recall_sem"].to_list(),
        }

        # Create grouped bar plot
        fig, ax = plt.subplots(figsize=(7.5, 3.5))

        metric_names = list(metrics.keys())
        n_metrics = len(metric_names)
        n_models = len(model_names)

        # Get all values for automatic y-axis scaling
        all_values = [val for metric_vals in metrics.values() for val in metric_vals]
        min_val = min(all_values)
        max_val = max(all_values)
        ylim_lower = max(0, min_val - 0.05)
        ylim_upper = min(1, max_val + 0.05)

        # Width of each bar and spacing
        bar_width = 0.15
        x = np.arange(n_metrics)

        # Get colors for each model (use MODEL_COLORS if available, else generate from blue/purple spectrum)
        def get_model_color(model_name: str, index: int, total: int) -> str:
            # Check for exact match in MODEL_COLORS
            if model_name in MODEL_COLORS:
                return MODEL_COLORS[model_name]
            # Check for partial match (case-insensitive)
            model_lower = model_name.lower()
            for key, color in MODEL_COLORS.items():
                if key in model_lower or model_lower in key:
                    return color
            # Fallback: generate color from blue-purple spectrum
            if total <= 1:
                return "#2171B5"
            hue_start = 0.55  # Blue
            hue_end = 0.75  # Purple
            hue = hue_start + (hue_end - hue_start) * (index / (total - 1))
            import colorsys

            rgb = colorsys.hsv_to_rgb(hue, 0.6, 0.7)
            return f"#{int(rgb[0] * 255):02x}{int(rgb[1] * 255):02x}{int(rgb[2] * 255):02x}"

        colors = [get_model_color(name, i, n_models) for i, name in enumerate(model_names)]

        # Create bars for each model
        for i, model_name in enumerate(model_names):
            values = [metrics[metric][i] for metric in metric_names]
            errors = [sems[metric][i] for metric in metric_names]
            offset = (i - n_models / 2 + 0.5) * bar_width
            ax.bar(
                x + offset,
                values,
                bar_width,
                label=model_name,
                yerr=errors,
                capsize=2,
                error_kw={"linewidth": 0.5, "elinewidth": 0.5, "capthick": 0.5},
                color=colors[i],
                edgecolor=COLORS["neutral_dark"],
                linewidth=0.8,
            )

        # Customize plot
        ax.set_xlabel("Metric", fontsize=9, fontweight="medium")
        ax.set_ylabel("Value", fontsize=9, fontweight="medium")
        ax.set_title(
            "Model Performance Comparison Across Metrics",
            fontsize=10,
            fontweight="semibold",
            pad=12,
        )
        ax.set_xticks(x)
        ax.set_xticklabels(metric_names)
        ax.legend(loc="upper right", frameon=False, fontsize=7)
        ax.grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)
        ax.set_ylim(0, ylim_upper)

        plt.tight_layout()

        figures.append((fig, "_comparison"))

        return figures

    def save_figure_to_pdf(self, fig: plt.Figure, suffix: str = ""):
        """Save matplotlib figure to PDF file."""
        from pathlib import Path

        filename = f"{self.name}{suffix}.pdf" if suffix else f"{self.name}.pdf"
        output_path = self.plots_dir / filename
        fig.savefig(output_path, format="pdf", bbox_inches="tight")
        plt.close(fig)
        return output_path

    def run_figure_pdf(self) -> list:
        """Generate plot(s) and save to PDF."""
        result = self.plot()
        if result is None:
            return []

        paths = []
        for item in result:
            if isinstance(item, tuple) and len(item) == 2:
                fig, fig_suffix = item
                paths.append(self.save_figure_to_pdf(fig, suffix=fig_suffix))
        return paths


if __name__ == "__main__":
    from medguard.utils.parsing import load_pydantic_from_json

    print("Loading model evaluations...")
    model_evaluations: list[tuple[str, Evaluation]] = [
        (
            "gpt-oss-120b-low",
            load_pydantic_from_json(
                Evaluation, "outputs/20251104/gpt-oss-120b-low/evaluation.json"
            ).clean(),
        ),
        (
            "gpt-oss-120b-medium",
            load_pydantic_from_json(
                Evaluation, "outputs/20251104/gpt-oss-120b-medium/evaluation.json"
            ).clean(),
        ),
        (
            "gpt-oss-120b-high",
            load_pydantic_from_json(
                Evaluation, "outputs/20251104/gpt-oss-120b-high/evaluation.json"
            ).clean(),
        ),
        (
            "gpt-oss-20b-medium",
            load_pydantic_from_json(
                Evaluation, "outputs/20251104/gpt-oss-20b-medium/evaluation.json"
            ).clean(),
        ),
        (
            "gemma",
            load_pydantic_from_json(Evaluation, "outputs/20251104/gemma/evaluation.json").clean(),
        ),
        (
            "medgemma",
            load_pydantic_from_json(
                Evaluation, "outputs/20251104/medgemma/evaluation.json"
            ).clean(),
        ),
    ]

    print(f"Loaded {len(model_evaluations)} models")

    analysis = ModelComparisonAnalysis(model_evaluations)
    df, path = analysis.run()
    print(f"\nSaved data to: {path}")
    print(df)

    print("\nGenerating PNG plots...")
    fig_paths = analysis.run_figure()
    for p in fig_paths:
        print(f"  Saved: {p}")

    print("\nGenerating PDF plots...")
    pdf_paths = analysis.run_figure_pdf()
    for p in pdf_paths:
        print(f"  Saved: {p}")
