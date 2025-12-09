"""
Elderly patients (65+) and their active medication counts.

For Lauren's narrative - showing polypharmacy in elderly population.

Section: Paper narrative/introduction
Returns: Total patients, patients 65+, and medication count bins for 65+ cohort

NOTE: Current data shows only ~16% of elderly patients (13,257 out of 83,284) appear in
medication bins. This suggests ~84% of elderly patients have no prescription data in
gp_prescriptions table. This should be investigated to understand if it's:
- Expected behavior (many elderly patients without GP prescriptions in the data)
- Data quality issue
- SQL query issue missing patients with 0 medications
Investigation needed to determine appropriate handling for visualization and interpretation.
"""

import polars as pl
import matplotlib.pyplot as plt

from medguard.analysis.base import AnalysisBase


# Reference date for "active medications" and age calculation
REFERENCE_DATE = "2025-03-01"


SQL = """
WITH patient_ages AS (
    -- Calculate age as of reference date
    SELECT
        pl.PK_Patient_Link_ID,
        p.Dob,
        DATE_DIFF('year', p.Dob, DATE '{reference_date}') as age
    FROM {patient_link_view} pl
    LEFT JOIN {patient_view} p ON pl.PK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
        AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
        AND p.Dob IS NOT NULL
),
elderly_patients AS (
    -- Patients age 65 and above
    SELECT *
    FROM patient_ages
    WHERE age >= 65
),
active_medications_elderly AS (
    -- Count active medications for each elderly patient on reference date
    SELECT
        ep.PK_Patient_Link_ID,
        ep.age,
        COUNT(DISTINCT gp.medication_code) as active_medication_count
    FROM elderly_patients ep
    LEFT JOIN {gp_prescriptions} gp
        ON ep.PK_Patient_Link_ID = gp.FK_Patient_Link_ID
        AND gp.medication_start_date <= DATE '{reference_date}'
        AND (gp.medication_end_date IS NULL OR gp.medication_end_date >= DATE '{reference_date}')
    GROUP BY ep.PK_Patient_Link_ID, ep.age
),
medication_bins AS (
    -- Bin medication counts: ≤5, 6-8, ≥9
    SELECT
        PK_Patient_Link_ID,
        age,
        active_medication_count,
        CASE
            WHEN active_medication_count <= 5 THEN '0-5 medicines'
            WHEN active_medication_count BETWEEN 6 AND 8 THEN '6-8 medicines'
            WHEN active_medication_count >= 9 THEN '9+ medicines'
        END as medication_bin
    FROM active_medications_elderly
)
SELECT
    -- Summary statistics
    (SELECT COUNT(*) FROM patient_ages) as total_patients,
    (SELECT COUNT(*) FROM elderly_patients) as patients_65_and_above,

    -- Medication bins for elderly
    SUM(CASE WHEN medication_bin = '0-5 medicines' THEN 1 ELSE 0 END) as elderly_0_to_5_medicines,
    SUM(CASE WHEN medication_bin = '6-8 medicines' THEN 1 ELSE 0 END) as elderly_6_to_8_medicines,
    SUM(CASE WHEN medication_bin = '9+ medicines' THEN 1 ELSE 0 END) as elderly_9_plus_medicines
FROM medication_bins
"""


SQL_DETAILED = """
WITH patient_ages AS (
    -- Calculate age as of reference date
    SELECT
        pl.PK_Patient_Link_ID,
        p.Dob,
        DATE_DIFF('year', p.Dob, DATE '{reference_date}') as age
    FROM {patient_link_view} pl
    LEFT JOIN {patient_view} p ON pl.PK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
        AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
        AND p.Dob IS NOT NULL
),
elderly_patients AS (
    -- Patients age 65 and above
    SELECT *
    FROM patient_ages
    WHERE age >= 65
),
active_medications_elderly AS (
    -- Count active medications for each elderly patient
    SELECT
        ep.PK_Patient_Link_ID,
        ep.age,
        COUNT(DISTINCT gp.medication_code) as active_medication_count
    FROM elderly_patients ep
    LEFT JOIN {gp_prescriptions} gp
        ON ep.PK_Patient_Link_ID = gp.FK_Patient_Link_ID
        AND gp.medication_start_date <= DATE '{reference_date}'
        AND (gp.medication_end_date IS NULL OR gp.medication_end_date >= DATE '{reference_date}')
    GROUP BY ep.PK_Patient_Link_ID, ep.age
)
SELECT
    CASE
        WHEN active_medication_count <= 5 THEN '0-5 medicines'
        WHEN active_medication_count BETWEEN 6 AND 8 THEN '6-8 medicines'
        WHEN active_medication_count >= 9 THEN '9+ medicines'
    END as medication_bin,
    COUNT(*) as patient_count
FROM active_medications_elderly
GROUP BY medication_bin
ORDER BY
    CASE
        WHEN medication_bin = '0-5 medicines' THEN 1
        WHEN medication_bin = '6-8 medicines' THEN 2
        WHEN medication_bin = '9+ medicines' THEN 3
    END
"""


class ElderlyPatientsMedicationCountsAnalysis(AnalysisBase):
    """Summary: Elderly patients (65+) and medication count bins."""

    def __init__(self, processor):
        super().__init__(processor, name="elderly_patients_medication_counts")

    def get_sql_statement(self) -> str:
        return SQL.format(
            reference_date=REFERENCE_DATE,
            patient_link_view=self.processor.default_kwargs["patient_link_view"],
            patient_view=self.processor.default_kwargs["patient_view"],
            gp_prescriptions=self.processor.default_kwargs["gp_prescriptions"],
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # Add percentages for elderly medication bins
        total_elderly = df["patients_65_and_above"][0]

        return df.with_columns(
            [
                (pl.col("elderly_0_to_5_medicines") / total_elderly * 100)
                .round(1)
                .alias("elderly_0_to_5_medicines_pct"),
                (pl.col("elderly_6_to_8_medicines") / total_elderly * 100)
                .round(1)
                .alias("elderly_6_to_8_medicines_pct"),
                (pl.col("elderly_9_plus_medicines") / total_elderly * 100)
                .round(1)
                .alias("elderly_9_plus_medicines_pct"),
                (pl.col("patients_65_and_above") / pl.col("total_patients") * 100)
                .round(1)
                .alias("pct_patients_65_and_above"),
            ]
        )

    def plot(self) -> plt.Figure:
        """
        Create vertical bar chart showing elderly patients by medication categories.

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
        categories = ["0-5\nMedications", "6-8\nMedications", "9+\nMedications"]
        percentages = [
            df["elderly_0_to_5_medicines_pct"][0],
            df["elderly_6_to_8_medicines_pct"][0],
            df["elderly_9_plus_medicines_pct"][0],
        ]
        counts = [
            df["elderly_0_to_5_medicines"][0],
            df["elderly_6_to_8_medicines"][0],
            df["elderly_9_plus_medicines"][0],
        ]

        # Create vertical bar chart
        fig, ax = plt.subplots(figsize=(8, 6))

        colors = ["#27ae60", "#f39c12", "#e74c3c"]  # Green, Orange, Red
        bars = ax.bar(
            categories,
            percentages,
            color=colors,
            alpha=0.8,
            edgecolor="black",
            linewidth=1,
        )

        # Add value labels on top of bars
        for i, (bar, pct, count) in enumerate(zip(bars, percentages, counts)):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{pct}%\n(n={int(count):,})",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        # Labels and title
        ax.set_xlabel("Medication Category", fontweight="bold")
        ax.set_ylabel("Percentage of Elderly Patients (%)", fontweight="bold")
        ax.set_title(
            "Elderly Patients (Age 65+) by Active Medication Count",
            fontweight="bold",
            pad=20,
        )
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.set_ylim(0, max(percentages) * 1.25)  # Add padding for labels

        plt.tight_layout()

        return fig


class ElderlyPatientsMedicationCountsDetailedAnalysis(AnalysisBase):
    """Detailed breakdown: Elderly patients by medication count bins."""

    def __init__(self, processor):
        super().__init__(processor, name="elderly_patients_medication_counts_detailed")

    def get_sql_statement(self) -> str:
        return SQL_DETAILED.format(
            reference_date=REFERENCE_DATE,
            patient_link_view=self.processor.default_kwargs["patient_link_view"],
            patient_view=self.processor.default_kwargs["patient_view"],
            gp_prescriptions=self.processor.default_kwargs["gp_prescriptions"],
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # Add percentages
        total = df["patient_count"].sum()

        return df.with_columns(
            [
                (pl.col("patient_count") / total * 100)
                .round(1)
                .alias("pct_of_elderly"),
            ]
        )
