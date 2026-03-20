from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import subprocess


@dataclass
class ValidationResult:
    lsp_errors: list[str]
    test_summary: str
    format_summary: str
    passed: bool
    error: Optional[str] = None


class Validator:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root).resolve()
    
    def run(self, target: Optional[str] = None) -> ValidationResult:
        lsp_result = self._run_lsp(target)
        test_result = self._run_tests(target)
        format_result = self._run_formatter(target)
        
        passed = lsp_result.success and test_result.success
        
        return ValidationResult(
            lsp_errors=[] if lsp_result.success else [lsp_result.error or "LSP check failed"],
            test_summary=test_result.output if test_result.success else (test_result.error or "Tests failed"),
            format_summary=format_result.output if format_result.success else (format_result.error or "Formatting check failed"),
            passed=passed,
        )
    
    def _run_lsp(self, target: Optional[str]) -> "ToolResult":
        from tools.lsp_check import run as lsp_run
        target_path = target or str(self.repo_root)
        return lsp_run(target_path)
    
    def _run_tests(self, target: Optional[str]) -> "ToolResult":
        from tools.run_tests import run as test_run
        return test_run(target)
    
    def _run_formatter(self, target: Optional[str]) -> "ToolResult":
        from tools import ToolResult
        
        target_path = Path(target) if target else self.repo_root
        ext = target_path.suffix if target_path.is_file() else ""
        
        if ext in (".py", "") and ext != ".ts" and ext != ".tsx" and ext != ".js":
            return self._format_python(target_path)
        elif ext in (".ts", ".tsx", ".js", ".jsx", ".json", ".md"):
            return self._format_with_prettier(target_path)
        
        return ToolResult(output="No formatter needed", success=True)
    
    def _format_python(self, target: Path) -> "ToolResult":
        from tools import ToolResult
        
        try:
            result = subprocess.run(
                ["black", "--check", str(target)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return ToolResult(output="Python formatting OK", success=True)
            return ToolResult(output="", success=False, error=result.stderr or "Black formatting issues found")
        except FileNotFoundError:
            return ToolResult(output="", success=True, error="black not installed, skipping")
        except Exception as e:
            return ToolResult(output="", success=False, error=str(e))
    
    def _format_with_prettier(self, target: Path) -> "ToolResult":
        from tools import ToolResult
        
        try:
            result = subprocess.run(
                ["npx", "prettier", "--check", str(target)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return ToolResult(output="Prettier formatting OK", success=True)
            return ToolResult(output="", success=False, error="Prettier formatting issues found")
        except FileNotFoundError:
            return ToolResult(output="", success=True, error="prettier not installed, skipping")
        except Exception as e:
            return ToolResult(output="", success=False, error=str(e))