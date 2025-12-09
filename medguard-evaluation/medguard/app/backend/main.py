"""
FastAPI backend for MedGuard evaluation clinician interface.

This application served the internal evaluation interface used by clinicians to
review MedGuard outputs within the Trusted Research Environment. It is included
for reference but requires access to patient data to function.
"""

import json
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from medguard.app.backend.combined_data_loader import combined_data_store as data_store
from medguard.app.backend.services import get_all_events, get_post_smr_events, get_pre_smr_events
from medguard.scorer.models import EvaluationAnalysis, MedGuardAnalysis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - load data on startup."""
    # Startup
    data_file = Path(".data/analysed_patients_with_filters.jsonl")
    if not data_file.exists():
        print(f"Warning: Data file {data_file} not found")
    else:
        data_store.load_data(data_file)

    yield

    # Shutdown (if needed)
    print("Shutting down application")


# Initialize FastAPI app
app = FastAPI(
    title="MedGuard Evaluation API",
    description="Backend API for clinician evaluation of ground truth output",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "MedGuard Evaluation API", "status": "running"}


@app.get("/patients", response_model=List[str])
async def get_patients() -> List[str]:
    """Get list of all patient IDs as strings to preserve precision."""
    patient_ids = data_store.get_all_patient_ids()
    print(f"Getting list of all patient IDs: {patient_ids}")
    # Return as strings to avoid JavaScript number precision issues
    return [str(pid) for pid in patient_ids]


@app.get("/patients/completed")
async def get_completed_patients() -> List[str]:
    """Get list of patient IDs that have completed Stage 1 evaluations."""
    evaluations_dir = Path(".data/evaluations")
    if not evaluations_dir.exists():
        return []

    completed_patients = []
    for file_path in evaluations_dir.glob("*.json"):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                if data.get("stage") == 1:  # Only Stage 1 indicates completion
                    patient_id = data.get("patient_id")
                    if patient_id and patient_id not in completed_patients:
                        completed_patients.append(patient_id)
        except (json.JSONDecodeError, KeyError):
            continue

    return completed_patients


@app.get("/patients/{patient_id}")
async def get_patient(patient_id: str) -> Dict[str, Any]:
    """Get full patient profile."""
    # Convert string back to int for lookup
    record = data_store.get_patient_record(int(patient_id))
    if not record:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    # Return as dict with field names instead of aliases
    return record.patient.model_dump(by_alias=False)


@app.get("/patients/{patient_id}/events/pre-smr")
async def get_patient_pre_smr_events(patient_id: str) -> List[Dict[str, Any]]:
    """Get events available before the SMR."""
    record = data_store.get_patient_record(int(patient_id))
    if not record:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    return get_pre_smr_events(record)


@app.get("/patients/{patient_id}/events/post-smr")
async def get_patient_post_smr_events(patient_id: str) -> List[Dict[str, Any]]:
    """Get events that occurred after the SMR."""
    record = data_store.get_patient_record(int(patient_id))
    if not record:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    return get_post_smr_events(record)


@app.get("/patients/{patient_id}/events/all")
async def get_patient_all_events(patient_id: str) -> List[Dict[str, Any]]:
    """Get all events for a patient."""
    record = data_store.get_patient_record(int(patient_id))
    if not record:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    return get_all_events(record)


@app.get("/patients/{patient_id}/analysis/medguard", response_model=Optional[MedGuardAnalysis])
async def get_medguard_analysis(patient_id: str) -> Optional[MedGuardAnalysis]:
    """Get MedGuard analysis."""
    record = data_store.get_patient_record(int(patient_id))
    if not record:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return record.medguard_analysis


@app.get("/patients/{patient_id}/analysis/evaluation", response_model=Optional[EvaluationAnalysis])
async def get_evaluation_analysis(patient_id: str) -> Optional[EvaluationAnalysis]:
    """Get evaluation analysis."""
    record = data_store.get_patient_record(int(patient_id))
    if not record:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return record.evaluation_analysis


@app.get("/patients/{patient_id}/analysis-date")
async def get_patient_analysis_date(patient_id: str) -> Dict[str, Any]:
    """Get the analysis date for a patient."""
    record = data_store.get_patient_record(int(patient_id))
    if not record:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    return {"patient_id": patient_id, "analysis_date": record.analysis_date.isoformat()}


@app.post("/patients/{patient_id}/evaluation")
async def save_evaluation(patient_id: str, evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save clinician evaluation data (mock implementation)."""
    # Verify patient exists
    record = data_store.get_patient_record(int(patient_id))
    if not record:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    # Create evaluations directory if it doesn't exist
    evaluations_dir = Path(".data/evaluations")
    evaluations_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = evaluations_dir / f"{patient_id}_{timestamp}.json"

    # Add metadata to evaluation
    evaluation_with_metadata = {
        "patient_id": patient_id,
        "smr_date": record.analysis_date.isoformat(),
        "evaluation_timestamp": datetime.now().isoformat(),
        "stage": evaluation_data.get("stage"),
        "data": evaluation_data,
    }

    # Save to JSON file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(evaluation_with_metadata, f, indent=2)

    print(f"Saved evaluation for patient {patient_id} to {filename}")

    return {"success": True, "message": "Evaluation saved successfully", "filename": str(filename)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
