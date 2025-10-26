"""
Application Ports - Protocol Definitions

Defines the interfaces (protocols) for dependencies used by the application layer.
These protocols decouple the application from infrastructure implementations.
"""

from pathlib import Path
from typing import List, Protocol

from src.domain.errors import ParseError
from src.domain.value_objects import WDLDocument


class WdlRepositoryPort(Protocol):
    """Protocol for WDL file repository operations."""

    def find_internal_wdl_files(self) -> List[Path]:
        """
        Find all internal WDL files in the repository.

        Returns:
            List of paths to internal WDL files
        """
        ...

    def get_relative_path(self, wdl_path: Path) -> Path:
        """
        Get the relative path of a WDL file from the repository root.

        Args:
            wdl_path: Absolute path to a WDL file

        Returns:
            Relative path from repository root
        """
        ...

    def is_external(self, wdl_path: Path) -> bool:
        """
        Check if a WDL file is external to the repository.

        Args:
            wdl_path: Path to check

        Returns:
            True if the file is external, False otherwise
        """
        ...


class ParserPort(Protocol):
    """Protocol for WDL parsing operations."""

    def parse_document(self, wdl_path: Path) -> WDLDocument:
        """
        Parse a WDL file into a WDLDocument.

        Args:
            wdl_path: Path to the WDL file to parse

        Returns:
            Parsed WDLDocument

        Raises:
            Exception: If parsing fails
        """
        ...

    def convert_exception_to_error(self, wdl_file: Path, exception: Exception) -> ParseError:
        """
        Convert a parsing exception to a structured ParseError.

        Args:
            wdl_file: Path to the file that failed to parse
            exception: The exception that occurred

        Returns:
            Structured ParseError object
        """
        ...


class DocumentationGeneratorPort(Protocol):
    """Protocol for documentation generation operations."""

    def execute(self, documents: List[WDLDocument], parse_errors: List[ParseError]) -> bool:
        """
        Generate documentation for the given documents.

        Args:
            documents: List of parsed WDL documents
            parse_errors: List of parse errors encountered

        Returns:
            True if generation was successful, False otherwise
        """
        ...


class AssetCopierPort(Protocol):
    """Protocol for static asset copying operations."""

    def copy_static_assets(self, output_dir: Path) -> None:
        """
        Copy static assets to the output directory.

        Args:
            output_dir: Directory where assets should be copied

        Raises:
            FileNotFoundError: If source assets don't exist
        """
        ...
