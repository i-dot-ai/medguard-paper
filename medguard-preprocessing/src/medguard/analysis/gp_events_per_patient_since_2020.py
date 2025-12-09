"""
Mean/median number of GP events per patient (since 2020).

Section: 2.2 Data Source and Population
Returns: patients_with_events_since_2020, mean_events_per_patient, median_events_per_patient,
         min_events, max_events, stddev_events
"""

import polars as pl

from medguard.analysis.base import AnalysisBase

SQL = """
WITH patient_event_counts_since_2020 AS (
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
    COUNT(*) as patients_with_events_since_2020,
    AVG(event_count) as mean_events_per_patient,
    MEDIAN(event_count) as median_events_per_patient,
    MIN(event_count) as min_events,
    MAX(event_count) as max_events,
    STDDEV(event_count) as stddev_events
FROM patient_event_counts_since_2020
"""


class GPEventsPerPatientSince2020Analysis(AnalysisBase):
    """GP events per patient statistics (since 2020)."""

    def __init__(self, processor):
        super().__init__(processor, name="gp_events_per_patient_since_2020")

    def get_sql_statement(self) -> str:
        return SQL.format(
            gp_events_view=self.processor.default_kwargs["gp_events_view"]
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # Round numeric columns to 1 decimal place
        return df.with_columns(
            [
                pl.col("mean_events_per_patient").round(1),
                pl.col("median_events_per_patient").round(1),
                pl.col("stddev_events").round(1),
            ]
        )
