"""
Expert Assessment vs PINCER Classification Analysis

Section 3.2.1: Comparison between expert assessments and PINCER classifications.
Calculates agreement rates and identification of additional issues.
"""

import polars as pl

from medguard.analysis.base import EvaluationAnalysisBase
from medguard.evaluation.clinician.models import Stage2Data
from medguard.analysis.filters import (
    by_filter,
    by_positive_ground_truth,
    by_negative_ground_truth,
    agrees_with_rules,
    disagrees_with_rules,
    clinician_found_missed_issues,
    clinician_found_any_issues,
    clinician_found_no_issues,
    no_data_error,
    PINCER_FILTER_IDS,
)


class ExpertPincerComparisonAnalysis(EvaluationAnalysisBase):
    """
    Calculate agreement metrics between expert assessments and PINCER classifications.

    Metrics calculated:
    1. Expert agreed with PINCER classification (agrees_with_rules == "yes")
    2. Expert disagreed with PINCER classification (agrees_with_rules == "no")
    3. Expert identified additional issues beyond PINCER
    """

    def __init__(self, evaluation, name: str = "expert_pincer_comparison"):
        super().__init__(evaluation, name=name)

    def _has_additional_issues(self, stage2: "Stage2Data") -> bool:
        """
        Determine if expert identified additional issues beyond the PINCER rule.

        Logic:
        1. If medguard_identified_rule_issues == "yes":
           - Additional issues = agreed with >1 issue OR found missed issues
        2. If medguard_identified_rule_issues != "yes":
           - Additional issues = agreed with any issue OR found missed issues
        """
        num_agreed_issues = sum(1 for x in stage2.issue_assessments if x)
        found_missed = stage2.missed_issues == "yes"

        if stage2.medguard_identified_rule_issues == "yes":
            # MedGuard identified the PINCER rule, so "additional" means >1 issue or missed
            return num_agreed_issues > 1 or found_missed
        else:
            # MedGuard did NOT identify the PINCER rule, so ANY issue is "additional"
            return num_agreed_issues > 0 or found_missed

    def execute(self) -> pl.DataFrame:
        """
        Execute analysis and return DataFrame.

        Returns DataFrame with columns:
        - filter_id: PINCER filter ID (or "Overall" for aggregate)
        - n_patients: Total number of patients with valid clinician evaluations
        - n_expert_agreed: Count where agrees_with_rules == "yes"
        - n_expert_disagreed: Count where agrees_with_rules == "no"
        - n_additional_issues: Count where expert found additional issues
        - pct_expert_agreed: Percentage who agreed
        - pct_expert_disagreed: Percentage who disagreed
        - pct_additional_issues: Percentage with additional issues
        """
        rows = []

        # First, calculate overall metrics (across all filters with positive ground truth)
        ids_positive_gt = self.evaluation.filter_by_analysed_record(by_positive_ground_truth())
        ids_no_error = self.evaluation.filter_by_clinician_evaluation(no_data_error())
        overall_ids = list(set.intersection(ids_positive_gt, ids_no_error))

        if len(overall_ids) > 0:
            overall_eval = self.evaluation.filter_by_patient_ids(overall_ids)
            clinician_evals = overall_eval.clinician_evaluations

            n_expert_agreed = sum(1 for e in clinician_evals if e.agrees_with_rules == "yes")
            n_expert_disagreed = sum(1 for e in clinician_evals if e.agrees_with_rules == "no")
            n_additional_issues = sum(
                1
                for e in clinician_evals
                if self._has_additional_issues(e) and e.agrees_with_rules == "no"
            )

            n_total = len(overall_ids)

            rows.append(
                {
                    "filter_id": "Overall",
                    "n_patients": n_total,
                    "n_expert_agreed": n_expert_agreed,
                    "n_expert_disagreed": n_expert_disagreed,
                    "n_additional_issues": n_additional_issues,
                    "pct_expert_agreed": (n_expert_agreed / n_total * 100) if n_total > 0 else None,
                    "pct_expert_disagreed": (
                        (n_expert_disagreed / n_total * 100) if n_total > 0 else None
                    ),
                    "pct_additional_issues": (
                        (n_additional_issues / n_total * 100) if n_total > 0 else None
                    ),
                }
            )

        # Then, calculate metrics stratified by filter
        for filter_id in PINCER_FILTER_IDS:
            # Get patients matching this filter
            ids_by_filter = self.evaluation.filter_by_analysed_record(by_filter(filter_id))

            # Filter to clinician evaluations with valid data
            ids_by_clinician = self.evaluation.filter_by_clinician_evaluation(no_data_error())
            ids = list(set.intersection(ids_by_filter, ids_by_clinician))

            if len(ids) == 0:
                continue

            # Create filtered evaluation
            filtered_eval = self.evaluation.filter_by_patient_ids(ids)

            # Calculate counts from clinician evaluations
            clinician_evals = filtered_eval.clinician_evaluations

            n_expert_agreed = sum(1 for e in clinician_evals if e.agrees_with_rules == "yes")

            n_expert_disagreed = sum(1 for e in clinician_evals if e.agrees_with_rules == "no")

            n_additional_issues = sum(
                1
                for e in clinician_evals
                if self._has_additional_issues(e) and e.agrees_with_rules == "no"
            )

            n_total = len(ids)

            rows.append(
                {
                    "filter_id": filter_id,
                    "n_patients": n_total,
                    "n_expert_agreed": n_expert_agreed,
                    "n_expert_disagreed": n_expert_disagreed,
                    "n_additional_issues": n_additional_issues,
                    "pct_expert_agreed": (n_expert_agreed / n_total * 100) if n_total > 0 else None,
                    "pct_expert_disagreed": (
                        (n_expert_disagreed / n_total * 100) if n_total > 0 else None
                    ),
                    "pct_additional_issues": (
                        (n_additional_issues / n_total * 100) if n_total > 0 else None
                    ),
                }
            )

        df = pl.DataFrame(rows)
        return df


class ExpertPincerContingencyAnalysis(EvaluationAnalysisBase):
    """
    2x2 Contingency table comparing PINCER classification vs Expert assessment.

    Shows agreement/disagreement between PINCER rules and expert clinical judgment.
    """

    def __init__(self, evaluation, name: str = "expert_pincer_contingency"):
        super().__init__(evaluation, name=name)

    def execute(self) -> pl.DataFrame:
        """
        Execute analysis and return 2x2 contingency table.

        Returns DataFrame with:
        - True Agreement (TP): PINCER positive, Expert agrees issue present
        - False Positive (FP): PINCER positive, Expert says no issue
        - False Negative (FN): PINCER negative, Expert found issues anyway
        - True Agreement (TN): PINCER negative, Expert agrees no issue
        """
        # Get all valid clinician evaluations
        ids_no_error = self.evaluation.filter_by_clinician_evaluation(no_data_error())

        # True Positives: PINCER positive, expert found any issue
        ids_positive = self.evaluation.filter_by_analysed_record(by_positive_ground_truth())
        ids_expert_positive = self.evaluation.filter_by_clinician_evaluation(lambda x: x.issue)
        tp_ids = list(set.intersection(ids_positive, ids_expert_positive, ids_no_error))
        tp = len(tp_ids)

        # False Positives: PINCER positive, expert not found any issue
        ids_expert_negative = self.evaluation.filter_by_clinician_evaluation(lambda x: not x.issue)
        fp_ids = fp_ids = list(set.intersection(ids_positive, ids_expert_negative, ids_no_error))
        fp = len(fp_ids)

        # False Negative: PINCER negative, expert found any issue
        ids_negative = self.evaluation.filter_by_analysed_record(by_negative_ground_truth())
        fn_ids = list(set.intersection(ids_negative, ids_expert_positive, ids_no_error))
        fn = len(fn_ids)

        # True Negative: PINCER negative, expert found no issue
        tn_ids = list(set.intersection(ids_negative, ids_expert_negative, ids_no_error))
        tn = len(tn_ids)

        # Calculate totals and metrics
        total = tp + fp + fn + tn
        pincer_positive = tp + fp
        pincer_negative = fn + tn
        expert_issue = tp + fn
        expert_no_issue = fp + tn

        # Calculate agreement metrics
        accuracy = (tp + tn) / total * 100 if total > 0 else None
        sensitivity = tp / (tp + fn) * 100 if (tp + fn) > 0 else None
        specificity = tn / (tn + fp) * 100 if (tn + fp) > 0 else None
        ppv = tp / (tp + fp) * 100 if (tp + fp) > 0 else None
        npv = tn / (tn + fn) * 100 if (tn + fn) > 0 else None

        df = pl.DataFrame(
            [
                {
                    "metric": "True Agreement (TP)",
                    "description": "PINCER positive, Expert agrees",
                    "count": tp,
                    "percentage": (tp / total * 100) if total > 0 else None,
                },
                {
                    "metric": "False Positive (FP)",
                    "description": "PINCER positive, Expert disagrees",
                    "count": fp,
                    "percentage": (fp / total * 100) if total > 0 else None,
                },
                {
                    "metric": "False Negative (FN)",
                    "description": "PINCER negative, Expert found issues",
                    "count": fn,
                    "percentage": (fn / total * 100) if total > 0 else None,
                },
                {
                    "metric": "True Agreement (TN)",
                    "description": "PINCER negative, Expert agrees",
                    "count": tn,
                    "percentage": (tn / total * 100) if total > 0 else None,
                },
                {
                    "metric": "PINCER Positive Total",
                    "description": "Total cases where PINCER flagged issue",
                    "count": pincer_positive,
                    "percentage": (pincer_positive / total * 100) if total > 0 else None,
                },
                {
                    "metric": "PINCER Negative Total",
                    "description": "Total cases where PINCER no issue",
                    "count": pincer_negative,
                    "percentage": (pincer_negative / total * 100) if total > 0 else None,
                },
                {
                    "metric": "Expert Issue Total",
                    "description": "Total cases where expert found issue",
                    "count": expert_issue,
                    "percentage": (expert_issue / total * 100) if total > 0 else None,
                },
                {
                    "metric": "Expert No Issue Total",
                    "description": "Total cases where expert found no issue",
                    "count": expert_no_issue,
                    "percentage": (expert_no_issue / total * 100) if total > 0 else None,
                },
                {
                    "metric": "Total",
                    "description": "Total valid cases",
                    "count": total,
                    "percentage": 100.0,
                },
                {
                    "metric": "Accuracy",
                    "description": "Overall agreement rate",
                    "count": None,
                    "percentage": accuracy,
                },
                {
                    "metric": "Sensitivity (Recall)",
                    "description": "TP / (TP + FN)",
                    "count": None,
                    "percentage": sensitivity,
                },
                {
                    "metric": "Specificity",
                    "description": "TN / (TN + FP)",
                    "count": None,
                    "percentage": specificity,
                },
                {
                    "metric": "PPV (Precision)",
                    "description": "TP / (TP + FP)",
                    "count": None,
                    "percentage": ppv,
                },
                {
                    "metric": "NPV",
                    "description": "TN / (TN + FN)",
                    "count": None,
                    "percentage": npv,
                },
            ]
        )

        return df
