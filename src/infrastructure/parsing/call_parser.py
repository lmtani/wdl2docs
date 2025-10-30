"""
Call Parser - Shared Parsing Logic

Centralizes the logic for parsing WDL calls.
"""

from pathlib import Path
from typing import List, Dict
import WDL.Tree

from src.domain.value_objects import WDLImport, WDLCall
from src.infrastructure.shared.path_resolver import PathResolver


class CallParser:
    """
    Parses WDL call statements into domain objects.

    Centralizes the logic for creating WDLCall objects, determining
    call types, and resolving links.
    """

    def __init__(self, base_path: Path):
        """
        Initialize the call parser.

        Args:
            base_path: Base path for relative path calculations
        """
        self.base_path = base_path

    def parse_calls(self, workflow: WDL.Tree.Workflow, imports: List[WDLImport]) -> List[WDLCall]:
        """
        Parse all calls in a workflow.

        Args:
            workflow: MiniWDL workflow object
            imports: List of imports in the document

        Returns:
            List of WDLCall domain objects
        """
        calls = []

        for call in workflow.body:
            if isinstance(call, WDL.Tree.Call):
                try:
                    wdl_call = self.create_call_object(call, imports)
                    calls.append(wdl_call)
                except ValueError:
                    # Skip invalid calls
                    continue

        return calls

    def create_call_object(self, call: WDL.Tree.Call, imports: List[WDLImport]) -> WDLCall:
        """
        Create a WDLCall domain object from a MiniWDL call.

        Args:
            call: MiniWDL Call object
            imports: List of imports in the document

        Returns:
            WDLCall domain object

        Raises:
            ValueError: If call is invalid (no callee or name)
        """
        callee = call.callee
        if not callee or not hasattr(callee, "name"):
            raise ValueError("Invalid call: callee has no name")

        # Determine call type
        call_type = self._determine_call_type(callee)

        # Check if it's a local or imported call
        is_local = self._is_local_call(call, imports)

        # Determine link target
        link_target = self._determine_link_target(call, imports, is_local, callee)

        # Parse input mappings
        inputs_mapping = self._parse_input_mappings(call)

        return WDLCall(
            name=callee.name,
            task_or_workflow=callee.name,
            alias=call.name if call.name != callee.name else None,
            inputs_mapping=inputs_mapping,
            is_local=is_local,
            link_target=link_target,
            call_type=call_type,
        )

    @staticmethod
    def _determine_call_type(callee) -> str:
        """
        Determine if the call is to a task or workflow.

        Args:
            callee: MiniWDL callee object

        Returns:
            "workflow" or "task"
        """
        return "workflow" if isinstance(callee, WDL.Tree.Workflow) else "task"

    @staticmethod
    def _is_local_call(call: WDL.Tree.Call, imports: List[WDLImport]) -> bool:
        """
        Check if a call is local (not imported).

        Args:
            call: MiniWDL Call object
            imports: List of imports

        Returns:
            True if call is local, False if imported
        """
        if not call.callee_id:
            return True

        namespace = call.callee_id[0]
        return namespace not in [imp.namespace for imp in imports if imp.namespace]

    def _determine_link_target(
        self, call: WDL.Tree.Call, imports: List[WDLImport], is_local: bool, callee
    ) -> str:
        """
        Determine the link target for a call.

        Args:
            call: MiniWDL Call object
            imports: List of imports
            is_local: Whether the call is local
            callee: MiniWDL callee object

        Returns:
            Link target (HTML anchor or relative path)
        """
        if is_local:
            # Local reference - use anchor
            return f"#{callee.name}"

        # Imported reference - find the import and create relative link
        namespace = call.callee_id[0] if call.callee_id else None
        if not namespace:
            return f"#{callee.name}"

        import_obj = next((imp for imp in imports if imp.namespace == namespace), None)
        if import_obj and import_obj.resolved_path:
            # Calculate relative link for HTML
            rel_path = PathResolver.calculate_relative_path(import_obj.resolved_path, self.base_path)
            return str(rel_path).replace(".wdl", ".html")

        return f"#{callee.name}"

    @staticmethod
    def _parse_input_mappings(call: WDL.Tree.Call) -> Dict[str, str]:
        """
        Parse input mappings from a call.

        Args:
            call: MiniWDL Call object

        Returns:
            Dictionary of input name to expression string
        """
        inputs_mapping = {}

        if call.inputs:
            for name, expr in call.inputs.items():
                try:
                    inputs_mapping[name] = str(expr)
                except Exception:
                    inputs_mapping[name] = "unknown"

        return inputs_mapping
