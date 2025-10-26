"""
Unit tests for domain entities.

Tests the domain entities including WDLDockerImage.
"""

from src.domain.entitites import WDLDockerImage


def should_initialize_wdl_docker_image_with_required_fields():
    """Test WDLDockerImage initialization with required fields."""
    # Arrange & Act
    image = WDLDockerImage(image="ubuntu:20.04")

    # Assert
    assert image.image == "ubuntu:20.04"
    assert image.task_names == []
    assert image.is_parameterized is False
    assert image.parameter_name is None
    assert image.default_value is None


def should_initialize_wdl_docker_image_with_all_fields():
    """Test WDLDockerImage initialization with all fields."""
    # Arrange
    task_names = ["task1", "task2"]
    parameter_name = "docker_image"
    default_value = "ubuntu:20.04"

    # Act
    image = WDLDockerImage(
        image="ubuntu:latest",
        task_names=task_names,
        is_parameterized=True,
        parameter_name=parameter_name,
        default_value=default_value,
    )

    # Assert
    assert image.image == "ubuntu:latest"
    assert image.task_names == task_names
    assert image.is_parameterized is True
    assert image.parameter_name == parameter_name
    assert image.default_value == default_value


def should_return_image_as_display_image_for_non_parameterized():
    """Test display_image property for non-parameterized images."""
    # Arrange
    image = WDLDockerImage(image="ubuntu:20.04")

    # Act & Assert
    assert image.display_image == "ubuntu:20.04"


def should_return_default_value_as_display_image_for_parameterized_with_default():
    """Test display_image property for parameterized images with default value."""
    # Arrange
    image = WDLDockerImage(
        image="ubuntu:latest", is_parameterized=True, parameter_name="docker_img", default_value="ubuntu:20.04"
    )

    # Act & Assert
    assert image.display_image == "ubuntu:20.04"


def should_return_parameterized_message_for_parameterized_without_default():
    """Test display_image property for parameterized images without default value."""
    # Arrange
    image = WDLDockerImage(image="ubuntu:latest", is_parameterized=True, parameter_name="docker_img")

    # Act & Assert
    assert image.display_image == "Parameterized (via docker_img)"


def should_return_generic_parameterized_message_for_parameterized_without_name():
    """Test display_image property for parameterized images without parameter name."""
    # Arrange
    image = WDLDockerImage(image="ubuntu:latest", is_parameterized=True)

    # Act & Assert
    assert image.display_image == "Parameterized"


def should_return_short_name_for_simple_image():
    """Test short_name property for simple image names."""
    # Arrange
    image = WDLDockerImage(image="ubuntu:20.04")

    # Act & Assert
    assert image.short_name == "ubuntu"


def should_return_short_name_for_image_with_registry():
    """Test short_name property for images with registry."""
    # Arrange
    image = WDLDockerImage(image="quay.io/biocontainers/samtools:1.15")

    # Act & Assert
    assert image.short_name == "samtools"


def should_return_short_name_for_parameterized_with_default():
    """Test short_name property for parameterized images with default value."""
    # Arrange
    image = WDLDockerImage(
        image="ubuntu:latest", is_parameterized=True, default_value="quay.io/biocontainers/samtools:1.15"
    )

    # Act & Assert
    assert image.short_name == "samtools"


def should_return_parameterized_short_name_for_parameterized_without_default():
    """Test short_name property for parameterized images without default value."""
    # Arrange
    image = WDLDockerImage(image="ubuntu:latest", is_parameterized=True)

    # Act & Assert
    assert image.short_name == "parameterized"


def should_return_task_count():
    """Test task_count property."""
    # Arrange
    image = WDLDockerImage(image="ubuntu:20.04", task_names=["task1", "task2", "task3"])

    # Act & Assert
    assert image.task_count == 3


def should_return_zero_task_count_for_empty_list():
    """Test task_count property with empty task list."""
    # Arrange
    image = WDLDockerImage(image="ubuntu:20.04")

    # Act & Assert
    assert image.task_count == 0
