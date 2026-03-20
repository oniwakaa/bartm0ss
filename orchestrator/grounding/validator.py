from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class ValidationResult:
    lsp_errors: list[str]
    test_summary: str
    passed: bool
    error: Optional[str] = None


class Validator:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root).resolve()
    
    def run(self, target: Optional[str] = None) -> ValidationResult:
        lsp_result = self._run_lsp(target)
        test_result = self._run_tests(target)
        
        passed = lsp_result.success and test_result.success
        
        return ValidationResult(
            lsp_errors=[] if lsp_result.success else [lsp_result.error or "LSP check failed"],
            test_summary=test_result.output if test_result.success else (test_result.error or "Tests failed"),
            passed=passed,
        )
    
    def _run_lsp(self, target: Optional[str]) -> "ToolResult":
        from tools.lsp_check import run as lsp_run
        target_path = target or str(self.repo_root)
        return lsp_run(target_path)
    
    def _run_tests(self, target: Optional[str]) -> "ToolResult":
        from tools.run_tests import run as test_run
        return test_run(target)