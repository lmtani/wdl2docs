"""
Infrastructure Layer

Contains implementations for external interactions and technical concerns:
- Parsing: WDL parsing adapters (MiniWDL integration)
- File System: File discovery and document repository
- Templating: Template loading and asset copying
- Rendering: HTML generation
"""

from src.infrastructure.parsing import MiniwdlParser
from src.infrastructure.fs import DocumentRepository
from src.infrastructure.rendering import DocumentationGenerator

__all__ = [
    "MiniwdlParser",
    "DocumentRepository",
    "DocumentationGenerator",
]
