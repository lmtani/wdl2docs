"""
Asset Copier - Templating Adapter

Manages copying static assets (CSS, JS) for the documentation site.
"""

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class AssetCopier:
    """
    Manages static assets for the documentation.

    Handles copying static files (CSS, JS) from templates directory
    """

    def __init__(self, templates_dir: Path, static_dir_name: str = "static"):
        """
        Initialize asset copier.

        Args:
            templates_dir: Path to templates directory containing static assets
            static_dir_name: Name of static directory (default: "static")
        """
        self.templates_dir = templates_dir
        self.static_dir_name = static_dir_name
        self.source_static_dir = templates_dir / static_dir_name
        logger.info(f"Asset copier sources directory: {self.source_static_dir}")

    def copy_static_assets(self, output_dir: Path) -> None:
        """
        Copy static assets to output directory.

        Creates minimal assets if source doesn't exist.

        Args:
            output_dir: Output directory for documentation
        """
        target_static_dir = output_dir / self.static_dir_name

        if self.source_static_dir.exists():
            # Remove target if it exists
            if target_static_dir.exists():
                shutil.rmtree(target_static_dir)

            # Copy entire static directory
            shutil.copytree(self.source_static_dir, target_static_dir)
            logger.info(f"Static assets copied from {self.source_static_dir} to {target_static_dir}")
            return

        raise FileNotFoundError(f"Could not find static directory at {self.source_static_dir}")
