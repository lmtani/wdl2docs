"""
Mermaid Graph Generator - Infrastructure Layer

Generates Mermaid flowchart diagrams from WDL workflow body.
"""

import logging
from pathlib import Path
from typing import List, Set

import WDL.Tree

logger = logging.getLogger(__name__)


def generate_mermaid_graph(workflow: WDL.Tree.Workflow, wdl_path: Path, base_path: Path) -> str:
    """
    Generate Mermaid graph for a workflow.

    Args:
        workflow: The workflow to generate graph for
        wdl_path: Path to the WDL file
        base_path: Base path of the project

    Returns:
        Mermaid graph as string
    """
    generator = MermaidGraphGenerator(workflow.name)
    if hasattr(workflow, "body") and workflow.body:
        return generator.generate(workflow.body)
    return ""


class MermaidGraphGenerator:
    """Generates Mermaid flowchart from workflow body."""

    def __init__(self, workflow_name: str):
        """
        Initialize graph generator.

        Args:
            workflow_name: Name of the workflow
        """
        self.workflow_name = workflow_name
        self.lines = ["flowchart TD"]
        self.node_counter = 0
        self.scatter_counter = 0
        self.conditional_counter = 0

        # Track all calls and their dependencies
        self.call_nodes = {}  # call_name -> node_id
        self.call_dependencies = {}  # call_name -> set of call names it depends on
        self.call_elements = {}  # call_name -> WDL.Tree.Call element

        # Track intermediate variable declarations
        self.var_dependencies = {}  # var_name -> set of call names it depends on

        # Track scatter/conditional context dependencies
        self.context_dependencies = {}  # call_name -> set of call names from scatter/if expressions

        # Track connections to be added outside subgraphs
        self.start_connections = []  # List of node_ids that should connect to Start
        self.dependency_connections = []  # List of (from_node, to_node) tuples

    def generate(self, body: List) -> str:
        """
        Generate Mermaid flowchart from workflow body.

        Args:
            body: Workflow body elements

        Returns:
            Mermaid flowchart as string
        """
        self.lines.append(f"    Start([{self.workflow_name}])")

        # Three-pass generation for correct dependencies
        self._collect_all_calls(body)
        self._analyze_dependencies()
        final_nodes = self._process_elements(body, {"Start"})

        # Add connections outside subgraphs
        self._add_connections()

        # Add End node
        self._add_end_node(final_nodes)

        # Add styling
        self._add_styling()

        return "\n".join(self.lines)

    def _get_node_id(self) -> str:
        """Generate unique node ID."""
        self.node_counter += 1
        return f"N{self.node_counter}"

    def _collect_all_calls(self, elements: List, parent_context: str = "", inherited_deps: Set[str] = None) -> None:
        """First pass: collect all calls and variable declarations."""
        if inherited_deps is None:
            inherited_deps = set()

        for element in elements:
            if isinstance(element, WDL.Tree.Call):
                call_name = element.name
                self.call_elements[call_name] = element
                self.call_dependencies[call_name] = set()

                # Store inherited dependencies from scatter/conditional
                if inherited_deps:
                    self.context_dependencies[call_name] = inherited_deps.copy()

            elif isinstance(element, WDL.Tree.Decl):
                # Track variable declarations
                var_name = element.name
                if hasattr(element, "expr") and element.expr:
                    self.var_dependencies[var_name] = self._extract_dependencies_from_expr(element.expr)

            elif isinstance(element, WDL.Tree.Scatter):
                # Extract dependencies from scatter expression
                scatter_deps = inherited_deps.copy()
                if hasattr(element, "expr") and element.expr:
                    scatter_deps.update(self._extract_dependencies_from_expr(element.expr))

                if hasattr(element, "body") and element.body:
                    self._collect_all_calls(element.body, parent_context, scatter_deps)

            elif isinstance(element, WDL.Tree.Conditional):
                # Extract dependencies from conditional expression
                cond_deps = inherited_deps.copy()
                if hasattr(element, "expr") and element.expr:
                    cond_deps.update(self._extract_dependencies_from_expr(element.expr))

                if hasattr(element, "body") and element.body:
                    self._collect_all_calls(element.body, parent_context, cond_deps)

    def _analyze_dependencies(self) -> None:
        """Second pass: analyze dependencies between calls."""
        for call_name, element in self.call_elements.items():
            deps = self._extract_call_dependencies(element)
            # Add context dependencies from scatter/conditional expressions
            if call_name in self.context_dependencies:
                deps.update(self.context_dependencies[call_name])
            self.call_dependencies[call_name] = deps

    def _process_elements(self, elements: List, parent_nodes: Set[str], indent: str = "    ") -> Set[str]:
        """
        Third pass: process elements and create graph nodes.

        Args:
            elements: Workflow body elements
            parent_nodes: Set of node IDs that should connect to nodes at this level
            indent: Indentation for output

        Returns:
            Set of node IDs representing the end of this block
        """
        level_start_nodes = set()
        level_end_nodes = set()

        for element in elements:
            if isinstance(element, WDL.Tree.Call):
                node_id = self._process_call(element, parent_nodes, indent)
                level_start_nodes.add(node_id)
                level_end_nodes.add(node_id)

            elif isinstance(element, WDL.Tree.Scatter):
                scatter_ends = self._process_scatter(element, parent_nodes, indent)
                level_end_nodes.update(scatter_ends)

            elif isinstance(element, WDL.Tree.Conditional):
                cond_ends = self._process_conditional(element, parent_nodes, indent)
                level_end_nodes.update(cond_ends)

        return level_end_nodes if level_end_nodes else parent_nodes

    def _process_call(self, call: WDL.Tree.Call, parent_nodes: Set[str], indent: str) -> str:
        """Process a call element and return its node ID."""
        call_name = call.name

        # Create node if not already created
        if call_name not in self.call_nodes:
            node_id = self._get_node_id()
            self.call_nodes[call_name] = node_id

            callee_name = call.callee.name if hasattr(call.callee, "name") else str(call.callee)
            display_name = call_name if call_name == callee_name else f"{call_name}<br/><i>{callee_name}</i>"

            # Different shapes for tasks vs workflows
            if hasattr(call.callee, "__class__") and "Task" in call.callee.__class__.__name__:
                self.lines.append(f'{indent}{node_id}["{display_name}"]')
            else:
                self.lines.append(f'{indent}{node_id}[/"{display_name}"/]')

        node_id = self.call_nodes[call_name]

        # Connect to dependencies or parent nodes
        deps = self.call_dependencies.get(call_name, set())
        connected = False

        if deps:
            # Register dependency connections
            for dep_name in deps:
                if dep_name in self.call_nodes:
                    dep_node = self.call_nodes[dep_name]
                    self.dependency_connections.append((dep_node, node_id))
                    connected = True

        # If no dependencies, connect to Start
        if not connected and "Start" in parent_nodes:
            self.start_connections.append(node_id)

        return node_id

    def _process_scatter(self, scatter: WDL.Tree.Scatter, parent_nodes: Set[str], indent: str) -> Set[str]:
        """Process a scatter element."""
        # Check if scatter contains calls
        if not self._has_calls(scatter.body if hasattr(scatter, "body") and scatter.body else []):
            # No subgraph needed
            if hasattr(scatter, "body") and scatter.body:
                return self._process_elements(scatter.body, parent_nodes, indent)
            return parent_nodes

        # Create subgraph for scatter
        self.scatter_counter += 1
        scatter_id = f"S{self.scatter_counter}"
        scatter_var = scatter.variable

        scatter_collection = self._get_scatter_collection(scatter)
        scatter_label = (
            f"🔃 scatter {scatter_var} in {scatter_collection}" if scatter_collection else f"🔃 scatter {scatter_var}"
        )

        self.lines.append(f'{indent}subgraph {scatter_id} ["{scatter_label}"]')
        self.lines.append(f"{indent}    direction TB")

        scatter_ends = self._process_elements(scatter.body, parent_nodes, indent + "    ")

        self.lines.append(f"{indent}end")
        return scatter_ends

    def _process_conditional(self, conditional: WDL.Tree.Conditional, parent_nodes: Set[str], indent: str) -> Set[str]:
        """Process a conditional element."""
        # Check if conditional contains calls
        if not self._has_calls(conditional.body if hasattr(conditional, "body") and conditional.body else []):
            # No subgraph needed
            if hasattr(conditional, "body") and conditional.body:
                return self._process_elements(conditional.body, parent_nodes, indent)
            return parent_nodes

        # Create subgraph for conditional
        self.conditional_counter += 1
        cond_id = f"C{self.conditional_counter}"

        condition_expr = self._get_condition_expr(conditional)
        conditional_label = f"↔️ if {condition_expr}".replace('"', "'")

        self.lines.append(f'{indent}subgraph {cond_id} ["{conditional_label}"]')
        self.lines.append(f"{indent}    direction TB")

        cond_ends = self._process_elements(conditional.body, parent_nodes, indent + "    ")

        self.lines.append(f"{indent}end")
        return cond_ends

    def _add_connections(self) -> None:
        """Add all connections outside subgraphs."""
        # Add dependency connections
        for from_node, to_node in self.dependency_connections:
            self.lines.append(f"    {from_node} --> {to_node}")

        # Add Start connections
        for node_id in self.start_connections:
            self.lines.append(f"    Start --> {node_id}")

    def _add_end_node(self, final_nodes: Set[str]) -> None:
        """Add End node and connect leaf nodes."""
        # Find leaf nodes (not dependencies of any other node)
        all_dependencies = set()
        for deps in self.call_dependencies.values():
            all_dependencies.update(deps)

        leaf_nodes = set()
        for call_name in self.call_elements.keys():
            if call_name not in all_dependencies and call_name in self.call_nodes:
                leaf_nodes.add(self.call_nodes[call_name])

        # Connect leaf nodes to End
        nodes_to_connect = leaf_nodes if leaf_nodes else final_nodes
        for node in nodes_to_connect:
            self.lines.append(f"    {node} --> End([End])")

    def _add_styling(self) -> None:
        """Add CSS styling to graph."""
        self.lines.append("    classDef taskNode fill:#a371f7,stroke:#8b5cf6,stroke-width:2px,color:#fff")
        self.lines.append("    classDef workflowNode fill:#58a6ff,stroke:#1f6feb,stroke-width:2px,color:#fff")

    def _extract_dependencies_from_expr(self, expr) -> Set[str]:
        """Extract call names that an expression depends on."""
        dependencies = set()
        identifiers = set()

        def extract_identifiers(e):
            """Recursively extract identifier names."""
            if hasattr(e, "name"):
                identifiers.add(str(e.name) if hasattr(e.name, "__str__") else e.name)

            if hasattr(e, "expr"):
                extract_identifiers(e.expr)

            if hasattr(e, "arguments"):
                for arg in e.arguments:
                    if hasattr(arg, "expr"):
                        extract_identifiers(arg.expr)
                    else:
                        extract_identifiers(arg)

            if hasattr(e, "items"):
                for item in e.items:
                    extract_identifiers(item)

        extract_identifiers(expr)

        # Check which identifiers match call names or variables
        for identifier in identifiers:
            ref = identifier.split(".")[0] if "." in identifier else identifier

            if ref in self.call_elements:
                dependencies.add(ref)
            elif ref in self.var_dependencies:
                # Transitive dependency through variable
                dependencies.update(self.var_dependencies[ref])

        return dependencies

    def _extract_call_dependencies(self, call: WDL.Tree.Call) -> Set[str]:
        """Extract which other calls this element depends on."""
        dependencies = set()

        if not hasattr(call, "inputs") or not call.inputs:
            return dependencies

        for param_name, expr in call.inputs.items():
            if expr:
                dependencies.update(self._extract_dependencies_from_expr(expr))

        return dependencies

    def _has_calls(self, elements: List) -> bool:
        """Check if elements contain any calls."""
        for elem in elements:
            if isinstance(elem, WDL.Tree.Call):
                return True
            elif isinstance(elem, (WDL.Tree.Scatter, WDL.Tree.Conditional)):
                if hasattr(elem, "body") and elem.body and self._has_calls(elem.body):
                    return True
        return False

    def _get_scatter_collection(self, scatter: WDL.Tree.Scatter) -> str:
        """Get scatter collection expression as string."""
        if not hasattr(scatter, "expr") or not scatter.expr:
            return ""

        try:
            expr = scatter.expr

            if hasattr(expr, "name"):
                return expr.name
            elif hasattr(expr, "function_name"):
                func_name = expr.function_name
                if hasattr(expr, "arguments") and expr.arguments:
                    args = []
                    for arg in expr.arguments:
                        try:
                            if hasattr(arg, "name"):
                                args.append(str(arg.name))
                            elif hasattr(arg, "value"):
                                args.append(str(arg.value))
                            else:
                                args.append(str(arg))
                        except Exception:
                            args.append("...")
                    return f"{func_name}({', '.join(args)})"
                else:
                    return f"{func_name}()"
            else:
                return str(expr)
        except Exception:
            return "items"

    def _get_condition_expr(self, conditional: WDL.Tree.Conditional) -> str:
        """Get conditional expression as string."""
        if hasattr(conditional, "expr") and conditional.expr:
            try:
                return str(conditional.expr)
            except Exception:
                pass
        return "condition"
