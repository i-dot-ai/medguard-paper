# MedGuard Evaluation App

A clinical evaluation interface for assessing medication review outputs through progressive information revelation.

## Overview

This application provides a web interface for clinicians to evaluate ground truth medication review scenarios across four progressive stages. It uses a split-panel design where clinicians review patient information while completing structured evaluation forms.

### Architecture

- **Backend**: FastAPI server serving patient data and analysis
- **Frontend**: Next.js React application with TypeScript and Tailwind CSS
- **Data**: JSONL patient records with comprehensive clinical event histories

### Progressive Information Revelation

The app implements a 4-stage evaluation process:

1. **Stage 1 - Pre-SMR Clinical Assessment**: Review patient history before Structured Medication Review (SMR)
2. **Stage 2 - MedGuard Review**: Assess MedGuard AI analysis and recommendations  
3. **Stage 3 - Post-SMR Information**: Review complete information including post-SMR events
4. **Stage 4 - Ground Truth Comparison**: Compare assessments with established ground truth

Each stage progressively reveals more information while automatically switching to relevant analysis tabs.

## Quick Start

### Prerequisites

- Python 3.10.17
- Node.js 18+
- Patient data file (`.data/output_parsed_all.jsonl`)

### Setup

1. **Backend Setup**:
   ```bash
   # From project root
   uv sync
   source .venv/bin/activate
   
   # Start backend server
   uv run python -m medguard.app.backend.main
   ```
   Server runs on http://localhost:8000

2. **Frontend Setup**:
   ```bash
   # Navigate to frontend directory
   cd medguard/app/frontend
   
   # Install dependencies
   pnpm install
   
   # Start development server
   pnpm dev
   ```
   Frontend runs on http://localhost:3000

### Usage

1. Navigate to http://localhost:3000
2. Select a patient ID from the available list
3. Progress through the 4 evaluation stages
4. Each stage saves evaluation data to `.data/evaluations/`

## Interface Components

### Left Panel (60% width)
- **Patient History Tab**: Demographics, clinical events, comprehensive search
- **MedGuard Analysis Tab**: AI-generated medication review (Stage 2+)
- **Change Analysis Tab**: Medication change consensus analysis (Stage 3+)  
- **Evaluation Analysis Tab**: Final evaluation scoring (Stage 4+)

### Right Panel (40% width)
- **Stage Navigation**: Visual progress through evaluation stages
- **Evaluation Forms**: Stage-specific assessment forms with validation
- **Patient Header**: Patient ID display with home navigation

### Key Features

- **Progressive Data Revelation**: Information availability increases by stage
- **Comprehensive Search**: Full-text search across all clinical event details
- **Event Filtering**: Filter by event type, date range, and search terms
- **Specialized Event Cards**: Custom display for GP events, prescriptions, inpatient episodes, etc.
- **Clinical Context**: QOF registers and frailty deficits with full descriptions
- **Modern UI**: Card-based design with responsive layout and smooth transitions

## Data Model

### Patient Profile
- Demographics (age calculated from DOB, sex, ethnicity)
- Clinical scores (frailty, mortality risk, IMD deprivation)
- QOF registers and frailty deficits with lookup descriptions
- Comprehensive event timeline

### Clinical Events
- **GP Events**: Observations, SMR status, clinical notes
- **Prescriptions**: Medications with dosage, active periods, repeat status
- **Inpatient Episodes**: Admissions, discharges, specialties, wards
- **A&E Visits**: Emergency attendances with reasons and outcomes
- **Outpatient Visits**: Specialist appointments and referrals
- **Allergies**: Allergen details, severity, reaction codes
- **Medication Changes**: SMR-driven medication modifications

### Analysis Data
- **MedGuard Analysis**: AI medication review with confidence scores
- **Change Analysis**: Medication change predictability and reasoning
- **Evaluation Analysis**: Final evaluation scoring and rationale

## API Endpoints

### Patient Data
- `GET /patients` - List all patient IDs
- `GET /patients/{patient_id}` - Get patient profile
- `GET /patients/{patient_id}/events/pre-smr` - Pre-SMR events only
- `GET /patients/{patient_id}/events/post-smr` - Post-SMR events only  
- `GET /patients/{patient_id}/events/all` - All patient events

### Analysis Data
- `GET /patients/{patient_id}/analysis/medguard` - MedGuard AI analysis
- `GET /patients/{patient_id}/analysis/medication-change` - Change consensus analysis
- `GET /patients/{patient_id}/analysis/evaluation` - Evaluation analysis
- `GET /patients/{patient_id}/smr-date` - SMR date for progressive revelation

### Evaluation Submission
- `POST /patients/{patient_id}/evaluation` - Save clinician evaluation data

## Development

### Frontend Structure
```
medguard/app/frontend/
├── app/
│   ├── evaluation/[patientId]/page.tsx    # Main evaluation interface
│   └── page.tsx                           # Home page with patient list
├── components/
│   ├── evaluation/                        # Stage-specific evaluation forms
│   │   ├── Stage1Form.tsx                # Pre-SMR assessment
│   │   ├── Stage2Form.tsx                # MedGuard review
│   │   ├── Stage3Form.tsx                # Post-SMR assessment
│   │   └── Stage4Form.tsx                # Ground truth comparison
│   └── information/                       # Information display components
│       ├── PatientHistoryTab.tsx         # Main patient info and events
│       ├── EventFilters.tsx              # Search and filtering
│       └── [EventType]Card.tsx           # Specialized event displays
├── lib/
│   └── api.ts                            # API client functions
└── types/
    └── api.ts                            # TypeScript interfaces
```

### Backend Structure
```
medguard/app/backend/
├── main.py                               # FastAPI application
├── data_loader.py                        # Patient data loading
└── services.py                           # Event filtering services
```

### Development Commands

```bash
# Backend
uv run python -m medguard.app.backend.main

# Frontend
cd medguard/app/frontend
pnpm dev
pnpm build
pnpm start

# Code quality
uv run ruff check .
uv run ruff format .
```

## Data Requirements

The application requires patient data in JSONL format at `.data/output_parsed_all.jsonl`. Each line contains:
- Patient profile with demographics and clinical scores
- Aggregated clinical events (GP visits, prescriptions, hospital episodes)
- Analysis data (MedGuard, medication change consensus, evaluation scoring)
- SMR dates for progressive revelation timing

Contact the MedGuard project team for access to evaluation datasets.

## Evaluation Output

Clinician evaluations are saved as JSON files in `.data/evaluations/` with:
- Patient ID and SMR date context
- Stage-specific evaluation responses
- Timestamp and metadata for analysis