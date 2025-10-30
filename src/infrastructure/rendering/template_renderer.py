"""
Template Renderer - Infrastructure Layer

Handles Jinja2 template rendering and configuration.
Encapsulates all template-related operations.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """
    Jinja2 template renderer.

    Configures and manages Jinja2 environment for rendering HTML templates.
    """

    def __init__(self, templates_dir: Path, root_path: Path):
        """
        Initialize the renderer.

        Args:
            templates_dir: Directory containing Jinja2 templates
            root_path: Project root path for relative path calculations
        """
        self.templates_dir = templates_dir
        self.root_path = root_path

        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters
        self._register_filters()

        logger.debug(f"Initialized TemplateRenderer with templates from {templates_dir}")

    def _register_filters(self) -> None:
        """Register custom Jinja2 filters."""
        self.env.filters["basename"] = lambda p: Path(p).name
        self.env.filters["parent"] = lambda p: Path(p).parent
        self.env.filters["relpath"] = self._relpath_filter
        self.env.filters["normalize_path"] = lambda p: str(self._normalize_path(Path(p)))
        self.env.filters["safe_code"] = lambda s: Markup(s) if s else ""
        self.env.filters["relative_link"] = self._relative_link_filter

    def _relative_link_filter(self, target_path: str, from_path: str) -> str:
        """
        Calculate relative link from one document to another.

        Args:
            target_path: Target document path (e.g., "subworkflows/v1/bam_processing.html")
            from_path: Current document path (e.g., "workflows/v1/illumina/ngs/exome/SingleSampleGenotyping.wdl")

        Returns:
            Relative link (e.g., "../../../../../subworkflows/v1/bam_processing.html")
        """
        # Normalize paths
        target = self._normalize_path(Path(target_path))
        current = self._normalize_path(Path(from_path))

        # Ensure target has .html extension
        if target.suffix == ".wdl":
            target = target.with_suffix(".html")

        # Calculate how many levels up we need to go
        # Filter out '.' from parts to handle root-level files correctly
        parent_parts = [p for p in current.parent.parts if p != "."]
        current_depth = len(parent_parts)

        # Build relative path
        if current_depth > 0:
            up_levels = "../" * current_depth
            relative = up_levels + str(target)
        else:
            relative = str(target)

        return relative

    def _normalize_path(self, path: Path) -> Path:
        """
        Normalize a path by resolving .. references.

        For external files, ensures they start with 'external/'.

        Args:
            path: Path to normalize

        Returns:
            Normalized path
        """
        parts = list(path.parts)

        # If path contains 'external', normalize from 'external' onwards
        if "external" in parts:
            external_idx = parts.index("external")
            return Path(*parts[external_idx:])

        # Otherwise, resolve .. manually
        normalized_parts = []
        for part in parts:
            if part == "..":
                if normalized_parts:
                    normalized_parts.pop()
            elif part != ".":
                normalized_parts.append(part)

        return Path(*normalized_parts) if normalized_parts else path

    def _relpath_filter(self, path: Path, start: Optional[Path] = None) -> str:
        """
        Jinja2 filter to get relative path.

        Args:
            path: Path to make relative
            start: Starting path (defaults to root_path)

        Returns:
            Relative path as string
        """
        if start is None:
            start = self.root_path
        try:
            return str(Path(path).relative_to(start))
        except ValueError:
            return str(path)

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with given context.

        Args:
            template_name: Name of the template file
            context: Context dictionary for template rendering

        Returns:
            Rendered HTML string
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}", exc_info=True)
            raise

    def get_template(self, template_name: str):
        """
        Get a Jinja2 template by name.

        Args:
            template_name: Name of the template file

        Returns:
            Jinja2 Template object
        """
        return self.env.get_template(template_name)
