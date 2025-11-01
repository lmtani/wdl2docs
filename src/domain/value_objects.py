from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List

from src.domain.entitites import WDLDockerImage


@dataclass(frozen=True)
class WDLType:
    """Represents a WDL type (String, Int, File, Array[String], etc.)"""

    name: str
    optional: bool = False
    is_struct: bool = False
    struct_fields: Optional[Dict[str, "WDLType"]] = None

    def __str__(self) -> str:
        type_str = self.name
        if self.optional:
            type_str += "?"
        return type_str

    @property
    def field_count(self) -> int:
        """Returns the number of fields in a struct."""
        if self.struct_fields:
            return len(self.struct_fields)
        return 0


@dataclass(frozen=True)
class WDLCommand:
    """Represents a task command."""

    raw_command: str
    formatted_command: str  # After dedent and formatting


@dataclass(frozen=True)
class WDLInput:
    """Represents an input parameter for a task or workflow."""

    name: str
    type: WDLType
    description: Optional[str] = None
    default_value: Optional[str] = None

    @property
    def has_default(self) -> bool:
        return self.default_value is not None

    @property
    def is_struct(self) -> bool:
        """Check if this input is a struct type."""
        return self.type.is_struct if self.type else False


@dataclass
class WDLOutput:
    """Represents an output from a task or workflow."""

    name: str
    type: WDLType
    description: Optional[str] = None
    expression: Optional[str] = None


@dataclass
class WDLImport:
    """Represents an import statement in a WDL file."""

    path: str
    namespace: Optional[str] = None
    resolved_path: Optional[Path] = None

    @property
    def display_name(self) -> str:
        """Returns a human-readable name for this import."""
        if self.namespace:
            return self.namespace
        return Path(self.path).stem


@dataclass
class WDLTask:
    """Represents a WDL task."""

    name: str
    description: Optional[str] = None
    inputs: List[WDLInput] = field(default_factory=list)
    outputs: List[WDLOutput] = field(default_factory=list)
    command: Optional[WDLCommand] = None
    runtime: Dict[str, str] = field(default_factory=dict)
    meta: Dict[str, str] = field(default_factory=dict)
    author: Optional[str] = None
    email: Optional[str] = None

    @property
    def has_description(self) -> bool:
        return self.description is not None
    
    @property
    def has_author(self) -> bool:
        return self.author is not None
    
    @property
    def has_email(self) -> bool:
        return self.email is not None

    @property
    def has_inputs(self) -> bool:
        return len(self.inputs) > 0

    @property
    def has_outputs(self) -> bool:
        return len(self.outputs) > 0

    @property
    def has_command(self) -> bool:
        return self.command is not None

    @property
    def has_runtime(self) -> bool:
        return len(self.runtime) > 0


@dataclass
class WDLCall:
    """Represents a call to a task or subworkflow."""

    name: str
    task_or_workflow: str
    alias: Optional[str] = None
    inputs_mapping: Dict[str, str] = field(default_factory=dict)
    is_local: bool = True  # True if defined in same file, False if imported
    link_target: Optional[str] = None  # URL for external, #anchor for local
    call_type: str = "task"  # "task" or "workflow"

    @property
    def display_name(self) -> str:
        return self.alias if self.alias else self.name

    @property
    def is_external(self) -> bool:
        """Returns True if this call references an external file."""
        return not self.is_local

    @property
    def is_workflow_call(self) -> bool:
        """Returns True if this call references a workflow."""
        return self.call_type == "workflow"

    @property
    def is_task_call(self) -> bool:
        """Returns True if this call references a task."""
        return self.call_type == "task"


@dataclass
class WDLWorkflow:
    """Represents a WDL workflow."""

    name: str
    description: Optional[str] = None
    inputs: List[WDLInput] = field(default_factory=list)
    outputs: List[WDLOutput] = field(default_factory=list)
    calls: List[WDLCall] = field(default_factory=list)
    docker_images: List[WDLDockerImage] = field(default_factory=list)
    mermaid_graph: Optional[str] = None  # Mermaid diagram representation
    meta: Dict[str, str] = field(default_factory=dict)
    author: Optional[str] = None
    email: Optional[str] = None

    @property
    def has_description(self) -> bool:
        return self.description is not None
    
    @property
    def has_author(self) -> bool:
        return self.author is not None
    
    @property
    def has_email(self) -> bool:
        return self.email is not None

    @property
    def has_inputs(self) -> bool:
        return len(self.inputs) > 0

    @property
    def has_outputs(self) -> bool:
        return len(self.outputs) > 0

    @property
    def has_calls(self) -> bool:
        return len(self.calls) > 0

    @property
    def has_docker_images(self) -> bool:
        return len(self.docker_images) > 0

    @property
    def has_graph(self) -> bool:
        return self.mermaid_graph is not None and len(self.mermaid_graph) > 0


@dataclass
class WDLDocument:
    """
    Represents a complete WDL file.

    A WDL file can contain:
    - Multiple tasks (and no workflow)
    - A workflow and multiple tasks
    - A workflow with imports to other workflows/tasks
    """

    file_path: Path
    relative_path: Path
    version: str = "1.0"
    workflow: Optional[WDLWorkflow] = None
    tasks: List[WDLTask] = field(default_factory=list)
    imports: List[WDLImport] = field(default_factory=list)
    source_code: Optional[str] = None

    @property
    def name(self) -> str:
        """Returns the name of this document (workflow name or file name)."""
        if self.workflow:
            return self.workflow.name
        return self.file_path.stem

    @property
    def has_workflow(self) -> bool:
        return self.workflow is not None

    @property
    def has_tasks(self) -> bool:
        return len(self.tasks) > 0

    @property
    def has_imports(self) -> bool:
        return len(self.imports) > 0

    @property
    def document_type(self) -> str:
        """Returns the type of this document: workflow, tasks, or mixed."""
        if self.has_workflow and self.has_tasks:
            return "mixed"
        elif self.has_workflow:
            return "workflow"
        elif self.has_tasks:
            return "tasks"
        else:
            return "empty"

    @property
    def is_external(self) -> bool:
        """Returns True if this document is from an external/third-party source."""
        # Normalize path to handle ../ references before checking
        path_str = str(self.relative_path)
        # Check if 'external' appears anywhere in the parts
        parts = Path(path_str).parts
        return "external" in parts

    @property
    def description(self) -> Optional[str]:
        """Returns the description from workflow or first task."""
        if self.workflow and self.workflow.description:
            return self.workflow.description
        if self.tasks and self.tasks[0].description:
            return self.tasks[0].description
        return None
