"""
Generate Documentation Use Case - Application Layer

Orchestrates the complete documentation generation workflow:
1. Discovers WDL files
2. Parses them (including external dependencies)
3. Generates HTML documentation
"""

import logging
from pathlib import Path
from typing import List

from src.application.ports import (
    DocumentationGeneratorPort,
    ParserPort,
    WdlRepositoryPort,
)

logger = logging.getLogger(__name__)


class GenerateDocumentationUseCase:
    """
    Complete documentation generation workflow.

    Coordinates document discovery, parsing, and HTML generation
    using infrastructure services.
    """

    def __init__(
        self,
        repository: WdlRepositoryPort,
        parser: ParserPort,
        documentation_generator: DocumentationGeneratorPort,
    ):
        """
        Initialize the use case with injected dependencies.

        Args:
            repository: WDL file repository for discovering files
            parser: WDL parser for parsing documents
            documentation_generator: Documentation generator for creating HTML
        """
        self.repository = repository
        self.parser = parser
        self._documentation_generator = documentation_generator

    def execute(self) -> bool:
        """
        Execute the complete documentation generation workflow.

        Returns:
            True if documentation was generated successfully, False otherwise
        """
        logger.info("Starting documentation generation...")

        # Step 1: Discover WDL files using repository
        wdl_files = self._discover_files()
        if not wdl_files:
            logger.warning("No WDL files found!")
            return False

        # Step 2: Parse WDL files using parser
        documents, parse_errors = self._parse_files(wdl_files)
        if not documents:
            logger.warning("No WDL files could be parsed!")
            return False

        # Step 3: Generate HTML documentation using rendering infrastructure
        success = self._documentation_generator.execute(documents, parse_errors)

        if success:
            logger.info("✓ Documentation generation complete!")

        return success

    def _discover_files(self) -> List[Path]:
        """
        Discover WDL files using repository.

        Returns:
            List of WDL file paths
        """
        logger.info("Discovering WDL files...")

        # Use repository to find internal files
        wdl_files = self.repository.find_internal_wdl_files()

        logger.info(f"Found {len(wdl_files)} WDL files")
        return wdl_files

    def _parse_files(self, wdl_files: List[Path]) -> tuple:
        """
        Parse WDL files and discover external dependencies.

        Args:
            wdl_files: List of WDL files to parse

        Returns:
            Tuple of (documents, parse_errors)
        """
        logger.info(f"Parsing {len(wdl_files)} internal WDL files...")

        documents = []
        parse_errors = []
        parsed_paths = set()

        # Parse internal files
        for wdl_file in wdl_files:
            doc, error = self._parse_single_file(wdl_file, "internal")
            if doc:
                documents.append(doc)
                parsed_paths.add(doc.file_path)
            if error:
                parse_errors.append(error)

        logger.info(f"Parsed {len(documents)} internal WDL files")
        if parse_errors:
            logger.warning(f"Encountered {len(parse_errors)} errors during parsing")

        # Discover and parse external dependencies
        external_count = self._parse_external_dependencies(documents, parsed_paths, parse_errors)

        logger.info(
            f"Total: {len(documents)} files ({len(documents) - external_count} internal + {external_count} external)"
        )

        return documents, parse_errors

    def _parse_single_file(self, wdl_file: Path, file_type: str = "internal") -> tuple:
        """
        Parse a single WDL file with error handling.

        Args:
            wdl_file: Path to the WDL file
            file_type: Type of file for logging

        Returns:
            Tuple of (WDLDocument or None, ParseError or None)
        """
        try:
            rel_path = self.repository.get_relative_path(wdl_file)
            logger.info(f"Parsing {file_type}: {rel_path}")

            doc = self.parser.parse_document(wdl_file)
            return doc, None

        except Exception as e:
            logger.error(f"Error parsing {wdl_file}: {e}")
            error = self.parser.convert_exception_to_error(wdl_file, e)
            return None, error

    def _parse_external_dependencies(self, documents, parsed_paths, parse_errors) -> int:
        """
        Discover and parse external dependencies transitively.

        Args:
            documents: List to append parsed documents to
            parsed_paths: Set of already parsed paths
            parse_errors: List to append errors to

        Returns:
            Number of external files parsed
        """
        logger.info("Discovering external dependencies...")
        external_files_to_parse = []
        initial_count = len(documents)

        # Collect external imports from internal files
        for doc in documents:
            self._collect_external_imports(doc, parsed_paths, external_files_to_parse)

        # Parse external files and their transitive imports
        while external_files_to_parse:
            external_file = external_files_to_parse.pop(0)
            doc, error = self._parse_single_file(external_file, "external")

            if doc:
                documents.append(doc)
                self._collect_external_imports(doc, parsed_paths, external_files_to_parse)

            if error:
                parse_errors.append(error)

        return len(documents) - initial_count

    def _collect_external_imports(self, doc, parsed_paths: set, external_files: List[Path]) -> None:
        """
        Collect external imports from a document.

        Args:
            doc: Document to collect imports from
            parsed_paths: Set of already parsed paths
            external_files: List to append discovered external files to
        """
        if not doc.has_imports:
            return

        for imp in doc.imports:
            if not imp.resolved_path or imp.resolved_path in parsed_paths:
                continue

            normalized_path = imp.resolved_path.resolve()
            if normalized_path in parsed_paths:
                continue

            # Use repository to check if external
            if self.repository.is_external(normalized_path):
                external_files.append(normalized_path)
                parsed_paths.add(normalized_path)
