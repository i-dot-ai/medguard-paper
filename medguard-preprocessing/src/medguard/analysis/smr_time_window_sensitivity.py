"""
SMR Time Window Sensitivity Analysis

This analysis tests how the choice of time window affects the percentage of SMRs
that show medication changes. We test windows from 1 day to 3 months:
- 1 day
- 4 days
- 7 days (0.25 months)
- 15 days (0.50 months)
- 22 days (0.75 months)
- 30 days (1.00 months)
- ... in 0.25 month increments up to 90 days (3.00 months)

For each window, we:
1. Detect medication starts/stops using the same logic as smr_medications.sql
2. Calculate percentage of SMRs with at least one medication change
3. Show how this percentage increases with longer windows

This demonstrates that there's no clear "cliff" at the SMR date - medication
changes happen gradually over time rather than immediately after the review.
The percentage of SMRs with medication changes increases smoothly from shorter
to longer time windows, showing sensitivity to the chosen time window.
"""

import logging
from pathlib import Path
import polars as pl
import matplotlib.pyplot as plt

from medguard.analysis.base import AnalysisBase

logger = logging.getLogger(__name__)


class SMRTimeWindowSensitivityAnalysis(AnalysisBase):
    """
    Calculate percentage of SMRs with medication changes for different time windows.

    Tests windows from 0.25 to 3.0 months (in 0.25 month increments) to show
    sensitivity to window choice. Uses 30 days = 1 month for conversion.
    """

    def __init__(self, processor):
        super().__init__(processor, name="smr_time_window_sensitivity")

    def get_sql_statement(self) -> str:
        """Not used - we override execute() to run multiple window sizes."""
        return ""

    def execute(self) -> pl.DataFrame:
        """
        Override execute to run analysis for multiple time windows.

        For each window:
        1. Load smr_medications.sql template
        2. Replace '3 MONTHS' with specific interval
        3. Calculate medication changes
        4. Count SMRs with any_change
        """

        # Load the SQL template
        sql_template_path = (
            Path(__file__).parent.parent / "sql" / "views" / "smr_medications.sql"
        )
        with open(sql_template_path, "r") as f:
            sql_template = f.read()

        # Define time windows to test
        # Start with very short windows (1, 4 days)
        # Then 0.25 to 3.0 months in 0.25 month increments (using 30 days = 1 month)
        windows = [
            ("0.03_months", "1 DAYS", 1, 1 / 30),
            ("0.13_months", "4 DAYS", 4, 4 / 30),
        ]

        for months in [i * 0.25 for i in range(1, 13)]:  # 0.25, 0.5, 0.75, ..., 3.0
            days = int(months * 30)
            window_name = f"{months:.2f}_months"
            windows.append((window_name, f"{days} DAYS", days, months))

        results = []

        for window_name, interval_str, days, months in windows:
            logger.info(f"\nAnalyzing {window_name} window ({days} days)...")

            # Replace '3 MONTHS' with the specific interval (in days)
            sql_modified = sql_template.replace("'3 MONTHS'", f"'{interval_str}'")

            # Format with processor kwargs (table names)
            sql_modified = sql_modified.format(**self.processor.default_kwargs)

            # Execute to create the medication changes table
            self.processor.conn.execute(sql_modified)

            # Now query to count SMRs with changes
            smr_events_view = self.processor.default_kwargs["smr_events_view"]
            smr_medications = self.processor.default_kwargs["smr_medications_table"]

            count_sql = f"""
            -- Get all SMRs with outcome codes
            WITH smr_with_outcomes AS (
                SELECT DISTINCT
                    FK_Patient_Link_ID,
                    EventDate as smr_date,
                    flag_smr
                FROM {smr_events_view}
                WHERE was_smr = TRUE
                    AND flag_smr IS NOT NULL
            ),

            -- Join to medication changes
            smr_with_changes AS (
                SELECT
                    s.FK_Patient_Link_ID,
                    s.smr_date,
                    s.flag_smr,
                    CASE
                        WHEN m.medication_code IS NOT NULL THEN TRUE
                        ELSE FALSE
                    END as any_change
                FROM smr_with_outcomes s
                LEFT JOIN {smr_medications} m
                    ON s.FK_Patient_Link_ID = m.FK_Patient_Link_ID
                    AND s.smr_date = m.smr_date
            ),

            -- Aggregate to one row per SMR
            smr_aggregated AS (
                SELECT
                    FK_Patient_Link_ID,
                    smr_date,
                    flag_smr,
                    MAX(any_change) as any_change
                FROM smr_with_changes
                GROUP BY FK_Patient_Link_ID, smr_date, flag_smr
            )

            SELECT
                COUNT(*) as total_smrs,
                SUM(CASE WHEN any_change = TRUE THEN 1 ELSE 0 END) as smrs_with_change,
                SUM(CASE WHEN any_change = FALSE THEN 1 ELSE 0 END) as smrs_without_change
            FROM smr_aggregated
            """

            count_result = self.processor.conn.execute(count_sql).fetchone()
            total_smrs, smrs_with_change, smrs_without_change = count_result

            percentage_with_change = (
                (smrs_with_change / total_smrs * 100) if total_smrs > 0 else 0.0
            )

            logger.info(f"  Total SMRs: {total_smrs:,}")
            logger.info(
                f"  SMRs with change: {smrs_with_change:,} ({percentage_with_change:.1f}%)"
            )
            logger.info(
                f"  SMRs without change: {smrs_without_change:,} ({100 - percentage_with_change:.1f}%)"
            )

            results.append(
                {
                    "time_window_months": round(months, 2),
                    "time_window_days": days,
                    "total_smrs": total_smrs,
                    "smrs_with_change": smrs_with_change,
                    "smrs_without_change": smrs_without_change,
                    "percentage_with_change": round(percentage_with_change, 1),
                    "percentage_without_change": round(100 - percentage_with_change, 1),
                }
            )

        # Create DataFrame
        df = pl.DataFrame(results).sort("time_window_days")

        logger.info("\n=== Time Window Sensitivity Summary ===")
        for row in df.iter_rows(named=True):
            logger.info(
                f"{row['time_window_months']:4.2f} months ({row['time_window_days']:3d} days): "
                f"{row['percentage_with_change']:5.1f}% with changes"
            )

        return df

    def plot(self) -> plt.Figure:
        """
        Create line plot showing medication change detection sensitivity to time window.

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
        days = df["time_window_days"].to_list()
        pct_with_change = df["percentage_with_change"].to_list()

        # Create line plot
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(
            days,
            pct_with_change,
            marker="o",
            linewidth=2,
            markersize=6,
            color="#3498db",
            alpha=0.8,
        )

        # Add horizontal lines at key percentages
        ax.axhline(y=42.7, color="gray", linestyle="--", alpha=0.5, linewidth=1)
        ax.text(
            47.5,
            41.2,
            "30 days: 42.7%",
            va="top",
            ha="center",
            fontsize=9,
            color="gray",
        )

        ax.axhline(y=58.5, color="gray", linestyle="--", alpha=0.5, linewidth=1)
        ax.text(
            47.5,
            57.0,
            "90 days: 58.5%",
            va="top",
            ha="center",
            fontsize=9,
            color="gray",
        )

        # Labels and title
        ax.set_xlabel("Time Window (Days)", fontweight="bold")
        ax.set_ylabel("SMRs with Medication Changes (%)", fontweight="bold")
        ax.set_title(
            "Medication Change Detection Sensitivity to Time Window",
            fontweight="bold",
            pad=20,
        )
        ax.grid(True, alpha=0.3, linestyle="--")

        # Set axis limits
        ax.set_xlim(0, 95)
        ax.set_ylim(0, 65)

        plt.tight_layout()

        return fig
