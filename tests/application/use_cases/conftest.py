"""
Pytest fixtures for use cases tests.

Provides mocks and fakes for infrastructure layer components.
"""

import pytest
from pathlib import Path
from typing import List, Optional

from src.domain.value_objects import (
    WDLDocument,
    WDLWorkflow,
    WDLTask,
    WDLInput,
    WDLOutput,
    WDLType,
    WDLCommand,
    WDLImport,
)
from src.domain.errors import ParseError


class FakeWdlRepository:
    """Fake WdlRepository for testing."""

    def __init__(self, internal_files: List[Path], external_files: Optional[List[Path]] = None):
        self.internal_files = internal_files
        self.external_files = external_files or []
        self.root_path = Path("/fake/root")

    def find_internal_wdl_files(self) -> List[Path]:
        """Return configured internal files."""
        return self.internal_files

    def find_external_wdl_files(self) -> List[Path]:
        """Return configured external files."""
        return self.external_files

    def find_all_wdl_files(self) -> List[Path]:
        """Return all files."""
        return self.internal_files + self.external_files

    def get_relative_path(self, wdl_path: Path) -> Path:
        """Return path as-is for fake."""
        try:
            return wdl_path.relative_to(self.root_path)
        except ValueError:
            return wdl_path

    def is_external(self, wdl_path: Path) -> bool:
        """Check if file is in external list."""
        return wdl_path in self.external_files or "external" in str(wdl_path)

    def exists(self, wdl_path: Path) -> bool:
        """Check if path exists in internal or external files."""
        return wdl_path in self.internal_files or wdl_path in self.external_files


class FakeMiniwdlParser:
    """Fake MiniwdlParser for testing."""

    def __init__(self, documents: dict, errors: Optional[dict] = None):
        """
        Initialize fake parser.

        Args:
            documents: Dictionary mapping Path -> WDLDocument
            errors: Dictionary mapping Path -> Exception (for files that should fail)
        """
        self.documents = documents
        self.errors = errors or {}
        self.parse_calls = []

    def parse_document(self, wdl_path: Path) -> WDLDocument:
        """Return pre-configured document or raise error."""
        self.parse_calls.append(wdl_path)

        if wdl_path in self.errors:
            raise self.errors[wdl_path]

        if wdl_path in self.documents:
            return self.documents[wdl_path]

        # Default document if not configured
        return WDLDocument(
            file_path=wdl_path,
            relative_path=wdl_path,
            version="1.0",
            workflow=None,
            tasks=[],
            imports=[],
            source_code="",
        )

    def convert_exception_to_error(self, wdl_file: Path, exception: Exception) -> ParseError:
        """Convert exception to ParseError."""
        return ParseError(
            file_path=wdl_file,
            relative_path=wdl_file,
            error_type=type(exception).__name__,
            error_message=str(exception),
            line_number=None,
            column_number=None,
        )


class FakeHtmlGenerator:
    """Fake HtmlGenerator for testing."""

    def __init__(self):
        self.generated_documents = []
        self.index_generated = False
        self.docker_page_generated = False

    def generate_document_page(self, doc: WDLDocument) -> Path:
        """Record document generation."""
        self.generated_documents.append(doc)
        return Path("/fake/output") / f"{doc.relative_path}.html"

    def generate_index(self, documents: List[WDLDocument], parse_errors: List[ParseError]) -> Path:
        """Record index generation."""
        self.index_generated = True
        return Path("/fake/output/index.html")

    def generate_docker_images_page(self, documents: List[WDLDocument]) -> Path:
        """Record Docker page generation."""
        self.docker_page_generated = True
        return Path("/fake/output/docker_images.html")


class FakeDocumentationGenerator:
    """Fake DocumentationGenerator that implements DocumentationGeneratorPort."""

    def __init__(self):
        self.execute_called = False
        self.documents = []
        self.parse_errors = []
        self.should_fail = False

    def execute(self, documents: List[WDLDocument], parse_errors: List[ParseError]) -> bool:
        """Execute documentation generation."""
        self.execute_called = True
        self.documents = documents
        self.parse_errors = parse_errors

        if self.should_fail:
            return False

        return len(documents) > 0


@pytest.fixture
def fake_repository():
    """Factory fixture to create fake repositories."""

    def _create(internal_files: List[Path], external_files: Optional[List[Path]] = None):
        return FakeWdlRepository(internal_files, external_files)

    return _create


@pytest.fixture
def fake_parser():
    """Factory fixture to create fake parsers."""

    def _create(documents: dict, errors: Optional[dict] = None):
        return FakeMiniwdlParser(documents, errors)

    return _create


@pytest.fixture
def fake_html_generator():
    """Create fake HTML generator."""
    return FakeHtmlGenerator()


@pytest.fixture
def fake_documentation_generator():
    """Factory fixture to create fake documentation generators."""

    def _create(should_fail: bool = False):
        generator = FakeDocumentationGenerator()
        generator.should_fail = should_fail
        return generator

    return _create


@pytest.fixture
def use_case_factory(fake_repository, fake_parser, fake_documentation_generator):
    """Factory fixture to create GenerateDocumentationUseCase with default mocks."""
    from src.application.use_cases.generate_documentation import GenerateDocumentationUseCase

    def _create(
        internal_files: Optional[List[Path]] = None,
        external_files: Optional[List[Path]] = None,
        documents: Optional[dict] = None,
        parse_errors: Optional[dict] = None,
        should_fail_generation: bool = False,
    ):
        """
        Create a use case with mocked dependencies.

        Args:
            internal_files: List of internal WDL files (defaults to empty)
            external_files: List of external WDL files (defaults to empty)
            documents: Dict mapping Path -> WDLDocument for successful parsing
            parse_errors: Dict mapping Path -> Exception for files that fail parsing
            should_fail_generation: Whether documentation generation should fail

        Returns:
            Tuple of (use_case, repository, parser, doc_generator)
        """
        repository = fake_repository(internal_files or [], external_files or [])
        parser = fake_parser(documents or {}, parse_errors or {})
        doc_generator = fake_documentation_generator(should_fail=should_fail_generation)

        use_case = GenerateDocumentationUseCase(repository, parser, doc_generator)

        return use_case, repository, parser, doc_generator

    return _create


@pytest.fixture
def sample_wdl_document(temp_dir):
    """Create a sample WDLDocument for testing."""
    wdl_path = temp_dir / "workflow.wdl"

    return WDLDocument(
        file_path=wdl_path,
        relative_path=Path("workflow.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="TestWorkflow",
            description="A test workflow",
            inputs=[
                WDLInput(
                    name="input_file",
                    type=WDLType(name="File", optional=False),
                    description="Input file",
                    default_value=None,
                )
            ],
            outputs=[
                WDLOutput(
                    name="result",
                    type=WDLType(name="File", optional=False),
                    description="Output file",
                    expression="ProcessTask.output",
                )
            ],
            calls=[],
            docker_images=[],
            mermaid_graph="",
        ),
        tasks=[],
        imports=[],
        source_code="version 1.0\nworkflow TestWorkflow {}",
    )


@pytest.fixture
def sample_wdl_document_with_import(temp_dir):
    """Create a sample WDLDocument with external import for testing."""
    wdl_path = temp_dir / "workflow.wdl"
    external_path = temp_dir / "external" / "lib.wdl"

    return WDLDocument(
        file_path=wdl_path,
        relative_path=Path("workflow.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="TestWorkflow",
            description="A test workflow",
            inputs=[],
            outputs=[],
            calls=[],
            docker_images=[],
            mermaid_graph="",
        ),
        tasks=[],
        imports=[
            WDLImport(
                path="external/lib.wdl",
                namespace="lib",
                resolved_path=external_path,
            )
        ],
        source_code="version 1.0\nimport 'external/lib.wdl' as lib\nworkflow TestWorkflow {}",
    )


@pytest.fixture
def sample_external_document(temp_dir):
    """Create a sample external WDLDocument."""
    external_path = temp_dir / "external" / "lib.wdl"

    return WDLDocument(
        file_path=external_path,
        relative_path=Path("external/lib.wdl"),
        version="1.0",
        workflow=None,
        tasks=[
            WDLTask(
                name="ExternalTask",
                description="External task",
                inputs=[],
                outputs=[],
                command=WDLCommand(raw_command="echo test", formatted_command="echo test"),
                runtime={},
            )
        ],
        imports=[],
        source_code="version 1.0\ntask ExternalTask {}",
    )
