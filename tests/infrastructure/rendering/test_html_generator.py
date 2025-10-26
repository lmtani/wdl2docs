"""
Unit tests for HtmlGenerator infrastructure component.

Tests the HTML file generation functionality, including:
- Document page generation
- Index page generation
- Docker images page generation
- Graph page generation
"""

import pytest
from pathlib import Path

from src.infrastructure.rendering.html_generator import HtmlGenerator
from src.infrastructure.rendering.template_renderer import TemplateRenderer
from src.domain.value_objects import (
    WDLDocument,
    WDLWorkflow,
    WDLTask,
    WDLCommand,
)
from src.domain.errors import ParseError


@pytest.fixture
def templates_dir(temp_dir):
    """Create a templates directory with required templates."""
    templates = temp_dir / "templates"
    templates.mkdir()

    # Create basic templates
    (templates / "document.html").write_text("<html><body>{{ doc.name }}</body></html>")
    (templates / "index.html").write_text("<html><body>Index</body></html>")
    (templates / "docker_images.html").write_text("<html><body>Docker Images</body></html>")
    (templates / "graph.html").write_text("<html><body>Graph</body></html>")

    return templates


@pytest.fixture
def template_renderer(templates_dir, temp_dir):
    """Create a TemplateRenderer instance."""
    return TemplateRenderer(templates_dir=templates_dir, root_path=temp_dir)


@pytest.fixture
def html_generator(temp_dir, template_renderer):
    """Create an HtmlGenerator instance."""
    output_dir = temp_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return HtmlGenerator(output_dir=output_dir, renderer=template_renderer)


@pytest.fixture
def sample_wdl_document(temp_dir):
    """Create a sample WDLDocument for testing."""
    return WDLDocument(
        file_path=temp_dir / "workflow.wdl",
        relative_path=Path("workflow.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="TestWorkflow",
            description="A test workflow",
            inputs=[],
            outputs=[],
            calls=[],
            meta={},
            docker_images=[],
            mermaid_graph="graph TD;\nA-->B;",
        ),
        tasks=[],
        imports=[],
        source_code="version 1.0\nworkflow TestWorkflow {}",
    )


@pytest.fixture
def sample_wdl_document_with_tasks(temp_dir):
    """Create a sample WDLDocument with tasks."""
    return WDLDocument(
        file_path=temp_dir / "tasks.wdl",
        relative_path=Path("tasks.wdl"),
        version="1.0",
        workflow=None,
        tasks=[
            WDLTask(
                name="TestTask",
                description="A test task",
                inputs=[],
                outputs=[],
                command=WDLCommand(raw_command="echo test", formatted_command="echo test"),
                runtime={},
                meta={},
            )
        ],
        imports=[],
        source_code="version 1.0\ntask TestTask {}",
    )


def should_initialize_with_output_dir_and_renderer(temp_dir, template_renderer):
    """Test that HtmlGenerator initializes with correct parameters."""
    # Arrange
    output_dir = temp_dir / "output"

    # Act
    generator = HtmlGenerator(output_dir=output_dir, renderer=template_renderer)

    # Assert
    assert generator.output_dir == output_dir
    assert generator.renderer == template_renderer


def should_generate_document_page_for_workflow(html_generator, sample_wdl_document):
    """Test generating HTML page for a workflow document."""
    # Arrange
    doc = sample_wdl_document

    # Act
    result_path = html_generator.generate_document_page(doc)

    # Assert
    assert result_path.exists()
    assert result_path.name == "workflow.html"
    content = result_path.read_text()
    assert "TestWorkflow" in content


def should_generate_document_page_for_tasks(html_generator, sample_wdl_document_with_tasks):
    """Test generating HTML page for a tasks document."""
    # Arrange
    doc = sample_wdl_document_with_tasks

    # Act
    result_path = html_generator.generate_document_page(doc)

    # Assert
    assert result_path.exists()
    assert result_path.name == "tasks.html"


def should_create_output_directory_structure(html_generator, temp_dir):
    """Test that output directories are created as needed."""
    # Arrange
    doc = WDLDocument(
        file_path=temp_dir / "deep" / "nested" / "workflow.wdl",
        relative_path=Path("deep/nested/workflow.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="NestedWorkflow",
            description="A nested workflow",
            inputs=[],
            outputs=[],
            calls=[],
            meta={},
            docker_images=[],
            mermaid_graph="",
        ),
        tasks=[],
        imports=[],
        source_code="version 1.0\nworkflow NestedWorkflow {}",
    )

    # Act
    result_path = html_generator.generate_document_page(doc)

    # Assert
    assert result_path.exists()
    assert result_path.parent.exists()
    assert result_path.parent.name == "nested"


def should_generate_graph_page_when_workflow_has_graph(html_generator, sample_wdl_document):
    """Test generating separate graph page for workflow with graph."""
    # Arrange
    doc = sample_wdl_document

    # Act
    doc_path = html_generator.generate_document_page(doc)

    # Assert
    graph_path = doc_path.parent / "workflow-graph.html"
    assert graph_path.exists()
    content = graph_path.read_text()
    assert "Graph" in content


def should_not_generate_graph_page_when_workflow_has_no_graph(html_generator, temp_dir):
    """Test that graph page is not generated when workflow has no graph."""
    # Arrange
    doc = WDLDocument(
        file_path=temp_dir / "no_graph.wdl",
        relative_path=Path("no_graph.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="NoGraphWorkflow",
            description="A workflow without graph",
            inputs=[],
            outputs=[],
            calls=[],
            meta={},
            docker_images=[],
            mermaid_graph="",  # Empty graph
        ),
        tasks=[],
        imports=[],
        source_code="version 1.0\nworkflow NoGraphWorkflow {}",
    )

    # Act
    doc_path = html_generator.generate_document_page(doc)

    # Assert
    graph_path = doc_path.parent / "no_graph-graph.html"
    assert not graph_path.exists()


def should_generate_index_page(html_generator, sample_wdl_document):
    """Test generating main index.html page."""
    # Arrange
    documents = [sample_wdl_document]

    # Act
    index_path = html_generator.generate_index(documents)

    # Assert
    assert index_path.exists()
    assert index_path.name == "index.html"
    content = index_path.read_text()
    assert "Index" in content


def should_generate_index_page_with_parse_errors(html_generator, sample_wdl_document):
    """Test generating index page with parse errors."""
    # Arrange
    documents = [sample_wdl_document]
    parse_errors = [
        ParseError(
            file_path=Path("error.wdl"),
            relative_path=Path("error.wdl"),
            error_type="SyntaxError",
            error_message="Invalid syntax",
            line_number=1,
            column_number=10,
        )
    ]

    # Act
    index_path = html_generator.generate_index(documents, parse_errors)

    # Assert
    assert index_path.exists()


def should_generate_docker_images_page(html_generator, sample_wdl_document):
    """Test generating Docker images inventory page."""
    # Arrange
    documents = [sample_wdl_document]

    # Act
    docker_path = html_generator.generate_docker_images_page(documents)

    # Assert
    assert docker_path.exists()
    assert docker_path.name == "docker_images.html"
    content = docker_path.read_text()
    assert "Docker Images" in content


def should_organize_documents_by_type_in_index_context(html_generator):
    """Test that documents are organized correctly in index context."""
    # Arrange
    workflow_doc = WDLDocument(
        file_path=Path("workflow.wdl"),
        relative_path=Path("workflow.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="TestWorkflow",
            description="A workflow",
            inputs=[],
            outputs=[],
            calls=[],
            meta={},
            docker_images=[],
            mermaid_graph="",
        ),
        tasks=[],
        imports=[],
        source_code="",
    )

    task_doc = WDLDocument(
        file_path=Path("tasks.wdl"),
        relative_path=Path("tasks.wdl"),
        version="1.0",
        workflow=None,
        tasks=[
            WDLTask(
                name="TestTask",
                description="A task",
                inputs=[],
                outputs=[],
                command=WDLCommand(raw_command="echo test", formatted_command="echo test"),
                runtime={},
                meta={},
            )
        ],
        imports=[],
        source_code="",
    )

    mixed_doc = WDLDocument(
        file_path=Path("mixed.wdl"),
        relative_path=Path("mixed.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="MixedWorkflow",
            description="A mixed document",
            inputs=[],
            outputs=[],
            calls=[],
            meta={},
            docker_images=[],
            mermaid_graph="",
        ),
        tasks=[
            WDLTask(
                name="MixedTask",
                description="A task in mixed document",
                inputs=[],
                outputs=[],
                command=WDLCommand(raw_command="echo test", formatted_command="echo test"),
                runtime={},
                meta={},
            )
        ],
        imports=[],
        source_code="",
    )

    documents = [workflow_doc, task_doc, mixed_doc]

    # Act
    context = html_generator._prepare_index_context(documents, [])

    # Assert
    assert len(context["workflows"]) == 1
    assert len(context["task_files"]) == 1
    assert len(context["mixed_files"]) == 1
    assert context["total_workflows"] == 2  # workflow + mixed
    assert context["total_tasks"] == 2  # task in mixed + task file
    assert context["total_files"] == 3
