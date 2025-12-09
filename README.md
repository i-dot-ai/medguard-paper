# MedGuard

Evaluation framework for LLM-based medication safety review, developed for research evaluating AI-assisted medication review in NHS primary care.

## Repository Structure

```
medguard-paper/
├── medguard-preprocessing/    # Patient profile construction and PINCER filters
│   ├── src/medguard/
│   │   ├── data_processor.py  # Patient profile building
│   │   ├── models.py          # Pydantic models with .prompt() methods
│   │   └── sql/filters/       # 10 PINCER medication safety filter SQL files
│   └── scripts/               # Profile generation scripts
│
├── medguard-evaluation/       # LLM evaluation framework
│   ├── evals/                 # inspect-ai task definitions
│   ├── medguard/
│   │   ├── agents/            # Agent implementations (reasoning, ISimpathy, self-critique)
│   │   ├── scorer/            # LLM-as-judge scoring system
│   │   ├── analysis/          # Paper figure generation
│   │   └── app/               # Clinician evaluation interface (FastAPI + Next.js)
│   └── scripts/               # Analysis and figure generation
```

## medguard-preprocessing

Data processing pipeline for building patient profiles from NHS electronic health records and implementing PINCER medication safety filters. See [medguard-preprocessing/README.md](medguard-preprocessing/README.md) for detailed documentation.

```bash
cd medguard-preprocessing
uv sync
uv run python scripts/generate_patient_profiles_with_filters.py
```

Requires Python 3.12+ and NHS patient data in matching parquet format.

## medguard-evaluation

Evaluation framework built on [inspect-ai](https://github.com/UKGovernmentBEIS/inspect_ai). See [medguard-evaluation/README.md](medguard-evaluation/README.md) for detailed documentation.

```bash
cd medguard-evaluation
uv sync
playwright install chromium  # For figure generation

# Run evaluation
uv run inspect eval evals/eval_reasoning.py --model openai/azure/gpt-4.1-mini --limit 10

# Generate paper figures
uv run python scripts/generate_analyses.py

# Serve local model with vLLM
make serve-vllm model=meta-llama/Llama-3.1-8B-Instruct

# Run evaluation with vLLM
make run-eval script=eval_reasoning model=meta-llama/Llama-3.1-8B-Instruct limit=100
```

Requires Python 3.10.17.

### Clinician Evaluation App

```bash
# Backend (from medguard-evaluation/)
uv run python -m medguard.app.backend.main  # Server on :8000

# Frontend (from medguard-evaluation/medguard/app/frontend/)
pnpm install
pnpm dev  # Server on :3000
```

## Data Availability

Patient data was accessed within an NHS Trusted Research Environment and cannot be shared. The repository contains evaluation code, agent implementations, and analysis scripts. The PINCER filter SQL and patient profile construction code can be adapted for other NHS datasets.

## License

MIT License — see [LICENSE](LICENSE) for details.
