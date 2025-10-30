"""
AST Mapper - Parsing Adapter

Maps MiniWDL AST objects to domain objects.
"""

from pathlib import Path
from typing import Optional, List, Dict
import WDL.Tree

from src.domain.value_objects import (
    WDLWorkflow,
    WDLTask,
    WDLInput,
    WDLOutput,
    WDLType,
    WDLCommand,
    WDLImport,
)
from src.infrastructure.parsing.docker_extractor import DockerExtractor
from src.infrastructure.parsing.graph_generator import generate_mermaid_graph
from src.infrastructure.parsing.call_parser import CallParser
from src.infrastructure.shared.path_resolver import PathResolver


class AstMapper:
    """
    Maps MiniWDL AST objects to domain objects.

    Handles the transformation from MiniWDL's internal representation
    to our domain model.
    """

    def __init__(self, base_path: Path, output_dir: Path):
        """
        Initialize the AST mapper.

        Args:
            base_path: Base path for relative calculations
            output_dir: Output directory for generated content
        """
        self.base_path = base_path
        self.output_dir = output_dir
        self.docker_extractor = DockerExtractor()
        self.call_parser = CallParser(base_path)

    def map_workflow(self, workflow: WDL.Tree.Workflow, imports: List[WDLImport], wdl_path: Path) -> WDLWorkflow:
        """Map a miniwdl Workflow object to domain WDLWorkflow."""
        # Parse basic info
        name = workflow.name
        description = self._extract_description(workflow)
        meta = self._parse_meta(workflow)

        # Parse inputs and outputs
        inputs = [self._parse_input(inp.value) for inp in workflow.available_inputs]
        outputs = [self._parse_output(out) for out in workflow.outputs] if workflow.outputs else []

        # Parse calls
        calls = self.call_parser.parse_calls(workflow, imports)

        # Extract docker images
        docker_images = self.docker_extractor.extract_from_workflow(workflow)

        # Generate mermaid graph
        mermaid_graph = generate_mermaid_graph(workflow, wdl_path, self.base_path)

        return WDLWorkflow(
            name=name,
            description=description,
            inputs=inputs,
            outputs=outputs,
            calls=calls,
            meta=meta,
            docker_images=docker_images,
            mermaid_graph=mermaid_graph,
        )

    def map_task(self, task: WDL.Tree.Task) -> WDLTask:
        """Map a miniwdl Task object to domain WDLTask."""
        name = task.name
        description = self._extract_description(task)
        meta = self._parse_meta(task)

        # Parse inputs and outputs
        inputs = [self._parse_input(inp.value) for inp in task.available_inputs]
        outputs = [self._parse_output(out) for out in task.outputs] if task.outputs else []

        # Parse command
        command = self._parse_command(task)

        # Parse runtime
        runtime = self._parse_runtime(task)

        return WDLTask(
            name=name,
            description=description,
            inputs=inputs,
            outputs=outputs,
            command=command,
            runtime=runtime,
            meta=meta,
        )

    @staticmethod
    def map_imports(doc: WDL.Tree.Document, wdl_path: Path) -> List[WDLImport]:
        """Map import statements."""
        imports = []
        for imp in doc.imports:
            namespace = imp.namespace if imp.namespace else None
            resolved_path = PathResolver.resolve_import_path(imp.uri, wdl_path)

            imports.append(
                WDLImport(
                    path=imp.uri,
                    namespace=namespace,
                    resolved_path=resolved_path,
                )
            )

        return imports

    def _parse_input(self, inp: WDL.Tree.Decl) -> WDLInput:
        """Parse a WDL input declaration."""
        name = inp.name
        wdl_type = self._parse_type(inp.type)
        description = None
        default_value = None

        if inp.expr:
            try:
                default_value = str(inp.expr)
            except Exception:
                default_value = None

        return WDLInput(
            name=name,
            type=wdl_type,
            description=description,
            default_value=default_value,
        )

    def _parse_output(self, out: WDL.Tree.Decl) -> WDLOutput:
        """Parse a WDL output declaration."""
        name = out.name
        wdl_type = self._parse_type(out.type)
        expression = str(out.expr) if out.expr else None

        return WDLOutput(
            name=name,
            type=wdl_type,
            description=None,
            expression=expression,
        )

    def _parse_type(self, wdl_type: WDL.Type.Base) -> WDLType:
        """Parse a WDL type into domain WDLType."""
        # Handle optional types
        optional = isinstance(wdl_type, WDL.Type.String) and wdl_type.optional
        if hasattr(wdl_type, "optional"):
            optional = wdl_type.optional

        # Get the type name
        type_name = str(wdl_type)
        if type_name.endswith("?"):
            type_name = type_name[:-1]
            optional = True

        # Check if it's a struct
        is_struct = isinstance(wdl_type, WDL.Type.StructInstance)
        struct_fields = None

        if is_struct and hasattr(wdl_type, "members") and wdl_type.members:
            struct_fields = {}
            for field_name, field_type in wdl_type.members.items():
                struct_fields[field_name] = self._parse_type(field_type)

        return WDLType(
            name=type_name,
            optional=optional,
            is_struct=is_struct,
            struct_fields=struct_fields,
        )

    @staticmethod
    def _parse_command(task: WDL.Tree.Task) -> Optional[WDLCommand]:
        """Parse task command."""
        if not task.command:
            return None

        raw_command = str(task.command)

        # Format command (dedent)
        lines = raw_command.split("\n")
        # Remove first and last empty lines
        if lines and not lines[0].strip():
            lines = lines[1:]
        if lines and not lines[-1].strip():
            lines = lines[:-1]

        # Find minimum indentation
        min_indent = float("inf")
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)

        # Remove minimum indentation
        if min_indent != float("inf"):
            formatted_lines = [line[min_indent:] if len(line) > min_indent else line for line in lines]
        else:
            formatted_lines = lines

        formatted_command = "\n".join(formatted_lines)

        return WDLCommand(
            raw_command=raw_command,
            formatted_command=formatted_command,
        )

    @staticmethod
    def _parse_runtime(task: WDL.Tree.Task) -> Dict[str, str]:
        """Parse task runtime attributes."""
        runtime = {}

        if task.runtime:
            for key, expr in task.runtime.items():
                try:
                    runtime[key] = str(expr)
                except Exception:
                    runtime[key] = "unknown"

        return runtime

    @staticmethod
    def _parse_meta(obj) -> Dict[str, str]:
        """Parse meta section."""
        meta = {}

        if hasattr(obj, "meta") and obj.meta:
            for key, value in obj.meta.items():
                meta[key] = str(value)

        return meta

    @staticmethod
    def _extract_description(obj) -> Optional[str]:
        """Extract description from meta section."""
        if hasattr(obj, "meta") and obj.meta:
            if "description" in obj.meta:
                return str(obj.meta["description"])
        return None
