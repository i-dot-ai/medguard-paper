"""
Simple SQL template loader for the MedGuard preprocessing pipeline.
Loads SQL templates from files and supports variable injection.
"""

from pathlib import Path
from typing import Any, Dict


class SQLTemplateLoader:
    """Load SQL templates from files and inject variables."""

    def __init__(self, base_path: Path = None):
        """
        Initialize the SQL template loader.

        Args:
            base_path: Base directory containing SQL files.
                      Defaults to src/medguard/sql relative to this file.
        """
        if base_path is None:
            base_path = Path(__file__).parent / "sql"
        self.base_path = Path(base_path)

    def load_template(self, template_path: str) -> str:
        """
        Load a SQL template from a file.

        Args:
            template_path: Path to the template file relative to base_path
                          (e.g., "views/gp_events_enriched.sql")

        Returns:
            The SQL template as a string
        """
        full_path = self.base_path / template_path
        with open(full_path, "r") as f:
            return f.read()

    def render_template(self, template_path: str, variables: Dict[str, Any]) -> str:
        """
        Load a SQL template and inject variables.

        Args:
            template_path: Path to the template file relative to base_path
            variables: Dictionary of variables to inject into the template

        Returns:
            The rendered SQL query with variables injected
        """
        template = self.load_template(template_path)
        return template.format(**variables)
