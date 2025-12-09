"""
Total patients in dataset.

Section: 2.2 Data Source and Population
Returns: Single row with total_patients count
"""

import polars as pl
from medguard.analysis.base import AnalysisBase


SQL = """
SELECT
    COUNT(*) as total_patients
FROM {patient_link_view}
WHERE (Merged != 'Y' OR Merged IS NULL)
    AND (Deleted != 'Y' OR Deleted IS NULL)
"""


class TotalPatientsAnalysis(AnalysisBase):
    """Total patients in the dataset."""

    def __init__(self, processor):
        super().__init__(processor, name="total_patients")

    def get_sql_statement(self) -> str:
        return SQL.format(
            patient_link_view=self.processor.default_kwargs["patient_link_view"]
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # No transformation needed
        return df
