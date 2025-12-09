"""
Failure Mode Correlation Analysis

Creates a confusion/co-occurrence matrix showing which failure modes
appear together in the same patients.
"""

import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


class FailureModeCorrelationAnalysis:
    """Analyze co-occurrence patterns of failure modes."""

    def __init__(
        self,
        csv_path: str = "outputs/failure_vignettes/vignettes_index_annotated.csv",
        name: str = "failure_mode_confusion_matrix",
    ):
        """Initialize with path to annotated vignettes CSV."""
        self.csv_path = csv_path
        self.df = None
        self.name = name
        self.output_dir = Path("outputs/eval_analyses")
        self.plot_dir = self.output_dir / "plots"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.plot_dir.mkdir(parents=True, exist_ok=True)

    def load_data(self):
        """Load and preprocess the vignettes CSV."""
        self.df = pl.read_csv(self.csv_path, encoding="utf8-lossy")
        return self

    def execute(self) -> pl.DataFrame:
        """
        Build co-occurrence matrix showing how many patients have each pair of failure modes.

        Returns:
            pl.DataFrame with columns for each failure mode pair
        """
        self.load_data()

        # Define categories matching the vignette_failure_modes.py
        categories = {
            "Duplicate Prescription Errors": ["duplicate prescription errors"],
            "Unsafe medication transitions": ["too-aggressive", "too-aggressive/gradual-taper"],
            "Pharmacological knowledge gaps": ["understanding-drug-context"],
            "Premature action without information": [
                "further-information",
                "further-information/iron-studies",
            ],
            "Not considering patient context": [
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

        category_names = list(categories.keys())
        n_categories = len(category_names)

        # Build matrix
        matrix = np.zeros((n_categories, n_categories), dtype=int)

        # For each patient, determine which categories they have
        for patient_row in self.df.iter_rows(named=True):
            patient_cats = []

            # Check which categories this patient has
            for cat_idx, (cat_name, col_names) in enumerate(categories.items()):
                has_category = False
                for col in col_names:
                    if col in patient_row and patient_row[col] == "Y":
                        has_category = True
                        break
                if has_category:
                    patient_cats.append(cat_idx)

            # Increment co-occurrence counts for all pairs this patient has
            for i in patient_cats:
                for j in patient_cats:
                    matrix[i, j] += 1

        # Convert to DataFrame for output
        # Rows and columns are the category names
        result = pl.DataFrame(matrix, schema=category_names)
        result = result.with_columns(pl.Series("Category", category_names))

        # Reorder columns to have Category first
        result = result.select(["Category"] + category_names)

        return result

    def save_df(self, df: pl.DataFrame):
        """Save DataFrame to CSV."""
        csv_path = self.output_dir / f"{self.name}.csv"
        df.write_csv(str(csv_path))

    def load_df(self) -> pl.DataFrame:
        """Load previously saved DataFrame."""
        csv_path = self.output_dir / f"{self.name}.csv"
        return pl.read_csv(str(csv_path))

    def plot(self) -> plt.Figure:
        """
        Create heatmap visualization of failure mode co-occurrence.

        Returns:
            matplotlib.figure.Figure
        """
        df = self.load_df()

        # Extract matrix values (exclude Category column)
        category_names = [col for col in df.columns if col != "Category"]
        matrix = df.select(category_names).to_numpy()

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 10))

        # Create heatmap
        im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")

        # Set ticks
        ax.set_xticks(np.arange(len(category_names)))
        ax.set_yticks(np.arange(len(category_names)))

        # Set tick labels
        ax.set_xticklabels(category_names, rotation=45, ha="right", fontsize=9)
        ax.set_yticklabels(category_names, fontsize=9)

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Number of patients", rotation=270, labelpad=20)

        # Add text annotations
        for i in range(len(category_names)):
            for j in range(len(category_names)):
                text = ax.text(
                    j,
                    i,
                    matrix[i, j],
                    ha="center",
                    va="center",
                    color="black" if matrix[i, j] < matrix.max() / 2 else "white",
                    fontsize=8,
                )

        # Labels and title
        ax.set_xlabel("Failure Mode", fontsize=11)
        ax.set_ylabel("Failure Mode", fontsize=11)
        ax.set_title(
            "Failure Mode Co-occurrence Matrix\n(Number of patients exhibiting both failure modes)",
            fontsize=12,
            pad=15,
        )

        plt.tight_layout()
        return fig


if __name__ == "__main__":
    analysis = FailureModeCorrelationAnalysis()

    print("Executing confusion matrix analysis...")
    df = analysis.execute()
    analysis.save_df(df)
    print(f"Saved to {analysis.output_dir / f'{analysis.name}.csv'}")

    print("Creating heatmap...")
    fig = analysis.plot()
    plot_path = analysis.plot_dir / f"{analysis.name}.png"
    fig.savefig(plot_path, dpi=300, bbox_inches="tight")
    print(f"Plot saved to {plot_path}")

    plt.close(fig)
    print("Analysis complete!")
