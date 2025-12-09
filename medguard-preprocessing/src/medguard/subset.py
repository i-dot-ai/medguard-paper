import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Set

import duckdb

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatasetSubsetGenerator:
    """
    Generate a representative subset of the healthcare dataset by sampling patients
    from Patient_Link (master patient index) and filtering all related tables to
    only include records for those patients.
    """

    def __init__(self, source_path: str, target_path: str):
        self.source_path = Path(source_path)
        self.target_path = Path(target_path)
        self.conn = duckdb.connect()

        # Patient linking patterns - maps table names to their patient link columns
        self.patient_link_columns = {
            "SharedCare.Patient": "FK_Patient_Link_ID",
            "SharedCare.GP_Appointments": "FK_Patient_Link_ID",
            "SharedCare.GP_Encounters": "FK_Patient_Link_ID",
            "SharedCare.GP_Events": "FK_Patient_Link_ID",
            "SharedCare.GP_Medications": "FK_Patient_Link_ID",
            "SharedCare.Acute_Inpatients": "FK_Patient_Link_ID",
            "SharedCare.Acute_Outpatients": "FK_Patient_Link_ID",
            "SharedCare.Acute_AE": "FK_Patient_Link_ID",
            "SharedCare.Acute_Allergies": "FK_Patient_Link_ID",
            "SharedCare.Acute_Coding": "FK_Patient_Link_ID",
            "SharedCare.Acute_Coding_Clinician": "FK_Patient_Link_ID",
            "SharedCare.SocialCare_Alerts": "FK_Patient_Link_ID",
            "SharedCare.SocialCare_CarePlans": "FK_Patient_Link_ID",
            "SharedCare.SocialCare_Classifications": "FK_Patient_Link_ID",
            "SharedCare.SocialCare_Disabilities": "FK_Patient_Link_ID",
            "SharedCare.SocialCare_Events": "FK_Patient_Link_ID",
            "SharedCare.SocialCare_Practitioners": "FK_Patient_Link_ID",
            "SharedCare.SocialCare_Referrals": "FK_Patient_Link_ID",
            "SharedCare.SocialCare_RelatedPersons": "FK_Patient_Link_ID",
            "SharedCare.SocialCare_ServiceProvisions": "FK_Patient_Link_ID",
            "SUS.ECDS_Coding_Diagnoses_V4": "FK_Patient_Link_ID",
            "SUS.ECDS_Coding_Investigation_V4": "FK_Patient_Link_ID",
            "SUS.ECDS_Coding_Treatment_V4": "FK_Patient_Link_ID",
            "SUS.ECDS_V4": "FK_Patient_Link_ID",
            "SUS.SUS_All_Coding": "FK_Patient_Link_ID",
            "SUS.SUS_APC_Episodes": "FK_Patient_Link_ID",
            "SUS.SUS_APC_Spells": "FK_Patient_Link_ID",
            "SUS.SUS_EM": "FK_Patient_Link_ID",
            "SUS.SUS_OP": "FK_Patient_Link_ID",
        }

        # Patient_Link is special - we filter by PK not FK
        self.patient_link_primary_key = {
            "SharedCare.Patient_Link": "PK_Patient_Link_ID"
        }

    def discover_source_tables(self) -> Dict[str, str]:
        """Discover all available tables in the source directory"""
        tables = {}

        extract_path = self.source_path / "PopHealth" / "Medguard" / "Extract"

        if not extract_path.exists():
            logger.error(f"Source extract path not found: {extract_path}")
            return tables

        for table_dir in extract_path.iterdir():
            if table_dir.is_dir():
                v1_path = table_dir / "v1_0"
                if v1_path.exists():
                    parquet_files = list(v1_path.glob("*.parquet"))
                    if parquet_files:
                        pattern = str(v1_path / "*.parquet")
                        tables[table_dir.name] = pattern
                        logger.info(
                            f"Found source table {table_dir.name} with {len(parquet_files)} files"
                        )

        logger.info(f"Discovered {len(tables)} source tables")
        return tables

    def load_existing_patient_ids(self, existing_subset_path: str) -> Set[int]:
        """
        Load patient IDs from an existing subset to exclude them from new sampling

        Args:
            existing_subset_path: Path to existing subset directory

        Returns:
            Set of PK_Patient_Link_ID values from the existing subset
        """

        existing_path = Path(existing_subset_path)
        patient_link_pattern = str(
            existing_path
            / "PopHealth"
            / "Medguard"
            / "Extract"
            / "SharedCare.Patient_Link"
            / "v1_0"
            / "*.parquet"
        )

        logger.info(f"Loading existing patient IDs from: {existing_subset_path}")

        try:
            # Load existing patient link table
            self.conn.execute(
                f"CREATE OR REPLACE VIEW existing_patient_link AS SELECT * FROM '{patient_link_pattern}'"
            )

            # Get all patient IDs
            existing_ids_query = "SELECT PK_Patient_Link_ID FROM existing_patient_link"
            existing_ids = {
                row[0] for row in self.conn.execute(existing_ids_query).fetchall()
            }

            logger.info(f"Loaded {len(existing_ids):,} existing patient IDs to exclude")
            return existing_ids

        except Exception as e:
            logger.error(f"Error loading existing patient IDs: {e}")
            logger.warning("Continuing without exclusion - there may be overlap!")
            return set()

    @staticmethod
    def verify_no_overlap(subset_path1: str, subset_path2: str) -> bool:
        """
        Verify that two patient subsets have no overlapping patient IDs

        Args:
            subset_path1: Path to first subset
            subset_path2: Path to second subset

        Returns:
            True if no overlap, False if overlap detected
        """

        logger.info("Verifying no overlap between subsets...")
        logger.info(f"  Subset 1: {subset_path1}")
        logger.info(f"  Subset 2: {subset_path2}")

        conn = duckdb.connect()

        try:
            # Load patient IDs from first subset
            path1 = Path(subset_path1)
            pattern1 = str(
                path1
                / "PopHealth"
                / "Medguard"
                / "Extract"
                / "SharedCare.Patient_Link"
                / "v1_0"
                / "*.parquet"
            )
            conn.execute(
                f"CREATE OR REPLACE VIEW subset1 AS SELECT * FROM '{pattern1}'"
            )
            ids1 = {
                row[0]
                for row in conn.execute(
                    "SELECT PK_Patient_Link_ID FROM subset1"
                ).fetchall()
            }

            # Load patient IDs from second subset
            path2 = Path(subset_path2)
            pattern2 = str(
                path2
                / "PopHealth"
                / "Medguard"
                / "Extract"
                / "SharedCare.Patient_Link"
                / "v1_0"
                / "*.parquet"
            )
            conn.execute(
                f"CREATE OR REPLACE VIEW subset2 AS SELECT * FROM '{pattern2}'"
            )
            ids2 = {
                row[0]
                for row in conn.execute(
                    "SELECT PK_Patient_Link_ID FROM subset2"
                ).fetchall()
            }

            # Check for overlap
            overlap = ids1.intersection(ids2)

            logger.info(f"  Subset 1: {len(ids1):,} patients")
            logger.info(f"  Subset 2: {len(ids2):,} patients")
            logger.info(f"  Overlap: {len(overlap):,} patients")

            if len(overlap) == 0:
                logger.info(
                    "✓ SUCCESS: No overlap detected - subsets are completely disjoint!"
                )
                return True
            else:
                logger.error(
                    f"✗ FAILURE: {len(overlap):,} patients appear in both subsets!"
                )
                logger.error(f"  Example overlapping IDs: {list(overlap)[:10]}")
                return False

        except Exception as e:
            logger.error(f"Error verifying overlap: {e}")
            return False
        finally:
            conn.close()

    def sample_patients(
        self,
        sample_size: int = 50000,
        stratify: bool = True,
        random_seed: int = 42,
        include_opted_out: bool = False,
        include_deceased: bool = True,
        include_restricted: bool = False,
        exclude_patient_ids: Optional[Set[int]] = None,
    ) -> Set[int]:
        """
        Sample patients from the Patient_Link table using stratified sampling

        Args:
            sample_size: Number of patients to sample
            stratify: Whether to use stratified sampling by age/sex
            random_seed: Random seed for reproducibility
            include_opted_out: Whether to include patients who opted out
            include_deceased: Whether to include deceased patients
            include_restricted: Whether to include restricted access patients
            exclude_patient_ids: Set of patient IDs to exclude (e.g., from existing subsets)

        Returns:
            Set of PK_Patient_Link_ID values for sampled patients
        """

        logger.info(f"Sampling {sample_size:,} patients from Patient_Link table...")

        if exclude_patient_ids:
            logger.info(
                f"Excluding {len(exclude_patient_ids):,} existing patient IDs from sampling"
            )

        # Set random seed for reproducibility
        random.seed(random_seed)

        # Load patient link table
        patient_link_pattern = str(
            self.source_path
            / "PopHealth"
            / "Medguard"
            / "Extract"
            / "SharedCare.Patient_Link"
            / "v1_0"
            / "*.parquet"
        )

        try:
            # Create view of patient link table
            self.conn.execute(
                f"CREATE OR REPLACE VIEW source_patient_link AS SELECT * FROM '{patient_link_pattern}'"
            )

            # Build filter conditions for valid patients
            where_conditions = [
                "(Merged != 'Y' OR Merged IS NULL)",  # Exclude merged patients
                "(Deleted != 'Y' OR Deleted IS NULL)",  # Exclude deleted patients
            ]

            if not include_opted_out:
                where_conditions.append("(OptedOut != 'Y' OR OptedOut IS NULL)")

            if not include_deceased:
                where_conditions.append("(Deceased != 'Y' OR Deceased IS NULL)")

            if not include_restricted:
                where_conditions.append("(Restricted != 'Y' OR Restricted IS NULL)")

            # Add exclusion for existing patient IDs
            if exclude_patient_ids:
                excluded_ids_str = ",".join(map(str, exclude_patient_ids))
                where_conditions.append(
                    f"PK_Patient_Link_ID NOT IN ({excluded_ids_str})"
                )

            where_clause = " AND ".join(where_conditions)

            # Get total valid patient count
            total_count_sql = f"""
            SELECT COUNT(*) 
            FROM source_patient_link 
            WHERE {where_clause}
            """
            total_count = self.conn.execute(total_count_sql).fetchone()[0]

            logger.info(f"Total valid patients available: {total_count:,}")
            logger.info(
                f"Filters applied: opted_out={include_opted_out}, deceased={include_deceased}, restricted={include_restricted}"
            )

            if sample_size >= total_count:
                logger.warning(
                    f"Sample size ({sample_size:,}) >= total patients ({total_count:,}). Using all patients."
                )
                sample_size = total_count

            if stratify and total_count > sample_size:
                # Stratified sampling by age group and sex (requires joining to Patient table)
                sampled_patients = self._stratified_sampling(
                    sample_size, where_clause, exclude_patient_ids
                )
            else:
                # Simple random sampling from Patient_Link
                sampled_patients = self._simple_random_sampling(
                    sample_size, where_clause, exclude_patient_ids
                )

            logger.info(f"Successfully sampled {len(sampled_patients):,} patients")
            return sampled_patients

        except Exception as e:
            logger.error(f"Error sampling patients: {e}")
            raise

    def _stratified_sampling(
        self,
        sample_size: int,
        where_clause: str,
        exclude_patient_ids: Optional[Set[int]] = None,
    ) -> Set[int]:
        """Perform stratified sampling by age group and sex (exclusions already in where_clause)"""

        logger.info("Performing stratified sampling by age and sex...")

        # Need to join Patient_Link to Patient for demographics
        patient_pattern = str(
            self.source_path
            / "PopHealth"
            / "Medguard"
            / "Extract"
            / "SharedCare.Patient"
            / "v1_0"
            / "*.parquet"
        )
        self.conn.execute(
            f"CREATE OR REPLACE VIEW source_patient AS SELECT * FROM '{patient_pattern}'"
        )

        # Define age groups and get population distribution
        strata_sql = f"""
        WITH valid_patients AS (
            SELECT pl.PK_Patient_Link_ID
            FROM source_patient_link pl
            WHERE {where_clause}
        ),
        patient_demographics AS (
            SELECT DISTINCT ON (vp.PK_Patient_Link_ID)
                vp.PK_Patient_Link_ID,
                p.Dob,
                p.Sex
            FROM valid_patients vp
            LEFT JOIN source_patient p ON vp.PK_Patient_Link_ID = p.FK_Patient_Link_ID
            ORDER BY vp.PK_Patient_Link_ID, p.Dob NULLS LAST, p.Sex NULLS LAST
        )
        SELECT
            CASE
                WHEN pd.Dob IS NULL THEN 'Unknown Age'
                WHEN DATEDIFF('year', pd.Dob, CURRENT_DATE) < 18 THEN '0-17'
                WHEN DATEDIFF('year', pd.Dob, CURRENT_DATE) < 30 THEN '18-29'
                WHEN DATEDIFF('year', pd.Dob, CURRENT_DATE) < 45 THEN '30-44'
                WHEN DATEDIFF('year', pd.Dob, CURRENT_DATE) < 65 THEN '45-64'
                WHEN DATEDIFF('year', pd.Dob, CURRENT_DATE) < 80 THEN '65-79'
                ELSE '80+'
            END as age_group,
            COALESCE(pd.Sex, 'Unknown') as sex,
            COUNT(*) as count,
            ARRAY_AGG(pd.PK_Patient_Link_ID) as patient_ids
        FROM patient_demographics pd
        GROUP BY age_group, sex
        ORDER BY age_group, sex
        """

        strata_data = self.conn.execute(strata_sql).fetchall()

        total_pop = sum(row[2] for row in strata_data)
        sampled_patients = set()

        # Handle edge case: no patients available
        if total_pop == 0:
            logger.error(
                "No patients available for stratified sampling after applying filters"
            )
            return sampled_patients

        # If requesting more than available, cap at total population
        if sample_size > total_pop:
            logger.warning(
                f"Requested sample size ({sample_size:,}) exceeds total population ({total_pop:,})"
            )
            logger.warning(
                f"Reducing sample size to {total_pop:,} (all available patients)"
            )
            sample_size = total_pop

        # Use largest remainder method for exact allocation without rounding errors
        # Step 1: Calculate exact proportions and initial floor allocations
        allocations_with_remainders = []
        total_allocated = 0

        for age_group, sex, count, patient_ids in strata_data:
            exact_proportion = (count / total_pop) * sample_size
            floor_allocation = int(exact_proportion)  # Floor value
            remainder = exact_proportion - floor_allocation

            # Cap allocation at available patients in stratum
            floor_allocation = min(floor_allocation, count)

            allocations_with_remainders.append(
                {
                    "age_group": age_group,
                    "sex": sex,
                    "count": count,
                    "patient_ids": patient_ids,
                    "allocation": floor_allocation,
                    "remainder": remainder,
                }
            )
            total_allocated += floor_allocation

        # Step 2: Distribute remaining samples using largest remainder method
        remaining_to_allocate = sample_size - total_allocated

        if remaining_to_allocate > 0:
            # Sort by remainder (descending) to give priority to largest remainders
            sorted_by_remainder = sorted(
                allocations_with_remainders, key=lambda x: x["remainder"], reverse=True
            )

            for stratum in sorted_by_remainder:
                if remaining_to_allocate <= 0:
                    break

                # Only add 1 more if this stratum has capacity
                if stratum["allocation"] < stratum["count"]:
                    stratum["allocation"] += 1
                    remaining_to_allocate -= 1

        # Step 3: If still short (due to small strata), sample more from largest strata
        if remaining_to_allocate > 0:
            logger.warning(
                f"Still {remaining_to_allocate} samples short after largest remainder allocation"
            )

            # Sort by available capacity (count - allocation)
            sorted_by_capacity = sorted(
                allocations_with_remainders,
                key=lambda x: x["count"] - x["allocation"],
                reverse=True,
            )

            for stratum in sorted_by_capacity:
                if remaining_to_allocate <= 0:
                    break

                available = stratum["count"] - stratum["allocation"]
                can_add = min(available, remaining_to_allocate)

                if can_add > 0:
                    stratum["allocation"] += can_add
                    remaining_to_allocate -= can_add
                    logger.info(
                        f"  Added {can_add} extra samples to {stratum['age_group']} {stratum['sex']} to meet target"
                    )

        # Sample from each stratum with validation
        total_sampled = 0

        for stratum in allocations_with_remainders:
            age_group = stratum["age_group"]
            sex = stratum["sex"]
            count = stratum["count"]
            patient_ids = stratum["patient_ids"]
            stratum_sample_size = stratum["allocation"]

            # Validation: ensure we don't over-allocate any stratum
            if stratum_sample_size > count:
                logger.error(
                    f"ALLOCATION ERROR: {age_group} {sex} allocated {stratum_sample_size} but only {count} available"
                )
                raise ValueError(
                    f"Stratum over-allocated: {stratum_sample_size} > {count}"
                )

            if stratum_sample_size > 0:
                # Random sample from this stratum
                sampled_ids = random.sample(patient_ids, stratum_sample_size)
                sampled_patients.update(sampled_ids)
                total_sampled += stratum_sample_size

                proportion = (stratum_sample_size / count * 100) if count > 0 else 0
                logger.info(
                    f"  {age_group} {sex}: sampled {stratum_sample_size:,} from {count:,} ({proportion:.1f}%)"
                )

        # Comprehensive validation
        final_sample_size = len(sampled_patients)

        # Check 1: Final size matches what we allocated (detects duplicate IDs across strata)
        if total_sampled != final_sample_size:
            logger.error(
                f"VALIDATION ERROR: Allocated {total_sampled} but got {final_sample_size} unique patients"
            )
            logger.error(
                "This suggests duplicate patient IDs across strata - data integrity issue"
            )
            raise ValueError(
                f"Sample size mismatch: {total_sampled} allocated != {final_sample_size} unique"
            )

        # Check 2: Final size matches target (should always be true after cap above)
        if final_sample_size != sample_size:
            logger.error(
                f"VALIDATION ERROR: Got {final_sample_size:,} patients but expected {sample_size:,}"
            )
            raise ValueError(
                f"Sample size mismatch: {final_sample_size} != {sample_size}"
            )

        logger.info(
            f"✓ Validation passed: {final_sample_size:,} unique patients sampled"
        )
        return sampled_patients

    def _simple_random_sampling(
        self,
        sample_size: int,
        where_clause: str,
        exclude_patient_ids: Optional[Set[int]] = None,
    ) -> Set[int]:
        """Perform simple random sampling (exclusions already in where_clause)"""

        logger.info("Performing simple random sampling...")

        # Get all valid patient IDs from Patient_Link
        patient_ids_sql = f"""
        SELECT PK_Patient_Link_ID 
        FROM source_patient_link 
        WHERE {where_clause}
        """

        patient_ids = [row[0] for row in self.conn.execute(patient_ids_sql).fetchall()]

        # Random sample
        sampled_ids = random.sample(patient_ids, min(sample_size, len(patient_ids)))

        return set(sampled_ids)

    def create_subset_directory_structure(self):
        """Create the target directory structure matching the source"""

        target_extract_path = self.target_path / "PopHealth" / "Medguard" / "Extract"
        target_extract_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for each table
        source_tables = self.discover_source_tables()

        for table_name in source_tables.keys():
            table_target_dir = target_extract_path / table_name / "v1_0"
            table_target_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {table_target_dir}")

    def filter_and_save_table(
        self, table_name: str, sampled_patient_ids: Set[int], chunk_size: int = 100000
    ):
        """
        Filter a table to only include records for sampled patients and save to target location

        Args:
            table_name: Name of the table to filter
            sampled_patient_ids: Set of patient IDs to keep
            chunk_size: Number of rows to process at a time
        """

        logger.info(f"Processing table: {table_name}")

        # Source and target paths
        source_pattern = str(
            self.source_path
            / "PopHealth"
            / "Medguard"
            / "Extract"
            / table_name
            / "v1_0"
            / "*.parquet"
        )
        target_dir = (
            self.target_path
            / "PopHealth"
            / "Medguard"
            / "Extract"
            / table_name
            / "v1_0"
        )

        try:
            # Create view of source table
            view_name = f"source_{table_name.replace('.', '_')}"
            self.conn.execute(
                f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM '{source_pattern}'"
            )

            # Get total rows in source
            total_rows = self.conn.execute(
                f"SELECT COUNT(*) FROM {view_name}"
            ).fetchone()[0]
            logger.info(f"  Source table has {total_rows:,} rows")

            if total_rows == 0:
                logger.warning(f"  Table {table_name} is empty, skipping...")
                return

            # Determine how to filter this table
            if table_name == "SharedCare.Patient_Link":
                # For Patient_Link table, filter by PK_Patient_Link_ID directly
                filter_column = "PK_Patient_Link_ID"
                where_clause = f"WHERE {filter_column} IN ({','.join(map(str, sampled_patient_ids))})"

            elif table_name in self.patient_link_columns:
                # For tables linked by FK_Patient_Link_ID
                filter_column = self.patient_link_columns[table_name]
                where_clause = f"WHERE {filter_column} IN ({','.join(map(str, sampled_patient_ids))})"

            else:
                # For tables we don't know how to link, copy all data (reference tables, etc.)
                logger.warning(
                    f"  Unknown patient linking for {table_name}, copying all data"
                )
                where_clause = ""

            # Check if filter column exists
            if where_clause:
                try:
                    # Test if column exists
                    self.conn.execute(
                        f"SELECT {filter_column} FROM {view_name} LIMIT 1"
                    )
                except:
                    logger.warning(
                        f"  Column {filter_column} not found in {table_name}, copying all data"
                    )
                    where_clause = ""

            # Build filtered query
            if where_clause:
                filter_sql = f"SELECT * FROM {view_name} {where_clause}"
            else:
                filter_sql = f"SELECT * FROM {view_name}"

            # Execute and save
            target_file = (
                target_dir / f"filtered_{table_name.replace('.', '_')}.parquet"
            )

            copy_sql = f"COPY ({filter_sql}) TO '{target_file}' (FORMAT PARQUET)"
            self.conn.execute(copy_sql)

            # Get filtered row count
            filtered_count = self.conn.execute(
                f"SELECT COUNT(*) FROM ({filter_sql})"
            ).fetchone()[0]

            reduction_pct = (
                ((total_rows - filtered_count) / total_rows * 100)
                if total_rows > 0
                else 0
            )
            logger.info(
                f"  Filtered to {filtered_count:,} rows ({reduction_pct:.1f}% reduction)"
            )
            logger.info(f"  Saved to: {target_file}")

        except Exception as e:
            logger.error(f"  Error processing {table_name}: {e}")
            raise

    def generate_subset(
        self,
        sample_size: int = 50000,
        stratify: bool = True,
        random_seed: int = 42,
        include_opted_out: bool = False,
        include_deceased: bool = True,
        include_restricted: bool = False,
        exclude_patient_ids: Optional[Set[int]] = None,
    ):
        """
        Generate the complete dataset subset

        Args:
            sample_size: Number of patients to sample
            stratify: Whether to use stratified sampling
            random_seed: Random seed for reproducibility
            include_opted_out: Whether to include patients who opted out
            include_deceased: Whether to include deceased patients
            include_restricted: Whether to include restricted access patients
            exclude_patient_ids: Set of patient IDs to exclude (e.g., from existing subsets)
        """

        start_time = datetime.now()
        logger.info(f"Starting dataset subset generation at {start_time}")
        logger.info(f"Source: {self.source_path}")
        logger.info(f"Target: {self.target_path}")
        logger.info(f"Sample size: {sample_size:,} patients")
        logger.info(
            f"Inclusion settings: opted_out={include_opted_out}, deceased={include_deceased}, restricted={include_restricted}"
        )

        if exclude_patient_ids:
            logger.info(
                f"Exclusion: {len(exclude_patient_ids):,} existing patient IDs will be excluded"
            )

        try:
            # Step 1: Sample patients from Patient_Link
            sampled_patient_ids = self.sample_patients(
                sample_size,
                stratify,
                random_seed,
                include_opted_out,
                include_deceased,
                include_restricted,
                exclude_patient_ids,
            )

            # Step 2: Create directory structure
            logger.info("Creating target directory structure...")
            self.create_subset_directory_structure()

            # Step 3: Discover and process all tables
            source_tables = self.discover_source_tables()
            logger.info(f"Processing {len(source_tables)} tables...")

            # Process Patient_Link table first (most important)
            if "SharedCare.Patient_Link" in source_tables:
                self.filter_and_save_table(
                    "SharedCare.Patient_Link", sampled_patient_ids
                )

            # Then process Patient table
            if "SharedCare.Patient" in source_tables:
                self.filter_and_save_table("SharedCare.Patient", sampled_patient_ids)

            # Process all other tables
            for table_name in source_tables:
                if table_name not in ["SharedCare.Patient_Link", "SharedCare.Patient"]:
                    self.filter_and_save_table(table_name, sampled_patient_ids)

            # Step 4: Generate summary
            self.generate_subset_summary(sampled_patient_ids, sample_size)

            end_time = datetime.now()
            duration = end_time - start_time
            logger.info(f"Subset generation completed in {duration}")
            logger.info(f"Target directory ready: {self.target_path}")

        except Exception as e:
            logger.error(f"Failed to generate subset: {e}")
            raise

    def generate_subset_summary(
        self, sampled_patient_ids: Set[int], requested_sample_size: int
    ):
        """Generate a summary of the created subset"""

        summary_file = self.target_path / "subset_summary.txt"

        with open(summary_file, "w") as f:
            f.write("HEALTHCARE DATASET SUBSET SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source: {self.source_path}\n")
            f.write(f"Target: {self.target_path}\n\n")
            f.write(f"Requested sample size: {requested_sample_size:,} patients\n")
            f.write(f"Actual sample size: {len(sampled_patient_ids):,} patients\n")
            f.write(
                f"Sampling method: {'Stratified by age/sex' if len(sampled_patient_ids) < requested_sample_size else 'Complete population'}\n\n"
            )

            # Table summary
            f.write("TABLE SUMMARY:\n")
            f.write("-" * 30 + "\n")

            target_extract = self.target_path / "PopHealth" / "Medguard" / "Extract"

            table_stats = []

            for table_dir in sorted(target_extract.iterdir()):
                if table_dir.is_dir():
                    v1_path = table_dir / "v1_0"
                    if v1_path.exists():
                        parquet_files = list(v1_path.glob("*.parquet"))
                        if parquet_files:
                            # Get row count
                            try:
                                pattern = str(v1_path / "*.parquet")
                                view_name = (
                                    f"summary_{table_dir.name.replace('.', '_')}"
                                )
                                self.conn.execute(
                                    f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM '{pattern}'"
                                )
                                count = self.conn.execute(
                                    f"SELECT COUNT(*) FROM {view_name}"
                                ).fetchone()[0]

                                # For patient-linked tables, also get unique patient count
                                if table_dir.name in self.patient_link_columns:
                                    link_col = self.patient_link_columns[table_dir.name]
                                    unique_patients = self.conn.execute(
                                        f"SELECT COUNT(DISTINCT {link_col}) FROM {view_name} WHERE {link_col} IS NOT NULL"
                                    ).fetchone()[0]
                                    table_stats.append(
                                        {
                                            "table": table_dir.name,
                                            "rows": count,
                                            "unique_patients": unique_patients,
                                        }
                                    )
                                else:
                                    table_stats.append(
                                        {
                                            "table": table_dir.name,
                                            "rows": count,
                                            "unique_patients": None,
                                        }
                                    )
                            except:
                                table_stats.append(
                                    {
                                        "table": table_dir.name,
                                        "rows": "ERROR",
                                        "unique_patients": None,
                                    }
                                )

            # Write table statistics
            for stat in table_stats:
                if stat["unique_patients"] is not None:
                    f.write(
                        f"{stat['table']:<40}: {stat['rows']:>10,} rows ({stat['unique_patients']:,} patients)\n"
                    )
                else:
                    if isinstance(stat["rows"], int):
                        f.write(f"{stat['table']:<40}: {stat['rows']:>10,} rows\n")
                    else:
                        f.write(f"{stat['table']:<40}: {'ERROR':<10}\n")

            # Analyze patient demographics in subset
            f.write("\nPATIENT DEMOGRAPHICS IN SUBSET:\n")
            f.write("-" * 30 + "\n")

            try:
                # Get age/sex distribution from subset
                patient_link_pattern = str(
                    target_extract / "SharedCare.Patient_Link" / "v1_0" / "*.parquet"
                )
                patient_pattern = str(
                    target_extract / "SharedCare.Patient" / "v1_0" / "*.parquet"
                )

                self.conn.execute(
                    f"CREATE OR REPLACE VIEW subset_patient_link AS SELECT * FROM '{patient_link_pattern}'"
                )
                self.conn.execute(
                    f"CREATE OR REPLACE VIEW subset_patient AS SELECT * FROM '{patient_pattern}'"
                )

                demo_sql = """
                SELECT 
                    CASE 
                        WHEN p.Dob IS NULL THEN 'Unknown'
                        WHEN DATEDIFF('year', p.Dob, CURRENT_DATE) < 18 THEN '0-17'
                        WHEN DATEDIFF('year', p.Dob, CURRENT_DATE) < 30 THEN '18-29'
                        WHEN DATEDIFF('year', p.Dob, CURRENT_DATE) < 45 THEN '30-44'
                        WHEN DATEDIFF('year', p.Dob, CURRENT_DATE) < 65 THEN '45-64'
                        WHEN DATEDIFF('year', p.Dob, CURRENT_DATE) < 80 THEN '65-79'
                        ELSE '80+' 
                    END as age_group,
                    COALESCE(p.Sex, 'Unknown') as sex,
                    COUNT(*) as count
                FROM subset_patient_link pl
                LEFT JOIN subset_patient p ON pl.PK_Patient_Link_ID = p.FK_Patient_Link_ID
                GROUP BY age_group, sex
                ORDER BY age_group, sex
                """

                demo_data = self.conn.execute(demo_sql).fetchall()

                for age_group, sex, count in demo_data:
                    f.write(f"  {age_group:<10} {sex:<8}: {count:>6,}\n")

            except Exception as e:
                f.write(f"  Could not analyze demographics: {e}\n")

            f.write("\nSubset is ready for analysis!\n")
            f.write(
                f"Use this path in ModularPatientDataProcessor: {self.target_path}\n"
            )

        logger.info(f"Summary saved to: {summary_file}")


def main():
    """Example usage of the DatasetSubsetGenerator"""

    # Configuration
    source_path = "patient-data"  # Your original data path
    target_path = "patient-data-subset"  # Where to save the subset
    sample_size = 50000  # Number of patients to sample

    # Create subset generator
    generator = DatasetSubsetGenerator(source_path, target_path)

    # Generate the subset with specific inclusion criteria
    generator.generate_subset(
        sample_size=sample_size,
        stratify=True,  # Use stratified sampling
        random_seed=42,  # For reproducibility
        include_opted_out=False,  # Respect opt-outs
        include_deceased=True,  # Include deceased patients
        include_restricted=False,  # Exclude restricted access
    )

    print("\nSubset generation complete!")
    print(
        "You can now use the subset by initializing ModularPatientDataProcessor with:"
    )
    print(f"processor = ModularPatientDataProcessor('{target_path}')")


if __name__ == "__main__":
    main()
