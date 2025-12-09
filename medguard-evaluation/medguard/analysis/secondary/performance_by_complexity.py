"""
Performance by Patient Complexity Analysis

Generates performance metrics stratified by patient complexity:
- Medication count (polypharmacy)
- Age
- QOF register count

Section: 3.3.3
"""

import polars as pl
import matplotlib.pyplot as plt
from statistics import mean, stdev
from math import sqrt

from medguard.analysis.base import EvaluationAnalysisBase
from medguard.analysis.filters import (
    no_data_error,
    get_medication_count,
    get_age,
    get_qof_count,
    get_sex,
)


class PerformanceByComplexityAnalysis(EvaluationAnalysisBase):
    """
    Calculate mean clinician scores stratified by patient complexity measures.

    For each complexity bin:
    - N patients
    - Mean clinician score (0-100 scale)

    Includes all patients with no data errors (no restriction on agreement with rules).
    """

    def __init__(self, evaluation, name: str = "performance_by_complexity"):
        super().__init__(evaluation, name=name)

    def execute(self) -> pl.DataFrame:
        """
        Execute analysis and return DataFrame.

        Returns DataFrame with columns:
        - complexity_type: Type of complexity measure (medications, age, qof, sex)
        - bin_label: Human-readable bin label
        - bin_min: Minimum value for bin (inclusive, None for categorical)
        - bin_max: Maximum value for bin (exclusive, None for last bin or categorical)
        - n_patients: Number of patients in this bin
        - mean_clinician_score: Mean agreement score from clinician evaluations
        - sem_clinician_score: SEM of clinician score
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

        # === MEDICATION COUNT BINS ===
        medication_bins = [
            ("0-4", 0, 5),
            ("5-9", 5, 10),
            ("10-14", 10, 15),
            ("15+", 15, None),
        ]

        for bin_label, bin_min, bin_max in medication_bins:
            # Filter patients by medication count
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

            # Calculate metrics for this bin
            metrics = self._calculate_metrics(patient_ids)
            rows.append(
                {
                    "complexity_type": "medications",
                    "bin_label": bin_label,
                    "bin_min": bin_min,
                    "bin_max": bin_max,
                    **metrics,
                }
            )

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

            metrics = self._calculate_metrics(patient_ids)
            rows.append(
                {
                    "complexity_type": "age",
                    "bin_label": bin_label,
                    "bin_min": bin_min,
                    "bin_max": bin_max,
                    **metrics,
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

            metrics = self._calculate_metrics(patient_ids)
            rows.append(
                {
                    "complexity_type": "qof",
                    "bin_label": bin_label,
                    "bin_min": bin_min,
                    "bin_max": bin_max,
                    **metrics,
                }
            )

        # === GENDER/SEX BINS ===
        gender_bins = [
            ("Male", ["M"]),
            ("Female", ["F"]),
            ("Other/Unknown", ["O", "U"]),
        ]

        for bin_label, sex_values in gender_bins:
            patient_ids = set()
            for pid, record in all_records.items():
                sex = get_sex(record)
                if sex in sex_values:
                    patient_ids.add(pid)

            if len(patient_ids) == 0:
                continue

            metrics = self._calculate_metrics(patient_ids)
            rows.append(
                {
                    "complexity_type": "sex",
                    "bin_label": bin_label,
                    "bin_min": None,
                    "bin_max": None,
                    **metrics,
                }
            )

        df = pl.DataFrame(rows)
        return df

    def _calculate_metrics(self, patient_ids: set[int]) -> dict:
        """
        Calculate clinician evaluation metrics for a set of patient IDs.

        Args:
            patient_ids: Set of patient IDs to include

        Returns:
            Dictionary with metrics including mean and SEM
        """
        # Create filtered evaluation
        filtered_eval = self.evaluation.filter_by_patient_ids(patient_ids)

        mean_clinician_score = None
        sem_clinician_score = None

        if filtered_eval.clinician_evaluations:
            # Mean clinician score
            scores = [e.score for e in filtered_eval.clinician_evaluations]
            if scores:
                mean_clinician_score = mean(scores)
                if len(scores) > 1:
                    sem_clinician_score = stdev(scores) / sqrt(len(scores))
                else:
                    sem_clinician_score = 0.0

        return {
            "n_patients": len(patient_ids),
            "mean_clinician_score": mean_clinician_score,
            "sem_clinician_score": sem_clinician_score,
        }

    def plot(self) -> list[tuple[plt.Figure, str]]:
        """
        Create bar charts showing mean clinician score for each complexity measure.

        Returns:
            List of (figure, suffix) tuples for each complexity type
        """
        df = self.load_df()

        figures = []

        # Create separate plot for each complexity type
        for complexity_type in ["medications", "age", "qof", "sex"]:
            subset = df.filter(pl.col("complexity_type") == complexity_type)

            if len(subset) == 0:
                continue

            fig = self._create_complexity_plot(subset, complexity_type)
            figures.append((fig, f"_{complexity_type}"))

        return figures

    def _create_complexity_plot(self, df: pl.DataFrame, complexity_type: str) -> plt.Figure:
        """
        Create bar chart for a single complexity measure.

        Args:
            df: Subset DataFrame for this complexity type
            complexity_type: Type of complexity (medications, age, qof)

        Returns:
            Matplotlib figure
        """
        # Set publication style
        plt.style.use("seaborn-v0_8-paper")
        plt.rcParams["font.size"] = 11
        plt.rcParams["axes.labelsize"] = 12
        plt.rcParams["axes.titlesize"] = 13

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))

        # Prepare data
        bin_labels = df["bin_label"].to_list()
        n_patients = df["n_patients"].to_list()
        x = range(len(bin_labels))

        # Extract metrics (0-1 scale)
        mean_scores = [s if s is not None else 0 for s in df["mean_clinician_score"].to_list()]
        sem_scores = [s if s is not None else 0 for s in df["sem_clinician_score"].to_list()]

        # Create bars with error bars
        bars = ax.bar(
            x,
            mean_scores,
            color="#3498db",
            alpha=0.8,
            edgecolor="black",
            linewidth=0.5,
            yerr=sem_scores,
            capsize=5,
            error_kw={"linewidth": 1, "elinewidth": 1, "capthick": 1},
        )

        # Add sample size labels
        for i, n in enumerate(n_patients):
            ax.text(
                i,
                1.05,
                f"(n={n})",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )

        # Configure labels based on complexity type
        xlabel_map = {
            "medications": "Number of Active Medications",
            "age": "Patient Age (years)",
            "qof": "Number of QOF Registers",
            "sex": "Patient Sex",
        }
        title_map = {
            "medications": "Mean Clinician Score by Medication Count",
            "age": "Mean Clinician Score by Patient Age",
            "qof": "Mean Clinician Score by QOF Register Count",
            "sex": "Mean Clinician Score by Sex",
        }

        # Labels and styling
        ax.set_xlabel(xlabel_map[complexity_type], fontweight="bold")
        ax.set_ylabel("Mean Clinician Score", fontweight="bold")
        ax.set_title(title_map[complexity_type], fontweight="bold", pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(bin_labels)
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.set_ylim(0, 1.15)

        plt.tight_layout()
        return fig
