"""
HTML Documentation Generator using Jinja2.

Application-layer orchestrator for HTML documentation generation.
Delegates to infrastructure components for rendering and file operations.
"""

import logging
from pathlib import Path
from typing import List, Optional

from src.domain.value_objects import WDLDocument
from src.domain.errors import ParseError
from src.infrastructure.rendering.html_generator import HtmlGenerator
from src.infrastructure.rendering.template_renderer import TemplateRenderer
from src.application.ports import AssetCopierPort

logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """
    Application-layer orchestrator for documentation generation.

    Coordinates rendering infrastructure components to generate complete
    HTML documentation site.
    """

    def __init__(self, output_dir: Path, root_path: Path, asset_copier: AssetCopierPort):
        """
        Initialize the generator.

        Args:
            output_dir: Directory where HTML will be generated
            root_path: Root path of the project (for relative paths)
            asset_copier: Service for copying static assets
        """
        self.output_dir = output_dir
        self.root_path = root_path

        # Initialize infrastructure components
        templates_dir = Path(__file__).parent / "templates"
        self.renderer = TemplateRenderer(templates_dir, root_path)
        self.html_generator = HtmlGenerator(output_dir, self.renderer)
        self.static_assets = asset_copier

    def execute(self, documents: List[WDLDocument], parse_errors: List[ParseError]) -> bool:
        """
        Generate HTML documentation for all WDL documents.
        """
        try:
            for doc in documents:
                self.generate_document_page(doc, documents)

            self.generate_index(documents, parse_errors)
            self.generate_docker_images_page(documents)
            self.copy_static_assets()
            return True
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            return False

    def generate_document_page(self, doc: WDLDocument, all_documents: Optional[List[WDLDocument]] = None) -> Path:
        """
        Generate an HTML page for a single WDL document.

        Args:
            doc: WDLDocument to generate page for
            all_documents: List of all documents for cross-referencing (optional)

        Returns:
            Path to generated HTML file
        """
        return self.html_generator.generate_document_page(doc, all_documents)

    def generate_index(
        self,
        documents: List[WDLDocument],
        parse_errors: Optional[List[ParseError]] = None,
    ) -> Path:
        """
        Generate the main index.html page.

        Args:
            documents: List of all WDLDocument objects
            parse_errors: List of errors encountered during parsing (optional)

        Returns:
            Path to generated index.html
        """
        return self.html_generator.generate_index(documents, parse_errors)

    def generate_docker_images_page(self, documents: List[WDLDocument]) -> Path:
        """
        Generate the Docker images inventory page.

        Args:
            documents: List of all WDLDocument objects

        Returns:
            Path to generated docker_images.html
        """
        return self.html_generator.generate_docker_images_page(documents)

    def copy_static_assets(self) -> None:
        """Copy CSS, JS, and other static assets to output directory."""
        self.static_assets.copy_static_assets(self.output_dir)
