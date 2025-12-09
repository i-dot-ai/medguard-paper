"""
Distribution of active medication counts per patient.

Similar to Lauren's request but with exact counts instead of bins.
Shows how many patients have 0, 1, 2, 3... N active medications.

Section: Paper narrative/descriptive statistics
Returns: Exact patient counts for each active medication count
"""

import polars as pl
import matplotlib.pyplot as plt

from medguard.analysis.base import AnalysisBase


# Reference date for "active medications"
REFERENCE_DATE = "2025-03-01"


SQL_ALL_PATIENTS = """
WITH patient_base AS (
    -- All valid patients
    SELECT
        pl.PK_Patient_Link_ID,
        p.Dob
    FROM {patient_link_view} pl
    LEFT JOIN {patient_view} p ON pl.PK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
        AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
),
active_medications AS (
    -- Count active medications for each patient on reference date
    SELECT
        pb.PK_Patient_Link_ID,
        COUNT(DISTINCT gp.medication_code) as active_medication_count
    FROM patient_base pb
    LEFT JOIN {gp_prescriptions} gp
        ON pb.PK_Patient_Link_ID = gp.FK_Patient_Link_ID
        AND gp.medication_start_date <= DATE '{reference_date}'
        AND (gp.medication_end_date IS NULL OR gp.medication_end_date >= DATE '{reference_date}')
    GROUP BY pb.PK_Patient_Link_ID
)
SELECT
    active_medication_count,
    COUNT(*) as patient_count
FROM active_medications
GROUP BY active_medication_count
ORDER BY active_medication_count
"""


SQL_ELDERLY = """
WITH patient_base AS (
    -- Patients age 65 and above
    SELECT
        pl.PK_Patient_Link_ID,
        p.Dob,
        DATE_DIFF('year', p.Dob, DATE '{reference_date}') as age
    FROM {patient_link_view} pl
    LEFT JOIN {patient_view} p ON pl.PK_Patient_Link_ID = p.FK_Patient_Link_ID
    WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
        AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
        AND p.Dob IS NOT NULL
        AND DATE_DIFF('year', p.Dob, DATE '{reference_date}') >= 65
),
active_medications AS (
    -- Count active medications for each elderly patient
    SELECT
        pb.PK_Patient_Link_ID,
        COUNT(DISTINCT gp.medication_code) as active_medication_count
    FROM patient_base pb
    LEFT JOIN {gp_prescriptions} gp
        ON pb.PK_Patient_Link_ID = gp.FK_Patient_Link_ID
        AND gp.medication_start_date <= DATE '{reference_date}'
        AND (gp.medication_end_date IS NULL OR gp.medication_end_date >= DATE '{reference_date}')
    GROUP BY pb.PK_Patient_Link_ID
)
SELECT
    active_medication_count,
    COUNT(*) as patient_count
FROM active_medications
GROUP BY active_medication_count
ORDER BY active_medication_count
"""


class ActiveMedicationsPerPatientDistributionAnalysis(AnalysisBase):
    """Distribution of active medication counts - all patients."""

    def __init__(self, processor):
        super().__init__(processor, name="active_medications_per_patient_distribution")

    def get_sql_statement(self) -> str:
        return SQL_ALL_PATIENTS.format(
            reference_date=REFERENCE_DATE,
            patient_link_view=self.processor.default_kwargs["patient_link_view"],
            patient_view=self.processor.default_kwargs["patient_view"],
            gp_prescriptions=self.processor.default_kwargs["gp_prescriptions"],
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # Add cumulative counts and percentiles
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

    def plot(self):
        """
        Create bar charts showing active medication distribution.

        Returns:
            List of (figure, suffix) tuples - one linear scale, one log scale
        """
        # Load the saved data
        df = self.load_df()

        # Set publication-quality style
        plt.style.use("seaborn-v0_8-paper")
        plt.rcParams["font.size"] = 11
        plt.rcParams["axes.labelsize"] = 12
        plt.rcParams["axes.titlesize"] = 13

        # Extract data
        medication_counts = df["active_medication_count"].to_list()
        percentages = df["pct_of_patients"].to_list()

        max_count = max(medication_counts)
        xlim = 20.5 if max_count > 20 else max_count + 0.5

        # Create LINEAR scale plot
        fig_linear, ax_linear = plt.subplots(figsize=(10, 6))
        ax_linear.bar(
            medication_counts,
            percentages,
            color="#3498db",
            alpha=0.8,
            edgecolor="black",
            linewidth=0.5,
        )
        ax_linear.set_xlabel("Number of Active Medications", fontweight="bold")
        ax_linear.set_ylabel("Percentage of Patients (%)", fontweight="bold")
        ax_linear.set_title(
            "Distribution of Active Medications Per Patient", fontweight="bold", pad=20
        )
        ax_linear.grid(axis="y", alpha=0.3, linestyle="--")
        ax_linear.set_xlim(-0.5, xlim)
        fig_linear.tight_layout()

        # Create LOG scale plot
        fig_log, ax_log = plt.subplots(figsize=(10, 6))
        ax_log.bar(
            medication_counts,
            percentages,
            color="#3498db",
            alpha=0.8,
            edgecolor="black",
            linewidth=0.5,
        )
        ax_log.set_xlabel("Number of Active Medications", fontweight="bold")
        ax_log.set_ylabel("Percentage of Patients (%) - Log Scale", fontweight="bold")
        ax_log.set_title(
            "Distribution of Active Medications Per Patient (Log Scale)",
            fontweight="bold",
            pad=20,
        )
        ax_log.grid(axis="y", alpha=0.3, linestyle="--", which="both")
        ax_log.set_yscale("log")
        ax_log.set_xlim(-0.5, xlim)
        fig_log.tight_layout()

        return [(fig_linear, "_linear"), (fig_log, "_log")]


class ActiveMedicationsPerElderlyPatientDistributionAnalysis(AnalysisBase):
    """Distribution of active medication counts - elderly patients (65+) only."""

    def __init__(self, processor):
        super().__init__(
            processor, name="active_medications_per_elderly_patient_distribution"
        )

    def get_sql_statement(self) -> str:
        return SQL_ELDERLY.format(
            reference_date=REFERENCE_DATE,
            patient_link_view=self.processor.default_kwargs["patient_link_view"],
            patient_view=self.processor.default_kwargs["patient_view"],
            gp_prescriptions=self.processor.default_kwargs["gp_prescriptions"],
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        # Add cumulative counts and percentiles
        total_patients = df["patient_count"].sum()
        return df.with_columns(
            [
                (pl.col("patient_count") / total_patients * 100)
                .round(2)
                .alias("pct_of_elderly"),
                pl.col("patient_count").cum_sum().alias("cumulative_patients"),
                (pl.col("patient_count").cum_sum() / total_patients * 100)
                .round(2)
                .alias("cumulative_pct"),
            ]
        )

    def plot(self):
        """
        Create bar charts showing active medication distribution for elderly patients.

        Returns:
            List of (figure, suffix) tuples - linear, log, and overlay with total population
        """
        # Load the saved data
        df_elderly = self.load_df()

        # Load the total population data for comparison
        from pathlib import Path

        pop_csv = (
            Path(self.output_dir) / "active_medications_per_patient_distribution.csv"
        )
        df_population = pl.read_csv(pop_csv)

        # Set publication-quality style
        plt.style.use("seaborn-v0_8-paper")
        plt.rcParams["font.size"] = 11
        plt.rcParams["axes.labelsize"] = 12
        plt.rcParams["axes.titlesize"] = 13

        # Extract data
        elderly_counts = df_elderly["active_medication_count"].to_list()
        elderly_pct = df_elderly["pct_of_elderly"].to_list()

        pop_counts = df_population["active_medication_count"].to_list()
        pop_pct = df_population["pct_of_patients"].to_list()

        max_count = max(max(elderly_counts), max(pop_counts))
        xlim = 20.5 if max_count > 20 else max_count + 0.5

        # Create LINEAR scale plot (elderly only)
        fig_linear, ax_linear = plt.subplots(figsize=(10, 6))
        ax_linear.bar(
            elderly_counts,
            elderly_pct,
            color="#e67e22",
            alpha=0.8,
            edgecolor="black",
            linewidth=0.5,
        )
        ax_linear.set_xlabel("Number of Active Medications", fontweight="bold")
        ax_linear.set_ylabel("Percentage of Elderly Patients (%)", fontweight="bold")
        ax_linear.set_title(
            "Distribution of Active Medications Per Elderly Patient (Age 65+)",
            fontweight="bold",
            pad=20,
        )
        ax_linear.grid(axis="y", alpha=0.3, linestyle="--")
        ax_linear.set_xlim(-0.5, xlim)
        fig_linear.tight_layout()

        # Create LOG scale plot (elderly only)
        fig_log, ax_log = plt.subplots(figsize=(10, 6))
        ax_log.bar(
            elderly_counts,
            elderly_pct,
            color="#e67e22",
            alpha=0.8,
            edgecolor="black",
            linewidth=0.5,
        )
        ax_log.set_xlabel("Number of Active Medications", fontweight="bold")
        ax_log.set_ylabel(
            "Percentage of Elderly Patients (%) - Log Scale", fontweight="bold"
        )
        ax_log.set_title(
            "Distribution of Active Medications Per Elderly Patient (Age 65+) - Log Scale",
            fontweight="bold",
            pad=20,
        )
        ax_log.grid(axis="y", alpha=0.3, linestyle="--", which="both")
        ax_log.set_yscale("log")
        ax_log.set_xlim(-0.5, xlim)
        fig_log.tight_layout()

        # Create OVERLAY plot - LINEAR scale (elderly + total population) - Focus on 5+ medications
        fig_overlay, ax_overlay = plt.subplots(figsize=(10, 6))

        # Plot total population first (behind)
        ax_overlay.bar(
            pop_counts,
            pop_pct,
            color="#3498db",
            alpha=0.6,
            edgecolor="black",
            linewidth=0.5,
            label="All Patients",
        )

        # Plot elderly on top
        ax_overlay.bar(
            elderly_counts,
            elderly_pct,
            color="#e67e22",
            alpha=0.6,
            edgecolor="black",
            linewidth=0.5,
            label="Elderly Patients (Age 65+)",
        )

        ax_overlay.set_xlabel("Number of Active Medications", fontweight="bold")
        ax_overlay.set_ylabel("Percentage of Patients (%)", fontweight="bold")
        ax_overlay.set_title(
            "Active Medications Distribution: All Patients vs Elderly (Age 65+)\n(5+ Medications)",
            fontweight="bold",
            pad=20,
        )
        ax_overlay.grid(axis="y", alpha=0.3, linestyle="--")
        ax_overlay.set_xlim(4.5, xlim)  # Start at 5 medications

        # Adjust y-axis to fit the 5+ medications data range
        # Find max percentage in the 5+ range
        max_pct_5plus = max(
            [
                pct
                for count, pct in zip(
                    pop_counts + elderly_counts, pop_pct + elderly_pct
                )
                if count >= 5
            ],
            default=5,
        )
        ax_overlay.set_ylim(0, max_pct_5plus * 1.15)  # Add 15% padding

        ax_overlay.legend(loc="upper right", frameon=True, fancybox=True, shadow=True)
        fig_overlay.tight_layout()

        # Create OVERLAY plot - LOG scale (elderly + total population)
        fig_overlay_log, ax_overlay_log = plt.subplots(figsize=(10, 6))

        # Plot total population first (behind)
        ax_overlay_log.bar(
            pop_counts,
            pop_pct,
            color="#3498db",
            alpha=0.6,
            edgecolor="black",
            linewidth=0.5,
            label="All Patients",
        )

        # Plot elderly on top
        ax_overlay_log.bar(
            elderly_counts,
            elderly_pct,
            color="#e67e22",
            alpha=0.6,
            edgecolor="black",
            linewidth=0.5,
            label="Elderly Patients (Age 65+)",
        )

        ax_overlay_log.set_xlabel("Number of Active Medications", fontweight="bold")
        ax_overlay_log.set_ylabel(
            "Percentage of Patients (%) - Log Scale", fontweight="bold"
        )
        ax_overlay_log.set_title(
            "Active Medications Distribution: All Patients vs Elderly (Age 65+) - Log Scale",
            fontweight="bold",
            pad=20,
        )
        ax_overlay_log.grid(axis="y", alpha=0.3, linestyle="--", which="both")
        ax_overlay_log.set_yscale("log")
        ax_overlay_log.set_xlim(-0.5, xlim)
        ax_overlay_log.legend(
            loc="upper right", frameon=True, fancybox=True, shadow=True
        )
        fig_overlay_log.tight_layout()

        return [
            (fig_linear, "_linear"),
            (fig_log, "_log"),
            (fig_overlay, "_comparison"),
            (fig_overlay_log, "_comparison_log"),
        ]
