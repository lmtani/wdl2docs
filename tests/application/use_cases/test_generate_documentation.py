"""
Unit tests for GenerateDocumentationUseCase.

Tests the complete documentation generation workflow including:
- File discovery
- Parsing (internal and external)
- Documentation generation
- Error handling
"""

from pathlib import Path

from src.domain.value_objects import WDLDocument, WDLImport


def test_should_discover_and_parse_internal_files_successfully(temp_dir, use_case_factory, sample_wdl_document):
    """Test successful discovery and parsing of internal WDL files."""
    # Arrange
    wdl_file = temp_dir / "workflow.wdl"
    use_case, _, parser, doc_generator = use_case_factory(
        internal_files=[wdl_file], documents={wdl_file: sample_wdl_document}
    )

    # Act
    result = use_case.execute()

    # Assert
    assert result is True
    assert len(parser.parse_calls) == 1
    assert wdl_file in parser.parse_calls
    assert doc_generator.execute_called
    assert len(doc_generator.documents) == 1


def test_should_return_false_when_no_files_found(use_case_factory):
    """Test behavior when no WDL files are found."""
    # Arrange
    use_case, _, _, _ = use_case_factory()

    # Act
    result = use_case.execute()

    # Assert
    assert result is False


def test_should_return_false_when_all_files_fail_to_parse(temp_dir, use_case_factory):
    """Test behavior when all files fail to parse."""
    # Arrange
    wdl_file = temp_dir / "broken.wdl"
    use_case, _, parser, _ = use_case_factory(
        internal_files=[wdl_file], parse_errors={wdl_file: Exception("Parse error")}
    )

    # Act
    result = use_case.execute()

    # Assert
    assert result is False
    assert len(parser.parse_calls) == 1


def test_should_continue_parsing_when_some_files_fail(temp_dir, use_case_factory, sample_wdl_document):
    """Test that parsing continues when some files fail."""
    # Arrange
    good_file = temp_dir / "good.wdl"
    bad_file = temp_dir / "bad.wdl"
    use_case, _, parser, doc_generator = use_case_factory(
        internal_files=[good_file, bad_file],
        documents={good_file: sample_wdl_document},
        parse_errors={bad_file: Exception("Parse error")},
    )

    # Act
    result = use_case.execute()

    # Assert
    assert result is True
    assert len(parser.parse_calls) == 2
    assert len(doc_generator.documents) == 1


def test_should_discover_and_parse_external_dependencies(
    temp_dir,
    use_case_factory,
    sample_wdl_document_with_import,
    sample_external_document,
):
    """Test discovery and parsing of external dependencies."""
    # Arrange
    internal_file = temp_dir / "workflow.wdl"
    external_file = temp_dir / "external" / "lib.wdl"
    use_case, _, parser, doc_generator = use_case_factory(
        internal_files=[internal_file],
        external_files=[external_file],
        documents={
            internal_file: sample_wdl_document_with_import,
            external_file: sample_external_document,
        },
    )

    # Act
    result = use_case.execute()

    # Assert
    assert result is True
    assert len(parser.parse_calls) == 2  # internal + external
    assert internal_file in parser.parse_calls
    assert external_file in parser.parse_calls
    assert len(doc_generator.documents) == 2


def test_should_not_parse_same_external_file_twice(temp_dir, use_case_factory):
    """Test that external files are only parsed once even if imported multiple times."""
    # Arrange
    internal_file1 = temp_dir / "workflow1.wdl"
    internal_file2 = temp_dir / "workflow2.wdl"
    external_file = temp_dir / "external" / "lib.wdl"

    # Both internal files import the same external file
    doc1 = WDLDocument(
        file_path=internal_file1,
        relative_path=Path("workflow1.wdl"),
        version="1.0",
        workflow=None,
        tasks=[],
        imports=[
            WDLImport(
                path="external/lib.wdl",
                namespace="lib",
                resolved_path=external_file,
            )
        ],
        source_code="",
    )

    doc2 = WDLDocument(
        file_path=internal_file2,
        relative_path=Path("workflow2.wdl"),
        version="1.0",
        workflow=None,
        tasks=[],
        imports=[
            WDLImport(
                path="external/lib.wdl",
                namespace="lib",
                resolved_path=external_file,
            )
        ],
        source_code="",
    )

    external_doc = WDLDocument(
        file_path=external_file,
        relative_path=Path("external/lib.wdl"),
        version="1.0",
        workflow=None,
        tasks=[],
        imports=[],
        source_code="",
    )

    use_case, _, parser, _ = use_case_factory(
        internal_files=[internal_file1, internal_file2],
        external_files=[external_file],
        documents={
            internal_file1: doc1,
            internal_file2: doc2,
            external_file: external_doc,
        },
    )

    # Act
    result = use_case.execute()

    # Assert
    assert result is True
    # Should parse 2 internal + 1 external (not 2 external)
    assert len(parser.parse_calls) == 3
    assert parser.parse_calls.count(external_file) == 1


def test_should_handle_transitive_external_dependencies(temp_dir, use_case_factory):
    """Test handling of transitive external dependencies (external importing external)."""
    # Arrange
    internal_file = temp_dir / "workflow.wdl"
    external_file1 = temp_dir / "external" / "lib1.wdl"
    external_file2 = temp_dir / "external" / "lib2.wdl"

    # Internal imports external1, external1 imports external2
    internal_doc = WDLDocument(
        file_path=internal_file,
        relative_path=Path("workflow.wdl"),
        version="1.0",
        workflow=None,
        tasks=[],
        imports=[
            WDLImport(
                path="external/lib1.wdl",
                namespace="lib1",
                resolved_path=external_file1,
            )
        ],
        source_code="",
    )

    external_doc1 = WDLDocument(
        file_path=external_file1,
        relative_path=Path("external/lib1.wdl"),
        version="1.0",
        workflow=None,
        tasks=[],
        imports=[
            WDLImport(
                path="external/lib2.wdl",
                namespace="lib2",
                resolved_path=external_file2,
            )
        ],
        source_code="",
    )

    external_doc2 = WDLDocument(
        file_path=external_file2,
        relative_path=Path("external/lib2.wdl"),
        version="1.0",
        workflow=None,
        tasks=[],
        imports=[],
        source_code="",
    )

    use_case, _, parser, doc_generator = use_case_factory(
        internal_files=[internal_file],
        external_files=[external_file1, external_file2],
        documents={
            internal_file: internal_doc,
            external_file1: external_doc1,
            external_file2: external_doc2,
        },
    )

    # Act
    result = use_case.execute()

    # Assert
    assert result is True
    assert len(parser.parse_calls) == 3  # internal + external1 + external2
    assert len(doc_generator.documents) == 3


def test_should_skip_non_external_imports(temp_dir, use_case_factory):
    """Test that non-external imports are not processed as external."""
    # Arrange
    internal_file1 = temp_dir / "workflow.wdl"
    internal_file2 = temp_dir / "tasks.wdl"

    # Internal file imports another internal file
    doc1 = WDLDocument(
        file_path=internal_file1,
        relative_path=Path("workflow.wdl"),
        version="1.0",
        workflow=None,
        tasks=[],
        imports=[
            WDLImport(
                path="tasks.wdl",
                namespace="tasks",
                resolved_path=internal_file2,
            )
        ],
        source_code="",
    )

    doc2 = WDLDocument(
        file_path=internal_file2,
        relative_path=Path("tasks.wdl"),
        version="1.0",
        workflow=None,
        tasks=[],
        imports=[],
        source_code="",
    )

    use_case, _, parser, _ = use_case_factory(
        internal_files=[internal_file1, internal_file2],
        documents={
            internal_file1: doc1,
            internal_file2: doc2,
        },
    )

    # Act
    result = use_case.execute()

    # Assert
    assert result is True
    # Should only parse the 2 internal files (no external processing)
    assert len(parser.parse_calls) == 2


def test_should_handle_documents_without_imports(temp_dir, use_case_factory, sample_wdl_document):
    """Test handling of documents without imports."""
    # Arrange
    wdl_file = temp_dir / "workflow.wdl"
    use_case, _, parser, _ = use_case_factory(internal_files=[wdl_file], documents={wdl_file: sample_wdl_document})

    # Act
    result = use_case.execute()

    # Assert
    assert result is True
    assert len(parser.parse_calls) == 1


def test_should_return_false_when_documentation_generation_fails(temp_dir, use_case_factory, sample_wdl_document):
    """Test handling when documentation generation fails."""
    # Arrange
    wdl_file = temp_dir / "workflow.wdl"
    use_case, _, _, _ = use_case_factory(
        internal_files=[wdl_file], documents={wdl_file: sample_wdl_document}, should_fail_generation=True
    )

    # Act
    result = use_case.execute()

    # Assert
    assert result is False


def test_should_collect_parse_errors_and_pass_to_documentation_generation(
    temp_dir, use_case_factory, sample_wdl_document
):
    """Test that parse errors are collected and passed to documentation generation."""
    # Arrange
    good_file = temp_dir / "good.wdl"
    bad_file = temp_dir / "bad.wdl"
    use_case, _, _, doc_generator = use_case_factory(
        internal_files=[good_file, bad_file],
        documents={good_file: sample_wdl_document},
        parse_errors={bad_file: Exception("Parse error")},
    )

    # Act
    result = use_case.execute()

    # Assert
    assert result is True
    assert doc_generator.execute_called
    assert len(doc_generator.documents) == 1
    assert len(doc_generator.parse_errors) == 1  # One error from bad_file
