"""
Unit tests for TemplateRenderer infrastructure component.

Tests the Jinja2 template rendering functionality, including:
- Template rendering
- Custom filters
- Path normalization
- Relative link calculation
"""

import pytest
from pathlib import Path

from src.infrastructure.rendering.template_renderer import TemplateRenderer


@pytest.fixture
def templates_dir(temp_dir):
    """Create a templates directory with sample templates."""
    templates = temp_dir / "templates"
    templates.mkdir()

    # Create a simple template
    template_file = templates / "test.html"
    template_file.write_text("<html><body>{{ content }}</body></html>")

    return templates


@pytest.fixture
def template_renderer(templates_dir, temp_dir):
    """Create a TemplateRenderer instance."""
    return TemplateRenderer(templates_dir=templates_dir, root_path=temp_dir)


def should_initialize_with_templates_dir_and_root_path(templates_dir, temp_dir):
    """Test that TemplateRenderer initializes with correct paths."""
    # Arrange & Act
    renderer = TemplateRenderer(templates_dir=templates_dir, root_path=temp_dir)

    # Assert
    assert renderer.templates_dir == templates_dir
    assert renderer.root_path == temp_dir
    assert renderer.env is not None


def should_render_template_with_context(templates_dir, temp_dir):
    """Test template rendering with context variables."""
    # Arrange
    renderer = TemplateRenderer(templates_dir=templates_dir, root_path=temp_dir)
    context = {"content": "Hello World"}

    # Act
    result = renderer.render_template("test.html", context)

    # Assert
    assert "<html><body>Hello World</body></html>" == result


def should_get_template_by_name(templates_dir, temp_dir):
    """Test getting a template object by name."""
    # Arrange
    renderer = TemplateRenderer(templates_dir=templates_dir, root_path=temp_dir)

    # Act
    template = renderer.get_template("test.html")

    # Assert
    assert template is not None
    assert template.name == "test.html"


def should_apply_basename_filter(template_renderer):
    """Test the basename custom filter."""
    # Arrange
    path = Path("workflows/v1/main.wdl")

    # Act
    result = template_renderer.env.filters["basename"](path)

    # Assert
    assert result == "main.wdl"


def should_apply_parent_filter(template_renderer):
    """Test the parent custom filter."""
    # Arrange
    path = Path("workflows/v1/main.wdl")

    # Act
    result = template_renderer.env.filters["parent"](path)

    # Assert
    assert result == Path("workflows/v1")


def should_apply_relpath_filter(template_renderer, temp_dir):
    """Test the relpath custom filter."""
    # Arrange
    file_path = temp_dir / "workflows" / "main.wdl"

    # Act
    result = template_renderer.env.filters["relpath"](file_path)

    # Assert
    assert result == "workflows/main.wdl"


def should_apply_normalize_path_filter(template_renderer):
    """Test the normalize_path custom filter."""
    # Arrange
    path = Path("workflows/../workflows/main.wdl")

    # Act
    result = template_renderer.env.filters["normalize_path"](path)

    # Assert
    assert result == "workflows/main.wdl"


def should_apply_safe_code_filter(template_renderer):
    """Test the safe_code custom filter."""
    # Arrange
    code = "<script>alert('test')</script>"

    # Act
    result = template_renderer.env.filters["safe_code"](code)

    # Assert
    assert result == code  # Should be marked as safe


def should_apply_safe_code_filter_to_none(template_renderer):
    """Test the safe_code filter with None input."""
    # Arrange & Act
    result = template_renderer.env.filters["safe_code"](None)

    # Assert
    assert result == ""


def should_calculate_relative_link_from_nested_path(template_renderer):
    """Test relative link calculation from nested path."""
    # Arrange
    target_path = "subworkflows/v1/bam_processing.html"
    from_path = "workflows/v1/illumina/ngs/exome/SingleSampleGenotyping.wdl"

    # Act
    result = template_renderer.env.filters["relative_link"](target_path, from_path)

    # Assert
    assert result == "../../../../../subworkflows/v1/bam_processing.html"


def should_calculate_relative_link_from_root_path(template_renderer):
    """Test relative link calculation from root path."""
    # Arrange
    target_path = "workflows/main.html"
    from_path = "main.wdl"

    # Act
    result = template_renderer.env.filters["relative_link"](target_path, from_path)

    # Assert
    # From root level, no "../" prefix should be added
    assert result == "workflows/main.html"


def should_calculate_relative_link_to_external_from_root(template_renderer):
    """Test relative link to external directory from root-level file."""
    # Arrange
    target_path = "external/vendor/lib.html"
    from_path = "main.wdl"

    # Act
    result = template_renderer.env.filters["relative_link"](target_path, from_path)

    # Assert
    # From root level, path should be direct without "../" prefix
    assert result == "external/vendor/lib.html"


def should_normalize_external_path(template_renderer):
    """Test path normalization for external files."""
    # Arrange
    path = Path("external/vendor/lib.wdl")

    # Act
    result = template_renderer._normalize_path(path)

    # Assert
    assert result == Path("external/vendor/lib.wdl")


def should_normalize_path_with_dots(template_renderer):
    """Test path normalization with .. references."""
    # Arrange
    path = Path("workflows/../workflows/main.wdl")

    # Act
    result = template_renderer._normalize_path(path)

    # Assert
    assert result == Path("workflows/main.wdl")


def should_normalize_simple_path(template_renderer):
    """Test path normalization for simple paths."""
    # Arrange
    path = Path("workflows/main.wdl")

    # Act
    result = template_renderer._normalize_path(path)

    # Assert
    assert result == Path("workflows/main.wdl")
