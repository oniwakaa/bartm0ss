import difflib
from pathlib import Path
from typing import Optional
from . import ToolResult


def run(filepath: str, diff_content: str, repo_root: Optional[str] = None) -> ToolResult:
    file_path = Path(filepath)
    
    if not file_path.exists():
        return ToolResult(output="", success=False, error=f"File not found: {filepath}")
    
    if repo_root:
        repo = Path(repo_root)
        try:
            file_path.resolve().relative_to(repo)
        except ValueError:
            return ToolResult(output="", success=False, error="Path outside repo root")
    
    try:
        original = file_path.read_text().splitlines(keepends=True)
        modified = original.copy()
        
        patch_lines = diff_content.splitlines(keepends=True)
        patch = list(difflib.unified_diff(original, modified, fromfile=str(file_path)))
        
        success = apply_patch(file_path, diff_content)
        
        if success:
            return ToolResult(output=f"Patch applied to {filepath}", success=True)
        else:
            return ToolResult(output="", success=False, error="Patch failed to apply")
    except Exception as e:
        return ToolResult(output="", success=False, error=str(e))


def apply_patch(file_path: Path, diff_content: str) -> bool:
    import subprocess
    
    result = subprocess.run(
        ["patch", "-p1", "-u", "--dry-run", str(file_path)],
        input=diff_content,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        return False
    
    result = subprocess.run(
        ["patch", "-p1", "-u", str(file_path)],
        input=diff_content,
        capture_output=True,
        text=True,
    )
    
    return result.returncode == 0