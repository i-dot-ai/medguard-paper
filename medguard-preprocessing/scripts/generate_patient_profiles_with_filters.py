from datetime import datetime

from medguard.data_processor import ModularPatientDataProcessor
from medguard.utils import export_pydantic_to_jsonl


def main():
    processor = ModularPatientDataProcessor(
        base_path="patient-data-test-set/PopHealth/Medguard/Extract"
    )

    # Specify which filters to apply and total sample size
    # Valid filter IDs: 5, 6, 10, 16, 23, 26, 28, 33, 43, 55
    filter_ids = [
        5,
        6,
        10,
        16,
        23,
        26,
        28,
        33,
        43,
        55,
    ]  # Can use integers or strings (e.g., ["005", "006", "010"])
    total_n = 200  # Total patients (will be split 50/50 positive/negative)

    print(f"Running filters: {filter_ids}")
    print(f"Target sample size: {total_n} (balanced positive/negative)")

    # Get balanced sample of patients
    patient_ids, patient_filters, patient_sample_dates, patient_primary_filters = (
        processor.get_balanced_patient_sample(
            filter_ids=filter_ids,
            total_n=total_n,
            min_duration_days=14,
            start_date_after=datetime(2020, 1, 1),
        )
    )

    print(f"\nSampled {len(patient_ids)} patients total")
    print(f"  - Positive (matching filters): {len(patient_filters)}")
    print(f"  - Negative (not matching): {len(patient_ids) - len(patient_filters)}")
    print(f"  - Sample dates assigned: {len(patient_sample_dates)}")

    # Show sample_date distribution
    if patient_sample_dates:
        sample_dates = list(patient_sample_dates.values())
        print(f"  - Sample date range: {min(sample_dates)} to {max(sample_dates)}")

    if not patient_ids:
        print("No patients found matching filters. Exiting.")
        return

    # Build profiles with filter information and sample_dates attached
    profiles = processor.build_patient_profiles_from_ids(
        patient_ids=patient_ids,
        patient_filters=patient_filters,
        patient_sample_dates=patient_sample_dates,
        patient_primary_filters=patient_primary_filters,
        to_pydantic_model=True,
    )

    # Print summary of matched filters
    print(f"\nBuilt {len(profiles)} patient profiles")

    # Check sample_date assignment
    profiles_with_dates = sum(1 for p in profiles if p.sample_date is not None)
    print(f"  - Profiles with sample_date: {profiles_with_dates}/{len(profiles)}")
    if profiles and profiles[0].sample_date:
        print(f"  - Example sample_date: {profiles[0].sample_date}")

    # Count positive vs negative
    positive_count = sum(1 for p in profiles if p.matched_filters)
    negative_count = len(profiles) - positive_count
    print("\nBalanced sample breakdown:")
    print(f"  - Positive cases (with filters): {positive_count}")
    print(f"  - Negative cases (no filters): {negative_count}")

    print("\nFilter match summary:")
    filter_counts = {}
    for profile in profiles:
        for filter_match in profile.matched_filters:
            filter_id = filter_match.filter_id
            filter_counts[filter_id] = filter_counts.get(filter_id, 0) + 1

    for filter_id, count in sorted(filter_counts.items()):
        print(f"  Filter {filter_id}: {count} patients")

    # Print example filter matches with dates
    if profiles and any(p.matched_filters for p in profiles):
        # Find first profile with filter matches
        example_profile = next(p for p in profiles if p.matched_filters)
        print("\nExample filter match:")
        for i, filter_match in enumerate(example_profile.matched_filters):
            primary_indicator = " (PRIMARY)" if i == 0 else ""
            print(
                f"  {filter_match.filter_id}{primary_indicator}: {filter_match.start_date} to {filter_match.end_date}"
            )

        # Count how many patients have multiple filter matches
        multi_filter_count = sum(1 for p in profiles if len(p.matched_filters) > 1)
        print(
            f"\nPatients matching multiple filters: {multi_filter_count}/{positive_count}"
        )

        # Verify primary filter distribution
        primary_filter_distribution = {}
        for profile in profiles:
            if profile.matched_filters:
                # First filter should be the primary
                primary_id = profile.matched_filters[0].filter_id
                primary_filter_distribution[primary_id] = (
                    primary_filter_distribution.get(primary_id, 0) + 1
                )

        print("\nPrimary filter distribution (first in matched_filters):")
        for filter_id in sorted(primary_filter_distribution.keys()):
            print(
                f"  Filter {filter_id}: {primary_filter_distribution[filter_id]} patients"
            )

    # Export to JSONL
    timestamp = datetime.now().strftime("%Y-%m-%d")
    num_filters = len(filter_ids)
    actual_sample_size = len(profiles)
    output_path = f"outputs/{timestamp}-patient_profiles_balanced_{num_filters}filters_n{actual_sample_size}.jsonl"

    export_pydantic_to_jsonl(profiles, output_path=output_path)
    print(f"\nExported to: {output_path}")


if __name__ == "__main__":
    main()
