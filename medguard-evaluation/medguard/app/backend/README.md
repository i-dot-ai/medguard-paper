# MedGuard Evaluation Backend

FastAPI backend for clinician evaluation of ground truth output.

## Running the Backend

```bash
# From project root
uvicorn medguard.app.backend.main:app --reload

# Or run directly
python -m medguard.app.backend.main
```

The API will be available at http://localhost:8000

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

- `GET /patients` - List all patient IDs
- `GET /patients/{patient_id}` - Get full patient profile
- `GET /patients/{patient_id}/events/pre-smr` - Events before SMR
- `GET /patients/{patient_id}/events/post-smr` - Events after SMR  
- `GET /patients/{patient_id}/events/all` - All patient events
- `GET /patients/{patient_id}/analysis/medication-change` - Medication change analysis
- `GET /patients/{patient_id}/analysis/evaluation` - Evaluation analysis
- `GET /patients/{patient_id}/analysis/medguard` - MedGuard analysis
- `GET /patients/{patient_id}/smr-date` - Get SMR date for patient

## Data Source

Currently hardcoded to load from: `.data/2025-09-02-synthetic-dataset.jsonl`