"""
Document Repository - File System Adapter

Responsible for document persistence and file reading operations.
Encapsulates local file system access for WDL documents.
"""

import logging
from pathlib import Path
from typing import List, Set, Optional

from src.infrastructure.fs.discovery import Discovery

logger = logging.getLogger(__name__)


class DocumentRepository:
    """
    Repository for WDL documents in the filesystem.

    Handles access to WDL files and delegates discovery operations
    to the Discovery service.
    """

    def __init__(
        self, root_path: Path, exclude_patterns: Optional[List[str]] = None, external_dirs: Optional[List[str]] = None
    ):
        """
        Initialize the repository.

        Args:
            root_path: Root directory of the WDL project
            exclude_patterns: Patterns to exclude from search (e.g., ['test/', 'cache/'])
            external_dirs: Directory names considered as external dependencies (e.g., ['external', 'vendor'])
        """
        self.root_path = root_path
        self.exclude_patterns = exclude_patterns or ["__pycache__/", ".git/"]
        self.external_dirs = external_dirs or ["external"]
        self.discovery = Discovery(root_path, exclude_patterns)

    def find_internal_wdl_files(self) -> List[Path]:
        """
        Find all internal WDL files (excluding external/ directory).

        Delegates to Discovery service.
        """
        return self.discovery.find_internal_wdl_files()

    def find_all_wdl_files(self) -> List[Path]:
        """
        Find all WDL files including external dependencies.

        Delegates to Discovery service.
        """
        return self.discovery.find_all_wdl_files()

    def find_external_wdl_files(self) -> List[Path]:
        """
        Find only external WDL files (in external/ directory).

        Delegates to Discovery service.
        """
        return self.discovery.find_external_wdl_files()

    def collect_import_chain(self, starting_files: List[Path], visited: Optional[Set[Path]] = None) -> Set[Path]:
        """
        Collect all files transitively imported by starting files.

        Delegates to Discovery service.
        """
        return self.discovery.collect_import_chain(starting_files, visited)

    def exists(self, wdl_path: Path) -> bool:
        """
        Check if a WDL file exists.

        Args:
            wdl_path: Path to check

        Returns:
            True if file exists and is a .wdl file
        """
        return wdl_path.exists() and wdl_path.suffix == ".wdl"

    def get_relative_path(self, wdl_path: Path) -> Path:
        """
        Get path relative to repository root.

        Args:
            wdl_path: Absolute or relative path

        Returns:
            Path relative to root_path
        """
        try:
            return wdl_path.relative_to(self.root_path)
        except ValueError:
            # File is outside root, return as-is
            return wdl_path

    def is_external(self, wdl_path: Path) -> bool:
        """
        Check if a WDL file is external (third-party).

        A file is considered external if:
        1. It's located outside the root_path, OR
        2. It's inside one of the configured external directories

        Args:
            wdl_path: Path to check

        Returns:
            True if file is external
        """
        try:
            # Try to get path relative to root
            relative = self.get_relative_path(wdl_path)

            # If get_relative_path returned the original path unchanged,
            # it means the file is outside root_path
            if relative == wdl_path:
                return True

            # Check if path contains any of the external directory names
            return any(ext_dir in relative.parts for ext_dir in self.external_dirs)
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"DocumentRepository(root_path={self.root_path})"
