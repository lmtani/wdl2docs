"""
Unit tests for AstMapper infrastructure component.

Tests the AST mapping functionality, including:
- Description parsing from parameter_meta
- Type parsing
- Input/output mapping
"""

import pytest
from pathlib import Path
import WDL

from src.infrastructure.parsing.ast_mapper import AstMapper
from src.domain.value_objects import WDLInput, WDLOutput


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def ast_mapper(temp_dir):
    """Create an AstMapper instance."""
    output_dir = temp_dir / "output"
    return AstMapper(base_path=temp_dir, output_dir=output_dir)


class TestDescriptionParsing:
    """Tests for description parsing from parameter_meta."""

    def should_parse_simple_string_description(self, ast_mapper):
        """Test parsing a simple string description."""
        # Arrange
        parameter_meta = {
            "input_file": "Path to the input file"
        }
        
        # Act
        description = ast_mapper._parse_description(parameter_meta, "input_file")
        
        # Assert
        assert description == "Path to the input file"

    def should_parse_dict_with_description_field(self, ast_mapper):
        """Test parsing a dictionary with description field."""
        # Arrange
        parameter_meta = {
            "input_file": "{'description': 'Path to the input file', 'help': 'Additional info'}"
        }
        
        # Act
        description = ast_mapper._parse_description(parameter_meta, "input_file")
        
        # Assert
        assert description == "Path to the input file"

    def should_parse_dict_with_only_description(self, ast_mapper):
        """Test parsing a dictionary with only description field."""
        # Arrange
        parameter_meta = {
            "input_file": "{'description': 'Path to the input file'}"
        }
        
        # Act
        description = ast_mapper._parse_description(parameter_meta, "input_file")
        
        # Assert
        assert description == "Path to the input file"

    def should_return_none_for_missing_parameter(self, ast_mapper):
        """Test that None is returned when parameter is not in meta."""
        # Arrange
        parameter_meta = {
            "other_param": "Some description"
        }
        
        # Act
        description = ast_mapper._parse_description(parameter_meta, "missing_param")
        
        # Assert
        assert description is None

    def should_return_none_for_empty_parameter_meta(self, ast_mapper):
        """Test that None is returned for empty parameter_meta."""
        # Arrange
        parameter_meta = {}
        
        # Act
        description = ast_mapper._parse_description(parameter_meta, "any_param")
        
        # Assert
        assert description is None

    def should_fallback_to_raw_string_for_dict_without_description(self, ast_mapper):
        """Test fallback to raw string when dict has no description field."""
        # Arrange
        parameter_meta = {
            "input_file": "{'help': 'Some help text', 'category': 'input'}"
        }
        
        # Act
        description = ast_mapper._parse_description(parameter_meta, "input_file")
        
        # Assert
        assert description == "{'help': 'Some help text', 'category': 'input'}"

    def should_handle_invalid_dict_syntax(self, ast_mapper):
        """Test that invalid dict syntax falls back to raw string."""
        # Arrange
        parameter_meta = {
            "input_file": "{'description': invalid syntax"
        }
        
        # Act
        description = ast_mapper._parse_description(parameter_meta, "input_file")
        
        # Assert
        assert description == "{'description': invalid syntax"

    def should_handle_multiline_descriptions(self, ast_mapper):
        """Test handling of multiline descriptions."""
        # Arrange
        parameter_meta = {
            "input_file": "This is a multiline\ndescription with\nmultiple lines"
        }
        
        # Act
        description = ast_mapper._parse_description(parameter_meta, "input_file")
        
        # Assert
        assert description == "This is a multiline\ndescription with\nmultiple lines"

    def should_handle_description_with_special_characters(self, ast_mapper):
        """Test handling of descriptions with special characters."""
        # Arrange
        parameter_meta = {
            "input_file": "Path with special chars: @#$%^&*()"
        }
        
        # Act
        description = ast_mapper._parse_description(parameter_meta, "input_file")
        
        # Assert
        assert description == "Path with special chars: @#$%^&*()"

    def should_handle_double_quoted_dict_format(self, ast_mapper):
        """Test handling of dictionary with double quotes."""
        # Arrange
        parameter_meta = {
            "input_file": '{"description": "Path to the input file"}'
        }
        
        # Act
        description = ast_mapper._parse_description(parameter_meta, "input_file")
        
        # Assert
        assert description == "Path to the input file"


class TestTryParseAsDict:
    """Tests for _try_parse_as_dict helper method."""

    def should_parse_valid_dict_with_description(self, ast_mapper):
        """Test parsing a valid dict string with description."""
        # Arrange
        raw_value = "{'description': 'Test description', 'other': 'value'}"
        
        # Act
        result = ast_mapper._try_parse_as_dict(raw_value)
        
        # Assert
        assert result == "Test description"

    def should_return_none_for_dict_without_description(self, ast_mapper):
        """Test that None is returned for dict without description field."""
        # Arrange
        raw_value = "{'other': 'value', 'category': 'test'}"
        
        # Act
        result = ast_mapper._try_parse_as_dict(raw_value)
        
        # Assert
        assert result is None

    def should_return_none_for_non_dict_value(self, ast_mapper):
        """Test that None is returned for non-dict values."""
        # Arrange
        raw_value = "['list', 'of', 'items']"
        
        # Act
        result = ast_mapper._try_parse_as_dict(raw_value)
        
        # Assert
        assert result is None

    def should_return_none_for_plain_string(self, ast_mapper):
        """Test that None is returned for plain strings."""
        # Arrange
        raw_value = "Just a plain string"
        
        # Act
        result = ast_mapper._try_parse_as_dict(raw_value)
        
        # Assert
        assert result is None

    def should_return_none_for_invalid_syntax(self, ast_mapper):
        """Test that None is returned for invalid syntax."""
        # Arrange
        raw_value = "{'invalid': syntax"
        
        # Act
        result = ast_mapper._try_parse_as_dict(raw_value)
        
        # Assert
        assert result is None

    def should_handle_empty_dict(self, ast_mapper):
        """Test handling of empty dictionary."""
        # Arrange
        raw_value = "{}"
        
        # Act
        result = ast_mapper._try_parse_as_dict(raw_value)
        
        # Assert
        assert result is None


class TestInputParsing:
    """Tests for input parsing with descriptions."""

    def should_parse_input_with_simple_description(self, ast_mapper, temp_dir):
        """Test parsing input with simple string description."""
        # Arrange
        wdl_content = """
        version 1.0
        
        task test_task {
            input {
                File input_file
            }
            
            parameter_meta {
                input_file: "Path to the input file"
            }
            
            command {
                echo "test"
            }
        }
        """
        wdl_file = temp_dir / "test.wdl"
        wdl_file.write_text(wdl_content)
        doc = WDL.load(str(wdl_file))
        task = doc.tasks[0]
        parameter_meta = ast_mapper._extract_parameter_meta(task)
        
        # Act
        inputs = [ast_mapper._parse_input(inp.value, parameter_meta) for inp in task.available_inputs]
        
        # Assert
        assert len(inputs) == 1
        assert inputs[0].name == "input_file"
        assert inputs[0].description == "Path to the input file"

    def should_parse_input_with_dict_description(self, ast_mapper, temp_dir):
        """Test parsing input with dictionary description."""
        # Arrange
        wdl_content = """
        version 1.0
        
        task test_task {
            input {
                File input_file
            }
            
            parameter_meta {
                input_file: {
                    description: "Path to the input file",
                    help: "Additional help text"
                }
            }
            
            command {
                echo "test"
            }
        }
        """
        wdl_file = temp_dir / "test.wdl"
        wdl_file.write_text(wdl_content)
        doc = WDL.load(str(wdl_file))
        task = doc.tasks[0]
        parameter_meta = ast_mapper._extract_parameter_meta(task)
        
        # Act
        inputs = [ast_mapper._parse_input(inp.value, parameter_meta) for inp in task.available_inputs]
        
        # Assert
        assert len(inputs) == 1
        assert inputs[0].name == "input_file"
        assert inputs[0].description == "Path to the input file"

    def should_parse_input_without_description(self, ast_mapper, temp_dir):
        """Test parsing input without description."""
        # Arrange
        wdl_content = """
        version 1.0
        
        task test_task {
            input {
                File input_file
            }
            
            command {
                echo "test"
            }
        }
        """
        wdl_file = temp_dir / "test.wdl"
        wdl_file.write_text(wdl_content)
        doc = WDL.load(str(wdl_file))
        task = doc.tasks[0]
        parameter_meta = ast_mapper._extract_parameter_meta(task)
        
        # Act
        inputs = [ast_mapper._parse_input(inp.value, parameter_meta) for inp in task.available_inputs]
        
        # Assert
        assert len(inputs) == 1
        assert inputs[0].name == "input_file"
        assert inputs[0].description is None

    def should_parse_multiple_inputs_with_mixed_descriptions(self, ast_mapper, temp_dir):
        """Test parsing multiple inputs with different description formats."""
        # Arrange
        wdl_content = """
        version 1.0
        
        task test_task {
            input {
                File input_file
                String sample_name
                Int? optional_param
            }
            
            parameter_meta {
                input_file: "Simple string description"
                sample_name: {
                    description: "Dict description",
                    category: "required"
                }
            }
            
            command {
                echo "test"
            }
        }
        """
        wdl_file = temp_dir / "test.wdl"
        wdl_file.write_text(wdl_content)
        doc = WDL.load(str(wdl_file))
        task = doc.tasks[0]
        parameter_meta = ast_mapper._extract_parameter_meta(task)
        
        # Act
        inputs = [ast_mapper._parse_input(inp.value, parameter_meta) for inp in task.available_inputs]
        
        # Assert
        assert len(inputs) == 3
        assert inputs[0].description == "Simple string description"
        assert inputs[1].description == "Dict description"
        assert inputs[2].description is None  # No description provided
