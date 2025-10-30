"""
HTML Documentation Generator using Jinja2.

Application-layer orchestrator for HTML documentation generation.
Delegates to infrastructure components for rendering and file operations.
"""

import logging
import shutil
from pathlib import Path
from typing import List

from src.domain.value_objects import WDLDocument
from src.domain.errors import ParseError
from src.infrastructure.rendering.html_generator import HtmlGenerator
from src.infrastructure.rendering.template_renderer import TemplateRenderer

logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """
    Application-layer orchestrator for documentation generation.

    Coordinates rendering infrastructure components to generate complete
    HTML documentation site.
    """

    def __init__(self, output_dir: Path, root_path: Path):
        """
        Initialize the generator.

        Args:
            output_dir: Directory where HTML will be generated
            root_path: Root path of the project (for relative paths)
        """
        self.output_dir = output_dir
        self.root_path = root_path

        # Initialize infrastructure components
        self._templates_dir = Path(__file__).parent / "templates"
        self.renderer = TemplateRenderer(self._templates_dir, root_path)
        self.html_generator = HtmlGenerator(output_dir, self.renderer)
        self.static_dir = "static"
        self.source_static_dir = self._templates_dir / self.static_dir

    def execute(self, documents: List[WDLDocument], parse_errors: List[ParseError]) -> bool:
        """
        Generate HTML documentation for all WDL documents.
        """
        try:
            for doc in documents:
                self.html_generator.generate_document_page(doc, documents)

            self.html_generator.generate_index(documents, parse_errors)
            self.html_generator.generate_docker_images_page(documents)
            self.copy_static_assets()
            return True
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            return False

    def copy_static_assets(self) -> None:
        """Copy CSS, JS, and other static assets to output directory."""
        target_static_dir = self.output_dir / self.static_dir

        if self.source_static_dir.exists():
            # Remove target if it exists
            if target_static_dir.exists():
                shutil.rmtree(target_static_dir)

            # Copy entire static directory
            shutil.copytree(self.source_static_dir, target_static_dir)
            logger.info(f"Static assets copied from {self.source_static_dir} to {target_static_dir}")
            return

        raise FileNotFoundError(f"Could not find static directory at {self.source_static_dir}")
