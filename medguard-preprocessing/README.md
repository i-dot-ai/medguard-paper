# MedGuard Preprocessing

Data processing pipeline for the paper: **"A Real-World Evaluation of LLM Medication Safety Reviews in NHS Primary Care"**

This repository contains the preprocessing infrastructure used to build patient profiles from NHS electronic health records and implement PINCER medication safety filters for evaluating large language models on medication review tasks.

## Paper Context

This codebase supports the evaluation described in our paper, which:

- **Evaluates LLM medication safety review** using real NHS patient data from a Trusted Research Environment
- **Implements 10 PINCER medication safety filters** to identify potentially hazardous prescribing patterns
- **Builds structured patient profiles** from GP events, prescriptions, hospital episodes, and other clinical data sources
- **Enables stratified sampling** to create balanced evaluation cohorts matching cases to controls

## Quick Start

```bash
# Install dependencies
uv sync

# Generate patient profiles with filter-based sampling
uv run python scripts/generate_patient_profiles_with_filters.py
```

Requires Python 3.12+ and access to NHS patient data from Cheshire and Merseyside in matching parquet format.

## Mapping Paper Concepts to Code

### PINCER Filters (Section 2.3 in paper)

The 10 validated PINCER medication safety filters are implemented as SQL queries:

| Filter ID | Clinical Scenario | SQL File |
|-----------|-------------------|----------|
| 005 | Diltiazem/verapamil in heart failure | `src/medguard/sql/filters/005_diltiazem_verapamil_heart_failure.sql` |
| 006 | Beta-blocker in asthma without cardiac indication | `src/medguard/sql/filters/006_asthma_beta_blocker_no_cardiac_condition.sql` |
| 010 | Antipsychotic in elderly dementia without psychosis | `src/medguard/sql/filters/010_antipsychotic_elderly_dementia_not_psychosis.sql` |
| 016 | Metformin with severe renal impairment (eGFR ≤30) | `src/medguard/sql/filters/016_metformin_renal_impairment_egfr_30.sql` |
| 023 | Combined hormonal contraceptive with BMI ≥40 | `src/medguard/sql/filters/023_chc_bmi_40_or_greater.sql` |
| 026 | Methotrexate without folic acid | `src/medguard/sql/filters/026_methotrexate_no_folic_acid.sql` |
| 028 | NSAID + peptic ulcer without gastroprotection | `src/medguard/sql/filters/028_nsaid_peptic_ulcer_no_gastroprotection.sql` |
| 033 | Warfarin + antibiotic without INR monitoring | `src/medguard/sql/filters/033_warfarin_antibiotic_no_inr.sql` |
| 043 | Loop diuretic in elderly without renal function check | `src/medguard/sql/filters/043_elderly_loop_diuretic_no_renal_check.sql` |
| 055 | Methotrexate without LFT monitoring | `src/medguard/sql/filters/055_methotrexate_no_lft_monitoring.sql` |

Each filter returns temporal periods (`start_date`, `end_date`) when patients matched the hazardous prescribing criteria.

### Patient Profile Building (Section 2.2)

The `ModularPatientDataProcessor` class (`src/medguard/data_processor.py`) orchestrates profile construction:

```python
from medguard.data_processor import ModularPatientDataProcessor

processor = ModularPatientDataProcessor(db_path="path/to/data")

# Build profiles for patients matching PINCER filters
profiles = processor.build_patient_profiles(
    sampling_strategy="filter_based",
    n_patients=200
)
```

Patient profiles aggregate:
- **Demographics**: Age, sex, IMD score, frailty score
- **QOF registers**: Chronic disease registers (diabetes, asthma, COPD, etc.)
- **Medications**: Active prescriptions with start/end dates
- **GP Events**: Clinical observations coded in SNOMED CT
- **Hospital data**: Inpatient episodes, A&E visits, outpatient appointments
- **Filter matches**: Periods when PINCER criteria were met

### Stratified Sampling (Section 2.3.5)

The negative case sampling strategy matches controls to positive cases on:
- Age (10-year bins)
- Gender
- Number of GP events since 2020 (quartiles)
- Number of active prescriptions (quartiles)

```python
# Get balanced sample with stratification
patients = processor.get_balanced_patient_sample(
    n_positive=100,
    n_negative=100,
    stratify_on=["age_bin", "gender", "gp_events_quartile", "prescriptions_quartile"]
)
```

### Semi-Automated Filter Generation (Section 2.3.2)

Filters were developed using Claude Code with a custom MCP server for SNOMED code identification.

See `src/medguard/sql/filters/FILTER.md` for comprehensive filter development guidelines.

## Repository Structure

```
medguard-preprocessing/
├── LICENSE
├── README.md
├── CLAUDE.md                 # Claude Code instructions
├── pyproject.toml
├── src/
│   └── medguard/
│       ├── data_processor.py # Main orchestrator for patient profile building
│       ├── models.py         # Pydantic models: PatientProfile, Medication, etc.
│       ├── sql_loader.py     # SQL template loading and variable injection
│       ├── sql/
│       │   ├── filters/      # 10 PINCER safety filter SQL files
│       │   │   └── FILTER.md # Filter development guidelines
│       │   ├── views/        # Enriched data views
│       │   ├── sampling/     # Patient sampling strategies
│       │   └── profile_building/
│       └── analysis/         # Statistical analysis modules
└── scripts/
    ├── generate_patient_profiles.py
    ├── generate_patient_profiles_with_filters.py
    ├── generate_no_filter_patient_profiles.py
    ├── run_statistics_analyses.py
    └── generate_all_plots.py
```

## Key Data Models

All models in `src/medguard/models.py` support a `.prompt()` method for generating LLM-friendly text representations:

```python
from medguard.models import PatientProfile

profile = profiles[0]

# Generate text prompt for LLM evaluation
prompt_text = profile.prompt()

# Access structured data
print(f"Patient has {len(profile.medications)} active medications")
print(f"Filter matches: {[f.filter_type.value for f in profile.filter_matches]}")
```

### Event Types

| Model | Description |
|-------|-------------|
| `Medication` | Active prescription with start/end dates, dosage |
| `GPEvent` | Clinical observation (SNOMED-coded) |
| `InpatientEpisode` | Hospital admission |
| `AEVisit` | A&E attendance |
| `OutpatientVisit` | Outpatient appointment |
| `Allergy` | Recorded allergies |
| `FilterMatch` | Period when patient matched a PINCER filter |

## Analysis Framework

Statistical analyses extend `AnalysisBase` (`src/medguard/analysis/base.py`):

```python
from medguard.analysis.pincer_filter_statistics import PINCERFilterStatistics

analysis = PINCERFilterStatistics(processor)
df, path = analysis.run()  # Execute SQL, save CSV
analysis.run_figure()       # Generate and save plots
```

## Data Requirements

Expected parquet files in `patient-data-subset/PopHealth/Medguard/Extract/`:

| Table | Description |
|-------|-------------|
| `SharedCare_Patient` | Demographics (Dob, Sex, IMD_Score, FrailtyScore) |
| `SharedCare_GP_Events` | Clinical observations (SNOMED-coded) |
| `GPPrescriptions` | Consolidated prescription "islands" |
| `SharedCare_Acute_Inpatients` | Hospital inpatient episodes |
| `SharedCare_Acute_AE` | A&E visits |
| `SharedCare_Acute_Outpatients` | Outpatient appointments |
| `SharedCare_Reference_SnomedCT` | SNOMED code descriptions |

## UK SNOMED CT Extension Codes

**Critical**: UK prescription data uses UK dm+d codes (13-15 digits containing `1000001`), not international SNOMED codes (6-9 digits). Filters using international codes will return zero results.

```sql
-- International code (for reference only)
('387207008')  -- Ibuprofen (substance) - won't match prescriptions

-- UK dm+d codes (match actual prescriptions)
('42104811000001109')  -- Ibuprofen 200mg tablet
('42104911000001104')  -- Ibuprofen 400mg tablet
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

This work was conducted within the NHS Trusted Research Environment provided by GraphNet, using electronic health records from Cheshire and Merseyside NHS Trust.
