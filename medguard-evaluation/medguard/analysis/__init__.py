"""
Evaluation analysis modules for MedGuard.

Primary analyses for the paper figures:
- Figure1CompositeAnalysis: Main paper figure with hierarchical evaluation and failure modes
- ComplexityCorrelationAnalysis: Patient complexity correlation analysis
- ModelComparisonAnalysis: Multi-model performance comparison
- FailureModeAnalysis: Failure mode categorization

Secondary analyses are available in medguard.analysis.secondary submodule.
"""

from medguard.analysis import utils
from medguard.analysis.base import EvaluationAnalysisBase, TextAnalysisBase
from medguard.analysis.complexity_correlation import ComplexityCorrelationAnalysis
from medguard.analysis.failure_mode_analysis import FailureModeAnalysis
from medguard.analysis.figure_1_composite import Figure1CompositeAnalysis
from medguard.analysis.model_comparison import ModelComparisonAnalysis

__all__ = [
    "EvaluationAnalysisBase",
    "TextAnalysisBase",
    "Figure1CompositeAnalysis",
    "ComplexityCorrelationAnalysis",
    "ModelComparisonAnalysis",
    "FailureModeAnalysis",
    "utils",
]
