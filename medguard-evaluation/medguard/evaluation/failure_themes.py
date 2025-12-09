from collections import defaultdict
from pydantic import BaseModel
from medguard.evaluation.themefinder import (
    CANDIDATE_THEMES,
    OpenAISemaphoreClient,
    ThemeDiscoveryPipeline,
)
from medguard.scorer.models import AnalysedPatientRecord, FailureReason

import plotly.graph_objects as go
from plotly.subplots import make_subplots


class FailureThemes(BaseModel):
    counts: dict[FailureReason, int]
    subcounts: dict[FailureReason, dict[str, int]]


def get_traces_and_themes_from_analysed_patient_records(
    records: list[AnalysedPatientRecord],
) -> list[list[str], list[str]]:
    failures: dict[FailureReason, list[str]] = defaultdict(list)

    for record in records:
        if record.evaluation_analysis.failure_analysis:
            for failure in record.evaluation_analysis.failure_analysis:
                failures[failure.reason].append(failure.reasoning)

    result = []
    for reason in list(FailureReason):
        themes = CANDIDATE_THEMES[reason]
        traces = failures[reason]

        result.append((traces, themes))

    return result


async def get_failure_count_and_dict(
    reasons: list[str], themes: list[str]
) -> tuple[int, dict[str, int]]:
    themefinder = ThemeDiscoveryPipeline()
    res = await themefinder.run_themefinder(traces=reasons, themes=themes)

    theme_counts = defaultdict(int)
    for theme_list in res:
        for theme in theme_list:
            theme_counts[theme] += 1
    return len(res), theme_counts


def get_failures_by_reason(
    failure_reasons: dict[FailureReason, list[str]],
    themes_by_reason: dict[FailureReason, list[str]],
) -> FailureThemes:
    counts: dict[FailureReason, int] = {}
    subcounts: dict[FailureReason, dict[str, int]] = {}

    for reason in list(FailureReason):
        individual_failure_reasons = failure_reasons[reason]
        individual_failure_themes = themes_by_reason[reason]
        count, themes_dict = get_failure_count_and_dict(
            individual_failure_reasons, individual_failure_themes
        )

        counts[reason] = count
        subcounts[reason] = themes_dict

    return FailureThemes(counts=counts, subcounts=subcounts)


def get_failure_themes_from_themefinder_results(
    results: list[list[str]], traces_and_themes: list[list[str]]
) -> FailureThemes:
    counts = {}
    subcounts = {}

    i = 0
    for reason, (traces, themes) in zip(list(FailureReason), traces_and_themes):
        traces_count = len(traces)

        themes_dict = defaultdict(lambda: 0)
        for trace in traces:
            trace_themes = results[i]
            for theme in trace_themes:
                themes_dict[theme.replace("‑", "-")] += 1
            i += 1

        counts[reason] = traces_count
        subcounts[reason] = dict(themes_dict)

    return FailureThemes(
        counts=counts,
        subcounts=subcounts,
    )


async def get_failure_themes_from_analysed_patient_records(
    records: list[AnalysedPatientRecord], n_concurrent_requests: int = 50
) -> FailureThemes:
    traces_and_themes = get_traces_and_themes_from_analysed_patient_records(records)

    client = OpenAISemaphoreClient(max_concurrent_requests=n_concurrent_requests)
    themefinder = ThemeDiscoveryPipeline()

    results = await themefinder.classify_all_traces_multiple_themes(traces_and_themes, client)

    return get_failure_themes_from_themefinder_results(results, traces_and_themes)


def plot_failure_themes(failure_themes: FailureThemes):
    """
    Creates a visualization with:
    - Top plot: Bar chart of failure counts sorted largest to smallest
    - Bottom: 3x3 grid of subcount bar charts for each failure reason
    """

    def truncate_text(text, max_length=20):
        """Truncate text for display while keeping full text for hover"""
        return text if len(text) <= max_length else text[: max_length - 3] + "..."

    # Sort main counts from largest to smallest
    sorted_counts = sorted(failure_themes.counts.items(), key=lambda x: x[1], reverse=True)

    # Create subplots: 1 row for main plot, then 3x3 grid for subcounts
    fig = make_subplots(
        rows=4,
        cols=3,
        row_heights=[0.25, 0.25, 0.25, 0.25],
        subplot_titles=["Failure Counts by Reason"]
        + [reason.value.replace("_", " ").title() for reason, _ in sorted_counts],
        specs=[[{"type": "bar", "colspan": 3}, None, None]]
        + [[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}] for _ in range(3)],
        vertical_spacing=0.12,
        horizontal_spacing=0.12,
    )

    # Top plot: Main failure counts
    reasons = [reason.value.replace("_", " ") for reason, _ in sorted_counts]
    counts = [count for _, count in sorted_counts]

    fig.add_trace(
        go.Bar(
            x=reasons,
            y=counts,
            text=counts,
            textposition="outside",
            marker_color="lightblue",
            showlegend=False,
            hovertext=reasons,
            hovertemplate="<b>%{hovertext}</b><br>Count: %{y}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # 3x3 grid: Subcounts for each failure reason
    for idx, (reason, _) in enumerate(sorted_counts):
        row = (idx // 3) + 2  # Start from row 2
        col = (idx % 3) + 1

        subcounts = failure_themes.subcounts.get(reason, {})

        if subcounts:
            # Sort subcounts from largest to smallest
            sorted_subcounts = sorted(subcounts.items(), key=lambda x: x[1], reverse=True)
            sub_labels_full = [label for label, _ in sorted_subcounts]
            sub_labels_truncated = [truncate_text(label, 15) for label in sub_labels_full]
            sub_values = [value for _, value in sorted_subcounts]

            fig.add_trace(
                go.Bar(
                    x=sub_labels_truncated,
                    y=sub_values,
                    text=sub_values,
                    textposition="outside",
                    marker_color="lightcoral",
                    showlegend=False,
                    hovertext=sub_labels_full,
                    hovertemplate="<b>%{hovertext}</b><br>Count: %{y}<extra></extra>",
                ),
                row=row,
                col=col,
            )
        else:
            # No subcounts available
            fig.add_annotation(
                text="No subcategories",
                xref=f"x{idx + 2}",
                yref=f"y{idx + 2}",
                x=0.5,
                y=0.5,
                xanchor="center",
                showarrow=False,
                font=dict(size=12, color="gray"),
                row=row,
                col=col,
            )

    # Update layout
    fig.update_xaxes(tickangle=45, tickfont=dict(size=10))
    fig.update_yaxes(tickfont=dict(size=10))
    fig.update_layout(
        height=1800,
        width=1600,
        title_text="Failure Analysis Dashboard",
        title_font_size=24,
        showlegend=False,
        font=dict(size=11),
    )

    # Update subplot titles font size
    for annotation in fig["layout"]["annotations"]:
        annotation["font"] = dict(size=12)

    return fig
