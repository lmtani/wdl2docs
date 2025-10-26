"""
Unit tests for AssetCopier infrastructure component.

Tests the asset copying functionality, including:
- Static asset copying
- Directory creation
- Error handling for missing source
"""

import pytest
from unittest.mock import patch

from src.infrastructure.templating.asset_copier import AssetCopier


@pytest.fixture
def templates_dir(temp_dir):
    """Create a templates directory with static assets."""
    templates = temp_dir / "templates"
    static_dir = templates / "static"
    static_dir.mkdir(parents=True)

    # Create some sample assets
    (static_dir / "style.css").write_text("body { color: blue; }")
    (static_dir / "script.js").write_text("console.log('hello');")

    return templates


@pytest.fixture
def asset_copier(templates_dir):
    """Create an AssetCopier instance."""
    return AssetCopier(templates_dir=templates_dir)


@pytest.fixture
def mocked_asset_copier(asset_copier):
    """Create an AssetCopier instance with mocked shutil functions."""
    with (
        patch("src.infrastructure.templating.asset_copier.shutil.copytree") as mock_copytree,
        patch("src.infrastructure.templating.asset_copier.shutil.rmtree") as mock_rmtree,
    ):
        asset_copier._mock_copytree = mock_copytree
        asset_copier._mock_rmtree = mock_rmtree
        yield asset_copier


def should_initialize_with_default_static_dir_name(templates_dir):
    """Test that AssetCopier initializes with default static directory name."""
    # Arrange & Act
    copier = AssetCopier(templates_dir=templates_dir)

    # Assert
    assert copier.templates_dir == templates_dir
    assert copier.static_dir_name == "static"
    assert copier.source_static_dir == templates_dir / "static"


def should_initialize_with_custom_static_dir_name(templates_dir):
    """Test that AssetCopier accepts custom static directory name."""
    # Arrange
    custom_name = "assets"

    # Act
    copier = AssetCopier(templates_dir=templates_dir, static_dir_name=custom_name)

    # Assert
    assert copier.static_dir_name == custom_name
    assert copier.source_static_dir == templates_dir / custom_name


def should_copy_static_assets_when_source_exists(mocked_asset_copier, temp_dir):
    """Test successful copying of static assets using mocked fixture."""
    # Arrange
    output_dir = temp_dir / "output"
    output_dir.mkdir()
    target_static_dir = output_dir / "static"

    # Act
    mocked_asset_copier.copy_static_assets(output_dir)

    # Assert
    mocked_asset_copier._mock_copytree.assert_called_once_with(mocked_asset_copier.source_static_dir, target_static_dir)


def should_remove_existing_target_directory_before_copying(mocked_asset_copier, temp_dir):
    """Test that existing target directory is removed before copying."""
    # Arrange
    output_dir = temp_dir / "output"
    output_dir.mkdir()
    target_static_dir = output_dir / "static"
    target_static_dir.mkdir()  # Create existing directory

    # Act
    mocked_asset_copier.copy_static_assets(output_dir)

    # Assert
    mocked_asset_copier._mock_rmtree.assert_called_once_with(target_static_dir)
    mocked_asset_copier._mock_copytree.assert_called_once_with(mocked_asset_copier.source_static_dir, target_static_dir)


def should_raise_error_when_source_directory_does_not_exist(temp_dir):
    """Test that FileNotFoundError is raised when source static directory doesn't exist."""
    # Arrange
    templates_dir = temp_dir / "templates"
    templates_dir.mkdir()
    # Don't create static directory
    copier = AssetCopier(templates_dir=templates_dir)
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Act & Assert
    with pytest.raises(FileNotFoundError) as exc_info:
        copier.copy_static_assets(output_dir)

    assert "Could not find static directory" in str(exc_info.value)
    assert str(copier.source_static_dir) in str(exc_info.value)


def should_copy_assets_to_correct_target_directory(mocked_asset_copier, temp_dir):
    """Test that assets are copied to the correct target directory."""
    # Arrange
    templates_dir = temp_dir / "templates"
    static_dir = templates_dir / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    (static_dir / "test.css").write_text("test")

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    mocked_asset_copier.templates_dir = templates_dir
    expected_target = output_dir / "static"

    # Act
    mocked_asset_copier.copy_static_assets(output_dir)

    # Assert
    mocked_asset_copier._mock_copytree.assert_called_once_with(static_dir, expected_target)


def should_use_custom_static_directory_name(mocked_asset_copier, temp_dir):
    """Test that custom static directory name is used correctly."""
    # Arrange
    templates_dir = temp_dir / "templates"
    assets_dir = templates_dir / "assets"  # Custom name
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "test.css").write_text("test")

    output_dir = temp_dir / "output"
    output_dir.mkdir()

    copier = AssetCopier(templates_dir=templates_dir, static_dir_name="assets")
    expected_target = output_dir / "assets"

    # Act
    copier.copy_static_assets(output_dir)

    # Assert
    mocked_asset_copier._mock_copytree.assert_called_once_with(assets_dir, expected_target)
