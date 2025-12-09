"""
Index of Multiple Deprivation (IMD) distribution analysis.

Section: 2.2 Data Source and Population
Returns: IMD score distribution for the dataset
         - Histogram of IMD scores
         - Summary statistics for comparison with national averages
"""

import polars as pl
import matplotlib.pyplot as plt

from medguard.analysis.base import AnalysisBase


SQL_IMD_HISTOGRAM = """
SELECT
    IMD_Score,
    COUNT(*) as patient_count
FROM {patient_link_view} pl
LEFT JOIN {patient_view} p ON pl.PK_Patient_Link_ID = p.FK_Patient_Link_ID
WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
    AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
    AND p.IMD_Score IS NOT NULL
GROUP BY IMD_Score
ORDER BY IMD_Score
"""


SQL_IMD_SUMMARY = """
WITH patient_imd AS (
    SELECT
        p.IMD_Score
    FROM {patient_link_view} pl
    LEFT JOIN {patient_view} p ON pl.PK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
        AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
        AND p.IMD_Score IS NOT NULL
)
SELECT
    COUNT(*) as total_patients_with_imd,
    AVG(IMD_Score) as mean_imd,
    STDDEV(IMD_Score) as stddev_imd,
    MIN(IMD_Score) as min_imd,
    MAX(IMD_Score) as max_imd,
    MEDIAN(IMD_Score) as median_imd,
    APPROX_QUANTILE(IMD_Score, 0.25) as q1_imd,
    APPROX_QUANTILE(IMD_Score, 0.75) as q3_imd
FROM patient_imd
"""


SQL_IMD_DECILES = """
WITH patient_imd AS (
    SELECT
        p.IMD_Score,
        -- UK IMD deciles: 1 = most deprived, 10 = least deprived
        -- IMD_Score is a rank from 1-32844 (number of LSOAs in England)
        -- Convert to deciles based on rank position
        CASE
            WHEN p.IMD_Score < 0 THEN '0 (Invalid)'
            WHEN p.IMD_Score <= 3284 THEN '1 (Most deprived)'
            WHEN p.IMD_Score <= 6568 THEN '2'
            WHEN p.IMD_Score <= 9852 THEN '3'
            WHEN p.IMD_Score <= 13136 THEN '4'
            WHEN p.IMD_Score <= 16420 THEN '5'
            WHEN p.IMD_Score <= 19704 THEN '6'
            WHEN p.IMD_Score <= 22988 THEN '7'
            WHEN p.IMD_Score <= 26272 THEN '8'
            WHEN p.IMD_Score <= 29556 THEN '9'
            ELSE '10 (Least deprived)'
        END as imd_decile
    FROM {patient_link_view} pl
    LEFT JOIN {patient_view} p ON pl.PK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
        AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
        AND p.IMD_Score IS NOT NULL
)
SELECT
    imd_decile,
    COUNT(*) as patient_count
FROM patient_imd
GROUP BY imd_decile
ORDER BY imd_decile
"""


SQL_IMD_COMPLETENESS = """
SELECT
    COUNT(*) as total_patients,
    SUM(CASE WHEN p.IMD_Score IS NOT NULL THEN 1 ELSE 0 END) as patients_with_imd,
    SUM(CASE WHEN p.IMD_Score IS NULL THEN 1 ELSE 0 END) as patients_without_imd,
    ROUND(100.0 * SUM(CASE WHEN p.IMD_Score IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) as imd_completion_rate_pct
FROM {patient_link_view} pl
LEFT JOIN {patient_view} p ON pl.PK_Patient_Link_ID = p.FK_Patient_Link_ID
WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
    AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
"""


class IMDHistogramAnalysis(AnalysisBase):
    """Raw histogram of IMD scores (exact counts per score)."""

    def __init__(self, processor):
        super().__init__(processor, name="imd_histogram")

    def get_sql_statement(self) -> str:
        return SQL_IMD_HISTOGRAM.format(
            patient_link_view=self.processor.default_kwargs["patient_link_view"],
            patient_view=self.processor.default_kwargs["patient_view"],
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # Add cumulative and percentage columns
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


class IMDSummaryStatisticsAnalysis(AnalysisBase):
    """Summary statistics for IMD scores."""

    def __init__(self, processor):
        super().__init__(processor, name="imd_summary_statistics")

    def get_sql_statement(self) -> str:
        return SQL_IMD_SUMMARY.format(
            patient_link_view=self.processor.default_kwargs["patient_link_view"],
            patient_view=self.processor.default_kwargs["patient_view"],
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # Round all numeric columns
        return df.with_columns(
            [
                pl.col("mean_imd").round(2),
                pl.col("stddev_imd").round(2),
                pl.col("median_imd").round(1),
                pl.col("q1_imd").round(1),
                pl.col("q3_imd").round(1),
            ]
        )


class IMDDecilesAnalysis(AnalysisBase):
    """IMD distribution by decile (1=most deprived, 10=least deprived)."""

    def __init__(self, processor):
        super().__init__(processor, name="imd_deciles")

    def get_sql_statement(self) -> str:
        return SQL_IMD_DECILES.format(
            patient_link_view=self.processor.default_kwargs["patient_link_view"],
            patient_view=self.processor.default_kwargs["patient_view"],
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # Add percentage column
        total_patients = df["patient_count"].sum()
        return df.with_columns(
            [
                (pl.col("patient_count") / total_patients * 100)
                .round(1)
                .alias("pct_of_patients"),
            ]
        )

    def plot(self) -> plt.Figure:
        """
        Create bar chart showing IMD decile distribution.

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

        # Create ordered decile labels (0-10)
        # Need to properly order the deciles since SQL returns them as strings
        decile_order = [
            "0 (Invalid)",
            "1 (Most deprived)",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10 (Least deprived)",
        ]

        # Create a mapping for sorting
        decile_to_num = {decile: i for i, decile in enumerate(decile_order)}

        # Sort dataframe by decile order
        df = df.with_columns(
            [
                pl.col("imd_decile")
                .map_elements(lambda x: decile_to_num.get(x, 99), return_dtype=pl.Int64)
                .alias("sort_order")
            ]
        ).sort("sort_order")

        # Extract data
        deciles = df["imd_decile"].to_list()
        percentages = df["pct_of_patients"].to_list()
        counts = df["patient_count"].to_list()

        # Create bar chart
        fig, ax = plt.subplots(figsize=(10, 6))

        # Use gradient from red (deprived) to green (affluent)
        # Generate enough colors for all deciles (up to 11 if invalid exists)
        num_colors = max(len(deciles), 11)
        color_step = 256 // num_colors
        colors_list = plt.cm.RdYlGn(range(0, 256, color_step))

        # Assign colors based on decile labels (gray for invalid, gradient for 1-10)
        colors = []
        for decile in deciles:
            if "Invalid" in decile:
                colors.append("#808080")  # Gray for invalid
            elif "Most" in decile:
                colors.append(colors_list[0])  # First color (red)
            elif "Least" in decile:
                colors.append(colors_list[-1])  # Last color (green)
            else:
                # Extract decile number and map to color
                decile_num = int(decile)
                colors.append(colors_list[decile_num])

        bars = ax.bar(
            range(len(deciles)),
            percentages,
            color=colors,
            alpha=0.8,
            edgecolor="black",
            linewidth=0.5,
        )

        # Add value labels on bars (only if percentage > 0.5%)
        for i, (bar, pct, count) in enumerate(zip(bars, percentages, counts)):
            height = bar.get_height()
            if pct >= 0.5:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    f"{pct:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

        # Clean up decile labels for x-axis
        clean_labels = []
        for decile in deciles:
            if "Invalid" in decile:
                clean_labels.append("0\n(Invalid)")
            elif "Most" in decile:
                clean_labels.append("1\n(Most\ndeprived)")
            elif "Least" in decile:
                clean_labels.append("10\n(Least\ndeprived)")
            else:
                clean_labels.append(decile)

        # Labels and title
        ax.set_xticks(range(len(deciles)))
        ax.set_xticklabels(clean_labels, fontsize=10)
        ax.set_xlabel("IMD Decile", fontweight="bold")
        ax.set_ylabel("Percentage of Patients (%)", fontweight="bold")
        ax.set_title(
            "Patient Distribution by Index of Multiple Deprivation (IMD) Decile",
            fontweight="bold",
            pad=20,
        )
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.set_ylim(0, max(percentages) * 1.15)  # Add padding for labels

        plt.tight_layout()

        return fig


class IMDCompletenessAnalysis(AnalysisBase):
    """Data completeness for IMD scores."""

    def __init__(self, processor):
        super().__init__(processor, name="imd_completeness")

    def get_sql_statement(self) -> str:
        return SQL_IMD_COMPLETENESS.format(
            patient_link_view=self.processor.default_kwargs["patient_link_view"],
            patient_view=self.processor.default_kwargs["patient_view"],
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # No transformation needed
        return df


class IMDPercentilesPlotAnalysis(AnalysisBase):
    """IMD distribution by percentile (calculated from histogram for plotting only)."""

    def __init__(self, processor):
        super().__init__(processor, name="imd_percentiles_plot")

    def get_sql_statement(self) -> str:
        # Not used - we load from histogram
        return ""

    def execute(self) -> pl.DataFrame:
        # This analysis doesn't save data, only creates plots
        return pl.DataFrame()

    def plot(self) -> plt.Figure:
        """
        Create bar chart showing IMD percentile distribution.
        Calculates percentiles from the imd_histogram.csv file.

        Returns:
            Matplotlib figure
        """
        # Load the histogram data
        from pathlib import Path

        histogram_path = Path(self.output_dir) / "imd_histogram.csv"
        df = pl.read_csv(histogram_path)

        # Filter out invalid scores (< 0)
        df_valid = df.filter(pl.col("IMD_Score") >= 0)

        # Calculate percentiles based on rank (IMD_Score is the rank 1-32844)
        # Each percentile represents 328.44 LSOAs
        df_valid = df_valid.with_columns(
            [
                ((pl.col("IMD_Score") - 1) / 328.44)
                .floor()
                .cast(pl.Int64)
                .alias("percentile_raw")
            ]
        )

        # Cap at percentile 99 (0-99 for 100 percentiles)
        df_valid = df_valid.with_columns(
            [
                pl.when(pl.col("percentile_raw") > 99)
                .then(pl.lit(99))
                .otherwise(pl.col("percentile_raw"))
                .alias("imd_percentile")
            ]
        )

        # Group by percentile and sum patient counts
        percentile_df = (
            df_valid.group_by("imd_percentile")
            .agg([pl.col("patient_count").sum().alias("patient_count")])
            .sort("imd_percentile")
        )

        # Calculate percentages
        total = percentile_df["patient_count"].sum()
        percentile_df = percentile_df.with_columns(
            [(pl.col("patient_count") / total * 100).round(2).alias("pct_of_patients")]
        )

        # Set publication-quality style
        plt.style.use("seaborn-v0_8-paper")
        plt.rcParams["font.size"] = 11
        plt.rcParams["axes.labelsize"] = 12
        plt.rcParams["axes.titlesize"] = 13

        # Extract data
        percentiles = percentile_df["imd_percentile"].to_list()
        percentages = percentile_df["pct_of_patients"].to_list()

        # Create bar chart
        fig, ax = plt.subplots(figsize=(12, 6))

        # Use gradient from red (deprived) to green (affluent)
        colors = plt.cm.RdYlGn([i / 99 for i in range(100)])

        # Map percentiles to colors
        bar_colors = [colors[p] for p in percentiles]

        bars = ax.bar(
            percentiles,
            percentages,
            color=bar_colors,
            alpha=0.8,
            edgecolor="none",
            width=1.0,
        )

        # Labels and title
        ax.set_xlabel(
            "IMD Percentile (0 = Most Deprived, 99 = Least Deprived)", fontweight="bold"
        )
        ax.set_ylabel("Percentage of Patients (%)", fontweight="bold")
        ax.set_title(
            "Patient Distribution by Index of Multiple Deprivation (IMD) Percentile",
            fontweight="bold",
            pad=20,
        )
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.set_xlim(-1, 100)

        # Add vertical lines at key percentiles
        for p in [0, 25, 50, 75, 99]:
            ax.axvline(x=p, color="gray", linestyle="--", alpha=0.3, linewidth=1)

        plt.tight_layout()

        return fig
