from pathlib import Path
import tempfile
import pytest
from tools.codesearch import run as codesearch_run
from tools.codepeek import run as codepeek_run


class TestCodesearch:
    def test_search_finds_match(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    print('hello')\n")
        
        result = codesearch_run("hello", str(tmp_path))
        assert result.success is True
        assert "hello" in result.output

    def test_search_no_match(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo():\n    pass\n")
        
        result = codesearch_run("nonexistent", str(tmp_path))
        assert result.success is True
        assert "No matches" in result.output or result.output == ""

    def test_invalid_path(self):
        result = codesearch_run("test", "/nonexistent/path")
        assert result.success is False
        assert "Path not found" in result.error

    def test_output_truncation(self, tmp_path):
        test_file = tmp_path / "large.py"
        lines = [f"# Line {i}" * 10 for i in range(500)]
        test_file.write_text("\n".join(lines))
        
        result = codesearch_run("Line", str(tmp_path))
        assert len(result.output) <= 2000 + len("\n...[truncated]")


class TestCodepeek:
    def test_peek_returns_lines(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3\nline4\nline5\n")
        
        result = codepeek_run(str(test_file), 1, 3)
        assert result.success is True
        assert "1: line1" in result.output
        assert "3: line3" in result.output

    def test_peek_invalid_line(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\n")
        
        result = codepeek_run(str(test_file), 10)
        assert result.success is False
        assert "Invalid line number" in result.error

    def test_peek_nonexistent_file(self):
        result = codepeek_run("/nonexistent/file.py", 1)
        assert result.success is False
        assert "not found" in result.error.lower()


class TestApplyDiff:
    def test_apply_valid_patch(self, tmp_path):
        from tools.apply_diff import run as apply_run
        
        test_file = tmp_path / "test.py"
        test_file.write_text("original content\n")
        
        diff = f"--- {test_file}\n+++ {test_file}\n@@ -1 +1 @@\n-original content\n+modified content\n"
        
        result = apply_run(str(test_file), diff)
        assert result.success is True

    def test_apply_invalid_patch(self, tmp_path):
        from tools.apply_diff import run as apply_run
        
        test_file = tmp_path / "test.py"
        test_file.write_text("original\n")
        
        diff = "malformed diff content"
        
        result = apply_run(str(test_file), diff)
        assert result.success is False


class TestLspCheck:
    def test_check_python_file(self, tmp_path):
        from tools.lsp_check import run as lsp_run
        
        test_file = tmp_path / "test.py"
        test_file.write_text("def valid():\n    pass\n")
        
        result = lsp_run(str(test_file))
        assert result.success is True or "pyright" in result.error


class TestRunTests:
    def test_no_test_config(self, tmp_path):
        from tools.run_tests import run as test_run
        
        result = test_run(str(tmp_path))
        assert result.success is False
        assert "No test configuration" in result.error