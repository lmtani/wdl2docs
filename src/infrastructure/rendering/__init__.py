"""
Rendering Infrastructure Module

This module contains all components related to HTML rendering and static assets
management. It encapsulates Jinja2 template rendering, HTML file generation,
and static assets copying.
"""

from .generator import DocumentationGenerator

__all__ = ["DocumentationGenerator"]
