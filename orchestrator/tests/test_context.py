import pytest
from pathlib import Path
from rlm.context import Context, FileMetadata, Snippet, SubTask


class TestFileMetadata:
    def test_create_file_metadata(self):
        meta = FileMetadata(
            path="/path/to/file.py",
            content_hash="abc123",
            line_count=100,
            language="python"
        )
        assert meta.path == "/path/to/file.py"
        assert meta.content_hash == "abc123"
        assert meta.line_count == 100
        assert meta.language == "python"

    def test_file_metadata_optional_language(self):
        meta = FileMetadata(
            path="/path/to/file.py",
            content_hash="abc123",
            line_count=50
        )
        assert meta.language is None


class TestSnippet:
    def test_create_snippet(self):
        snippet = Snippet(
            snippet_id="snip001",
            file_path="/path/to/file.py",
            start_line=10,
            end_line=20,
            content="def hello():\n    print('hello')"
        )
        assert snippet.snippet_id == "snip001"
        assert snippet.start_line == 10
        assert snippet.end_line == 20


class TestSubTask:
    def test_create_pending_task(self):
        task = SubTask(
            task_id="task001",
            query="Find all functions"
        )
        assert task.task_id == "task001"
        assert task.status == "pending"
        assert task.result is None
        assert task.error is None

    def test_resolved_task(self):
        task = SubTask(
            task_id="task001",
            query="Find all functions",
            status="resolved",
            result="Found 5 functions"
        )
        assert task.status == "resolved"
        assert task.result == "Found 5 functions"


class TestContext:
    def test_create_context(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        assert context.repo_root == str(tmp_path)
        assert len(context.snippets) == 0
        assert len(context.tasks) == 0

    def test_add_snippet(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3\n")
        
        sid = context.add_snippet(str(test_file), 1, 2, "line1\nline2")
        
        assert sid in context.snippets
        assert context.snippets[sid].content == "line1\nline2"
        assert context.snippets[sid].file_path == str(test_file)

    def test_add_snippet_generates_unique_ids(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        
        sid1 = context.add_snippet("file.py", 1, 10, "content1")
        sid2 = context.add_snippet("file.py", 11, 20, "content2")
        
        assert sid1 != sid2

    def test_get_snippet(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        
        sid = context.add_snippet("file.py", 1, 10, "some content")
        
        snippet = context.get_snippet(sid)
        assert snippet is not None
        assert snippet.content == "some content"

    def test_get_nonexistent_snippet(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        
        snippet = context.get_snippet("nonexistent")
        assert snippet is None

    def test_add_task(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        
        tid = context.add_task("Find all TODO comments")
        
        assert tid in context.tasks
        assert context.tasks[tid].query == "Find all TODO comments"
        assert context.tasks[tid].status == "pending"

    def test_resolve_task(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        tid = context.add_task("Query")
        
        context.resolve_task(tid, "Result here")
        
        assert context.tasks[tid].status == "resolved"
        assert context.tasks[tid].result == "Result here"
        assert context.tasks[tid].error is None

    def test_fail_task(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        tid = context.add_task("Query")
        
        context.fail_task(tid, "Something went wrong")
        
        assert context.tasks[tid].status == "failed"
        assert context.tasks[tid].error == "Something went wrong"
        assert context.tasks[tid].result is None

    def test_resolve_nonexistent_task(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        
        context.resolve_task("nonexistent", "Result")
        
        assert "nonexistent" not in context.tasks

    def test_build_summary_prompt(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        
        context.add_snippet("file1.py", 1, 10, "content1")
        context.add_snippet("file2.py", 5, 15, "content2")
        
        summary = context.build_summary_prompt()
        
        assert "Repo:" in summary
        assert str(tmp_path) in summary
        assert "Snippets: 2" in summary

    def test_summary_prompt_token_budget(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        
        for i in range(100):
            context.add_snippet(f"file{i}.py", 1, 10, f"content {i}" * 10)
        
        summary = context.build_summary_prompt()
        
        assert len(summary) < 1000

    def test_add_file_metadata(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        
        meta = FileMetadata(
            path=str(tmp_path / "test.py"),
            content_hash="abc123",
            line_count=50,
            language="python"
        )
        context.file_metadata[meta.path] = meta
        
        assert len(context.file_metadata) == 1
        assert context.file_metadata[meta.path].line_count == 50