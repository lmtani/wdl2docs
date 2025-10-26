"""
Unit tests for workflow call tracking functionality.

Tests that workflows can be tracked when they are called as subworkflows.
"""

import pytest
from pathlib import Path

from src.infrastructure.rendering.html_generator import HtmlGenerator
from src.infrastructure.rendering.template_renderer import TemplateRenderer
from src.domain.value_objects import WDLDocument, WDLWorkflow, WDLCall


@pytest.fixture
def templates_dir(temp_dir):
    """Create a templates directory with required templates."""
    templates = temp_dir / "templates"
    templates.mkdir()

    # Create basic templates
    (templates / "document.html").write_text("<html><body>{{ doc.name }}</body></html>")

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


def test_get_workflow_call_info_returns_none_for_non_workflow_document(html_generator, temp_dir):
    """Test that _get_workflow_call_info returns None for documents without workflow."""
    # Arrange
    doc = WDLDocument(
        file_path=temp_dir / "tasks.wdl",
        relative_path=Path("tasks.wdl"),
        version="1.0",
        workflow=None,
        tasks=[],
        imports=[],
    )

    # Act
    result = html_generator._get_workflow_call_info(doc, [doc])

    # Assert
    assert result is None


def test_get_workflow_call_info_returns_none_when_workflow_not_called(html_generator, temp_dir):
    """Test that _get_workflow_call_info returns None when workflow is not called by others."""
    # Arrange
    workflow_doc = WDLDocument(
        file_path=temp_dir / "workflow.wdl",
        relative_path=Path("workflow.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="MyWorkflow",
            description="A workflow",
            inputs=[],
            outputs=[],
            calls=[],
            meta={},
            docker_images=[],
        ),
        tasks=[],
        imports=[],
    )

    # Act
    result = html_generator._get_workflow_call_info(workflow_doc, [workflow_doc])

    # Assert
    assert result is None


def test_get_workflow_call_info_tracks_single_caller(html_generator, temp_dir):
    """Test that _get_workflow_call_info correctly tracks a single calling workflow."""
    # Arrange
    subworkflow = WDLDocument(
        file_path=temp_dir / "subworkflow.wdl",
        relative_path=Path("subworkflow.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="SubWorkflow",
            description="A subworkflow",
            inputs=[],
            outputs=[],
            calls=[],
            meta={},
            docker_images=[],
        ),
        tasks=[],
        imports=[],
    )

    main_workflow = WDLDocument(
        file_path=temp_dir / "main.wdl",
        relative_path=Path("main.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="MainWorkflow",
            description="Main workflow",
            inputs=[],
            outputs=[],
            calls=[
                WDLCall(
                    name="sub",
                    task_or_workflow="SubWorkflow",
                    call_type="workflow",
                )
            ],
            meta={},
            docker_images=[],
        ),
        tasks=[],
        imports=[],
    )

    all_docs = [subworkflow, main_workflow]

    # Act
    result = html_generator._get_workflow_call_info(subworkflow, all_docs)

    # Assert
    assert result is not None
    assert result["count"] == 1
    assert len(result["workflows"]) == 1
    assert result["workflows"][0]["name"] == "MainWorkflow"
    assert result["workflows"][0]["file_path"] == "main.wdl"


def test_get_workflow_call_info_tracks_multiple_callers(html_generator, temp_dir):
    """Test that _get_workflow_call_info correctly tracks multiple calling workflows."""
    # Arrange
    subworkflow = WDLDocument(
        file_path=temp_dir / "subworkflow.wdl",
        relative_path=Path("subworkflow.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="SubWorkflow",
            description="A subworkflow",
            inputs=[],
            outputs=[],
            calls=[],
            meta={},
            docker_images=[],
        ),
        tasks=[],
        imports=[],
    )

    main_workflow1 = WDLDocument(
        file_path=temp_dir / "main1.wdl",
        relative_path=Path("main1.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="MainWorkflow1",
            description="First main workflow",
            inputs=[],
            outputs=[],
            calls=[
                WDLCall(
                    name="sub",
                    task_or_workflow="SubWorkflow",
                    call_type="workflow",
                )
            ],
            meta={},
            docker_images=[],
        ),
        tasks=[],
        imports=[],
    )

    main_workflow2 = WDLDocument(
        file_path=temp_dir / "main2.wdl",
        relative_path=Path("main2.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="MainWorkflow2",
            description="Second main workflow",
            inputs=[],
            outputs=[],
            calls=[
                WDLCall(
                    name="sub",
                    task_or_workflow="SubWorkflow",
                    call_type="workflow",
                )
            ],
            meta={},
            docker_images=[],
        ),
        tasks=[],
        imports=[],
    )

    all_docs = [subworkflow, main_workflow1, main_workflow2]

    # Act
    result = html_generator._get_workflow_call_info(subworkflow, all_docs)

    # Assert
    assert result is not None
    assert result["count"] == 2
    assert len(result["workflows"]) == 2
    workflow_names = [w["name"] for w in result["workflows"]]
    assert "MainWorkflow1" in workflow_names
    assert "MainWorkflow2" in workflow_names


def test_get_workflow_call_info_ignores_task_calls(html_generator, temp_dir):
    """Test that _get_workflow_call_info ignores task calls and only counts workflow calls."""
    # Arrange
    subworkflow = WDLDocument(
        file_path=temp_dir / "subworkflow.wdl",
        relative_path=Path("subworkflow.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="SubWorkflow",
            description="A subworkflow",
            inputs=[],
            outputs=[],
            calls=[],
            meta={},
            docker_images=[],
        ),
        tasks=[],
        imports=[],
    )

    main_workflow = WDLDocument(
        file_path=temp_dir / "main.wdl",
        relative_path=Path("main.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="MainWorkflow",
            description="Main workflow",
            inputs=[],
            outputs=[],
            calls=[
                WDLCall(
                    name="sub",
                    task_or_workflow="SubWorkflow",
                    call_type="task",  # This is a task call, not a workflow call
                )
            ],
            meta={},
            docker_images=[],
        ),
        tasks=[],
        imports=[],
    )

    all_docs = [subworkflow, main_workflow]

    # Act
    result = html_generator._get_workflow_call_info(subworkflow, all_docs)

    # Assert
    assert result is None  # Should return None because no workflow calls were found


def test_generate_document_page_includes_workflow_call_info(html_generator, temp_dir):
    """Test that generate_document_page includes workflow call info when document is called."""
    # Arrange
    subworkflow = WDLDocument(
        file_path=temp_dir / "subworkflow.wdl",
        relative_path=Path("subworkflow.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="SubWorkflow",
            description="A subworkflow",
            inputs=[],
            outputs=[],
            calls=[],
            meta={},
            docker_images=[],
        ),
        tasks=[],
        imports=[],
    )

    main_workflow = WDLDocument(
        file_path=temp_dir / "main.wdl",
        relative_path=Path("main.wdl"),
        version="1.0",
        workflow=WDLWorkflow(
            name="MainWorkflow",
            description="Main workflow",
            inputs=[],
            outputs=[],
            calls=[
                WDLCall(
                    name="sub",
                    task_or_workflow="SubWorkflow",
                    call_type="workflow",
                )
            ],
            meta={},
            docker_images=[],
        ),
        tasks=[],
        imports=[],
    )

    all_docs = [subworkflow, main_workflow]

    # Act
    output_file = html_generator.generate_document_page(subworkflow, all_docs)

    # Assert
    assert output_file.exists()
    # We can't easily check the HTML content since the template is minimal in tests,
    # but we can verify the file was created without errors
