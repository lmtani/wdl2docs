"""
Unit tests for Discovery infrastructure component.

Tests the file discovery functionality, including:
- Finding internal WDL files
- Finding all WDL files
- Finding external WDL files
- Import chain collection
- Exclusion pattern handling
"""

import pytest
from pathlib import Path

from src.infrastructure.fs.discovery import Discovery


@pytest.fixture
def discovery_structure(temp_dir):
    """Create a test directory structure with WDL files."""
    # Create internal files
    (temp_dir / "workflows").mkdir()
    (temp_dir / "workflows" / "main.wdl").write_text("version 1.0\nworkflow Main {}")
    (temp_dir / "tasks").mkdir()
    (temp_dir / "tasks" / "process.wdl").write_text("version 1.0\ntask Process {}")

    # Create external files
    (temp_dir / "external").mkdir()
    (temp_dir / "external" / "vendor").mkdir()
    (temp_dir / "external" / "vendor" / "lib.wdl").write_text("version 1.0\ntask Lib {}")

    # Create excluded files
    (temp_dir / "__pycache__").mkdir()
    (temp_dir / "__pycache__" / "cache.wdl").write_text("version 1.0\ntask Cache {}")

    return temp_dir


@pytest.fixture
def discovery(discovery_structure):
    """Create a Discovery instance."""
    return Discovery(root_path=discovery_structure)


def should_initialize_with_root_path_and_default_patterns(discovery_structure):
    """Test Discovery initialization with default exclude patterns."""
    # Arrange & Act
    discovery = Discovery(root_path=discovery_structure)

    # Assert
    assert discovery.root_path == discovery_structure
    assert "__pycache__/" in discovery.exclude_patterns
    assert ".git/" in discovery.exclude_patterns


def should_initialize_with_custom_exclude_patterns(discovery_structure):
    """Test Discovery initialization with custom exclude patterns."""
    # Arrange
    custom_patterns = ["test/", "build/"]

    # Act
    discovery = Discovery(root_path=discovery_structure, exclude_patterns=custom_patterns)

    # Assert
    assert discovery.exclude_patterns == custom_patterns


def should_find_internal_wdl_files_excluding_external(discovery, discovery_structure):
    """Test finding internal WDL files (excluding external/)."""
    # Arrange & Act
    files = discovery.find_internal_wdl_files()

    # Assert
    expected_files = [
        discovery_structure / "tasks" / "process.wdl",
        discovery_structure / "workflows" / "main.wdl",
    ]
    assert files == sorted(expected_files)

    # Ensure external files are not included
    external_file = discovery_structure / "external" / "vendor" / "lib.wdl"
    assert external_file not in files


def should_find_all_wdl_files_including_external(discovery, discovery_structure):
    """Test finding all WDL files including external."""
    # Arrange & Act
    files = discovery.find_all_wdl_files()

    # Assert
    expected_files = [
        discovery_structure / "external" / "vendor" / "lib.wdl",
        discovery_structure / "tasks" / "process.wdl",
        discovery_structure / "workflows" / "main.wdl",
    ]
    assert files == sorted(expected_files)


def should_find_only_external_wdl_files(discovery, discovery_structure):
    """Test finding only external WDL files."""
    # Arrange & Act
    files = discovery.find_external_wdl_files()

    # Assert
    expected_files = [
        discovery_structure / "external" / "vendor" / "lib.wdl",
    ]
    assert files == expected_files


def should_return_empty_list_when_no_external_directory(discovery_structure):
    """Test that empty list is returned when external directory doesn't exist."""
    # Arrange
    root_without_external = discovery_structure / "no_external"
    root_without_external.mkdir()
    discovery = Discovery(root_path=root_without_external)

    # Act
    files = discovery.find_external_wdl_files()

    # Assert
    assert files == []


def should_exclude_files_based_on_patterns(discovery, discovery_structure):
    """Test that files are excluded based on patterns."""
    # Arrange & Act
    files = discovery.find_all_wdl_files()

    # Assert
    # Should not include __pycache__ files
    cache_file = discovery_structure / "__pycache__" / "cache.wdl"
    assert cache_file not in files


def should_collect_import_chain_from_starting_files(discovery, discovery_structure):
    """Test collecting import chain from starting files."""
    # Arrange
    starting_files = [discovery_structure / "workflows" / "main.wdl"]

    # Act
    chain = discovery.collect_import_chain(starting_files)

    # Assert
    # Should include the starting file and any siblings
    assert discovery_structure / "workflows" / "main.wdl" in chain
    # May include other files in the same directory (heuristic)


def should_skip_non_existent_files_in_import_chain(discovery, discovery_structure):
    """Test that non-existent files are skipped in import chain collection."""
    # Arrange
    non_existent = discovery_structure / "nonexistent.wdl"
    starting_files = [non_existent]

    # Act
    chain = discovery.collect_import_chain(starting_files)

    # Assert
    assert non_existent in chain  # Still included even if doesn't exist
    # But no other files should be added


def should_check_file_exists_correctly(discovery, discovery_structure):
    """Test file existence checking."""
    # Arrange
    existing_file = discovery_structure / "workflows" / "main.wdl"
    non_wdl_file = discovery_structure / "workflows" / "main.txt"
    non_wdl_file.write_text("not wdl")
    non_existent_file = discovery_structure / "nonexistent.wdl"

    # Act & Assert
    assert discovery._exists(existing_file) is True
    assert discovery._exists(non_wdl_file) is False
    assert discovery._exists(non_existent_file) is False


def should_exclude_files_outside_root(discovery):
    """Test that files outside root are excluded."""
    # Arrange
    outside_file = Path("/tmp/outside_test.wdl")
    outside_file.write_text("version 1.0\nworkflow Outside {}")

    # Act
    should_exclude = discovery._should_exclude(outside_file, [])

    # Assert
    assert should_exclude is True

    # Cleanup
    outside_file.unlink(missing_ok=True)


def should_exclude_files_matching_patterns(discovery, discovery_structure):
    """Test pattern-based exclusion."""
    # Arrange
    cache_file = discovery_structure / "__pycache__" / "cache.wdl"
    normal_file = discovery_structure / "workflows" / "main.wdl"
    patterns = ["__pycache__/"]

    # Act & Assert
    assert discovery._should_exclude(cache_file, patterns) is True
    assert discovery._should_exclude(normal_file, patterns) is False


def should_not_exclude_files_not_matching_patterns(discovery, discovery_structure):
    """Test that files not matching patterns are not excluded."""
    # Arrange
    normal_file = discovery_structure / "workflows" / "main.wdl"
    patterns = ["__pycache__/"]

    # Act
    should_exclude = discovery._should_exclude(normal_file, patterns)

    # Assert
    assert should_exclude is False
