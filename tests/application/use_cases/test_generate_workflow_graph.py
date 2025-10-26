"""
Unit tests for GenerateWorkflowGraph use case.

Tests the workflow graph generation functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import WDL.Tree

from src.application.use_cases.generate_workflow_graph import GenerateWorkflowGraphUseCase


@pytest.fixture
def use_case():
    """Create a GenerateWorkflowGraphUseCase instance."""
    return GenerateWorkflowGraphUseCase()


@pytest.fixture
def sample_wdl_file(temp_dir):
    """Create a sample WDL file."""
    wdl_file = temp_dir / "workflow.wdl"
    wdl_content = """
version 1.0

workflow TestWorkflow {
    call TaskA
    call TaskB { input: data = TaskA.output }
}

task TaskA {
    command { echo "A" }
    output { String output = read_string(stdout()) }
}

task TaskB {
    input { String data }
    command { echo ~{data} }
    output { String output = read_string(stdout()) }
}
"""
    wdl_file.write_text(wdl_content)
    return wdl_file


@pytest.fixture
def mock_workflow():
    """Create a mock workflow."""
    workflow = Mock(spec=WDL.Tree.Workflow)
    workflow.name = "TestWorkflow"
    workflow.body = []
    return workflow


@pytest.fixture
def mock_document(mock_workflow):
    """Create a mock WDL document."""
    doc = Mock()
    doc.workflow = mock_workflow
    doc.imports = []
    return doc


def test_should_initialize_with_templates_dir():
    """Test that use case initializes correctly."""
    # Arrange & Act
    use_case = GenerateWorkflowGraphUseCase()
    
    # Assert
    assert use_case is not None


def test_should_return_false_when_wdl_file_not_found(use_case, temp_dir):
    """Test that use case returns False when WDL file doesn't exist."""
    # Arrange
    non_existent = temp_dir / "nonexistent.wdl"
    output_file = temp_dir / "output.html"
    
    # Act
    result = use_case.execute(non_existent, output_file)
    
    # Assert
    assert result is False


def test_should_return_false_when_file_is_not_wdl(use_case, temp_dir):
    """Test that use case returns False when file is not a WDL file."""
    # Arrange
    text_file = temp_dir / "test.txt"
    text_file.write_text("not a wdl file")
    output_file = temp_dir / "output.html"
    
    # Act
    result = use_case.execute(text_file, output_file)
    
    # Assert
    assert result is False


@patch('src.application.use_cases.generate_workflow_graph.WDLLoader')
@patch('src.application.use_cases.generate_workflow_graph.generate_mermaid_graph')
def test_should_return_false_when_syntax_error(
    mock_generate_graph, mock_loader, use_case, sample_wdl_file, temp_dir
):
    """Test that use case returns False on syntax errors."""
    # Arrange
    mock_loader.load_wdl_file.side_effect = Exception("syntax error")
    output_file = temp_dir / "output.html"
    
    # Act
    result = use_case.execute(sample_wdl_file, output_file)
    
    # Assert
    assert result is False
    mock_generate_graph.assert_not_called()


@patch('src.application.use_cases.generate_workflow_graph.WDLLoader')
@patch('src.application.use_cases.generate_workflow_graph.generate_mermaid_graph')
def test_should_return_false_when_no_workflow_found(
    mock_generate_graph, mock_loader, use_case, sample_wdl_file, temp_dir
):
    """Test that use case returns False when no workflow is found."""
    # Arrange
    mock_doc = Mock()
    mock_doc.workflow = None
    mock_doc.imports = []
    mock_loader.load_wdl_file.return_value = mock_doc
    output_file = temp_dir / "output.html"
    
    # Act
    result = use_case.execute(sample_wdl_file, output_file)
    
    # Assert
    assert result is False
    mock_generate_graph.assert_not_called()


@patch('src.application.use_cases.generate_workflow_graph.WDLLoader')
@patch('src.application.use_cases.generate_workflow_graph.generate_mermaid_graph')
def test_should_generate_graph_successfully(
    mock_generate_graph, mock_loader, 
    use_case, sample_wdl_file, temp_dir, mock_document
):
    """Test successful graph generation."""
    # Arrange
    mock_loader.load_wdl_file.return_value = mock_document
    mock_generate_graph.return_value = "flowchart TD\n    Start --> End"
    output_file = temp_dir / "output.md"
    
    # Act
    result = use_case.execute(sample_wdl_file, output_file)
    
    # Assert
    assert result is True
    assert output_file.exists()
    
    # Check that Markdown was generated
    markdown_content = output_file.read_text()
    assert "TestWorkflow" in markdown_content
    assert "```mermaid" in markdown_content
    assert "flowchart TD" in markdown_content


@patch('src.application.use_cases.generate_workflow_graph.WDLLoader')
@patch('src.application.use_cases.generate_workflow_graph.generate_mermaid_graph')
def test_should_create_output_directory_if_not_exists(
    mock_generate_graph, mock_loader, use_case, sample_wdl_file, temp_dir, mock_document
):
    """Test that output directory is created if it doesn't exist."""
    # Arrange
    mock_loader.load_wdl_file.return_value = mock_document
    mock_generate_graph.return_value = "flowchart TD\n    Start --> End"
    output_file = temp_dir / "subdir" / "nested" / "output.html"
    
    # Act
    result = use_case.execute(sample_wdl_file, output_file)
    
    # Assert
    assert result is True
    assert output_file.exists()
    assert output_file.parent.exists()


@patch('src.application.use_cases.generate_workflow_graph.WDLLoader')
@patch('src.application.use_cases.generate_workflow_graph.generate_mermaid_graph')
def test_should_handle_empty_graph(
    mock_generate_graph, mock_loader, use_case, sample_wdl_file, temp_dir, mock_document
):
    """Test that empty graphs are handled gracefully."""
    # Arrange
    mock_loader.load_wdl_file.return_value = mock_document
    mock_generate_graph.return_value = ""  # Empty graph
    output_file = temp_dir / "output.html"
    
    # Act
    result = use_case.execute(sample_wdl_file, output_file)
    
    # Assert
    assert result is True  # Should still succeed
    assert output_file.exists()


def test_extract_workflow_from_document(use_case, mock_document):
    """Test workflow extraction from document."""
    # Arrange & Act
    workflow = use_case._extract_workflow(mock_document)
    
    # Assert
    assert workflow is not None
    assert workflow.name == "TestWorkflow"


def test_extract_workflow_from_imports(use_case):
    """Test workflow extraction from imported documents."""
    # Arrange
    mock_workflow = Mock(spec=WDL.Tree.Workflow)
    mock_workflow.name = "ImportedWorkflow"
    
    mock_import_doc = Mock()
    mock_import_doc.workflow = mock_workflow
    
    mock_import = Mock()
    mock_import.doc = mock_import_doc
    
    doc = Mock()
    doc.workflow = None
    doc.imports = [mock_import]
    
    # Act
    workflow = use_case._extract_workflow(doc)
    
    # Assert
    assert workflow is not None
    assert workflow.name == "ImportedWorkflow"


def test_extract_workflow_returns_none_when_not_found(use_case):
    """Test that None is returned when no workflow is found."""
    # Arrange
    doc = Mock()
    doc.workflow = None
    doc.imports = []
    
    # Act
    workflow = use_case._extract_workflow(doc)
    
    # Assert
    assert workflow is None


def test_render_markdown_contains_required_elements(use_case):
    """Test that rendered Markdown contains required elements."""
    # Arrange
    workflow_name = "MyWorkflow"
    mermaid_graph = "flowchart TD\n    A --> B"
    wdl_file = Path("/path/to/workflow.wdl")
    
    # Act
    markdown = use_case._render_markdown(workflow_name, mermaid_graph, wdl_file)
    
    # Assert
    assert workflow_name in markdown
    assert "```mermaid" in markdown
    assert mermaid_graph in markdown
    assert str(wdl_file) in markdown
    assert "# " in markdown  # Has heading


def test_save_markdown_creates_file(use_case, temp_dir):
    """Test that Markdown is saved to file."""
    # Arrange
    output_file = temp_dir / "test.md"
    markdown_content = "# Test\n\n```mermaid\nflowchart TD\n```"
    
    # Act
    use_case._save_markdown(output_file, markdown_content)
    
    # Assert
    assert output_file.exists()
    assert output_file.read_text() == markdown_content
