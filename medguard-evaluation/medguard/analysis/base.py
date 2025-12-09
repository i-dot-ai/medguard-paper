"""Base class for evaluation analyses."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Union

import matplotlib.pyplot as plt
import polars as pl

if TYPE_CHECKING:
    from medguard.evaluation.evaluation import Evaluation


class EvaluationAnalysisBase(ABC):
    """Abstract base class for evaluation analyses."""

    def __init__(
        self, evaluation: "Evaluation", name: str, output_dir: str = "outputs/eval_analyses"
    ):
        """Initialize analysis with evaluation data and output configuration."""
        self.evaluation: "Evaluation" = evaluation
        self.name: str = name
        self.output_dir: Path = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.plots_dir: Path = self.output_dir / "plots"
        self.plots_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def execute(self) -> pl.DataFrame:
        """Execute analysis and return results as DataFrame."""
        pass

    def save(self, df: Optional[pl.DataFrame] = None) -> Path:
        """Save DataFrame to CSV. If df is None, executes analysis first."""
        if df is None:
            df = self.execute()
        output_path = self.output_dir / f"{self.name}.csv"
        df.write_csv(output_path)
        return output_path

    def load_df(self) -> pl.DataFrame:
        """Load DataFrame from saved CSV file."""
        csv_path = self.output_dir / f"{self.name}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(
                f"CSV file not found: {csv_path}. Run execute() and save() first."
            )
        return pl.read_csv(csv_path)

    def plot(self) -> Optional[Union[plt.Figure, List[tuple[plt.Figure, str]]]]:
        """
        Create visualization(s) from saved data.

        Returns:
            - Single matplotlib figure
            - List of (figure, suffix) tuples for multiple plots
            - None if plotting not implemented
        """
        return None

    def save_figure_to_png(self, fig: plt.Figure, suffix: str = "") -> Path:
        """Save matplotlib figure to PNG file."""
        filename = f"{self.name}{suffix}.png" if suffix else f"{self.name}.png"
        output_path = self.plots_dir / filename
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def run_figure(self, suffix: str = "") -> Optional[Union[Path, List[Path]]]:
        """Generate plot(s) and save to PNG."""
        result = self.plot()
        if result is None:
            return None

        if isinstance(result, plt.Figure):
            return self.save_figure_to_png(result, suffix=suffix)

        if isinstance(result, list):
            paths = []
            for item in result:
                if isinstance(item, tuple) and len(item) == 2:
                    fig, fig_suffix = item
                    paths.append(self.save_figure_to_png(fig, suffix=fig_suffix))
                else:
                    paths.append(self.save_figure_to_png(item, suffix=suffix))
            return paths

        return None

    def run(self) -> tuple[pl.DataFrame, Path]:
        """Execute analysis and save results."""
        df = self.execute()
        path = self.save(df)
        return df, path


class TextAnalysisBase(ABC):
    """Abstract base class for text-based evaluation analyses."""

    def __init__(
        self, evaluation: "Evaluation", name: str, output_dir: str = "outputs/eval_analyses"
    ):
        """Initialize analysis with evaluation data and output configuration."""
        self.evaluation: "Evaluation" = evaluation
        self.name: str = name
        self.output_dir: Path = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def execute(self) -> str:
        """Execute analysis and return formatted text."""
        pass

    def save(self, text: Optional[str] = None) -> Path:
        """Save text to .txt file. If text is None, executes analysis first."""
        if text is None:
            text = self.execute()
        output_path = self.output_dir / f"{self.name}.txt"
        output_path.write_text(text)
        return output_path

    def load_text(self) -> str:
        """Load text from saved .txt file."""
        txt_path = self.output_dir / f"{self.name}.txt"
        if not txt_path.exists():
            raise FileNotFoundError(
                f"Text file not found: {txt_path}. Run execute() and save() first."
            )
        return txt_path.read_text()

    def run(self) -> tuple[str, Path]:
        """Execute analysis and save results."""
        text = self.execute()
        path = self.save(text)
        return text, path
