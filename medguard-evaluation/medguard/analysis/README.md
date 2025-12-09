# MedGuard Analysis Framework

This directory contains the analysis framework for generating results, tables, and figures for the MedGuard evaluation paper.

## Overview

The analysis framework provides two base classes for creating standardized analyses:

1. **`EvaluationAnalysisBase`** - For analyses that produce tabular data (polars DataFrames) and optional visualizations
2. **`TextAnalysisBase`** - For analyses that produce formatted text reports

All analyses follow a consistent pattern: `execute()` → `save()` → optional `plot()` or `run_figure()`.

## File Structure

```
medguard/analysis/
├── README.md                          # This file
├── base.py                            # Base classes
├── filters.py                         # Filter utilities for stratification
├── performance_by_filter.py           # Example: DataFrame + plot analysis
├── performance_by_complexity.py       # Example: DataFrame + plot analysis
├── performance_summary.py             # Example: Text-based analysis
├── expert_pincer_comparison.py        # Example: Multiple analyses in one file
├── model_comparison.py                # Example: Custom initialization
└── self_consistency.py                # Example: Specialized analysis
```

## Adding a New Analysis

### Option 1: DataFrame-Based Analysis (with optional plots)

Use `EvaluationAnalysisBase` when you want to:
- Generate tabular data (metrics, stratified results, etc.)
- Save results as CSV files
- Optionally create matplotlib visualizations

**Step-by-step:**

1. **Create a new file** in `medguard/analysis/` (e.g., `my_analysis.py`)

2. **Implement the analysis class:**

```python
"""
My Analysis Title

Brief description of what this analysis does and which table/figure
it corresponds to in the paper.

Section: X.X.X
"""

import polars as pl
import matplotlib.pyplot as plt
from medguard.analysis.base import EvaluationAnalysisBase


class MyAnalysis(EvaluationAnalysisBase):
    """
    One-line description of the analysis.
    
    More detailed description of what metrics are computed,
    how data is stratified, etc.
    """

    def __init__(self, evaluation, name: str = "my_analysis"):
        super().__init__(evaluation, name=name)

    def execute(self) -> pl.DataFrame:
        """
        Execute analysis and return DataFrame.
        
        Returns DataFrame with columns:
        - column1: Description
        - column2: Description
        - ...
        """
        # Your analysis logic here
        # Access evaluation data via self.evaluation
        
        rows = []
        # ... compute metrics ...
        
        df = pl.DataFrame(rows)
        return df

    def plot(self) -> plt.Figure:
        """
        Optional: Create visualization from saved data.
        
        Returns:
            Matplotlib figure
        """
        df = self.load_df()
        
        # Create your plot
        fig, ax = plt.subplots(figsize=(10, 6))
        # ... plotting code ...
        
        return fig
```

3. **Export the class** in `__init__.py`:

```python
from medguard.analysis.my_analysis import MyAnalysis

__all__ = [
    # ... existing exports ...
    "MyAnalysis",
]
```

4. **Add to generation script** in `scripts/generate_plots.py`:

```python
from medguard.analysis import MyAnalysis

def main():
    evaluation = load_pydantic_from_json(Evaluation, "path/to/evaluation.json")
    
    df_analyses: list[EvaluationAnalysisBase] = [
        # ... existing analyses ...
        MyAnalysis(evaluation),
    ]
```

### Option 2: Text-Based Analysis

Use `TextAnalysisBase` when you want to:
- Generate formatted text reports
- Save results as `.txt` files
- No plotting needed

**Step-by-step:**

1. **Create a new file** in `medguard/analysis/` (e.g., `my_text_analysis.py`)

2. **Implement the analysis class:**

```python
"""
My Text Analysis Title

Brief description of the text report this generates.
"""

from medguard.analysis.base import TextAnalysisBase


class MyTextAnalysis(TextAnalysisBase):
    """Generate formatted text summary of X."""

    def __init__(self, evaluation, name: str = "my_text_analysis"):
        super().__init__(evaluation, name=name)

    def execute(self) -> str:
        """
        Execute analysis and return formatted text.
        
        Returns:
            Formatted string with analysis results
        """
        # Your analysis logic here
        output = "=" * 80 + "\n"
        output += "MY ANALYSIS TITLE\n"
        output += "=" * 80 + "\n\n"
        
        # ... compute and format results ...
        
        return output
```

3. **Export and add to script** (same as Option 1, but in `text_analyses` list)

```python
text_analyses: list[TextAnalysisBase] = [
    # ... existing analyses ...
    MyTextAnalysis(evaluation),
]

for analysis in text_analyses:
    analysis.run()  # Execute and save (no plotting)
```

## Base Class Reference

### `EvaluationAnalysisBase`

**Constructor:**
```python
def __init__(self, evaluation: Evaluation, name: str, output_dir: str = "outputs/eval_analyses")
```

**Methods:**
- `execute() -> pl.DataFrame` - **[Abstract]** Implement your analysis logic
- `save(df: Optional[pl.DataFrame] = None) -> Path` - Save DataFrame to CSV
- `load_df() -> pl.DataFrame` - Load DataFrame from saved CSV
- `plot() -> Optional[Union[plt.Figure, List[tuple[plt.Figure, str]]]]` - **[Optional]** Create visualization(s)
- `save_figure_to_png(fig: plt.Figure, suffix: str = "") -> Path` - Save figure to PNG
- `run_figure(suffix: str = "") -> Optional[Union[Path, List[Path]]]` - Generate and save plot(s)
- `run() -> tuple[pl.DataFrame, Path]` - Execute and save in one call

**Attributes:**
- `self.evaluation` - The Evaluation instance
- `self.name` - Analysis name (used for filenames)
- `self.output_dir` - Directory for CSV outputs
- `self.plots_dir` - Directory for PNG outputs (`output_dir/plots/`)

### `TextAnalysisBase`

**Constructor:**
```python
def __init__(self, evaluation: Evaluation, name: str, output_dir: str = "outputs/eval_analyses")
```

**Methods:**
- `execute() -> str` - **[Abstract]** Implement your analysis logic
- `save(text: Optional[str] = None) -> Path` - Save text to .txt file
- `load_text() -> str` - Load text from saved file
- `run() -> tuple[str, Path]` - Execute and save in one call

**Attributes:**
- `self.evaluation` - The Evaluation instance
- `self.name` - Analysis name (used for filenames)
- `self.output_dir` - Directory for text outputs

## Common Patterns

### Multiple Plots from One Analysis

Return a list of `(figure, suffix)` tuples:

```python
def plot(self) -> List[tuple[plt.Figure, str]]:
    df = self.load_df()
    
    fig1, ax1 = plt.subplots()
    # ... create first plot ...
    
    fig2, ax2 = plt.subplots()
    # ... create second plot ...
    
    return [(fig1, "_bar"), (fig2, "_scatter")]
```

This will save:
- `my_analysis_bar.png`
- `my_analysis_scatter.png`

### Multiple Related Analyses in One File

See `expert_pincer_comparison.py` for an example of defining multiple analysis classes in a single file when they share common logic.

### Custom Initialization

You can pass additional parameters or multiple evaluations (see `model_comparison.py`):

```python
class MyAnalysis(EvaluationAnalysisBase):
    def __init__(self, evaluation, custom_param: str, name: str = "my_analysis"):
        super().__init__(evaluation, name=name)
        self.custom_param = custom_param
```

### Filtering and Stratification

Use utilities from `filters.py`:

```python
from medguard.analysis.filters import by_filter, agrees_with_rules, PINCER_FILTER_IDS

# Filter by PINCER filter ID
ids = self.evaluation.filter_by_analysed_record(by_filter("F1"))

# Filter by clinician agreement
ids = self.evaluation.filter_by_clinician_evaluation(agrees_with_rules())

# Combine filters with set operations
filtered_ids = ids_from_filter & ids_from_clinician

# Create filtered evaluation
filtered_eval = self.evaluation.filter_by_patient_ids(filtered_ids)
```

## Output Locations

By default, all analyses save to:

```
outputs/eval_analyses/
├── analysis_name.csv              # DataFrame results
├── analysis_name.txt              # Text results
└── plots/
    ├── analysis_name.png          # Single plot
    ├── analysis_name_suffix1.png  # Multiple plots
    └── analysis_name_suffix2.png
```

You can override the `output_dir` in the constructor:

```python
MyAnalysis(evaluation, name="custom", output_dir="outputs/custom_location")
```

## Best Practices

1. **Naming Convention:**
   - Use descriptive names: `performance_by_filter` not `analysis1`
   - Match the paper section/figure: `"figure_2"` or `"table_3"`

2. **Documentation:**
   - Module docstring: Describe what analysis does and paper reference
   - Class docstring: Brief description
   - `execute()` docstring: Document returned DataFrame columns or text format

3. **Data Access:**
   - Access data via `self.evaluation`
   - Use filtering methods for stratification
   - Don't modify the original evaluation object

4. **Error Handling:**
   - Handle empty filtered datasets gracefully
   - Check for None values in clinician evaluations
   - Validate inputs in custom constructors

5. **Plotting:**
   - Use publication-ready styles: `plt.style.use("seaborn-v0_8-paper")`
   - Set appropriate font sizes (11-13pt)
   - Include clear labels, legends, and titles
   - Use `tight_layout()` to prevent label cutoff
   - Always call `plt.close(fig)` (handled by `save_figure_to_png`)

6. **Testing:**
   - Test with small subsets of data first
   - Verify CSV/txt outputs manually
   - Check plot appearance before finalizing

## Examples

See existing analysis files for complete examples:

- **Simple DataFrame analysis:** `performance_by_filter.py`
- **Complex plotting:** `performance_by_complexity.py`
- **Text-based analysis:** `performance_summary.py`
- **Multiple plots:** `expert_pincer_comparison.py`
- **Custom initialization:** `model_comparison.py`

## Running Analyses

**Single analysis:**
```python
from medguard.analysis import MyAnalysis
from medguard.evaluation.evaluation import Evaluation
from medguard.utils.parsing import load_pydantic_from_json

evaluation = load_pydantic_from_json(Evaluation, "path/to/evaluation.json")
analysis = MyAnalysis(evaluation)

# Option 1: Run everything
df, csv_path = analysis.run()
plot_path = analysis.run_figure()

# Option 2: Step by step
df = analysis.execute()
csv_path = analysis.save(df)
fig = analysis.plot()
plot_path = analysis.save_figure_to_png(fig)
```

**Batch processing:**
```bash
# From repo root
python scripts/generate_plots.py
```

## Troubleshooting

**Import errors:**
- Ensure you added the class to `__init__.py`
- Check for circular imports

**File not found errors:**
- Run `execute()` and `save()` before `load_df()` or `load_text()`
- Check that evaluation data path is correct

**Plot not saving:**
- Ensure `plot()` returns a Figure or list of (Figure, suffix) tuples
- Check that `plots_dir` exists (created automatically)

**Type errors:**
- Verify `execute()` return type matches base class (DataFrame or str)
- Check that all DataFrame operations return polars DataFrames, not pandas

