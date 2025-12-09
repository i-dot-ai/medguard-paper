"""
Vignette Failure Mode Analysis

Analyzes failure modes from manually annotated patient vignettes.
This is a standalone analysis that doesn't inherit from the base classes,
as it works directly with the annotated vignettes CSV rather than evaluation objects.
"""

import polars as pl
import matplotlib.pyplot as plt
from pathlib import Path
from medguard.analysis.utils import setup_publication_plot


class VignetteFailureModeAnalysis:
    """Analyze failure modes from annotated vignettes."""

    def __init__(self, csv_path: str = "outputs/failure_vignettes/vignettes_index_annotated.csv"):
        """Initialize with path to annotated vignettes CSV."""
        self.csv_path = csv_path
        self.df = None
        self.output_dir = Path("outputs/eval_analyses")
        self.plot_dir = self.output_dir / "plots"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.plot_dir.mkdir(parents=True, exist_ok=True)

    def load_data(self):
        """Load and preprocess the vignettes CSV."""
        self.df = pl.read_csv(self.csv_path, encoding="utf8-lossy")
        return self

    def get_category_counts(self):
        """
        Get counts for each failure category, rolled up from subcategories
        and broken down by level. Counts unique patients (no double-counting
        if patient has both main category and subcategory marked).

        Returns:
            pl.DataFrame with columns: category, level_1, level_2, level_3, total
        """
        # Define main categories and their subcategory columns
        # Keys are display names used in paper, values are CSV column names
        categories = {
            "Duplicate Prescription Errors": ["duplicate prescription errors"],
            "Unsafe medication transitions": ["too-aggressive", "too-aggressive/gradual-taper"],
            "Pharmacological knowledge gaps": ["understanding-drug-context"],
            "Premature action without information": [
                "further-information",
                "further-information/iron-studies",
            ],
            "Not considering patient specific context": [
                "nuance",
                "nuance/end-of-life",
                "nuance/already-tolerated",
                "nuance/overly-cautious",
            ],
            "Hallucination": ["hallucination", "hallucination/drug-component"],
            "Healthcare system context": ["clinician-context"],
            "Guideline misapplication": ["incorrect-understanding-guidelines"],
            "Missed clinical issues": [
                "missed-issue",
                "missed-issue/missed-deprescription-opportunity",
                "missed-issue/missed-issue",
            ],
        }

        results = []
        for cat_name, cols in categories.items():
            # Count unique patients by level (avoid double-counting subcategories)
            # Create a condition that checks if ANY of the category columns is 'Y'
            l1_patients = set()
            l2_patients = set()
            l3_patients = set()

            for col in cols:
                if col in self.df.columns:
                    # Get patient IDs for each level
                    l1_ids = (
                        self.df.filter((pl.col(col) == "Y") & (pl.col("level") == 1))
                        .select("patient_id_hash")["patient_id_hash"]
                        .to_list()
                    )
                    l1_patients.update(l1_ids)

                    l2_ids = (
                        self.df.filter((pl.col(col) == "Y") & (pl.col("level") == 2))
                        .select("patient_id_hash")["patient_id_hash"]
                        .to_list()
                    )
                    l2_patients.update(l2_ids)

                    l3_ids = (
                        self.df.filter((pl.col(col) == "Y") & (pl.col("level") == 3))
                        .select("patient_id_hash")["patient_id_hash"]
                        .to_list()
                    )
                    l3_patients.update(l3_ids)

            l1_count = len(l1_patients)
            l2_count = len(l2_patients)
            l3_count = len(l3_patients)
            total = l1_count + l2_count + l3_count

            if total > 0:
                results.append(
                    {
                        "category": cat_name,
                        "level_1": l1_count,
                        "level_2": l2_count,
                        "level_3": l3_count,
                        "total": total,
                    }
                )

        return pl.DataFrame(results)

    def plot_failure_modes(self):
        """
        Create stacked vertical bar plot showing failure mode counts by level.

        Returns:
            matplotlib.figure.Figure
        """
        # Get category counts
        counts_df = self.get_category_counts()

        # Sort by total count descending
        counts_df = counts_df.sort("total", descending=True)

        # Convert to lists for plotting
        categories = counts_df["category"].to_list()
        level_1 = counts_df["level_1"].to_list()
        level_2 = counts_df["level_2"].to_list()
        level_3 = counts_df["level_3"].to_list()

        # Create figure
        fig, ax = setup_publication_plot(
            figsize=(14, 8),
            title="Failure Mode Distribution by Hierarchical Level",
            xlabel="Failure Mode Category",
            ylabel="Count",
        )

        # Create vertical stacked bar chart
        x_pos = range(len(categories))

        # Define colors for each level (using colorblind-friendly categorical palette)
        colors = {
            "Level 1": "#1f77b4",  # Blue
            "Level 2": "#9467bd",  # Purple
            "Level 3": "#17becf",  # Teal/Cyan
        }

        # Plot stacked bars
        ax.bar(
            x_pos,
            level_1,
            color=colors["Level 1"],
            label="Level 1: Issue Identification",
            edgecolor="white",
            linewidth=0.5,
        )
        ax.bar(
            x_pos,
            level_2,
            bottom=level_1,
            color=colors["Level 2"],
            label="Level 2: Issue Correctness",
            edgecolor="white",
            linewidth=0.5,
        )

        # Calculate bottom offset for level 3
        level_1_2_sum = [l1 + l2 for l1, l2 in zip(level_1, level_2)]
        ax.bar(
            x_pos,
            level_3,
            bottom=level_1_2_sum,
            color=colors["Level 3"],
            label="Level 3: Intervention Appropriateness",
            edgecolor="white",
            linewidth=0.5,
        )

        # Customize
        ax.set_xticks(x_pos)
        ax.set_xticklabels(categories, rotation=45, ha="right")
        ax.legend(loc="upper right", frameon=True, fancybox=False, edgecolor="black")
        ax.grid(axis="y", alpha=0.3, linestyle="--")

        # Add value labels at the top of each bar
        totals = counts_df["total"].to_list()
        for i, total in enumerate(totals):
            ax.text(
                i, total + 1, f"n={total}", ha="center", va="bottom", fontsize=9, fontweight="bold"
            )

        plt.tight_layout()
        return fig

    def save_summary_stats(self):
        """Save summary statistics to CSV and text file."""
        counts_df = self.get_category_counts()

        # Save CSV
        csv_path = self.output_dir / "vignette_failure_mode_counts.csv"
        counts_df.write_csv(str(csv_path))

        # Save formatted text summary
        txt_path = self.output_dir / "vignette_failure_mode_summary.txt"
        with open(txt_path, "w") as f:
            f.write("VIGNETTE FAILURE MODE ANALYSIS SUMMARY\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"Total patients analyzed: {self.df.height}\n")
            f.write(f"  Level 1 (False Positive): {self.df.filter(pl.col('level') == 1).height}\n")
            f.write(
                f"  Level 2 (Issues Partially Correct): {self.df.filter(pl.col('level') == 2).height}\n"
            )
            f.write(
                f"  Level 3 (Intervention Incorrect/Partial): {self.df.filter(pl.col('level') == 3).height}\n\n"
            )

            f.write("FAILURE MODE COUNTS BY CATEGORY\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'Category':<45} {'L1':>6} {'L2':>6} {'L3':>6} {'Total':>6}\n")
            f.write("-" * 70 + "\n")

            # Sort by total descending
            sorted_df = counts_df.sort("total", descending=True)
            for row in sorted_df.iter_rows(named=True):
                f.write(
                    f"{row['category']:<45} {row['level_1']:>6} {row['level_2']:>6} "
                    f"{row['level_3']:>6} {row['total']:>6}\n"
                )

            f.write("-" * 70 + "\n")
            totals = sorted_df.select(
                [
                    pl.col("level_1").sum(),
                    pl.col("level_2").sum(),
                    pl.col("level_3").sum(),
                    pl.col("total").sum(),
                ]
            ).row(0)
            f.write(f"{'TOTAL':<45} {totals[0]:>6} {totals[1]:>6} {totals[2]:>6} {totals[3]:>6}\n")

        print(f"Summary statistics saved to {txt_path}")
        return txt_path

    def run(self):
        """Execute full analysis pipeline."""
        print("Loading vignettes data...")
        self.load_data()

        print("Generating summary statistics...")
        self.save_summary_stats()

        print("Creating failure mode plot...")
        fig = self.plot_failure_modes()

        # Save plot
        plot_path = self.plot_dir / "vignette_failure_mode_distribution.png"
        fig.savefig(plot_path, dpi=300, bbox_inches="tight")
        print(f"Plot saved to {plot_path}")

        plt.close(fig)
        print("Analysis complete!")


if __name__ == "__main__":
    analysis = VignetteFailureModeAnalysis()
    analysis.run()
