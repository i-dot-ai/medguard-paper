"""Generate all statistical plots from saved CSV data.

This script regenerates all publication-quality plots for the paper.
No database connection required - works from saved CSV files.
"""

from medguard.analysis.smr_medication_change_contingency import (
    SMRMedicationChangeContingencyAnalysis,
)
from medguard.analysis.smr_time_window_sensitivity import (
    SMRTimeWindowSensitivityAnalysis,
)
from medguard.analysis.smr_time_to_medication_change import (
    SMRTimeToMedicationChangeAnalysis,
    SMRTimeToMedicationChangeRawDataAnalysis,
)
from medguard.analysis.active_medications_per_patient_distribution import (
    ActiveMedicationsPerPatientDistributionAnalysis,
    ActiveMedicationsPerElderlyPatientDistributionAnalysis,
)
from medguard.analysis.elderly_patients_medication_counts import (
    ElderlyPatientsMedicationCountsAnalysis,
)
from medguard.analysis.gp_events_per_patient_histogram import (
    GPEventsPerPatientBinnedSince2020Analysis,
)
from medguard.analysis.imd_distribution import (
    IMDDecilesAnalysis,
    IMDPercentilesPlotAnalysis,
)
from medguard.analysis.pincer_filter_statistics import (
    PincerFilterSummaryAnalysis,
    PincerFilterMultipleMatchesAnalysis,
)


def main():
    print("Generating all statistical plots...")
    print("=" * 60)

    # SMR analyses
    print("\n1. SMR Medication Change Contingency...")
    analysis = SMRMedicationChangeContingencyAnalysis(processor=None)
    output = analysis.run_figure()
    print(f"   ✓ Saved to: {output}")

    print("\n2. SMR Time Window Sensitivity...")
    analysis = SMRTimeWindowSensitivityAnalysis(processor=None)
    output = analysis.run_figure()
    print(f"   ✓ Saved to: {output}")

    print("\n3. SMR Time to Medication Change Summary...")
    analysis = SMRTimeToMedicationChangeAnalysis(processor=None)
    output = analysis.run_figure()
    print(f"   ✓ Saved to: {output}")

    print("\n4. SMR Time to Medication Change Raw Data...")
    analysis = SMRTimeToMedicationChangeRawDataAnalysis(processor=None)
    output = analysis.run_figure()
    print(f"   ✓ Saved to: {output}")

    # Medication distribution analyses
    print("\n5. Active Medications Per Patient Distribution...")
    analysis = ActiveMedicationsPerPatientDistributionAnalysis(processor=None)
    outputs = analysis.run_figure()
    for output in outputs:
        print(f"   ✓ Saved to: {output}")

    print("\n6. Active Medications Per Elderly Patient Distribution...")
    analysis = ActiveMedicationsPerElderlyPatientDistributionAnalysis(processor=None)
    outputs = analysis.run_figure()
    for output in outputs:
        print(f"   ✓ Saved to: {output}")

    print("\n7. Elderly Patients Medication Counts...")
    analysis = ElderlyPatientsMedicationCountsAnalysis(processor=None)
    output = analysis.run_figure()
    print(f"   ✓ Saved to: {output}")

    # GP events
    print("\n8. GP Events Per Patient (Since 2020)...")
    analysis = GPEventsPerPatientBinnedSince2020Analysis(processor=None)
    output = analysis.run_figure()
    print(f"   ✓ Saved to: {output}")

    # IMD analyses
    print("\n9. IMD Deciles Distribution...")
    analysis = IMDDecilesAnalysis(processor=None)
    output = analysis.run_figure()
    print(f"   ✓ Saved to: {output}")

    print("\n10. IMD Percentiles Distribution...")
    analysis = IMDPercentilesPlotAnalysis(processor=None)
    output = analysis.run_figure()
    print(f"   ✓ Saved to: {output}")

    # PINCER analyses
    print("\n11. PINCER Filter Summary...")
    analysis = PincerFilterSummaryAnalysis(processor=None)
    outputs = analysis.run_figure()
    for output in outputs:
        print(f"   ✓ Saved to: {output}")

    print("\n12. PINCER Filter Multiple Matches...")
    analysis = PincerFilterMultipleMatchesAnalysis(processor=None)
    output = analysis.run_figure()
    print(f"   ✓ Saved to: {output}")

    print("\n" + "=" * 60)
    print("✓ All plots generated successfully!")
    print("Plots saved to: outputs/statistics/plots/")


if __name__ == "__main__":
    main()
