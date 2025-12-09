"""
Pairwise Agreement Analysis

Calculates the probability that additional runs agree with a given run's
intervention recommendation (True or False).
"""

import polars as pl
from collections import defaultdict

from medguard.analysis.base import EvaluationAnalysisBase


class PairwiseAgreementAnalysis(EvaluationAnalysisBase):
    """
    Calculate pairwise agreement for intervention recommendations across multiple runs.
    """

    def __init__(self, evaluation, name: str = "pairwise_agreement"):
        super().__init__(evaluation, name=name)

    def execute(self) -> pl.DataFrame:
        """
        Execute analysis and return DataFrame.

        Returns DataFrame with:
        - metric: Type of probability
        - probability: The calculated probability
        - n_runs: Number of runs this is based on
        - n_patients: Number of patients
        """
        # Collect all intervention_required values per patient
        intervention_by_patient = defaultdict(list)

        for patient_id in self.evaluation.patient_ids(restrict_to_ground_truth=True):
            for record in self.evaluation.analysed_records_dict[patient_id]:
                intervention_by_patient[patient_id].append(
                    record.medguard_analysis.intervention_required
                )

        # Calculate pairwise agreement probabilities
        # For each run that says "True", what proportion of OTHER runs also say "True"?
        total_true_runs = 0
        other_runs_also_true = 0

        total_false_runs = 0
        other_runs_also_false = 0

        for patient_id, interventions in intervention_by_patient.items():
            n_true = sum(interventions)
            n_false = len(interventions) - n_true
            total_runs = len(interventions)

            if total_runs < 2:
                continue  # Need at least 2 runs to compare

            # For each True run, count how many other runs are also True
            if n_true > 0:
                total_true_runs += n_true
                # Each True run sees (n_true - 1) other True runs out of (total_runs - 1) other runs
                other_runs_also_true += n_true * (n_true - 1) / (total_runs - 1)

            # For each False run, count how many other runs are also False
            if n_false > 0:
                total_false_runs += n_false
                # Each False run sees (n_false - 1) other False runs out of (total_runs - 1) other runs
                other_runs_also_false += n_false * (n_false - 1) / (total_runs - 1)

        p_other_true_given_true = (
            other_runs_also_true / total_true_runs if total_true_runs > 0 else 0
        )
        p_other_false_given_false = (
            other_runs_also_false / total_false_runs if total_false_runs > 0 else 0
        )

        df = pl.DataFrame(
            {
                "metric": [
                    "P(another run says True | one run says True)",
                    "P(another run says False | one run says False)",
                ],
                "probability": [p_other_true_given_true, p_other_false_given_false],
                "n_runs": [total_true_runs, total_false_runs],
                "n_patients": [len(intervention_by_patient), len(intervention_by_patient)],
            }
        )

        return df
