"""
Analysis module for generating paper statistics.

Each analysis class inherits from AnalysisBase and implements:
- get_sql_statement(): Returns SQL query string
- post_process_df(): Optional polars DataFrame transformations

Usage:
    from medguard.data_processor import ModularPatientDataProcessor
    from medguard.analysis.total_patients import TotalPatientsAnalysis

    processor = ModularPatientDataProcessor()
    analysis = TotalPatientsAnalysis(processor)
    df, output_path = analysis.run()
"""

from medguard.analysis.base import AnalysisBase

# Section 2.2: Data Source and Population
from medguard.analysis.total_patients import TotalPatientsAnalysis
from medguard.analysis.gp_events_date_range import GPEventsDateRangeAnalysis
from medguard.analysis.gp_events_per_patient_overall import (
    GPEventsPerPatientOverallAnalysis,
)
from medguard.analysis.gp_events_per_patient_since_2020 import (
    GPEventsPerPatientSince2020Analysis,
)
from medguard.analysis.data_completeness_gp_events import (
    DataCompletenessGPEventsAnalysis,
)

# Histogram analyses
from medguard.analysis.gp_events_per_patient_histogram import (
    GPEventsPerPatientHistogramOverallAnalysis,
    GPEventsPerPatientHistogramSince2020Analysis,
    GPEventsPerPatientBinnedOverallAnalysis,
    GPEventsPerPatientBinnedSince2020Analysis,
)

# Elderly patients and polypharmacy
from medguard.analysis.elderly_patients_medication_counts import (
    ElderlyPatientsMedicationCountsAnalysis,
    ElderlyPatientsMedicationCountsDetailedAnalysis,
)

# Active medication distributions
from medguard.analysis.active_medications_per_patient_distribution import (
    ActiveMedicationsPerPatientDistributionAnalysis,
    ActiveMedicationsPerElderlyPatientDistributionAnalysis,
)

# IMD distribution
from medguard.analysis.imd_distribution import (
    IMDHistogramAnalysis,
    IMDSummaryStatisticsAnalysis,
    IMDDecilesAnalysis,
    IMDCompletenessAnalysis,
)

# PINCER filter statistics
from medguard.analysis.pincer_filter_statistics import (
    PincerFilterRawMatchesAnalysis,
    PincerFilterSummaryAnalysis,
    PincerFilterMultipleMatchesAnalysis,
)

# SMR analysis
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

__all__ = [
    "AnalysisBase",
    # Section 2.2: Data Source and Population
    "TotalPatientsAnalysis",
    "GPEventsDateRangeAnalysis",
    "GPEventsPerPatientOverallAnalysis",
    "GPEventsPerPatientSince2020Analysis",
    "DataCompletenessGPEventsAnalysis",
    # Histograms
    "GPEventsPerPatientHistogramOverallAnalysis",
    "GPEventsPerPatientHistogramSince2020Analysis",
    "GPEventsPerPatientBinnedOverallAnalysis",
    "GPEventsPerPatientBinnedSince2020Analysis",
    # Elderly patients / polypharmacy
    "ElderlyPatientsMedicationCountsAnalysis",
    "ElderlyPatientsMedicationCountsDetailedAnalysis",
    # Active medication distributions
    "ActiveMedicationsPerPatientDistributionAnalysis",
    "ActiveMedicationsPerElderlyPatientDistributionAnalysis",
    # IMD distribution
    "IMDHistogramAnalysis",
    "IMDSummaryStatisticsAnalysis",
    "IMDDecilesAnalysis",
    "IMDCompletenessAnalysis",
    # PINCER filter statistics
    "PincerFilterRawMatchesAnalysis",
    "PincerFilterSummaryAnalysis",
    "PincerFilterMultipleMatchesAnalysis",
    # SMR analysis
    "SMRTimeToMedicationChangeAnalysis",
    "SMRTimeToFirstMedicationChangeAnalysis",
    "SMRTimeToMedicationChangeRawDataAnalysis",
    "SMRTimeToFirstMedicationChangeRawDataAnalysis",
    "SMRMedicationChangeContingencyAnalysis",
    "SMRTimeWindowSensitivityAnalysis",
]
