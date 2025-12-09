"""
Population-level performance metrics from stratified random sample.

This analysis calculates population-level sensitivity, specificity, PPV, NPV, and accuracy
by reweighting the stratified sample (50 System-flagged + 50 System-not-flagged) using
the known population flagging rate (46%).
"""

import polars as pl

from medguard.analysis.base import EvaluationAnalysisBase


class PopulationLevelMetrics(EvaluationAnalysisBase):
    """Calculate population-level performance metrics from stratified sample."""

    def __init__(self, evaluation, flagged_rate: float = 0.46, name: str = "population_metrics"):
        """
        Initialize population-level metrics analysis.

        Args:
            evaluation: Evaluation object (should be the no-filters random sample)
            flagged_rate: Fraction of patients System flagged in broader population
            name: Analysis name for saving outputs
        """
        super().__init__(evaluation, name=name)
        self.flagged_rate = flagged_rate
        self.not_flagged_rate = 1 - flagged_rate

    def execute(self) -> pl.DataFrame:
        """Calculate population-level metrics from stratified sample."""
        # Build confusion matrix from sample
        tp = 0
        tn = 0
        fp = 0
        fn = 0

        for patient_id in self.evaluation.patient_ids():
            clinician_analysis = self.evaluation.clinician_evaluations_dict[patient_id]
            medguard_analysis = self.evaluation.analysed_records_dict_first[
                patient_id
            ].medguard_analysis

            clinician_issue = clinician_analysis.issue
            medguard_issue = medguard_analysis.issue

            if clinician_issue and medguard_issue:
                tp += 1
            elif clinician_issue and not medguard_issue:
                fn += 1
            elif not clinician_issue and medguard_issue:
                fp += 1
            elif not clinician_issue and not medguard_issue:
                tn += 1

        # Sample-level counts
        n_flagged = tp + fp
        n_not_flagged = tn + fn
        n_total = n_flagged + n_not_flagged

        # Performance rates within each stratum
        rate_tp_given_flagged = tp / n_flagged if n_flagged > 0 else 0
        rate_fp_given_flagged = fp / n_flagged if n_flagged > 0 else 0
        rate_tn_given_not_flagged = tn / n_not_flagged if n_not_flagged > 0 else 0
        rate_fn_given_not_flagged = fn / n_not_flagged if n_not_flagged > 0 else 0

        # Population-weighted proportions
        tp_pop = self.flagged_rate * rate_tp_given_flagged
        fp_pop = self.flagged_rate * rate_fp_given_flagged
        tn_pop = self.not_flagged_rate * rate_tn_given_not_flagged
        fn_pop = self.not_flagged_rate * rate_fn_given_not_flagged

        # Population-level metrics
        actual_positives = tp_pop + fn_pop
        actual_negatives = tn_pop + fp_pop
        predicted_positives = tp_pop + fp_pop
        predicted_negatives = tn_pop + fn_pop

        # Calculate metrics
        accuracy = (tp_pop + tn_pop) / (actual_positives + actual_negatives)
        sensitivity = tp_pop / actual_positives if actual_positives > 0 else 0
        specificity = tn_pop / actual_negatives if actual_negatives > 0 else 0
        ppv = tp_pop / predicted_positives if predicted_positives > 0 else 0
        npv = tn_pop / predicted_negatives if predicted_negatives > 0 else 0
        precision = ppv  # Same as PPV
        recall = sensitivity  # Same as sensitivity
        f1_score = (
            2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        )

        # False positive and negative rates
        fpr = fp_pop / actual_negatives if actual_negatives > 0 else 0
        fnr = fn_pop / actual_positives if actual_positives > 0 else 0

        # Cohen's Kappa
        expected_agreement = (
            predicted_positives * actual_positives + predicted_negatives * actual_negatives
        )
        kappa = (
            (accuracy - expected_agreement) / (1 - expected_agreement)
            if expected_agreement < 1
            else 0
        )

        # Create output DataFrame (all values as floats for consistency)
        data = {
            "metric": [
                "Sample Size (after cleaning)",
                "Sample: System Flagged",
                "Sample: System Not Flagged",
                "Sample: TP",
                "Sample: FP",
                "Sample: TN",
                "Sample: FN",
                "Population: System Flagging Rate",
                "Population: Prevalence (expert)",
                "Population: TP (proportion)",
                "Population: FP (proportion)",
                "Population: TN (proportion)",
                "Population: FN (proportion)",
                "Accuracy",
                "Sensitivity (Recall)",
                "Specificity",
                "PPV (Precision)",
                "NPV",
                "F1 Score",
                "False Positive Rate",
                "False Negative Rate",
                "Cohen's Kappa",
            ],
            "value": [
                float(n_total),
                float(n_flagged),
                float(n_not_flagged),
                float(tp),
                float(fp),
                float(tn),
                float(fn),
                self.flagged_rate,
                actual_positives,
                tp_pop,
                fp_pop,
                tn_pop,
                fn_pop,
                accuracy,
                sensitivity,
                specificity,
                ppv,
                npv,
                f1_score,
                fpr,
                fnr,
                kappa,
            ],
            "description": [
                "Total patients in cleaned evaluation",
                "Patients System flagged in sample",
                "Patients System did not flag in sample",
                "True Positives in sample",
                "False Positives in sample",
                "True Negatives in sample",
                "False Negatives in sample",
                "Fraction of population System flags",
                "Fraction of population with issues",
                "Fraction of population that are TP",
                "Fraction of population that are FP",
                "Fraction of population that are TN",
                "Fraction of population that are FN",
                "Overall accuracy (TP+TN)/(TP+FP+TN+FN)",
                "TP / (TP+FN) - catches X% of all issues",
                "TN / (TN+FP) - correctly ignores X% of non-issues",
                "TP / (TP+FP) - X% of flags are correct",
                "TN / (TN+FN) - X% of non-flags are correct",
                "Harmonic mean of precision and recall",
                "FP / (FP+TN) - incorrectly flags X% of non-issues",
                "FN / (FN+TP) - misses X% of issues",
                "Agreement beyond chance",
            ],
        }

        return pl.DataFrame(data)
