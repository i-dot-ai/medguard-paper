"""
PINCER filter statistics analysis.

Uses processor.get_patients_by_filters() with production parameters to ensure
identical treatment as patient profile generation.

Three separate analysis classes:
1. PincerFilterRawMatchesAnalysis - Raw matches (filter_id, start_date, end_date)
2. PincerFilterSummaryAnalysis - Per-filter summary with prevalence
3. PincerFilterMultipleMatchesAnalysis - Distribution of multiple filter matches
"""

from datetime import datetime, date
from typing import Dict, List
import logging

import polars as pl
import matplotlib.pyplot as plt

from medguard.analysis.base import AnalysisBase

logger = logging.getLogger(__name__)


# Production parameters (matching generate_patient_profiles_with_filters.py)
FILTER_IDS = [5, 6, 10, 16, 23, 26, 28, 33, 43, 55]
MIN_DURATION_DAYS = 14
START_DATE_AFTER = datetime(2020, 1, 1)
OBSERVATION_END_DATE = date(2025, 10, 24)  # Today's date from env


def get_filter_data(processor) -> Dict[int, List[Dict]]:
    """
    Get patient filter data using production parameters.

    This is called by all three analysis classes to ensure they use
    identical data.
    """
    logger.info("Fetching PINCER filter data with production parameters...")
    logger.info(f"  Filters: {FILTER_IDS}")
    logger.info(f"  Min duration: {MIN_DURATION_DAYS} days")
    logger.info(f"  Start date after: {START_DATE_AFTER}")

    patient_filters = processor.get_patients_by_filters(
        filter_ids=FILTER_IDS,
        min_duration_days=MIN_DURATION_DAYS,
        start_date_after=START_DATE_AFTER,
    )

    logger.info(f"Found {len(patient_filters)} unique patients matching filters")
    return patient_filters


class PincerFilterRawMatchesAnalysis(AnalysisBase):
    """Raw filter matches (filter_id, start_date, end_date - NO patient_id)."""

    def __init__(self, processor):
        super().__init__(processor, name="pincer_filter_raw_matches")

    def get_sql_statement(self) -> str:
        # Not used - we call processor.get_patients_by_filters() directly
        return ""

    def execute(self) -> pl.DataFrame:
        # Override execute to use processor.get_patients_by_filters()
        patient_filters = get_filter_data(self.processor)

        # Generate raw data (filter_id, start_date, end_date - NO patient_id)
        rows = []
        for patient_id, filter_matches in patient_filters.items():
            for match in filter_matches:
                # Handle both datetime and date objects
                start_date = match["start_date"]
                end_date = match["end_date"]
                if hasattr(start_date, "date"):
                    start_date = start_date.date()
                if hasattr(end_date, "date"):
                    end_date = end_date.date()

                rows.append(
                    {
                        "filter_id": match["filter_id"],
                        "start_date": start_date,
                        "end_date": end_date,
                    }
                )

        df = pl.DataFrame(rows)
        return df.sort(["filter_id", "start_date"])


class PincerFilterSummaryAnalysis(AnalysisBase):
    """Per-filter summary statistics including prevalence."""

    def __init__(self, processor):
        super().__init__(processor, name="pincer_filter_summary")

    def get_sql_statement(self) -> str:
        # Not used - we call processor.get_patients_by_filters() directly
        return ""

    def execute(self) -> pl.DataFrame:
        # Override execute to use processor.get_patients_by_filters()
        # Get data WITH 14-day minimum
        patient_filters_with_min = get_filter_data(self.processor)

        # Get data WITHOUT minimum duration constraint
        logger.info("Fetching PINCER filter data with NO minimum duration...")
        patient_filters_no_min = self.processor.get_patients_by_filters(
            filter_ids=FILTER_IDS,
            min_duration_days=None,  # No minimum duration
            start_date_after=START_DATE_AFTER,
        )
        logger.info(
            f"Found {len(patient_filters_no_min)} unique patients (no min duration)"
        )

        # Get total patients in dataset for population-level prevalence
        patient_link_view = self.processor.default_kwargs["patient_link_view"]
        total_patients_sql = f"""
        SELECT COUNT(*) as total_patients
        FROM {patient_link_view}
        WHERE (Merged != 'Y' OR Merged IS NULL)
            AND (Deleted != 'Y' OR Deleted IS NULL)
        """
        total_patients = self.processor.conn.execute(total_patients_sql).fetchone()[0]
        logger.info(f"Total patients in dataset: {total_patients:,}")

        # Organize by filter_id - WITH 14-day minimum
        filter_to_matches_with_min = {}
        for patient_id, filter_matches in patient_filters_with_min.items():
            for match in filter_matches:
                filter_id = match["filter_id"]
                if filter_id not in filter_to_matches_with_min:
                    filter_to_matches_with_min[filter_id] = []

                # Handle both datetime and date objects
                start_date = match["start_date"]
                end_date = match["end_date"]
                if hasattr(start_date, "date"):
                    start_date = start_date.date()
                if hasattr(end_date, "date"):
                    end_date = end_date.date()

                filter_to_matches_with_min[filter_id].append(
                    {
                        "patient_id": patient_id,
                        "start_date": start_date,
                        "end_date": end_date,
                    }
                )

        # Organize by filter_id - NO minimum duration
        filter_to_matches_no_min = {}
        for patient_id, filter_matches in patient_filters_no_min.items():
            for match in filter_matches:
                filter_id = match["filter_id"]
                if filter_id not in filter_to_matches_no_min:
                    filter_to_matches_no_min[filter_id] = []

                # Handle both datetime and date objects
                start_date = match["start_date"]
                end_date = match["end_date"]
                if hasattr(start_date, "date"):
                    start_date = start_date.date()
                if hasattr(end_date, "date"):
                    end_date = end_date.date()

                filter_to_matches_no_min[filter_id].append(
                    {
                        "patient_id": patient_id,
                        "start_date": start_date,
                        "end_date": end_date,
                    }
                )

        # Calculate observation period in days
        observation_start = START_DATE_AFTER.date()
        observation_period_days = (OBSERVATION_END_DATE - observation_start).days

        # Get all filter IDs that appear in either dataset
        all_filter_ids = set(filter_to_matches_with_min.keys()) | set(
            filter_to_matches_no_min.keys()
        )

        summary_rows = []
        for filter_id in sorted(all_filter_ids):
            # Process WITH 14-day minimum
            matches_with_min = filter_to_matches_with_min.get(filter_id, [])
            if matches_with_min:
                unique_patients_with_min = set(
                    m["patient_id"] for m in matches_with_min
                )
                n_patients_with_min = len(unique_patients_with_min)
                durations_with_min = [
                    (m["end_date"] - m["start_date"]).days for m in matches_with_min
                ]
                total_at_risk_days_with_min = sum(durations_with_min)
                total_observation_days_matched_with_min = (
                    observation_period_days * n_patients_with_min
                )
                prevalence_among_matched_with_min = (
                    total_at_risk_days_with_min
                    / total_observation_days_matched_with_min
                    if total_observation_days_matched_with_min > 0
                    else 0.0
                )
                total_observation_days_population = (
                    observation_period_days * total_patients
                )
                prevalence_population_with_min = (
                    total_at_risk_days_with_min / total_observation_days_population
                    if total_observation_days_population > 0
                    else 0.0
                )
            else:
                unique_patients_with_min = set()
                n_patients_with_min = 0
                durations_with_min = []
                total_at_risk_days_with_min = 0
                prevalence_among_matched_with_min = 0.0
                prevalence_population_with_min = 0.0

            # Process WITHOUT minimum duration
            matches_no_min = filter_to_matches_no_min.get(filter_id, [])
            if matches_no_min:
                unique_patients_no_min = set(m["patient_id"] for m in matches_no_min)
                n_patients_no_min = len(unique_patients_no_min)
                durations_no_min = [
                    (m["end_date"] - m["start_date"]).days for m in matches_no_min
                ]
                total_at_risk_days_no_min = sum(durations_no_min)
                total_observation_days_matched_no_min = (
                    observation_period_days * n_patients_no_min
                )
                prevalence_among_matched_no_min = (
                    total_at_risk_days_no_min / total_observation_days_matched_no_min
                    if total_observation_days_matched_no_min > 0
                    else 0.0
                )
                total_observation_days_population = (
                    observation_period_days * total_patients
                )
                prevalence_population_no_min = (
                    total_at_risk_days_no_min / total_observation_days_population
                    if total_observation_days_population > 0
                    else 0.0
                )
            else:
                unique_patients_no_min = set()
                n_patients_no_min = 0
                durations_no_min = []
                total_at_risk_days_no_min = 0
                prevalence_among_matched_no_min = 0.0
                prevalence_population_no_min = 0.0

            # Use the WITH minimum data for duration statistics (as that's the production constraint)
            summary_rows.append(
                {
                    "filter_id": filter_id,
                    # Stats with 14-day minimum (production constraint)
                    "unique_patients_min14d": n_patients_with_min,
                    "total_matches_min14d": len(matches_with_min),
                    "mean_duration_days_min14d": round(
                        sum(durations_with_min) / len(durations_with_min), 1
                    )
                    if durations_with_min
                    else 0,
                    "median_duration_days_min14d": round(
                        sorted(durations_with_min)[len(durations_with_min) // 2], 1
                    )
                    if durations_with_min
                    else 0,
                    "min_duration_days_min14d": min(durations_with_min)
                    if durations_with_min
                    else 0,
                    "max_duration_days_min14d": max(durations_with_min)
                    if durations_with_min
                    else 0,
                    "prevalence_among_matched_min14d": round(
                        prevalence_among_matched_with_min, 6
                    ),
                    "prevalence_population_min14d": round(
                        prevalence_population_with_min, 6
                    ),
                    # Stats without minimum duration
                    "unique_patients_no_min": n_patients_no_min,
                    "total_matches_no_min": len(matches_no_min),
                    "prevalence_among_matched_no_min": round(
                        prevalence_among_matched_no_min, 6
                    ),
                    "prevalence_population_no_min": round(
                        prevalence_population_no_min, 6
                    ),
                }
            )

        return pl.DataFrame(summary_rows)

    def plot(self):
        """
        Create plots showing PINCER filter prevalence.

        Returns:
            List of (figure, suffix) tuples for multiple plots
        """
        # Load the saved data
        df = self.load_df()

        # Set publication-quality style
        plt.style.use("seaborn-v0_8-paper")
        plt.rcParams["font.size"] = 11
        plt.rcParams["axes.labelsize"] = 12
        plt.rcParams["axes.titlesize"] = 13

        # Extract data
        filter_ids = df["filter_id"].to_list()
        prevalence_per_million = (
            df["prevalence_population_min14d"] * 1_000_000
        ).to_list()  # Convert to per million
        unique_patients = df["unique_patients_min14d"].to_list()

        # PLOT 1: Population prevalence
        fig1, ax1 = plt.subplots(figsize=(10, 6))

        # Use a color gradient
        colors = plt.cm.viridis(range(0, 256, 256 // len(filter_ids)))
        bars = ax1.bar(
            range(len(filter_ids)),
            prevalence_per_million,
            color=colors,
            alpha=0.8,
            edgecolor="black",
            linewidth=0.5,
        )

        # Add value labels on top of bars
        for i, (bar, prev) in enumerate(zip(bars, prevalence_per_million)):
            height = bar.get_height()
            ax1.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{prev:.0f}",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )

        # Labels and title
        ax1.set_xticks(range(len(filter_ids)))
        ax1.set_xticklabels(
            [f"Filter {fid}" for fid in filter_ids], rotation=45, ha="right"
        )
        ax1.set_xlabel("PINCER Filter ID", fontweight="bold")
        ax1.set_ylabel("Expected Number per Million", fontweight="bold")
        ax1.set_title(
            "PINCER Filter Population Prevalence\n(14-Day Minimum Duration)",
            fontweight="bold",
            pad=20,
        )
        ax1.grid(axis="y", alpha=0.3, linestyle="--")
        ax1.set_ylim(0, max(prevalence_per_million) * 1.3)  # Add padding for labels

        plt.tight_layout()

        # PLOT 2: Patient counts by filter
        fig2, ax2 = plt.subplots(figsize=(10, 6))

        bars2 = ax2.bar(
            range(len(filter_ids)),
            unique_patients,
            color=colors,
            alpha=0.8,
            edgecolor="black",
            linewidth=0.5,
        )

        # Add value labels on top of bars
        for i, (bar, n_patients) in enumerate(zip(bars2, unique_patients)):
            height = bar.get_height()
            ax2.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{int(n_patients):,}",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )

        # Labels and title
        ax2.set_xticks(range(len(filter_ids)))
        ax2.set_xticklabels(
            [f"Filter {fid}" for fid in filter_ids], rotation=45, ha="right"
        )
        ax2.set_xlabel("PINCER Filter ID", fontweight="bold")
        ax2.set_ylabel("Number of Unique Patients", fontweight="bold")
        ax2.set_title(
            "Number of Patients Matched by Each PINCER Filter\n(14-Day Minimum Duration)",
            fontweight="bold",
            pad=20,
        )
        ax2.grid(axis="y", alpha=0.3, linestyle="--")
        ax2.set_ylim(0, max(unique_patients) * 1.3)  # Add padding for labels

        plt.tight_layout()

        return [(fig1, "_prevalence"), (fig2, "_patient_counts")]


class PincerFilterMultipleMatchesAnalysis(AnalysisBase):
    """Distribution of patients matching 1, 2, 3+ filters."""

    def __init__(self, processor):
        super().__init__(processor, name="pincer_filter_multiple_matches")

    def get_sql_statement(self) -> str:
        # Not used - we call processor.get_patients_by_filters() directly
        return ""

    def execute(self) -> pl.DataFrame:
        # Override execute to use processor.get_patients_by_filters()
        patient_filters = get_filter_data(self.processor)

        # Count how many filters each patient matches
        filter_count_distribution = {}
        for patient_id, filter_matches in patient_filters.items():
            n_filters = len(filter_matches)
            if n_filters not in filter_count_distribution:
                filter_count_distribution[n_filters] = 0
            filter_count_distribution[n_filters] += 1

        # Convert to DataFrame
        rows = []
        total_patients = len(patient_filters)
        for n_filters in sorted(filter_count_distribution.keys()):
            count = filter_count_distribution[n_filters]
            rows.append(
                {
                    "number_of_filters_matched": n_filters,
                    "patient_count": count,
                    "percentage": round(100.0 * count / total_patients, 1)
                    if total_patients > 0
                    else 0.0,
                }
            )

        return pl.DataFrame(rows)

    def plot(self) -> plt.Figure:
        """
        Create bar chart showing distribution of patients by number of PINCER filters matched.

        Returns:
            Matplotlib figure
        """
        # Load the saved data
        df = self.load_df()

        # Set publication-quality style
        plt.style.use("seaborn-v0_8-paper")
        plt.rcParams["font.size"] = 11
        plt.rcParams["axes.labelsize"] = 12
        plt.rcParams["axes.titlesize"] = 13

        # Extract data
        num_filters = df["number_of_filters_matched"].to_list()
        percentages = df["percentage"].to_list()
        counts = df["patient_count"].to_list()

        # Create bar chart
        fig, ax = plt.subplots(figsize=(8, 6))

        # Use purple/blue color scheme for PINCER filters
        colors = ["#3498db", "#9b59b6", "#e74c3c"][: len(num_filters)]
        bars = ax.bar(
            num_filters,
            percentages,
            color=colors,
            alpha=0.8,
            edgecolor="black",
            linewidth=0.5,
        )

        # Add value labels on top of bars
        for i, (bar, pct, count) in enumerate(zip(bars, percentages, counts)):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{pct:.1f}%\n(n={int(count):,})",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        # Labels and title
        ax.set_xlabel("Number of PINCER Filters Matched", fontweight="bold")
        ax.set_ylabel("Percentage of Patients (%)", fontweight="bold")
        ax.set_title(
            "Distribution of Patients by Number of PINCER Filters Matched",
            fontweight="bold",
            pad=20,
        )
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.set_ylim(0, max(percentages) * 1.25)  # Add padding for labels

        # Set x-axis ticks to show only the actual filter counts
        ax.set_xticks(num_filters)
        ax.set_xlim(min(num_filters) - 0.5, max(num_filters) + 0.5)

        plt.tight_layout()

        return fig
