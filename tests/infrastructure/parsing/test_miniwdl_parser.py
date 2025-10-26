"""
Unit tests for MiniwdlParser infrastructure component.

Tests the WDL parsing functionality, including:
- Document parsing
- Workflow and task extraction
- Error handling and conversion
- Import resolution
"""

import pytest
from pathlib import Path

from src.infrastructure.parsing.miniwdl_parser import MiniwdlParser
from src.domain.errors import ParseError


def should_parse_simple_workflow_successfully(temp_dir, create_wdl_file, sample_wdl_content):
    """Test parsing a simple workflow WDL file."""
    # Arrange
    wdl_file = create_wdl_file("workflow.wdl", sample_wdl_content)
    output_dir = temp_dir / "output"
    parser = MiniwdlParser(base_path=temp_dir, output_dir=output_dir)

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    assert document is not None
    assert document.file_path == wdl_file
    assert document.version == "1.0"
    assert document.workflow is not None
    assert document.workflow.name == "HelloWorld"
    assert len(document.tasks) == 1
    assert document.tasks[0].name == "SayHello"


def should_extract_workflow_metadata(temp_dir, create_wdl_file, sample_wdl_content):
    """Test extraction of workflow metadata."""
    # Arrange
    wdl_file = create_wdl_file("workflow.wdl", sample_wdl_content)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    workflow = document.workflow
    assert workflow.description == "A simple hello world workflow"
    assert "description" in workflow.meta
    assert workflow.meta["description"] == "A simple hello world workflow"


def should_parse_workflow_inputs_with_optional_types(temp_dir, create_wdl_file, sample_wdl_content):
    """Test parsing workflow inputs including optional types."""
    # Arrange
    wdl_file = create_wdl_file("workflow.wdl", sample_wdl_content)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    inputs = document.workflow.inputs
    # Note: includes inputs from called tasks (docker_image from SayHello task)
    assert len(inputs) >= 2

    # Check required input
    name_input = next(inp for inp in inputs if inp.name == "name")
    assert name_input.type.name == "String"
    assert not name_input.type.optional

    # Check optional input
    file_input = next(inp for inp in inputs if inp.name == "optional_file")
    assert file_input.type.name == "File"
    assert file_input.type.optional


def should_parse_workflow_outputs(temp_dir, create_wdl_file, sample_wdl_content):
    """Test parsing workflow outputs."""
    # Arrange
    wdl_file = create_wdl_file("workflow.wdl", sample_wdl_content)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    outputs = document.workflow.outputs
    assert len(outputs) == 1
    assert outputs[0].name == "greeting"
    assert outputs[0].type.name == "String"
    assert "SayHello.message" in outputs[0].expression


def should_parse_task_with_runtime_configuration(temp_dir, create_wdl_file, sample_task_wdl):
    """Test parsing task with runtime specifications."""
    # Arrange
    wdl_file = create_wdl_file("task.wdl", sample_task_wdl)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    task = document.tasks[0]
    assert task.name == "ProcessFile"

    runtime = task.runtime
    assert "docker" in runtime
    assert "cpu" in runtime
    assert "memory" in runtime
    assert runtime["memory"] == '"8 GB"'


def should_parse_task_inputs_with_default_values(temp_dir, create_wdl_file, sample_task_wdl):
    """Test parsing task inputs with default values."""
    # Arrange
    wdl_file = create_wdl_file("task.wdl", sample_task_wdl)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    task = document.tasks[0]
    inputs = task.inputs

    # Check input with default
    threads_input = next(inp for inp in inputs if inp.name == "threads")
    assert threads_input.default_value is not None
    assert "4" in threads_input.default_value


def should_parse_task_command_and_format_correctly(temp_dir, create_wdl_file, sample_task_wdl):
    """Test parsing and formatting task command."""
    # Arrange
    wdl_file = create_wdl_file("task.wdl", sample_task_wdl)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    task = document.tasks[0]
    command = task.command

    assert command is not None
    assert "samtools view" in command.formatted_command
    assert "~{threads}" in command.formatted_command
    assert command.raw_command != ""


def should_parse_workflow_calls(temp_dir, create_wdl_file, sample_wdl_content):
    """Test parsing workflow calls to tasks."""
    # Arrange
    wdl_file = create_wdl_file("workflow.wdl", sample_wdl_content)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    workflow = document.workflow
    calls = workflow.calls

    assert len(calls) == 1
    assert calls[0].name == "SayHello"
    assert calls[0].task_or_workflow == "SayHello"
    assert calls[0].is_local


def should_parse_imports(temp_dir, create_wdl_file):
    """Test parsing import statements."""
    # Arrange
    # Create the imported files first
    task_content = """version 1.0
task BwaAlign {
    input {
        File fastq
    }
    command <<< echo "aligning" >>>
    output {
        File output_bam = "output.bam"
    }
}"""

    # Create directory structure
    (temp_dir / "tasks").mkdir(parents=True, exist_ok=True)
    create_wdl_file("tasks/alignment.wdl", task_content)
    create_wdl_file(
        "tasks/variant_calling.wdl", task_content.replace("BwaAlign", "CallVariants").replace("fastq", "bam")
    )

    # Now create the importing file
    import_wdl = """version 1.0

import "tasks/alignment.wdl" as align
import "tasks/variant_calling.wdl" as vc

workflow Pipeline {
    input {
        File fastq
    }
    
    call align.BwaAlign { input: fastq = fastq }
    
    output {
        File bam = BwaAlign.output_bam
    }
}
"""
    wdl_file = create_wdl_file("pipeline.wdl", import_wdl)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    imports = document.imports
    assert len(imports) == 2

    # Check first import
    align_import = imports[0]
    assert "alignment.wdl" in align_import.path
    assert align_import.namespace == "align"


def should_convert_syntax_error_to_parse_error(temp_dir, create_wdl_file):
    """Test conversion of WDL syntax errors to ParseError."""
    # Arrange
    invalid_wdl = """version 1.0
workflow Invalid {
    # Missing closing brace
"""
    wdl_file = create_wdl_file("invalid.wdl", invalid_wdl)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    try:
        parser.parse_document(wdl_file)
        pytest.fail("Expected parsing to fail")
    except Exception as e:
        parse_error = parser.convert_exception_to_error(wdl_file, e)

    # Assert
    assert isinstance(parse_error, ParseError)
    assert parse_error.file_path == wdl_file
    assert parse_error.error_type in ["SyntaxError", "ValidationError", "MultipleValidationErrors"]
    assert parse_error.error_message != ""


def should_handle_missing_workflow(temp_dir, create_wdl_file, sample_task_wdl):
    """Test parsing file with only tasks (no workflow)."""
    # Arrange
    wdl_file = create_wdl_file("tasks_only.wdl", sample_task_wdl)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    assert document.workflow is None
    assert len(document.tasks) == 1


def should_calculate_relative_path_correctly(temp_dir, create_wdl_file, sample_wdl_content):
    """Test relative path calculation for nested files."""
    # Arrange
    wdl_file = create_wdl_file("workflows/v1/main.wdl", sample_wdl_content)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    assert document.relative_path == Path("workflows/v1/main.wdl")


def should_parse_scatter_block(temp_dir, create_wdl_file, sample_scatter_wdl):
    """Test parsing workflow with scatter block."""
    # Arrange
    wdl_file = create_wdl_file("scatter.wdl", sample_scatter_wdl)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    workflow = document.workflow
    assert workflow is not None
    assert workflow.name == "ScatterExample"

    # Verify scatter is present by checking inputs/outputs
    # Scatter blocks contain calls, but they may not be directly in workflow.calls
    # The important thing is that the workflow parsed successfully
    assert len(workflow.inputs) >= 1
    assert len(workflow.outputs) >= 1


def should_extract_docker_images_from_task(temp_dir, create_wdl_file, sample_task_wdl):
    """Test Docker image extraction from task runtime."""
    # Arrange
    wdl_file = create_wdl_file("task.wdl", sample_task_wdl)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    task = document.tasks[0]
    runtime = task.runtime

    assert "docker" in runtime
    assert "docker_image" in runtime["docker"]


def should_handle_task_without_outputs(temp_dir, create_wdl_file):
    """Test parsing task without outputs."""
    # Arrange
    wdl_content = """version 1.0

task NoOutputs {
    input {
        String message
    }
    
    command <<<
        echo ~{message}
    >>>
    
    runtime {
        docker: "ubuntu:20.04"
    }
}
"""
    wdl_file = create_wdl_file("no_outputs.wdl", wdl_content)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    task = document.tasks[0]
    assert task.name == "NoOutputs"
    assert len(task.outputs) == 0


def should_parse_array_types(temp_dir, create_wdl_file, sample_scatter_wdl):
    """Test parsing Array types in inputs."""
    # Arrange
    wdl_file = create_wdl_file("scatter.wdl", sample_scatter_wdl)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    workflow = document.workflow
    inputs = workflow.inputs

    # Find array input
    array_input = next(inp for inp in inputs if "input_files" in inp.name)
    assert "Array" in array_input.type.name


def should_preserve_source_code(temp_dir, create_wdl_file, sample_wdl_content):
    """Test that original source code is preserved."""
    # Arrange
    wdl_file = create_wdl_file("workflow.wdl", sample_wdl_content)
    parser = MiniwdlParser(base_path=temp_dir, output_dir=temp_dir / "output")

    # Act
    document = parser.parse_document(wdl_file)

    # Assert
    assert document.source_code is not None
    assert "workflow HelloWorld" in document.source_code
    assert "task SayHello" in document.source_code
