"""
Complexity Variable Correlation Analysis

Analyzes correlations between patient complexity measures (age, QoF count, medication count)
to understand whether observed performance trends are independent or confounded.

Outputs:
- Pairwise correlation matrix between complexity variables
- Multiple regression predicting clinician score from all variables
- Partial correlations (each variable's effect controlling for others)
"""

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from scipy import stats

from medguard.analysis.base import EvaluationAnalysisBase
from medguard.analysis.filters import get_age, get_medication_count, get_qof_count, no_data_error


class ComplexityCorrelationAnalysis(EvaluationAnalysisBase):
    """
    Analyze correlations between complexity variables and their relationship to performance.
    """

    def __init__(self, evaluation, name: str = "complexity_correlation"):
        super().__init__(evaluation, name=name)

    def execute(self) -> pl.DataFrame:
        """
        Execute correlation analysis.

        Returns DataFrame with:
        - Patient-level data (age, medications, qof, clinician_score)
        - Summary statistics and correlations stored in metadata rows
        """
        ids_no_error = self.evaluation.filter_by_clinician_evaluation(no_data_error())
        records = {
            pid: record
            for pid, record in self.evaluation.analysed_records_dict_last.items()
            if pid in ids_no_error
        }

        # Build patient-level dataframe
        rows = []
        for pid, record in records.items():
            age = get_age(record)
            if age is None:
                continue

            clinician_eval = self.evaluation.clinician_evaluations_dict.get(pid)
            if clinician_eval is None:
                continue

            rows.append(
                {
                    "patient_id": pid,
                    "age": age,
                    "medications": get_medication_count(record),
                    "qof": get_qof_count(record),
                    "clinician_score": clinician_eval.score,
                }
            )

        return pl.DataFrame(rows)

    def compute_correlations(self) -> dict:
        """Compute correlation matrix and regression results from saved data."""
        df = self.load_df()

        age = df["age"].to_numpy()
        meds = df["medications"].to_numpy()
        qof = df["qof"].to_numpy()
        score = df["clinician_score"].to_numpy()

        # Pairwise correlations between predictors
        corr_age_meds, p_age_meds = stats.pearsonr(age, meds)
        corr_age_qof, p_age_qof = stats.pearsonr(age, qof)
        corr_meds_qof, p_meds_qof = stats.pearsonr(meds, qof)

        # Correlations with outcome
        corr_age_score, p_age_score = stats.pearsonr(age, score)
        corr_meds_score, p_meds_score = stats.pearsonr(meds, score)
        corr_qof_score, p_qof_score = stats.pearsonr(qof, score)

        # Multiple regression: score ~ age + medications + qof
        X = np.column_stack([np.ones(len(age)), age, meds, qof])
        y = score
        # OLS: beta = (X'X)^-1 X'y
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        y_pred = X @ beta
        residuals = y - y_pred
        n, p = X.shape
        mse = np.sum(residuals**2) / (n - p)
        var_beta = mse * np.linalg.inv(X.T @ X)
        se_beta = np.sqrt(np.diag(var_beta))
        t_stats = beta / se_beta
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), n - p))

        # R-squared
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - ss_res / ss_tot

        # Standardized coefficients (beta * sd_x / sd_y)
        sd_x = np.array([1, np.std(age), np.std(meds), np.std(qof)])
        sd_y = np.std(score)
        std_beta = beta * sd_x / sd_y

        # Partial correlations (correlation of each variable with outcome, controlling for others)
        def partial_corr(x, y, controls):
            """Partial correlation between x and y, controlling for controls."""
            # Regress x on controls, get residuals
            C = np.column_stack([np.ones(len(x))] + [c for c in controls])
            x_resid = x - C @ np.linalg.lstsq(C, x, rcond=None)[0]
            y_resid = y - C @ np.linalg.lstsq(C, y, rcond=None)[0]
            return stats.pearsonr(x_resid, y_resid)

        partial_age, p_partial_age = partial_corr(age, score, [meds, qof])
        partial_meds, p_partial_meds = partial_corr(meds, score, [age, qof])
        partial_qof, p_partial_qof = partial_corr(qof, score, [age, meds])

        # VIF (Variance Inflation Factor)
        def vif(x, others):
            X_others = np.column_stack([np.ones(len(x))] + others)
            x_pred = X_others @ np.linalg.lstsq(X_others, x, rcond=None)[0]
            ss_res = np.sum((x - x_pred) ** 2)
            ss_tot = np.sum((x - np.mean(x)) ** 2)
            r2 = 1 - ss_res / ss_tot
            return 1 / (1 - r2) if r2 < 1 else float("inf")

        vif_age = vif(age, [meds, qof])
        vif_meds = vif(meds, [age, qof])
        vif_qof = vif(qof, [age, meds])

        return {
            "n_patients": len(df),
            "correlations": {
                "age_meds": {"r": corr_age_meds, "p": p_age_meds},
                "age_qof": {"r": corr_age_qof, "p": p_age_qof},
                "meds_qof": {"r": corr_meds_qof, "p": p_meds_qof},
                "age_score": {"r": corr_age_score, "p": p_age_score},
                "meds_score": {"r": corr_meds_score, "p": p_meds_score},
                "qof_score": {"r": corr_qof_score, "p": p_qof_score},
            },
            "regression": {
                "r_squared": r_squared,
                "coefficients": {
                    "intercept": {
                        "b": beta[0],
                        "se": se_beta[0],
                        "t": t_stats[0],
                        "p": p_values[0],
                    },
                    "age": {
                        "b": beta[1],
                        "se": se_beta[1],
                        "t": t_stats[1],
                        "p": p_values[1],
                        "std_b": std_beta[1],
                    },
                    "medications": {
                        "b": beta[2],
                        "se": se_beta[2],
                        "t": t_stats[2],
                        "p": p_values[2],
                        "std_b": std_beta[2],
                    },
                    "qof": {
                        "b": beta[3],
                        "se": se_beta[3],
                        "t": t_stats[3],
                        "p": p_values[3],
                        "std_b": std_beta[3],
                    },
                },
            },
            "partial_correlations": {
                "age": {"r": partial_age, "p": p_partial_age},
                "medications": {"r": partial_meds, "p": p_partial_meds},
                "qof": {"r": partial_qof, "p": p_partial_qof},
            },
            "vif": {
                "age": vif_age,
                "medications": vif_meds,
                "qof": vif_qof,
            },
        }

    def plot(self) -> list[tuple[plt.Figure, str]]:
        """Create correlation visualizations."""
        df = self.load_df()
        results = self.compute_correlations()

        figures = []

        # Figure 1: Correlation matrix heatmap
        fig_corr = self._plot_correlation_matrix(df, results)
        figures.append((fig_corr, "_correlation_matrix"))

        # Figure 2: Scatter plot matrix
        fig_scatter = self._plot_scatter_matrix(df)
        figures.append((fig_scatter, "_scatter_matrix"))

        # Figure 3: Regression coefficients
        fig_reg = self._plot_regression_coefficients(results)
        figures.append((fig_reg, "_regression"))

        return figures

    def _plot_correlation_matrix(self, df: pl.DataFrame, results: dict) -> plt.Figure:
        """Create correlation matrix heatmap with MedGuard styling (lower triangle only)."""
        from matplotlib.colors import LinearSegmentedColormap

        # MedGuard color palette
        COLORS = {
            "correct": "#2D7D90",
            "true_negative": "#7CB4B8",
            "false_negative": "#C44D56",
            "failure_level_2": "#E07B4C",
            "neutral_light": "#E8E8E8",
            "neutral_dark": "#4A4A4A",
        }

        # MedGuard style settings
        plt.rcParams.update(
            {
                "font.family": "sans-serif",
                "font.sans-serif": ["Source Sans Pro", "Arial", "Helvetica"],
                "font.size": 8,
                "axes.titlesize": 10,
                "axes.labelsize": 9,
                "axes.spines.top": False,
                "axes.spines.right": False,
                "axes.linewidth": 0.8,
                "axes.edgecolor": COLORS["neutral_dark"],
                "figure.facecolor": "white",
                "axes.facecolor": "white",
            }
        )

        fig, ax = plt.subplots(figsize=(5, 3.75))

        # Build 4x4 correlation matrix (age, meds, qof, score)
        variables = ["Age", "Medications", "QoF", "Clinician\nScore"]
        corr = results["correlations"]
        matrix = np.array(
            [
                [1.0, corr["age_meds"]["r"], corr["age_qof"]["r"], corr["age_score"]["r"]],
                [corr["age_meds"]["r"], 1.0, corr["meds_qof"]["r"], corr["meds_score"]["r"]],
                [corr["age_qof"]["r"], corr["meds_qof"]["r"], 1.0, corr["qof_score"]["r"]],
                [corr["age_score"]["r"], corr["meds_score"]["r"], corr["qof_score"]["r"], 1.0],
            ]
        )

        # Mask upper triangle (k=1 excludes diagonal, so diagonal is shown)
        mask = np.triu(np.ones_like(matrix, dtype=bool), k=1)
        masked_matrix = np.ma.masked_where(mask, matrix)

        # Create MedGuard diverging colormap: coral (negative) -> neutral -> teal (positive)
        medguard_cmap = LinearSegmentedColormap.from_list(
            "medguard_diverging",
            [COLORS["false_negative"], COLORS["neutral_light"], COLORS["correct"]],
            N=256,
        )

        im = ax.imshow(masked_matrix, cmap=medguard_cmap, vmin=-1, vmax=1)

        # Add cell borders only for lower triangle (including diagonal)
        for i in range(4):
            for j in range(4):
                if j <= i:
                    rect = plt.Rectangle(
                        (j - 0.5, i - 0.5),
                        1,
                        1,
                        fill=False,
                        edgecolor=COLORS["neutral_dark"],
                        linewidth=0.8,
                    )
                    ax.add_patch(rect)

        ax.set_xticks(range(4))
        ax.set_yticks(range(4))
        ax.set_xticklabels(variables, fontsize=9, fontweight="medium")
        ax.set_yticklabels(variables, fontsize=9, fontweight="medium")

        # Add correlation values only for lower triangle (including diagonal)
        for i in range(4):
            for j in range(4):
                if j <= i:
                    # Use white text on dark backgrounds, dark text on light backgrounds
                    color = "white" if abs(matrix[i, j]) > 0.5 else COLORS["neutral_dark"]
                    ax.text(
                        j,
                        i,
                        f"{matrix[i, j]:.2f}",
                        ha="center",
                        va="center",
                        color=color,
                        fontsize=10,
                        fontweight="semibold",
                    )

        # Colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label("Pearson r", fontsize=9, fontweight="medium")
        cbar.ax.tick_params(labelsize=8)
        cbar.outline.set_linewidth(0.8)
        cbar.outline.set_edgecolor(COLORS["neutral_dark"])

        ax.set_title(
            "Correlation Matrix: Patient Complexity Variables",
            fontsize=10,
            fontweight="semibold",
            pad=15,
        )

        # Remove top/right spines (already set via rcParams, but ensure for this axes)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        plt.tight_layout()
        return fig

    def _plot_scatter_matrix(self, df: pl.DataFrame) -> plt.Figure:
        """Create scatter plot matrix."""
        fig, axes = plt.subplots(3, 3, figsize=(12, 12))

        variables = [
            ("age", "Age"),
            ("medications", "Medications"),
            ("qof", "QoF Count"),
        ]

        for i, (var_i, label_i) in enumerate(variables):
            for j, (var_j, label_j) in enumerate(variables):
                ax = axes[i, j]
                x = df[var_j].to_numpy()
                y = df[var_i].to_numpy()

                if i == j:
                    # Diagonal: histogram
                    ax.hist(x, bins=20, color="#3498db", alpha=0.7, edgecolor="black")
                    ax.set_ylabel("Count")
                else:
                    # Off-diagonal: scatter
                    ax.scatter(x, y, alpha=0.4, s=20, color="#3498db")
                    # Add regression line
                    z = np.polyfit(x, y, 1)
                    p = np.poly1d(z)
                    x_line = np.linspace(x.min(), x.max(), 100)
                    ax.plot(x_line, p(x_line), "r-", linewidth=2)
                    # Add correlation
                    r, _ = stats.pearsonr(x, y)
                    ax.text(
                        0.05,
                        0.95,
                        f"r={r:.2f}",
                        transform=ax.transAxes,
                        fontsize=10,
                        fontweight="bold",
                        va="top",
                    )

                if i == 2:
                    ax.set_xlabel(label_j, fontweight="bold")
                if j == 0:
                    ax.set_ylabel(label_i, fontweight="bold")

        plt.suptitle("Complexity Variables: Pairwise Relationships", fontweight="bold", y=1.02)
        plt.tight_layout()
        return fig

    def _plot_regression_coefficients(self, results: dict) -> plt.Figure:
        """Plot standardized regression coefficients with confidence intervals."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        reg = results["regression"]["coefficients"]
        partial = results["partial_correlations"]

        variables = ["Age", "Medications", "QoF"]
        keys = ["age", "medications", "qof"]

        # Left: Standardized regression coefficients
        std_betas = [reg[k]["std_b"] for k in keys]
        # 95% CI for standardized beta (approximate)
        errors = [
            1.96 * reg[k]["se"] * np.std([1, 1, 1][i]) for i, k in enumerate(keys)
        ]  # simplified

        colors = ["#e74c3c" if reg[k]["p"] < 0.05 else "#95a5a6" for k in keys]
        y_pos = range(len(variables))

        ax1.barh(y_pos, std_betas, color=colors, edgecolor="black", height=0.6)
        ax1.axvline(x=0, color="black", linestyle="-", linewidth=1)
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(variables)
        ax1.set_xlabel("Standardized Coefficient (β)", fontweight="bold")
        ax1.set_title(
            f"Multiple Regression (R² = {results['regression']['r_squared']:.3f})",
            fontweight="bold",
        )

        # Add p-values
        for i, k in enumerate(keys):
            p = reg[k]["p"]
            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
            ax1.text(std_betas[i] + 0.01, i, f"p={p:.3f}{sig}", va="center", fontsize=10)

        ax1.grid(axis="x", alpha=0.3, linestyle="--")

        # Right: Partial correlations
        partial_rs = [partial[k]["r"] for k in keys]
        colors2 = ["#27ae60" if partial[k]["p"] < 0.05 else "#95a5a6" for k in keys]

        ax2.barh(y_pos, partial_rs, color=colors2, edgecolor="black", height=0.6)
        ax2.axvline(x=0, color="black", linestyle="-", linewidth=1)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(variables)
        ax2.set_xlabel("Partial Correlation (r)", fontweight="bold")
        ax2.set_title("Partial Correlations\n(controlling for other variables)", fontweight="bold")

        for i, k in enumerate(keys):
            p = partial[k]["p"]
            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
            ax2.text(partial_rs[i] + 0.01, i, f"p={p:.3f}{sig}", va="center", fontsize=10)

        ax2.grid(axis="x", alpha=0.3, linestyle="--")

        plt.tight_layout()
        return fig

    def summary_text(self) -> str:
        """Generate text summary of correlation analysis."""
        results = self.compute_correlations()
        corr = results["correlations"]
        reg = results["regression"]
        partial = results["partial_correlations"]
        vif = results["vif"]

        lines = [
            "=" * 60,
            "COMPLEXITY VARIABLE CORRELATION ANALYSIS",
            "=" * 60,
            f"\nN = {results['n_patients']} patients\n",
            "-" * 40,
            "PAIRWISE CORRELATIONS (between predictors)",
            "-" * 40,
            f"  Age ↔ Medications:  r = {corr['age_meds']['r']:+.3f}  (p = {corr['age_meds']['p']:.4f})",
            f"  Age ↔ QoF:          r = {corr['age_qof']['r']:+.3f}  (p = {corr['age_qof']['p']:.4f})",
            f"  Medications ↔ QoF:  r = {corr['meds_qof']['r']:+.3f}  (p = {corr['meds_qof']['p']:.4f})",
            "",
            "-" * 40,
            "BIVARIATE CORRELATIONS (with clinician score)",
            "-" * 40,
            f"  Age → Score:         r = {corr['age_score']['r']:+.3f}  (p = {corr['age_score']['p']:.4f})",
            f"  Medications → Score: r = {corr['meds_score']['r']:+.3f}  (p = {corr['meds_score']['p']:.4f})",
            f"  QoF → Score:         r = {corr['qof_score']['r']:+.3f}  (p = {corr['qof_score']['p']:.4f})",
            "",
            "-" * 40,
            "MULTIPLE REGRESSION: Score ~ Age + Medications + QoF",
            "-" * 40,
            f"  R² = {reg['r_squared']:.4f}",
            "",
            "  Coefficients (standardized β shows relative importance):",
            f"    Age:         b = {reg['coefficients']['age']['b']:+.5f}, β = {reg['coefficients']['age']['std_b']:+.3f}, p = {reg['coefficients']['age']['p']:.4f}",
            f"    Medications: b = {reg['coefficients']['medications']['b']:+.5f}, β = {reg['coefficients']['medications']['std_b']:+.3f}, p = {reg['coefficients']['medications']['p']:.4f}",
            f"    QoF:         b = {reg['coefficients']['qof']['b']:+.5f}, β = {reg['coefficients']['qof']['std_b']:+.3f}, p = {reg['coefficients']['qof']['p']:.4f}",
            "",
            "-" * 40,
            "PARTIAL CORRELATIONS (controlling for other variables)",
            "-" * 40,
            f"  Age | (Meds, QoF):         r = {partial['age']['r']:+.3f}  (p = {partial['age']['p']:.4f})",
            f"  Medications | (Age, QoF):  r = {partial['medications']['r']:+.3f}  (p = {partial['medications']['p']:.4f})",
            f"  QoF | (Age, Meds):         r = {partial['qof']['r']:+.3f}  (p = {partial['qof']['p']:.4f})",
            "",
            "-" * 40,
            "VARIANCE INFLATION FACTORS (VIF > 5 suggests multicollinearity)",
            "-" * 40,
            f"  Age:         VIF = {vif['age']:.2f}",
            f"  Medications: VIF = {vif['medications']:.2f}",
            f"  QoF:         VIF = {vif['qof']:.2f}",
            "",
            "=" * 60,
            "INTERPRETATION",
            "=" * 60,
        ]

        # Add interpretation
        high_corr = []
        for name, r in [
            ("Age-Meds", corr["age_meds"]["r"]),
            ("Age-QoF", corr["age_qof"]["r"]),
            ("Meds-QoF", corr["meds_qof"]["r"]),
        ]:
            if abs(r) > 0.3:
                high_corr.append(f"{name} (r={r:.2f})")

        if high_corr:
            lines.append(f"  Correlated predictors: {', '.join(high_corr)}")
        else:
            lines.append("  Predictors show low intercorrelation (all |r| < 0.3)")

        # Which variables have independent effects?
        sig_vars = []
        for k in ["age", "medications", "qof"]:
            if partial[k]["p"] < 0.05:
                sig_vars.append(k.capitalize())

        if sig_vars:
            lines.append(f"  Independent effects: {', '.join(sig_vars)} (p < 0.05 in partial corr)")
        else:
            lines.append("  No variables show significant independent effects")

        lines.append("")
        return "\n".join(lines)

    def save_figure_to_pdf(self, fig: plt.Figure, suffix: str = "") -> "Path":
        """Save matplotlib figure to PDF file."""
        from pathlib import Path

        filename = f"{self.name}{suffix}.pdf" if suffix else f"{self.name}.pdf"
        output_path = self.plots_dir / filename
        fig.savefig(output_path, format="pdf", bbox_inches="tight")
        plt.close(fig)
        return output_path

    def run_figure_pdf(self) -> list:
        """Generate plot(s) and save to PDF."""
        result = self.plot()
        if result is None:
            return []

        paths = []
        for item in result:
            if isinstance(item, tuple) and len(item) == 2:
                fig, fig_suffix = item
                paths.append(self.save_figure_to_pdf(fig, suffix=fig_suffix))
        return paths


if __name__ == "__main__":
    from medguard.evaluation.evaluation import Evaluation, merge_evaluations
    from medguard.utils.parsing import load_pydantic_from_json

    print("Loading 300-patient cohort (200 + 100 merged)...")
    evaluation_200 = load_pydantic_from_json(
        Evaluation, "outputs/20251018/test-set/evaluation.json"
    )
    evaluation_100 = load_pydantic_from_json(
        Evaluation, "outputs/20251027/no-filters/evaluation.json"
    )
    print(f"  - Loaded {len(evaluation_200.patient_ids())} from test-set")
    print(f"  - Loaded {len(evaluation_100.patient_ids())} from no-filters")

    evaluation = merge_evaluations([evaluation_100, evaluation_200])
    print(f"  - Merged: {len(evaluation.patient_ids())} patients total")

    evaluation = evaluation.clean()
    print(f"  - After clean(): {len(evaluation.patient_ids())} evaluable patients")

    print("\nRunning analysis...")
    analysis = ComplexityCorrelationAnalysis(evaluation)
    df, csv_path = analysis.run()
    print(f"Saved CSV to: {csv_path}")

    print("\n" + analysis.summary_text())

    print("\nGenerating PNG plots...")
    fig_paths = analysis.run_figure()
    for path in fig_paths:
        print(f"  Saved: {path}")

    print("\nGenerating PDF plots...")
    pdf_paths = analysis.run_figure_pdf()
    for path in pdf_paths:
        print(f"  Saved: {path}")

    print("\n✓ Analysis complete!")
