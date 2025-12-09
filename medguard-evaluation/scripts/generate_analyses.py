"""
Generate all paper figures for the MedGuard evaluation.

This script generates the following figures:
- Figure 1a: Primary workflow diagram (from workflow_flowchart_primary.html)
- Figure 1b: Hierarchical evaluation stages (from Figure1CompositeAnalysis panel_a)
- Figure 1c: Failure mode categories (from Figure1CompositeAnalysis panel_c)
- Figure 1d: Complexity correlation matrix (from ComplexityCorrelationAnalysis)
- Figure 1e: Model comparison (from ModelComparisonAnalysis)
- Figure 2: Failure analysis vignettes (from figure_2.html)

Usage:
    uv run python scripts/generate_analyses.py

Secondary analyses are available in medguard/analysis/secondary/ but are not run by default.

NOTE: This script requires evaluation data that was generated within an NHS Trusted
Research Environment and cannot be shared. The paths below reference internal evaluation
outputs. External users can view the pre-computed results in outputs/eval_analyses/
but cannot regenerate them.
"""

import shutil
from pathlib import Path

from medguard.analysis import (
    ComplexityCorrelationAnalysis,
    Figure1CompositeAnalysis,
    ModelComparisonAnalysis,
)
from medguard.evaluation.evaluation import Evaluation, merge_evaluations
from medguard.utils.parsing import load_pydantic_from_json

# Paths
ANALYSIS_DIR = Path(__file__).parent.parent / "medguard" / "analysis"
PLOTS_DIR = Path(__file__).parent.parent / "outputs" / "eval_analyses" / "plots"


def html_to_pdf(html_path: Path, pdf_path: Path) -> bool:
    """
    Convert HTML file to PDF using playwright.

    Returns True if successful, False otherwise.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "  ⚠ playwright not installed. Install with: uv add playwright && playwright install chromium"
        )
        return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_path.absolute()}")
            page.pdf(path=str(pdf_path), format="A4", print_background=True)
            browser.close()
        return True
    except Exception as e:
        print(f"  ⚠ Failed to convert {html_path.name}: {e}")
        return False


def main():
    print("=" * 70)
    print("MEDGUARD PAPER FIGURE GENERATION")
    print("=" * 70)

    # Ensure output directory exists
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # LOAD EVALUATIONS
    # ========================================================================
    print("\n1. Loading evaluations...")

    # Primary evaluation: 300-patient cohort (200 + 100 merged)
    evaluation_200 = load_pydantic_from_json(
        Evaluation, "outputs/20251018/test-set/evaluation.json"
    )
    evaluation_100 = load_pydantic_from_json(
        Evaluation, "outputs/20251027/no-filters/evaluation.json"
    )
    print(f"   - Loaded {len(evaluation_200.patient_ids())} from test-set")
    print(f"   - Loaded {len(evaluation_100.patient_ids())} from no-filters")

    primary_evaluation = merge_evaluations([evaluation_100, evaluation_200])
    primary_evaluation = primary_evaluation.clean()
    print(f"   - Merged and cleaned: {len(primary_evaluation.patient_ids())} evaluable patients")

    # Model comparison evaluations
    print("\n2. Loading model comparison evaluations...")
    model_evaluations: list[tuple[str, Evaluation]] = [
        (
            "gpt-oss-120b-low",
            load_pydantic_from_json(
                Evaluation, "outputs/20251104/gpt-oss-120b-low/evaluation.json"
            ).clean(),
        ),
        (
            "gpt-oss-120b-medium",
            load_pydantic_from_json(
                Evaluation, "outputs/20251104/gpt-oss-120b-medium/evaluation.json"
            ).clean(),
        ),
        (
            "gpt-oss-120b-high",
            load_pydantic_from_json(
                Evaluation, "outputs/20251104/gpt-oss-120b-high/evaluation.json"
            ).clean(),
        ),
        (
            "gpt-oss-20b-medium",
            load_pydantic_from_json(
                Evaluation, "outputs/20251104/gpt-oss-20b-medium/evaluation.json"
            ).clean(),
        ),
        (
            "gemma",
            load_pydantic_from_json(Evaluation, "outputs/20251104/gemma/evaluation.json").clean(),
        ),
        (
            "medgemma",
            load_pydantic_from_json(
                Evaluation, "outputs/20251104/medgemma/evaluation.json"
            ).clean(),
        ),
    ]
    print(f"   - Loaded {len(model_evaluations)} models")

    # ========================================================================
    # FIGURE 1a: Primary Workflow (HTML to PDF)
    # ========================================================================
    print("\n" + "-" * 70)
    print("Figure 1a: Primary Workflow")
    print("-" * 70)

    workflow_html = ANALYSIS_DIR / "workflow_flowchart_primary.html"
    figure_1a_pdf = PLOTS_DIR / "figure_1a.pdf"

    if workflow_html.exists():
        print(f"  Source: {workflow_html.name}")
        if html_to_pdf(workflow_html, figure_1a_pdf):
            print(f"  ✓ Saved: {figure_1a_pdf}")
        else:
            print(f"  ✗ Failed to generate figure_1a.pdf")
    else:
        print(f"  ✗ Source not found: {workflow_html}")

    # ========================================================================
    # FIGURE 1b & 1c: Hierarchical Evaluation and Failure Modes
    # ========================================================================
    print("\n" + "-" * 70)
    print("Figure 1b & 1c: Hierarchical Evaluation and Failure Modes")
    print("-" * 70)

    figure1_analysis = Figure1CompositeAnalysis(primary_evaluation)
    print("  Running Figure1CompositeAnalysis...")
    figure1_analysis.run()
    figure1_analysis.run_figure()

    # Copy panel outputs to figure_1b and figure_1c
    panel_a = PLOTS_DIR / "figure_1_composite_panel_a.pdf"
    panel_c = PLOTS_DIR / "figure_1_composite_panel_c.pdf"
    figure_1b_pdf = PLOTS_DIR / "figure_1b.pdf"
    figure_1c_pdf = PLOTS_DIR / "figure_1c.pdf"

    # Generate PDFs
    figure1_analysis.run_figure_pdf()

    if panel_a.exists():
        shutil.copy(panel_a, figure_1b_pdf)
        print(f"  ✓ Saved: {figure_1b_pdf}")
    else:
        print(f"  ✗ Panel A not found: {panel_a}")

    if panel_c.exists():
        shutil.copy(panel_c, figure_1c_pdf)
        print(f"  ✓ Saved: {figure_1c_pdf}")
    else:
        print(f"  ✗ Panel C not found: {panel_c}")

    # ========================================================================
    # FIGURE 1d: Complexity Correlation Matrix
    # ========================================================================
    print("\n" + "-" * 70)
    print("Figure 1d: Complexity Correlation Matrix")
    print("-" * 70)

    complexity_analysis = ComplexityCorrelationAnalysis(primary_evaluation)
    print("  Running ComplexityCorrelationAnalysis...")
    complexity_analysis.run()
    complexity_analysis.run_figure()
    complexity_analysis.run_figure_pdf()

    corr_matrix = PLOTS_DIR / "complexity_correlation_correlation_matrix.pdf"
    figure_1d_pdf = PLOTS_DIR / "figure_1d.pdf"

    if corr_matrix.exists():
        shutil.copy(corr_matrix, figure_1d_pdf)
        print(f"  ✓ Saved: {figure_1d_pdf}")
    else:
        print(f"  ✗ Correlation matrix not found: {corr_matrix}")

    # ========================================================================
    # FIGURE 1e: Model Comparison
    # ========================================================================
    print("\n" + "-" * 70)
    print("Figure 1e: Model Comparison")
    print("-" * 70)

    model_comparison = ModelComparisonAnalysis(model_evaluations)
    print("  Running ModelComparisonAnalysis...")
    model_comparison.run()
    model_comparison.run_figure()
    model_comparison.run_figure_pdf()

    model_comp = PLOTS_DIR / "model_comparison_comparison.pdf"
    figure_1e_pdf = PLOTS_DIR / "figure_1e.pdf"

    if model_comp.exists():
        shutil.copy(model_comp, figure_1e_pdf)
        print(f"  ✓ Saved: {figure_1e_pdf}")
    else:
        print(f"  ✗ Model comparison not found: {model_comp}")

    # ========================================================================
    # FIGURE 2: Failure Analysis Vignettes (HTML to PDF)
    # ========================================================================
    print("\n" + "-" * 70)
    print("Figure 2: Failure Analysis Vignettes")
    print("-" * 70)

    figure2_html = ANALYSIS_DIR / "figure_2.html"
    figure_2_pdf = PLOTS_DIR / "figure_2.pdf"

    if figure2_html.exists():
        print(f"  Source: {figure2_html.name}")
        if html_to_pdf(figure2_html, figure_2_pdf):
            print(f"  ✓ Saved: {figure_2_pdf}")
        else:
            print(f"  ✗ Failed to generate figure_2.pdf")
    else:
        print(f"  ✗ Source not found: {figure2_html}")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    figures = [
        ("Figure 1a", figure_1a_pdf, "Primary workflow diagram"),
        ("Figure 1b", figure_1b_pdf, "Hierarchical evaluation stages"),
        ("Figure 1c", figure_1c_pdf, "Failure mode categories"),
        ("Figure 1d", figure_1d_pdf, "Complexity correlation matrix"),
        ("Figure 1e", figure_1e_pdf, "Model comparison"),
        ("Figure 2", figure_2_pdf, "Failure analysis vignettes"),
    ]

    for name, path, desc in figures:
        status = "✓" if path.exists() else "✗"
        print(f"  {status} {name}: {desc}")

    print("\n" + "=" * 70)
    print("Done! All paper figures generated in outputs/eval_analyses/plots/")
    print("=" * 70)


if __name__ == "__main__":
    main()
