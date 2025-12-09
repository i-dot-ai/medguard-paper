"""Utility functions for the MedGuard preprocessing pipeline."""

from pathlib import Path
from typing import List
from pydantic import BaseModel


def export_pydantic_to_jsonl(
    models: List[BaseModel], output_path: str = "outputs/patient_sample.jsonl"
) -> None:
    """
    Export a list of Pydantic models to a JSONL file.

    Args:
        models: List of Pydantic model instances
        output_path: Path to output JSONL file
    """
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        for model in models:
            f.write(model.model_dump_json() + "\n")
