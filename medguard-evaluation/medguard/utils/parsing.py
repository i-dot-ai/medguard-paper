import json
from pathlib import Path
from typing import Any, Generator, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def read_jsonl(file_path: str) -> Generator[Any, None, None]:
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                yield json.loads(line)


def save_pydantic_list_to_jsonl(pydantic_list: list[BaseModel], path: str):
    with open(path, "w") as f:
        for item in pydantic_list:
            f.write(item.model_dump_json() + "\n")


def load_pydantic_from_json(model_class: Type[T], path: str | Path) -> T:
    """
    Load a single Pydantic model from a JSON file.

    Args:
        model_class: The Pydantic model class to load into
        path: Path to the JSON file

    Returns:
        Instance of model_class

    Example:
        eval = load_pydantic_from_json(Evaluation, "outputs/evaluation.json")
    """
    with open(path, "r") as f:
        data = json.load(f)
    return model_class.model_validate(data)


def load_pydantic_list_from_jsonl(model_class: Type[T], path: str | Path) -> list[T]:
    """
    Load a list of Pydantic models from a JSONL file.

    Args:
        model_class: The Pydantic model class to load into
        path: Path to the JSONL file

    Returns:
        List of model_class instances

    Example:
        records = load_pydantic_list_from_jsonl(AnalysedPatientRecord, "results.jsonl")
    """
    models = []
    for data in read_jsonl(str(path)):
        models.append(model_class.model_validate(data))
    return models
