from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
import hashlib


@dataclass
class FileMetadata:
    path: str
    content_hash: str
    line_count: int
    language: Optional[str] = None


@dataclass
class Snippet:
    snippet_id: str
    file_path: str
    start_line: int
    end_line: int
    content: str


@dataclass
class SubTask:
    task_id: str
    query: str
    status: str = "pending"
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class Context:
    repo_root: str
    snippets: dict[str, Snippet] = field(default_factory=dict)
    tasks: dict[str, SubTask] = field(default_factory=dict)
    file_metadata: dict[str, FileMetadata] = field(default_factory=dict)

    def add_snippet(
        self, file_path: str, start_line: int, end_line: int, content: str
    ) -> str:
        snippet_id = self._generate_id(f"{file_path}:{start_line}-{end_line}")
        self.snippets[snippet_id] = Snippet(
            snippet_id=snippet_id,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            content=content,
        )
        return snippet_id

    def get_snippet(self, snippet_id: str) -> Optional[Snippet]:
        return self.snippets.get(snippet_id)

    def add_task(self, query: str) -> str:
        task_id = self._generate_id(query)
        self.tasks[task_id] = SubTask(task_id=task_id, query=query)
        return task_id

    def resolve_task(self, task_id: str, result: str) -> None:
        if task_id in self.tasks:
            self.tasks[task_id].status = "resolved"
            self.tasks[task_id].result = result

    def fail_task(self, task_id: str, error: str) -> None:
        if task_id in self.tasks:
            self.tasks[task_id].status = "failed"
            self.tasks[task_id].error = error

    def build_summary_prompt(self, max_tokens: int = 512) -> str:
        lines = [f"Repo: {self.repo_root}", f"Snippets: {len(self.snippets)}"]
        for sid, snippet in list(self.snippets.items())[:5]:
            lines.append(f"  [{sid}] {snippet.file_path}:{snippet.start_line}")
        lines.append(f"Tasks: {len(self.tasks)}")
        for tid, task in list(self.tasks.items())[:5]:
            status = task.status
            lines.append(f"  [{tid}] {status}: {task.query[:50]}")
        return "\n".join(lines)

    def _generate_id(self, seed: str) -> str:
        return hashlib.md5(seed.encode()).hexdigest()[:8]