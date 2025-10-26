"""
File System Adapters

Adapters for file system operations:
- Discovery: Recursive scanning for WDL files
- Document Repository: Local persistence and file reading
"""

from src.infrastructure.fs.discovery import Discovery
from src.infrastructure.fs.document_repo import DocumentRepository

__all__ = [
    "Discovery",
    "DocumentRepository",
]
