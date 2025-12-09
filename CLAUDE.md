# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MedGuard is a research project for evaluating LLM-based medication safety reviews in NHS primary care. The repository contains two main subprojects:

- **medguard-preprocessing**: Data processing pipeline for building patient profiles from NHS electronic health records and implementing PINCER medication safety filters
- **medguard-evaluation**: Evaluation framework for assessing LLM performance on medication review tasks using inspect-ai

## Common Commands

### medguard-preprocessing
```bash
cd medguard-preprocessing
uv sync
uv run python scripts/generate_patient_profiles_with_filters.py
```

### medguard-evaluation
```bash
cd medguard-evaluation
uv sync
playwright install chromium  # Required for figure generation

# Run evaluation
uv run inspect eval evals/eval_reasoning.py --model openai/azure/gpt-4.1-mini --limit 10

# Generate paper figures
uv run python scripts/generate_analyses.py

# Serve local model with vLLM
make serve-vllm model=meta-llama/Llama-3.1-8B-Instruct

# Run evaluation with vLLM
make run-eval script=eval_reasoning model=meta-llama/Llama-3.1-8B-Instruct limit=100

# Lint and format
uv run ruff check .
uv run ruff format .
```

### Frontend (medguard-evaluation/medguard/app/frontend)
```bash
pnpm install
pnpm dev    # Development server on :3000
pnpm build
```

### Backend (medguard-evaluation)
```bash
uv run python -m medguard.app.backend.main  # Server on :8000
```

## Architecture

### medguard-preprocessing

Core components:
- `src/medguard/data_processor.py` - `ModularPatientDataProcessor` class orchestrates patient profile building
- `src/medguard/models.py` - Pydantic models (`PatientProfile`, `Medication`, `GPEvent`, etc.) with `.prompt()` methods for LLM-friendly text
- `src/medguard/sql_loader.py` - SQL template loading with variable injection
- `src/medguard/sql/filters/` - 10 PINCER medication safety filter SQL files (005, 006, 010, 016, 023, 026, 028, 033, 043, 055)

Data flow: NHS parquet files → DuckDB queries → Patient profiles with filter matches

### medguard-evaluation

Built on [inspect-ai](https://github.com/UKGovernmentBEIS/inspect_ai) for evaluation:
- `evals/` - Task definitions (eval_reasoning.py, eval_self_critique.py)
- `medguard/agents/` - Agent implementations:
  - `reasoning_agent/` - Single-pass reasoning ("the System" in paper)
  - `isimpathy/` - Multi-stage ISimpathy workflow
  - `self_critique/` - Meta-agent for output refinement
- `medguard/scorer/` - LLM-as-judge scoring system:
  - `pincer_filters/scorer.py` - PINCER filter-based evaluation
  - `ground_truth/scorer.py` - Clinician ground truth comparison
- `medguard/analysis/` - Paper figure generation:
  - Base class: `EvaluationAnalysisBase` with `execute()`, `run()`, `run_figure()` pattern
  - `secondary/` - Additional analyses not in main paper
- `medguard/tools/` - Drug information lookup (BNF, NICE, PubMed)

### Three-Level Hierarchical Evaluation

1. **Level 1**: Issue identification (did the system flag a patient who needed review?)
2. **Level 2**: Issue correctness (did it identify the right issues?)
3. **Level 3**: Intervention appropriateness (did it propose correct interventions?)

## Critical: UK SNOMED CT Extension Codes

UK prescription data uses UK dm+d codes (13-15 digits containing `1000001`), NOT international SNOMED codes (6-9 digits). Filters using international codes will return zero results.

```sql
-- International code (won't match prescriptions)
('387207008')  -- Ibuprofen (substance)

-- UK dm+d codes (match actual prescriptions)
('42104811000001109')  -- Ibuprofen 200mg tablet
```

When writing SQL filters, use the SNOMED MCP tool with `uk_extension_only=True` to get matching codes.

## SQL Filter Development

See `medguard-preprocessing/src/medguard/sql/filters/FILTER.md` for comprehensive guidelines.

Key points:
- Use `{gp_prescriptions}` for medications (GPPrescriptions table)
- Use `{gp_events_enriched}` for clinical diagnoses
- Use `{patient_view}` (singular) for demographics
- Use `DATE_DIFF('year', p.Dob, CURRENT_DATE)` for age calculations
- Prioritize precision over recall

## Python Requirements

- medguard-preprocessing: Python 3.12+
- medguard-evaluation: Python 3.10.17 (exact version required)
