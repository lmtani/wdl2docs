"""
Analyzer - Parsing Adapter

Analyzes dependencies and relationships between WDL elements.
"""

from pathlib import Path
from typing import List, Set, Dict
import WDL.Tree

from src.domain.value_objects import WDLImport, WDLCall
from src.infrastructure.parsing.call_parser import CallParser


class Analyzer:
    """
    Analyzes dependencies and relationships in WDL documents.

    Handles analysis of call dependencies, import chains, and
    relationships between workflows and tasks.
    """

    def __init__(self, base_path: Path):
        """
        Initialize the analyzer.

        Args:
            base_path: Base path for path calculations
        """
        self.base_path = base_path
        self.call_parser = CallParser(base_path)

    def analyze_dependencies(self, workflow: WDL.Tree.Workflow, imports: List[WDLImport]) -> Dict[str, Set[str]]:
        """
        Analyze dependencies within a workflow.

        Args:
            workflow: MiniWDL workflow to analyze
            imports: List of imports in the document

        Returns:
            Dictionary mapping task/workflow names to their dependencies
        """
        dependencies = {}

        for call in workflow.body:
            if isinstance(call, WDL.Tree.Call):
                # Determine if it's a task or workflow call
                callee = call.callee
                if not callee or not hasattr(callee, "name"):
                    continue

                caller_name = call.name if call.name else callee.name
                callee_name = callee.name

                # Add dependency
                if caller_name not in dependencies:
                    dependencies[caller_name] = set()
                dependencies[caller_name].add(callee_name)

        return dependencies

    def find_external_dependencies(self, documents: List, parsed_paths: Set[Path]) -> List[Path]:
        """
        Find external dependencies that need to be parsed.

        Args:
            documents: List of already parsed documents
            parsed_paths: Set of already parsed file paths

        Returns:
            List of external file paths that need parsing
        """
        external_files = []

        for doc in documents:
            if hasattr(doc, "imports"):
                for imp in doc.imports:
                    if not imp.resolved_path or imp.resolved_path in parsed_paths:
                        continue

                    normalized_path = imp.resolved_path.resolve()
                    if normalized_path in parsed_paths:
                        continue

                    # Check if external
                    if self._is_external_path(normalized_path):
                        external_files.append(normalized_path)
                        parsed_paths.add(normalized_path)

        return external_files

    def build_call_graph(self, workflow: WDL.Tree.Workflow, imports: List[WDLImport]) -> Dict[str, List[WDLCall]]:
        """
        Build a call graph for the workflow.

        Args:
            workflow: MiniWDL workflow
            imports: List of imports

        Returns:
            Dictionary mapping callers to their calls
        """
        call_graph = {}
        calls = self.call_parser.parse_calls(workflow, imports)

        for wdl_call in calls:
            caller_name = wdl_call.alias if wdl_call.alias else wdl_call.name

            if caller_name not in call_graph:
                call_graph[caller_name] = []

            call_graph[caller_name].append(wdl_call)

        return call_graph

    def _is_external_path(self, path: Path) -> bool:
        """
        Check if a path is external to the project.

        Args:
            path: Path to check

        Returns:
            True if path contains 'external' in its parts
        """
        try:
            relative = path.relative_to(self.base_path)
            return "external" in relative.parts
        except ValueError:
            return False
