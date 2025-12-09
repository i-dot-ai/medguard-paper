"""
Histogram data for GP events per patient distribution.

Section: 2.2 Data Source and Population
Returns: Binned counts of patients by number of GP events
         - For plotting histograms in the paper
         - Separate analyses for overall and since 2020
"""

import polars as pl
import matplotlib.pyplot as plt

from medguard.analysis.base import AnalysisBase


SQL_OVERALL = """
WITH patient_event_counts AS (
    SELECT
        FK_Patient_Link_ID,
        COUNT(*) as event_count
    FROM {gp_events_view}
    WHERE (Deleted = 'N' OR Deleted IS NULL)
        AND EventDate IS NOT NULL
    GROUP BY FK_Patient_Link_ID
)
SELECT
    event_count,
    COUNT(*) as patient_count
FROM patient_event_counts
GROUP BY event_count
ORDER BY event_count
"""

SQL_SINCE_2020 = """
WITH patient_event_counts AS (
    SELECT
        FK_Patient_Link_ID,
        COUNT(*) as event_count
    FROM {gp_events_view}
    WHERE (Deleted = 'N' OR Deleted IS NULL)
        AND EventDate IS NOT NULL
        AND EventDate >= '2020-01-01'
    GROUP BY FK_Patient_Link_ID
)
SELECT
    event_count,
    COUNT(*) as patient_count
FROM patient_event_counts
GROUP BY event_count
ORDER BY event_count
"""


class GPEventsPerPatientHistogramOverallAnalysis(AnalysisBase):
    """Raw histogram data: patients by GP event count (all time)."""

    def __init__(self, processor):
        super().__init__(processor, name="gp_events_per_patient_histogram_overall")

    def get_sql_statement(self) -> str:
        return SQL_OVERALL.format(
            gp_events_view=self.processor.default_kwargs["gp_events_view"]
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # Add cumulative counts and percentiles for convenience
        total_patients = df["patient_count"].sum()
        return df.with_columns(
            [
                pl.col("patient_count").cum_sum().alias("cumulative_patients"),
                (pl.col("patient_count").cum_sum() / total_patients * 100)
                .round(2)
                .alias("cumulative_pct"),
            ]
        )


class GPEventsPerPatientHistogramSince2020Analysis(AnalysisBase):
    """Raw histogram data: patients by GP event count (since 2020)."""

    def __init__(self, processor):
        super().__init__(processor, name="gp_events_per_patient_histogram_since_2020")

    def get_sql_statement(self) -> str:
        return SQL_SINCE_2020.format(
            gp_events_view=self.processor.default_kwargs["gp_events_view"]
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # Add cumulative counts and percentiles
        total_patients = df["patient_count"].sum()
        return df.with_columns(
            [
                pl.col("patient_count").cum_sum().alias("cumulative_patients"),
                (pl.col("patient_count").cum_sum() / total_patients * 100)
                .round(2)
                .alias("cumulative_pct"),
            ]
        )


# Binned histogram for easier visualization
SQL_BINNED = """
WITH patient_event_counts AS (
    SELECT
        FK_Patient_Link_ID,
        COUNT(*) as event_count
    FROM {gp_events_view}
    WHERE (Deleted = 'N' OR Deleted IS NULL)
        AND EventDate IS NOT NULL
        {date_filter}
    GROUP BY FK_Patient_Link_ID
),
binned_counts AS (
    SELECT
        CASE
            WHEN event_count = 0 THEN '0'
            WHEN event_count BETWEEN 1 AND 10 THEN '1-10'
            WHEN event_count BETWEEN 11 AND 25 THEN '11-25'
            WHEN event_count BETWEEN 26 AND 50 THEN '26-50'
            WHEN event_count BETWEEN 51 AND 100 THEN '51-100'
            WHEN event_count BETWEEN 101 AND 250 THEN '101-250'
            WHEN event_count BETWEEN 251 AND 500 THEN '251-500'
            WHEN event_count BETWEEN 501 AND 1000 THEN '501-1000'
            WHEN event_count BETWEEN 1001 AND 2500 THEN '1001-2500'
            WHEN event_count BETWEEN 2501 AND 5000 THEN '2501-5000'
            WHEN event_count BETWEEN 5001 AND 10000 THEN '5001-10000'
            WHEN event_count > 10000 THEN '>10000'
        END as bin,
        event_count,
        1 as patient
    FROM patient_event_counts
)
SELECT
    bin,
    COUNT(*) as patient_count,
    MIN(event_count) as min_events_in_bin,
    MAX(event_count) as max_events_in_bin,
    ROUND(AVG(event_count), 1) as avg_events_in_bin
FROM binned_counts
GROUP BY bin
ORDER BY min_events_in_bin
"""


class GPEventsPerPatientBinnedOverallAnalysis(AnalysisBase):
    """Binned histogram: patients by event count ranges (all time)."""

    def __init__(self, processor):
        super().__init__(processor, name="gp_events_per_patient_binned_overall")

    def get_sql_statement(self) -> str:
        return SQL_BINNED.format(
            gp_events_view=self.processor.default_kwargs["gp_events_view"],
            date_filter="",
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # Add percentage of total
        total_patients = df["patient_count"].sum()
        return df.with_columns(
            [
                (pl.col("patient_count") / total_patients * 100)
                .round(2)
                .alias("pct_of_patients"),
                pl.col("patient_count").cum_sum().alias("cumulative_patients"),
                (pl.col("patient_count").cum_sum() / total_patients * 100)
                .round(2)
                .alias("cumulative_pct"),
            ]
        )


class GPEventsPerPatientBinnedSince2020Analysis(AnalysisBase):
    """Binned histogram: patients by event count ranges (since 2020)."""

    def __init__(self, processor):
        super().__init__(processor, name="gp_events_per_patient_binned_since_2020")

    def get_sql_statement(self) -> str:
        return SQL_BINNED.format(
            gp_events_view=self.processor.default_kwargs["gp_events_view"],
            date_filter="AND EventDate >= '2020-01-01'",
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # Add percentage of total
        total_patients = df["patient_count"].sum()
        return df.with_columns(
            [
                (pl.col("patient_count") / total_patients * 100)
                .round(2)
                .alias("pct_of_patients"),
                pl.col("patient_count").cum_sum().alias("cumulative_patients"),
                (pl.col("patient_count").cum_sum() / total_patients * 100)
                .round(2)
                .alias("cumulative_pct"),
            ]
        )

    def plot(self) -> plt.Figure:
        """
        Create bar chart showing distribution of GP events per patient (since 2020).

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
        bins = df["bin"].to_list()
        percentages = df["pct_of_patients"].to_list()
        counts = df["patient_count"].to_list()

        # Create bar chart
        fig, ax = plt.subplots(figsize=(10, 6))

        # Use blue color for general population
        bars = ax.bar(
            bins,
            percentages,
            color="#3498db",
            alpha=0.8,
            edgecolor="black",
            linewidth=0.5,
        )

        # Add value labels on top of bars for percentages > 1%
        for i, (bar, pct, count) in enumerate(zip(bars, percentages, counts)):
            height = bar.get_height()
            if pct >= 1.0:  # Only label bars with >= 1%
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    f"{pct:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

        # Labels and title
        ax.set_xlabel("Number of GP Events (Since 2020)", fontweight="bold")
        ax.set_ylabel("Percentage of Patients (%)", fontweight="bold")
        ax.set_title(
            "Distribution of GP Events Per Patient (Since 2020)",
            fontweight="bold",
            pad=20,
        )
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.set_ylim(0, max(percentages) * 1.15)  # Add padding for labels

        # Rotate x-axis labels for readability
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        return fig
