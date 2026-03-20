from pathlib import Path
from typing import Optional
from . import ToolResult


def run(query: str, docs_dir: Optional[str] = None) -> ToolResult:
    search_dir = Path(docs_dir) if docs_dir else Path.cwd() / "docs"
    
    if not search_dir.exists():
        return ToolResult(output="", success=False, error=f"Docs directory not found: {search_dir}")
    
    import subprocess
    
    try:
        result = subprocess.run(
            ["rg", "-i", "--no-heading", "-C", "2", query, str(search_dir)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            return ToolResult(output=result.stdout.strip(), success=True)
        elif result.returncode == 1:
            return ToolResult(output="No matches in documentation", success=True)
        else:
            return ToolResult(output="", success=False, error=result.stderr.strip())
    except FileNotFoundError:
        return ToolResult(output="", success=False, error="ripgrep not installed. Run: brew install ripgrep")
    except Exception as e:
        return ToolResult(output="", success=False, error=str(e))