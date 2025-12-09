from plotly import graph_objects as go


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .performance_metrics import GroundTruthPerformanceMetrics


def generate_full_sankey_figure(data: "GroundTruthPerformanceMetrics"):
    labels = [
        "Positive ground truth",  # 0
        "Negative ground truth",  # 1
        "Any issue identified",  # 2
        "Any issue identified",  # 3
        "No issues identified",  # 4
        "All issues correct",  # 5
        "Some issues correct",  # 6
        "Correct intervention",  # 7
        "Partially correct intervention",  # 8
        "Incorrect intervention",  # 9
    ]

    links = [
        (0, 2, data.positive_any_issue),
        (1, 3, data.negative_any_issue),
        (1, 4, data.negative_no_issue),
        (2, 5, data.positive_all_correct),
        (2, 6, data.positive_some_correct),
        (3, 9, data.negative_any_issue),
        (4, 7, data.negative_no_issue),
        (5, 7, data.all_correct_correct_intervention),
        (5, 8, data.all_correct_partial_intervention),
        (5, 9, data.all_correct_incorrect_intervention),
        (6, 7, data.some_correct_correct_intervention),
        (6, 8, data.some_correct_partial_intervention),
        (6, 9, data.some_correct_incorrect_intervention),
    ]

    node_colors = [
        "#3498db",  # 0: Positive Ground Truth - blue
        "#95a5a6",  # 1: Negative Ground Truth - gray
        "#5dade2",  # 2: Positive Any Issue - light blue
        "#f39c12",  # 3: Negative Any Issue - orange (problematic - FP)
        "#27ae60",  # 4: Negative No Issue - green (TN)
        "#2ecc71",  # 5: Positive All Correct - bright green
        "#f1c40f",  # 6: Positive Some Correct - yellow
        "#27ae60",  # 7: Correct Intervention - green (TP)
        "#f39c12",  # 8: Partial Correct Intervention - orange
        "#e74c3c",  # 9: Incorrect Intervention - red (FN)
    ]

    links = [(source, target, value) for source, target, value in links if value > 0]

    # Calculate total input for percentages
    total_input = sum(link[2] for link in links if link[0] in [0, 1])

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

    # Add values and percentages to labels
    labels_with_values = [
        f"{label}<br>{node_values.get(i, 0)} ({node_values.get(i, 0) / total_input * 100:.1f}%)"
        for i, label in enumerate(labels)
    ]

    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=labels_with_values,
                    color=node_colors,
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
        font_size=10,
        height=600,
    )

    return fig
