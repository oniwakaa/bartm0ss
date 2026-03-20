from pathlib import Path
from typing import Optional
from . import ToolResult


def run(filepath: str, start_line: int, n_lines: Optional[int] = None) -> ToolResult:
    file_path = Path(filepath)
    
    if not file_path.exists():
        return ToolResult(output="", success=False, error=f"File not found: {filepath}")
    
    if not file_path.is_file():
        return ToolResult(output="", success=False, error=f"Not a file: {filepath}")
    
    try:
        lines = file_path.read_text().splitlines()
        
        if start_line < 1 or start_line > len(lines):
            return ToolResult(output="", success=False, error=f"Invalid line number: {start_line}")
        
        end_line = start_line + (n_lines or 50) - 1
        end_line = min(end_line, len(lines))
        
        selected = lines[start_line - 1:end_line]
        numbered = [f"{i}: {line}" for i, line in enumerate(selected, start=start_line)]
        
        return ToolResult(output="\n".join(numbered), success=True)
    except Exception as e:
        return ToolResult(output="", success=False, error=str(e))