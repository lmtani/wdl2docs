"""
Analyzer - Parsing Adapter

Analyzes dependencies and relationships between WDL elements.
"""

from pathlib import Path
from typing import List, Set, Dict
import WDL.Tree

from src.domain.value_objects import WDLImport, WDLCall
from src.infrastructure.parsing.path_resolver import PathResolver


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

        for call in workflow.body:
            if isinstance(call, WDL.Tree.Call):
                callee = call.callee
                if not callee or not hasattr(callee, "name"):
                    continue

                caller_name = call.name if call.name else callee.name

                if caller_name not in call_graph:
                    call_graph[caller_name] = []

                # Create WDLCall object (simplified for analysis)
                wdl_call = self._create_call_object(call, imports)
                call_graph[caller_name].append(wdl_call)

        return call_graph

    def _create_call_object(self, call: WDL.Tree.Call, imports: List[WDLImport]) -> WDLCall:
        """Create a WDLCall object for analysis purposes."""
        callee = call.callee
        if not callee or not hasattr(callee, "name"):
            raise ValueError("Invalid call: callee has no name")

        call_type = "workflow" if isinstance(callee, WDL.Tree.Workflow) else "task"

        # Check if imported
        is_local = call.callee_id[0] not in [imp.namespace for imp in imports if imp.namespace]

        # Determine link target
        link_target = None
        if not is_local:
            namespace = call.callee_id[0]
            import_obj = next((imp for imp in imports if imp.namespace == namespace), None)
            if import_obj and import_obj.resolved_path:
                rel_path = PathResolver.calculate_relative_path(import_obj.resolved_path, self.base_path)
                link_target = str(rel_path).replace(".wdl", ".html")
        else:
            link_target = f"#{callee.name}"

        # Parse input mappings
        inputs_mapping = {}
        if call.inputs:
            for name, expr in call.inputs.items():
                inputs_mapping[name] = str(expr)

        return WDLCall(
            name=callee.name,
            task_or_workflow=callee.name,
            alias=call.name if call.name != callee.name else None,
            inputs_mapping=inputs_mapping,
            is_local=is_local,
            link_target=link_target,
            call_type=call_type,
        )

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
