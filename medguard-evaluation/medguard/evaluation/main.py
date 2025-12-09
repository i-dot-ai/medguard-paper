from medguard.evaluation.performance_metrics.filter.performance_metrics import (
    analysed_patient_records_to_performance_metrics,
)

import datetime
from datetime import datetime, timezone
from pathlib import Path

from medguard.evaluation.calibration_metrics import calculate_calibration_metrics
from medguard.evaluation.evaluation_metrics import calculate_evaluation_metrics
from medguard.evaluation.evaluation import Evaluation
from medguard.utils.parsing import save_pydantic_list_to_jsonl
from medguard.evaluation.utils import load_patient_profiles_from_jsonl
from medguard.evaluation.pipeline import (
    load_analysed_patient_records_from_eval_log,
    add_patient_profiles_to_analysed_patient_records,
)


def generate_evaluation_from_logs_and_patient_records(
    logs_path: Path | list[Path], patient_records_path: Path, description: str | None = None
) -> Evaluation:
    # 1 - Make the output folder if it doesn't exist
    output_folder_path = (
        Path(__file__).parent.parent.parent
        / "outputs"
        / datetime.now(timezone.utc).strftime("%Y%m%d")
    )

    if description is not None:
        output_folder_path = output_folder_path / description
    else:
        hms = datetime.now(timezone.utc).strftime("%H%M%S")
        output_folder_path = output_folder_path / hms

    output_folder_path.mkdir(parents=True, exist_ok=True)

    # 1 - Get the complete patient records
    print("Loading analysed patient records from eval log...")

    # Handle both single path and list of paths
    if isinstance(logs_path, list):
        # Load from multiple log files and combine (keeping all entries including duplicates)
        analysed_patient_records = []
        for path in logs_path:
            records = load_analysed_patient_records_from_eval_log(str(path))
            analysed_patient_records.extend(records)
    else:
        analysed_patient_records = load_analysed_patient_records_from_eval_log(str(logs_path))

    patient_profiles = load_patient_profiles_from_jsonl(patient_records_path)

    complete_patient_records = add_patient_profiles_to_analysed_patient_records(
        analysed_patient_records, patient_profiles
    )
    save_pydantic_list_to_jsonl(
        complete_patient_records, output_folder_path / "patient_records.jsonl"
    )

    # 2 - Get the performance metrics
    print("Generating performance metrics...")
    performance_metrics = analysed_patient_records_to_performance_metrics(complete_patient_records)

    # 3 - Generate the evaluation metrics
    print("Generating evaluation metrics...")
    evaluation_metrics = calculate_evaluation_metrics(
        performance_metrics.TP,
        performance_metrics.TN,
        performance_metrics.FP,
        performance_metrics.FN,
    )

    # 4 - Generate the calibration metrics
    print("Generating calibration metrics...")
    predictions = [
        record.medguard_analysis.intervention_probability for record in complete_patient_records
    ]
    ground_truth = [len(record.patient.matched_filters) > 0 for record in complete_patient_records]
    calibration_metrics = calculate_calibration_metrics(predictions, ground_truth)

    # # 5 - Generate the failure themes
    # print("Generating failure themes...")
    # failure_themes = asyncio.run(get_failure_themes_from_analysed_patient_records(complete_patient_records))

    # 6 - Generate the evaluation object
    print("Generating evaluation object...")
    evaluation = Evaluation(
        output_folder_path=output_folder_path,
        logs_path=logs_path,
        raw_patient_records_path=patient_records_path,
        analysed_patient_records_path=output_folder_path / "patient_records.jsonl",
        description=description,
        performance_metrics=performance_metrics,
        evaluation_metrics=evaluation_metrics,
        calibration_metrics=calibration_metrics,
        failure_themes=None,
    )

    # 7 - Save the evaluation
    evaluation.save()

    return evaluation
