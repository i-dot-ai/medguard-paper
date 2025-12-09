"""
Clinician Score by Month Analysis

Analyzes how clinician scores vary by analysis month to check for temporal bias.
"""

import polars as pl
import matplotlib.pyplot as plt
from statistics import mean, stdev
from math import sqrt

from medguard.analysis.base import EvaluationAnalysisBase
from medguard.analysis.filters import no_data_error


class ScoreByMonthAnalysis(EvaluationAnalysisBase):
    def __init__(self, evaluation, name: str = "score_by_month"):
        super().__init__(evaluation, name=name)

    def execute(self) -> pl.DataFrame:
        ids_no_error = self.evaluation.filter_by_clinician_evaluation(no_data_error())

        rows = []
        for pid in ids_no_error:
            records = self.evaluation.analysed_records_dict.get(pid)
            clinician_eval = self.evaluation.clinician_evaluations_dict.get(pid)

            if not records or not clinician_eval:
                continue

            record = records[-1]  # Use last record
            analysis_date = record.analysis_date
            month_num = analysis_date.month

            rows.append(
                {
                    "patient_id": pid,
                    "month_num": month_num,
                    "score": clinician_eval.score,
                }
            )

        df = pl.DataFrame(rows)

        # Aggregate by month
        summary = (
            df.group_by("month_num")
            .agg(
                [
                    pl.col("score").mean().alias("mean_score"),
                    pl.col("score").std().alias("std_score"),
                    pl.col("score").count().alias("n_patients"),
                ]
            )
            .sort("month_num")
        )

        # Calculate SEM
        summary = summary.with_columns(
            (pl.col("std_score") / pl.col("n_patients").sqrt()).alias("sem_score")
        )

        return summary

    def plot(self) -> plt.Figure:
        df = self.load_df()

        month_names = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]

        plt.style.use("seaborn-v0_8-paper")
        plt.rcParams["font.size"] = 11
        plt.rcParams["axes.labelsize"] = 12
        plt.rcParams["axes.titlesize"] = 13

        fig, ax = plt.subplots(figsize=(10, 6))

        month_nums = df["month_num"].to_list()
        months = [month_names[m - 1] for m in month_nums]
        mean_scores = df["mean_score"].to_list()
        std_scores = [s if s is not None else 0 for s in df["std_score"].to_list()]
        n_patients = df["n_patients"].to_list()
        x = range(len(months))

        ax.bar(
            x,
            mean_scores,
            color="#3498db",
            alpha=0.8,
            edgecolor="black",
            linewidth=0.5,
            yerr=std_scores,
            capsize=5,
            error_kw={"linewidth": 1, "elinewidth": 1, "capthick": 1},
        )

        for i, n in enumerate(n_patients):
            ax.text(
                i,
                mean_scores[i] + std_scores[i] + 0.05,
                f"n={n}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        ax.set_xlabel("Month", fontweight="bold")
        ax.set_ylabel("Clinician Score (mean ± std)", fontweight="bold")
        ax.set_title(
            "Clinician Score by Month (Aggregated Across Years)", fontweight="bold", pad=20
        )
        ax.set_xticks(x)
        ax.set_xticklabels(months)
        ax.set_ylim(0, 1.2)
        ax.grid(axis="y", alpha=0.3, linestyle="--")

        plt.tight_layout()
        return fig


class ScoreByYearAnalysis(EvaluationAnalysisBase):
    def __init__(self, evaluation, name: str = "score_by_year"):
        super().__init__(evaluation, name=name)

    def execute(self) -> pl.DataFrame:
        ids_no_error = self.evaluation.filter_by_clinician_evaluation(no_data_error())

        rows = []
        for pid in ids_no_error:
            records = self.evaluation.analysed_records_dict.get(pid)
            clinician_eval = self.evaluation.clinician_evaluations_dict.get(pid)

            if not records or not clinician_eval:
                continue

            record = records[-1]
            year = record.analysis_date.year

            rows.append(
                {
                    "patient_id": pid,
                    "year": year,
                    "score": clinician_eval.score,
                }
            )

        df = pl.DataFrame(rows)

        summary = (
            df.group_by("year")
            .agg(
                [
                    pl.col("score").mean().alias("mean_score"),
                    pl.col("score").std().alias("std_score"),
                    pl.col("score").count().alias("n_patients"),
                ]
            )
            .sort("year")
        )

        summary = summary.with_columns(
            (pl.col("std_score") / pl.col("n_patients").sqrt()).alias("sem_score")
        )

        return summary

    def plot(self) -> plt.Figure:
        df = self.load_df()

        plt.style.use("seaborn-v0_8-paper")
        plt.rcParams["font.size"] = 11
        plt.rcParams["axes.labelsize"] = 12
        plt.rcParams["axes.titlesize"] = 13

        fig, ax = plt.subplots(figsize=(10, 6))

        years = [str(y) for y in df["year"].to_list()]
        mean_scores = df["mean_score"].to_list()
        std_scores = [s if s is not None else 0 for s in df["std_score"].to_list()]
        n_patients = df["n_patients"].to_list()
        x = range(len(years))

        ax.bar(
            x,
            mean_scores,
            color="#e74c3c",
            alpha=0.8,
            edgecolor="black",
            linewidth=0.5,
            yerr=std_scores,
            capsize=5,
            error_kw={"linewidth": 1, "elinewidth": 1, "capthick": 1},
        )

        for i, n in enumerate(n_patients):
            ax.text(
                i,
                mean_scores[i] + std_scores[i] + 0.05,
                f"n={n}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        ax.set_xlabel("Year", fontweight="bold")
        ax.set_ylabel("Clinician Score (mean ± std)", fontweight="bold")
        ax.set_title("Clinician Score by Year", fontweight="bold", pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(years)
        ax.set_ylim(0, 1.2)
        ax.grid(axis="y", alpha=0.3, linestyle="--")

        plt.tight_layout()
        return fig


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

    # By month
    analysis = ScoreByMonthAnalysis(evaluation)
    df, path = analysis.run()
    print(f"\nSaved data to: {path}")
    print(df)
    fig_path = analysis.run_figure()
    print(f"Saved plot to: {fig_path}")

    # By year
    analysis_year = ScoreByYearAnalysis(evaluation)
    df_year, path_year = analysis_year.run()
    print(f"\nSaved data to: {path_year}")
    print(df_year)
    fig_path_year = analysis_year.run_figure()
    print(f"Saved plot to: {fig_path_year}")
