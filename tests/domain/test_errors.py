"""
Unit tests for domain errors.

Tests the domain error classes including ParseError.
"""

from pathlib import Path
from datetime import datetime

from src.domain.errors import ParseError


def should_initialize_parse_error_with_required_fields():
    """Test ParseError initialization with required fields."""
    # Arrange
    file_path = Path("workflow.wdl")
    relative_path = Path("workflow.wdl")
    error_type = "SyntaxError"
    error_message = "Invalid syntax"

    # Act
    error = ParseError(
        file_path=file_path, relative_path=relative_path, error_type=error_type, error_message=error_message
    )

    # Assert
    assert error.file_path == file_path
    assert error.relative_path == relative_path
    assert error.error_type == error_type
    assert error.error_message == error_message
    assert error.line_number is None
    assert error.column_number is None
    assert isinstance(error.timestamp, str)


def should_initialize_parse_error_with_all_fields():
    """Test ParseError initialization with all fields."""
    # Arrange
    file_path = Path("/full/path/workflow.wdl")
    relative_path = Path("workflow.wdl")
    error_type = "ValidationError"
    error_message = "Invalid input type"
    line_number = 10
    column_number = 5

    # Act
    error = ParseError(
        file_path=file_path,
        relative_path=relative_path,
        error_type=error_type,
        error_message=error_message,
        line_number=line_number,
        column_number=column_number,
    )

    # Assert
    assert error.file_path == file_path
    assert error.relative_path == relative_path
    assert error.error_type == error_type
    assert error.error_message == error_message
    assert error.line_number == line_number
    assert error.column_number == column_number
    assert isinstance(error.timestamp, str)


def should_return_error_severity_for_error_types():
    """Test severity property for various error types."""
    # Arrange
    test_cases = [
        ("SyntaxError", "error"),
        ("ValidationError", "error"),
        ("ImportError", "error"),
        ("Warning", "warning"),
        ("DeprecationWarning", "warning"),
        ("syntax warning", "warning"),
    ]

    for error_type, expected_severity in test_cases:
        # Act
        error = ParseError(
            file_path=Path("test.wdl"),
            relative_path=Path("test.wdl"),
            error_type=error_type,
            error_message="Test message",
        )

        # Assert
        assert error.severity == expected_severity, f"Failed for {error_type}"


def should_return_short_message_for_short_messages():
    """Test short_message property for messages shorter than max length."""
    # Arrange
    short_message = "This is a short error message"
    error = ParseError(
        file_path=Path("test.wdl"),
        relative_path=Path("test.wdl"),
        error_type="SyntaxError",
        error_message=short_message,
    )

    # Act & Assert
    assert error.short_message == short_message


def should_truncate_long_messages():
    """Test short_message property for messages longer than max length."""
    # Arrange
    long_message = "A" * 250  # Much longer than 200 chars
    error = ParseError(
        file_path=Path("test.wdl"), relative_path=Path("test.wdl"), error_type="SyntaxError", error_message=long_message
    )

    # Act
    short_message = error.short_message

    # Assert
    assert len(short_message) == 203  # 200 + "..."
    assert short_message.endswith("...")
    assert short_message.startswith("A" * 200)


def should_return_none_location_info_when_no_line_info():
    """Test location_info property when no line/column info is available."""
    # Arrange
    error = ParseError(
        file_path=Path("test.wdl"), relative_path=Path("test.wdl"), error_type="SyntaxError", error_message="Test error"
    )

    # Act & Assert
    assert error.location_info is None


def should_return_line_only_location_info():
    """Test location_info property when only line number is available."""
    # Arrange
    error = ParseError(
        file_path=Path("test.wdl"),
        relative_path=Path("test.wdl"),
        error_type="SyntaxError",
        error_message="Test error",
        line_number=42,
    )

    # Act & Assert
    assert error.location_info == "Line 42"


def should_return_line_and_column_location_info():
    """Test location_info property when both line and column are available."""
    # Arrange
    error = ParseError(
        file_path=Path("test.wdl"),
        relative_path=Path("test.wdl"),
        error_type="SyntaxError",
        error_message="Test error",
        line_number=42,
        column_number=10,
    )

    # Act & Assert
    assert error.location_info == "Line 42, Column 10"


def should_generate_timestamp_automatically():
    """Test that timestamp is generated automatically."""
    # Arrange
    before_creation = datetime.now()

    # Act
    error = ParseError(
        file_path=Path("test.wdl"), relative_path=Path("test.wdl"), error_type="SyntaxError", error_message="Test error"
    )

    after_creation = datetime.now()

    # Assert
    timestamp = datetime.fromisoformat(error.timestamp)
    assert before_creation <= timestamp <= after_creation
