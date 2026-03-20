import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class Safety:
    def __init__(self, repo_root: str, non_interactive: bool = False):
        self.repo_root = Path(repo_root).resolve()
        self.non_interactive = non_interactive
        self.log_file = self.repo_root / ".bartm0ss" / "command_log.jsonl"
        
        if not self.log_file.parent.exists():
            self.log_file.parent.mkdir(parents=True)
    
    def log_command(self, command: str, result: str, approved: Optional[bool] = None) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "result": result,
        }
        if approved is not None:
            entry["approved"] = approved
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def needs_approval(self, command: str) -> bool:
        if self.non_interactive:
            return False
        
        return command.strip().lower().startswith("apply-diff")
    
    def request_approval(self, command: str, diff: Optional[str] = None) -> bool:
        if self.non_interactive:
            return True
        
        print(f"\nApproval required for: {command}")
        if diff:
            print("Diff:")
            print(diff)
        
        try:
            response = input("Approve? [Y/n]: ").strip().lower()
            return response in ("y", "yes", "")
        except (EOFError, KeyboardInterrupt):
            return False