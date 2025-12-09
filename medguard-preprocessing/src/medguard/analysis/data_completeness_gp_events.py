"""
Data completeness statistics for GP Events fields.

Section: 2.2 Data Source and Population
Returns: field_name, total_records, non_null_records, completion_rate_pct
"""

import polars as pl

from medguard.analysis.base import AnalysisBase

SQL = """
SELECT
    'GP Events - EventDate' as field_name,
    COUNT(*) as total_records,
    SUM(CASE WHEN EventDate IS NOT NULL THEN 1 ELSE 0 END) as non_null_records
FROM {gp_events_view}
WHERE (Deleted = 'N' OR Deleted IS NULL)

UNION ALL

SELECT
    'GP Events - SuppliedCode',
    COUNT(*) as total_records,
    SUM(CASE WHEN SuppliedCode IS NOT NULL THEN 1 ELSE 0 END) as non_null_records
FROM {gp_events_view}
WHERE (Deleted = 'N' OR Deleted IS NULL)

UNION ALL

SELECT
    'GP Events - Description',
    COUNT(*) as total_records,
    SUM(CASE WHEN description IS NOT NULL THEN 1 ELSE 0 END) as non_null_records
FROM {gp_events_enriched}
"""


class DataCompletenessGPEventsAnalysis(AnalysisBase):
    """Data completeness statistics for GP Events."""

    def __init__(self, processor):
        super().__init__(processor, name="data_completeness_gp_events")

    def get_sql_statement(self) -> str:
        return SQL.format(
            gp_events_view=self.processor.default_kwargs["gp_events_view"],
            gp_events_enriched=self.processor.default_kwargs["gp_events_enriched"],
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # Calculate completion rate percentage using polars
        return df.with_columns(
            ((pl.col("non_null_records") / pl.col("total_records")) * 100)
            .round(1)
            .alias("completion_rate_pct")
        )
