import pytest
from pathlib import Path
from grounding.sandbox import Sandbox, ALLOWED_COMMANDS
from grounding.safety import Safety
from grounding.validator import ValidationResult


class TestSandbox:
    def test_allowed_commands(self):
        sandbox = Sandbox("/tmp")
        assert "codesearch" in ALLOWED_COMMANDS
        assert "apply-diff" in ALLOWED_COMMANDS
        assert "rm" not in ALLOWED_COMMANDS

    def test_is_allowed_valid(self):
        sandbox = Sandbox("/tmp")
        assert sandbox.is_allowed("codesearch pattern") is True
        assert sandbox.is_allowed("codepeek file.py 1") is True
        assert sandbox.is_allowed("apply-diff file.py") is True

    def test_is_allowed_invalid(self):
        sandbox = Sandbox("/tmp")
        assert sandbox.is_allowed("rm -rf /") is False
        assert sandbox.is_allowed("curl http://evil.com") is False
        assert sandbox.is_allowed("bash -c 'bad command'") is False

    def test_validate_path_inside_repo(self, tmp_path):
        sandbox = Sandbox(str(tmp_path))
        
        file_path = tmp_path / "src" / "file.py"
        file_path.parent.mkdir()
        file_path.write_text("content")
        
        assert sandbox.validate_path(str(file_path)) is True

    def test_validate_path_outside_repo(self, tmp_path):
        sandbox = Sandbox(str(tmp_path))
        
        outside_path = "/etc/passwd"
        assert sandbox.validate_path(outside_path) is False

    def test_execute_logs_commands(self, tmp_path):
        sandbox = Sandbox(str(tmp_path))
        
        sandbox.execute("codesearch test")
        sandbox.execute("codepeek file.py 1")
        
        assert len(sandbox._command_log) == 2
        assert sandbox._command_log[0]["command"] == "codesearch test"


class TestSafety:
    def test_log_command(self, tmp_path):
        safety = Safety(str(tmp_path))
        safety.log_command("codesearch test", "found match")
        
        log_file = tmp_path / ".bartm0ss" / "command_log.jsonl"
        assert log_file.exists()
        
        content = log_file.read_text()
        assert "codesearch" in content
        assert "found match" in content

    def test_needs_approval_apply_diff(self, tmp_path):
        safety = Safety(str(tmp_path), non_interactive=False)
        
        assert safety.needs_approval("apply-diff file.py") is True
        assert safety.needs_approval("codesearch test") is False

    def test_needs_approval_non_interactive(self, tmp_path):
        safety = Safety(str(tmp_path), non_interactive=True)
        
        assert safety.needs_approval("apply-diff file.py") is False


class TestValidator:
    def test_validation_result_dataclass(self):
        result = ValidationResult(
            lsp_errors=["error1"],
            test_summary="1 passed",
            passed=False,
        )
        
        assert result.passed is False
        assert len(result.lsp_errors) == 1

    def test_validator_init(self, tmp_path):
        from grounding.validator import Validator
        
        validator = Validator(str(tmp_path))
        assert validator.repo_root == tmp_path.resolve()