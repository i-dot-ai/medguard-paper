import duckdb
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
from medguard.data_processor import ModularPatientDataProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PatientDataAnalyzer:
    """
    Analysis and exploration tools for patient data.
    Uses ModularPatientDataProcessor for core functionality.
    """

    def __init__(
        self, processor: ModularPatientDataProcessor = None, base_path: str = None
    ):
        """
        Initialize analyzer with either an existing processor or create a new one

        Args:
            processor: Existing ModularPatientDataProcessor instance
            base_path: Path to data if creating new processor
        """
        if processor:
            self.processor = processor
        elif base_path:
            self.processor = ModularPatientDataProcessor(base_path)
        else:
            self.processor = ModularPatientDataProcessor()

        self.conn = self.processor.conn
        self.table_views = self.processor.table_views

        logger.info(
            f"PatientDataAnalyzer initialized with {len(self.table_views)} tables"
        )

    def print_database_schema(
        self, include_sample_data: bool = True, max_sample_rows: int = 3
    ):
        """
        Print comprehensive schema information for all tables in the database

        Args:
            include_sample_data: Whether to show sample data for each table
            max_sample_rows: Maximum number of sample rows to display
        """

        print("\n" + "=" * 100)
        print("DATABASE SCHEMA OVERVIEW")
        print("=" * 100)
        print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total tables/views: {len(self.table_views)}")

        # Get overview statistics
        total_rows = 0
        for table_name, view_name in self.table_views.items():
            try:
                count = self.conn.execute(
                    f"SELECT COUNT(*) FROM {view_name}"
                ).fetchone()[0]
                total_rows += count
            except:
                pass

        print(f"Total rows across all tables: {total_rows:,}")
        print("=" * 100)

        # Process each table
        for table_name, view_name in sorted(self.table_views.items()):
            self._print_table_schema(
                table_name, view_name, include_sample_data, max_sample_rows
            )

    def _print_table_schema(
        self,
        table_name: str,
        view_name: str,
        include_sample_data: bool,
        max_sample_rows: int,
    ):
        """Print schema information for a single table"""

        print(f"\n📋 {table_name}")
        print(f"   View: {view_name}")
        print("-" * 80)

        try:
            # Get column information using DESCRIBE
            describe_sql = f"DESCRIBE {view_name}"
            describe_result = self.conn.execute(describe_sql).fetchall()
            columns_info = [(row[0], row[1], row[2]) for row in describe_result]

            # Get row count
            count_sql = f"SELECT COUNT(*) FROM {view_name}"
            row_count = self.conn.execute(count_sql).fetchone()[0]

            print(f"   Columns ({len(columns_info)} total):")

            # Print columns with numbering
            for i, (col_name, data_type, nullable) in enumerate(columns_info, 1):
                nullable_str = "NULL" if nullable == "YES" or nullable else "NOT NULL"
                print(f"   {i:2d}. {col_name:<40} {data_type:<15}")

            print(f"\n   Total rows: {row_count:,}")

            # Get data freshness for date columns
            self._print_data_freshness(view_name, columns_info)

            # Get completion rates for key columns
            self._print_completion_rates(view_name, columns_info)

            # Show sample data if requested
            if include_sample_data and row_count > 0:
                self._print_sample_data(view_name, max_sample_rows)

        except Exception as e:
            print(f"   ❌ Error analyzing table: {e}")

    def _print_data_freshness(self, view_name: str, columns_info: List[Tuple]):
        """Print data freshness information for date/timestamp columns"""

        date_columns = []
        for col_name, data_type, _ in columns_info:
            if any(
                date_type in data_type.upper()
                for date_type in ["DATE", "TIMESTAMP", "TIME"]
            ):
                date_columns.append(col_name)

        if date_columns:
            print(f"\n   📅 Date Range Information:")
            for col in date_columns[:3]:  # Limit to first 3 date columns
                try:
                    sql = f"""
                    SELECT 
                        MIN({col}) as min_date,
                        MAX({col}) as max_date,
                        COUNT({col}) as non_null_count
                    FROM {view_name} 
                    WHERE {col} IS NOT NULL
                    """
                    result = self.conn.execute(sql).fetchone()

                    if result and result[2] > 0:  # non_null_count > 0
                        min_date = result[0]
                        max_date = result[1]
                        count = result[2]
                        print(
                            f"      {col}: {min_date} to {max_date} ({count:,} records)"
                        )
                except:
                    print(f"      {col}: Unable to analyze")

    def _print_completion_rates(self, view_name: str, columns_info: List[Tuple]):
        """Print completion rates for key columns"""

        # Focus on key columns that are often important for analysis
        key_patterns = ["ID", "CODE", "DATE", "DESCRIPTION", "NAME", "TYPE", "STATUS"]
        key_columns = []

        for col_name, data_type, _ in columns_info:
            if any(pattern in col_name.upper() for pattern in key_patterns):
                key_columns.append(col_name)

        if key_columns:
            print(f"\n   📊 Completion Rates (Key Fields):")

            # Limit to most important columns
            for col in key_columns[:5]:
                try:
                    sql = f"""
                    SELECT 
                        COUNT(*) as total_count,
                        COUNT({col}) as non_null_count,
                        COUNT(CASE WHEN {col} IS NOT NULL AND TRIM(CAST({col} AS VARCHAR)) != '' THEN 1 END) as non_empty_count
                    FROM {view_name}
                    """
                    result = self.conn.execute(sql).fetchone()

                    if result:
                        total, non_null, non_empty = result
                        if total > 0:
                            completion_rate = (non_empty / total) * 100
                            print(
                                f"      {col:<30}: {completion_rate:5.1f}% ({non_empty:,}/{total:,})"
                            )
                except:
                    print(f"      {col:<30}: Unable to analyze")

    def _print_sample_data(self, view_name: str, max_rows: int):
        """Print sample data from the table"""

        print(f"\n   📋 Sample Data (first {max_rows} rows):")

        try:
            # Get a few columns for sample display
            sql = f"SELECT * FROM {view_name} LIMIT {max_rows}"
            result = self.conn.execute(sql).fetchall()

            if result:
                # Get column names
                columns = [desc[0] for desc in self.conn.description]

                # Limit columns for display (first 5 non-ID columns)
                display_columns = []
                for col in columns:
                    if len(display_columns) >= 5:
                        break
                    if not col.upper().endswith("_ID") or len(display_columns) < 2:
                        display_columns.append(col)

                # Find indices of display columns
                col_indices = [columns.index(col) for col in display_columns]

                # Print header
                header = " | ".join(f"{col[:15]:<15}" for col in display_columns)
                print(f"      {header}")
                print(f"      {'-' * len(header)}")

                # Print rows
                for row in result:
                    values = []
                    for idx in col_indices:
                        value = row[idx]
                        if value is None:
                            values.append("NULL")
                        else:
                            str_val = str(value)[:15]
                            values.append(str_val)

                    row_str = " | ".join(f"{val:<15}" for val in values)
                    print(f"      {row_str}")

                if len(columns) > len(display_columns):
                    print(
                        f"      ... and {len(columns) - len(display_columns)} more columns"
                    )

        except Exception as e:
            print(f"      ❌ Error showing sample data: {e}")

    def analyze_patient_population(self):
        """Analyze the patient population using Patient_Link as master"""

        print("\n" + "=" * 100)
        print("TRUE PATIENT POPULATION ANALYSIS")
        print("=" * 100)

        patient_link_view = self.table_views.get(
            "SharedCare.Patient_Link", "SharedCare_Patient_Link"
        )
        patient_view = self.table_views.get("SharedCare.Patient", "SharedCare_Patient")

        if not patient_link_view:
            print("❌ Patient_Link table not found")
            return

        try:
            # Basic population stats from Patient_Link
            link_stats_sql = f"""
            SELECT 
                COUNT(*) as total_links,
                COUNT(CASE WHEN Merged = 'Y' THEN 1 END) as merged_patients,
                COUNT(CASE WHEN Deceased = 'Y' THEN 1 END) as deceased_patients,
                COUNT(CASE WHEN OptedOut = 'Y' THEN 1 END) as opted_out_patients,
                COUNT(CASE WHEN Restricted = 'Y' THEN 1 END) as restricted_patients,
                COUNT(CASE WHEN ConsentEPR = 'Y' THEN 1 END) as consented_patients,
                COUNT(CASE WHEN Deleted = 'Y' THEN 1 END) as deleted_patients
            FROM {patient_link_view}
            """

            link_stats = self.conn.execute(link_stats_sql).fetchone()

            print(f"📊 Patient Link Statistics:")
            print(f"   Total patient links: {link_stats[0]:,}")
            print(
                f"   Merged patients: {link_stats[1]:,} ({link_stats[1] / link_stats[0] * 100:.1f}%)"
            )
            print(
                f"   Deceased patients: {link_stats[2]:,} ({link_stats[2] / link_stats[0] * 100:.1f}%)"
            )
            print(
                f"   Opted out patients: {link_stats[3]:,} ({link_stats[3] / link_stats[0] * 100:.1f}%)"
            )
            print(
                f"   Restricted access: {link_stats[4]:,} ({link_stats[4] / link_stats[0] * 100:.1f}%)"
            )
            print(
                f"   With EPR consent: {link_stats[5]:,} ({link_stats[5] / link_stats[0] * 100:.1f}%)"
            )
            print(
                f"   Deleted: {link_stats[6]:,} ({link_stats[6] / link_stats[0] * 100:.1f}%)"
            )

            # Valid patient count
            valid_count = self.processor.get_total_patient_count(
                include_opted_out=False, include_deceased=True, include_restricted=False
            )
            print(
                f"\n   Valid patients (excl. merged/deleted/opted out): {valid_count:,}"
            )

            # Demographic completeness for valid patients
            if patient_view:
                demo_stats_sql = f"""
                WITH valid_patients AS (
                    SELECT pl.PK_Patient_Link_ID
                    FROM {patient_link_view} pl
                    WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
                      AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
                      AND (pl.OptedOut != 'Y' OR pl.OptedOut IS NULL)
                )
                SELECT 
                    COUNT(vp.PK_Patient_Link_ID) as valid_patients,
                    COUNT(p.FK_Patient_Link_ID) as has_demographics,
                    COUNT(p.Dob) as has_dob,
                    COUNT(p.Sex) as has_sex,
                    COUNT(p.PostCode) as has_postcode,
                    COUNT(p.GPPracticeCode) as has_gp
                FROM valid_patients vp
                LEFT JOIN {patient_view} p ON vp.PK_Patient_Link_ID = p.FK_Patient_Link_ID
                """

                demo_stats = self.conn.execute(demo_stats_sql).fetchone()

                print(f"\n📋 Demographic Data Coverage (for valid patients):")
                print(
                    f"   Has patient record: {demo_stats[1]:,} ({demo_stats[1] / demo_stats[0] * 100:.1f}%)"
                )
                print(
                    f"   Has date of birth: {demo_stats[2]:,} ({demo_stats[2] / demo_stats[0] * 100:.1f}%)"
                )
                print(
                    f"   Has sex recorded: {demo_stats[3]:,} ({demo_stats[3] / demo_stats[0] * 100:.1f}%)"
                )
                print(
                    f"   Has postcode: {demo_stats[4]:,} ({demo_stats[4] / demo_stats[0] * 100:.1f}%)"
                )
                print(
                    f"   Has GP practice: {demo_stats[5]:,} ({demo_stats[5] / demo_stats[0] * 100:.1f}%)"
                )

                # Age distribution for valid patients
                self._analyze_age_distribution(patient_link_view, patient_view)

                # Sex distribution for valid patients
                self._analyze_sex_distribution(patient_link_view, patient_view)

                # Geographic distribution
                self._analyze_geographic_distribution(patient_link_view, patient_view)

        except Exception as e:
            print(f"❌ Error analyzing patient population: {e}")

    def _analyze_age_distribution(self, patient_link_view: str, patient_view: str):
        """Analyze age distribution for valid patients"""

        print(f"\n📈 Age Distribution (Valid Patients):")

        age_sql = f"""
        WITH valid_patients AS (
            SELECT pl.PK_Patient_Link_ID
            FROM {patient_link_view} pl
            WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
              AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
              AND (pl.OptedOut != 'Y' OR pl.OptedOut IS NULL)
        )
        SELECT 
            CASE 
                WHEN DATEDIFF('year', p.Dob, CURRENT_DATE) < 0 THEN 'Invalid (<0)'
                WHEN DATEDIFF('year', p.Dob, CURRENT_DATE) > 150 THEN 'Invalid (>150)'
                WHEN DATEDIFF('year', p.Dob, CURRENT_DATE) < 18 THEN '0-17'
                WHEN DATEDIFF('year', p.Dob, CURRENT_DATE) < 30 THEN '18-29'
                WHEN DATEDIFF('year', p.Dob, CURRENT_DATE) < 45 THEN '30-44'
                WHEN DATEDIFF('year', p.Dob, CURRENT_DATE) < 65 THEN '45-64'
                WHEN DATEDIFF('year', p.Dob, CURRENT_DATE) < 80 THEN '65-79'
                ELSE '80+' 
            END as age_group,
            COUNT(*) as count
        FROM valid_patients vp
        INNER JOIN {patient_view} p ON vp.PK_Patient_Link_ID = p.FK_Patient_Link_ID
        WHERE p.Dob IS NOT NULL
        GROUP BY age_group
        ORDER BY 
            CASE 
                WHEN age_group = 'Invalid (<0)' THEN 0
                WHEN age_group = 'Invalid (>150)' THEN 1
                WHEN age_group = '0-17' THEN 2
                WHEN age_group = '18-29' THEN 3
                WHEN age_group = '30-44' THEN 4
                WHEN age_group = '45-64' THEN 5
                WHEN age_group = '65-79' THEN 6
                WHEN age_group = '80+' THEN 7
            END
        """

        age_data = self.conn.execute(age_sql).fetchall()
        total_with_age = sum(row[1] for row in age_data)

        for age_group, count in age_data:
            percentage = (count / total_with_age * 100) if total_with_age > 0 else 0
            print(f"   {age_group:<15}: {count:8,} ({percentage:5.1f}%)")

    def _analyze_sex_distribution(self, patient_link_view: str, patient_view: str):
        """Analyze sex distribution for valid patients"""

        print(f"\n👥 Sex Distribution (Valid Patients):")

        sex_sql = f"""
        WITH valid_patients AS (
            SELECT pl.PK_Patient_Link_ID
            FROM {patient_link_view} pl
            WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
              AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
              AND (pl.OptedOut != 'Y' OR pl.OptedOut IS NULL)
        )
        SELECT 
            COALESCE(p.Sex, 'Unknown') as sex,
            COUNT(*) as count
        FROM valid_patients vp
        LEFT JOIN {patient_view} p ON vp.PK_Patient_Link_ID = p.FK_Patient_Link_ID
        GROUP BY sex
        ORDER BY count DESC
        """

        sex_data = self.conn.execute(sex_sql).fetchall()
        total = sum(row[1] for row in sex_data)

        for sex, count in sex_data:
            percentage = (count / total * 100) if total > 0 else 0
            print(f"   {sex:<10}: {count:8,} ({percentage:5.1f}%)")

    def _analyze_geographic_distribution(
        self, patient_link_view: str, patient_view: str
    ):
        """Analyze geographic distribution for valid patients"""

        print(f"\n🗺️  Geographic Distribution (Top 10 Postcode Areas):")

        geo_sql = f"""
        WITH valid_patients AS (
            SELECT pl.PK_Patient_Link_ID
            FROM {patient_link_view} pl
            WHERE (pl.Merged != 'Y' OR pl.Merged IS NULL)
              AND (pl.Deleted != 'Y' OR pl.Deleted IS NULL)
              AND (pl.OptedOut != 'Y' OR pl.OptedOut IS NULL)
        )
        SELECT 
            SUBSTR(p.PostCode, 1, 2) as postcode_area,
            COUNT(*) as count
        FROM valid_patients vp
        INNER JOIN {patient_view} p ON vp.PK_Patient_Link_ID = p.FK_Patient_Link_ID
        WHERE p.PostCode IS NOT NULL
        GROUP BY SUBSTR(p.PostCode, 1, 2)
        ORDER BY count DESC
        LIMIT 10
        """

        geo_data = self.conn.execute(geo_sql).fetchall()

        for postcode, count in geo_data:
            print(f"   {postcode:<5}: {count:8,}")

    def analyze_patient_link_integrity(self):
        """Analyze the integrity and relationships in Patient_Link table"""

        print("\n" + "=" * 100)
        print("PATIENT LINK INTEGRITY ANALYSIS")
        print("=" * 100)

        patient_link_view = self.table_views.get(
            "SharedCare.Patient_Link", "SharedCare_Patient_Link"
        )
        patient_view = self.table_views.get("SharedCare.Patient", "SharedCare_Patient")

        if not patient_link_view:
            print("❌ Patient_Link table not found")
            return

        try:
            # Analyze merge chains
            print(f"🔄 Merge Chain Analysis:")

            merge_analysis_sql = f"""
            WITH merge_chains AS (
                SELECT 
                    pl1.PK_Patient_Link_ID as merged_from,
                    pl1.MergedTo as merged_to,
                    pl2.Merged as target_also_merged,
                    pl2.MergedTo as final_target
                FROM {patient_link_view} pl1
                LEFT JOIN {patient_link_view} pl2 ON pl1.MergedTo = pl2.PK_Patient_Link_ID
                WHERE pl1.Merged = 'Y' AND pl1.MergedTo IS NOT NULL
            )
            SELECT 
                COUNT(*) as total_merges,
                COUNT(CASE WHEN target_also_merged = 'Y' THEN 1 END) as chained_merges,
                COUNT(DISTINCT merged_to) as unique_targets
            FROM merge_chains
            """

            merge_stats = self.conn.execute(merge_analysis_sql).fetchone()

            print(f"   Total merge records: {merge_stats[0]:,}")
            print(
                f"   Chained merges (merged to another merged patient): {merge_stats[1]:,}"
            )
            print(f"   Unique merge targets: {merge_stats[2]:,}")

            # Check for orphaned patient records
            if patient_view:
                print(f"\n🔗 Data Linkage Integrity:")

                orphan_sql = f"""
                WITH all_patient_links AS (
                    SELECT DISTINCT PK_Patient_Link_ID 
                    FROM {patient_link_view}
                ),
                all_patient_fks AS (
                    SELECT DISTINCT FK_Patient_Link_ID 
                    FROM {patient_view}
                    WHERE FK_Patient_Link_ID IS NOT NULL
                )
                SELECT 
                    (SELECT COUNT(*) FROM all_patient_fks WHERE FK_Patient_Link_ID NOT IN (SELECT PK_Patient_Link_ID FROM all_patient_links)) as orphaned_patients,
                    (SELECT COUNT(*) FROM all_patient_links WHERE PK_Patient_Link_ID NOT IN (SELECT FK_Patient_Link_ID FROM all_patient_fks)) as links_without_patient
                """

                orphan_stats = self.conn.execute(orphan_sql).fetchone()

                print(
                    f"   Patient records with invalid FK_Patient_Link_ID: {orphan_stats[0]:,}"
                )
                print(
                    f"   Patient_Link records without Patient record: {orphan_stats[1]:,}"
                )

            # Analyze consent patterns
            print(f"\n📝 Consent Analysis:")

            consent_sql = f"""
            SELECT 
                CASE 
                    WHEN ConsentEPR = 'Y' AND OptedOut != 'Y' THEN 'Consented & Active'
                    WHEN ConsentEPR = 'Y' AND OptedOut = 'Y' THEN 'Consented but Opted Out'
                    WHEN ConsentEPR != 'Y' AND OptedOut != 'Y' THEN 'No Consent but Active'
                    WHEN ConsentEPR != 'Y' AND OptedOut = 'Y' THEN 'No Consent & Opted Out'
                    ELSE 'Unknown Status'
                END as consent_status,
                COUNT(*) as count
            FROM {patient_link_view}
            WHERE (Merged != 'Y' OR Merged IS NULL)
              AND (Deleted != 'Y' OR Deleted IS NULL)
            GROUP BY consent_status
            ORDER BY count DESC
            """

            consent_data = self.conn.execute(consent_sql).fetchall()

            for status, count in consent_data:
                print(f"   {status:<30}: {count:8,}")

        except Exception as e:
            print(f"❌ Error analyzing patient link integrity: {e}")

    def get_table_relationships(self):
        """Analyze relationships between tables based on foreign keys"""

        print("\n" + "=" * 100)
        print("TABLE RELATIONSHIPS")
        print("=" * 100)

        # Look for foreign key patterns
        relationships = {}
        patient_linked_tables = []

        for table_name, view_name in self.table_views.items():
            try:
                # Get columns that look like foreign keys
                columns_sql = f"DESCRIBE {view_name}"
                columns = self.conn.execute(columns_sql).fetchall()

                fk_columns = []
                has_patient_link = False

                for col_name, data_type, nullable in columns:
                    if col_name.startswith("FK_") and col_name.endswith("_ID"):
                        fk_columns.append(col_name)
                        if col_name == "FK_Patient_Link_ID":
                            has_patient_link = True

                if fk_columns:
                    relationships[table_name] = fk_columns

                if has_patient_link:
                    patient_linked_tables.append(table_name)

            except Exception as e:
                continue

        # Print relationships
        print("📊 Foreign Key Relationships:")
        for table_name, fk_columns in sorted(relationships.items()):
            print(f"\n   {table_name}:")
            for fk in fk_columns:
                # Try to infer target table
                target_table = fk.replace("FK_", "").replace("_ID", "")
                print(f"      └─ {fk} → (likely {target_table})")

        # Highlight patient linking
        print(f"\n🔗 Patient-Linked Tables ({len(patient_linked_tables)} total):")
        for table in sorted(patient_linked_tables):
            # Check if we can get a count of linked patients
            try:
                view_name = self.table_views[table]
                count_sql = f"""
                SELECT COUNT(DISTINCT FK_Patient_Link_ID) 
                FROM {view_name} 
                WHERE FK_Patient_Link_ID IS NOT NULL
                """
                patient_count = self.conn.execute(count_sql).fetchone()[0]
                print(f"      └─ {table} ({patient_count:,} unique patients)")
            except:
                print(f"      └─ {table}")

    def analyze_data_coverage(self):
        """Analyze which patients have data in which domains"""

        print("\n" + "=" * 100)
        print("PATIENT DATA COVERAGE ANALYSIS")
        print("=" * 100)

        patient_link_view = self.table_views.get(
            "SharedCare.Patient_Link", "SharedCare_Patient_Link"
        )

        if not patient_link_view:
            print("❌ Patient_Link table not found")
            return

        # Get total valid patients
        total_valid = self.processor.get_total_patient_count()
        print(f"Total valid patients: {total_valid:,}")

        # Define key domains to check
        domains = [
            ("Demographics", "SharedCare.Patient", "FK_Patient_Link_ID"),
            ("Medications", "SharedCare.GP_Medications", "FK_Patient_Link_ID"),
            ("GP Events", "SharedCare.GP_Events", "FK_Patient_Link_ID"),
            ("GP Encounters", "SharedCare.GP_Encounters", "FK_Patient_Link_ID"),
            (
                "Hospital Admissions",
                "SharedCare.Acute_Inpatients",
                "FK_Patient_Link_ID",
            ),
            ("A&E Visits", "SharedCare.Acute_AE", "FK_Patient_Link_ID"),
            ("Outpatient Visits", "SharedCare.Acute_Outpatients", "FK_Patient_Link_ID"),
            ("Allergies", "SharedCare.Acute_Allergies", "FK_Patient_Link_ID"),
            ("Social Care", "SharedCare.SocialCare_Events", "FK_Patient_Link_ID"),
        ]

        coverage_stats = []

        for domain_name, table_name, link_col in domains:
            if table_name in self.table_views:
                view_name = self.table_views[table_name]

                try:
                    # Count unique patients with data in this domain
                    coverage_sql = f"""
                    WITH valid_patients AS (
                        SELECT PK_Patient_Link_ID
                        FROM {patient_link_view}
                        WHERE (Merged != 'Y' OR Merged IS NULL)
                          AND (Deleted != 'Y' OR Deleted IS NULL)
                          AND (OptedOut != 'Y' OR OptedOut IS NULL)
                    )
                    SELECT COUNT(DISTINCT t.{link_col}) as patients_with_data
                    FROM {view_name} t
                    INNER JOIN valid_patients vp ON t.{link_col} = vp.PK_Patient_Link_ID
                    WHERE t.{link_col} IS NOT NULL
                      AND (t.Deleted != 'Y' OR t.Deleted IS NULL)
                    """

                    result = self.conn.execute(coverage_sql).fetchone()
                    patients_with_data = result[0]
                    coverage_pct = (
                        (patients_with_data / total_valid * 100)
                        if total_valid > 0
                        else 0
                    )

                    coverage_stats.append(
                        {
                            "domain": domain_name,
                            "patients_with_data": patients_with_data,
                            "coverage_pct": coverage_pct,
                            "patients_without_data": total_valid - patients_with_data,
                        }
                    )

                except Exception as e:
                    logger.warning(f"Could not analyze {domain_name}: {e}")

        # Print coverage statistics
        print(f"\n📊 Data Coverage by Domain:")
        print(f"{'Domain':<25} {'Has Data':>12} {'Coverage %':>12} {'No Data':>12}")
        print("-" * 65)

        for stat in sorted(
            coverage_stats, key=lambda x: x["coverage_pct"], reverse=True
        ):
            print(
                f"{stat['domain']:<25} {stat['patients_with_data']:>12,} {stat['coverage_pct']:>11.1f}% {stat['patients_without_data']:>12,}"
            )

        # Find patients with no clinical data at all
        print(f"\n🔍 Analyzing Completely Empty Patients...")

        empty_patients_sql = f"""
        WITH valid_patients AS (
            SELECT PK_Patient_Link_ID
            FROM {patient_link_view}
            WHERE (Merged != 'Y' OR Merged IS NULL)
              AND (Deleted != 'Y' OR Deleted IS NULL)
              AND (OptedOut != 'Y' OR OptedOut IS NULL)
        ),
        patients_with_any_data AS (
            SELECT DISTINCT FK_Patient_Link_ID
            FROM (
                SELECT FK_Patient_Link_ID FROM {self.table_views.get("SharedCare.GP_Medications", "SharedCare_GP_Medications")} WHERE FK_Patient_Link_ID IS NOT NULL
                UNION
                SELECT FK_Patient_Link_ID FROM {self.table_views.get("SharedCare.GP_Events", "SharedCare_GP_Events")} WHERE FK_Patient_Link_ID IS NOT NULL
                UNION
                SELECT FK_Patient_Link_ID FROM {self.table_views.get("SharedCare.GP_Encounters", "SharedCare_GP_Encounters")} WHERE FK_Patient_Link_ID IS NOT NULL
                UNION
                SELECT FK_Patient_Link_ID FROM {self.table_views.get("SharedCare.Acute_Inpatients", "SharedCare_Acute_Inpatients")} WHERE FK_Patient_Link_ID IS NOT NULL
                UNION
                SELECT FK_Patient_Link_ID FROM {self.table_views.get("SharedCare.Acute_AE", "SharedCare_Acute_AE")} WHERE FK_Patient_Link_ID IS NOT NULL
            )
        )
        SELECT 
            COUNT(vp.PK_Patient_Link_ID) as total_valid,
            COUNT(pwd.FK_Patient_Link_ID) as has_any_clinical_data,
            COUNT(vp.PK_Patient_Link_ID) - COUNT(pwd.FK_Patient_Link_ID) as no_clinical_data
        FROM valid_patients vp
        LEFT JOIN patients_with_any_data pwd ON vp.PK_Patient_Link_ID = pwd.FK_Patient_Link_ID
        """

        try:
            empty_stats = self.conn.execute(empty_patients_sql).fetchone()
            empty_pct = (
                (empty_stats[2] / empty_stats[0] * 100) if empty_stats[0] > 0 else 0
            )

            print(
                f"   Patients with NO clinical data: {empty_stats[2]:,} ({empty_pct:.1f}%)"
            )
            print(
                f"   Patients with at least some clinical data: {empty_stats[1]:,} ({100 - empty_pct:.1f}%)"
            )
        except Exception as e:
            print(f"   ❌ Could not analyze empty patients: {e}")

    def run_comprehensive_analysis(self, output_file: str = None):
        """Run all available analyses"""

        print("\n" + "=" * 100)
        print("COMPREHENSIVE PATIENT DATA ANALYSIS")
        print("=" * 100)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Run all analyses
        self.print_database_schema(include_sample_data=False)
        self.analyze_patient_link_integrity()
        self.analyze_patient_population()
        self.get_table_relationships()
        self.analyze_data_coverage()

        print("\n" + "=" * 100)
        print("ANALYSIS COMPLETE")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)


def main():
    """Example usage of PatientDataAnalyzer"""

    # Initialize analyzer (will create its own processor)
    analyzer = PatientDataAnalyzer()

    # Run comprehensive analysis
    analyzer.run_comprehensive_analysis()

    # Or run specific analyses
    # analyzer.analyze_patient_link_integrity()
    # analyzer.analyze_data_coverage()


if __name__ == "__main__":
    main()
