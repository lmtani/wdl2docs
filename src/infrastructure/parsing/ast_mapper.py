"""
AST Mapper - Parsing Adapter

Maps MiniWDL AST objects to domain objects.
"""
import ast
from pathlib import Path
from typing import Optional, List, Dict
import WDL.Tree
import logging
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


logger = logging.getLogger(__name__)


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
        parameter_meta = self._extract_parameter_meta(workflow)
        meta = self._parse_meta(workflow)
        
        # Extract author and email from meta
        author = meta.get('author')
        email = meta.get('email')

        # Parse inputs and outputs
        inputs = [self._parse_input(inp.value, parameter_meta) for inp in workflow.available_inputs]
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
            docker_images=docker_images,
            mermaid_graph=mermaid_graph,
            meta=meta,
            author=author,
            email=email,
        )

    def map_task(self, task: WDL.Tree.Task) -> WDLTask:
        """Map a miniwdl Task object to domain WDLTask."""
        name = task.name
        description = self._extract_description(task)
        parameter_meta = self._extract_parameter_meta(task)
        meta = self._parse_meta(task)
        
        # Extract author and email from meta
        author = meta.get('author')
        email = meta.get('email')

        # Parse inputs and outputs
        inputs = [self._parse_input(inp.value, parameter_meta) for inp in task.available_inputs]
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
            author=author,
            email=email,
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


    def _parse_description(self, parameter_meta: dict[str, str], name: str) -> Optional[str]:
        """
        Parse description for a parameter from parameter_meta.
        
        Supports two formats:
        1. Simple string: "This is a description"
        2. Dictionary with description field: {"description": "This is a description", "other": "value"}
        
        Args:
            parameter_meta: Dictionary of parameter metadata
            name: Parameter name to look up
            
        Returns:
            Description string or None if not found
        """
        raw_description = parameter_meta.get(name)
        if not raw_description:
            return None
        
        # Try to parse as a dictionary (JSON-like format)
        description = self._try_parse_as_dict(raw_description)
        if description:
            return description
        
        # Fall back to using the raw string as description
        logger.debug(f"Using raw string as description for parameter '{name}': {raw_description}")
        return raw_description
    
    @staticmethod
    def _try_parse_as_dict(raw_value: str) -> Optional[str]:
        """
        Try to parse a string as a dictionary and extract the 'description' field.
        
        Args:
            raw_value: Raw string value from parameter_meta
            
        Returns:
            Description value if parsing succeeds and 'description' key exists, None otherwise
        """
        try:
            parsed = ast.literal_eval(raw_value)
            if isinstance(parsed, dict):
                return parsed.get("description")
        except (ValueError, SyntaxError, AttributeError):
            pass
        return None

    def _parse_input(self, inp: WDL.Tree.Decl, parameter_meta: dict[str, str]) -> WDLInput:
        """Parse a WDL input declaration."""
        name = inp.name
        wdl_type = self._parse_type(inp.type)
        description = self._parse_description(parameter_meta, name)
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
    def _extract_description(obj) -> Optional[str]:
        """Extract description from meta section."""
        if hasattr(obj, "meta") and obj.meta:
            if "description" in obj.meta:
                return str(obj.meta["description"])
        return None
    
    @staticmethod
    def _parse_meta(obj) -> Dict[str, str]:
        """Parse meta section and return all metadata as dict."""
        meta = {}

        if hasattr(obj, "meta") and obj.meta:
            for key, value in obj.meta.items():
                meta[key] = str(value)

        return meta

    @staticmethod
    def _extract_parameter_meta(obj) -> dict[str, str]:
        """Extract parameter_meta from meta section."""
        parameter_meta = {}

        if hasattr(obj, "parameter_meta"):
            param_meta_obj = obj.parameter_meta
            if isinstance(param_meta_obj, dict):
                for key, value in param_meta_obj.items():
                    parameter_meta[key] = str(value)

        return parameter_meta
