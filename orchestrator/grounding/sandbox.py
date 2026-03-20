from pathlib import Path
from typing import Optional


ALLOWED_COMMANDS = {
    "codesearch",
    "codepeek",
    "codeoutline",
    "codestats",
    "apply-diff",
    "lsp-check",
    "run-tests",
    "docsearch",
    "subagent",
}


class CommandNotAllowedError(Exception):
    pass


class PathNotAllowedError(Exception):
    pass


class Sandbox:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root).resolve()
        self._command_log: list[dict] = []

    def is_allowed(self, command: str) -> bool:
        cmd_parts = command.strip().split()
        if not cmd_parts:
            return False
        
        base_cmd = cmd_parts[0]
        return base_cmd in ALLOWED_COMMANDS

    def validate_path(self, target_path: str) -> bool:
        path = Path(target_path).resolve()
        try:
            path.relative_to(self.repo_root)
            return True
        except ValueError:
            return False

    def execute(self, command: str) -> str:
        import json
        from datetime import datetime
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
        }
        
        if not self.is_allowed(command):
            entry["result"] = "rejected"
            self._command_log.append(entry)
            return f"Command '{command}' not in allowlist"
        
        cmd_parts = command.strip().split()
        base_cmd = cmd_parts[0]
        
        if base_cmd in ("codepeek", "codeoutline", "codestats", "lsp-check", "apply-diff"):
            if len(cmd_parts) >= 2:
                target = cmd_parts[1]
                if not self.validate_path(target):
                    entry["result"] = "path_rejected"
                    self._command_log.append(entry)
                    return f"Path '{target}' outside repo root"
        
        entry["result"] = "executed"
        self._command_log.append(entry)
        
        return f"Executed: {command}"