"""
MiniwdlParser - Facade for all WDL parsing operations.

This module provides a complete facade for parsing WDL files using miniwdl,
isolating all miniwdl-specific code and returning pure domain objects.
"""

from pathlib import Path
import WDL

from src.domain.value_objects import (
    WDLDocument,
)
from src.domain.errors import ParseError
from src.infrastructure.parsing.loader import Loader
from src.infrastructure.parsing.ast_mapper import AstMapper
from src.infrastructure.parsing.analyzer import Analyzer
from src.infrastructure.parsing.path_resolver import PathResolver


class MiniwdlParser:
    """
    Facade for parsing WDL files and converting to domain objects.

    This class isolates all miniwdl-specific operations and provides
    a clean interface that returns only domain objects.
    """

    def __init__(self, base_path: Path, output_dir: Path):
        """
        Initialize the parser with base directories.

        Args:
            base_path: Root directory of WDL files
            output_dir: Directory for generated documentation
        """
        self.base_path = base_path
        self.output_dir = output_dir
        self.loader = Loader()
        self.ast_mapper = AstMapper(base_path, output_dir)
        self.analyzer = Analyzer(base_path)

    def parse_document(self, wdl_path: Path) -> WDLDocument:
        """
        Parse a WDL file and return a complete WDLDocument.

        Args:
            wdl_path: Path to the WDL file

        Returns:
            WDLDocument with all parsed information
        """
        # Load the WDL document
        doc, source_code = self.loader.load_with_source(wdl_path)

        # Parse basic document info
        version = self.loader.extract_version(doc)
        relative_path = self._calculate_relative_path(wdl_path)

        # Parse imports
        imports = self.ast_mapper.map_imports(doc, wdl_path)

        # Parse workflow if exists
        workflow = None
        if doc.workflow:
            workflow = self.ast_mapper.map_workflow(doc.workflow, imports, wdl_path)

        # Parse tasks
        tasks = [self.ast_mapper.map_task(task) for task in doc.tasks]

        return WDLDocument(
            file_path=wdl_path,
            relative_path=relative_path,
            version=version,
            workflow=workflow,
            tasks=tasks,
            imports=imports,
            source_code=source_code,
        )

    def _calculate_relative_path(self, wdl_path: Path) -> Path:
        """Calculate relative path from base path."""
        return PathResolver.calculate_relative_path(wdl_path, self.base_path)

    def convert_exception_to_error(self, wdl_file: Path, exception: Exception) -> ParseError:
        """
        Convert a parsing exception to a domain ParseError.

        This method isolates WDL-specific exception handling from the application layer.

        Args:
            wdl_file: Path to the file that failed
            exception: The exception that occurred

        Returns:
            ParseError domain object
        """
        # Extract error type
        error_type = type(exception).__name__
        if isinstance(exception, WDL.Error.SyntaxError):
            error_type = "SyntaxError"
        elif isinstance(exception, WDL.Error.ImportError):
            error_type = "ImportError"
        elif isinstance(exception, WDL.Error.ValidationError):
            error_type = "ValidationError"

        # Extract line and column from WDL exceptions
        line_num = None
        col_num = None

        if isinstance(exception, (WDL.Error.SyntaxError, WDL.Error.ImportError, WDL.Error.ValidationError)):
            if hasattr(exception, "pos") and exception.pos:
                line_num = getattr(exception.pos, "line", None)
                col_num = getattr(exception.pos, "column", None)

        # Calculate relative path
        relative_path = PathResolver.calculate_relative_path(wdl_file, self.base_path)

        return ParseError(
            file_path=wdl_file,
            relative_path=relative_path,
            error_type=error_type,
            error_message=str(exception),
            line_number=line_num,
            column_number=col_num,
        )
