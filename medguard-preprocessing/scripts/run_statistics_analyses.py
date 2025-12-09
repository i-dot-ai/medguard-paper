"""
Script to run all paper statistics analyses.

Usage:
    python scripts/run_statistics_analyses.py
"""

import logging

from medguard.analysis.data_completeness_gp_events import (
    DataCompletenessGPEventsAnalysis,
)
from medguard.analysis.gp_events_date_range import GPEventsDateRangeAnalysis
from medguard.analysis.gp_events_per_patient_overall import (
    GPEventsPerPatientOverallAnalysis,
)
from medguard.analysis.gp_events_per_patient_since_2020 import (
    GPEventsPerPatientSince2020Analysis,
)
from medguard.analysis.gp_events_per_patient_histogram import (
    GPEventsPerPatientHistogramOverallAnalysis,
    GPEventsPerPatientHistogramSince2020Analysis,
    GPEventsPerPatientBinnedOverallAnalysis,
    GPEventsPerPatientBinnedSince2020Analysis,
)
from medguard.analysis.elderly_patients_medication_counts import (
    ElderlyPatientsMedicationCountsAnalysis,
    ElderlyPatientsMedicationCountsDetailedAnalysis,
)
from medguard.analysis.active_medications_per_patient_distribution import (
    ActiveMedicationsPerPatientDistributionAnalysis,
    ActiveMedicationsPerElderlyPatientDistributionAnalysis,
)
from medguard.analysis.imd_distribution import (
    IMDHistogramAnalysis,
    IMDSummaryStatisticsAnalysis,
    IMDDecilesAnalysis,
    IMDCompletenessAnalysis,
)
from medguard.analysis.pincer_filter_statistics import (
    PincerFilterRawMatchesAnalysis,
    PincerFilterSummaryAnalysis,
    PincerFilterMultipleMatchesAnalysis,
)
from medguard.analysis.smr_time_to_medication_change import (
    SMRTimeToMedicationChangeAnalysis,
    SMRTimeToFirstMedicationChangeAnalysis,
    SMRTimeToMedicationChangeRawDataAnalysis,
    SMRTimeToFirstMedicationChangeRawDataAnalysis,
)
from medguard.analysis.smr_medication_change_contingency import (
    SMRMedicationChangeContingencyAnalysis,
)
from medguard.analysis.smr_time_window_sensitivity import (
    SMRTimeWindowSensitivityAnalysis,
)
from medguard.analysis.total_patients import TotalPatientsAnalysis
from medguard.data_processor import ModularPatientDataProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Run all statistics analyses."""

    logger.info("Initializing ModularPatientDataProcessor...")
    processor = ModularPatientDataProcessor(
        base_path="patient-data-test-set/PopHealth/MedGuard/Extract"
    )
    processor_all = ModularPatientDataProcessor(
        base_path="patient-data/PopHealth/MedGuard/Extract",
        initialise_enriched_views=False,
    )

    # Define all analyses to run
    analyses = [
        # Section 2.2: Data Source and Population
        TotalPatientsAnalysis(processor_all),
        GPEventsDateRangeAnalysis(processor),
        GPEventsPerPatientOverallAnalysis(processor),
        GPEventsPerPatientSince2020Analysis(processor),
        DataCompletenessGPEventsAnalysis(processor),
        # Histograms - GP Events
        GPEventsPerPatientHistogramOverallAnalysis(processor),
        GPEventsPerPatientHistogramSince2020Analysis(processor),
        GPEventsPerPatientBinnedOverallAnalysis(processor),
        GPEventsPerPatientBinnedSince2020Analysis(processor),
        # Elderly patients and polypharmacy
        ElderlyPatientsMedicationCountsAnalysis(processor),
        ElderlyPatientsMedicationCountsDetailedAnalysis(processor),
        # Active medication distributions
        ActiveMedicationsPerPatientDistributionAnalysis(processor),
        ActiveMedicationsPerElderlyPatientDistributionAnalysis(processor),
        # IMD distribution
        IMDHistogramAnalysis(processor),
        IMDSummaryStatisticsAnalysis(processor),
        IMDDecilesAnalysis(processor),
        IMDCompletenessAnalysis(processor),
        # PINCER filter statistics
        PincerFilterRawMatchesAnalysis(processor),
        PincerFilterSummaryAnalysis(processor),
        PincerFilterMultipleMatchesAnalysis(processor),
        # SMR analysis
        SMRTimeToMedicationChangeAnalysis(processor),
        SMRTimeToFirstMedicationChangeAnalysis(processor),
        SMRTimeToMedicationChangeRawDataAnalysis(processor),
        SMRTimeToFirstMedicationChangeRawDataAnalysis(processor),
        SMRMedicationChangeContingencyAnalysis(processor),
        SMRTimeWindowSensitivityAnalysis(processor),
    ]

    logger.info(f"Running {len(analyses)} analyses...")

    # Run each analysis
    results = {}
    for analysis in analyses:
        try:
            logger.info(f"Running {analysis.name}...")
            df, output_path = analysis.run()
            results[analysis.name] = {
                "df": df,
                "path": output_path,
                "rows": len(df),
                "cols": len(df.columns),
            }
            logger.info(
                f"  ✓ Saved to {output_path} ({len(df)} rows, {len(df.columns)} cols)"
            )
        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")
            results[analysis.name] = {"error": str(e)}

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)

    successful = [name for name, result in results.items() if "error" not in result]
    failed = [name for name, result in results.items() if "error" in result]

    logger.info(f"Successful: {len(successful)}/{len(analyses)}")
    logger.info(f"Failed: {len(failed)}/{len(analyses)}")

    if failed:
        logger.info("\nFailed analyses:")
        for name in failed:
            logger.info(f"  - {name}: {results[name]['error']}")

    logger.info(f"\nOutputs saved to: outputs/statistics/")


if __name__ == "__main__":
    main()
