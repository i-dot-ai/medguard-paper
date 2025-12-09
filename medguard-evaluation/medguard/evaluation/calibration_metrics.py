import numpy as np
import plotly.graph_objects as go
from pydantic import BaseModel


class CalibrationBin(BaseModel):
    bin_start: float
    bin_end: float
    predicted_prob: float
    actual_proportion: float
    count: int


class CalibrationMetrics(BaseModel):
    bins: list[CalibrationBin]
    brier_score: float
    ece: float  # Expected Calibration Error

    def generate_calibration_plot(self) -> go.Figure:
        return generate_calibration_plot(self)


def calculate_calibration_metrics(
    predictions: list[float], ground_truth: list[bool], n_bins: int = 10
) -> CalibrationMetrics:
    """Calculate calibration metrics from predicted probabilities and ground truth labels.

    Args:
        predictions: List of predicted probabilities (0-1) for intervention required
        ground_truth: List of boolean ground truth labels (True = intervention required)
        n_bins: Number of bins for calibration curve (default 10)

    Returns:
        CalibrationMetrics containing bins, brier score, and ECE
    """
    predictions_array = np.array(predictions)
    ground_truth_array = np.array(ground_truth, dtype=float)

    # Calculate Brier score
    brier_score = float(np.mean((predictions_array - ground_truth_array) ** 2))

    # Create bins
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bins = []
    ece = 0.0
    total_samples = len(predictions)

    for i in range(n_bins):
        bin_start = bin_edges[i]
        bin_end = bin_edges[i + 1]

        # Find predictions in this bin
        if i == n_bins - 1:  # Last bin includes upper edge
            in_bin = (predictions_array >= bin_start) & (predictions_array <= bin_end)
        else:
            in_bin = (predictions_array >= bin_start) & (predictions_array < bin_end)

        count = int(np.sum(in_bin))

        if count > 0:
            predicted_prob = float(np.mean(predictions_array[in_bin]))
            actual_proportion = float(np.mean(ground_truth_array[in_bin]))

            # Contribution to ECE
            ece += (count / total_samples) * abs(predicted_prob - actual_proportion)

            bins.append(
                CalibrationBin(
                    bin_start=bin_start,
                    bin_end=bin_end,
                    predicted_prob=predicted_prob,
                    actual_proportion=actual_proportion,
                    count=count,
                )
            )

    return CalibrationMetrics(bins=bins, brier_score=brier_score, ece=ece)


def generate_calibration_plot(calibration_metrics: CalibrationMetrics) -> go.Figure:
    """Generate a calibration plot with perfect calibration line and actual calibration curve.

    Args:
        calibration_metrics: CalibrationMetrics object containing binned data

    Returns:
        Plotly Figure object
    """
    # Extract data from bins
    predicted_probs = [bin.predicted_prob for bin in calibration_metrics.bins]
    actual_proportions = [bin.actual_proportion for bin in calibration_metrics.bins]
    counts = [bin.count for bin in calibration_metrics.bins]
    bin_centers = [(bin.bin_start + bin.bin_end) / 2 for bin in calibration_metrics.bins]

    # Create figure with secondary y-axis for histogram
    fig = go.Figure()

    # Perfect calibration line (diagonal)
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="Perfect Calibration",
            line=dict(color="gray", dash="dash", width=2),
        )
    )

    # Actual calibration curve
    fig.add_trace(
        go.Scatter(
            x=predicted_probs,
            y=actual_proportions,
            mode="lines+markers",
            name="Model Calibration",
            line=dict(color="#2E86AB", width=3),
            marker=dict(size=8, color="#2E86AB"),
            hovertemplate="Predicted: %{x:.2f}<br>Actual: %{y:.2f}<extra></extra>",
        )
    )

    # Add histogram as bar chart at the bottom
    fig.add_trace(
        go.Bar(
            x=bin_centers,
            y=counts,
            name="Sample Count",
            marker=dict(color="#A23B72", opacity=0.6),
            width=0.08,
            yaxis="y2",
            hovertemplate="Bin: %{x:.2f}<br>Count: %{y}<extra></extra>",
        )
    )

    # Update layout
    fig.update_layout(
        title=dict(
            text=f"Calibration Plot<br><sub>Brier Score: {calibration_metrics.brier_score:.3f} | ECE: {calibration_metrics.ece:.3f}</sub>",
            x=0.5,
            xanchor="center",
        ),
        xaxis=dict(title="Predicted Probability", range=[0, 1], gridcolor="lightgray"),
        yaxis=dict(title="Actual Proportion", range=[0, 1], gridcolor="lightgray"),
        yaxis2=dict(title="Sample Count", overlaying="y", side="right", showgrid=False),
        hovermode="closest",
        plot_bgcolor="white",
        width=800,
        height=600,
        legend=dict(
            x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.8)", bordercolor="lightgray", borderwidth=1
        ),
    )

    return fig
