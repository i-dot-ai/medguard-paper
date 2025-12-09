import polars as pl
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional
import json
from datetime import date

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PolarsEDAAnalyzer:
    """
    EDA analyzer using Polars for much cleaner and more intuitive data manipulation.
    Reads parquet files directly with lazy evaluation for efficiency.
    """

    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.extract_path = self.data_path / "PopHealth" / "Medguard" / "Extract"
        self.figures = []
        self.analysis_results = {}

        # Lazy dataframe cache
        self._lazy_frames = {}

        logger.info(f"Polars EDA Analyzer initialized with data path: {self.data_path}")
        self._discover_tables()

    def _discover_tables(self):
        """Discover available parquet files and create lazy frame references"""

        if not self.extract_path.exists():
            logger.error(f"Extract path not found: {self.extract_path}")
            return

        table_count = 0
        for table_dir in self.extract_path.iterdir():
            if table_dir.is_dir():
                v1_path = table_dir / "v1_0"
                if v1_path.exists():
                    parquet_files = list(v1_path.glob("*.parquet"))
                    if parquet_files:
                        # Create lazy frame reference
                        pattern = str(v1_path / "*.parquet")
                        table_name = table_dir.name
                        self._lazy_frames[table_name] = pattern
                        table_count += 1
                        logger.info(f"Found table: {table_name}")

        logger.info(f"Discovered {table_count} tables")

    def get_lazy_frame(self, table_name: str) -> pl.LazyFrame:
        """Get a lazy frame for a specific table"""

        if table_name not in self._lazy_frames:
            raise ValueError(
                f"Table {table_name} not found. Available: {list(self._lazy_frames.keys())}"
            )

        pattern = self._lazy_frames[table_name]
        return pl.scan_parquet(pattern)

    def get_patient_data(self, active_only: bool = True) -> pl.LazyFrame:
        """Get patient data with optional filtering for active patients"""

        patients = self.get_lazy_frame("SharedCare.Patient")

        if active_only:
            patients = patients.filter(
                (pl.col("Deleted") != "Y") | pl.col("Deleted").is_null()
            )

        return patients

    # ============================================================================
    # DEMOGRAPHIC ANALYSIS
    # ============================================================================

    def analyze_demographics_completion(self) -> go.Figure:
        """Analyze completion rates for key demographic fields using Polars"""

        logger.info("Analyzing demographic completion rates...")

        patients = self.get_patient_data(active_only=True)

        # Key demographic fields to analyze
        demographic_fields = [
            "Dob",
            "Sex",
            "GPPracticeCode",
            "GPPracticeName",
            "GPPostCode",
            "MaritalStatus",
            "EthnicOrigin",
            "LSOA_Code",
            "IMD_Score",
            "FrailtyScore",
            "QOFRegisters",
            "MortalityRiskScore",
            "SocialCareFlag",
        ]

        # Calculate completion rates
        completion_stats = []
        total_patients = patients.select(pl.count()).collect().item()

        for field in demographic_fields:
            completed = (
                patients.filter(
                    pl.col(field).is_not_null()
                    & (pl.col(field).cast(pl.Utf8).str.strip_chars() != "")
                )
                .select(pl.count())
                .collect()
                .item()
            )

            completion_rate = (completed / total_patients) * 100

            completion_stats.append(
                {
                    "field_name": field,
                    "completion_rate": completion_rate,
                    "completed_patients": completed,
                    "total_patients": total_patients,
                }
            )

        # Convert to DataFrame for plotting
        df = pd.DataFrame(completion_stats).sort_values(
            "completion_rate", ascending=True
        )

        # Store results
        self.analysis_results["demographics_completion"] = df

        # Create visualization
        fig = px.bar(
            df,
            x="completion_rate",
            y="field_name",
            orientation="h",
            title="Demographic Field Completion Rates",
            labels={"completion_rate": "Completion Rate (%)", "field_name": "Field"},
            text="completion_rate",
        )

        fig.update_traces(texttemplate="%{text:.1f}%", textposition="inside")
        fig.update_layout(height=500)

        self.figures.append(("demographics_completion", fig))
        logger.info(f"✓ Demographics analysis complete")
        return fig

    def analyze_age_sex_distribution(self) -> go.Figure:
        """Create population pyramid using Polars with percentages instead of counts"""

        logger.info("Analyzing age/sex distribution...")

        patients = self.get_patient_data(active_only=True)

        # Calculate age and create age groups
        age_sex_data = (
            patients.filter(pl.col("Dob").is_not_null())
            .with_columns(
                [
                    # Calculate age
                    (
                        (pl.date(2025, 7, 23) - pl.col("Dob")).dt.total_days() / 365.25
                    ).alias("age"),
                    pl.col("Sex").fill_null("Unknown").alias("sex_clean"),
                ]
            )
            .with_columns(
                [
                    # Create age groups
                    pl.when(pl.col("age") < 0)
                    .then(pl.lit("Invalid"))
                    .when(pl.col("age") > 120)
                    .then(pl.lit("Invalid"))
                    .when(pl.col("age") < 5)
                    .then(pl.lit("0-4"))
                    .when(pl.col("age") < 10)
                    .then(pl.lit("5-9"))
                    .when(pl.col("age") < 15)
                    .then(pl.lit("10-14"))
                    .when(pl.col("age") < 20)
                    .then(pl.lit("15-19"))
                    .when(pl.col("age") < 25)
                    .then(pl.lit("20-24"))
                    .when(pl.col("age") < 30)
                    .then(pl.lit("25-29"))
                    .when(pl.col("age") < 35)
                    .then(pl.lit("30-34"))
                    .when(pl.col("age") < 40)
                    .then(pl.lit("35-39"))
                    .when(pl.col("age") < 45)
                    .then(pl.lit("40-44"))
                    .when(pl.col("age") < 50)
                    .then(pl.lit("45-49"))
                    .when(pl.col("age") < 55)
                    .then(pl.lit("50-54"))
                    .when(pl.col("age") < 60)
                    .then(pl.lit("55-59"))
                    .when(pl.col("age") < 65)
                    .then(pl.lit("60-64"))
                    .when(pl.col("age") < 70)
                    .then(pl.lit("65-69"))
                    .when(pl.col("age") < 75)
                    .then(pl.lit("70-74"))
                    .when(pl.col("age") < 80)
                    .then(pl.lit("75-79"))
                    .when(pl.col("age") < 85)
                    .then(pl.lit("80-84"))
                    .when(pl.col("age") < 90)
                    .then(pl.lit("85-89"))
                    .otherwise(pl.lit("90+"))
                    .alias("age_group")
                ]
            )
            .group_by(["age_group", "sex_clean"])
            .agg(pl.count().alias("count"))
            .collect()
            .to_pandas()
        )

        # Calculate total population and convert to percentages
        total_population = age_sex_data["count"].sum()
        age_sex_data["percentage"] = (age_sex_data["count"] / total_population) * 100

        # Store results
        self.analysis_results["age_sex_distribution"] = age_sex_data

        # Create population pyramid
        fig = go.Figure()

        age_order = [
            "0-4",
            "5-9",
            "10-14",
            "15-19",
            "20-24",
            "25-29",
            "30-34",
            "35-39",
            "40-44",
            "45-49",
            "50-54",
            "55-59",
            "60-64",
            "65-69",
            "70-74",
            "75-79",
            "80-84",
            "85-89",
            "90+",
            "Invalid",
        ]

        for sex in ["M", "F", "Unknown"]:
            sex_data = age_sex_data[age_sex_data["sex_clean"] == sex]
            if not sex_data.empty:
                # Sort by age group
                sex_data = (
                    sex_data.set_index("age_group").reindex(age_order).reset_index()
                )
                sex_data = sex_data.dropna(subset=["percentage"])

                multiplier = -1 if sex == "M" else 1
                color = "blue" if sex == "M" else "pink" if sex == "F" else "gray"

                fig.add_trace(
                    go.Bar(
                        name=f"{'Male' if sex == 'M' else 'Female' if sex == 'F' else 'Unknown'}",
                        y=sex_data["age_group"],
                        x=sex_data["percentage"] * multiplier,
                        orientation="h",
                        marker_color=color,
                        text=[f"{pct:.1f}%" for pct in sex_data["percentage"]],
                        textposition="inside",
                        hovertemplate=f"%{{y}}<br>Percentage: %{{text}}<br>Count: %{{customdata}}<extra></extra>",
                        customdata=sex_data["count"],  # Include count in hover data
                    )
                )

        fig.update_layout(
            title="Population Pyramid - Age and Sex Distribution (% of Total Population)",
            xaxis_title="Percentage of Total Population (%)",
            yaxis_title="Age Group",
            barmode="overlay",
            height=600,
        )

        # Update x-axis to show percentages properly
        fig.update_xaxes(
            tickformat=".1f",
            range=[
                -max(age_sex_data["percentage"]) * 1.1,
                max(age_sex_data["percentage"]) * 1.1,
            ],
        )

        self.figures.append(("age_sex_pyramid", fig))
        logger.info(f"✓ Age/sex analysis complete")
        return fig

    # ============================================================================
    # MEDICATION ANALYSIS
    # ============================================================================

    def analyze_medication_patterns(self) -> go.Figure:
        """Comprehensive medication analysis using Polars"""

        logger.info("Analyzing medication patterns...")

        # Get medication data
        medications = self.get_lazy_frame("SharedCare.GP_Medications").filter(
            (pl.col("Deleted") != "Y") | pl.col("Deleted").is_null()
        )

        # Calculate medication statistics per patient
        med_stats = (
            medications.group_by("FK_Patient_Link_ID")
            .agg(
                [
                    pl.count().alias("total_prescriptions"),
                    pl.n_unique("SuppliedCode").alias("unique_medications"),
                    (pl.col("RepeatMedicationFlag") == "Y")
                    .sum()
                    .alias("repeat_prescriptions"),
                    pl.col("MedicationStartDate")
                    .is_not_null()
                    .sum()
                    .alias("has_start_date"),
                    pl.col("MedicationEndDate")
                    .is_not_null()
                    .sum()
                    .alias("has_end_date"),
                    # Calculate average duration where both dates exist
                    # Calculate average duration where both dates exist
                    pl.when(
                        pl.col("MedicationStartDate").is_not_null()
                        & pl.col("MedicationEndDate").is_not_null()
                    )
                    .then(
                        (
                            pl.col("MedicationEndDate") - pl.col("MedicationStartDate")
                        ).dt.total_days()
                    )
                    .mean()
                    .alias("avg_duration_days"),
                ]
            )
            .with_columns(
                [
                    # Calculate repeat percentage
                    (
                        pl.col("repeat_prescriptions")
                        * 100.0
                        / pl.col("total_prescriptions")
                    ).alias("repeat_percentage"),
                    # Calculate completion percentages
                    (
                        pl.col("has_start_date") * 100.0 / pl.col("total_prescriptions")
                    ).alias("start_date_completion"),
                    (
                        pl.col("has_end_date") * 100.0 / pl.col("total_prescriptions")
                    ).alias("end_date_completion"),
                ]
            )
            .with_columns(
                [
                    # Create polypharmacy categories
                    pl.when(pl.col("unique_medications") == 0)
                    .then(pl.lit("0 medications"))
                    .when(pl.col("unique_medications") == 1)
                    .then(pl.lit("1 medication"))
                    .when(pl.col("unique_medications").is_between(2, 4))
                    .then(pl.lit("2-4 medications"))
                    .when(pl.col("unique_medications").is_between(5, 9))
                    .then(pl.lit("5-9 medications (polypharmacy)"))
                    .when(pl.col("unique_medications").is_between(10, 19))
                    .then(pl.lit("10-19 medications"))
                    .otherwise(pl.lit("20+ medications"))
                    .alias("medication_category")
                ]
            )
            .collect()
        )

        # Aggregate by category
        category_stats = (
            med_stats.group_by("medication_category")
            .agg(
                [
                    pl.count().alias("patient_count"),
                    pl.mean("total_prescriptions").alias("avg_total_prescriptions"),
                    pl.mean("repeat_percentage").alias("avg_repeat_percentage"),
                    pl.mean("start_date_completion").alias("avg_start_date_completion"),
                    pl.mean("end_date_completion").alias("avg_end_date_completion"),
                    pl.mean("avg_duration_days").alias("avg_duration_days"),
                ]
            )
            .sort("medication_category")
            .to_pandas()
        )

        # After creating category_stats, add this to enforce order and convert to pandas:
        category_order = [
            "0 medications",
            "1 medication",
            "2-4 medications",
            "5-9 medications (polypharmacy)",
            "10-19 medications",
            "20+ medications",
        ]

        category_stats_df = (
            category_stats.set_index("medication_category")
            .reindex(category_order)
            .reset_index()
            .dropna()  # Remove any categories not in our data
        )

        # Store results
        self.analysis_results["medication_patterns"] = category_stats
        self.analysis_results["individual_med_stats"] = med_stats.to_pandas()

        # Create visualization
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=[
                "Patient Distribution by Unique Medication Count",
                "Average Total Prescriptions per Category",
                "Repeat vs Acute Prescription %",
                "Date Field Completion Rates",
            ],
        )

        # Patient distribution
        fig.add_trace(
            go.Bar(
                x=category_stats_df["medication_category"],
                y=category_stats_df["patient_count"],
                name="Patient Count",
                marker_color="lightblue",
            ),
            row=1,
            col=1,
        )

        # Average prescriptions
        fig.add_trace(
            go.Bar(
                x=category_stats_df["medication_category"],
                y=category_stats_df["avg_total_prescriptions"],
                name="Avg Prescriptions",
                marker_color="green",
            ),
            row=1,
            col=2,
        )

        # Repeat percentages
        fig.add_trace(
            go.Bar(
                x=category_stats_df["medication_category"],
                y=category_stats_df["avg_repeat_percentage"],
                name="% Repeat",
                marker_color="orange",
            ),
            row=2,
            col=1,
        )

        # Date completion
        fig.add_trace(
            go.Scatter(
                x=category_stats_df["medication_category"],
                y=category_stats_df["avg_start_date_completion"],
                mode="lines+markers",
                name="Start Date %",
                line=dict(color="blue"),
            ),
            row=2,
            col=2,
        )
        fig.add_trace(
            go.Scatter(
                x=category_stats_df["medication_category"],
                y=category_stats_df["avg_end_date_completion"],
                mode="lines+markers",
                name="End Date %",
                line=dict(color="red"),
            ),
            row=2,
            col=2,
        )

        # Then in the plotting section, update the layout:
        fig.update_layout(
            title_text="Comprehensive Medication Analysis",
            height=700,
            showlegend=False,
            font_size=10,  # Reduce overall font size
        )

        # Update x-axes with smaller text and better angles
        fig.update_xaxes(
            tickangle=-45,
            tickfont_size=9,  # Smaller tick labels
            title_font_size=10,  # Smaller axis titles
            row=1,
            col=1,
        )
        fig.update_xaxes(
            tickangle=-45, tickfont_size=9, title_font_size=10, row=1, col=2
        )
        fig.update_xaxes(
            tickangle=-45, tickfont_size=9, title_font_size=10, row=2, col=1
        )
        fig.update_xaxes(
            tickangle=-45, tickfont_size=9, title_font_size=10, row=2, col=2
        )

        fig.update_layout(
            title_text="Comprehensive Medication Analysis", height=700, showlegend=False
        )
        fig.update_xaxes(tickangle=-45, row=1, col=1)
        fig.update_xaxes(tickangle=-45, row=1, col=2)
        fig.update_xaxes(tickangle=-45, row=2, col=1)
        fig.update_xaxes(tickangle=-45, row=2, col=2)

        self.figures.append(("medication_patterns", fig))
        logger.info(f"✓ Medication analysis complete")
        return fig

    def analyze_polypharmacy_snapshot(
        self, months_ago: int = 6, include_no_end_date: bool = True, max_meds=20
    ) -> go.Figure:
        """Analyze polypharmacy at a specific point in time"""

        logger.info(f"Analyzing polypharmacy snapshot {months_ago} months ago...")

        # Calculate snapshot date (6 months ago)
        snapshot_date = date.today() - timedelta(days=months_ago * 30)  # Approximate
        logger.info(f"Snapshot date: {snapshot_date}")

        # Get all active patients (universe of patients)
        all_patients = (
            self.get_patient_data(active_only=True)
            .select("FK_Patient_Link_ID")
            .unique()
            .collect()
        )

        # Get medication data
        medications = self.get_lazy_frame("SharedCare.GP_Medications").filter(
            (pl.col("Deleted") != "Y") | pl.col("Deleted").is_null()
        )

        # Filter for medications active at the snapshot date
        active_meds_base = medications.filter(
            # Medication started before or on snapshot date
            (pl.col("MedicationStartDate") <= pl.lit(snapshot_date))
            | pl.col("MedicationStartDate").is_null()
        )

        if include_no_end_date:
            # Include both: explicit end dates and no end dates
            active_meds_snapshot = active_meds_base.filter(
                # Medication either has no end date OR ended after snapshot date
                pl.col("MedicationEndDate").is_null()
                | (pl.col("MedicationEndDate") > pl.lit(snapshot_date))
            ).unique(subset=["FK_Patient_Link_ID", "SuppliedCode"])
        else:
            # Only include medications with explicit end dates
            active_meds_snapshot = active_meds_base.filter(
                # Must have an end date AND ended after snapshot date
                pl.col("MedicationEndDate").is_not_null()
                & (pl.col("MedicationEndDate") > pl.lit(snapshot_date))
            ).unique(subset=["FK_Patient_Link_ID", "SuppliedCode"])

        # Count unique active medications per patient at snapshot
        patient_med_counts = (
            active_meds_snapshot.group_by("FK_Patient_Link_ID")
            .agg([pl.n_unique("SuppliedCode").alias("active_medications_count")])
            .with_columns(
                [
                    # Cap at max_meds for display purposes
                    pl.when(pl.col("active_medications_count") > max_meds)
                    .then(max_meds)
                    .otherwise(pl.col("active_medications_count"))
                    .alias("medication_count_capped")
                ]
            )
            .collect()
        )

        all_patient_med_counts = all_patients.join(
            patient_med_counts, on="FK_Patient_Link_ID", how="left"
        ).with_columns(
            [
                # Fill nulls with 0 (patients with no active medications)
                pl.col("active_medications_count").fill_null(0),
                pl.col("medication_count_capped").fill_null(0),
            ]
        )

        # Get histogram data
        category_counts = (
            all_patient_med_counts.group_by("medication_count_capped")
            .agg([pl.count().alias("patient_count")])
            .sort("medication_count_capped")
            .to_pandas()
        )

        # Create full range 0-max_meds with zeros for missing values
        full_range = pd.DataFrame({"medication_count_capped": range(0, max_meds + 1)})
        category_counts_ordered = full_range.merge(
            category_counts, on="medication_count_capped", how="left"
        ).fillna(0)
        # Calculate total patients for percentage calculation
        total_patients = category_counts_ordered["patient_count"].sum()

        # Add percentage column
        category_counts_ordered["percentage"] = (
            category_counts_ordered["patient_count"] / total_patients * 100
            if total_patients > 0
            else 0
        )

        # Store results
        end_date_filter = (
            "with_and_without_end_dates"
            if include_no_end_date
            else "explicit_end_dates_only"
        )
        self.analysis_results[
            f"polypharmacy_snapshot_{months_ago}m_{end_date_filter}"
        ] = {
            "snapshot_date": snapshot_date,
            "include_no_end_date": include_no_end_date,
            "category_counts": category_counts_ordered,
            "individual_counts": patient_med_counts.to_pandas(),
        }

        # Create histogram
        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=category_counts_ordered["medication_count_capped"],
                y=category_counts_ordered["percentage"],
                marker_color="steelblue",
                text=[f"{p:.1f}%" for p in category_counts_ordered["percentage"]],
                textposition="outside",
            )
        )

        # Calculate total patients for subtitle
        total_patients = category_counts_ordered["patient_count"].sum()
        end_date_status = (
            "Including no-end-date meds"
            if include_no_end_date
            else "Explicit end dates only"
        )

        fig.update_layout(
            title=f"Polypharmacy Distribution - Point in Time Snapshot<br>"
            f"<sub>Date: {snapshot_date} ({months_ago} months ago) | "
            f"Total Patients: {total_patients:,} | {end_date_status}</sub>",
            xaxis_title="Number of Active Medications",
            yaxis_title="Percentage of Patients (%)",
            xaxis=dict(
                tickmode="linear", tick0=0, dtick=1, range=[-0.5, max_meds + 0.5]
            ),
            height=500,
            showlegend=False,
        )

        # # Add percentage annotations
        # for i, (med_count, count) in enumerate(zip(category_counts_ordered['medication_count_capped'],
        #                                         category_counts_ordered['patient_count'])):
        #     if count > 0:  # Only annotate bars that exist
        #         percentage = (count / total_patients) * 100 if total_patients > 0 else 0
        #         fig.add_annotation(
        #             x=med_count,
        #             y=count + max(category_counts_ordered['patient_count']) * 0.02,
        #             text=f"{percentage:.1f}%",
        #             showarrow=False,
        #             font=dict(size=10)
        #         )

        self.figures.append(
            (f"polypharmacy_snapshot_{months_ago}m_{end_date_filter}", fig)
        )
        logger.info(f"✓ Polypharmacy snapshot analysis complete")

        return fig

    # ============================================================================
    # EVENT DISTRIBUTION ANALYSIS
    # ============================================================================

    def analyze_event_distributions(self) -> go.Figure:
        """Analyze distribution of healthcare events per patient"""

        logger.info("Analyzing event distributions...")

        patients = self.get_patient_data(active_only=True)

        # Get event counts for each patient across different domains
        event_data = patients.select(["FK_Patient_Link_ID"]).unique().collect()

        # Medications per patient
        med_counts = (
            self.get_lazy_frame("SharedCare.GP_Medications")
            .filter((pl.col("Deleted") != "Y") | pl.col("Deleted").is_null())
            .group_by("FK_Patient_Link_ID")
            .agg(pl.count().alias("medications"))
            .collect()
        )

        # GP events per patient
        gp_counts = (
            self.get_lazy_frame("SharedCare.GP_Events")
            .filter((pl.col("Deleted") != "Y") | pl.col("Deleted").is_null())
            .group_by("FK_Patient_Link_ID")
            .agg(pl.count().alias("gp_events"))
            .collect()
        )

        # Inpatient episodes per patient
        # Hospital admissions per patient (actual stays, not events)
        inp_counts = (
            self.get_lazy_frame("SharedCare.Acute_Inpatients")
            .filter(
                ((pl.col("Deleted") != "Y") | pl.col("Deleted").is_null())
                & (pl.col("EventType") == "Admission")  # Only count actual admissions
            )
            .group_by("FK_Patient_Link_ID")
            .agg(pl.count().alias("hospital_admissions"))  # Rename for clarity
            .collect()
        )

        # A&E visits per patient
        ae_counts = (
            self.get_lazy_frame("SharedCare.Acute_AE")
            .filter(
                (pl.col("Deleted") != "Y")
                | pl.col("Deleted").is_null() & (pl.col("EventType") == "Attendance")
            )
            .group_by("FK_Patient_Link_ID")
            .agg(pl.count().alias("ae_visits"))
            .collect()
        )

        # Join all counts together
        combined_data = (
            event_data.join(med_counts, on="FK_Patient_Link_ID", how="left")
            .join(gp_counts, on="FK_Patient_Link_ID", how="left")
            .join(inp_counts, on="FK_Patient_Link_ID", how="left")
            .join(ae_counts, on="FK_Patient_Link_ID", how="left")
            .with_columns(
                [
                    pl.col("medications").fill_null(0),
                    pl.col("gp_events").fill_null(0),
                    pl.col("hospital_admissions").fill_null(0),
                    pl.col("ae_visits").fill_null(0),
                ]
            )
        )

        df = combined_data.to_pandas()

        # Store results
        self.analysis_results["event_distributions"] = df

        # Calculate summary statistics
        summary_stats = {}
        for col in ["medications", "gp_events", "hospital_admissions", "ae_visits"]:
            zero_pct = (df[col] == 0).mean() * 100
            summary_stats[col] = {
                "zero_percentage": zero_pct,
                "mean": df[col].mean(),
                "median": df[col].median(),
                "p95": df[col].quantile(0.95),
            }

        # Create improved histograms
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=[
                f"Medications per Patient<br><sup>{summary_stats['medications']['zero_percentage']:.1f}% have 0</sup>",
                f"GP Events per Patient<br><sup>{summary_stats['gp_events']['zero_percentage']:.1f}% have 0</sup>",
                f"Hospital Admissions per Patient<br><sup>{summary_stats['hospital_admissions']['zero_percentage']:.1f}% have 0</sup>",
                f"A&E Attendance per Patient<br><sup>{summary_stats['ae_visits']['zero_percentage']:.1f}% have 0</sup>",
            ],
            vertical_spacing=0.15,
        )

        # Function to create smart histogram
        def add_smart_histogram(data, title, color, row, col):
            p95 = np.percentile(data, 95)
            # Cap display at p95 to avoid long tail
            display_data = data[data <= p95] if p95 > 0 else data

            fig.add_trace(
                go.Histogram(
                    x=display_data,
                    name=title,
                    marker_color=color,
                    nbinsx=min(50, int(p95) + 1) if p95 > 0 else 10,
                    hovertemplate=f"{title}: %{{x}}<br>Patients: %{{y}}<extra></extra>",
                ),
                row=row,
                col=col,
            )

        # Add histograms
        add_smart_histogram(df["medications"], "Medications", "blue", 1, 1)
        add_smart_histogram(df["gp_events"], "GP Events", "green", 1, 2)
        add_smart_histogram(df["hospital_admissions"], "Admissions", "orange", 2, 1)
        add_smart_histogram(df["ae_visits"], "A&E Visits", "red", 2, 2)

        fig.update_layout(
            title_text="Healthcare Event Distributions per Patient<br><sup>Capped at 95th percentile for clarity</sup>",
            showlegend=False,
            height=700,
        )

        # Update axis labels with stats
        fig.update_xaxes(
            title_text=f"Medications (Mean: {summary_stats['medications']['mean']:.1f})",
            row=1,
            col=1,
        )
        fig.update_xaxes(
            title_text=f"GP Events (Mean: {summary_stats['gp_events']['mean']:.1f})",
            row=1,
            col=2,
        )
        fig.update_xaxes(
            title_text=f"Admissions (Mean: {summary_stats['hospital_admissions']['mean']:.1f})",
            row=2,
            col=1,
        )
        fig.update_xaxes(
            title_text=f"A&E Visits (Mean: {summary_stats['ae_visits']['mean']:.1f})",
            row=2,
            col=2,
        )

        self.figures.append(("event_distributions", fig))
        logger.info(f"✓ Event distribution analysis complete")
        return fig

    # ============================================================================
    # EMPTY PATIENTS ANALYSIS
    # ============================================================================

    def analyze_empty_patients(self) -> go.Figure:
        """Analyze patients with no clinical activity"""

        logger.info("Analyzing empty patients...")

        patients = self.get_patient_data(active_only=True)
        total_patients = (
            patients.select("FK_Patient_Link_ID")
            .unique()
            .select(pl.count())
            .collect()
            .item()
        )

        # Check activity in each domain
        activity_checks = {}

        # Define tables to check
        activity_tables = {
            "Medications": "SharedCare.GP_Medications",
            "GP Events": "SharedCare.GP_Events",
            "GP Encounters": "SharedCare.GP_Encounters",
            "Inpatient Care": "SharedCare.Acute_Inpatients",
            "A&E Visits": "SharedCare.Acute_AE",
            "Outpatient Care": "SharedCare.Acute_Outpatients",
            "Allergies": "SharedCare.Acute_Allergies",
            "Social Care": "SharedCare.SocialCare_Events",
        }

        results = []

        for domain_name, table_name in activity_tables.items():
            try:
                # Get unique patients with activity in this domain
                active_patients = (
                    self.get_lazy_frame(table_name)
                    .filter((pl.col("Deleted") != "Y") | pl.col("Deleted").is_null())
                    .select("FK_Patient_Link_ID")
                    .unique()
                    .collect()
                )

                patients_with_data = len(active_patients)
                patients_without_data = total_patients - patients_with_data
                percentage_empty = (patients_without_data / total_patients) * 100
                percentage_has_data = (patients_with_data / total_patients) * 100

                results.append(
                    {
                        "data_type": domain_name,
                        "has_data": patients_with_data,
                        "no_data": patients_without_data,
                        "has_data_pct": percentage_has_data,
                        "no_data_pct": percentage_empty,
                        "total_patients": total_patients,
                    }
                )

            except Exception as e:
                logger.warning(f"Could not analyze {domain_name}: {e}")

        # Convert to DataFrame
        df = pd.DataFrame(results).sort_values("no_data_pct", ascending=False)

        # Store results
        self.analysis_results["empty_patients"] = df

        # Create visualization - single plot with percentages
        fig = go.Figure()

        # Stacked bar showing coverage in percentages
        fig.add_trace(
            go.Bar(
                name="Has Data",
                x=df["data_type"],
                y=df["has_data_pct"],
                marker_color="lightgreen",
                text=[f"{pct:.1f}%" for pct in df["has_data_pct"]],
                textposition="inside",
                hovertemplate="%{x}<br>Has data: %{text}<br>Count: %{customdata:,}<extra></extra>",
                customdata=df["has_data"],
            )
        )

        fig.add_trace(
            go.Bar(
                name="No Data",
                x=df["data_type"],
                y=df["no_data_pct"],
                marker_color="lightcoral",
                text=[f"{pct:.1f}%" for pct in df["no_data_pct"]],
                textposition="inside",
                hovertemplate="%{x}<br>No data: %{text}<br>Count: %{customdata:,}<extra></extra>",
                customdata=df["no_data"],
            )
        )

        fig.update_layout(
            title=f"Patient Data Coverage Analysis<br><sup>Total patients: {total_patients:,}</sup>",
            barmode="stack",
            height=600,
            xaxis_title="Data Type",
            yaxis_title="Percentage of Patients (%)",
            showlegend=True,
        )

        fig.update_xaxes(tickangle=-45)

        self.figures.append(("empty_patients", fig))
        logger.info(f"✓ Empty patients analysis complete")
        return fig

    # ============================================================================
    # ORCHESTRATOR
    # ============================================================================

    def generate_eda_report(
        self,
        output_file: str = "healthcare_eda_report.html",
        analyses_to_run: List[str] = None,
    ):
        """Generate complete EDA report in one function"""

        if analyses_to_run is None:
            analyses_to_run = [
                "demographics",
                "age_sex",
                "medication_patterns",
                "event_distributions",
                "empty_patients",
            ]

        analysis_functions = {
            "demographics": self.analyze_demographics_completion,
            "age_sex": self.analyze_age_sex_distribution,
            "medication_patterns": self.analyze_medication_patterns,
            "event_distributions": self.analyze_event_distributions,
            "empty_patients": self.analyze_empty_patients,
        }

        logger.info(f"Generating EDA report with {len(analyses_to_run)} analyses...")
        start_time = datetime.now()

        # HTML start
        html_start = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Healthcare EDA Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .section {{ margin-bottom: 50px; }}
                .section-title {{ font-size: 24px; color: #333; margin-bottom: 20px; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
            </style>
        </head>
        <body>
            <h1>Healthcare EDA Report</h1>
            <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <hr>
        """

        # Start writing the file
        with open(output_file, "w") as f:
            f.write(html_start)

            successful_count = 0

            # Run each analysis and write directly to HTML
            for analysis_name in analyses_to_run:
                if analysis_name not in analysis_functions:
                    logger.warning(f"Unknown analysis: {analysis_name}")
                    continue

                try:
                    logger.info(f"Running {analysis_name}...")
                    analysis_start = datetime.now()

                    fig = analysis_functions[analysis_name]()

                    analysis_duration = datetime.now() - analysis_start
                    logger.info(
                        f"✓ {analysis_name} completed in {analysis_duration.total_seconds():.1f}s"
                    )

                    # Write section to HTML
                    section_title = analysis_name.replace("_", " ").title()
                    f.write(f'<div class="section">')
                    f.write(f'<div class="section-title">{section_title}</div>')
                    f.write(fig.to_html(full_html=False, include_plotlyjs="cdn"))
                    f.write("</div>")

                    successful_count += 1

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"✗ {analysis_name} failed: {error_msg}")

                    # Write error to HTML
                    f.write(f'<div class="section">')
                    f.write(
                        f'<div class="section-title">{analysis_name.replace("_", " ").title()} (Failed)</div>'
                    )
                    f.write(f'<p style="color: red;">Error: {error_msg}</p>')
                    f.write("</div>")

            # Close HTML
            f.write("</body></html>")

        total_duration = datetime.now() - start_time

        logger.info(f"EDA report completed in {total_duration.total_seconds():.1f}s")
        logger.info(f"Success rate: {successful_count}/{len(analyses_to_run)}")
        logger.info(f"Report saved to: {Path(output_file).absolute()}")

        return str(Path(output_file).absolute())


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================


def run_polars_eda(data_path: str, output_file: str = "polars_eda_report.html"):
    """
    Convenience function to run full Polars EDA analysis

    Args:
        data_path: Path to the patient data directory
        output_file: Output HTML filename

    Returns:
        Path to generated HTML report
    """

    # Initialize analyzer
    eda = PolarsEDAAnalyzer(data_path)

    # Run analysis
    results = eda.run_comprehensive_eda()

    # Save report
    report_path = eda.save_html_report(results, output_file)

    # Print summary
    print(f"\n{'=' * 60}")
    print("POLARS EDA ANALYSIS COMPLETE 🐻‍❄️")
    print(f"{'=' * 60}")
    print(
        f"Successful analyses: {results['summary']['successful_analyses']}/{results['summary']['total_analyses_requested']}"
    )
    print(f"Total duration: {results['summary']['total_duration_seconds']:.1f} seconds")
    print(f"Figures generated: {results['summary']['total_figures_generated']}")
    print(f"Report saved to: {report_path}")
    print(f"{'=' * 60}")

    return report_path


# Example usage:
if __name__ == "__main__":
    # Run on your subset data
    report_path = run_polars_eda("patient-data-subset")
    print(f"Report available at: {report_path}")
