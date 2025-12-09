from typing import TYPE_CHECKING

import plotly.graph_objects as go

if TYPE_CHECKING:
    from .performance_metrics import FilterPerformanceMetrics


def generate_full_sankey_figure(performance_metrics: "FilterPerformanceMetrics") -> go.Figure:
    # Define the flow data
    links = [
        # Positive Ground Truth
        (0, 1, performance_metrics.positive_gt_any_issue),
        (0, 2, performance_metrics.positive_gt_no_issue),
        (1, 3, performance_metrics.positive_gt_correct_issue),
        (1, 4, performance_metrics.positive_gt_incorrect_issue),
        (3, 5, performance_metrics.positive_gt_correct_intervention),
        (3, 6, performance_metrics.positive_gt_incorrect_intervention),
        # Negative Ground Truth
        (7, 8, performance_metrics.negative_gt_any_issue),
        (7, 9, performance_metrics.negative_gt_no_issue),
        (9, 12, performance_metrics.negative_gt_no_issue),
        # True Positives
        (5, 10, performance_metrics.positive_gt_correct_intervention),
        # False Negatives
        (2, 13, performance_metrics.positive_gt_no_issue),
        # False Positives
        (4, 11, performance_metrics.positive_gt_incorrect_issue),
        (6, 11, performance_metrics.positive_gt_incorrect_intervention),
        (8, 11, performance_metrics.negative_gt_any_issue),
    ]

    links = [(source, target, value) for source, target, value in links if value > 0]

    # Calculate total input for percentages
    total_input = sum(link[2] for link in links if link[0] in [0, 7])

    # Calculate flow through each node - only count INCOMING flows to avoid double-counting
    node_values = {}
    for source, target, value in links:
        node_values[target] = node_values.get(target, 0) + value

    # For source-only nodes (no incoming flows), sum ALL their outgoing flows
    source_only_nodes = set()
    for source, target, value in links:
        if source not in node_values:
            source_only_nodes.add(source)

    for node in source_only_nodes:
        node_values[node] = sum(value for source, target, value in links if source == node)

    # Original labels
    labels = [
        "Positive Ground Truth",  # 0
        "Any Issue Identified",  # 1
        "No Issue Identified",  # 2
        "Correct Issue Identified",  # 3
        "Incorrect Issue Identified",  # 4
        "Correct Intervention Suggested",  # 5
        "Incorrect Intervention Suggested",  # 6
        "Negative Ground Truth",  # 7
        "Any Issue Identified",  # 8
        "No Issue Identified",  # 9
        "True Positive",  # 10
        "False Positive",  # 11
        "True Negative",  # 12
        "False Negative",  # 13
    ]

    # Add values and percentages to labels
    labels_with_values = [
        f"{label}<br>{node_values.get(i, 0)} ({node_values.get(i, 0) / total_input * 100:.1f}%)"
        for i, label in enumerate(labels)
    ]

    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",  # This helps with node positioning
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=labels_with_values,
                    color=[
                        "#2ECC71",  # 0 - Positive GT: Green (condition present)
                        "#F39C12",  # 1 - Any Issue Identified: Amber
                        "#E74C3C",  # 2 - No Issue Identified (from positive): Red flag
                        "#27AE60",  # 3 - Correct Issue: Dark green
                        "#E67E22",  # 4 - Incorrect Issue: Orange
                        "#229954",  # 5 - Correct Intervention: Darker green
                        "#D35400",  # 6 - Incorrect Intervention: Dark orange
                        "#3498DB",  # 7 - Negative GT: Blue (no condition)
                        "#E67E22",  # 8 - Any Issue (from negative): Orange warning
                        "#5DADE2",  # 9 - No Issue (from negative): Light blue
                        "#1E8449",  # 10 - True Positive: Deep green (success)
                        "#C0392B",  # 11 - False Positive: Red (false alarm)
                        "#2874A6",  # 12 - True Negative: Deep blue (success)
                        "#922B21",  # 13 - False Negative: Dark red (critical miss)
                    ],
                    # Manual positioning: x for horizontal, y for vertical (0=top, 1=bottom)
                    # x = [0.01, 0.25, 0.25, 0.5, 0.5, 0.75, 0.75, 0.01, 0.25, 0.25, 0.99, 0.99, 0.99, 0.99],
                    y=[
                        0.2,
                        0.1,
                        0.3,
                        0.05,
                        0.25,
                        0.01,
                        0.15,
                        0.7,
                        0.55,
                        0.8,
                        0.01,
                        0.25,
                        0.95,
                        0.5,
                    ],
                ),
                link=dict(
                    source=[link[0] for link in links],
                    target=[link[1] for link in links],
                    value=[link[2] for link in links],
                ),
            )
        ]
    )

    fig.update_layout(
        # title_text="MedGuard Sankey Diagram",
        font_size=10,  # Reduced to fit the extra text
        height=600,
    )
    return fig


def generate_binary_sankey_figure(performance_metrics: "FilterPerformanceMetrics") -> go.Figure:
    # Define the flow data
    links = [
        # Positive Ground Truth
        (0, 1, performance_metrics.positive_gt_any_issue),
        (0, 2, performance_metrics.positive_gt_no_issue),
        # Negative Ground Truth
        (3, 4, performance_metrics.negative_gt_any_issue),
        (3, 5, performance_metrics.negative_gt_no_issue),
        # Correct
        (1, 6, performance_metrics.positive_gt_any_issue),
        (5, 6, performance_metrics.negative_gt_no_issue),
        # Incorrect
        (2, 7, performance_metrics.positive_gt_no_issue),
        (4, 7, performance_metrics.negative_gt_any_issue),
    ]

    # Calculate total input for percentages (ground truth nodes are 0 and 3)
    total_input = sum(link[2] for link in links if link[0] in [0, 3])

    # Calculate flow through each node - only count INCOMING flows to avoid double-counting
    node_values = {}
    for source, target, value in links:
        node_values[target] = node_values.get(target, 0) + value

    # For source-only nodes (no incoming flows), sum ALL their outgoing flows
    source_only_nodes = set()
    for source, target, value in links:
        if source not in node_values:
            source_only_nodes.add(source)

    for node in source_only_nodes:
        node_values[node] = sum(value for source, target, value in links if source == node)

    # Original labels
    labels = [
        "Positive Ground Truth",  # 0
        "Any Issue Identified",  # 1
        "No Issue Identified",  # 2
        "Negative Ground Truth",  # 3
        "Any Issue Identified",  # 4
        "No Issue Identified",  # 5
        "Correct",  # 6
        "Incorrect",  # 7
    ]

    # Add values and percentages to labels
    labels_with_values = [
        f"{label}<br>{node_values.get(i, 0)} ({node_values.get(i, 0) / total_input * 100:.1f}%)"
        for i, label in enumerate(labels)
    ]

    fig = go.Figure(
        data=[
            go.Sankey(
                # arrangement='snap',
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=labels_with_values,
                    color=[
                        "#2ECC71",  # 0 - Positive GT: Green
                        "#F39C12",  # 1 - Any Issue Identified (from positive): Amber
                        "#E74C3C",  # 2 - No Issue Identified (from positive): Red flag
                        "#3498DB",  # 3 - Negative GT: Blue
                        "#E67E22",  # 4 - Any Issue (from negative): Orange warning
                        "#5DADE2",  # 5 - No Issue (from negative): Light blue
                        "#1E8449",  # 6 - Correct: Deep green (success)
                        "#C0392B",  # 7 - Incorrect: Red (error)
                    ],
                    # Manual positioning: x for horizontal, y for vertical (0=top, 1=bottom)
                    # Column 1: Ground truths (0, 3)
                    # Column 2: Intermediate classifications (1, 2, 4, 5)
                    # Column 3: Final outcomes (6, 7)
                    x=[0.01, 0.5, 0.5, 0.01, 0.5, 0.5, 0.99, 0.99],
                    y=[0.2, 0.1, 0.3, 0.7, 0.8, 0.6, 0.3, 0.7],
                ),
                link=dict(
                    source=[link[0] for link in links],
                    target=[link[1] for link in links],
                    value=[link[2] for link in links],
                ),
            )
        ]
    )

    fig.update_layout(title_text="MedGuard Binary Classification", font_size=10, height=600)
    return fig
