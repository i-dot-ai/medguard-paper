import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List

import duckdb

from medguard.models import PatientProfile
from medguard.sql_loader import SQLTemplateLoader

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ModularPatientDataProcessor:
    """
    Core processor for building patient profiles from healthcare data.
    Uses Patient_Link as the authoritative source for patient identification.
    """

    def __init__(
        self,
        base_path: str = "patient-data-subset/PopHealth/Medguard/Extract",
        initialise_enriched_views: bool = True,
    ):
        self.base_path = Path(base_path)
        self.conn = duckdb.connect()
        self.table_views = {}
        self.sql_loader = SQLTemplateLoader()

        self.default_kwargs = {
            "patient_view": "SharedCare_Patient",
            "patient_link_view": "SharedCare_Patient_Link",
            "gp_events_enriched": "GPEventsEnriched",
            "gp_events_view": "SharedCare_GP_Events",
            "gp_medications_enriched": "GPMedicationsEnriched",
            "gp_medications_view": "SharedCare_GP_Medications",
            "gp_encounters_enriched": "GPEncountersEnriched",
            "gp_encounters_view": "SharedCare_GP_Encounters",
            "reference_coding_view": "SharedCare_Reference_Coding",
            "reference_snomed_view": "SharedCare_Reference_SnomedCT",
            "smr_codes_view": "SMRCodes",
            "smr_codes_input_file": "inputs/snomed_codes_super_core.csv",
            "smr_outcomes_view": "SMROutcomes",
            "smr_outcomes_input_file": "inputs/smr_codes.csv",
            "smr_positive_outcomes_view": "SMRPositiveOutcomes",
            "smr_positive_outcomes_input_file": "inputs/smr_positive_codes.csv",
            "smr_negative_outcomes_view": "SMRNegativeOutcomes",
            "smr_negative_outcomes_input_file": "inputs/smr_negative_codes.csv",
            "smr_events_view": "SMREvents",
            "smr_outcome_flag_view": "SMROutcomeFlag",
            "smr_patients_view": "SMRPatients",
            "smr_medications_table": "SMRMedications",
            "stratified_sample_view": "StratifiedSampleView",
            "gp_events_excluded_description_view": "GPExcludedDescription",
            "gp_events_excluded_description_input_file": "inputs/gp_events_excluded_description.csv",
            "patients_with_smr_view": "PatientsWithSMR",
            "patients_smr_with_outcome_view": "PatientsSMRWithOutcome",
            "patients_smr_without_outcome_view": "PatientsSMRWithoutOutcome",
            "balanced_smr_sample_view": "BalancedSMRSample",
            "patient_smr_summary_view": "PatientSMRSummary",
            "gp_prescriptions": "GPPrescriptions",
            "duration_days": str(int(28 * 2)),
        }

        # Define available aggregations with their configurations
        self.aggregations = {
            "medications": {
                "table": self.default_kwargs.get("gp_medications_enriched"),
                "patient_link_col": "FK_Patient_Link_ID",
                "fields": [
                    "computed_start_date",
                    "computed_end_date",
                    "Dosage",
                    "Units",
                    "Quantity",
                    "CourseLengthPerIssue",
                    "RepeatMedicationFlag",
                    # Enriched fields
                    "description",
                ],
                "filter": "Deleted = 'N' OR Deleted IS NULL",
            },
            "gp_events": {
                "table": self.default_kwargs.get("gp_events_enriched"),
                "patient_link_col": "FK_Patient_Link_ID",
                "fields": [
                    "EventDate",
                    "description",
                    "Units",
                    "Value",
                    "Episodicity",
                    "was_smr",
                    "flag_smr",
                ],
                "filter": "Deleted = 'N' OR Deleted IS NULL",
            },
            # No field that we can use to easily link to SNOMED or similar, so this is all we've got
            "inpatient_episodes": {
                "table": "SharedCare.Acute_Inpatients",
                "patient_link_col": "FK_Patient_Link_ID",
                "fields": [
                    "EventType",
                    "AdmissionDate",
                    "AdmissionTypeDescription",
                    "AdmissionSourceDescription",
                    "AdmissionCategoryDescription",
                    "ExpectedDischargeDate",
                    "TransferDate",
                    "DischargeDate",
                    "DischargeMethodDescription",
                    "DischargeDestinationDescription",
                    "WardDescription",
                    "SpecialtyDescription",
                ],
                "filter": "Deleted = 'N' OR Deleted IS NULL",
            },
            # No field that we can use to easily link to SNOMED or similar, will leave as is
            "ae_visits": {
                "table": "SharedCare.Acute_AE",
                "patient_link_col": "FK_Patient_Link_ID",
                "fields": [
                    "EventType",
                    "AttendanceDate",
                    "ExpectedDischargeDate",
                    "DischargeDate",
                    "DischargeMethodDescription",
                    "DischargeDestinationDescription",
                    "LocationDescription",
                    "ReasonForAttendanceDescription",
                ],
                "filter": "Deleted = 'N' OR Deleted IS NULL",
            },
            "outpatient_visits": {
                "table": "SharedCare.Acute_Outpatients",
                "patient_link_col": "FK_Patient_Link_ID",
                "fields": [
                    "EventType",
                    "ReferralDate",
                    "AttendanceDate",
                    "ProcessDate",
                    "DischargeDate",
                    "DischargeMethodDescription",
                    "ClinicDescription",
                    "ReferralOutcome",
                    "SpecialtyDescription",
                    "AttendanceTypeDescription",
                ],
                "filter": "Deleted = 'N' OR Deleted IS NULL",
            },
            "allergies": {
                "table": "SharedCare.Acute_Allergies",
                "patient_link_col": "FK_Patient_Link_ID",
                "fields": [
                    "AllergenTypeCode",
                    "AllergenDescription",
                    "AllergenReference",
                    "AllergenCodeSystem",
                    "AllergenSeverity",
                    "AllergenReactionCode",
                    "AllergenRecordedDate",
                ],
                "filter": "Deleted = 'N' OR Deleted IS NULL",
            },
            "social_care_events": {
                "table": "SharedCare.SocialCare_Events",
                "patient_link_col": "FK_Patient_Link_ID",
                "fields": [
                    "Status",
                    "TypeDescription",
                    "StartDate",
                    "EndDate",
                    "EventType",
                ],
                "filter": "Deleted = 'N' OR Deleted IS NULL",
            },
            "smr_medication_changes": {
                "table": self.default_kwargs.get("smr_medications_table"),
                "patient_link_col": "FK_Patient_Link_ID",
                "fields": [
                    "smr_date",
                    "medication_code",
                    "medication_name",
                    "change_type",
                ],
                "filter": None,
            },
            "gp_prescriptions": {
                "table": self.default_kwargs.get("gp_prescriptions"),
                "patient_link_col": "FK_Patient_Link_ID",
                "fields": [
                    "medication_code",
                    "medication_name",
                    "dosage",
                    "units",
                    "medication_start_date",
                    "medication_end_date",
                    "total_duration_days",
                    "prescription_count",
                    "average_course_length",
                    "is_repeat_medication",
                ],
            },
        }

        # Initialize views on creation
        self._initialize(initialise_enriched_views)

    def _initialize(self, initialise_enriched_views: bool):
        """Initialize the processor by discovering tables and creating views"""
        logger.info("Initializing ModularPatientDataProcessor...")
        self.create_table_views()
        if initialise_enriched_views:
            self.create_enriched_views()
        logger.info(f"Initialization complete. Found {len(self.table_views)} tables.")

    def discover_tables(self) -> Dict[str, str]:
        """Discover all available tables and their parquet file paths"""
        tables = {}

        if not self.base_path.exists():
            logger.error(f"Base path not found: {self.base_path}")
            return tables

        for table_dir in self.base_path.iterdir():
            if table_dir.is_dir():
                v1_path = table_dir / "v1_0"
                if v1_path.exists():
                    parquet_files = list(v1_path.glob("*.parquet"))
                    if parquet_files:
                        pattern = str(v1_path / "*.parquet")
                        tables[table_dir.name] = pattern
                        logger.debug(
                            f"Found table {table_dir.name} with {len(parquet_files)} files"
                        )

        return tables

    def create_table_views(self):
        """Create DuckDB views for all discovered tables"""
        tables = self.discover_tables()

        for table_name, parquet_pattern in tables.items():
            view_name = table_name.replace(".", "_")

            try:
                sql = f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM '{parquet_pattern}'"
                self.conn.execute(sql)
                self.table_views[table_name] = view_name

                # Log basic info about the view
                count_sql = f"SELECT COUNT(*) FROM {view_name}"
                count = self.conn.execute(count_sql).fetchone()[0]
                logger.debug(f"Created view {view_name} with {count:,} rows")

            except Exception as e:
                logger.error(f"Failed to create view for {table_name}: {e}")

    def create_enriched_views(self):
        # Check if reference tables exist

        templates = [
            "GPExcludedDescription",
            "GPMedicationsEnriched",
            "GPEncountersEnriched",
            "SMRCodes",
            "SMROutcomes",
            "SMRPositiveOutcomes",
            "SMRNegativeOutcomes",
            "GPPrescriptions",
            "SMRMedications",
            "SMREvents",
            "GPEventsEnriched",
            "SMRPatients",
        ]

        for template in templates:
            logger.info(f"Processing {template}")
            self.execute_sql_template(template)

        logger.info(f"Created {len(templates)} enriched views: {templates}")

    def execute_sql_template(self, template_name: str, **kwargs):
        """Execute a SQL template with parameters"""

        # Map template names to file paths
        template_mapping = {
            "GPEventsEnriched": "views/gp_events_enriched.sql",
            "GPMedicationsEnriched": "views/gp_medications_enriched.sql",
            "GPEncountersEnriched": "views/gp_encounters_enriched.sql",
            "GPExcludedDescription": "loading/gp_excluded_descriptions.sql",
            "SMRCodes": "loading/smr_codes.sql",
            "SMRPositiveOutcomes": "loading/smr_positive_outcomes.sql",
            "SMRNegativeOutcomes": "loading/smr_negative_outcomes.sql",
            "SMROutcomes": "loading/smr_outcomes.sql",
            "SMREvents": "views/smr_events.sql",
            "SMRPatients": "views/smr_patients.sql",
            "GPPrescriptions": "views/gp_prescriptions.sql",
            "SMRMedications": "views/smr_medications.sql",
        }

        template_path = template_mapping.get(template_name)
        if not template_path:
            raise ValueError(f"Unknown template: {template_name}")

        merged_kwargs = {**self.default_kwargs, **kwargs}
        sql = self.sql_loader.render_template(template_path, merged_kwargs)
        logger.debug(f"Executing SQL from template: {template_path}")
        return self.conn.execute(sql)

    def build_aggregation_cte(self, agg_name: str, config: dict) -> str:
        """Build a CTE for a specific aggregation that filters on patient_batch"""
        view_name = self.table_views.get(
            config["table"], config["table"].replace(".", "_")
        )
        fields = config["fields"]
        patient_link_col = config["patient_link_col"]
        filter_clause = config.get("filter", "")

        # Build JSON objects for each field - handle NULL values
        json_fields = []
        for field in fields:
            json_fields.append(f"'{field}', {field}")
        json_object = f"JSON_OBJECT({', '.join(json_fields)})"

        # Build filter clause if present
        filter_with_and = f"AND ({filter_clause})" if filter_clause else ""

        if agg_name == "gp_events":
            # Use specialized template for gp_events
            cte = self.sql_loader.render_template(
                "profile_building/aggregations/gp_events_agg.sql",
                {
                    "agg_name": agg_name,
                    "patient_link_col": patient_link_col,
                    "view_name": view_name,
                    "filter_clause": filter_with_and,
                },
            )
        else:
            # Use generic template for other aggregations
            cte = self.sql_loader.render_template(
                "profile_building/aggregations/generic_agg.sql",
                {
                    "agg_name": agg_name,
                    "patient_link_col": patient_link_col,
                    "view_name": view_name,
                    "json_object": json_object,
                    "filter_clause": filter_with_and,
                },
            )

        return cte

    def get_patient_sample(
        self,
        sample_strategy: str = "all",
        limit: int = 100,
        offset: int = 0,
        include_deceased: bool = True,
        seed: float = 0.42,
    ) -> List[int]:
        """
        Get a list of patient IDs based on the sampling strategy.

        Args:
            sample_strategy: One of:
                - "all": All valid patients
                - "smr": Patients with at least one SMR event
                - "balanced_smr": 50/50 split of SMR patients with/without outcomes
                - "no_smr": Patients with no SMR events
                - "no_filter": Patients who do NOT match any PINCER filters (excludes all 10 filters)
            limit: Number of patients to return
            offset: Number of patients to skip
            include_deceased: Whether to include deceased patients
            seed: Random seed for reproducibility

        Returns:
            List of FK_Patient_Link_IDs
        """

        # Set random seed for reproducibility
        self.conn.execute(f"SELECT setseed({seed})")

        # Base filters for valid patients
        patient_link_view = self.table_views.get(
            "SharedCare.Patient_Link", "SharedCare_Patient_Link"
        )
        deceased_filter = (
            ""
            if include_deceased
            else "AND (pl.Deceased != 'Y' OR pl.Deceased IS NULL)"
        )

        if sample_strategy == "all":
            sql = self.sql_loader.render_template(
                "sampling/all_patients.sql",
                {
                    "patient_link_view": patient_link_view,
                    "deceased_filter": deceased_filter,
                    "limit": limit,
                    "offset": offset,
                },
            )

        elif sample_strategy == "smr":
            sql = self.sql_loader.render_template(
                "sampling/smr_patients.sql",
                {
                    "patient_link_view": patient_link_view,
                    "smr_patients_view": self.default_kwargs.get("smr_patients_view"),
                    "deceased_filter": deceased_filter,
                    "limit": limit,
                    "offset": offset,
                },
            )

        elif sample_strategy == "no_smr":
            # For no_smr, we inline the SQL since we don't have a template yet
            sql = f"""
            SELECT pl.PK_Patient_Link_ID
            FROM {patient_link_view} pl
            LEFT JOIN {self.default_kwargs.get("smr_patients_view")} ps
                ON pl.PK_Patient_Link_ID = ps.FK_Patient_Link_ID
            WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
                AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
                {deceased_filter}
                AND (ps.has_an_smr IS NULL OR ps.has_an_smr = FALSE)
            ORDER BY pl.PK_Patient_Link_ID
            LIMIT {limit}
            OFFSET {offset}
            """

        elif sample_strategy == "balanced_smr_snomed":
            # Get exactly half with outcomes, half without
            half_limit = limit // 2
            remainder = limit % 2  # Handle odd numbers

            sql = self.sql_loader.render_template(
                "sampling/balanced_smr_snomed.sql",
                {
                    "patient_link_view": patient_link_view,
                    "smr_patients_view": self.default_kwargs.get("smr_patients_view"),
                    "deceased_filter": deceased_filter,
                    "half_limit": half_limit,
                    "half_limit_with_remainder": half_limit + remainder,
                    "half_offset": offset // 2,
                },
            )

        elif sample_strategy == "balanced_smr_medication_changes":
            half_limit = limit // 2
            remainder = limit % 2

            sql = self.sql_loader.render_template(
                "sampling/balanced_smr_medication_changes.sql",
                {
                    "patient_link_view": patient_link_view,
                    "smr_patients_view": self.default_kwargs.get("smr_patients_view"),
                    "smr_medications_table": self.default_kwargs.get(
                        "smr_medications_table"
                    ),
                    "deceased_filter": deceased_filter,
                    "half_limit": half_limit,
                    "half_limit_with_remainder": half_limit + remainder,
                    "half_offset": offset // 2,
                },
            )

        elif sample_strategy == "no_filter":
            # Get all patients matching any filter, then exclude them
            logger.info("Finding patients matching any PINCER filter to exclude...")
            patient_filters = self.get_patients_by_filters(filter_ids=None)
            excluded_patient_ids = list(patient_filters.keys())

            if excluded_patient_ids:
                # Create comma-separated list for SQL IN clause
                excluded_ids_str = ",".join(str(pid) for pid in excluded_patient_ids)
                logger.info(
                    f"Excluding {len(excluded_patient_ids)} patients who match filters"
                )
            else:
                # No patients match filters, exclude none (use -1 as placeholder)
                excluded_ids_str = "-1"
                logger.info("No patients match any filters (all patients eligible)")

            sql = self.sql_loader.render_template(
                "sampling/no_filter_patients.sql",
                {
                    "patient_link_view": patient_link_view,
                    "deceased_filter": deceased_filter,
                    "excluded_patient_ids": excluded_ids_str,
                    "limit": limit,
                    "offset": offset,
                },
            )

        else:
            raise ValueError(f"Unknown sample_strategy: {sample_strategy}")

        logger.info(
            f"Getting patient sample: strategy={sample_strategy}, limit={limit}, offset={offset}"
        )

        try:
            result = self.conn.execute(sql).fetchall()
            patient_ids = [row[0] for row in result]
            logger.info(f"Retrieved {len(patient_ids)} patient IDs")
            return patient_ids
        except Exception as e:
            logger.error(f"Error getting patient sample: {e}")
            return []

    def get_patients_by_filters(
        self,
        filter_ids: List[str] = None,
        min_duration_days: int = None,
        start_date_after: datetime = None,
    ) -> Dict[int, List[Dict]]:
        """
        Get patients matching specific clinical filters.

        Args:
            filter_ids: List of filter IDs to apply (e.g., [5, 6, 10] or ["005", "006", "010"])
                       Can be integers or strings. Strings are used for file lookup,
                       but returned filter_ids will be integers as per SQL output.
                       Valid filter IDs: 5, 6, 10, 16, 23, 26, 28, 33, 43, 55
                       If None, applies all available filters
            min_duration_days: If provided, only include filter matches where
                              (end_date - start_date) >= min_duration_days
            start_date_after: If provided, only include filter matches where
                             start_date >= start_date_after

        Returns:
            Dictionary mapping FK_Patient_Link_ID to list of filter match dicts
            Each filter match dict contains: filter_id (int), start_date, end_date
            If a patient matches a filter multiple times, only the latest period is kept
            Example: {12345: [{"filter_id": 5, "start_date": ..., "end_date": ...}]}
        """

        # Discover available filters if none specified
        if filter_ids is None:
            filter_dir = Path(__file__).parent / "sql" / "filters"
            if filter_dir.exists():
                filter_ids = [f.stem.split("_")[0] for f in filter_dir.glob("*.sql")]
            else:
                logger.warning("No filters directory found")
                return {}

        # Normalize filter IDs to 3-digit strings
        filter_ids = [str(fid).zfill(3) for fid in filter_ids]

        patient_filters = {}

        for filter_id in filter_ids:
            try:
                # Load and execute the filter SQL template
                filter_files = list(
                    Path(__file__).parent.glob(f"sql/filters/{filter_id}_*.sql")
                )

                if not filter_files:
                    logger.warning(f"No filter file found for filter_id: {filter_id}")
                    continue

                filter_file = filter_files[0]
                sql = self.sql_loader.render_template(
                    f"filters/{filter_file.name}", {**self.default_kwargs}
                )

                logger.info(f"Executing filter {filter_id}: {filter_file.name}")

                result = self.conn.execute(sql).fetchall()

                # Track the latest match for each patient-filter combination
                latest_matches = {}  # (patient_id, filter_id) -> (start_date, end_date)

                # Process results - expecting 4 columns: patient_id, filter_id, start_date, end_date
                for row in result:
                    patient_id = row[0]
                    matched_filter_id = row[1]
                    start_date = row[2]
                    end_date = row[3]

                    key = (patient_id, matched_filter_id)

                    # Keep only the latest period (by start_date)
                    if key not in latest_matches or start_date > latest_matches[key][0]:
                        latest_matches[key] = (start_date, end_date)

                # Convert to final structure and apply Python filters
                filtered_matches_count = 0
                for (patient_id, matched_filter_id), (
                    start_date,
                    end_date,
                ) in latest_matches.items():
                    # Apply Python filters

                    # Filter 1: Minimum duration check
                    if min_duration_days is not None:
                        duration = (end_date - start_date).days
                        if duration < min_duration_days:
                            continue

                    # Filter 2: Start date must be after provided date
                    if start_date_after is not None:
                        if start_date < start_date_after:
                            continue

                    # Add to results if passed all filters
                    if patient_id not in patient_filters:
                        patient_filters[patient_id] = []

                    patient_filters[patient_id].append(
                        {
                            "filter_id": int(
                                matched_filter_id
                            ),  # Ensure integer (SQL returns int)
                            "start_date": start_date,
                            "end_date": end_date,
                        }
                    )
                    filtered_matches_count += 1

                logger.info(
                    f"Filter {filter_id} matched {len(latest_matches)} patient-filter combinations "
                    f"({filtered_matches_count} after Python filters)"
                )

            except Exception as e:
                logger.error(f"Error executing filter {filter_id}: {e}")
                continue

        logger.info(f"Total patients matching filters: {len(patient_filters)}")
        return patient_filters

    def get_balanced_patient_sample(
        self,
        filter_ids: List[str],
        total_n: int,
        min_duration_days: int = None,
        start_date_after: datetime = None,
    ) -> tuple[List[int], Dict[int, List[Dict]], Dict[int, date], Dict[int, str]]:
        """
        Get a balanced sample of patients matching filters (positive) and not matching (negative).

        Samples equally from each filter to get positive cases (up to half of total_n),
        then uses stratified matching to sample negative cases that match the demographic
        and clinical characteristics of positive cases at the same sample_date.

        Sample dates are calculated as the midpoint between filter start and end dates.
        Negative patients are matched to positives within the same month and assigned
        the same sample_date as their matched positive patient.

        Each positive patient is assigned a "primary filter" (the filter they were sampled from)
        to ensure equal distribution across filters even when patients match multiple filters.

        Stratification features (calculated at sample_date):
        - Age bins: <40, 40-60, 60-75, >75
        - Gender: M, F
        - Condition count bins (GPEvents before sample_date): 0-10, 11-25, 26-50, >50
        - Active prescription count bins (active at sample_date): 0-5, 6-12, 13-20, >20

        For each positive patient, a negative patient is sampled from the same stratum
        (matching on all 4 features). This controls for confounding variables.

        Args:
            filter_ids: List of filter IDs to apply (e.g., [5, 6, 10] or ["005", "006", "010"])
                       Can be integers or strings. Valid filter IDs: 5, 6, 10, 16, 23, 26, 28, 33, 43, 55
            total_n: Total number of patients to sample
            min_duration_days: If provided, only include filter matches where
                              (end_date - start_date) >= min_duration_days
            start_date_after: If provided, only include filter matches where
                             start_date >= start_date_after

        Returns:
            Tuple of (patient_ids, patient_filters, patient_sample_dates, patient_primary_filters) where:
            - patient_ids: List of sampled patient IDs (positive + negative)
            - patient_filters: Dict mapping patient_id to matched filters (only for positive cases)
            - patient_sample_dates: Dict mapping patient_id to sample_date (for all sampled patients)
            - patient_primary_filters: Dict mapping patient_id to primary filter_id (only for positive cases)
        """
        import random

        # Calculate target numbers
        target_positive = total_n // 2
        target_negative = total_n - target_positive

        logger.info(
            f"Target: {target_positive} positive, {target_negative} negative (total: {total_n})"
        )

        # Get all patients matching filters
        patient_filters = self.get_patients_by_filters(
            filter_ids=filter_ids,
            min_duration_days=min_duration_days,
            start_date_after=start_date_after,
        )

        # Organize patients by filter
        filter_to_patients = {}  # filter_id -> set of patient_ids
        for patient_id, filter_matches in patient_filters.items():
            for match in filter_matches:
                filter_id = match["filter_id"]
                if filter_id not in filter_to_patients:
                    filter_to_patients[filter_id] = set()
                filter_to_patients[filter_id].add(patient_id)

        # Sample equally from each filter
        patients_per_filter = target_positive // len(filter_ids) if filter_ids else 0
        remainder = target_positive % len(filter_ids) if filter_ids else 0

        positive_patients = set()
        total_shortfall = 0
        excess_by_filter = {}  # Track excess patients per filter
        shortfall_by_filter = {}  # Track shortfall per filter
        patient_to_primary_filter = {}  # Track which filter each patient was sampled from

        # First pass: sample from each filter, track shortfalls and excess
        for i, filter_id in enumerate(sorted(filter_to_patients.keys())):
            available = filter_to_patients[filter_id]
            # Add 1 extra to first 'remainder' filters to distribute remainder
            target_for_filter = patients_per_filter + (1 if i < remainder else 0)

            if len(available) < target_for_filter:
                # Shortfall: take all available
                shortfall = target_for_filter - len(available)
                total_shortfall += shortfall
                shortfall_by_filter[filter_id] = shortfall
                logger.warning(
                    f"Filter {filter_id}: Only {len(available)} patients available, "
                    f"target was {target_for_filter} (shortfall: {shortfall})"
                )
                sampled = available
            elif len(available) > target_for_filter:
                # Excess: randomly sample target amount, save excess for later
                excess = list(available)
                random.shuffle(excess)
                sampled = set(excess[:target_for_filter])
                not_sampled = set(
                    excess[target_for_filter:]
                )  # The excess patients (as set)

                # Only add to excess if not already sampled (handles multi-filter patients)
                new_excess = not_sampled - positive_patients
                excess_by_filter[filter_id] = new_excess

                logger.info(
                    f"Filter {filter_id}: {len(available)} patients available, "
                    f"randomly sampling {target_for_filter} (excess: {len(new_excess)} unique saved for shortfall recovery)"
                )
            else:
                # Exact match
                sampled = available

            # Track which filter each patient was sampled from (only if not already sampled)
            for patient_id in sampled:
                if patient_id not in patient_to_primary_filter:
                    patient_to_primary_filter[patient_id] = filter_id

            positive_patients.update(sampled)
            logger.info(f"Filter {filter_id}: Sampled {len(sampled)} patients")

        logger.info(
            f"Initial positive patients sampled: {len(positive_patients)} (target: {target_positive})"
        )

        # Second pass: preferentially recover shortfalls from same filter's excess
        if shortfall_by_filter:
            logger.info(
                "Recovering shortfalls preferentially from same filter's excess..."
            )

            # Try to recover each filter's shortfall from that filter's excess first
            for filter_id, shortfall in shortfall_by_filter.items():
                if filter_id in excess_by_filter and excess_by_filter[filter_id]:
                    # Remove any excess patients that are already sampled
                    available_excess = excess_by_filter[filter_id] - positive_patients

                    if available_excess:
                        can_recover = min(shortfall, len(available_excess))
                        recovery_sample = random.sample(
                            list(available_excess), can_recover
                        )
                        positive_patients.update(recovery_sample)

                        # Assign primary filter to recovered patients
                        for patient_id in recovery_sample:
                            if patient_id not in patient_to_primary_filter:
                                patient_to_primary_filter[patient_id] = filter_id

                        # Update the shortfall and excess
                        shortfall_by_filter[filter_id] -= can_recover
                        excess_by_filter[filter_id] = available_excess - set(
                            recovery_sample
                        )

                        logger.info(
                            f"Filter {filter_id}: Recovered {can_recover} patients from same filter's excess (shortfall reduced to {shortfall_by_filter[filter_id]})"
                        )

        # Third pass: use remaining excess from all filters to fill any remaining shortfalls
        actual_shortfall = target_positive - len(positive_patients)

        if actual_shortfall > 0:
            # Collect all remaining excess across all filters
            all_remaining_excess = set()
            for filter_id, excess in excess_by_filter.items():
                all_remaining_excess.update(excess - positive_patients)

            if all_remaining_excess:
                logger.info(
                    f"Recovering remaining shortfall: {actual_shortfall} patients needed, {len(all_remaining_excess)} unique available in global excess pool"
                )

                can_recover = min(actual_shortfall, len(all_remaining_excess))
                if can_recover > 0:
                    recovery_sample = random.sample(
                        list(all_remaining_excess), can_recover
                    )
                    positive_patients.update(recovery_sample)

                    # Assign primary filter to recovered patients (use first matched filter)
                    for patient_id in recovery_sample:
                        if (
                            patient_id in patient_filters
                            and patient_id not in patient_to_primary_filter
                        ):
                            # Get the first filter this patient matches
                            first_filter = patient_filters[patient_id][0]["filter_id"]
                            patient_to_primary_filter[patient_id] = first_filter

                    logger.info(
                        f"Recovered {can_recover} patients from global excess pool"
                    )

                if can_recover < actual_shortfall:
                    remaining_shortfall = actual_shortfall - can_recover
                    logger.warning(
                        f"Still short by {remaining_shortfall} patients after recovery (insufficient unique excess)"
                    )
            else:
                logger.warning(
                    f"Shortfall of {actual_shortfall} patients but no excess available for recovery"
                )

        logger.info(
            f"Final positive patients sampled: {len(positive_patients)} (target: {target_positive})"
        )

        # Balance negative sample size if we have fewer positive cases than expected
        if len(positive_patients) < target_positive:
            original_target_negative = target_negative
            target_negative = len(positive_patients)
            logger.info(
                f"Balancing sample: Reducing negative target from {original_target_negative} to {target_negative} "
                f"to match actual positive sample size"
            )

        # Calculate sample_date for each positive patient (midpoint of first filter match)
        from datetime import date

        logger.info("Calculating sample_dates for positive patients...")
        patient_to_sample_date = {}
        today = date.today()
        future_date_count = 0

        for patient_id in positive_patients:
            filter_matches = patient_filters[patient_id]
            if filter_matches:
                # Use first filter match to calculate sample_date
                first_match = filter_matches[0]
                start = first_match["start_date"]
                end = first_match["end_date"]

                # Validate dates - skip if either is in the future (likely bad data)
                if start.date() > today or end.date() > today:
                    logger.warning(
                        f"Patient {patient_id} has future filter dates (start: {start.date()}, end: {end.date()}) - skipping"
                    )
                    future_date_count += 1
                    continue

                # Calculate midpoint
                sample_date = start + (end - start) / 2
                patient_to_sample_date[patient_id] = sample_date.date()

        if future_date_count > 0:
            logger.warning(
                f"Excluded {future_date_count} patients with future filter dates from sample_date calculation"
            )

        # Remove patients without valid sample_dates and try to replace them
        positive_patients_with_dates = set(patient_to_sample_date.keys())
        removed_patients = positive_patients - positive_patients_with_dates

        if removed_patients:
            logger.warning(
                f"Removing {len(removed_patients)} positive patients without valid sample_dates"
            )

            # Group removed patients by their primary filter
            removed_by_filter = {}
            for patient_id in removed_patients:
                primary_filter = patient_to_primary_filter.get(patient_id)
                if primary_filter:
                    if primary_filter not in removed_by_filter:
                        removed_by_filter[primary_filter] = []
                    removed_by_filter[primary_filter].append(patient_id)

            positive_patients = positive_patients_with_dates

            # Try to replace removed patients preferentially from same filter's excess
            total_replaced = 0
            for filter_id, removed_list in removed_by_filter.items():
                replacement_needed = len(removed_list)

                if filter_id in excess_by_filter:
                    # Get valid replacements from this filter's excess (with valid dates)
                    available_excess = excess_by_filter[filter_id] - positive_patients
                    valid_replacements = []

                    for candidate_id in available_excess:
                        if candidate_id in patient_filters:
                            first_match = patient_filters[candidate_id][0]
                            start = first_match["start_date"]
                            end = first_match["end_date"]

                            # Only use if dates are valid (not in future)
                            if start.date() <= today and end.date() <= today:
                                valid_replacements.append(candidate_id)

                    # Replace from same filter's excess
                    can_replace = min(replacement_needed, len(valid_replacements))
                    if can_replace > 0:
                        replacements = random.sample(valid_replacements, can_replace)

                        # Calculate sample_dates and assign primary filter for replacements
                        for replacement_id in replacements:
                            first_match = patient_filters[replacement_id][0]
                            start = first_match["start_date"]
                            end = first_match["end_date"]
                            sample_date = start + (end - start) / 2
                            patient_to_sample_date[replacement_id] = sample_date.date()
                            patient_to_primary_filter[replacement_id] = filter_id

                        positive_patients.update(replacements)
                        excess_by_filter[filter_id] = available_excess - set(
                            replacements
                        )
                        total_replaced += can_replace
                        logger.info(
                            f"Filter {filter_id}: Replaced {can_replace}/{replacement_needed} removed patients from same filter's excess"
                        )

            # Try global replacement for any remaining
            still_need_replacement = len(removed_patients) - total_replaced
            if still_need_replacement > 0:
                # Collect all remaining excess with valid dates
                all_remaining_excess = set()
                for filter_id, excess in excess_by_filter.items():
                    for candidate_id in excess:
                        if (
                            candidate_id not in positive_patients
                            and candidate_id in patient_filters
                        ):
                            first_match = patient_filters[candidate_id][0]
                            start = first_match["start_date"]
                            end = first_match["end_date"]
                            if start.date() <= today and end.date() <= today:
                                all_remaining_excess.add(candidate_id)

                can_replace = min(still_need_replacement, len(all_remaining_excess))
                if can_replace > 0:
                    replacements = random.sample(
                        list(all_remaining_excess), can_replace
                    )

                    for replacement_id in replacements:
                        first_match = patient_filters[replacement_id][0]
                        start = first_match["start_date"]
                        end = first_match["end_date"]
                        sample_date = start + (end - start) / 2
                        patient_to_sample_date[replacement_id] = sample_date.date()
                        if replacement_id not in patient_to_primary_filter:
                            patient_to_primary_filter[replacement_id] = first_match[
                                "filter_id"
                            ]

                    positive_patients.update(replacements)
                    total_replaced += can_replace
                    logger.info(
                        f"Replaced {can_replace} removed patients from global excess pool"
                    )

            if total_replaced < len(removed_patients):
                still_short = len(removed_patients) - total_replaced
                logger.warning(
                    f"Could not replace all removed patients, still short by {still_short}"
                )

        logger.info(
            f"Final positive patients with valid sample_dates: {len(positive_patients)}"
        )

        # Log sample_date range
        if patient_to_sample_date:
            sample_dates = list(patient_to_sample_date.values())
            min_date = min(sample_dates)
            max_date = max(sample_dates)
            logger.info(f"Sample date range: {min_date} to {max_date}")

        # Group positive patients by sample_date month (YYYY-MM)
        from collections import defaultdict

        patients_by_month = defaultdict(set)
        for patient_id, sample_date in patient_to_sample_date.items():
            month_key = sample_date.strftime("%Y-%m")
            patients_by_month[month_key].add(patient_id)

        logger.info(f"Positive patients span {len(patients_by_month)} unique months")
        for month, count in sorted(patients_by_month.items()):
            logger.info(f"  Month {month}: {count} patients")

        # Perform stratified matching by month
        # This ensures age and active medications are calculated at the same time point
        logger.info("Computing stratification features by month...")

        negative_patients = set()
        unmatched_positive = []
        stratum_stats = {}
        all_negative_by_stratum = {}  # Track remaining negatives across all months

        # Loop over each unique month
        for month_idx, (month_key, positive_ids_in_month) in enumerate(
            sorted(patients_by_month.items()), 1
        ):
            # Use middle of the month as sample_date for this cohort
            # (All patients in this month will have sample_dates within this month)
            year, month = month_key.split("-")
            sample_date_for_month = f"{year}-{month}-15"

            logger.info(
                f"Processing month {month_idx}/{len(patients_by_month)}: {month_key} ({len(positive_ids_in_month)} positive patients)"
            )

            # Run stratification query for this month
            stratification_sql = self.sql_loader.render_template(
                "sampling/patient_stratification_features.sql",
                {
                    **self.default_kwargs,
                    "deceased_filter": "",
                    "sample_date": sample_date_for_month,
                },
            )

            stratification_results = self.conn.execute(stratification_sql).fetchall()

            # Build lookups for this month
            patient_to_stratum = {}
            stratum_to_patients = {}

            for row in stratification_results:
                patient_id = row[0]
                stratum_key = row[8]  # Last column is stratum_key

                patient_to_stratum[patient_id] = stratum_key

                if stratum_key not in stratum_to_patients:
                    stratum_to_patients[stratum_key] = []
                stratum_to_patients[stratum_key].append(patient_id)

            # Separate into negative candidates by stratum (for this month)
            negative_by_stratum = {}

            for stratum_key, patients in stratum_to_patients.items():
                negative_in_stratum = [
                    p for p in patients if p not in positive_patients
                ]
                if negative_in_stratum:
                    negative_by_stratum[stratum_key] = negative_in_stratum

            # Match negatives to positives within this month
            for positive_id in positive_ids_in_month:
                stratum_key = patient_to_stratum.get(positive_id)

                if stratum_key is None:
                    logger.warning(
                        f"Positive patient {positive_id} has no stratum - skipping match"
                    )
                    unmatched_positive.append(positive_id)
                    continue

                # Track stats for this stratum
                if stratum_key not in stratum_stats:
                    stratum_stats[stratum_key] = {
                        "positive": 0,
                        "negative_sampled": 0,
                        "negative_available": 0,
                    }
                stratum_stats[stratum_key]["positive"] += 1

                # Try to sample a negative from the same stratum
                if (
                    stratum_key in negative_by_stratum
                    and negative_by_stratum[stratum_key]
                ):
                    # Sample and remove from available pool
                    sampled_negative = random.choice(negative_by_stratum[stratum_key])
                    negative_by_stratum[stratum_key].remove(sampled_negative)
                    negative_patients.add(sampled_negative)
                    stratum_stats[stratum_key]["negative_sampled"] += 1

                    # Assign the same sample_date as the matched positive
                    patient_to_sample_date[sampled_negative] = patient_to_sample_date[
                        positive_id
                    ]
                else:
                    # No negatives available in this stratum
                    unmatched_positive.append(positive_id)

            # Track remaining negatives from this month for shortfall recovery
            for stratum_key, neg_list in negative_by_stratum.items():
                if stratum_key not in all_negative_by_stratum:
                    all_negative_by_stratum[stratum_key] = []
                all_negative_by_stratum[stratum_key].extend(neg_list)

        logger.info("Completed month-by-month stratified matching")

        # Log how many negatives have sample_dates assigned
        negatives_with_dates = sum(
            1 for pid in negative_patients if pid in patient_to_sample_date
        )
        logger.info(
            f"Negative patients with sample_dates assigned: {negatives_with_dates}/{len(negative_patients)}"
        )

        # Log matching statistics
        positive_processed = len(positive_patients)
        expected_negatives = positive_processed - len(unmatched_positive)
        logger.info("Stratified matching complete:")
        logger.info(f"  - Processed {positive_processed} positive patients")
        logger.info(
            f"  - Matched {len(negative_patients)} negative patients (expected {expected_negatives})"
        )
        logger.info(f"  - Unmatched positive patients: {len(unmatched_positive)}")

        # Log top 10 strata by size
        top_strata = sorted(
            stratum_stats.items(), key=lambda x: x[1]["positive"], reverse=True
        )[:10]
        logger.info("Top 10 strata by positive patient count:")
        for stratum_key, stats in top_strata:
            logger.info(
                f"  {stratum_key}: {stats['positive']} positive, {stats['negative_sampled']} matched, {stats['negative_available']} available"
            )

        if unmatched_positive:
            logger.warning(
                f"Could not find matched negatives for {len(unmatched_positive)} positive patients. "
                f"These strata may have no negative candidates."
            )

        logger.info(
            f"Total negative patients sampled: {len(negative_patients)} (target: {target_negative})"
        )

        # Fill negative shortfall from remaining negative pool
        negative_shortfall = target_negative - len(negative_patients)
        if negative_shortfall > 0:
            # Collect all remaining negatives across all strata (from all months)
            remaining_negatives = []
            for stratum_key, neg_list in all_negative_by_stratum.items():
                remaining_negatives.extend(neg_list)

            # Remove any that are already selected or are positive patients
            available_negatives = [
                p
                for p in remaining_negatives
                if p not in negative_patients and p not in positive_patients
            ]

            logger.info(
                f"Negative shortfall: {negative_shortfall} patients needed, {len(available_negatives)} available from all strata"
            )

            if available_negatives:
                can_recover = min(negative_shortfall, len(available_negatives))
                recovery_sample = random.sample(available_negatives, can_recover)
                negative_patients.update(recovery_sample)

                # Assign sample_dates to recovered negatives (randomly sample from positive patient dates)
                positive_sample_dates = list(patient_to_sample_date.values())
                for recovered_negative in recovery_sample:
                    # Assign a random sample_date from the distribution of positive patients
                    patient_to_sample_date[recovered_negative] = random.choice(
                        positive_sample_dates
                    )

                logger.info(
                    f"Recovered {can_recover} negative patients from remaining pool"
                )
                logger.info(
                    f"Assigned random sample_dates to {can_recover} recovered negative patients"
                )

                if can_recover < negative_shortfall:
                    logger.warning(
                        f"Still short by {negative_shortfall - can_recover} negative patients after recovery"
                    )
            else:
                logger.warning(
                    f"No additional negatives available to fill shortfall of {negative_shortfall}"
                )

        logger.info(
            f"Final negative patients sampled: {len(negative_patients)} (target: {target_negative})"
        )

        # Combine positive and negative patients
        all_sampled_ids = list(positive_patients.union(negative_patients))

        # Filter patient_filters to only include sampled positive patients
        sampled_patient_filters = {
            pid: filters
            for pid, filters in patient_filters.items()
            if pid in positive_patients
        }

        logger.info(
            f"Total patients in balanced sample: {len(all_sampled_ids)} (target: {total_n})"
        )

        # Log final sample_date statistics
        logger.info("Sample date summary:")
        logger.info(
            f"  - Total patients with sample_dates: {len(patient_to_sample_date)}"
        )
        logger.info(
            f"  - Positive patients: {len([p for p in positive_patients if p in patient_to_sample_date])}"
        )
        logger.info(
            f"  - Negative patients: {len([p for p in negative_patients if p in patient_to_sample_date])}"
        )

        if patient_to_sample_date:
            all_dates = list(patient_to_sample_date.values())
            logger.info(f"  - Date range: {min(all_dates)} to {max(all_dates)}")

        # Log primary filter distribution
        logger.info("Primary filter distribution:")
        primary_filter_counts = {}
        for patient_id, filter_id in patient_to_primary_filter.items():
            primary_filter_counts[filter_id] = (
                primary_filter_counts.get(filter_id, 0) + 1
            )
        for filter_id in sorted(primary_filter_counts.keys()):
            logger.info(
                f"  Filter {filter_id}: {primary_filter_counts[filter_id]} patients (primary)"
            )

        return (
            all_sampled_ids,
            sampled_patient_filters,
            patient_to_sample_date,
            patient_to_primary_filter,
        )

    def build_patient_profiles_from_ids(
        self,
        patient_ids: List[int],
        include_aggregations: List[str] = None,
        to_pydantic_model: bool = False,
        patient_filters: Dict[int, List[str]] = None,
        patient_sample_dates: Dict[int, date] = None,
        patient_primary_filters: Dict[int, str] = None,
    ) -> List[Dict] | List[PatientProfile]:
        """
        Build patient profiles for a specific list of patient IDs.

        Args:
            patient_ids: List of FK_Patient_Link_IDs to build profiles for
            include_aggregations: List of aggregation names to include
            to_pydantic_model: Whether to convert to Pydantic models
            patient_filters: Optional dict mapping patient_id to list of matched filter_ids
            patient_sample_dates: Optional dict mapping patient_id to sample_date
            patient_primary_filters: Optional dict mapping patient_id to primary filter_id
                                    (will reorder matched_filters to put primary filter first)

        Returns:
            List of patient profile dictionaries or PatientProfile models
        """

        if not patient_ids:
            logger.warning("No patient IDs provided")
            return []

        # Default to all aggregations if none specified
        if include_aggregations is None:
            include_aggregations = list(self.aggregations.keys())

        # Validate requested aggregations
        invalid = [agg for agg in include_aggregations if agg not in self.aggregations]
        if invalid:
            logger.warning(f"Invalid aggregations requested: {invalid}")
            include_aggregations = [
                agg for agg in include_aggregations if agg in self.aggregations
            ]

        if not include_aggregations:
            logger.error("No valid aggregations to include")
            return []

        # Get view names
        patient_link_view = self.table_views.get(
            "SharedCare.Patient_Link", "SharedCare_Patient_Link"
        )
        patient_view = self.table_views.get("SharedCare.Patient", "SharedCare_Patient")

        # Build CTEs
        ctes = []

        # First CTE: Patient IDs we're processing
        patient_id_values = ",".join(f"({pid})" for pid in patient_ids)
        patient_ids_cte = self.sql_loader.render_template(
            "profile_building/patient_ids.sql", {"patient_id_values": patient_id_values}
        )
        ctes.append(patient_ids_cte)

        # Second CTE: Valid patients with demographics
        patient_batch_cte = self.sql_loader.render_template(
            "profile_building/patient_batch.sql",
            {"patient_view": patient_view, "patient_link_view": patient_link_view},
        )
        ctes.append(patient_batch_cte)

        # Add aggregation CTEs (these remain the same)
        for agg_name in include_aggregations:
            if agg_name in self.aggregations:
                cte = self.build_aggregation_cte(agg_name, self.aggregations[agg_name])
                ctes.append(cte)

        # Build LEFT JOINs and select fields (unchanged)
        joins = []
        select_fields = []

        for agg_name in include_aggregations:
            if agg_name in self.aggregations:
                alias = agg_name[:6]
                joins.append(
                    f"LEFT JOIN {agg_name}_agg {alias} ON pb.PK_Patient_Link_ID = {alias}.PK_Patient_Link_ID"
                )
                select_fields.append(
                    f"COALESCE({alias}.{agg_name}, '[]') as {agg_name}"
                )

        # Build final query
        ctes_joined = ",".join(ctes)
        select_fields_str = (
            f",\n    {', '.join(select_fields)}" if select_fields else ""
        )
        joins_str = "\n".join(joins) if joins else ""

        sql = self.sql_loader.render_template(
            "profile_building/build_patient_profiles.sql",
            {
                "ctes": ctes_joined,
                "select_fields": select_fields_str,
                "joins": joins_str,
            },
        )

        logger.info(f"Building profiles for {len(patient_ids)} patients")
        logger.debug(f"Including aggregations: {include_aggregations}")

        try:
            result = self.conn.execute(sql).fetchall()

            # Get column names
            columns = [desc[0] for desc in self.conn.description]

            # Convert to list of dictionaries
            patient_profiles = []
            for row in result:
                profile = dict(zip(columns, row))
                profile["aggregations"] = {}

                # Parse JSON strings back to objects
                for agg_name in include_aggregations:
                    if agg_name in profile and isinstance(profile[agg_name], str):
                        try:
                            profile["aggregations"][agg_name] = json.loads(
                                profile[agg_name]
                            )
                        except:
                            profile["aggregations"][agg_name] = []

                # Remove the raw aggregation fields from the profile
                for agg_name in include_aggregations:
                    if agg_name in profile:
                        del profile[agg_name]

                # Attach matched filters if provided
                if patient_filters:
                    patient_link_id = profile.get("PK_Patient_Link_ID")
                    profile["matched_filters"] = patient_filters.get(
                        patient_link_id, []
                    )
                else:
                    profile["matched_filters"] = []

                # Reorder matched_filters to put primary filter first
                if patient_primary_filters and profile["matched_filters"]:
                    patient_link_id = profile.get("PK_Patient_Link_ID")
                    primary_filter_id = patient_primary_filters.get(patient_link_id)

                    if primary_filter_id:
                        # Find the primary filter in matched_filters
                        primary_match = None
                        other_matches = []

                        for filter_match in profile["matched_filters"]:
                            if filter_match["filter_id"] == primary_filter_id:
                                primary_match = filter_match
                            else:
                                other_matches.append(filter_match)

                        # Reorder: primary first, then others
                        if primary_match:
                            profile["matched_filters"] = [primary_match] + other_matches

                # Attach sample_date if provided
                if patient_sample_dates:
                    patient_link_id = profile.get("PK_Patient_Link_ID")
                    profile["sample_date"] = patient_sample_dates.get(patient_link_id)

                patient_profiles.append(profile)

            # Log sample_date attachment statistics
            if patient_sample_dates:
                profiles_with_dates = sum(
                    1 for p in patient_profiles if p.get("sample_date") is not None
                )
                logger.info(
                    f"Built {len(patient_profiles)} patient profiles ({profiles_with_dates} with sample_dates)"
                )
            else:
                logger.info(f"Built {len(patient_profiles)} patient profiles")

            if to_pydantic_model:
                return self.convert_to_pydantic_models(patient_profiles)
            else:
                return patient_profiles

        except Exception as e:
            logger.error(f"Error building patient profiles: {e}", exc_info=e)
            return []

    def build_patient_profiles(
        self,
        sample_strategy: str = "all",
        include_aggregations: List[str] = None,
        limit: int = 100,
        offset: int = 0,
        include_deceased: bool = True,
        to_pydantic_model: bool = False,
        seed: float = 0.42,
        # Deprecated parameters for backwards compatibility
        require_smr: bool = False,
        require_balanced_smr: bool = False,
    ) -> List[Dict] | List[PatientProfile]:
        """
        High-level function to build patient profiles with a specific sampling strategy.

        This is now a wrapper that:
        1. Gets patient IDs based on the sampling strategy
        2. Builds profiles for those IDs
        """

        # Handle deprecated parameters
        if require_balanced_smr:
            sample_strategy = "balanced_smr"
        elif require_smr:
            sample_strategy = "smr"

        # Step 1: Get patient IDs
        patient_ids = self.get_patient_sample(
            sample_strategy=sample_strategy,
            limit=limit,
            offset=offset,
            include_deceased=include_deceased,
            seed=seed,
        )

        if not patient_ids:
            logger.warning("No patients found for the specified criteria")
            return []

        # Step 2: Build profiles for these IDs
        return self.build_patient_profiles_from_ids(
            patient_ids=patient_ids,
            include_aggregations=include_aggregations,
            to_pydantic_model=to_pydantic_model,
        )

    def convert_to_pydantic_models(
        self, patient_profiles: list[dict]
    ) -> list[PatientProfile]:
        """
        Convert patient profile dictionaries to Pydantic models.

        Handles validation errors gracefully by skipping problematic profiles
        and logging which patients failed validation.
        """
        converted_profiles = []
        failed_count = 0

        for x in patient_profiles:
            try:
                profile = (
                    PatientProfile(**x)
                    .add_events_from_aggregations(x["aggregations"])
                    .sort_events_by_date()
                )
                converted_profiles.append(profile)

            except Exception as e:
                failed_count += 1
                patient_id = x.get("PK_Patient_Link_ID", "unknown")
                logger.warning(
                    f"Failed to convert patient {patient_id}: {str(e)[:200]}"
                )

        if failed_count > 0:
            logger.warning(
                f"Converted {len(converted_profiles)}/{len(patient_profiles)} profiles successfully. "
                f"{failed_count} profiles failed and were skipped."
            )

        return converted_profiles

    def export_jsonl(
        self, profiles: List[Dict], output_path: str = "patient_profiles.jsonl"
    ):
        """Export patient profiles as JSONL for LLM consumption"""
        if not profiles:
            logger.error("No profiles to export")
            return

        with open(output_path, "w") as f:
            for profile in profiles:
                f.write(json.dumps(profile, default=str) + "\n")

        logger.info(f"Exported {len(profiles)} patient profiles to {output_path}")

    def save_to_parquet(
        self, profiles: List[Dict], output_path: str = "patient_profiles.parquet"
    ):
        """Save patient profiles to parquet file using DuckDB"""
        if not profiles:
            logger.error("No profiles to save")
            return

        # Create a copy to avoid modifying the original
        profiles_copy = []
        for profile in profiles:
            profile_copy = profile.copy()
            # Convert lists to JSON strings for storage
            for key, value in profile_copy.items():
                if isinstance(value, list):
                    profile_copy[key] = json.dumps(value)
            profiles_copy.append(profile_copy)

        # Create temporary table and export
        self.conn.execute(
            "CREATE OR REPLACE TABLE temp_profiles AS SELECT * FROM ?", [profiles_copy]
        )
        self.conn.execute(f"COPY temp_profiles TO '{output_path}' (FORMAT PARQUET)")
        self.conn.execute("DROP TABLE temp_profiles")

        logger.info(f"Saved {len(profiles)} patient profiles to {output_path}")

    def process_in_batches(
        self,
        include_aggregations: List[str],
        batch_size: int = 1000,
        output_prefix: str = "patient_batch",
        output_format: str = "jsonl",
        max_batches: int = None,
        include_deceased: bool = True,
    ):
        """
        Process all patients in batches to handle large datasets

        Args:
            include_aggregations: List of aggregation names to include
            batch_size: Number of patients per batch
            output_prefix: Prefix for output files
            output_format: 'jsonl' or 'parquet'
            max_batches: Maximum number of batches to process (None for all)
            include_deceased: Whether to include deceased patients
        """
        total_patients = self.get_total_patient_count(
            include_deceased=include_deceased,
        )

        logger.info(f"Total patients to process: {total_patients:,}")

        num_batches = (total_patients + batch_size - 1) // batch_size
        if max_batches:
            num_batches = min(num_batches, max_batches)

        processed_count = 0

        for batch_num in range(num_batches):
            offset = batch_num * batch_size
            logger.info(
                f"\nProcessing batch {batch_num + 1}/{num_batches} (offset: {offset})"
            )

            profiles = self.build_patient_profiles(
                include_aggregations=include_aggregations,
                limit=batch_size,
                offset=offset,
                include_deceased=include_deceased,
            )

            if profiles:
                processed_count += len(profiles)

                if output_format == "jsonl":
                    output_file = f"{output_prefix}_{batch_num + 1:04d}.jsonl"
                    self.export_jsonl(profiles, output_file)
                elif output_format == "parquet":
                    output_file = f"{output_prefix}_{batch_num + 1:04d}.parquet"
                    self.save_to_parquet(profiles, output_file)

        logger.info(f"\nCompleted processing {num_batches} batches")
        logger.info(f"Total patients processed: {processed_count:,}")

    def get_aggregation_info(self) -> Dict[str, Dict]:
        """Get information about available aggregations"""
        return self.aggregations.copy()


def main():
    """Example usage of the ModularPatientDataProcessor"""

    # Initialize processor
    processor = ModularPatientDataProcessor()

    # Get total patient count
    total_count = processor.get_total_patient_count()
    print(f"Total valid patients: {total_count:,}")

    # Get a sample batch with medications and events
    print("\nBuilding sample patient profiles...")
    profiles = processor.build_patient_profiles(
        include_aggregations=["medications", "gp_events"],
        limit=5,
        offset=0,
        include_deceased=True,
    )

    if profiles:
        print(f"\nGenerated {len(profiles)} patient profiles")

        # Show sample structure
        sample = profiles[0].copy()
        # Truncate lists for display
        for key, value in sample.items():
            if isinstance(value, list) and len(value) > 2:
                sample[key] = value[:2] + [f"... ({len(value)} total items)"]

        print("\nSample patient profile structure:")
        print(json.dumps(sample, indent=2, default=str))

        # Export to JSONL
        processor.export_jsonl(profiles[:2], "sample_profiles.jsonl")
        print("\nExported sample profiles to sample_profiles.jsonl")

    print("\nProcessor initialized successfully!")


if __name__ == "__main__":
    main()
