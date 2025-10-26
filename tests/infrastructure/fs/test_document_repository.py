"""
Unit tests for DocumentRepository infrastructure component.

Tests the document repository functionality, including:
- File discovery operations
- Path resolution
- External file detection
- File existence checks
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from src.infrastructure.fs.document_repo import DocumentRepository


@pytest.fixture
def mock_discovery():
    """Create a mock Discovery service."""
    discovery = Mock()
    return discovery


@pytest.fixture
def document_repository(temp_dir, mock_discovery):
    """Create a DocumentRepository with mocked discovery service."""
    repository = DocumentRepository(root_path=temp_dir, exclude_patterns=["__pycache__/"])
    repository.discovery = mock_discovery
    return repository


def should_initialize_with_default_exclude_patterns(temp_dir):
    """Test that DocumentRepository initializes with default exclude patterns."""
    # Arrange & Act
    repository = DocumentRepository(root_path=temp_dir)

    # Assert
    assert repository.root_path == temp_dir
    assert "__pycache__/" in repository.exclude_patterns
    assert ".git/" in repository.exclude_patterns


def should_initialize_with_custom_exclude_patterns(temp_dir):
    """Test that DocumentRepository accepts custom exclude patterns."""
    # Arrange
    custom_patterns = ["test/", "cache/"]

    # Act
    repository = DocumentRepository(root_path=temp_dir, exclude_patterns=custom_patterns)

    # Assert
    assert repository.exclude_patterns == custom_patterns


def should_initialize_with_default_external_dirs(temp_dir):
    """Test that DocumentRepository initializes with default external_dirs."""
    # Arrange & Act
    repository = DocumentRepository(root_path=temp_dir)

    # Assert
    assert repository.external_dirs == ["external"]


def should_initialize_with_custom_external_dirs(temp_dir):
    """Test that DocumentRepository accepts custom external_dirs."""
    # Arrange
    custom_external_dirs = ["vendor", "third_party", "external"]

    # Act
    repository = DocumentRepository(root_path=temp_dir, external_dirs=custom_external_dirs)

    # Assert
    assert repository.external_dirs == custom_external_dirs


def should_delegate_find_internal_wdl_files_to_discovery(document_repository, mock_discovery):
    """Test that find_internal_wdl_files delegates to Discovery service."""
    # Arrange
    expected_files = [Path("workflow.wdl"), Path("task.wdl")]
    mock_discovery.find_internal_wdl_files.return_value = expected_files

    # Act
    result = document_repository.find_internal_wdl_files()

    # Assert
    assert result == expected_files
    mock_discovery.find_internal_wdl_files.assert_called_once()


def should_delegate_find_all_wdl_files_to_discovery(document_repository, mock_discovery):
    """Test that find_all_wdl_files delegates to Discovery service."""
    # Arrange
    expected_files = [Path("internal/workflow.wdl"), Path("external/lib.wdl")]
    mock_discovery.find_all_wdl_files.return_value = expected_files

    # Act
    result = document_repository.find_all_wdl_files()

    # Assert
    assert result == expected_files
    mock_discovery.find_all_wdl_files.assert_called_once()


def should_delegate_find_external_wdl_files_to_discovery(document_repository, mock_discovery):
    """Test that find_external_wdl_files delegates to Discovery service."""
    # Arrange
    expected_files = [Path("external/lib.wdl")]
    mock_discovery.find_external_wdl_files.return_value = expected_files

    # Act
    result = document_repository.find_external_wdl_files()

    # Assert
    assert result == expected_files
    mock_discovery.find_external_wdl_files.assert_called_once()


def should_delegate_collect_import_chain_to_discovery(document_repository, mock_discovery):
    """Test that collect_import_chain delegates to Discovery service."""
    # Arrange
    starting_files = [Path("workflow.wdl")]
    expected_chain = {Path("workflow.wdl"), Path("task.wdl")}
    mock_discovery.collect_import_chain.return_value = expected_chain

    # Act
    result = document_repository.collect_import_chain(starting_files)

    # Assert
    assert result == expected_chain
    mock_discovery.collect_import_chain.assert_called_once_with(starting_files, None)


def should_check_file_exists_correctly(temp_dir, document_repository):
    """Test file existence checking."""
    # Arrange
    wdl_file = temp_dir / "test.wdl"
    wdl_file.write_text("version 1.0\nworkflow Test {}")
    non_wdl_file = temp_dir / "test.txt"
    non_wdl_file.write_text("not a wdl file")

    # Act & Assert
    assert document_repository.exists(wdl_file) is True
    assert document_repository.exists(non_wdl_file) is False
    assert document_repository.exists(temp_dir / "nonexistent.wdl") is False


def should_get_relative_path_from_root(temp_dir, document_repository):
    """Test relative path calculation from repository root."""
    # Arrange
    absolute_path = temp_dir / "workflows" / "main.wdl"

    # Act
    relative_path = document_repository.get_relative_path(absolute_path)

    # Assert
    assert relative_path == Path("workflows/main.wdl")


def should_return_path_as_is_when_outside_root(document_repository):
    """Test that paths outside root are returned as-is."""
    # Arrange
    outside_path = Path("/external/path/file.wdl")

    # Act
    result = document_repository.get_relative_path(outside_path)

    # Assert
    assert result == outside_path


def should_identify_external_files_correctly(temp_dir, document_repository):
    """Test external file detection."""
    # Arrange
    internal_path = temp_dir / "workflows" / "main.wdl"
    external_path = temp_dir / "external" / "lib.wdl"
    outside_path = Path("/some/other/path/file.wdl")

    # Act & Assert
    assert document_repository.is_external(internal_path) is False
    assert document_repository.is_external(external_path) is True
    # Files outside root_path should now be detected as external
    assert document_repository.is_external(outside_path) is True


def should_identify_custom_external_dirs(temp_dir):
    """Test external file detection with custom external directories."""
    # Arrange
    repository = DocumentRepository(
        root_path=temp_dir, 
        external_dirs=["vendor", "third_party"]
    )
    internal_path = temp_dir / "workflows" / "main.wdl"
    vendor_path = temp_dir / "vendor" / "lib.wdl"
    third_party_path = temp_dir / "third_party" / "utils.wdl"
    external_path = temp_dir / "external" / "old.wdl"  # Not in custom list

    # Act & Assert
    assert repository.is_external(internal_path) is False
    assert repository.is_external(vendor_path) is True
    assert repository.is_external(third_party_path) is True
    # 'external' is not in custom list, so should be internal
    assert repository.is_external(external_path) is False


def should_provide_string_representation(document_repository, temp_dir):
    """Test string representation of DocumentRepository."""
    # Arrange & Act
    result = str(document_repository)

    # Assert
    assert f"DocumentRepository(root_path={temp_dir})" == result
