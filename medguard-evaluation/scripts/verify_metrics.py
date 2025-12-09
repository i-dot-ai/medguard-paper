"""
Verify and compute all metrics for the paper.

This script ensures all metrics cited in the paper come from analysis code,
not manual calculations.
"""

import sys

sys.path.insert(0, ".")

from medguard.evaluation.evaluation import Evaluation
from medguard.utils.parsing import load_pydantic_from_json
from medguard.evaluation.performance_metrics.ground_truth.performance_metrics import (
    clinician_evaluations_to_performance_metrics,
)
import polars as pl
import pandas as pd

# Load evaluation
evaluation = load_pydantic_from_json(Evaluation, "outputs/20251018/test-set/evaluation.json")

print("=" * 80)
print("VERIFICATION OF ALL METRICS FOR PAPER")
print("=" * 80)
print()

# Total cases
print("SAMPLE SIZES")
print("-" * 80)
print(f"Total clinician evaluations: {len(evaluation.clinician_evaluations)}")
eval_no_errors = evaluation.exclude_data_errors()
print(f"After excluding data errors: {len(eval_no_errors.clinician_evaluations)}")
print()

# Ground Truth Binary Metrics
print("GROUND TRUTH BINARY METRICS (System vs Expert)")
print("-" * 80)
metrics = clinician_evaluations_to_performance_metrics(eval_no_errors.clinician_evaluations)
print(f"TP (System+, Expert+): {metrics.positive_any_issue}")
print(f"FP (System+, Expert-): {metrics.positive_no_issue}")
print(f"TN (System-, Expert-): {metrics.negative_no_issue}")
print(f"FN (System-, Expert+): {metrics.negative_any_issue}")
print(
    f"Total: {metrics.positive_any_issue + metrics.positive_no_issue + metrics.negative_no_issue + metrics.negative_any_issue}"
)
print(f"Expert found issues: {metrics.positive_any_issue + metrics.negative_any_issue}")
print(f"Expert found no issues: {metrics.positive_no_issue + metrics.negative_no_issue}")
print()

# PINCER vs Expert Contingency
print("PINCER vs EXPERT CONTINGENCY")
print("-" * 80)
contingency = pd.read_csv("outputs/eval_analyses/expert_pincer_contingency.csv")
pincer_pos_expert_yes = int(
    contingency[contingency["metric"] == "True Agreement (TP)"]["count"].iloc[0]
)
pincer_pos_expert_no = int(
    contingency[contingency["metric"] == "False Positive (FP)"]["count"].iloc[0]
)
pincer_neg_expert_yes = int(
    contingency[contingency["metric"] == "False Negative (FN)"]["count"].iloc[0]
)
pincer_neg_expert_no = int(
    contingency[contingency["metric"] == "True Agreement (TN)"]["count"].iloc[0]
)

print(f"PINCER+, Expert+: {pincer_pos_expert_yes}")
print(f"PINCER+, Expert-: {pincer_pos_expert_no}")
print(f"PINCER-, Expert+: {pincer_neg_expert_yes}")
print(f"PINCER-, Expert-: {pincer_neg_expert_no}")
print(
    f"Total: {pincer_pos_expert_yes + pincer_pos_expert_no + pincer_neg_expert_yes + pincer_neg_expert_no}"
)
print(f"Expert found issues: {pincer_pos_expert_yes + pincer_neg_expert_yes}")
print()

# DISCREPANCY CHECK
print("⚠️  DISCREPANCY DETECTED:")
print(
    f"   System vs Expert says: Expert found issues in {metrics.positive_any_issue + metrics.negative_any_issue} cases"
)
print(
    f"   PINCER vs Expert says: Expert found issues in {pincer_pos_expert_yes + pincer_neg_expert_yes} cases"
)
print(
    f"   Difference: {(metrics.positive_any_issue + metrics.negative_any_issue) - (pincer_pos_expert_yes + pincer_neg_expert_yes)} cases"
)
print()
print("This needs investigation - the two analyses may be using different patient subsets.")
