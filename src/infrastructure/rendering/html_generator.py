"""
HTML Generator - Infrastructure Layer

Generates HTML files from WDL documents using template renderer.
Handles file I/O and directory structure creation.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.domain.value_objects import WDLDocument
from src.domain.errors import ParseError
from src.infrastructure.rendering.template_renderer import TemplateRenderer
from src.infrastructure.shared.path_resolver import PathResolver

logger = logging.getLogger(__name__)


class HtmlGenerator:
    """
    Generates HTML documentation files.

    Uses TemplateRenderer for rendering and handles file I/O operations.
    """

    def __init__(self, output_dir: Path, renderer: TemplateRenderer):
        """
        Initialize the generator.

        Args:
            output_dir: Directory where HTML files will be written
            renderer: Template renderer instance
        """
        self.output_dir = output_dir
        self.renderer = renderer

    def generate_document_page(self, doc: WDLDocument, all_documents: Optional[List[WDLDocument]] = None) -> Path:
        """
        Generate HTML page for a WDL document.

        Args:
            doc: WDLDocument to generate page for
            all_documents: List of all documents for cross-referencing (optional)

        Returns:
            Path to generated HTML file
        """
        # Normalize path and determine output file
        relative_path = PathResolver.normalize_relative_path(doc.relative_path)
        output_file = self.output_dir / relative_path.with_suffix(".html")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Calculate relative path to root for navigation
        depth = len(relative_path.parts) - 1
        root_rel = "../" * depth if depth > 0 else "./"

        # Calculate workflow references if this is a workflow and we have all documents
        workflow_call_info = None
        if doc.has_workflow and all_documents:
            workflow_call_info = self._get_workflow_call_info(doc, all_documents)

        # Render template
        html_content = self.renderer.render_template(
            "document.html",
            {
                "doc": doc,
                "root_path": root_rel,
                "page_title": doc.name,
                "workflow_call_info": workflow_call_info,
            },
        )

        # Write HTML file
        output_file.write_text(html_content, encoding="utf-8")
        logger.debug(f"Generated {output_file}")

        # Generate graph page if workflow has a graph
        if doc.has_workflow and doc.workflow.has_graph:
            self.generate_graph_page(doc, root_rel)

        return output_file

    def generate_graph_page(self, doc: WDLDocument, root_rel: str) -> Path:
        """
        Generate separate graph page for a workflow.

        Args:
            doc: WDLDocument with workflow
            root_rel: Relative path to root

        Returns:
            Path to generated graph HTML file
        """
        # Normalize path
        relative_path = self.renderer._normalize_path(doc.relative_path)
        stem = relative_path.stem
        graph_filename = f"{stem}-graph.html"
        graph_file = self.output_dir / relative_path.parent / graph_filename

        # Back to document link
        doc_filename = relative_path.with_suffix(".html").name

        # Render template
        html_content = self.renderer.render_template(
            "graph.html",
            {
                "workflow_name": doc.workflow.name,
                "mermaid_graph": doc.workflow.mermaid_graph,
                "root_path": root_rel,
                "back_to_doc": doc_filename,
            },
        )

        # Write HTML file
        graph_file.write_text(html_content, encoding="utf-8")
        logger.debug(f"Generated graph page {graph_file}")

        return graph_file

    def generate_index(
        self,
        documents: List[WDLDocument],
        parse_errors: Optional[List[ParseError]] = None,
    ) -> Path:
        """
        Generate main index.html page.

        Args:
            documents: List of all WDLDocument objects
            parse_errors: List of parsing errors (optional)

        Returns:
            Path to generated index.html
        """
        if parse_errors is None:
            parse_errors = []

        # Organize documents
        context = self._prepare_index_context(documents, parse_errors)

        # Render template
        html_content = self.renderer.render_template("index.html", context)

        # Write index file
        index_file = self.output_dir / "index.html"
        index_file.write_text(html_content, encoding="utf-8")
        logger.info(f"Generated index at {index_file}")

        return index_file

    def generate_docker_images_page(self, documents: List[WDLDocument]) -> Path:
        """
        Generate Docker images inventory page.

        Args:
            documents: List of all WDLDocument objects

        Returns:
            Path to generated docker_images.html
        """
        # Prepare context
        context = self._prepare_docker_context(documents)

        # Render template
        html_content = self.renderer.render_template("docker_images.html", context)

        # Write file
        docker_file = self.output_dir / "docker_images.html"
        docker_file.write_text(html_content, encoding="utf-8")
        logger.info(f"Generated Docker images inventory at {docker_file}")

        return docker_file

    def _prepare_index_context(self, documents: List[WDLDocument], parse_errors: List[ParseError]) -> Dict[str, Any]:
        """Prepare context for index template."""
        # Separate internal and external documents
        internal_docs = [doc for doc in documents if not doc.is_external]
        external_docs = [doc for doc in documents if doc.is_external]

        # Calculate how many times each workflow is called by others
        workflow_caller_counts = self._calculate_workflow_caller_counts(documents)

        # Organize internal documents by type
        workflows = sorted(
            [doc for doc in internal_docs if doc.has_workflow and not doc.has_tasks],
            key=lambda doc: doc.workflow.name.lower(),
        )
        mixed_files = sorted(
            [doc for doc in internal_docs if doc.has_workflow and doc.has_tasks],
            key=lambda doc: doc.workflow.name.lower(),
        )
        task_files = sorted(
            [doc for doc in internal_docs if doc.has_tasks and not doc.has_workflow],
            key=lambda doc: doc.name.lower(),
        )

        # Organize external documents by type
        external_workflows = sorted(
            [doc for doc in external_docs if doc.has_workflow and not doc.has_tasks],
            key=lambda doc: doc.workflow.name.lower(),
        )
        external_mixed = sorted(
            [doc for doc in external_docs if doc.has_workflow and doc.has_tasks],
            key=lambda doc: doc.workflow.name.lower(),
        )
        external_tasks = sorted(
            [doc for doc in external_docs if doc.has_tasks and not doc.has_workflow],
            key=lambda doc: doc.name.lower(),
        )

        # Categorize errors
        syntax_errors = [e for e in parse_errors if e.error_type == "SyntaxError"]
        other_errors = [e for e in parse_errors if e.error_type != "SyntaxError" and e.severity == "error"]
        warnings = [e for e in parse_errors if e.severity == "warning"]

        return {
            "documents": documents,
            "workflows": workflows,
            "mixed_files": mixed_files,
            "task_files": task_files,
            "external_workflows": external_workflows,
            "external_mixed": external_mixed,
            "external_tasks": external_tasks,
            "total_workflows": len(workflows) + len(mixed_files),
            "total_tasks": sum(len(doc.tasks) for doc in internal_docs),
            "total_files": len(internal_docs),
            "total_external": len(external_docs),
            "parse_errors": parse_errors,
            "syntax_errors": syntax_errors,
            "other_errors": other_errors,
            "warnings": warnings,
            "total_errors": len(parse_errors),
            "workflow_caller_counts": workflow_caller_counts,
        }

    def _calculate_workflow_caller_counts(self, documents: List[WDLDocument]) -> Dict[str, int]:
        """
        Calculate how many times each workflow is called by other workflows.

        Args:
            documents: List of all documents

        Returns:
            Dictionary mapping workflow names to the count of workflows that call them
        """
        caller_counts = {}

        # Build a dictionary of all workflow names for quick lookup
        workflow_names = set()
        for doc in documents:
            if doc.has_workflow:
                workflow_names.add(doc.workflow.name)

        # Count how many workflows call each workflow
        for doc in documents:
            if not doc.has_workflow:
                continue

            for call in doc.workflow.calls:
                # Only count workflow calls (not task calls)
                if call.is_workflow_call and call.task_or_workflow in workflow_names:
                    workflow_name = call.task_or_workflow
                    caller_counts[workflow_name] = caller_counts.get(workflow_name, 0) + 1

        return caller_counts

    def _get_workflow_call_info(self, doc: WDLDocument, all_documents: List[WDLDocument]) -> Optional[Dict[str, Any]]:
        """
        Get information about which workflows call this workflow.

        Args:
            doc: The workflow document to check
            all_documents: List of all documents

        Returns:
            Dictionary with call information or None if workflow is not called
        """
        if not doc.has_workflow:
            return None

        workflow_name = doc.workflow.name
        calling_workflows = []

        # Search through all documents to find calls to this workflow
        for caller_doc in all_documents:
            if not caller_doc.has_workflow or caller_doc == doc:
                continue

            # Check if this workflow calls our target workflow
            for call in caller_doc.workflow.calls:
                if call.is_workflow_call and call.task_or_workflow == workflow_name:
                    # Normalize path for URL
                    normalized_path = self.renderer._normalize_path(caller_doc.relative_path)
                    workflow_url = str(normalized_path.with_suffix(".html"))

                    calling_workflows.append(
                        {
                            "name": caller_doc.workflow.name,
                            "file_path": str(caller_doc.relative_path),
                            "url": workflow_url,
                        }
                    )

        if not calling_workflows:
            return None

        return {
            "count": len(calling_workflows),
            "workflows": calling_workflows,
        }

    def _prepare_docker_context(self, documents: List[WDLDocument]) -> Dict[str, Any]:
        """Prepare context for docker images template."""
        repositories_internal = {}
        repositories_external = {}

        for doc in documents:
            if not doc.has_workflow or not doc.workflow.has_docker_images:
                continue

            is_external = doc.is_external
            repositories = repositories_external if is_external else repositories_internal

            self._process_docker_images(doc, documents, repositories)

        # Convert to lists and sort
        self._finalize_repositories(repositories_internal)
        self._finalize_repositories(repositories_external)

        # Sort repositories
        sorted_repos_internal = dict(
            sorted(
                repositories_internal.items(),
                key=lambda x: (x[0] == "Parameterized Images", x[0]),
            )
        )
        sorted_repos_external = dict(
            sorted(
                repositories_external.items(),
                key=lambda x: (x[0] == "Parameterized Images", x[0]),
            )
        )

        # Calculate statistics
        stats_internal = self._calculate_docker_stats(repositories_internal, is_external=False)
        stats_external = self._calculate_docker_stats(repositories_external, is_external=True)

        return {
            "repositories_internal": sorted_repos_internal,
            "repositories_external": sorted_repos_external,
            **stats_internal,
            **stats_external,
            "has_external": stats_external["total_repositories_external"] > 0,
            "root_path": "./",
        }

    def _process_docker_images(self, doc: WDLDocument, all_documents: List[WDLDocument], repositories: Dict) -> None:
        """Process docker images from a document."""
        for docker_image in doc.workflow.docker_images:
            repo_name, image_key, image_data = self._extract_docker_info(docker_image)

            # Initialize repository if needed
            if repo_name not in repositories:
                repositories[repo_name] = {"images": {}, "image_count": 0}

            # Initialize image if needed
            if image_key not in repositories[repo_name]["images"]:
                repositories[repo_name]["images"][image_key] = image_data
                repositories[repo_name]["image_count"] += 1

            # Add task information
            self._add_task_info(
                docker_image,
                doc,
                all_documents,
                repositories[repo_name]["images"][image_key],
            )

    def _extract_docker_info(self, docker_image) -> tuple:
        """Extract repository name, image key, and image data."""
        image_full = docker_image.image
        is_parameterized = docker_image.is_parameterized

        grouping_image = docker_image.default_value if (is_parameterized and docker_image.default_value) else image_full

        if is_parameterized and not docker_image.default_value:
            repo_name = "Parameterized Images"
            image_name = docker_image.parameter_name or "unknown"
            image_tag = None
        else:
            if "/" in grouping_image:
                parts = grouping_image.rsplit("/", 1)
                repo_name = parts[0]
                image_part = parts[1]
            else:
                repo_name = "Docker Hub (library)"
                image_part = grouping_image

            if ":" in image_part:
                image_name, image_tag = image_part.split(":", 1)
            else:
                image_name = image_part
                image_tag = "latest"

        base_key = f"{image_name}:{image_tag}" if image_tag else image_name
        image_key = f"{base_key}__parameterized" if is_parameterized else base_key

        image_data = {
            "name": image_name,
            "tag": image_tag,
            "full_name": image_full,
            "is_parameterized": is_parameterized,
            "default_value": docker_image.default_value if is_parameterized else None,
            "parameter_name": docker_image.parameter_name if is_parameterized else None,
            "tasks": [],
            "task_count": 0,
        }

        return repo_name, image_key, image_data

    def _add_task_info(
        self,
        docker_image,
        doc: WDLDocument,
        all_documents: List[WDLDocument],
        image_data: Dict,
    ) -> None:
        """Add task information to image data."""
        for task_name in docker_image.task_names:
            task_url, task_file_path = self._find_task_url(task_name, doc, all_documents)

            image_data["tasks"].append(
                {
                    "task_name": task_name,
                    "workflow_name": doc.workflow.name,
                    "workflow_url": task_url,
                    "file_path": task_file_path,
                    "is_external": doc.is_external,
                }
            )
            image_data["task_count"] += 1

    def _find_task_url(self, task_name: str, doc: WDLDocument, all_documents: List[WDLDocument]) -> tuple:
        """Find URL and file path for a task."""
        # Check current document
        if doc.has_tasks:
            for task in doc.tasks:
                if task.name == task_name:
                    normalized_path = self.renderer._normalize_path(doc.relative_path)
                    task_url = f"{normalized_path.with_suffix('.html')}#task-{task_name}"
                    return task_url, str(normalized_path)

        # Search in all documents
        for search_doc in all_documents:
            if search_doc.has_tasks:
                for task in search_doc.tasks:
                    if task.name == task_name:
                        normalized_path = self.renderer._normalize_path(search_doc.relative_path)
                        task_url = f"{normalized_path.with_suffix('.html')}#task-{task_name}"
                        return task_url, str(normalized_path)

        # Fallback to workflow URL
        normalized_path = self.renderer._normalize_path(doc.relative_path)
        task_url = str(normalized_path.with_suffix(".html"))
        return task_url, str(normalized_path)

    def _finalize_repositories(self, repositories: Dict) -> None:
        """Convert images dict to list and sort."""
        for repo_name in repositories:
            repositories[repo_name]["images"] = list(repositories[repo_name]["images"].values())
            repositories[repo_name]["images"].sort(key=lambda x: x["name"])

    def _calculate_docker_stats(self, repositories: Dict, is_external: bool) -> Dict[str, int]:
        """Calculate statistics for docker repositories."""
        total_repos = len(repositories)
        total_images = sum(repo["image_count"] for repo in repositories.values())
        total_usages = sum(sum(img["task_count"] for img in repo["images"]) for repo in repositories.values())

        suffix = "_external" if is_external else "_internal"

        return {
            f"total_repositories{suffix}": total_repos,
            f"total_images{suffix}": total_images,
            f"total_usages{suffix}": total_usages,
        }
