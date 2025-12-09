from pathlib import Path
from typing import Callable

from inspect_ai.log import EvalSample, read_eval_log_samples
from pydantic import BaseModel, PrivateAttr

from medguard.data_ingest.models.patient_profile import PatientProfile
from medguard.evaluation.calibration_metrics import (
    CalibrationMetrics,
    calculate_calibration_metrics,
)
from medguard.evaluation.clinician.models import Stage2Data
from medguard.evaluation.clinician.utils import load_stage2_data_from_folder
from medguard.evaluation.evaluation_metrics import EvaluationMetrics, calculate_evaluation_metrics
from medguard.evaluation.failure_themes import FailureThemes
from medguard.evaluation.performance_metrics.filter.performance_metrics import (
    FilterPerformanceMetrics,
    analysed_patient_records_to_performance_metrics,
)
from medguard.evaluation.utils import (
    load_analysed_patient_records_from_jsonl,
    load_patient_profiles_from_jsonl,
)
from medguard.ground_truth.models import GroundTruthAssessmentFull
from medguard.ground_truth.utils import load_ground_truth_samples
from medguard.scorer.models import AnalysedPatientRecord


class Evaluation(BaseModel):
    """
    Complete evaluation analysis with filtering and stratification support.

    Data is loaded once and cached, then filtered/stratified views are created
    that share the cached data but recalculate metrics for the active subset.
    """

    # === Data Source Paths ===
    output_folder_path: Path | list[Path]
    logs_path: Path | list[Path] | None = None
    raw_patient_records_path: Path | list[Path] | None = None
    analysed_patient_records_path: Path | list[Path]
    description: str | None = None

    # === Active Patient Subset ===
    # If None, all patients are active. Otherwise, only this subset is included in metrics.
    active_patient_ids: set[int] | None = None

    # === Metrics (calculated from active patients only) ===
    performance_metrics: FilterPerformanceMetrics
    evaluation_metrics: EvaluationMetrics
    calibration_metrics: CalibrationMetrics
    failure_themes: FailureThemes | None = None

    # === Cached Data (lazy-loaded, shared across filtered views) ===
    # All dicts now store lists to preserve duplicates from multiple runs
    _patient_profiles: dict[int, list[PatientProfile]] | None = PrivateAttr(default=None)
    _analysed_records: dict[int, list[AnalysedPatientRecord]] | None = PrivateAttr(default=None)
    _log_samples: dict[int, list[EvalSample]] | None = PrivateAttr(default=None)
    _ground_truth_samples_dict: dict[int, GroundTruthAssessmentFull] | None = PrivateAttr(
        default=None
    )
    _clinician_evaluations_dict: dict[int, Stage2Data] | None = PrivateAttr(default=None)

    # === Data Access (loads and caches on first access) ===
    @property
    def patient_profiles_dict(self) -> dict[int, list[PatientProfile]]:
        """Load all patient profiles (lazy), return dict[patient_id, list[profiles]] preserving duplicates."""
        if self._patient_profiles is None:
            if self.raw_patient_records_path is None:
                raise ValueError("raw_patient_records_path is required to load patient profiles")
            profiles = load_patient_profiles_from_jsonl(str(self.raw_patient_records_path))
            # Group by patient_link_id, preserving duplicates
            grouped: dict[int, list[PatientProfile]] = {}
            for p in profiles:
                if p.patient_link_id not in grouped:
                    grouped[p.patient_link_id] = []
                grouped[p.patient_link_id].append(p)
            self._patient_profiles = grouped
        return self._patient_profiles

    @property
    def patient_profiles_dict_first(self) -> dict[int, PatientProfile]:
        """Get first profile per patient (convenience for non-duplicate cases)."""
        return {
            pid: profiles[0] for pid, profiles in self.patient_profiles_dict.items() if profiles
        }

    @property
    def patient_profiles_dict_last(self) -> dict[int, PatientProfile]:
        """Get last profile per patient (convenience for non-duplicate cases)."""
        return {
            pid: profiles[-1] for pid, profiles in self.patient_profiles_dict.items() if profiles
        }

    @property
    def patient_profiles(self) -> list[PatientProfile]:
        """Get all patient profiles including duplicates."""
        return [p for profiles in self.patient_profiles_dict.values() for p in profiles]

    @property
    def analysed_records_dict(self) -> dict[int, list[AnalysedPatientRecord]]:
        """Load all analysed records (lazy), return dict[patient_id, list[records]] preserving duplicates."""
        if self._analysed_records is None:
            records = load_analysed_patient_records_from_jsonl(
                str(self.analysed_patient_records_path)
            )
            # Group by patient_link_id, preserving duplicates
            grouped: dict[int, list[AnalysedPatientRecord]] = {}
            for r in records:
                if r.patient_link_id not in grouped:
                    grouped[r.patient_link_id] = []
                grouped[r.patient_link_id].append(r)
            self._analysed_records = grouped
        return self._analysed_records

    @property
    def analysed_records_dict_first(self) -> dict[int, AnalysedPatientRecord]:
        """Get first record per patient (convenience for non-duplicate cases)."""
        return {pid: records[0] for pid, records in self.analysed_records_dict.items() if records}

    @property
    def analysed_records_dict_last(self) -> dict[int, AnalysedPatientRecord]:
        """Get last record per patient (convenience for non-duplicate cases)."""
        return {pid: records[-1] for pid, records in self.analysed_records_dict.items() if records}

    @property
    def analysed_records(self) -> list[AnalysedPatientRecord]:
        """Get all analysed records including duplicates."""
        return [r for records in self.analysed_records_dict.values() for r in records]

    @property
    def log_samples_dict(self) -> dict[int, list[EvalSample]]:
        """Load all log samples (lazy), return dict[patient_id, list[samples]] preserving duplicates."""
        if self._log_samples is None:
            if self.logs_path is None:
                return {}

            # Handle both single path and list of paths
            paths = [self.logs_path] if isinstance(self.logs_path, Path) else self.logs_path

            # Group by patient_id, preserving duplicates
            grouped: dict[int, list[EvalSample]] = {}
            for path in paths:
                samples = list(read_eval_log_samples(str(path), all_samples_required=False))
                for sample in samples:
                    patient_id = sample.metadata["patient_id"]
                    if patient_id not in grouped:
                        grouped[patient_id] = []
                    grouped[patient_id].append(sample)
            self._log_samples = grouped
        return self._log_samples

    @property
    def log_samples_dict_first(self) -> dict[int, EvalSample]:
        """Get first sample per patient (convenience for non-duplicate cases)."""
        return {pid: samples[0] for pid, samples in self.log_samples_dict.items() if samples}

    @property
    def log_samples_dict_last(self) -> dict[int, EvalSample]:
        """Get last sample per patient (convenience for non-duplicate cases)."""
        return {pid: samples[-1] for pid, samples in self.log_samples_dict.items() if samples}

    @property
    def log_samples(self) -> list[EvalSample]:
        """Get all log samples including duplicates."""
        return [s for samples in self.log_samples_dict.values() for s in samples]

    # === Ground Truth Data - taken from clinician evaluations

    @property
    def ground_truth_samples_dict(self) -> dict[int, GroundTruthAssessmentFull]:
        """Load all ground truth samples (lazy), return full dict keyed by patient_link_id."""
        if self._ground_truth_samples_dict is None:
            self._ground_truth_samples_dict = load_ground_truth_samples()
        return self._ground_truth_samples_dict

    @property
    def ground_truth_samples(self) -> list[GroundTruthAssessmentFull]:
        """Get all ground truth samples."""
        return list(self.ground_truth_samples_dict.values())

    @property
    def clinician_evaluations_dict(self) -> dict[int, Stage2Data]:
        """Load all clinician evaluations (lazy), return full dict keyed by patient_link_id."""
        if self._clinician_evaluations_dict is None:
            self._clinician_evaluations_dict = load_stage2_data_from_folder()
        return self._clinician_evaluations_dict

    @property
    def clinician_evaluations(self) -> list[Stage2Data]:
        """Get all clinician evaluations."""
        return list(self.clinician_evaluations_dict.values())

    def patient_ids(
        self, restrict_to_ground_truth: bool = False, restrict_to_clinician_evaluation: bool = False
    ) -> list[int]:
        """Get all unique patient IDs."""
        ids = (
            set(self.analysed_records_dict.keys())
            & set(self.patient_profiles_dict.keys())
            & set(self.log_samples_dict.keys())
        )
        if restrict_to_ground_truth:
            ids = (
                ids
                & set(self.ground_truth_samples_dict.keys())
                & set(self.clinician_evaluations_dict.keys())
            )

        if restrict_to_clinician_evaluation:
            ids = ids & set(self.clinician_evaluations_dict.keys())
        return list(ids)

    def filter_by_patient_ids(
        self, patient_ids: set[int], description: str | None = None
    ) -> "Evaluation":
        """
        Create new Evaluation with only specified patient IDs.

        Stage 1: Determine which patient_ids to keep
        Stage 2: Recalculate all metrics using only those patients
        """

        # Get active records for the new subset (flatten all runs)
        all_records = self.analysed_records_dict
        filtered_records: list[AnalysedPatientRecord] = []
        for pid in patient_ids:
            if pid in all_records:
                filtered_records.extend(all_records[pid])  # Add all runs for this patient

        if len(filtered_records) == 0:
            raise ValueError("No records found for the specified patient IDs")

        # Recalculate metrics using only filtered records
        performance_metrics = analysed_patient_records_to_performance_metrics(filtered_records)
        evaluation_metrics = calculate_evaluation_metrics(
            performance_metrics.TP,
            performance_metrics.TN,
            performance_metrics.FP,
            performance_metrics.FN,
        )

        # Calculate calibration metrics
        predictions = [r.medguard_analysis.intervention_probability for r in filtered_records]
        ground_truth = [len(r.patient.matched_filters) > 0 for r in filtered_records]
        calibration_metrics = calculate_calibration_metrics(predictions, ground_truth)

        # Create new evaluation
        new_eval = Evaluation(
            output_folder_path=self.output_folder_path,
            logs_path=self.logs_path,
            raw_patient_records_path=self.raw_patient_records_path,
            analysed_patient_records_path=self.analysed_patient_records_path,
            description=description or f"{self.description} (filtered)",
            active_patient_ids=patient_ids,
            performance_metrics=performance_metrics,
            evaluation_metrics=evaluation_metrics,
            calibration_metrics=calibration_metrics,
            failure_themes=None,  # Don't copy failure themes
        )

        # Copy filtered data (preserving list structure)
        new_eval._patient_profiles = {
            pid: self.patient_profiles_dict[pid]
            for pid in patient_ids
            if pid in self.patient_profiles_dict
        }
        new_eval._analysed_records = {
            pid: self.analysed_records_dict[pid]
            for pid in patient_ids
            if pid in self.analysed_records_dict
        }
        new_eval._log_samples = {
            pid: self.log_samples_dict[pid] for pid in patient_ids if pid in self.log_samples_dict
        }
        new_eval._clinician_evaluations_dict = {
            pid: self.clinician_evaluations_dict[pid]
            for pid in patient_ids
            if pid in self.clinician_evaluations_dict
        }
        new_eval._ground_truth_samples_dict = {
            pid: self.ground_truth_samples_dict[pid]
            for pid in patient_ids
            if pid in self.ground_truth_samples_dict
        }

        return new_eval

    def filter_by_analysed_record(
        self, predicate: Callable[[AnalysedPatientRecord], bool], description: str | None = None
    ) -> set[int]:
        """
        Filter using a predicate function on AnalysedPatientRecord.

        Args:
            predicate: Function that takes AnalysedPatientRecord and returns True to keep
            description: Optional description for the filtered evaluation

        Returns:
            Set of patient IDs where ANY record matches the predicate
        """
        active_records = self.analysed_records_dict
        matched_ids = set()
        for pid, records in active_records.items():
            if any(predicate(r) for r in records):
                matched_ids.add(pid)
        return matched_ids

    def filter_by_clinician_evaluation(
        self, predicate: Callable[[Stage2Data], bool], description: str | None = None
    ) -> set[int]:
        """
        Filter using a predicate function on clinician evaluation.

        Args:
            predicate: Function that takes Stage2Data and returns True to keep
            description: Optional description for the filtered evaluation

        Returns:
            Set of patient IDs that match the predicate
        """
        clinician_evaluations = self.clinician_evaluations_dict
        return {pid for pid, e in clinician_evaluations.items() if predicate(e)}

    def exclude_data_errors(self) -> "Evaluation":
        ids = self.filter_by_clinician_evaluation(lambda x: x.data_error is False)
        return self.filter_by_patient_ids(ids)

    def save(self) -> None:
        # 1 - Make the output folder if it doesn't exist
        self.output_folder_path.mkdir(parents=True, exist_ok=True)

        # 2 - Save the full model
        with open(self.output_folder_path / "evaluation.json", "w") as f:
            f.write(self.model_dump_json(indent=2))

        # 2 - Save the performance metrics
        with open(self.output_folder_path / "performance_metrics.json", "w") as f:
            f.write(self.performance_metrics.model_dump_json(indent=2))

        # 3 - Save the evaluation metrics
        with open(self.output_folder_path / "evaluation_metrics.json", "w") as f:
            f.write(self.evaluation_metrics.model_dump_json(indent=2))

        # 4 - Save the calibration metrics
        with open(self.output_folder_path / "calibration_metrics.json", "w") as f:
            f.write(self.calibration_metrics.model_dump_json(indent=2))

        # 5 - Make a "figures" folder
        figures_folder_path = self.output_folder_path / "figures"
        figures_folder_path.mkdir(parents=True, exist_ok=True)

        # 6 - Save the sankey diagrams both as svgs and as html
        self.performance_metrics.generate_full_sankey_figure().write_image(
            figures_folder_path / "full_sankey.svg", "svg"
        )
        self.performance_metrics.generate_binary_sankey_figure().write_image(
            figures_folder_path / "binary_sankey.svg", "svg"
        )

        with open(figures_folder_path / "full_sankey.html", "w") as f:
            f.write(self.performance_metrics.generate_full_sankey_figure().to_html())
        with open(figures_folder_path / "binary_sankey.html", "w") as f:
            f.write(self.performance_metrics.generate_binary_sankey_figure().to_html())

        # 7 - Save the calibration plot
        self.calibration_metrics.generate_calibration_plot().write_image(
            figures_folder_path / "calibration.svg", "svg"
        )
        with open(figures_folder_path / "calibration.html", "w") as f:
            f.write(self.calibration_metrics.generate_calibration_plot().to_html())

        # # 8 - Save the failure themes
        # with open(self.output_folder_path / "failure_themes.json", "w") as f:
        #     f.write(self.failure_themes.model_dump_json(indent=2))

        # # 9 - Save the failure themes figure
        # with open(figures_folder_path / "failure_themes.html", "w") as f:
        #     f.write(plot_failure_themes(self.failure_themes).to_html())

    def clean(self):
        # Exclude entries with data errors
        print(f"Initial size: {len(self.analysed_records_dict)} patients")

        ids = self.patient_ids(restrict_to_clinician_evaluation=True)

        print(f"Sufficient information to make determination: {len(ids)} patients")

        evaluation = self.filter_by_patient_ids(ids)
        evaluation = evaluation.exclude_data_errors()

        print(f"No data error: {len(evaluation.analysed_records)} patients")

        return evaluation


def merge_item_or_list(items_or_lists: list) -> list:
    output = []
    for item in items_or_lists:
        if isinstance(item, list):
            output.extend(item)
        else:
            output.append(item)

    return output


def merge_dictionaries(dictionaries: list[dict], accept_repeats: bool = False) -> dict:
    output = {}

    for dictionary in dictionaries:
        for key, value in dictionary.items():
            if key in output:
                if not accept_repeats:
                    raise ValueError(f"Duplicate key found: {key}")
                # If accept_repeats is True, skip (keep first value)
            else:
                output[key] = value

    return output


def merge_evaluations(evaluations: list[Evaluation]) -> Evaluation:
    patient_profiles: dict[int, list[PatientProfile]] = merge_dictionaries(
        [e.patient_profiles_dict for e in evaluations]
    )
    analysed_records: dict[int, list[AnalysedPatientRecord]] = merge_dictionaries(
        [e.analysed_records_dict for e in evaluations]
    )
    log_samples: dict[int, list[EvalSample]] = merge_dictionaries(
        [e.log_samples_dict for e in evaluations]
    )
    ground_truth_samples: dict[int, GroundTruthAssessmentFull] = merge_dictionaries(
        [e.ground_truth_samples_dict for e in evaluations], accept_repeats=True
    )
    clinician_evaluations: dict[int, Stage2Data] = merge_dictionaries(
        [e.clinician_evaluations_dict for e in evaluations], accept_repeats=True
    )

    performance_metrics = analysed_patient_records_to_performance_metrics(
        [r for records in analysed_records.values() for r in records]
    )
    evaluation_metrics = calculate_evaluation_metrics(
        performance_metrics.TP,
        performance_metrics.TN,
        performance_metrics.FP,
        performance_metrics.FN,
    )

    predictions = [
        r.medguard_analysis.intervention_probability
        for records in analysed_records.values()
        for r in records
    ]

    ground_truth = [
        len(r.patient.matched_filters) > 0 for records in analysed_records.values() for r in records
    ]

    calibration_metrics = calculate_calibration_metrics(predictions, ground_truth)

    evaluation = Evaluation(
        output_folder_path=merge_item_or_list([e.output_folder_path for e in evaluations]),
        logs_path=merge_item_or_list([e.logs_path for e in evaluations]),
        raw_patient_records_path=merge_item_or_list(
            [e.raw_patient_records_path for e in evaluations]
        ),
        analysed_patient_records_path=merge_item_or_list(
            [e.analysed_patient_records_path for e in evaluations]
        ),
        description=", ".join([e.description for e in evaluations]),
        active_patient_ids=list(analysed_records.keys()),
        performance_metrics=performance_metrics,
        evaluation_metrics=evaluation_metrics,
        calibration_metrics=calibration_metrics,
        failure_themes=None,
    )

    evaluation._patient_profiles = patient_profiles
    evaluation._analysed_records = analysed_records
    evaluation._log_samples = log_samples
    evaluation._ground_truth_samples_dict = ground_truth_samples
    evaluation._clinician_evaluations_dict = clinician_evaluations

    return evaluation
