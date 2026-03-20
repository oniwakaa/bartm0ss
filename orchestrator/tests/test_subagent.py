import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from rlm.context import Context, Snippet, SubTask
from rlm.subagent import SubAgentSpawner
from models.ollama_client import OllamaUnavailableError


class TestSubAgent:
    def test_spawn_success(self, tmp_path):
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "subagent_summarize.txt").write_text("Summarize: {{snippet}}\nQuery: {{query}}")
        
        mock_client = MagicMock()
        mock_client.generate.return_value = "This is a summary"
        
        spawner = SubAgentSpawner(prompts_dir=str(prompts_dir))
        spawner._client = mock_client
        
        context = Context(repo_root=str(tmp_path))
        task_id = spawner.spawn("Summarize this", "some code", "summarize", context)
        
        assert task_id is not None
        assert task_id in context.tasks
        assert context.tasks[task_id].status == "resolved"
        assert context.tasks[task_id].result == "This is a summary"

    def test_spawn_ollama_failure(self, tmp_path):
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "subagent_extract.txt").write_text("Extract: {{snippet}}\nQuery: {{query}}")
        
        mock_client = MagicMock()
        mock_client.generate.side_effect = OllamaUnavailableError("Ollama not running")
        
        spawner = SubAgentSpawner(prompts_dir=str(prompts_dir))
        spawner._client = mock_client
        
        context = Context(repo_root=str(tmp_path))
        task_id = spawner.spawn("Extract symbols", "code here", "extract", context)
        
        assert task_id in context.tasks
        assert context.tasks[task_id].status == "failed"
        assert "Ollama not running" in context.tasks[task_id].error

    def test_template_not_found(self, tmp_path):
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        spawner = SubAgentSpawner(prompts_dir=str(prompts_dir))
        context = Context(repo_root=str(tmp_path))
        
        with pytest.raises(FileNotFoundError):
            spawner.spawn("Query", "code", "nonexistent", context)


class TestContext:
    def test_add_snippet(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        sid = context.add_snippet("test.py", 1, 10, "some content")
        
        assert sid in context.snippets
        assert context.snippets[sid].content == "some content"

    def test_add_task(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        tid = context.add_task("Find all functions")
        
        assert tid in context.tasks
        assert context.tasks[tid].status == "pending"

    def test_resolve_task(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        tid = context.add_task("Query")
        
        context.resolve_task(tid, "Result here")
        
        assert context.tasks[tid].status == "resolved"
        assert context.tasks[tid].result == "Result here"

    def test_fail_task(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        tid = context.add_task("Query")
        
        context.fail_task(tid, "Error occurred")
        
        assert context.tasks[tid].status == "failed"
        assert context.tasks[tid].error == "Error occurred"

    def test_summary_prompt_budget(self, tmp_path):
        context = Context(repo_root=str(tmp_path))
        
        for i in range(100):
            context.add_snippet(f"file{i}.py", 1, 10, f"content {i}")
        
        summary = context.build_summary_prompt()
        assert len(summary) < 1000