import pandas as pd

from pydantic import BaseModel


class EvaluationMetrics(BaseModel):
    kappa: float
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    true_positive_rate: float
    true_negative_rate: float
    false_positive_rate: float
    false_negative_rate: float
    total_samples: int
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    actual_positives: int
    actual_negatives: int
    predicted_positives: int
    predicted_negatives: int


def add_metric_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["true_positive"] = (df["prediction"] == "Yes") & (df["score"] == True)
    df["true_negative"] = (df["prediction"] == "No") & (df["score"] == True)
    df["false_positive"] = (df["prediction"] == "Yes") & (df["score"] == False)
    df["false_negative"] = (df["prediction"] == "No") & (df["score"] == False)
    return df


def calculate_evaluation_metrics(
    TP: int, TN: int, FP: int, FN: int, expected_agreement: float = 0.5
) -> EvaluationMetrics:
    """Core function to calculate evaluation metrics from a dataframe of samples. Uses the score column to determine if a sample if correct or incorrect.
    The target column (Yes/No) is used to determine the true labels.

    1. Cohen's Kappa ((observed agreement - expected agreement) / (1 - expected agreement))
    2. Accuracy, Raw Agreement - (n_correct / n_total)
    3. Sensitivity, True Positive Rate - (TP / Actual Positives)
    4. Specificity, True Negative Rate - (TN / Actual Negatives)
    5. False Positive Rate - (FP / Actual Negatives)
    6. False Negative Rate - (FN / Actual Positives)
    """

    actual_positives = TP + FN
    actual_negatives = TN + FP

    # Calculate Accuracy, Raw Agreement
    accuracy = (TP + TN) / (actual_positives + actual_negatives)

    # Calculate Recall
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0

    # Calculate Precision
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0

    # Calculate F1 Score
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # Calculate Sensitivity, True Positive Rate
    true_positive_rate = TP / actual_positives if actual_positives > 0 else 0

    # Calculate Specificity, True Negative Rate
    true_negative_rate = TN / actual_negatives if actual_negatives > 0 else 0

    # Calculate False Positive Rate
    false_positive_rate = FP / actual_negatives if actual_negatives > 0 else 0

    # Calculate False Negative Rate
    false_negative_rate = FN / actual_positives if actual_positives > 0 else 0

    # Cohen's Kappa
    kappa = (accuracy - expected_agreement) / (1 - expected_agreement)

    return EvaluationMetrics(
        kappa=kappa,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        true_positive_rate=true_positive_rate,
        true_negative_rate=true_negative_rate,
        false_positive_rate=false_positive_rate,
        false_negative_rate=false_negative_rate,
        total_samples=TP + TN + FP + FN,
        true_positives=TP,
        true_negatives=TN,
        false_positives=FP,
        false_negatives=FN,
        actual_positives=actual_positives,
        actual_negatives=actual_negatives,
        predicted_positives=TP + FP,
        predicted_negatives=TN + FN,
    )
