#!/usr/bin/env python3
"""
CLI tool to generate evaluations from logs and patient records.

Usage:
    python scripts/generate_evaluation.py
    python scripts/generate_evaluation.py --logs-dir custom/logs --inputs-dir custom/inputs
"""

import argparse
import sys
from pathlib import Path

from medguard.evaluation.main import generate_evaluation_from_logs_and_patient_records


def list_files(directory: Path, extension: str) -> list[Path]:
    """List all .jsonl files in a directory."""
    if not directory.exists():
        return []
    return sorted(directory.glob(f"*{extension}"))


def select_file(files: list[Path], prompt: str) -> Path | None:
    """Display a menu and let user select a file."""
    if not files:
        return None

    print(f"\n{prompt}")
    print("-" * 60)
    for i, file in enumerate(files, 1):
        print(f"{i}. {file.name}")
    print("-" * 60)

    while True:
        try:
            choice = input(f"Select a file (1-{len(files)}) or 'q' to quit: ").strip()
            if choice.lower() == "q":
                return None

            idx = int(choice) - 1
            if 0 <= idx < len(files):
                return files[idx]
            else:
                print(f"Please enter a number between 1 and {len(files)}")
        except ValueError:
            print("Please enter a valid number or 'q' to quit")
        except KeyboardInterrupt:
            print("\nCancelled")
            return None


def select_files_multiple(files: list[Path], prompt: str) -> list[Path] | None:
    """Display a menu and let user select one or more files (comma-separated)."""
    if not files:
        return None

    print(f"\n{prompt}")
    print("-" * 60)
    for i, file in enumerate(files, 1):
        print(f"{i}. {file.name}")
    print("-" * 60)

    while True:
        try:
            choice = input(
                f"Select file(s) (1-{len(files)}), comma-separated for multiple, or 'q' to quit: "
            ).strip()
            if choice.lower() == "q":
                return None

            # Parse comma-separated numbers
            indices = [int(x.strip()) - 1 for x in choice.split(",")]

            # Validate all indices
            if all(0 <= idx < len(files) for idx in indices):
                return [files[idx] for idx in indices]
            else:
                print(f"Please enter numbers between 1 and {len(files)}")
        except ValueError:
            print("Please enter valid numbers separated by commas, or 'q' to quit")
        except KeyboardInterrupt:
            print("\nCancelled")
            return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate evaluation from logs and patient records"
    )
    parser.add_argument(
        "--logs-dir",
        type=Path,
        default=Path("outputs/logs"),
        help="Directory containing log files (default: outputs/logs)",
    )
    parser.add_argument(
        "--inputs-dir",
        type=Path,
        default=Path("inputs"),
        help="Directory containing patient record files (default: inputs)",
    )
    parser.add_argument(
        "--description", type=str, help="Optional description for the evaluation output folder"
    )
    parser.add_argument(
        "--logs-file", type=Path, help="Directly specify logs file (skips interactive selection)"
    )
    parser.add_argument(
        "--patient-records-file",
        type=Path,
        help="Directly specify patient records file (skips interactive selection)",
    )

    args = parser.parse_args()

    # Get logs file(s)
    if args.logs_file:
        logs_path = args.logs_file
        if not logs_path.exists():
            print(f"Error: Logs file not found: {logs_path}")
            sys.exit(1)
    else:
        logs_files = list_files(args.logs_dir, ".eval")
        if not logs_files:
            print(f"Error: No .eval files found in {args.logs_dir}")
            print(
                "Please create the directory and add log files, or specify a different directory with --logs-dir"
            )
            sys.exit(1)

        selected = select_files_multiple(
            logs_files, "Select logs file(s) (for multiple runs, use comma-separated):"
        )
        if not selected:
            print("No logs file selected. Exiting.")
            sys.exit(0)

        # If only one file selected, use as Path; if multiple, use as list[Path]
        logs_path = selected[0] if len(selected) == 1 else selected

    # Get patient records file
    if args.patient_records_file:
        patient_records_path = args.patient_records_file
        if not patient_records_path.exists():
            print(f"Error: Patient records file not found: {patient_records_path}")
            sys.exit(1)
    else:
        patient_files = list_files(args.inputs_dir, ".jsonl")
        if not patient_files:
            print(f"Error: No .jsonl files found in {args.inputs_dir}")
            print(
                "Please create the directory and add patient record files, or specify a different directory with --inputs-dir"
            )
            sys.exit(1)

        patient_records_path = select_file(patient_files, "Select patient records file:")
        if not patient_records_path:
            print("No patient records file selected. Exiting.")
            sys.exit(0)

    # Get description
    description = args.description
    if not description:
        description_input = input("\nEnter optional description (press Enter to skip): ").strip()
        description = description_input if description_input else None

    # Generate evaluation
    print("\nGenerating evaluation...")
    print(f"  Logs: {logs_path}")
    print(f"  Patient records: {patient_records_path}")
    if description:
        print(f"  Description: {description}")

    try:
        evaluation = generate_evaluation_from_logs_and_patient_records(
            logs_path=logs_path, patient_records_path=patient_records_path, description=description
        )

        print("\n✓ Evaluation generated successfully!")
        print(f"  Output folder: {evaluation.output_folder_path}")

    except Exception as e:
        print(f"\n✗ Error generating evaluation: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
