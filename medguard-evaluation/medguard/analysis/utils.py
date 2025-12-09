"""
Utility functions for evaluation analyses.

Common patterns and helpers to reduce boilerplate in analysis implementations.
"""

import matplotlib.pyplot as plt


def setup_publication_plot(
    figsize: tuple[float, float] = (10, 6),
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    """
    Create matplotlib figure with consistent publication styling.

    Args:
        figsize: Figure size in inches (width, height)
        title: Optional plot title
        xlabel: Optional x-axis label
        ylabel: Optional y-axis label

    Returns:
        Tuple of (figure, axes) ready for plotting

    Example:
        fig, ax = setup_publication_plot(
            title="Performance by Age",
            xlabel="Age",
            ylabel="Score"
        )
        ax.bar(x, y)
        return fig
    """
    # Set publication style
    plt.style.use("seaborn-v0_8-paper")
    plt.rcParams["font.size"] = 11
    plt.rcParams["axes.labelsize"] = 12
    plt.rcParams["axes.titlesize"] = 13

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Set labels if provided
    if title:
        ax.set_title(title, fontweight="bold", pad=20)
    if xlabel:
        ax.set_xlabel(xlabel, fontweight="bold")
    if ylabel:
        ax.set_ylabel(ylabel, fontweight="bold")

    # Standard grid
    ax.grid(axis="y", alpha=0.3, linestyle="--")

    return fig, ax
