"""
Templating Adapters

Adapters for template operations:
- Jinja Environment: Template loading via importlib.resources
- Asset Copier: Copy static assets to output directory
"""

from src.infrastructure.templating.asset_copier import AssetCopier

__all__ = [
    "AssetCopier",
]
