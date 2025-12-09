import json
import os
from collections import defaultdict
from typing import Any

from .models import AnalysisData, Stage1Data, Stage2Data


def load_evaluations_from_folder(folder_path) -> list[AnalysisData]:
    files = os.listdir(folder_path)
    filepaths = [os.path.join(folder_path, file) for file in files if file.endswith(".json")]

    evaluation_data = []

    for filepath in filepaths:
        with open(filepath, "r") as f:
            data = json.load(f)
            evaluation_data.append(data)

    data_dict = defaultdict[Any, dict](dict)

    for result in evaluation_data:
        patient_id = result["patient_id"]
        stage = result["stage"]
        data_dict[patient_id][stage] = result["data"]["data"]

    data_dict = dict[Any, dict](data_dict)

    pydantic_list: list[AnalysisData] = []

    for key, value in data_dict.items():
        if value.get(1) and value.get(2):
            pydantic_list.append(
                AnalysisData(
                    patient_id=key, stage1=Stage1Data(**value[1]), stage2=Stage2Data(**value[2])
                )
            )
        else:
            pydantic_list.append(
                AnalysisData(patient_id=key, stage1=Stage1Data(**value[1]), stage2=None)
            )

    return pydantic_list


def load_stage2_data_from_folder(
    folder_paths: list[str] = [
        "outputs/evaluations/evaluations_test_200",
        "outputs/evaluations/evaluations_test_100",
    ],
) -> dict[int, Stage2Data]:
    analysis_data = []
    for path in folder_paths:
        analysis_data.extend(load_evaluations_from_folder(path))

    return {
        analysis_data.patient_id: analysis_data.stage2
        for analysis_data in analysis_data
        if analysis_data.stage2
    }
