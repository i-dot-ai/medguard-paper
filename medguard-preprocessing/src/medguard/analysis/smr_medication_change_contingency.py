"""
SMR Medication Change Contingency Table Analysis

This analysis creates a 2x2 contingency table showing the relationship between
SMR outcome codes and actual medication changes:
- Rows: flag_smr (True = positive outcome codes, False = negative outcome codes)
- Columns: any_change (True = at least one medication start/stop, False = no changes)

Percentages are calculated as proportion of the overall total (all SMRs), not
within each outcome group. This allows direct comparison of cell sizes.

Key findings:
- Shows percentage of all SMRs that are negative outcome with subsequent changes
- Shows percentage of all SMRs that are positive outcome with no recorded changes

Uses the existing smr_medications view which already computes medication changes
within a 3-month window around SMRs (for repeat medications only).
"""

import logging
import polars as pl
import matplotlib.pyplot as plt

from medguard.analysis.base import AnalysisBase

logger = logging.getLogger(__name__)


class SMRMedicationChangeContingencyAnalysis(AnalysisBase):
    """
    2x2 contingency table: flag_smr × any_change

    Shows percentage of SMRs with/without outcome codes that have medication changes.
    """

    def __init__(self, processor):
        super().__init__(processor, name="smr_medication_change_contingency")

    def get_sql_statement(self) -> str:
        """
        Build contingency table from smr_events and smr_medications.

        Logic:
        1. Get all SMRs with outcome codes (flag_smr IS NOT NULL)
        2. Join to medication changes (any started or stopped)
        3. Compute any_change = TRUE if at least one medication change exists
        4. Group by flag_smr × any_change and count
        """

        smr_events_view = self.processor.default_kwargs["smr_events_view"]
        smr_medications = self.processor.default_kwargs["smr_medications_table"]

        sql = f"""
        -- Get all SMRs with outcome codes
        WITH smr_with_outcomes AS (
            SELECT DISTINCT
                FK_Patient_Link_ID,
                EventDate as smr_date,
                flag_smr
            FROM {smr_events_view}
            WHERE was_smr = TRUE
                AND flag_smr IS NOT NULL  -- Only SMRs with coded outcomes
        ),

        -- Get medication changes for these SMRs
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

        -- Aggregate to one row per SMR (in case multiple medication changes)
        smr_aggregated AS (
            SELECT
                FK_Patient_Link_ID,
                smr_date,
                flag_smr,
                MAX(any_change) as any_change  -- TRUE if any medication changed
            FROM smr_with_changes
            GROUP BY FK_Patient_Link_ID, smr_date, flag_smr
        )

        SELECT
            flag_smr,
            any_change,
            COUNT(*) as count
        FROM smr_aggregated
        GROUP BY flag_smr, any_change
        ORDER BY flag_smr DESC, any_change DESC
        """

        return sql

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Calculate percentages as proportion of overall total (all SMRs).

        Each cell shows its percentage out of the total number of SMRs across all groups.
        """

        # Calculate overall total across all groups
        total = df["count"].sum()

        # Calculate percentages out of overall total
        df = df.with_columns(
            [
                (pl.col("count") / total * 100).round(1).alias("percentage"),
                pl.lit(total).alias("total"),
            ]
        )

        # Reorder columns and add readable labels
        df = df.with_columns(
            [
                pl.when(pl.col("flag_smr") == True)
                .then(pl.lit("positive_outcome"))
                .otherwise(pl.lit("negative_outcome"))
                .alias("outcome_type"),
                pl.when(pl.col("any_change") == True)
                .then(pl.lit("has_change"))
                .otherwise(pl.lit("no_change"))
                .alias("change_status"),
            ]
        )

        # Select final columns
        result = df.select(
            ["outcome_type", "change_status", "count", "total", "percentage"]
        ).sort(["outcome_type", "change_status"], descending=[True, True])

        # Log key findings
        logger.info("\n=== SMR Medication Change Contingency Table ===")

        for row in result.iter_rows(named=True):
            logger.info(
                f"{row['outcome_type']:20s} | {row['change_status']:12s} | "
                f"{row['count']:6d} | {row['percentage']:5.1f}%"
            )

        # Calculate key percentages (as proportion of all SMRs)
        negative_with_change = result.filter(
            (pl.col("outcome_type") == "negative_outcome")
            & (pl.col("change_status") == "has_change")
        )
        if len(negative_with_change) > 0:
            pct = negative_with_change["percentage"][0]
            logger.info(
                f"\nNegative outcome variability: {pct:.1f}% of all SMRs (negative outcome + medication changes)"
            )

        positive_no_change = result.filter(
            (pl.col("outcome_type") == "positive_outcome")
            & (pl.col("change_status") == "no_change")
        )
        if len(positive_no_change) > 0:
            pct = positive_no_change["percentage"][0]
            logger.info(
                f"Positive outcome inverse: {pct:.1f}% of all SMRs (positive outcome + no medication changes)"
            )

        return result

    def plot(self) -> plt.Figure:
        """
        Create grouped bar chart showing outcome codes vs medication changes.

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

        # Prepare data for grouped bar chart
        positive_data = df.filter(pl.col("outcome_type") == "positive_outcome").sort(
            "change_status", descending=True
        )
        negative_data = df.filter(pl.col("outcome_type") == "negative_outcome").sort(
            "change_status", descending=True
        )

        # Extract values
        categories = ["Has Change", "No Change"]
        positive_pcts = positive_data["percentage"].to_list()
        negative_pcts = negative_data["percentage"].to_list()

        # Create grouped bar chart
        fig, ax = plt.subplots(figsize=(8, 6))

        x = range(len(categories))
        width = 0.35

        bars1 = ax.bar(
            [i - width / 2 for i in x],
            positive_pcts,
            width,
            label="Positive Outcome SNOMED Code",
            color="#2ecc71",
            alpha=0.8,
        )
        bars2 = ax.bar(
            [i + width / 2 for i in x],
            negative_pcts,
            width,
            label="Negative Outcome SNOMED Code",
            color="#e74c3c",
            alpha=0.8,
        )

        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    f"{height:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                )

        # Labels and title
        ax.set_xlabel("Medication Change Status", fontweight="bold")
        ax.set_ylabel("Percentage of SMRs (%)", fontweight="bold")
        ax.set_title(
            "SMR Outcome Codes vs Medication Changes\n(3-Month Window)",
            fontweight="bold",
            pad=20,
        )
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.legend(loc="upper left", frameon=True, fancybox=True, shadow=True)
        ax.grid(axis="y", alpha=0.3, linestyle="--")

        # Set y-axis to start at 0 and go to 35%
        ax.set_ylim(0, 35)

        plt.tight_layout()

        return fig
