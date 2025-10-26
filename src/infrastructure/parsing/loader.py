"""
Loader - Parsing Adapter

Anti-corruption layer for MiniWDL file loading operations.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import WDL
import WDL.Error
import WDL.Tree

logger = logging.getLogger(__name__)


class Loader:
    """Handles loading WDL files and reading source code."""

    @staticmethod
    def load_wdl_file(wdl_file: Path) -> WDL.Tree.Document:
        """
        Load a WDL file using miniwdl.

        Args:
            wdl_file: Path to the WDL file

        Returns:
            Parsed WDL document from miniwdl

        Raises:
            WDL.Error.SyntaxError: If WDL syntax is invalid
            Exception: For other loading errors
        """
        logger.debug(f"Loading WDL file with miniwdl: {wdl_file}")

        try:
            doc = WDL.load(str(wdl_file))
            logger.debug(f"Successfully loaded WDL file: {wdl_file}")
            return doc
        except WDL.Error.SyntaxError as e:
            logger.error(f"Syntax error in {wdl_file}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading {wdl_file}: {e}")
            raise

    @staticmethod
    def read_source_code(wdl_file: Path) -> Optional[str]:
        """
        Read the source code from a WDL file.

        Args:
            wdl_file: Path to the WDL file

        Returns:
            Source code as string, or None if reading fails
        """
        try:
            with open(wdl_file, "r", encoding="utf-8") as f:
                source_code = f.read()
            logger.debug(f"Successfully read source code from {wdl_file}")
            return source_code
        except Exception as e:
            logger.warning(f"Could not read source code from {wdl_file}: {e}")
            return None

    @staticmethod
    def load_with_source(wdl_file: Path) -> Tuple[WDL.Tree.Document, Optional[str]]:
        """
        Load WDL file and read its source code.

        Args:
            wdl_file: Path to the WDL file

        Returns:
            Tuple of (WDL document, source code)

        Raises:
            WDL.Error.SyntaxError: If WDL syntax is invalid
            Exception: For other loading errors
        """
        doc = Loader.load_wdl_file(wdl_file)
        source_code = Loader.read_source_code(wdl_file)
        return doc, source_code

    @staticmethod
    def extract_version(doc: WDL.Tree.Document) -> str:
        """
        Extract WDL version from document.

        Args:
            doc: miniwdl document

        Returns:
            Version string (defaults to "1.0")
        """
        version = "1.0"
        if hasattr(doc, "wdl_version") and doc.wdl_version:
            version = doc.wdl_version
        return version
