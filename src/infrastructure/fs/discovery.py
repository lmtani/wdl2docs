"""
Discovery - File System Adapter

Responsible for recursive scanning and discovery of WDL files.
"""

import logging
from pathlib import Path
from typing import List, Set, Optional

logger = logging.getLogger(__name__)


class Discovery:
    """
    File discovery operations for WDL files.

    Handles recursive scanning of directories to find WDL files
    while respecting exclusion patterns.
    """

    def __init__(self, root_path: Path, exclude_patterns: Optional[List[str]] = None):
        """
        Initialize the discovery service.

        Args:
            root_path: Root directory to scan
            exclude_patterns: Patterns to exclude from search
        """
        self.root_path = root_path
        self.exclude_patterns = exclude_patterns or ["__pycache__/", ".git/"]

    def find_internal_wdl_files(self) -> List[Path]:
        """
        Find all internal WDL files (excluding external/ directory).

        Internal files are those that belong to the project itself,
        not third-party dependencies.

        Returns:
            Sorted list of Path objects for internal WDL files
        """
        # Always exclude external/ from internal scan
        patterns = self.exclude_patterns + ["external/"]

        wdl_files = []

        for wdl_file in self.root_path.rglob("*.wdl"):
            if not self._should_exclude(wdl_file, patterns):
                wdl_files.append(wdl_file)

        result = sorted(wdl_files)
        logger.info(f"Found {len(result)} internal WDL files")
        return result

    def find_all_wdl_files(self) -> List[Path]:
        """
        Find all WDL files including external dependencies.

        Returns:
            Sorted list of Path objects for all WDL files
        """
        wdl_files = []

        for wdl_file in self.root_path.rglob("*.wdl"):
            if not self._should_exclude(wdl_file, self.exclude_patterns):
                wdl_files.append(wdl_file)

        result = sorted(wdl_files)
        logger.info(f"Found {len(result)} WDL files (including external)")
        return result

    def find_external_wdl_files(self) -> List[Path]:
        """
        Find only external WDL files (in external/ directory).

        Returns:
            Sorted list of Path objects for external WDL files
        """
        external_dir = self.root_path / "external"

        if not external_dir.exists():
            logger.debug("No external/ directory found")
            return []

        wdl_files = []

        for wdl_file in external_dir.rglob("*.wdl"):
            if not self._should_exclude(wdl_file, self.exclude_patterns):
                wdl_files.append(wdl_file)

        result = sorted(wdl_files)
        logger.info(f"Found {len(result)} external WDL files")
        return result

    def collect_import_chain(self, starting_files: List[Path], visited: Optional[Set[Path]] = None) -> Set[Path]:
        """
        Collect all files transitively imported by starting files.

        This is useful for discovering external dependencies.
        Note: This method does NOT parse the files, it only discovers them
        based on import statements if they follow standard naming conventions.

        Args:
            starting_files: List of files to start from
            visited: Set of already visited files (for recursion)

        Returns:
            Set of all files in the import chain
        """
        if visited is None:
            visited = set()

        all_files = set(starting_files)

        for wdl_file in starting_files:
            if wdl_file in visited:
                continue

            visited.add(wdl_file)

            # Check if file exists
            if not self._exists(wdl_file):
                logger.debug(f"Skipping non-existent file: {wdl_file}")
                continue

            # Look for potential imports by checking the parent and sibling directories
            # This is a heuristic and won't catch all cases
            parent_dir = wdl_file.parent

            # Check common import locations
            for pattern in ["*.wdl"]:
                for sibling in parent_dir.glob(pattern):
                    if sibling not in visited and sibling != wdl_file:
                        all_files.add(sibling)

        return all_files

    def _exists(self, wdl_path: Path) -> bool:
        """
        Check if a WDL file exists.

        Args:
            wdl_path: Path to check

        Returns:
            True if file exists and is a .wdl file
        """
        return wdl_path.exists() and wdl_path.suffix == ".wdl"

    def _should_exclude(self, wdl_path: Path, patterns: List[str]) -> bool:
        """
        Check if a path should be excluded based on patterns.

        Args:
            wdl_path: Path to check
            patterns: List of exclusion patterns

        Returns:
            True if path should be excluded
        """
        try:
            relative_path_str = str(wdl_path.relative_to(self.root_path))
            return any(pattern in relative_path_str for pattern in patterns)
        except ValueError:
            # File is outside root_path, exclude it
            return True
