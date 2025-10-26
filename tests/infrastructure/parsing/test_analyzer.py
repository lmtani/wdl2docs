"""
Unit tests for Analyzer infrastructure component.

Tests the dependency analysis functionality, including:
- Finding external dependencies
- External path detection
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from src.infrastructure.parsing.analyzer import Analyzer
from src.domain.value_objects import WDLImport


@pytest.fixture
def analyzer(temp_dir):
    """Create an Analyzer instance."""
    return Analyzer(base_path=temp_dir)


@pytest.fixture
def mock_imports():
    """Create mock imports."""
    return [WDLImport(path="lib/tasks.wdl", namespace="lib", resolved_path=Path("/path/to/lib/tasks.wdl"))]


def should_initialize_with_base_path(temp_dir):
    """Test Analyzer initialization."""
    # Arrange & Act
    analyzer = Analyzer(base_path=temp_dir)

    # Assert
    assert analyzer.base_path == temp_dir


def should_find_external_dependencies(analyzer, temp_dir):
    """Test finding external dependencies."""
    # Arrange
    mock_doc = Mock()
    mock_import = Mock()
    mock_import.resolved_path = temp_dir / "external" / "lib.wdl"
    mock_doc.imports = [mock_import]

    parsed_paths = set()

    # Act
    external_files = analyzer.find_external_dependencies([mock_doc], parsed_paths)

    # Assert
    assert len(external_files) == 1
    assert external_files[0] == (temp_dir / "external" / "lib.wdl").resolve()


def should_not_include_already_parsed_external_dependencies(analyzer, temp_dir):
    """Test that already parsed external dependencies are not included."""
    # Arrange
    mock_doc = Mock()
    mock_import = Mock()
    resolved_path = (temp_dir / "external" / "lib.wdl").resolve()
    mock_import.resolved_path = resolved_path
    mock_doc.imports = [mock_import]

    parsed_paths = {resolved_path}

    # Act
    external_files = analyzer.find_external_dependencies([mock_doc], parsed_paths)

    # Assert
    assert external_files == []


def should_not_include_internal_dependencies_as_external(analyzer, temp_dir):
    """Test that internal dependencies are not included in external list."""
    # Arrange
    mock_doc = Mock()
    mock_import = Mock()
    mock_import.resolved_path = temp_dir / "internal" / "lib.wdl"
    mock_doc.imports = [mock_import]

    parsed_paths = set()

    # Act
    external_files = analyzer.find_external_dependencies([mock_doc], parsed_paths)

    # Assert
    assert external_files == []


def should_detect_external_paths_correctly(analyzer, temp_dir):
    """Test external path detection."""
    # Arrange
    external_path = temp_dir / "external" / "lib.wdl"
    internal_path = temp_dir / "internal" / "lib.wdl"
    outside_path = Path("/outside/lib.wdl")

    # Act & Assert
    assert analyzer._is_external_path(external_path) is True
    assert analyzer._is_external_path(internal_path) is False
    assert analyzer._is_external_path(outside_path) is False
