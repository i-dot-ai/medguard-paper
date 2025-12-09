"""
Date range of available GP Events records with percentiles.

Section: 2.2 Data Source and Population
Returns: earliest_event_date, latest_event_date, total_years, total_events,
         and percentiles (0.1, 1, 5, 25, 50, 75, 95, 99, 99.9) to account for noise
"""

import polars as pl

from medguard.analysis.base import AnalysisBase

SQL = """
SELECT
    MIN(EventDate) as min_date,
    MAX(EventDate) as max_date,
    COUNT(*) as total_events,

    -- Percentiles to account for outliers/noise
    APPROX_QUANTILE(EventDate, 0.001) as p0_1_date,
    APPROX_QUANTILE(EventDate, 0.01) as p1_date,
    APPROX_QUANTILE(EventDate, 0.05) as p5_date,
    APPROX_QUANTILE(EventDate, 0.25) as p25_date,
    APPROX_QUANTILE(EventDate, 0.50) as p50_date,
    APPROX_QUANTILE(EventDate, 0.75) as p75_date,
    APPROX_QUANTILE(EventDate, 0.95) as p95_date,
    APPROX_QUANTILE(EventDate, 0.99) as p99_date,
    APPROX_QUANTILE(EventDate, 0.999) as p99_9_date
FROM {gp_events_view}
WHERE (Deleted = 'N' OR Deleted IS NULL)
    AND EventDate IS NOT NULL
"""


class GPEventsDateRangeAnalysis(AnalysisBase):
    """Date range statistics for GP Events with percentiles."""

    def __init__(self, processor):
        super().__init__(processor, name="gp_events_date_range")

    def get_sql_statement(self) -> str:
        return SQL.format(
            gp_events_view=self.processor.default_kwargs["gp_events_view"]
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # Calculate date ranges for different percentile brackets
        return df.with_columns(
            [
                # Overall range
                (pl.col("max_date") - pl.col("min_date"))
                .dt.total_days()
                .alias("total_days_min_max"),
                ((pl.col("max_date") - pl.col("min_date")).dt.total_days() / 365.25)
                .round(1)
                .alias("total_years_min_max"),
                # Robust range (5th to 95th percentile - excludes 10% outliers)
                (pl.col("p95_date") - pl.col("p5_date"))
                .dt.total_days()
                .alias("total_days_p5_p95"),
                ((pl.col("p95_date") - pl.col("p5_date")).dt.total_days() / 365.25)
                .round(1)
                .alias("total_years_p5_p95"),
                # IQR range (25th to 75th percentile)
                (pl.col("p75_date") - pl.col("p25_date"))
                .dt.total_days()
                .alias("total_days_iqr"),
                ((pl.col("p75_date") - pl.col("p25_date")).dt.total_days() / 365.25)
                .round(1)
                .alias("total_years_iqr"),
            ]
        )
