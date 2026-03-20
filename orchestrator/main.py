#!/usr/bin/env python3
import sys
import json
from typing import Any
from rlm.loop import RLMLoop, EventType, LoopEvent

def run_task(task: str, repo_root: str = ".", non_interactive: bool = True) -> list[dict]:
    loop = RLMLoop(repo_root=repo_root, non_interactive=non_interactive)
    events = []
    for event in loop.run(task):
        events.append({
            "type": event.type.value,
            "content": event.content,
            "timestamp": event.timestamp,
        })
    return events


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")
    
    if method == "task.run":
        task = params.get("goal", "")
        repo = params.get("repo_root", ".")
        non_interactive = params.get("non_interactive", True)
        
        events = run_task(task, repo, non_interactive)
        return {"jsonrpc": "2.0", "id": request_id, "result": {"events": events}}
    
    if method == "task.cancel":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"status": "cancelled"}}
    
    if method == "config.get":
        from models.config import ROOT_MODEL, SUBAGENT_MODEL, ROOT_CONTEXT_LIMIT
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "rootModel": ROOT_MODEL,
                "subagentModel": SUBAGENT_MODEL,
                "contextLimit": ROOT_CONTEXT_LIMIT,
            },
        }
    
    if method == "config.set":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"status": "ok"}}
    
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}


def main():
    buffer = ""
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        buffer += line
        if buffer.endswith("\n"):
            try:
                request = json.loads(buffer.strip())
                response = handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
            except json.JSONDecodeError as e:
                print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Parse error: {e}"}}))
                sys.stdout.flush()
            finally:
                buffer = ""


if __name__ == "__main__":
    main()