from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolResult:
    output: str
    success: bool
    error: Optional[str] = None

    def __post_init__(self):
        max_len = 2000
        if len(self.output) > max_len:
            self.output = self.output[:max_len] + "\n...[truncated]"