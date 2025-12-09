"""
Performance by Filter - Clinician Scores

Shows average clinician evaluation scores (Stage2Data.score) broken down by PINCER filter type.
"""

import matplotlib.pyplot as plt
import polars as pl
from statistics import stdev
from math import sqrt

from medguard.analysis.base import EvaluationAnalysisBase
from medguard.analysis.filters import PINCER_FILTER_IDS, agrees_with_rules, no_data_error


class PerformanceByFilterClinicianAnalysis(EvaluationAnalysisBase):
    """Calculate mean clinician scores stratified by PINCER filter."""

    def __init__(self, evaluation, name: str = "performance_by_filter_clinician"):
        super().__init__(evaluation, name=name)

    def execute(self) -> pl.DataFrame:
        """
        Execute analysis and return DataFrame.

        Returns DataFrame with:
        - filter_id: PINCER filter ID
        - n_patients: Number of patients
        - mean_score: Mean clinician score (0-1 scale)
        - sem_score: SEM of clinician score
        """
        # Get patients with no data errors AND agrees with rules
        ids_no_errors = set(self.evaluation.filter_by_clinician_evaluation(no_data_error()))
        ids_agrees = set(self.evaluation.filter_by_clinician_evaluation(agrees_with_rules()))
        ids_filtered = ids_no_errors & ids_agrees

        rows = []

        for filter_id in PINCER_FILTER_IDS:
            # Get patients for this filter
            patient_ids = set()
            for pid, records in self.evaluation.analysed_records_dict.items():
                if pid not in ids_filtered:
                    continue
                for record in records:
                    active_filter = record.patient.get_active_filter()
                    if active_filter and active_filter.filter_id == filter_id:
                        patient_ids.add(pid)
                        break

            if len(patient_ids) == 0:
                continue

            # Calculate mean score and SEM
            scores = []
            for pid in patient_ids:
                if pid in self.evaluation.clinician_evaluations_dict:
                    scores.append(self.evaluation.clinician_evaluations_dict[pid].score)

            mean_score = sum(scores) / len(scores) if scores else None
            sem_score = None
            if scores:
                if len(scores) > 1:
                    sem_score = stdev(scores) / sqrt(len(scores))
                else:
                    sem_score = 0.0

            rows.append(
                {
                    "filter_id": filter_id,
                    "n_patients": len(patient_ids),
                    "mean_score": mean_score,
                    "sem_score": sem_score,
                }
            )

        return pl.DataFrame(rows)

    def plot(self) -> plt.Figure:
        """Create bar chart of mean clinician scores by filter."""
        df = self.load_df()

        plt.style.use("seaborn-v0_8-paper")
        plt.rcParams["font.size"] = 11

        fig, ax = plt.subplots(figsize=(10, 6))

        filter_ids = df["filter_id"].to_list()
        mean_scores = [s if s is not None else 0 for s in df["mean_score"].to_list()]
        sem_scores = [s if s is not None else 0 for s in df["sem_score"].to_list()]
        n_patients = df["n_patients"].to_list()
        x = range(len(filter_ids))

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

        ax.set_xlabel("PINCER Filter ID", fontweight="bold")
        ax.set_ylabel("Mean Clinician Score", fontweight="bold")
        ax.set_title("Mean Clinician Score by PINCER Filter", fontweight="bold", pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels([f"Filter {fid}" for fid in filter_ids], rotation=45, ha="right")
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.set_ylim(0, 1.15)

        plt.tight_layout()
        return fig
