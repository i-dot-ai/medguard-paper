"""
Base class for all analysis statistics.

Each analysis:
1. Defines SQL template as class variable
2. Implements get_sql_statement() to return formatted SQL
3. Optionally implements post_process_df() for polars transformations
4. Inherits execute() and save() from base class
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union, List

import polars as pl
import matplotlib.pyplot as plt

from medguard.data_processor import ModularPatientDataProcessor


class AnalysisBase(ABC):
    """
    Abstract base class for analysis statistics.

    Usage:
        class MyAnalysis(AnalysisBase):
            SQL = "SELECT COUNT(*) as total FROM {table}"

            def __init__(self, processor):
                super().__init__(processor, name="my_analysis")

            def get_sql_statement(self) -> str:
                return self.SQL.format(table="my_table")

            def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
                # Optional: add transformations
                return df
    """

    def __init__(
        self,
        processor: ModularPatientDataProcessor,
        name: str,
        output_dir: str = "outputs/statistics",
    ):
        """
        Initialize analysis.

        Args:
            processor: ModularPatientDataProcessor instance
            name: Name for output file (without extension)
            output_dir: Directory to save output CSV
        """
        self.processor: ModularPatientDataProcessor = processor
        self.name: str = name
        self.output_dir: Path = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create plots subdirectory
        self.plots_dir: Path = self.output_dir / "plots"
        self.plots_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def get_sql_statement(self) -> str:
        """
        Return the SQL statement to execute.

        Can format SQL template with processor.default_kwargs or other values.

        Returns:
            SQL query string
        """
        pass

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Post-process the DataFrame with polars transformations.

        Override this method to add any polars-specific transformations
        after SQL execution.

        Args:
            df: Polars DataFrame from SQL query

        Returns:
            Transformed polars DataFrame
        """
        # Default: no transformation
        return df

    def execute(self) -> pl.DataFrame:
        """
        Execute the SQL statement and return polars DataFrame.

        Returns:
            Polars DataFrame with query results
        """
        sql = self.get_sql_statement()

        # Execute SQL and get pandas DataFrame
        pandas_df = self.processor.conn.execute(sql).df()

        # Convert to polars DataFrame
        polars_df = pl.from_pandas(pandas_df)

        # Apply post-processing
        result = self.post_process_df(polars_df)

        return result

    def save(self, df: Optional[pl.DataFrame] = None) -> Path:
        """
        Save DataFrame to CSV file.

        Args:
            df: DataFrame to save. If None, executes query first.

        Returns:
            Path to saved CSV file
        """
        if df is None:
            df = self.execute()

        output_path = self.output_dir / f"{self.name}.csv"
        df.write_csv(output_path)

        return output_path

    def load_df(self) -> pl.DataFrame:
        """
        Load DataFrame from saved CSV file.

        Returns:
            Polars DataFrame loaded from CSV

        Raises:
            FileNotFoundError: If CSV file does not exist
        """
        csv_path = self.output_dir / f"{self.name}.csv"

        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        return pl.read_csv(csv_path)

    def plot(self) -> Optional[Union[plt.Figure, List[plt.Figure]]]:
        """
        Create visualization(s) from saved data.

        Override this method to create matplotlib figures from the saved CSV data.
        Use self.load_df() to load the data.

        Returns:
            Single matplotlib figure, list of figures, or None if plotting not implemented
        """
        # Default: no plot implementation
        return None

    def save_figure_to_png(self, fig: plt.Figure, suffix: str = "") -> Path:
        """
        Save matplotlib figure to PNG file.

        Args:
            fig: Matplotlib figure to save
            suffix: Optional suffix to add to filename (e.g., "_histogram")

        Returns:
            Path to saved PNG file
        """
        if suffix:
            filename = f"{self.name}{suffix}.png"
        else:
            filename = f"{self.name}.png"

        output_path = self.plots_dir / filename
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

        return output_path

    def run_figure(self, suffix: str = "") -> Optional[Union[Path, List[Path]]]:
        """
        Generate plot(s) and save to PNG.

        Convenience method that calls plot() and save_figure_to_png().

        Args:
            suffix: Optional suffix to add to filename (only used if plot() returns single figure)

        Returns:
            Path to saved PNG file, list of paths, or None if plotting not implemented
        """
        result = self.plot()

        if result is None:
            return None

        # Handle single figure
        if isinstance(result, plt.Figure):
            path = self.save_figure_to_png(result, suffix=suffix)
            return path

        # Handle list of (figure, suffix) tuples
        if isinstance(result, list):
            paths = []
            for item in result:
                if isinstance(item, tuple) and len(item) == 2:
                    fig, fig_suffix = item
                    path = self.save_figure_to_png(fig, suffix=fig_suffix)
                    paths.append(path)
                else:
                    # Just a figure without suffix
                    path = self.save_figure_to_png(item, suffix=suffix)
                    paths.append(path)
            return paths

        return None

    def run(self) -> tuple[pl.DataFrame, Path]:
        """
        Execute query and save results.

        Convenience method that combines execute() and save().

        Returns:
            Tuple of (DataFrame, output_path)
        """
        df = self.execute()
        path = self.save(df)

        return df, path
