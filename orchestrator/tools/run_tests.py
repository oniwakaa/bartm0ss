import subprocess
from pathlib import Path
from typing import Optional
from . import ToolResult


def run(target: Optional[str] = None) -> ToolResult:
    target_path = Path(target) if target else Path.cwd()
    
    if not target_path.exists():
        return ToolResult(output="", success=False, error=f"Target not found: {target}")
    
    pyproject = target_path / "pyproject.toml" if target_path.is_dir() else target_path.parent / "pyproject.toml"
    package_json = target_path / "package.json" if target_path.is_dir() else target_path.parent / "package.json"
    
    if pyproject.exists():
        try:
            result = subprocess.run(
                ["pytest", "-v", "--tb=short", str(target_path) if target else "."],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=target_path if target_path.is_dir() else target_path.parent,
            )
            return ToolResult(output=result.stdout or result.stderr, success=result.returncode == 0)
        except FileNotFoundError:
            return ToolResult(output="", success=False, error="pytest not installed. Run: pip install pytest")
        except subprocess.TimeoutExpired:
            return ToolResult(output="", success=False, error="Tests timed out")
        except Exception as e:
            return ToolResult(output="", success=False, error=str(e))
    
    if package_json.exists():
        try:
            result = subprocess.run(
                ["npm", "test"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=package_json.parent,
            )
            return ToolResult(output=result.stdout or result.stderr, success=result.returncode == 0)
        except FileNotFoundError:
            return ToolResult(output="", success=False, error="npm not installed")
        except subprocess.TimeoutExpired:
            return ToolResult(output="", success=False, error="Tests timed out")
        except Exception as e:
            return ToolResult(output="", success=False, error=str(e))
    
    return ToolResult(output="No test configuration found", success=False, error="No pyproject.toml or package.json")