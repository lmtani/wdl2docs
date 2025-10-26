"""
Path Resolver - Infrastructure Layer

Handles path normalization and resolution for WDL files.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PathResolver:
    """Handles path resolution and normalization."""

    @staticmethod
    def normalize_relative_path(path: Path) -> Path:
        """
        Normalize a path by resolving .. references while preserving the structure.
        For external files, ensures they start with 'external/'.

        Examples:
            workflows/v1/../../external/file.wdl -> external/file.wdl
            workflows/v1/file.wdl -> workflows/v1/file.wdl

        Args:
            path: Path to normalize

        Returns:
            Normalized path
        """
        # Convert to string and split into parts
        parts = list(path.parts)

        # If path contains 'external', normalize from 'external' onwards
        if "external" in parts:
            external_idx = parts.index("external")
            return Path(*parts[external_idx:])

        # Otherwise, resolve .. manually
        normalized_parts = []
        for part in parts:
            if part == "..":
                if normalized_parts:
                    normalized_parts.pop()
            elif part != ".":
                normalized_parts.append(part)

        return Path(*normalized_parts) if normalized_parts else path

    @staticmethod
    def calculate_relative_path(wdl_file: Path, root_path: Path) -> Path:
        """
        Calculate relative path from root, handling files outside root.

        Args:
            wdl_file: WDL file path
            root_path: Project root path

        Returns:
            Relative path
        """
        try:
            relative_path = wdl_file.relative_to(root_path)
        except ValueError:
            # File is outside root_path (e.g., external/ at same level as workflows/)
            wdl_file_resolved = wdl_file.resolve()

            # Find 'external' in the path and use everything from there
            parts = wdl_file_resolved.parts
            if "external" in parts:
                external_idx = parts.index("external")
                relative_path = Path(*parts[external_idx:])
            else:
                # Fallback: try to find a common ancestor
                try:
                    common = Path(*[p for p in root_path.parts if p in wdl_file.parts])
                    relative_path = wdl_file.relative_to(common)
                except Exception:
                    # Last resort: use the file's path relative to its parent's parent
                    relative_path = Path(*wdl_file.parts[-2:])

        # Normalize the path to resolve any .. references
        relative_path = PathResolver.normalize_relative_path(relative_path)
        return relative_path

    @staticmethod
    def resolve_import_path(import_uri: str, wdl_file: Path) -> Path | None:
        """
        Resolve import path relative to the WDL file.

        Args:
            import_uri: Import URI from WDL file
            wdl_file: Path to the WDL file containing the import

        Returns:
            Resolved path if exists, None otherwise
        """
        try:
            import_path = wdl_file.parent / import_uri
            if import_path.exists():
                return import_path
        except Exception as e:
            logger.debug(f"Could not resolve import path {import_uri}: {e}")

        return None
