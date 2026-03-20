import subprocess
from pathlib import Path
from . import ToolResult


def run(filepath: str) -> ToolResult:
    file_path = Path(filepath)
    
    if not file_path.exists():
        return ToolResult(output="", success=False, error=f"File not found: {filepath}")
    
    if not file_path.is_file():
        return ToolResult(output="", success=False, error=f"Not a file: {filepath}")
    
    try:
        wc_result = subprocess.run(
            ["wc", "-l", "-w", "-c", str(file_path)],
            capture_output=True,
            text=True,
        )
        
        stats = wc_result.stdout.strip()
        
        git_log = subprocess.run(
            ["git", "log", "--oneline", "-5", "--", str(file_path)],
            capture_output=True,
            text=True,
            cwd=file_path.parent,
        )
        
        commits = git_log.stdout.strip() if git_log.returncode == 0 else "No git history"
        
        output = f"File: {filepath}\n{stats}\n\nRecent commits:\n{commits}"
        return ToolResult(output=output, success=True)
    except Exception as e:
        return ToolResult(output="", success=False, error=str(e))