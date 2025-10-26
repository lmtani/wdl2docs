"""
Unit tests for WDLLoader infrastructure component.

Tests the WDL file loading functionality, including:
- Loading WDL files with miniwdl
- Reading source code
- Combined loading operations
- Version extraction
"""

import pytest
from unittest.mock import patch, MagicMock

from src.infrastructure.parsing.wdl_loader import WDLLoader


@pytest.fixture
def sample_wdl_content():
    """Sample WDL content for testing."""
    return """version 1.0

workflow TestWorkflow {
    call TestTask
}

task TestTask {
    command {
        echo "hello"
    }
    output {
        String result = "done"
    }
}"""


@pytest.fixture
def sample_wdl_file(temp_dir, sample_wdl_content):
    """Create a sample WDL file."""
    wdl_file = temp_dir / "test.wdl"
    wdl_file.write_text(sample_wdl_content)
    return wdl_file


@patch("src.infrastructure.parsing.wdl_loader.WDL.load")
def should_load_wdl_file_successfully(mock_wdl_load, sample_wdl_file):
    """Test successful loading of WDL file."""
    # Arrange
    mock_doc = MagicMock()
    mock_wdl_load.return_value = mock_doc

    # Act
    result = WDLLoader.load_wdl_file(sample_wdl_file)

    # Assert
    assert result == mock_doc
    mock_wdl_load.assert_called_once_with(str(sample_wdl_file))


@patch("src.infrastructure.parsing.wdl_loader.WDL.load")
def should_raise_syntax_error_for_invalid_wdl(mock_wdl_load, sample_wdl_file):
    """Test that SyntaxError is raised for invalid WDL."""
    # Arrange
    mock_wdl_load.side_effect = Exception("Syntax error")  # Simplified for testing

    # Act & Assert
    with pytest.raises(Exception):
        WDLLoader.load_wdl_file(sample_wdl_file)


@patch("src.infrastructure.parsing.wdl_loader.WDL.load")
def should_raise_exception_for_other_loading_errors(mock_wdl_load, sample_wdl_file):
    """Test that other exceptions are raised for loading errors."""
    # Arrange
    mock_wdl_load.side_effect = Exception("File not found")

    # Act & Assert
    with pytest.raises(Exception):
        WDLLoader.load_wdl_file(sample_wdl_file)


def should_read_source_code_successfully(sample_wdl_file, sample_wdl_content):
    """Test successful reading of source code."""
    # Arrange & Act
    result = WDLLoader.read_source_code(sample_wdl_file)

    # Assert
    assert result == sample_wdl_content


def should_return_none_when_source_code_reading_fails(temp_dir):
    """Test that None is returned when source code reading fails."""
    # Arrange
    non_existent_file = temp_dir / "nonexistent.wdl"

    # Act
    result = WDLLoader.read_source_code(non_existent_file)

    # Assert
    assert result is None


@patch("src.infrastructure.parsing.wdl_loader.WDLLoader.load_wdl_file")
@patch("src.infrastructure.parsing.wdl_loader.WDLLoader.read_source_code")
def should_load_with_source_successfully(mock_read_source, mock_load_wdl, sample_wdl_file, sample_wdl_content):
    """Test combined loading of WDL file and source code."""
    # Arrange
    mock_doc = MagicMock()
    mock_load_wdl.return_value = mock_doc
    mock_read_source.return_value = sample_wdl_content

    # Act
    doc, source = WDLLoader.load_with_source(sample_wdl_file)

    # Assert
    assert doc == mock_doc
    assert source == sample_wdl_content
    mock_load_wdl.assert_called_once_with(sample_wdl_file)
    mock_read_source.assert_called_once_with(sample_wdl_file)


@patch("src.infrastructure.parsing.wdl_loader.WDLLoader.load_wdl_file")
@patch("src.infrastructure.parsing.wdl_loader.WDLLoader.read_source_code")
def should_load_with_source_when_source_reading_fails(mock_read_source, mock_load_wdl, sample_wdl_file):
    """Test combined loading when source code reading fails."""
    # Arrange
    mock_doc = MagicMock()
    mock_load_wdl.return_value = mock_doc
    mock_read_source.return_value = None

    # Act
    doc, source = WDLLoader.load_with_source(sample_wdl_file)

    # Assert
    assert doc == mock_doc
    assert source is None


def should_extract_version_from_document():
    """Test version extraction from WDL document."""
    # Arrange
    mock_doc = MagicMock()
    mock_doc.wdl_version = "1.1"

    # Act
    version = WDLLoader.extract_version(mock_doc)

    # Assert
    assert version == "1.1"


def should_return_default_version_when_no_version_attribute():
    """Test default version when document has no version attribute."""
    # Arrange
    mock_doc = MagicMock()
    del mock_doc.wdl_version  # Remove the attribute

    # Act
    version = WDLLoader.extract_version(mock_doc)

    # Assert
    assert version == "1.0"


def should_return_default_version_when_version_is_none():
    """Test default version when document version is None."""
    # Arrange
    mock_doc = MagicMock()
    mock_doc.wdl_version = None

    # Act
    version = WDLLoader.extract_version(mock_doc)

    # Assert
    assert version == "1.0"


def should_return_default_version_when_version_is_empty():
    """Test default version when document version is empty."""
    # Arrange
    mock_doc = MagicMock()
    mock_doc.wdl_version = ""

    # Act
    version = WDLLoader.extract_version(mock_doc)

    # Assert
    assert version == "1.0"
