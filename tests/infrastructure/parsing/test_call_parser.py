"""
Unit tests for CallParser infrastructure component.

Tests the WDL call parsing functionality, including:
- Simple call parsing
- Recursive parsing of calls in scatter blocks
- Recursive parsing of calls in conditional blocks
- Nested structures (scatter inside conditional, etc.)
"""

import pytest
from pathlib import Path
import WDL

from src.infrastructure.parsing.call_parser import CallParser
from src.domain.value_objects import WDLImport


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def call_parser(temp_dir):
    """Create a CallParser instance."""
    return CallParser(base_path=temp_dir)


def _parse_wdl_content(content: str, temp_dir: Path):
    """Helper to parse WDL content and return the workflow."""
    wdl_file = temp_dir / "test.wdl"
    wdl_file.write_text(content)
    doc = WDL.load(str(wdl_file))
    return doc.workflow


def should_parse_simple_calls_at_top_level(call_parser, temp_dir):
    """Test parsing simple calls at the workflow top level."""
    # Arrange
    wdl_content = """
    version 1.0
    
    task my_task {
        command { echo "hello" }
    }
    
    workflow simple {
        call my_task
        call my_task as task_alias
    }
    """
    workflow = _parse_wdl_content(wdl_content, temp_dir)
    
    # Act
    calls = call_parser.parse_calls(workflow, [])
    
    # Assert
    assert len(calls) == 2
    assert calls[0].name == "my_task"
    assert calls[0].alias is None
    assert calls[1].name == "my_task"
    assert calls[1].alias == "task_alias"


def should_parse_calls_inside_scatter_block(call_parser, temp_dir):
    """Test parsing calls nested inside a scatter block."""
    # Arrange
    wdl_content = """
    version 1.0
    
    task process {
        input {
            String item
        }
        command { echo ~{item} }
        output {
            String result = read_string(stdout())
        }
    }
    
    workflow scatter_example {
        input {
            Array[String] items
        }
        
        scatter(item in items) {
            call process { input: item = item }
        }
    }
    """
    workflow = _parse_wdl_content(wdl_content, temp_dir)
    
    # Act
    calls = call_parser.parse_calls(workflow, [])
    
    # Assert
    assert len(calls) == 1
    assert calls[0].name == "process"
    assert calls[0].is_local is True


def should_parse_calls_inside_conditional_block(call_parser, temp_dir):
    """Test parsing calls nested inside a conditional block."""
    # Arrange
    wdl_content = """
    version 1.0
    
    task optional_task {
        command { echo "optional" }
        output {
            String result = read_string(stdout())
        }
    }
    
    workflow conditional_example {
        input {
            Boolean run_optional
        }
        
        if (run_optional) {
            call optional_task
        }
    }
    """
    workflow = _parse_wdl_content(wdl_content, temp_dir)
    
    # Act
    calls = call_parser.parse_calls(workflow, [])
    
    # Assert
    assert len(calls) == 1
    assert calls[0].name == "optional_task"


def should_parse_calls_in_nested_scatter_and_conditional(call_parser, temp_dir):
    """Test parsing calls in nested scatter and conditional blocks (like test.wdl example)."""
    # Arrange
    wdl_content = """
    version 1.0
    
    task compare {
        input {
            File genome_one
            File genome_two
        }
        command { echo "comparing" }
        output {
            File comparison_table = stdout()
        }
    }
    
    task merge {
        input {
            Array[File] tables
        }
        command { cat ~{sep=' ' tables} }
        output {
            File merged = stdout()
        }
    }
    
    workflow nested_example {
        input {
            Array[File] genome_set_one
            Array[File] genome_set_two
        }
        
        scatter(sample in zip(genome_set_one, genome_set_two)) {
            if (defined(genome_set_one)) {
                call compare {
                    input:
                        genome_one = sample.left,
                        genome_two = sample.right
                }
            }
        }
        
        Array[File] comparison_tables = select_all(compare.comparison_table)
        
        call merge {
            input:
                tables = comparison_tables
        }
    }
    """
    workflow = _parse_wdl_content(wdl_content, temp_dir)
    
    # Act
    calls = call_parser.parse_calls(workflow, [])
    
    # Assert
    # Should find both the 'compare' call inside scatter+if and the 'merge' call at top level
    assert len(calls) == 2
    call_names = {call.name for call in calls}
    assert "compare" in call_names
    assert "merge" in call_names


def should_parse_calls_with_multiple_levels_of_nesting(call_parser, temp_dir):
    """Test parsing calls with deep nesting: scatter -> conditional -> scatter."""
    # Arrange
    wdl_content = """
    version 1.0
    
    task inner_task {
        input { String value }
        command { echo ~{value} }
    }
    
    workflow deeply_nested {
        input {
            Array[String] outer_items
            Array[String] inner_items
            Boolean condition
        }
        
        scatter(outer in outer_items) {
            if (condition) {
                scatter(inner in inner_items) {
                    call inner_task { input: value = inner }
                }
            }
        }
    }
    """
    workflow = _parse_wdl_content(wdl_content, temp_dir)
    
    # Act
    calls = call_parser.parse_calls(workflow, [])
    
    # Assert
    assert len(calls) == 1
    assert calls[0].name == "inner_task"


def should_parse_mix_of_top_level_and_nested_calls(call_parser, temp_dir):
    """Test parsing a mix of top-level calls and nested calls."""
    # Arrange
    wdl_content = """
    version 1.0
    
    task setup {
        command { echo "setup" }
    }
    
    task process {
        input { String item }
        command { echo ~{item} }
    }
    
    task cleanup {
        command { echo "cleanup" }
    }
    
    workflow mixed_calls {
        input {
            Array[String] items
        }
        
        call setup
        
        scatter(item in items) {
            call process { input: item = item }
        }
        
        call cleanup
    }
    """
    workflow = _parse_wdl_content(wdl_content, temp_dir)
    
    # Act
    calls = call_parser.parse_calls(workflow, [])
    
    # Assert
    assert len(calls) == 3
    assert calls[0].name == "setup"
    assert calls[1].name == "process"
    assert calls[2].name == "cleanup"


def should_handle_empty_workflow_body(call_parser, temp_dir):
    """Test that parser handles workflows with no calls."""
    # Arrange
    wdl_content = """
    version 1.0
    
    workflow empty {
        input {
            String message
        }
        output {
            String result = message
        }
    }
    """
    workflow = _parse_wdl_content(wdl_content, temp_dir)
    
    # Act
    calls = call_parser.parse_calls(workflow, [])
    
    # Assert
    assert len(calls) == 0


def should_handle_scatter_without_calls(call_parser, temp_dir):
    """Test that parser handles scatter blocks that don't contain calls."""
    # Arrange
    wdl_content = """
    version 1.0
    
    workflow scatter_no_calls {
        input {
            Array[String] items
        }
        
        scatter(item in items) {
            String processed = item + "_processed"
        }
    }
    """
    workflow = _parse_wdl_content(wdl_content, temp_dir)
    
    # Act
    calls = call_parser.parse_calls(workflow, [])
    
    # Assert
    assert len(calls) == 0

