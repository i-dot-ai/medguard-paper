"""
Performance by Patient Complexity Analysis - Box Plot Version

Generates box-and-whisker plots showing distribution of clinician scores
stratified by patient complexity:
- Age
- QOF register count
- Medication count (polypharmacy)

Creates a single figure with three subplots side by side.

Section: 3.3.3
"""

import matplotlib.pyplot as plt
import polars as pl

from medguard.analysis.base import EvaluationAnalysisBase
from medguard.analysis.filters import get_age, get_medication_count, get_qof_count, no_data_error


class PerformanceByComplexityBoxPlotAnalysis(EvaluationAnalysisBase):
    """
    Calculate clinician score distributions stratified by patient complexity measures.

    For each complexity bin:
    - N patients
    - Individual clinician scores (stored as list for box plots)

    Includes all patients with no data errors (no restriction on agreement with rules).
    """

    def __init__(self, evaluation, name: str = "performance_by_complexity_boxplot"):
        super().__init__(evaluation, name=name)

    def execute(self) -> pl.DataFrame:
        """
        Execute analysis and return DataFrame.

        Returns DataFrame with columns:
        - complexity_type: Type of complexity measure (medications, age, qof)
        - bin_label: Human-readable bin label
        - bin_min: Minimum value for bin (inclusive)
        - bin_max: Maximum value for bin (exclusive, None for last bin)
        - n_patients: Number of patients in this bin
        - scores: Semicolon-separated string of individual clinician scores
        """
        # Get base patient IDs (all patients with no data errors)
        ids_by_clinician = self.evaluation.filter_by_clinician_evaluation(no_data_error())

        # Get analysed records for these patients (use _last for single record per patient)
        all_records = {
            pid: record
            for pid, record in self.evaluation.analysed_records_dict_last.items()
            if pid in ids_by_clinician
        }

        rows = []

        # === AGE BINS ===
        age_bins = [
            ("<65", 0, 65),
            ("65-74", 65, 75),
            ("75-84", 75, 85),
            ("85+", 85, None),
        ]

        for bin_label, bin_min, bin_max in age_bins:
            patient_ids = set()
            for pid, record in all_records.items():
                age = get_age(record)
                if age is None:
                    continue
                if bin_max is None:
                    if age >= bin_min:
                        patient_ids.add(pid)
                else:
                    if bin_min <= age < bin_max:
                        patient_ids.add(pid)

            if len(patient_ids) == 0:
                continue

            scores = self._get_clinician_scores(patient_ids)
            rows.append(
                {
                    "complexity_type": "age",
                    "bin_label": bin_label,
                    "bin_min": bin_min,
                    "bin_max": bin_max,
                    "n_patients": len(patient_ids),
                    "scores": ";".join(map(str, scores)),
                }
            )

        # === QOF REGISTER COUNT BINS ===
        qof_bins = [
            ("2-5", 2, 6),
            ("6-9", 6, 10),
            ("10-13", 10, 14),
            ("14-17", 14, 18),
            ("18+", 18, None),
        ]

        for bin_label, bin_min, bin_max in qof_bins:
            patient_ids = set()
            for pid, record in all_records.items():
                qof_count = get_qof_count(record)
                if bin_max is None:
                    if qof_count >= bin_min:
                        patient_ids.add(pid)
                else:
                    if bin_min <= qof_count < bin_max:
                        patient_ids.add(pid)

            if len(patient_ids) == 0:
                continue

            scores = self._get_clinician_scores(patient_ids)
            rows.append(
                {
                    "complexity_type": "qof",
                    "bin_label": bin_label,
                    "bin_min": bin_min,
                    "bin_max": bin_max,
                    "n_patients": len(patient_ids),
                    "scores": ";".join(map(str, scores)),
                }
            )

        # === MEDICATION COUNT BINS ===
        medication_bins = [
            ("0-4", 0, 5),
            ("5-9", 5, 10),
            ("10-14", 10, 15),
            ("15+", 15, None),
        ]

        for bin_label, bin_min, bin_max in medication_bins:
            patient_ids = set()
            for pid, record in all_records.items():
                med_count = get_medication_count(record)
                if bin_max is None:
                    if med_count >= bin_min:
                        patient_ids.add(pid)
                else:
                    if bin_min <= med_count < bin_max:
                        patient_ids.add(pid)

            if len(patient_ids) == 0:
                continue

            scores = self._get_clinician_scores(patient_ids)
            rows.append(
                {
                    "complexity_type": "medications",
                    "bin_label": bin_label,
                    "bin_min": bin_min,
                    "bin_max": bin_max,
                    "n_patients": len(patient_ids),
                    "scores": ";".join(map(str, scores)),
                }
            )

        df = pl.DataFrame(rows)
        return df

    def _get_clinician_scores(self, patient_ids: set[int]) -> list[float]:
        """
        Get individual clinician scores for a set of patient IDs.

        Args:
            patient_ids: Set of patient IDs to include

        Returns:
            List of individual clinician scores
        """
        scores = []
        for pid in patient_ids:
            if pid in self.evaluation.clinician_evaluations_dict:
                evaluation = self.evaluation.clinician_evaluations_dict[pid]
                scores.append(evaluation.score)
        return scores

    def plot(self) -> plt.Figure:
        """
        Create a single figure with three box-and-whisker subplots.

        Layout: [Age] [QOF] [Medications] (left to right)

        Returns:
            Single matplotlib figure with 3 subplots
        """
        df = self.load_df()

        # Set publication style
        plt.style.use("seaborn-v0_8-paper")
        plt.rcParams["font.size"] = 11
        plt.rcParams["axes.labelsize"] = 12
        plt.rcParams["axes.titlesize"] = 13

        # Create figure with 3 subplots side by side
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        # Plot each complexity type in order: age, qof, medications
        complexity_types = ["age", "qof", "medications"]
        titles = {
            "age": "Patient Age",
            "qof": "QOF Register Count",
            "medications": "Medication Count",
        }
        xlabels = {
            "age": "Age (years)",
            "qof": "Number of QOF Registers",
            "medications": "Number of Active Medications",
        }

        for idx, complexity_type in enumerate(complexity_types):
            ax = axes[idx]
            subset = df.filter(pl.col("complexity_type") == complexity_type)

            if len(subset) == 0:
                continue

            # Prepare data for box plot
            bin_labels = subset["bin_label"].to_list()
            n_patients = subset["n_patients"].to_list()

            # Parse scores from semicolon-separated strings
            all_scores = []
            for score_str in subset["scores"].to_list():
                scores = [float(s) for s in score_str.split(";")]
                all_scores.append(scores)

            # Create box plot
            ax.boxplot(
                all_scores,
                tick_labels=bin_labels,
                patch_artist=True,
                widths=0.6,
                showfliers=True,
                showmeans=True,
                boxprops=dict(facecolor="#3498db", alpha=0.7, linewidth=1.5),
                medianprops=dict(color="#e74c3c", linewidth=3, zorder=10),
                meanprops=dict(
                    marker="D",
                    markerfacecolor="#27ae60",
                    markeredgecolor="#27ae60",
                    markersize=8,
                    zorder=11,
                ),
                whiskerprops=dict(linewidth=1.5),
                capprops=dict(linewidth=1.5),
                flierprops=dict(
                    marker="o",
                    markerfacecolor="#2c3e50",
                    markeredgecolor="#2c3e50",
                    markersize=4,
                    alpha=0.4,
                    linestyle="none",
                ),
            )

            # Add sample size labels at bottom of figure with white background
            for i, n in enumerate(n_patients):
                ax.text(
                    i + 1,
                    0.02,
                    f"n={n}",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold",
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.9, pad=2),
                )

            # Styling
            ax.set_xlabel(xlabels[complexity_type], fontweight="bold")
            ax.set_title(titles[complexity_type], fontweight="bold", pad=15)
            ax.grid(axis="y", alpha=0.3, linestyle="--")
            ax.set_ylim(0, 1.0)

            # Only show y-axis label and ticks for first subplot
            if idx == 0:
                ax.set_ylabel("Clinician Score", fontweight="bold")
            else:
                ax.set_yticklabels([])

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

    print("\nRunning analysis...")
    analysis = PerformanceByComplexityBoxPlotAnalysis(evaluation)
    df, csv_path = analysis.run()
    print(f"Saved CSV to: {csv_path}")
    print(f"\nDataFrame preview:\n{df}")

    print("\nGenerating plots...")
    fig_path = analysis.run_figure()
    print(f"Saved figure to: {fig_path}")
    print("\n✓ Analysis complete!")
