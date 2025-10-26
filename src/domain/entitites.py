from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class WDLDockerImage:
    """Represents a Docker image used by one or more tasks."""

    image: str
    task_names: List[str] = field(default_factory=list)
    is_parameterized: bool = False
    parameter_name: Optional[str] = None
    default_value: Optional[str] = None

    @property
    def display_image(self) -> str:
        """Returns a display-friendly image string."""
        if self.is_parameterized:
            if self.default_value:
                return self.default_value
            if self.parameter_name:
                return f"Parameterized (via {self.parameter_name})"
            return "Parameterized"
        return self.image

    @property
    def short_name(self) -> str:
        """Returns a short name for the image (last part after /)."""
        if self.is_parameterized and self.default_value:
            # Use default value for short name
            parts = self.default_value.split("/")
            base_name = parts[-1] if parts else "parameterized"
            return base_name.split(":")[0]  # Remove tag
        if self.is_parameterized:
            return "parameterized"
        parts = self.image.split("/")
        return parts[-1].split(":")[0] if parts else self.image

    @property
    def task_count(self) -> int:
        """Returns the number of tasks using this image."""
        return len(self.task_names)
