# MedGuard Statistical Analyses

This module contains all statistical analyses for the MedGuard paper, including SQL queries, data processing, and visualization code.

## Overview

The analysis system is built around a base class pattern where each analysis:
1. Defines SQL queries to extract data from the database
2. Processes the results into a clean DataFrame
3. Saves the results as CSV files
4. Optionally generates publication-quality plots

## Architecture

### Base Class: `AnalysisBase`

All analyses inherit from `AnalysisBase` (`base.py`), which provides:

**Data Management**:
- `get_sql_statement()` - Return SQL query (abstract, must implement)
- `execute()` - Run SQL and return DataFrame
- `post_process_df(df)` - Optional transformation hook
- `save(df)` - Save DataFrame to CSV
- `run()` - Execute and save in one call

**Plotting**:
- `plot()` - Override to return matplotlib figure(s)
- `save_figure_to_png()` - Save figures to PNG (300 DPI)
- `run_figure()` - Generate and save plot(s)
- `load_df()` - Load saved CSV data for plotting

**File Paths**:
- CSV files: `outputs/statistics/{name}.csv`
- Plots: `outputs/statistics/plots/{name}.png`

## Creating a New Analysis

### Basic Structure

```python
"""
Brief description of what this analysis computes.

Section: [Paper section, e.g., 2.2 Data Source and Population]
Returns: [Description of output columns]
"""

import polars as pl
import matplotlib.pyplot as plt
from medguard.analysis.base import AnalysisBase

# SQL template at the top
SQL = """
SELECT
    column1,
    COUNT(*) as count
FROM {table_name}
WHERE condition = TRUE
GROUP BY column1
"""

class MyNewAnalysis(AnalysisBase):
    """One-line description for __init__ exports."""

    def __init__(self, processor):
        super().__init__(processor, name="my_analysis_name")

    def get_sql_statement(self) -> str:
        """Return SQL query for this analysis."""
        return SQL.format(
            table_name=self.processor.default_kwargs["table_name"]
        )

    def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
        """Optional: Transform the DataFrame after SQL execution."""
        # Add calculated columns, percentages, etc.
        total = df["count"].sum()
        return df.with_columns([
            (pl.col("count") / total * 100).round(1).alias("percentage")
        ])

    def plot(self) -> plt.Figure:
        """Optional: Create visualization from saved data."""
        df = self.load_df()  # Load the saved CSV

        # Set publication style
        plt.style.use('seaborn-v0_8-paper')
        plt.rcParams['font.size'] = 11
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 13

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(df['column1'], df['percentage'], color='#3498db', alpha=0.8)
        ax.set_xlabel('Category', fontweight='bold')
        ax.set_ylabel('Percentage (%)', fontweight='bold')
        ax.set_title('My Analysis Title', fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()
        return fig
```

### Add to Module Exports

In `src/medguard/analysis/__init__.py`:

```python
from medguard.analysis.my_new_analysis import MyNewAnalysis

__all__ = [
    # ... existing exports
    "MyNewAnalysis",
]
```

### Add to Run Scripts

In `scripts/run_statistics_analyses.py`:

```python
from medguard.analysis.my_new_analysis import MyNewAnalysis

analyses = [
    # ... existing analyses
    MyNewAnalysis(processor),
]
```

If plotting is implemented, also add to `scripts/generate_all_plots.py`:

```python
from medguard.analysis.my_new_analysis import MyNewAnalysis

print("\nX. My New Analysis...")
analysis = MyNewAnalysis(processor=None)
output = analysis.run_figure()
print(f"   ✓ Saved to: {output}")
```

## SQL Patterns

### Basic Query

```python
SQL = """
SELECT
    FK_Patient_Link_ID,
    COUNT(*) as event_count
FROM {gp_events_view}
WHERE (Deleted = 'N' OR Deleted IS NULL)
    AND EventDate >= '2020-01-01'
GROUP BY FK_Patient_Link_ID
"""
```

### Using CTEs (Common Table Expressions)

CTEs make complex queries more readable:

```python
SQL = """
WITH filtered_patients AS (
    -- Step 1: Filter patients
    SELECT PK_Patient_Link_ID
    FROM {patient_link_view}
    WHERE (Merged != 'Y' OR Merged IS NULL)
        AND (Deleted != 'Y' OR Deleted IS NULL)
),
patient_events AS (
    -- Step 2: Get events for filtered patients
    SELECT
        fp.PK_Patient_Link_ID,
        e.EventDate,
        e.EventCode
    FROM filtered_patients fp
    LEFT JOIN {gp_events_view} e
        ON fp.PK_Patient_Link_ID = e.FK_Patient_Link_ID
    WHERE (e.Deleted = 'N' OR e.Deleted IS NULL)
)
SELECT
    PK_Patient_Link_ID,
    COUNT(*) as event_count
FROM patient_events
GROUP BY PK_Patient_Link_ID
ORDER BY event_count DESC
"""
```

### SQL Best Practices

1. **Use placeholders**: Always use `{table_name}` placeholders for table names
2. **Filter deleted records**: Include `(Deleted = 'N' OR Deleted IS NULL)` checks
3. **Filter merged patients**: Include `(Merged != 'Y' OR Merged IS NULL)` for patient links
4. **Use CTEs**: Break complex queries into logical steps with comments
5. **Add SQL comments**: Explain each CTE's purpose
6. **Handle NULLs**: Use `IS NULL` checks and `COALESCE()` where appropriate
7. **Date format**: Use ISO format `'YYYY-MM-DD'` for dates

### Using processor.default_kwargs

The processor contains a `default_kwargs` dictionary with standardized view names:

```python
def get_sql_statement(self) -> str:
    return SQL.format(
        patient_view=self.processor.default_kwargs["patient_view"],
        patient_link_view=self.processor.default_kwargs["patient_link_view"],
        gp_events_view=self.processor.default_kwargs["gp_events_view"],
        gp_prescriptions=self.processor.default_kwargs["gp_prescriptions"],
    )
```

## Data Processing with Polars

### Post-Processing Examples

```python
def post_process_df(self, df: pl.DataFrame) -> pl.DataFrame:
    # Calculate percentages
    total = df["count"].sum()
    df = df.with_columns([
        (pl.col("count") / total * 100).round(2).alias("percentage")
    ])

    # Add cumulative columns
    df = df.with_columns([
        pl.col("count").cum_sum().alias("cumulative_count"),
        (pl.col("count").cum_sum() / total * 100).round(2).alias("cumulative_pct")
    ])

    # Round numeric columns
    df = df.with_columns([
        pl.col("mean_value").round(2),
        pl.col("median_value").round(1),
    ])

    # Add calculated columns
    df = df.with_columns([
        (pl.col("end_date") - pl.col("start_date")).alias("duration_days")
    ])

    return df
```

## Plotting

### Single Plot

```python
def plot(self) -> plt.Figure:
    """Return a single figure."""
    df = self.load_df()

    plt.style.use('seaborn-v0_8-paper')
    plt.rcParams['font.size'] = 11

    fig, ax = plt.subplots(figsize=(10, 6))
    # ... plotting code ...

    plt.tight_layout()
    return fig
```

### Multiple Plots

Return a list of `(figure, suffix)` tuples:

```python
def plot(self):
    """Return list of (figure, suffix) tuples."""
    df = self.load_df()

    # Create linear scale plot
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    ax1.bar(df['x'], df['y'])
    # ... styling ...
    plt.tight_layout()

    # Create log scale plot
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    ax2.bar(df['x'], df['y'])
    ax2.set_yscale('log')
    # ... styling ...
    plt.tight_layout()

    return [(fig1, "_linear"), (fig2, "_log")]
```

### Plot Styling Guidelines

**Standard Colors**:
```python
COLORS = {
    'blue': '#3498db',      # General population
    'orange': '#e67e22',    # Elderly patients
    'green': '#2ecc71',     # Positive outcomes
    'red': '#e74c3c',       # Negative outcomes
    'purple': '#9b59b6',    # PINCER filters
}
```

**Figure Sizes**:
```python
SIZES = {
    'standard': (10, 6),
    'wide': (12, 6),
    'narrow': (8, 6),
}
```

**Always Include**:
```python
# Publication style
plt.style.use('seaborn-v0_8-paper')
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13

# Grid and labels
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_xlabel('Label', fontweight='bold')
ax.set_ylabel('Label', fontweight='bold')
ax.set_title('Title', fontweight='bold', pad=20)

# Tight layout
plt.tight_layout()
```

## Analysis Categories

### 1. SMR (Structured Medication Review) Analyses

**Files**: `smr_*.py`

- `smr_medication_change_contingency.py` - 2×2 table of outcomes vs changes
- `smr_time_window_sensitivity.py` - How detection varies by time window
- `smr_time_to_medication_change.py` - Distribution of change timings

### 2. Medication Distribution Analyses

**Files**: `active_medications_*.py`, `elderly_patients_*.py`

- `active_medications_per_patient_distribution.py` - Polypharmacy patterns
- `elderly_patients_medication_counts.py` - Medication burden in elderly

### 3. GP Events Analyses

**Files**: `gp_events_*.py`, `data_completeness_*.py`

- `gp_events_per_patient_histogram.py` - Healthcare utilization patterns
- `gp_events_date_range.py` - Temporal coverage
- `data_completeness_gp_events.py` - Data quality metrics

### 4. Socioeconomic Analyses

**Files**: `imd_distribution.py`

- `IMDDecilesAnalysis` - Distribution by deprivation deciles
- `IMDPercentilesPlotAnalysis` - Full percentile granularity
- `IMDSummaryStatisticsAnalysis` - Mean, median, quartiles

### 5. PINCER Filter Analyses

**Files**: `pincer_filter_statistics.py`

- `PincerFilterSummaryAnalysis` - Prevalence by filter type
- `PincerFilterMultipleMatchesAnalysis` - Patients matching multiple filters

## Running Analyses

### Development: Single Analysis

```python
from medguard.data_processor import ModularPatientDataProcessor
from medguard.analysis.total_patients import TotalPatientsAnalysis

# Initialize processor (reuse across analyses)
processor = ModularPatientDataProcessor()

# Run analysis
analysis = TotalPatientsAnalysis(processor)
df = analysis.run()
print(df)

# Generate plot (if implemented)
output_path = analysis.run_figure()
print(f"Plot saved to: {output_path}")
```

### Production: All Analyses

```bash
# Step 1: Run all analyses (requires database)
uv run scripts/run_statistics_analyses.py

# Step 2: Generate all plots (no database needed)
uv run scripts/generate_all_plots.py
```

### Paper Updates

Regenerate plots anytime (no database required):

```bash
uv run scripts/generate_all_plots.py
```

Plots are tracked in version control for reproducibility.

## Special Cases

### Analyses Without SQL

Some analyses calculate from existing CSVs rather than running SQL:

```python
class IMDPercentilesPlotAnalysis(AnalysisBase):
    def __init__(self, processor):
        super().__init__(processor, name="imd_percentiles_plot")

    def get_sql_statement(self) -> str:
        return ""  # No SQL

    def execute(self) -> pl.DataFrame:
        return pl.DataFrame()  # No data saved

    def plot(self) -> plt.Figure:
        # Load data from another analysis
        from pathlib import Path
        histogram_path = Path(self.output_dir) / "imd_histogram.csv"
        df = pl.read_csv(histogram_path)

        # Process and plot
        # ...
        return fig
```

### Using Processor Methods Directly

For complex operations beyond SQL:

```python
def execute(self) -> pl.DataFrame:
    # Override execute() to use processor methods
    patient_filters = self.processor.get_patients_by_filters(
        filter_ids=[5, 6, 10],
        min_duration_days=14,
        start_date_after=datetime(2020, 1, 1)
    )

    # Process results into DataFrame
    rows = []
    for patient_id, filters in patient_filters.items():
        rows.append({
            'patient_id': patient_id,
            'filter_count': len(filters)
        })

    return pl.DataFrame(rows)
```

## Output Structure

```
outputs/statistics/
├── *.csv                           # Analysis results (tracked in git)
└── plots/
    └── *.png                       # Publication plots (tracked in git)
```

Both CSVs and plots are tracked in version control for paper reproducibility.

## Debugging

### View Generated SQL

```python
analysis = MyAnalysis(processor)
sql = analysis.get_sql_statement()
print(sql)
```

### Test SQL Directly

```python
result = processor.conn.execute(sql).df()
print(result)
```

### Load and Inspect Data

```python
analysis = MyAnalysis(processor=None)  # No DB needed
df = analysis.load_df()
print(df)
```

## Key Design Principles

1. **Separation of Concerns**: SQL logic is separate from plotting logic
2. **Reproducibility**: All plots can be regenerated from saved CSVs
3. **Version Control**: Both data and plots tracked for paper reproducibility
4. **No Database for Plots**: Plots work offline from saved data
5. **Consistent Styling**: All plots use the same publication-quality style
6. **Self-Documenting**: Analysis names match their purpose and output files
7. **Reusable Processor**: Pass processor instance rather than recreating

## Important Notes

### IMD Calculations

**IMD_Score is a rank from 1-32,844** (number of LSOAs in England), NOT a 0-100 scale:
- 1 = most deprived LSOA
- 32,844 = least deprived LSOA

To convert to percentile: `(IMD_Score - 1) / 328.44`

To convert to percentage: `IMD_Score / 32844 * 100`

### Date Handling

- Use ISO format `'YYYY-MM-DD'` in SQL
- DuckDB's `DATE` type for date columns
- `DATE_DIFF('unit', start, end)` for date arithmetic

### DuckDB Specifics

- Not all PostgreSQL features available
- Use `APPROX_QUANTILE()` for percentiles
- `DATE_DIFF()` instead of PostgreSQL's `-` operator
- `||` for string concatenation

### Polars vs Pandas

This project uses Polars for data processing:
- Faster than pandas
- More explicit syntax
- Better type handling
- Use `.with_columns()` for transformations
- Use expressions like `pl.col("name")`

## Contributing

When adding new analyses:

1. Create a new file in `src/medguard/analysis/`
2. Inherit from `AnalysisBase`
3. Implement `get_sql_statement()` at minimum
4. Add `plot()` if visualization is needed
5. Export in `__init__.py`
6. Add to `scripts/run_statistics_analyses.py`
7. Add to `scripts/generate_all_plots.py` if plotting
8. Update this README with your analysis category
