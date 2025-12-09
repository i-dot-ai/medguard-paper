"""
Secondary analysis modules for MedGuard.

These analyses are supplementary to the main paper figures and include:
- PINCER filter performance comparisons
- Self-consistency analysis
- Performance stratification (complexity, ethnicity)
- Expert-PINCER agreement analysis

To use these analyses, import from this submodule:
    from medguard.analysis.secondary import SelfConsistencyAnalysis

Note: These analyses reference specific evaluation outputs from the study
and cannot be rerun without access to the original data. Pre-computed
results are available in outputs/eval_analyses/.
"""

from medguard.analysis.secondary.evaluation_metrics_dump import EvaluationMetricsDumpAnalysis
from medguard.analysis.secondary.expert_pincer_comparison import (
    ExpertPincerComparisonAnalysis,
    ExpertPincerContingencyAnalysis,
)
from medguard.analysis.secondary.ground_truth_binary_metrics import GroundTruthBinaryMetricsAnalysis
from medguard.analysis.secondary.issue_precision_distribution import (
    IssuePrecisionDistributionAnalysis,
)
from medguard.analysis.secondary.pairwise_agreement import PairwiseAgreementAnalysis
from medguard.analysis.secondary.performance_by_complexity import PerformanceByComplexityAnalysis
from medguard.analysis.secondary.performance_by_complexity_boxplot import (
    PerformanceByComplexityBoxPlotAnalysis,
)
from medguard.analysis.secondary.performance_by_ethnicity import PerformanceByEthnicityAnalysis
from medguard.analysis.secondary.performance_by_filter_clinician import (
    PerformanceByFilterClinicianAnalysis,
)
from medguard.analysis.secondary.performance_summary import PerformanceSummaryAnalysis
from medguard.analysis.secondary.performance_summary_100 import PerformanceSummaryAnalysis100
from medguard.analysis.secondary.pincer_binary_metrics import PincerBinaryMetricsAnalysis
from medguard.analysis.secondary.population_level_metrics import PopulationLevelMetrics
from medguard.analysis.secondary.self_consistency import SelfConsistencyAnalysis
from medguard.analysis.secondary.self_consistency_combined import SelfConsistencyCombinedAnalysis

__all__ = [
    "EvaluationMetricsDumpAnalysis",
    "ExpertPincerComparisonAnalysis",
    "ExpertPincerContingencyAnalysis",
    "GroundTruthBinaryMetricsAnalysis",
    "IssuePrecisionDistributionAnalysis",
    "PairwiseAgreementAnalysis",
    "PerformanceByComplexityAnalysis",
    "PerformanceByComplexityBoxPlotAnalysis",
    "PerformanceByEthnicityAnalysis",
    "PerformanceByFilterClinicianAnalysis",
    "PerformanceSummaryAnalysis",
    "PerformanceSummaryAnalysis100",
    "PincerBinaryMetricsAnalysis",
    "PopulationLevelMetrics",
    "SelfConsistencyAnalysis",
    "SelfConsistencyCombinedAnalysis",
]
