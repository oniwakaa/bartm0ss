import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class ToolResult:
    output: str
    success: bool
    error: Optional[str] = None

    def __post_init__(self):
        max_len = 2000
        if len(self.output) > max_len:
            self.output = self.output[:max_len] + "\n...[truncated]"


def run(pattern: str, path: Optional[str] = None) -> ToolResult:
    search_path = Path(path) if path else Path.cwd()
    
    if not search_path.exists():
        return ToolResult(output="", success=False, error=f"Path not found: {search_path}")
    
    try:
        result = subprocess.run(
            ["rg", "--no-heading", "--line-number", pattern, str(search_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            return ToolResult(output=result.stdout.strip(), success=True)
        elif result.returncode == 1:
            return ToolResult(output="No matches found", success=True)
        else:
            return ToolResult(output="", success=False, error=result.stderr.strip())
    except FileNotFoundError:
        return ToolResult(output="", success=False, error="ripgrep not installed. Run: brew install ripgrep")
    except subprocess.TimeoutExpired:
        return ToolResult(output="", success=False, error="Search timed out")
    except Exception as e:
        return ToolResult(output="", success=False, error=str(e))