from medguard.subset import DatasetSubsetGenerator


def main():
    """
    Generate a holdout test set of 500,000 patients that has NO OVERLAP
    with the existing patient-data-subset (training/development data).

    This ensures the test set is completely independent for model evaluation.
    """

    # Initialize generator pointing to source data and new test set location
    generator = DatasetSubsetGenerator(
        source_path="patient-data",
        target_path="patient-data-test-set",
    )

    # Load existing patient IDs from the training/development subset to exclude them
    print("Loading existing patient IDs from patient-data-subset...")
    existing_patient_ids = generator.load_existing_patient_ids("patient-data-subset")

    # Generate test set with NEW patients (excluding existing ones)
    print("\nGenerating test set with NEW patients...")
    print(f"Excluding {len(existing_patient_ids):,} patients from existing subset")

    generator.generate_subset(
        sample_size=200000,
        stratify=True,  # Maintain demographic distribution
        random_seed=123,  # Different seed from original subset for independence
        include_opted_out=False,
        include_deceased=True,
        include_restricted=False,
        exclude_patient_ids=existing_patient_ids,  # KEY: Exclude existing patients
    )

    # Verify no overlap between training/dev set and test set
    print("\n" + "=" * 60)
    print("VERIFYING NO OVERLAP BETWEEN SUBSETS")
    print("=" * 60)

    no_overlap = DatasetSubsetGenerator.verify_no_overlap(
        "patient-data-subset", "patient-data-test-set"
    )

    print("\n" + "=" * 60)
    print("Test set generation complete!")
    print("=" * 60)
    print("Location: patient-data-test-set/")
    print("Size: 200,000 patients")

    if no_overlap:
        print("✓ VERIFIED: Test set is completely disjoint from training/dev set")
    else:
        print("✗ WARNING: Overlap detected! Check logs above for details")

    print("\nSee patient-data-test-set/subset_summary.txt for details")


if __name__ == "__main__":
    # Note: This will take approximately 40-60 minutes to complete
    # (longer than original due to larger sample size)
    main()
