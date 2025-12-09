"""
Figure 1 Composite Analysis - Main paper figure combining three visualizations.

This analysis creates the main paper figure (Figure 1) with three panels:
- (a) Hierarchical evaluation stages showing progression from binary classification to intervention correctness
- (b) Confusion matrix for binary classification (Level 1)
- (c) Failure mode categories by level

Data sources:
- Panels (a) and (b): Ground truth performance metrics from clinician evaluations
- Panel (c): Annotated failure vignettes from outputs/failure_vignettes/vignettes_index_annotated.csv
"""

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Patch

from medguard.analysis.base import EvaluationAnalysisBase
from medguard.evaluation.performance_metrics.ground_truth.performance_metrics import (
    clinician_evaluations_to_performance_metrics,
)

# MedGuard color palette (matching notebook)
COLORS = {
    "correct": "#2D7D90",
    "true_negative": "#7CB4B8",
    "failure_level_3": "#F0C05A",
    "failure_level_2": "#E07B4C",
    "false_negative": "#C44D56",
    "neutral_dark": "#4A4A4A",
}

# Failure mode categories and their CSV columns
# These must match the notebook (playground.ipynb) exactly
FAILURE_CATEGORIES = {
    "Acts decisively when uncertainty should prompt further information gathering": [
        "further-information",
        "missed-issue/missed-issue",
    ],
    "Applies standardised guidelines without adjusting for individual patient context": [
        "nuance",
        "missed-issue/missed-deprescription-opportunity",
    ],
    "Understands formal documentation but misunderstands how healthcare is actually delivered": [
        "duplicate prescription errors",
        "clinician-context",
    ],
    "Produces sensible clinical reasoning structure but unreliable about factual content": [
        "hallucination",
        "understanding-drug-context",
        "incorrect-understanding-guidelines",
    ],
    "Identifies correct clinical endpoints but recommends unsafe pathways to reach them": [
        "too-aggressive",
        "too-aggressive/gradual-taper",
    ],
}


class Figure1CompositeAnalysis(EvaluationAnalysisBase):
    """
    Generate Figure 1 composite visualization for the paper.

    Combines three panels:
    - (a) Hierarchical stages stacked bar chart
    - (b) Confusion matrix
    - (c) Failure mode categories by level
    """

    def __init__(
        self,
        evaluation,
        name: str = "figure_1_composite",
        failure_vignettes_path: str = "outputs/failure_vignettes/vignettes_index_annotated.csv",
    ):
        super().__init__(evaluation, name=name)
        self.failure_vignettes_path = Path(failure_vignettes_path)

    def execute(self) -> pl.DataFrame:
        """
        Compute all metrics needed for Figure 1.

        Returns DataFrame with columns:
        - metric_type: 'ground_truth' or 'failure_mode'
        - metric_name: Name of the metric
        - level_1, level_2, level_3: Values by level (for failure modes)
        - value: Single value (for ground truth metrics)
        """
        evaluation = self.evaluation.exclude_data_errors()
        metrics = clinician_evaluations_to_performance_metrics(evaluation.clinician_evaluations)

        rows = []

        # Ground truth metrics for panels (a) and (b)
        gt_metrics = {
            "positive": metrics.positive,
            "negative": metrics.negative,
            "positive_any_issue": metrics.positive_any_issue,
            "positive_no_issue": metrics.positive_no_issue,
            "negative_any_issue": metrics.negative_any_issue,
            "negative_no_issue": metrics.negative_no_issue,
            "positive_all_correct": metrics.positive_all_correct,
            "positive_some_correct": metrics.positive_some_correct,
            "positive_no_correct": metrics.positive_no_correct,
            "all_correct_correct_intervention": metrics.all_correct_correct_intervention,
            "all_correct_partial_intervention": metrics.all_correct_partial_intervention,
            "all_correct_incorrect_intervention": metrics.all_correct_incorrect_intervention,
            "some_correct_correct_intervention": metrics.some_correct_correct_intervention,
            "some_correct_partial_intervention": metrics.some_correct_partial_intervention,
            "some_correct_incorrect_intervention": metrics.some_correct_incorrect_intervention,
        }

        for name, value in gt_metrics.items():
            rows.append(
                {
                    "metric_type": "ground_truth",
                    "metric_name": name,
                    "value": value,
                    "level_1": None,
                    "level_2": None,
                    "level_3": None,
                }
            )

        # Failure mode categories for panel (c)
        if self.failure_vignettes_path.exists():
            failure_df = pl.read_csv(str(self.failure_vignettes_path), encoding="utf8-lossy")
            for cat_name, cols in FAILURE_CATEGORIES.items():
                l1_patients, l2_patients, l3_patients = set(), set(), set()
                for col in cols:
                    if col in failure_df.columns:
                        l1_ids = (
                            failure_df.filter((pl.col(col) == "Y") & (pl.col("level") == 1))
                            .select("patient_id_hash")["patient_id_hash"]
                            .to_list()
                        )
                        l1_patients.update(l1_ids)
                        l2_ids = (
                            failure_df.filter((pl.col(col) == "Y") & (pl.col("level") == 2))
                            .select("patient_id_hash")["patient_id_hash"]
                            .to_list()
                        )
                        l2_patients.update(l2_ids)
                        l3_ids = (
                            failure_df.filter((pl.col(col) == "Y") & (pl.col("level") == 3))
                            .select("patient_id_hash")["patient_id_hash"]
                            .to_list()
                        )
                        l3_patients.update(l3_ids)

                total = len(l1_patients) + len(l2_patients) + len(l3_patients)
                if total > 0:
                    rows.append(
                        {
                            "metric_type": "failure_mode",
                            "metric_name": cat_name,
                            "value": total,
                            "level_1": len(l1_patients),
                            "level_2": len(l2_patients),
                            "level_3": len(l3_patients),
                        }
                    )

        return pl.DataFrame(rows)

    def plot(self) -> list[tuple[plt.Figure, str]]:
        """
        Create Figure 1 composite and individual panels.

        Returns list of (figure, suffix) tuples for:
        - Composite figure
        - Individual panels (a, b, c)
        """
        df = self.load_df()
        gt_df = df.filter(pl.col("metric_type") == "ground_truth")
        fm_df = df.filter(pl.col("metric_type") == "failure_mode")

        def get_gt(name: str) -> int:
            return int(gt_df.filter(pl.col("metric_name") == name)["value"][0])

        # Extract values for panels (a) and (b)
        true_negative = get_gt("negative_no_issue")
        false_negative = get_gt("negative_any_issue")
        true_positive = get_gt("all_correct_correct_intervention")
        false_positive_level_2 = get_gt("positive_some_correct")
        false_positive_level_3 = get_gt("all_correct_partial_intervention") + get_gt(
            "all_correct_incorrect_intervention"
        )

        tp = get_gt("positive_any_issue")
        fn = get_gt("positive_no_issue")
        tn = get_gt("negative_no_issue")
        fp = get_gt("negative_any_issue")

        # Extract failure mode data for panel (c)
        categories = fm_df["metric_name"].to_list()
        level_1 = [int(v) if v is not None else 0 for v in fm_df["level_1"].to_list()]
        level_2 = [int(v) if v is not None else 0 for v in fm_df["level_2"].to_list()]
        level_3 = [int(v) if v is not None else 0 for v in fm_df["level_3"].to_list()]
        totals = [int(v) for v in fm_df["value"].to_list()]

        figures = []

        # Generate composite figure
        fig_composite = self._generate_composite(
            true_negative,
            false_negative,
            true_positive,
            false_positive_level_2,
            false_positive_level_3,
            tp,
            fp,
            tn,
            fn,
            categories,
            level_1,
            level_2,
            level_3,
            totals,
        )
        figures.append((fig_composite, ""))

        # Generate individual panels
        fig_1a = self._generate_figure_1a(
            true_negative,
            false_negative,
            true_positive,
            false_positive_level_2,
            false_positive_level_3,
        )
        figures.append((fig_1a, "_panel_a"))

        fig_1b = self._generate_figure_1b(tp, fp, tn, fn)
        figures.append((fig_1b, "_panel_b"))

        fig_1c = self._generate_figure_1c(categories, level_1, level_2, level_3, totals)
        figures.append((fig_1c, "_panel_c"))

        return figures

    def _set_publication_defaults(self):
        """Apply MedGuard style settings matching the notebook."""
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

    def _generate_figure_1a(
        self,
        true_negative: int,
        false_negative: int,
        true_positive: int,
        false_positive_level_2: int,
        false_positive_level_3: int,
        ax=None,
    ) -> plt.Figure:
        """Create stacked bar chart showing hierarchical evaluation stages (matching notebook)."""
        self._set_publication_defaults()

        categories = [
            "Level 1\n(Binary Classification)",
            "Level 2\n(Issue Correct)",
            "Level 3\n(Intervention Correct)",
        ]

        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 4.5))
        else:
            fig = ax.figure

        spacing_factor = 0.6
        x = np.arange(len(categories)) * spacing_factor
        width = 0.5

        # Bar 1: false_negative, true_negative, all positives combined
        ax.bar(
            [x[0]],
            [false_negative],
            width,
            bottom=0,
            color=COLORS["false_negative"],
            edgecolor=COLORS["neutral_dark"],
            linewidth=0.8,
        )
        ax.bar(
            [x[0]],
            [true_negative],
            width,
            bottom=[false_negative],
            color=COLORS["true_negative"],
            edgecolor=COLORS["neutral_dark"],
            linewidth=0.8,
        )
        ax.bar(
            [x[0]],
            [true_positive + false_positive_level_2 + false_positive_level_3],
            width,
            bottom=[false_negative + true_negative],
            color=COLORS["correct"],
            edgecolor=COLORS["neutral_dark"],
            linewidth=0.8,
        )

        # Bar 2: false_negative, true_negative, level_2, correct+level_3
        ax.bar(
            [x[1]],
            [false_negative],
            width,
            bottom=0,
            color=COLORS["false_negative"],
            edgecolor=COLORS["neutral_dark"],
            linewidth=0.8,
        )
        ax.bar(
            [x[1]],
            [true_negative],
            width,
            bottom=[false_negative],
            color=COLORS["true_negative"],
            edgecolor=COLORS["neutral_dark"],
            linewidth=0.8,
        )
        ax.bar(
            [x[1]],
            [false_positive_level_2],
            width,
            bottom=[false_negative + true_negative],
            color=COLORS["failure_level_2"],
            edgecolor=COLORS["neutral_dark"],
            linewidth=0.8,
        )
        ax.bar(
            [x[1]],
            [true_positive + false_positive_level_3],
            width,
            bottom=[false_negative + true_negative + false_positive_level_2],
            color=COLORS["correct"],
            edgecolor=COLORS["neutral_dark"],
            linewidth=0.8,
        )

        # Bar 3: all segments visible
        ax.bar(
            [x[2]],
            [false_negative],
            width,
            color=COLORS["false_negative"],
            edgecolor=COLORS["neutral_dark"],
            linewidth=0.8,
        )
        ax.bar(
            [x[2]],
            [true_negative],
            width,
            bottom=[false_negative],
            color=COLORS["true_negative"],
            edgecolor=COLORS["neutral_dark"],
            linewidth=0.8,
        )
        ax.bar(
            [x[2]],
            [false_positive_level_2],
            width,
            bottom=[false_negative + true_negative],
            color=COLORS["failure_level_2"],
            edgecolor=COLORS["neutral_dark"],
            linewidth=0.8,
        )
        ax.bar(
            [x[2]],
            [false_positive_level_3],
            width,
            bottom=[false_negative + true_negative + false_positive_level_2],
            color=COLORS["failure_level_3"],
            edgecolor=COLORS["neutral_dark"],
            linewidth=0.8,
        )
        ax.bar(
            [x[2]],
            [true_positive],
            width,
            bottom=[
                false_negative + true_negative + false_positive_level_2 + false_positive_level_3
            ],
            color=COLORS["correct"],
            edgecolor=COLORS["neutral_dark"],
            linewidth=0.8,
        )

        # Create legend
        legend_elements = [
            Patch(
                facecolor=COLORS["correct"],
                edgecolor=COLORS["neutral_dark"],
                label="Correct Intervention",
            ),
            Patch(
                facecolor=COLORS["failure_level_3"],
                edgecolor=COLORS["neutral_dark"],
                label="Failure Level 3",
            ),
            Patch(
                facecolor=COLORS["failure_level_2"],
                edgecolor=COLORS["neutral_dark"],
                label="Failure Level 2",
            ),
            Patch(
                facecolor=COLORS["true_negative"],
                edgecolor=COLORS["neutral_dark"],
                label="True Negative",
            ),
            Patch(
                facecolor=COLORS["false_negative"],
                edgecolor=COLORS["neutral_dark"],
                label="False Positive",
            ),
        ]

        ax.set_ylabel("Number of Patients", fontsize=9, fontweight="medium")
        ax.set_xlabel("Stage", fontsize=9, fontweight="medium")
        ax.set_xticks(x)
        ax.set_xticklabels(categories, ha="center")
        ax.legend(handles=legend_elements, loc="upper right", frameon=False, fontsize=7)

        # Add count labels on Stage 3
        stage3_x = x[2]
        label_fontsize = 8
        segments = [
            (0, false_negative, str(false_negative)),
            (false_negative, true_negative, str(true_negative)),
            (false_negative + true_negative, false_positive_level_2, str(false_positive_level_2)),
            (
                false_negative + true_negative + false_positive_level_2,
                false_positive_level_3,
                str(false_positive_level_3),
            ),
            (
                false_negative + true_negative + false_positive_level_2 + false_positive_level_3,
                true_positive,
                str(true_positive),
            ),
        ]
        for bottom, height, label in segments:
            center_y = bottom + height / 2
            ax.text(
                stage3_x,
                center_y,
                label,
                ha="center",
                va="center",
                fontsize=label_fontsize,
                fontweight="semibold",
                color=COLORS["neutral_dark"],
            )

        # Bracket annotations for ground truth groups
        negative_bottom = 0
        negative_top = false_negative + true_negative
        positive_bottom = negative_top
        positive_top = (
            negative_top + false_positive_level_2 + false_positive_level_3 + true_positive
        )

        negative_center_y = (negative_bottom + negative_top) / 2
        positive_center_y = (positive_bottom + positive_top) / 2

        annotation_x = stage3_x + 0.28
        annotation_x_text = stage3_x + 0.35

        # Negative ground truth bracket
        ax.annotate(
            "",
            xy=(annotation_x, negative_bottom),
            xytext=(annotation_x, negative_top),
            arrowprops=dict(arrowstyle="-", lw=0.8, color=COLORS["neutral_dark"]),
            annotation_clip=False,
        )
        ax.annotate(
            "",
            xy=(annotation_x, negative_center_y),
            xytext=(annotation_x_text, negative_center_y),
            arrowprops=dict(arrowstyle="-", lw=0.8, color=COLORS["neutral_dark"]),
            annotation_clip=False,
        )
        ax.text(
            annotation_x_text,
            negative_center_y,
            f"Ground Truth\nNegative (n={negative_top})",
            ha="left",
            va="center",
            fontsize=7,
        )

        # Positive ground truth bracket
        ax.annotate(
            "",
            xy=(annotation_x, positive_bottom),
            xytext=(annotation_x, positive_top),
            arrowprops=dict(arrowstyle="-", lw=0.8, color=COLORS["neutral_dark"]),
            annotation_clip=False,
        )
        ax.annotate(
            "",
            xy=(annotation_x, positive_center_y),
            xytext=(annotation_x_text, positive_center_y),
            arrowprops=dict(arrowstyle="-", lw=0.8, color=COLORS["neutral_dark"]),
            annotation_clip=False,
        )
        ax.text(
            annotation_x_text,
            positive_center_y,
            f"Ground Truth\nPositive (n={positive_top - negative_top})",
            ha="left",
            va="center",
            fontsize=7,
        )

        # Set x-axis limits (tighter fit)
        ax.set_xlim(-0.35, 2.2)

        # Add grid
        ax.yaxis.grid(True, linestyle="--", alpha=0.3, linewidth=0.5, zorder=0)
        ax.set_axisbelow(True)

        if ax is None:
            plt.tight_layout()

        return fig

    def _generate_figure_1b(self, tp: int, fp: int, tn: int, fn: int, ax=None) -> plt.Figure:
        """Create confusion matrix visualization."""
        self._set_publication_defaults()

        confusion_matrix = np.array([[tn, fp], [fn, tp]])
        labels = np.array(
            [["True Negative", "False Positive"], ["False Negative", "True Positive"]]
        )
        colors = np.array(
            [
                [COLORS["true_negative"], COLORS["false_negative"]],
                [COLORS["failure_level_2"], COLORS["correct"]],
            ]
        )

        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 4.5))
        else:
            fig = ax.figure

        for i in range(2):
            for j in range(2):
                rect = plt.Rectangle(
                    (j - 0.5, i - 0.5),
                    1,
                    1,
                    facecolor=colors[i, j],
                    edgecolor=COLORS["neutral_dark"],
                    linewidth=0.8,
                )
                ax.add_patch(rect)

        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["System: No Issue", "System: Issue"], fontsize=9, fontweight="medium")
        ax.set_yticklabels(
            ["Clinician: No Issue", "Clinician: Issue"], fontsize=9, fontweight="medium"
        )

        total = tp + fp + tn + fn
        for i in range(2):
            for j in range(2):
                value = confusion_matrix[i, j]
                label = labels[i, j]
                ax.text(
                    j,
                    i,
                    f"{label}\n{value}\n({value / total * 100:.1f}%)",
                    ha="center",
                    va="center",
                    color=COLORS["neutral_dark"],
                    fontsize=9,
                    fontweight="semibold",
                )

        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(-0.5, 1.5)
        ax.invert_yaxis()

        if ax is None:
            plt.tight_layout()

        return fig

    def _generate_figure_1c(
        self,
        categories: list[str],
        level_1: list[int],
        level_2: list[int],
        level_3: list[int],
        totals: list[int],
        ax=None,
    ) -> plt.Figure:
        """Create horizontal stacked bar chart of failure mode categories (matching notebook)."""
        self._set_publication_defaults()

        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 4.5))
        else:
            fig = ax.figure

        # Sort by total (largest first)
        sorted_indices = sorted(range(len(totals)), key=lambda i: totals[i], reverse=True)
        sorted_categories = [categories[i] for i in sorted_indices]
        sorted_level_1 = [level_1[i] for i in sorted_indices]
        sorted_level_2 = [level_2[i] for i in sorted_indices]
        sorted_level_3 = [level_3[i] for i in sorted_indices]
        sorted_totals = [totals[i] for i in sorted_indices]

        # Create horizontal stacked bar chart
        spacing_factor = 0.7
        y_pos = [i * spacing_factor for i in range(len(sorted_categories))]
        bar_height = 0.5

        # Calculate left offset for level 3 (stacking from left to right)
        level_1_2_sum = [l1 + l2 for l1, l2 in zip(sorted_level_1, sorted_level_2)]

        # Plot stacked bars (order: level 3 on right, level 2 middle, level 1 on left)
        ax.barh(
            y_pos,
            sorted_level_3,
            left=level_1_2_sum,
            height=bar_height,
            color=COLORS["failure_level_3"],
            label="Failure Level 3",
            edgecolor=COLORS["neutral_dark"],
            linewidth=0.8,
        )
        ax.barh(
            y_pos,
            sorted_level_2,
            left=sorted_level_1,
            height=bar_height,
            color=COLORS["failure_level_2"],
            label="Failure Level 2",
            edgecolor=COLORS["neutral_dark"],
            linewidth=0.8,
        )
        ax.barh(
            y_pos,
            sorted_level_1,
            height=bar_height,
            color=COLORS["false_negative"],
            label="False Positive",
            edgecolor=COLORS["neutral_dark"],
            linewidth=0.8,
        )

        # Wrap long category names
        wrapped_categories = [
            textwrap.fill(cat, width=35, break_long_words=False, break_on_hyphens=False)
            for cat in sorted_categories
        ]

        # Customize axes
        ax.set_yticks(y_pos)
        ax.set_yticklabels(wrapped_categories, ha="right")
        ax.set_ylabel("Failure Mode Category", fontsize=9, fontweight="medium")
        ax.set_xlabel("Count", fontsize=9, fontweight="medium")
        ax.invert_yaxis()

        # Legend (frameon=False per style guide)
        ax.legend(loc="lower right", frameon=False, fontsize=7)

        # Grid
        ax.grid(axis="x", alpha=0.3, linestyle="--", linewidth=0.5, zorder=0)
        ax.set_axisbelow(True)

        # Set x-axis limit
        max_total = max(sorted_totals) if sorted_totals else 70
        ax.set_xlim(0, max_total + 8)

        # Adjust left margin for multi-line labels
        if ax is None:
            plt.subplots_adjust(left=0.28)
        else:
            fig.subplots_adjust(left=0.28)

        # Add value labels at the right end of each bar
        for i, total in enumerate(sorted_totals):
            ax.text(
                total + 1,
                y_pos[i],
                f"n={total}",
                ha="left",
                va="center",
                fontsize=7,
                fontweight="semibold",
                color=COLORS["neutral_dark"],
            )

        if ax is None:
            plt.tight_layout()

        return fig

    def _generate_composite(
        self,
        true_negative: int,
        false_negative: int,
        true_positive: int,
        false_positive_level_2: int,
        false_positive_level_3: int,
        tp: int,
        fp: int,
        tn: int,
        fn: int,
        categories: list[str],
        level_1: list[int],
        level_2: list[int],
        level_3: list[int],
        totals: list[int],
    ) -> plt.Figure:
        """Create composite figure with all three panels."""
        self._set_publication_defaults()

        fig = plt.figure(figsize=(24, 15))
        gs = GridSpec(
            2, 2, figure=fig, hspace=0.25, wspace=0.3, height_ratios=[1, 1], width_ratios=[1, 1]
        )

        ax1a = fig.add_subplot(gs[0, 0])
        self._generate_figure_1a(
            true_negative,
            false_negative,
            true_positive,
            false_positive_level_2,
            false_positive_level_3,
            ax=ax1a,
        )

        ax1b = fig.add_subplot(gs[0, 1])
        self._generate_figure_1b(tp, fp, tn, fn, ax=ax1b)

        ax1c = fig.add_subplot(gs[1, :])
        self._generate_figure_1c(categories, level_1, level_2, level_3, totals, ax=ax1c)

        plt.tight_layout()
        return fig

    def save_figure_to_pdf(self, fig: plt.Figure, suffix: str = "") -> Path:
        """Save matplotlib figure to PDF file."""
        filename = f"{self.name}{suffix}.pdf" if suffix else f"{self.name}.pdf"
        output_path = self.plots_dir / filename
        fig.savefig(output_path, format="pdf", bbox_inches="tight")
        plt.close(fig)
        return output_path

    def run_figure_pdf(self) -> list[Path]:
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
    from medguard.evaluation.evaluation import Evaluation, merge_evaluations
    from medguard.utils.parsing import load_pydantic_from_json

    print("Loading evaluations...")
    evaluation_200 = load_pydantic_from_json(
        Evaluation, "outputs/20251018/test-set/evaluation.json"
    )
    evaluation_100 = load_pydantic_from_json(
        Evaluation, "outputs/20251027/no-filters/evaluation.json"
    )

    evaluation = merge_evaluations([evaluation_100, evaluation_200])
    evaluation = evaluation.clean()

    print(f"Loaded {len(evaluation.patient_ids())} patients")

    analysis = Figure1CompositeAnalysis(evaluation)
    df, path = analysis.run()
    print(f"\nSaved data to: {path}")

    # Save as PNG
    print("\nGenerating PNG plots...")
    fig_paths = analysis.run_figure()
    for p in fig_paths:
        print(f"  Saved: {p}")

    # Save as PDF
    print("\nGenerating PDF plots...")
    pdf_paths = analysis.run_figure_pdf()
    for p in pdf_paths:
        print(f"  Saved: {p}")
