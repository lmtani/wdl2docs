#!/usr/bin/env python3
"""
WDL2Doc - Documentation generator for WDL workflows and tasks.
"""

import click
import logging
import coloredlogs
from pathlib import Path

from src.application.use_cases.generate_documentation import GenerateDocumentationUseCase
from src.application.use_cases.generate_workflow_graph import GenerateWorkflowGraphUseCase
from src.infrastructure import DocumentationGenerator, MiniwdlParser, DocumentRepository


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """WDL2Doc - Generate documentation for WDL workflows and tasks."""


@cli.command()
@click.argument("root_path", type=click.Path(exists=True, file_okay=False, path_type=Path), required=False, default=".")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="docs/wdl",
    help="Output directory for generated documentation.",
    show_default=True,
)
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    default=["__pycache__/", ".git/", "cached-data/"],
    help="Patterns to exclude from search.",
    show_default=True,
)
@click.option(
    "--external-dirs",
    multiple=True,
    default=["external"],
    help="Directory names to treat as external dependencies.",
    show_default=True,
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
def generate(root_path, output, exclude, external_dirs, verbose):
    """Generate HTML documentation for WDL files in ROOT_PATH."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        coloredlogs.install(level="DEBUG")
    else:
        coloredlogs.install(level="INFO")

    root_path = root_path.resolve()
    output_dir = output.resolve()

    logger.info(f"📂 Scanning WDL files in: {root_path}")
    logger.info(f"📝 Output directory: {output_dir}")

    # Initialize infrastructure dependencies
    repository = DocumentRepository(root_path, list(exclude), list(external_dirs))
    parser = MiniwdlParser(root_path, output_dir)

    # Initialize DocumentationGenerator
    documentation_generator = DocumentationGenerator(output_dir, root_path)

    # Execute use case
    use_case = GenerateDocumentationUseCase(
        repository=repository, parser=parser, documentation_generator=documentation_generator
    )

    success = use_case.execute()

    if success:
        logger.info(f"✅ Documentation generated successfully at {output_dir}")
    else:
        logger.error("❌ Failed to generate documentation")
        raise click.Abort()


@cli.command()
@click.argument("wdl_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), required=True, help="Output Markdown file path.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
def graph(wdl_file, output, verbose):
    """Generate a Mermaid graph diagram for a WDL workflow."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        coloredlogs.install(level="DEBUG")
    else:
        coloredlogs.install(level="INFO")

    wdl_file = wdl_file.resolve()
    output_file = output.resolve()

    logger.info(f"🔄 Generating workflow graph for: {wdl_file}")
    logger.info(f"📄 Output file: {output_file}")

    # Execute use case
    use_case = GenerateWorkflowGraphUseCase()
    success = use_case.execute(wdl_file, output_file)

    if success:
        logger.info(f"✅ Graph generated successfully!")
        logger.info(f"📖 Open {output_file} in a Markdown viewer to see the graph")
    else:
        logger.error("❌ Failed to generate workflow graph")
        raise click.Abort()


if __name__ == "__main__":
    cli()
