"""
Docker Image Extractor - Infrastructure Layer

Extracts Docker image information from WDL tasks and workflows.
"""

import logging
from typing import Optional, Dict, List

import WDL.Tree

from src.domain.entitites import WDLDockerImage

logger = logging.getLogger(__name__)


class DockerExtractor:
    """Extracts Docker image information from WDL elements."""

    @staticmethod
    def extract_from_task(task: WDL.Tree.Task, call_name: str) -> Optional[Dict]:
        """
        Extract Docker image from a task's runtime section.

        Args:
            task: WDL Task object
            call_name: Name of the call using this task

        Returns:
            Dictionary with image information, or None if no docker image found.
            Dictionary contains:
                - image: str - Image string
                - is_parameterized: bool
                - parameter_name: Optional[str]
                - default_value: Optional[str]
                - image_key: str - Unique key for grouping
        """
        if not hasattr(task, "runtime") or not task.runtime:
            return None

        runtime = task.runtime

        # Runtime is a dict-like object mapping keys to expressions
        runtime_dict = DockerExtractor._convert_runtime_to_dict(runtime)
        if not runtime_dict:
            return None

        # Look for 'docker' or 'container' key
        docker_key = DockerExtractor._find_docker_key(runtime_dict)
        if not docker_key:
            return None

        docker_value = runtime_dict[docker_key]

        # Analyze docker value
        is_parameterized, parameter_name, image_str = DockerExtractor._analyze_docker_value(docker_value)

        # Find default value if parameterized
        default_value = None
        if is_parameterized and parameter_name:
            default_value = DockerExtractor._find_default_value(task, parameter_name)

        # Create unique key for grouping
        image_key = DockerExtractor._create_image_key(is_parameterized, parameter_name, default_value, image_str)

        return {
            "image": image_str,
            "is_parameterized": is_parameterized,
            "parameter_name": parameter_name,
            "default_value": default_value,
            "image_key": image_key,
        }

    @staticmethod
    def extract_from_workflow(workflow: WDL.Tree.Workflow) -> List[WDLDockerImage]:
        """
        Extract Docker images used by tasks called in the workflow.

        Args:
            workflow: WDL Workflow object

        Returns:
            List of WDLDockerImage objects
        """
        docker_images_dict = {}  # Dictionary to group by image

        # Get tasks available to this workflow
        tasks_by_name = DockerExtractor._build_task_map(workflow)

        logger.debug(f"Found {len(tasks_by_name)} tasks (local + imported) for workflow {workflow.name}")

        # Process workflow body to extract docker images
        if hasattr(workflow, "body") and workflow.body:
            DockerExtractor._process_workflow_body(workflow.body, tasks_by_name, docker_images_dict)

        # Convert dictionary to list of WDLDockerImage objects
        docker_images = [
            WDLDockerImage(
                image=info["image"],
                task_names=info["task_names"],
                is_parameterized=info["is_parameterized"],
                parameter_name=info["parameter_name"],
                default_value=info.get("default_value"),
            )
            for info in docker_images_dict.values()
        ]

        logger.debug(f"Total unique docker images found in workflow {workflow.name}: {len(docker_images)}")
        return docker_images

    @staticmethod
    def _convert_runtime_to_dict(runtime) -> Dict:
        """Convert runtime object to dictionary."""
        runtime_dict = {}
        try:
            if hasattr(runtime, "items"):
                runtime_dict = dict(runtime.items())
            elif isinstance(runtime, dict):
                runtime_dict = runtime
            else:
                # Try to iterate over it
                for key, value in runtime:
                    runtime_dict[key] = value
        except Exception as e:
            logger.debug(f"Could not convert runtime to dict: {e}")

        return runtime_dict

    @staticmethod
    def _find_docker_key(runtime_dict: Dict) -> Optional[str]:
        """Find docker key in runtime dictionary."""
        for key in ["docker", "container", "dockerImage"]:
            if key in runtime_dict:
                return key
        return None

    @staticmethod
    def _analyze_docker_value(docker_value) -> tuple[bool, Optional[str], str]:
        """
        Analyze docker value to determine if parameterized.

        Returns:
            Tuple of (is_parameterized, parameter_name, image_str)
        """
        is_parameterized = False
        parameter_name = None
        image_str = str(docker_value)

        # Check if it's an expression (contains references to inputs)
        if hasattr(docker_value, "__class__"):
            class_name = docker_value.__class__.__name__

            # Check if it's any kind of expression (not a literal string)
            if any(x in class_name for x in ["Expr", "Get", "Ident", "Apply"]):
                is_parameterized = True
                # Try to extract the parameter name
                try:
                    if hasattr(docker_value, "name"):
                        parameter_name = docker_value.name
                    elif hasattr(docker_value, "expr"):
                        parameter_name = str(docker_value.expr)
                except Exception:
                    pass

        # Additional check: if it doesn't start with quotes and doesn't contain /, it's likely a variable
        if (
            not is_parameterized
            and not image_str.startswith(('"', "'"))
            and "/" not in image_str
            and ":" not in image_str
        ):
            is_parameterized = True
            parameter_name = image_str

        # If it's a literal string without interpolation, clean up quotes
        if not is_parameterized and ('"' in image_str or "'" in image_str):
            image_str = image_str.strip("\"'")

        return is_parameterized, parameter_name, image_str

    @staticmethod
    def _find_default_value(task: WDL.Tree.Task, parameter_name: str) -> Optional[str]:
        """Find default value for a parameterized docker image."""
        if not hasattr(task, "available_inputs"):
            return None

        for inp in task.available_inputs:
            if inp.name == parameter_name:
                # Check if it has a default value
                if hasattr(inp, "value") and inp.value and hasattr(inp.value, "expr") and inp.value.expr:
                    try:
                        # Try to get the literal value
                        if hasattr(inp.value.expr, "literal"):
                            return str(inp.value.expr.literal).strip("\"'")
                        else:
                            return str(inp.value.expr).strip("\"'")
                    except Exception as e:
                        logger.debug(f"Could not extract default value for {parameter_name}: {e}")
                break

        return None

    @staticmethod
    def _create_image_key(
        is_parameterized: bool,
        parameter_name: Optional[str],
        default_value: Optional[str],
        image_str: str,
    ) -> str:
        """Create unique key for grouping images."""
        if is_parameterized:
            if default_value:
                # Group by default value, but keep parameterized flag
                return default_value
            else:
                return f"parameterized:{parameter_name or 'unknown'}"
        else:
            return image_str

    @staticmethod
    def _build_task_map(workflow: WDL.Tree.Workflow) -> Dict[str, WDL.Tree.Task]:
        """Build map of task names to task objects."""
        tasks_by_name = {}

        # Get local tasks from parent document
        if hasattr(workflow, "parent") and hasattr(workflow.parent, "tasks"):
            tasks_by_name = {task.name: task for task in workflow.parent.tasks}

        # Get tasks from imports
        if hasattr(workflow, "parent") and hasattr(workflow.parent, "imports"):
            for imp in workflow.parent.imports:
                if hasattr(imp, "doc") and imp.doc:
                    # Add tasks from imported document
                    if hasattr(imp.doc, "tasks"):
                        for task in imp.doc.tasks:
                            # Use the full qualified name if there's a namespace
                            if hasattr(imp, "namespace") and imp.namespace:
                                qualified_name = f"{imp.namespace}.{task.name}"
                                tasks_by_name[qualified_name] = task
                            # Also add without namespace for direct references
                            tasks_by_name[task.name] = task

        return tasks_by_name

    @staticmethod
    def _process_workflow_body(body: List, tasks_by_name: Dict[str, WDL.Tree.Task], docker_images_dict: Dict) -> None:
        """Process workflow body elements to extract docker images."""
        elements_to_process = list(body)

        while elements_to_process:
            element = elements_to_process.pop(0)

            # If it's a scatter or conditional, add its body to the processing queue
            if isinstance(element, (WDL.Tree.Scatter, WDL.Tree.Conditional)):
                if hasattr(element, "body") and element.body:
                    elements_to_process.extend(element.body)

            # Process Call elements
            elif isinstance(element, WDL.Tree.Call):
                DockerExtractor._process_call(element, tasks_by_name, docker_images_dict)

    @staticmethod
    def _process_call(
        call: WDL.Tree.Call,
        tasks_by_name: Dict[str, WDL.Tree.Task],
        docker_images_dict: Dict,
    ) -> None:
        """Process a single call element."""
        task_name = str(call.callee) if hasattr(call, "callee") else call.name

        # Try to find the task definition
        task = None
        if hasattr(call, "callee") and hasattr(call.callee, "name"):
            task_lookup_name = call.callee.name
            task = tasks_by_name.get(task_lookup_name)

        if task:
            # Extract docker image from task runtime
            docker_info = DockerExtractor.extract_from_task(task, call.name)
            if docker_info:
                # Group by image identifier
                image_key = docker_info["image_key"]

                if image_key not in docker_images_dict:
                    docker_images_dict[image_key] = {
                        "image": docker_info["image"],
                        "is_parameterized": docker_info["is_parameterized"],
                        "parameter_name": docker_info["parameter_name"],
                        "default_value": docker_info.get("default_value"),
                        "task_names": [],
                    }

                docker_images_dict[image_key]["task_names"].append(call.name)
                logger.debug(f"Added task {call.name} to docker image {image_key}")
            else:
                logger.debug(f"No docker image found for task {call.name}")
        else:
            logger.debug(f"Task {task_name} not found in local tasks, might be imported")
