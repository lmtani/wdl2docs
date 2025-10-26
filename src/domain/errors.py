from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ParseError:
    """Represents an error encountered during WDL parsing."""

    file_path: Path
    relative_path: Path
    error_type: str  # "SyntaxError", "ValidationError", "ImportError", etc.
    error_message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def severity(self) -> str:
        """Returns severity level: error or warning."""
        if "warning" in self.error_type.lower():
            return "warning"
        return "error"

    @property
    def short_message(self) -> str:
        """Returns a shortened version of the error message."""
        max_length = 200
        if len(self.error_message) <= max_length:
            return self.error_message
        return self.error_message[:max_length] + "..."

    @property
    def location_info(self) -> Optional[str]:
        """Returns formatted location information if available."""
        if self.line_number is not None and self.column_number is not None:
            return f"Line {self.line_number}, Column {self.column_number}"
        elif self.line_number is not None:
            return f"Line {self.line_number}"
        return None
