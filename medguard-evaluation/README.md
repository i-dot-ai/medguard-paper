# MedGuard Evaluation

An evaluation framework for LLM-based medication safety review systems, developed as part of a research study evaluating AI-assisted medication review in primary care.

## Overview

This repository contains the evaluation pipeline and analysis code used to assess LLM performance on medication safety review tasks. The framework implements:

- **Three-Level Hierarchical Evaluation**: Assesses system performance at increasing granularity:
  - Level 1: Issue identification (did the system flag a patient who needed review?)
  - Level 2: Issue correctness (did it identify the right issues?)
  - Level 3: Intervention appropriateness (did it propose correct interventions?)

- **Failure Mode Analysis**: Systematic categorisation of how and why medication safety systems fail, with clinician-assessed harm severity ratings.

- **Multi-Model Comparison**: Evaluation infrastructure supporting comparison across different foundation models and configurations.

- **Automated Scoring**: LLM-as-judge scoring system calibrated against clinician ground truth for scalable evaluation.

## Repository Structure

```
medguard/
├── agents/           # LLM agent implementations (ISimpathy, reasoning agents)
├── analysis/         # Paper figure generation and analysis scripts
│   └── secondary/    # Additional analyses not in main paper
├── evaluation/       # Evaluation pipeline and metrics
├── scorer/           # Ground truth and automated scoring
└── tools/            # Drug information lookup tools (BNF, NICE, PubMed)

evals/                # inspect-ai evaluation task definitions
scripts/              # Analysis and figure generation scripts
outputs/eval_analyses/  # Generated figures and analysis outputs
```

## Key Components

### Evaluation Framework
Built on [inspect-ai](https://github.com/UKGovernmentBEIS/inspect_ai), the evaluation pipeline processes patient profiles through configurable agent architectures and scores outputs against clinician-established ground truth.

### Analysis Pipeline
Run `scripts/generate_analyses.py` to generate all paper figures:
- Figure 1a-e: Workflow, hierarchical evaluation, failure modes, complexity analysis, model comparison
- Figure 2: Failure mode vignettes

### Agent Architectures
- **ISimpathy Agent**: Multi-stage workflow implementing the ISimpathy medication review framework
- **Reasoning Agent**: Simplified single-pass reasoning approach. This is "the System" used in the paper.
- **Self-Critique Agent**: Meta-agent for output refinement

## Data Availability

The patient data used in this study was accessed within an NHS Trusted Research Environment and cannot be shared. The repository contains:
- Evaluation code and analysis scripts
- Generated figures and summary statistics
- Agent and scorer implementations

## Setup

```bash
# Clone and install dependencies
git clone https://github.com/i-dot-ai/medguard-evaluation.git
cd medguard-evaluation
uv sync

# Install playwright for figure generation
playwright install chromium

# Generate paper figures
uv run python scripts/generate_analyses.py
```

## License

MIT License - see [LICENSE](LICENSE) for details.
