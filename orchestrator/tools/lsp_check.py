import subprocess
from pathlib import Path
from typing import Optional
from . import ToolResult


LSP_SERVERS = {
    ".py": "pyright",
    ".ts": "typescript-language-server",
    ".tsx": "typescript-language-server",
    ".js": "typescript-language-server",
}


def run(filepath: str) -> ToolResult:
    file_path = Path(filepath)
    
    if not file_path.exists():
        return ToolResult(output="", success=False, error=f"File not found: {filepath}")
    
    ext = file_path.suffix
    lsp_server = LSP_SERVERS.get(ext)
    
    if not lsp_server:
        return ToolResult(output="", success=False, error=f"No LSP server configured for {ext}")
    
    if ext == ".py":
        try:
            result = subprocess.run(
                ["pyright", "--outputjson", str(file_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            return ToolResult(output=result.stdout or result.stderr, success=result.returncode == 0)
        except FileNotFoundError:
            return ToolResult(output="", success=False, error="pyright not installed. Run: npm install -g pyright")
        except Exception as e:
            return ToolResult(output="", success=False, error=str(e))
    
    return ToolResult(output=f"LSP check for {filepath} (placeholder)", success=True)