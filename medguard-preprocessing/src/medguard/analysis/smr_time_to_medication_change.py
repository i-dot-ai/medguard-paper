"""
SMR Time to Medication Change Analysis

This analysis calculates time from SMR to meaningful medication changes,
comparing median days between SMRs with positive vs negative outcome codes.

This analysis calculates time from SMR to meaningful medication changes:
1. A prescription active at SMR ending (medication stopped)
2. A new prescription starting (new medication)

IMPORTANT: Returns ONE ROW PER MEDICATION CHANGE (not one per SMR).
- If an SMR has 5 medications that change, we get 5 data points
- Statistics are calculated across ALL medication changes, not per-SMR averages
- This measures the typical time for medications to change after an SMR

Compares two groups:
- SMRs with POSITIVE outcome codes (flag_smr = TRUE): e.g., "medication reviewed", "continue"
- SMRs with NEGATIVE outcome codes (flag_smr = FALSE): e.g., "no action", or no outcome coded

Returns statistics for three categories:
1. Repeat medications only (is_repeat_medication = TRUE)
2. Non-repeat medications only (is_repeat_medication = FALSE)
3. All medications combined

Key insight: Even when SMRs have positive outcome codes suggesting medication review,
the time to actual medication change is not meaningfully different from SMRs with
negative/no-action codes. This suggests SMR codes don't reliably predict medication changes.
"""

import logging
from datetime import datetime
from pathlib import Path

import polars as pl
import matplotlib.pyplot as plt
from scipy import stats

from medguard.analysis.base import AnalysisBase

logger = logging.getLogger(__name__)


class SMRTimeToMedicationChangeAnalysis(AnalysisBase):
    """
    Calculate time from SMR to medication change, comparing:
    - SMRs with positive outcome codes (flag_smr = TRUE)
    - SMRs with negative outcome codes (flag_smr = FALSE)

    Returns summary statistics and Mann-Whitney U test results.
    """

    def __init__(self, processor):
        super().__init__(processor, name="smr_time_to_medication_change")

    def get_sql_statement(self) -> str:
        """
        Build SQL query to get time to medication change for both SMR groups.

        For each SMR (positive or negative):
        - Find meaningful medication changes:
          1. A prescription active at SMR ending (medication stopped)
          2. A new prescription starting (new medication)
        - Calculate days between SMR and change
        - Returns ALL changes (not just first per SMR)
        """

        smr_events_view = self.processor.default_kwargs["smr_events_view"]
        gp_prescriptions = self.processor.default_kwargs["gp_prescriptions"]

        sql = f"""
        -- Get all SMR events with outcome codes (exclude NULL)
        WITH smr_events_with_outcomes AS (
            SELECT DISTINCT
                FK_Patient_Link_ID,
                EventDate as smr_date,
                flag_smr,
                CASE
                    WHEN flag_smr = TRUE THEN 'positive_outcome'
                    WHEN flag_smr = FALSE THEN 'negative_outcome'
                END as outcome_type
            FROM {smr_events_view}
            WHERE was_smr = TRUE
                AND flag_smr IS NOT NULL  -- Only include SMRs with coded outcomes
        ),

        -- Prescriptions active at the time of SMR
        prescriptions_active_at_smr AS (
            SELECT
                s.FK_Patient_Link_ID,
                s.smr_date,
                s.outcome_type,
                p.medication_code,
                p.medication_end_date,
                p.is_repeat_medication,
                'active_ending' as change_type
            FROM smr_events_with_outcomes s
            INNER JOIN {gp_prescriptions} p
                ON s.FK_Patient_Link_ID = p.FK_Patient_Link_ID
                AND p.medication_start_date <= s.smr_date
                AND p.medication_end_date > s.smr_date  -- Active at SMR
            WHERE p.medication_end_date IS NOT NULL
        ),

        -- New prescriptions starting after SMR
        new_prescriptions AS (
            SELECT
                s.FK_Patient_Link_ID,
                s.smr_date,
                s.outcome_type,
                p.medication_code,
                p.medication_start_date as medication_end_date,  -- Use start as the "change date"
                p.is_repeat_medication,
                'new_starting' as change_type
            FROM smr_events_with_outcomes s
            INNER JOIN {gp_prescriptions} p
                ON s.FK_Patient_Link_ID = p.FK_Patient_Link_ID
                AND p.medication_start_date > s.smr_date  -- Starts after SMR
        ),

        -- Combine both types of changes
        -- KEEP ALL CHANGES (not just the first per SMR)
        all_changes AS (
            SELECT * FROM prescriptions_active_at_smr
            UNION ALL
            SELECT * FROM new_prescriptions
        )

        SELECT
            outcome_type,
            smr_date,
            medication_end_date as change_date,
            medication_code,
            is_repeat_medication,
            change_type,
            CASE
                WHEN is_repeat_medication = TRUE THEN 'repeat'
                WHEN is_repeat_medication = FALSE THEN 'non_repeat'
                ELSE 'unknown'
            END as medication_type,
            DATE_DIFF('day', smr_date, medication_end_date) as days_to_change
        FROM all_changes
        WHERE medication_end_date IS NOT NULL
            AND DATE_DIFF('day', smr_date, medication_end_date) > 0  -- Positive time only
        ORDER BY outcome_type, medication_type, days_to_change
        """

        return sql

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Calculate summary statistics and Mann-Whitney U test for three categories:
        1. Repeat medications only
        2. Non-repeat medications only
        3. All medications combined

        Returns a summary DataFrame with medians and statistical tests for each category.
        """
        import statistics

        def compute_stats_for_category(df_subset, category_name):
            """Compute statistics for a specific medication category."""
            positive_days = df_subset.filter(
                pl.col("outcome_type") == "positive_outcome"
            )["days_to_change"].to_list()
            negative_days = df_subset.filter(
                pl.col("outcome_type") == "negative_outcome"
            )["days_to_change"].to_list()

            logger.info(f"\n{category_name}:")
            logger.info(f"  Positive outcome SMRs: {len(positive_days)} observations")
            logger.info(f"  Negative outcome SMRs: {len(negative_days)} observations")

            if len(positive_days) == 0 or len(negative_days) == 0:
                logger.warning(
                    f"  {category_name}: One or both groups have no observations"
                )
                return []

            # Calculate medians
            positive_median = statistics.median(positive_days)
            negative_median = statistics.median(negative_days)

            logger.info(f"  Positive median: {positive_median} days")
            logger.info(f"  Negative median: {negative_median} days")

            # Mann-Whitney U test
            u_statistic, p_value = stats.mannwhitneyu(
                positive_days, negative_days, alternative="two-sided"
            )
            logger.info(f"  Mann-Whitney U: {u_statistic}, p-value: {p_value}")

            return [
                {
                    "medication_category": category_name,
                    "group": "positive_outcome",
                    "n_observations": len(positive_days),
                    "median_days": round(positive_median, 1),
                    "test_statistic": None,
                    "p_value": None,
                },
                {
                    "medication_category": category_name,
                    "group": "negative_outcome",
                    "n_observations": len(negative_days),
                    "median_days": round(negative_median, 1),
                    "test_statistic": None,
                    "p_value": None,
                },
                {
                    "medication_category": category_name,
                    "group": "difference",
                    "n_observations": None,
                    "median_days": round(positive_median - negative_median, 1),
                    "test_statistic": None,
                    "p_value": None,
                },
                {
                    "medication_category": category_name,
                    "group": "mann_whitney_u",
                    "n_observations": None,
                    "median_days": None,
                    "test_statistic": round(u_statistic, 2),
                    "p_value": round(p_value, 6),
                },
            ]

        # Compute for all three categories
        all_rows = []

        # 1. Repeat medications only
        repeat_df = df.filter(pl.col("medication_type") == "repeat")
        all_rows.extend(compute_stats_for_category(repeat_df, "repeat_only"))

        # 2. Non-repeat medications only
        non_repeat_df = df.filter(pl.col("medication_type") == "non_repeat")
        all_rows.extend(compute_stats_for_category(non_repeat_df, "non_repeat_only"))

        # 3. All medications combined
        all_rows.extend(compute_stats_for_category(df, "all_medications"))

        return pl.DataFrame(all_rows)

    def plot(self) -> plt.Figure:
        """
        Create grouped bar chart comparing median time to medication change.

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

        # Filter to only the median rows (exclude difference and mann_whitney_u rows)
        median_df = df.filter(
            (pl.col("group") == "positive_outcome")
            | (pl.col("group") == "negative_outcome")
        )

        # Prepare data
        categories = ["Repeat Only", "Non-Repeat Only", "All Medications"]
        cat_map = {
            "repeat_only": "Repeat Only",
            "non_repeat_only": "Non-Repeat Only",
            "all_medications": "All Medications",
        }

        positive_medians = []
        negative_medians = []

        for cat_key in ["repeat_only", "non_repeat_only", "all_medications"]:
            pos_val = median_df.filter(
                (pl.col("medication_category") == cat_key)
                & (pl.col("group") == "positive_outcome")
            )["median_days"].to_list()
            neg_val = median_df.filter(
                (pl.col("medication_category") == cat_key)
                & (pl.col("group") == "negative_outcome")
            )["median_days"].to_list()

            positive_medians.append(pos_val[0] if pos_val else 0)
            negative_medians.append(neg_val[0] if neg_val else 0)

        # Create grouped bar chart
        fig, ax = plt.subplots(figsize=(10, 6))

        x = range(len(categories))
        width = 0.35

        bars1 = ax.bar(
            [i - width / 2 for i in x],
            positive_medians,
            width,
            label="Positive Outcome SNOMED Code",
            color="#2ecc71",
            alpha=0.8,
        )
        bars2 = ax.bar(
            [i + width / 2 for i in x],
            negative_medians,
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
                    f"{int(height)}",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                )

        # Labels and title
        ax.set_xlabel("Medication Category", fontweight="bold")
        ax.set_ylabel("Median Days to Medication Change", fontweight="bold")
        ax.set_title(
            "Median Time to Medication Change by SMR Outcome Type",
            fontweight="bold",
            pad=20,
        )
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.legend(loc="upper left", frameon=True, fancybox=True, shadow=True)
        ax.grid(axis="y", alpha=0.3, linestyle="--")

        # Set y-axis to start at 0
        ax.set_ylim(0, max(positive_medians + negative_medians) * 1.15)

        plt.tight_layout()

        return fig


class SMRTimeToFirstMedicationChangeAnalysis(AnalysisBase):
    """
    Calculate time from SMR to FIRST medication change only (for comparison).

    This is the BIASED approach (kept for illustration) that only looks at
    the earliest change per SMR. This gives much shorter times because it
    always picks the first medication to change, not the typical change time.

    Compare this to SMRTimeToMedicationChangeAnalysis which returns ALL changes.
    """

    def __init__(self, processor):
        super().__init__(processor, name="smr_time_to_first_medication_change")

    def get_sql_statement(self) -> str:
        """
        Build SQL query to get time to FIRST medication change per SMR.

        Uses ROW_NUMBER to select only the earliest change per SMR.
        This illustrates the selection bias of this approach.
        """

        smr_events_view = self.processor.default_kwargs["smr_events_view"]
        gp_prescriptions = self.processor.default_kwargs["gp_prescriptions"]

        sql = f"""
        -- Get all SMR events with outcome codes (exclude NULL)
        WITH smr_events_with_outcomes AS (
            SELECT DISTINCT
                FK_Patient_Link_ID,
                EventDate as smr_date,
                flag_smr,
                CASE
                    WHEN flag_smr = TRUE THEN 'positive_outcome'
                    WHEN flag_smr = FALSE THEN 'negative_outcome'
                END as outcome_type
            FROM {smr_events_view}
            WHERE was_smr = TRUE
                AND flag_smr IS NOT NULL  -- Only include SMRs with coded outcomes
        ),

        -- Prescriptions active at the time of SMR
        prescriptions_active_at_smr AS (
            SELECT
                s.FK_Patient_Link_ID,
                s.smr_date,
                s.outcome_type,
                p.medication_code,
                p.medication_end_date,
                p.is_repeat_medication,
                'active_ending' as change_type
            FROM smr_events_with_outcomes s
            INNER JOIN {gp_prescriptions} p
                ON s.FK_Patient_Link_ID = p.FK_Patient_Link_ID
                AND p.medication_start_date <= s.smr_date
                AND p.medication_end_date > s.smr_date  -- Active at SMR
            WHERE p.medication_end_date IS NOT NULL
        ),

        -- New prescriptions starting after SMR
        new_prescriptions AS (
            SELECT
                s.FK_Patient_Link_ID,
                s.smr_date,
                s.outcome_type,
                p.medication_code,
                p.medication_start_date as medication_end_date,  -- Use start as the "change date"
                p.is_repeat_medication,
                'new_starting' as change_type
            FROM smr_events_with_outcomes s
            INNER JOIN {gp_prescriptions} p
                ON s.FK_Patient_Link_ID = p.FK_Patient_Link_ID
                AND p.medication_start_date > s.smr_date  -- Starts after SMR
        ),

        -- Combine both types of changes
        all_changes AS (
            SELECT * FROM prescriptions_active_at_smr
            UNION ALL
            SELECT * FROM new_prescriptions
        ),

        -- For each SMR, find the FIRST (earliest) change only
        first_change_per_smr AS (
            SELECT
                FK_Patient_Link_ID,
                smr_date,
                outcome_type,
                medication_end_date as change_date,
                is_repeat_medication,
                change_type,
                ROW_NUMBER() OVER (
                    PARTITION BY FK_Patient_Link_ID, smr_date, outcome_type
                    ORDER BY medication_end_date
                ) as rn
            FROM all_changes
        )

        SELECT
            outcome_type,
            smr_date,
            change_date,
            is_repeat_medication,
            change_type,
            CASE
                WHEN is_repeat_medication = TRUE THEN 'repeat'
                WHEN is_repeat_medication = FALSE THEN 'non_repeat'
                ELSE 'unknown'
            END as medication_type,
            DATE_DIFF('day', smr_date, change_date) as days_to_change
        FROM first_change_per_smr
        WHERE rn = 1  -- Only the FIRST change per SMR
            AND change_date IS NOT NULL
            AND DATE_DIFF('day', smr_date, change_date) > 0  -- Positive time only
        ORDER BY outcome_type, medication_type, days_to_change
        """

        return sql

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Calculate summary statistics for FIRST change only approach.

        Uses same logic as main analysis but on biased data (first change only).
        """
        import statistics

        def compute_stats_for_category(df_subset, category_name):
            """Compute statistics for a specific medication category."""
            positive_days = df_subset.filter(
                pl.col("outcome_type") == "positive_outcome"
            )["days_to_change"].to_list()
            negative_days = df_subset.filter(
                pl.col("outcome_type") == "negative_outcome"
            )["days_to_change"].to_list()

            logger.info(f"\n{category_name} (FIRST CHANGE ONLY):")
            logger.info(f"  Positive outcome SMRs: {len(positive_days)} observations")
            logger.info(f"  Negative outcome SMRs: {len(negative_days)} observations")

            if len(positive_days) == 0 or len(negative_days) == 0:
                logger.warning(
                    f"  {category_name}: One or both groups have no observations"
                )
                return []

            # Calculate medians
            positive_median = statistics.median(positive_days)
            negative_median = statistics.median(negative_days)

            logger.info(f"  Positive median: {positive_median} days")
            logger.info(f"  Negative median: {negative_median} days")

            # Mann-Whitney U test
            u_statistic, p_value = stats.mannwhitneyu(
                positive_days, negative_days, alternative="two-sided"
            )
            logger.info(f"  Mann-Whitney U: {u_statistic}, p-value: {p_value}")

            return [
                {
                    "medication_category": category_name,
                    "group": "positive_outcome",
                    "n_observations": len(positive_days),
                    "median_days": round(positive_median, 1),
                    "test_statistic": None,
                    "p_value": None,
                },
                {
                    "medication_category": category_name,
                    "group": "negative_outcome",
                    "n_observations": len(negative_days),
                    "median_days": round(negative_median, 1),
                    "test_statistic": None,
                    "p_value": None,
                },
                {
                    "medication_category": category_name,
                    "group": "difference",
                    "n_observations": None,
                    "median_days": round(positive_median - negative_median, 1),
                    "test_statistic": None,
                    "p_value": None,
                },
                {
                    "medication_category": category_name,
                    "group": "mann_whitney_u",
                    "n_observations": None,
                    "median_days": None,
                    "test_statistic": round(u_statistic, 2),
                    "p_value": round(p_value, 6),
                },
            ]

        # Compute for all three categories
        all_rows = []

        # 1. Repeat medications only
        repeat_df = df.filter(pl.col("medication_type") == "repeat")
        all_rows.extend(compute_stats_for_category(repeat_df, "repeat_only"))

        # 2. Non-repeat medications only
        non_repeat_df = df.filter(pl.col("medication_type") == "non_repeat")
        all_rows.extend(compute_stats_for_category(non_repeat_df, "non_repeat_only"))

        # 3. All medications combined
        all_rows.extend(compute_stats_for_category(df, "all_medications"))

        return pl.DataFrame(all_rows)


class SMRTimeToMedicationChangeRawDataAnalysis(AnalysisBase):
    """
    Raw data for SMR time to medication change analysis (ALL CHANGES).

    IMPORTANT: Returns ONE ROW PER MEDICATION CHANGE (not one per SMR).
    If an SMR has 5 medications that change, you get 5 rows.

    Columns: outcome_type, medication_type, change_type, days_to_change

    This raw data can be used for:
    - Histogram visualization of medication change timing
    - Distribution analysis by outcome type
    - Verification of summary statistics
    """

    def __init__(self, processor):
        super().__init__(processor, name="smr_time_to_medication_change_raw_data")
        # Use a different output directory to avoid processor=None issue
        if processor is None:
            self.output_dir = Path("outputs/statistics")
            self.plots_dir = self.output_dir / "plots"

    def get_sql_statement(self) -> str:
        """Use same SQL as summary analysis."""
        # Reuse the SQL from the main analysis
        main_analysis = SMRTimeToMedicationChangeAnalysis(self.processor)
        return main_analysis.get_sql_statement()

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Return raw data (no dates/codes, just outcome_type, medication_type, change_type, and days_to_change).

        Each row represents a single medication change (not a single SMR).
        """
        # Remove dates and medication codes for privacy/simplicity
        return df.select(
            ["outcome_type", "medication_type", "change_type", "days_to_change"]
        ).sort(["medication_type", "outcome_type", "change_type", "days_to_change"])

    def plot(self) -> plt.Figure:
        """
        Create overlapping histogram showing distribution of time to medication change.

        Shows positive and negative outcomes overlaid for comparison.

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

        # Filter to just positive and negative outcomes (all medication types)
        plot_df = df.filter(
            (pl.col("outcome_type") == "positive_outcome")
            | (pl.col("outcome_type") == "negative_outcome")
        )

        # Convert to lists for plotting
        positive_days = plot_df.filter(pl.col("outcome_type") == "positive_outcome")[
            "days_to_change"
        ].to_list()
        negative_days = plot_df.filter(pl.col("outcome_type") == "negative_outcome")[
            "days_to_change"
        ].to_list()

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))

        # Create overlapping histograms with percentage on y-axis
        bins = range(0, 1500, 50)  # 50-day bins up to 1500 days

        # Calculate weights to convert counts to percentages
        weights_positive = [100.0 / len(positive_days)] * len(positive_days)
        weights_negative = [100.0 / len(negative_days)] * len(negative_days)

        ax.hist(
            positive_days,
            bins=bins,
            weights=weights_positive,
            alpha=0.6,
            color="#2ecc71",
            label="Positive Outcome SNOMED Code",
            edgecolor="black",
            linewidth=0.5,
        )
        ax.hist(
            negative_days,
            bins=bins,
            weights=weights_negative,
            alpha=0.6,
            color="#e74c3c",
            label="Negative Outcome SNOMED Code",
            edgecolor="black",
            linewidth=0.5,
        )

        # Labels and title
        ax.set_xlabel("Days to Medication Change", fontweight="bold")
        ax.set_ylabel("Percentage of Medication Changes (%)", fontweight="bold")
        ax.set_title(
            "Distribution of Time to Medication Change by SMR Outcome Type",
            fontweight="bold",
            pad=20,
        )
        ax.legend(loc="upper right", frameon=True, fancybox=True, shadow=True)
        ax.grid(axis="y", alpha=0.3, linestyle="--")

        # Set x-axis limit
        ax.set_xlim(0, 1500)

        plt.tight_layout()

        return fig


class SMRTimeToFirstMedicationChangeRawDataAnalysis(AnalysisBase):
    """
    Raw data for SMR time to FIRST medication change (BIASED APPROACH).

    Returns ONE ROW PER SMR (only the earliest change).

    Columns: outcome_type, medication_type, change_type, days_to_change

    Use this to compare against the "all changes" approach and illustrate
    the selection bias of only looking at first changes.
    """

    def __init__(self, processor):
        super().__init__(processor, name="smr_time_to_first_medication_change_raw_data")

    def get_sql_statement(self) -> str:
        """Use same SQL as first-change summary analysis."""
        # Reuse the SQL from the first-change analysis
        first_analysis = SMRTimeToFirstMedicationChangeAnalysis(self.processor)
        return first_analysis.get_sql_statement()

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Return raw data (no dates/codes, just outcome_type, medication_type, change_type, and days_to_change).

        Each row represents a single SMR (only the first change per SMR).
        """
        # Remove dates and medication codes for privacy/simplicity
        return df.select(
            ["outcome_type", "medication_type", "change_type", "days_to_change"]
        ).sort(["medication_type", "outcome_type", "change_type", "days_to_change"])
