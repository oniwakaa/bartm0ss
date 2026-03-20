import pytest
import json
from unittest.mock import MagicMock, patch
from pathlib import Path
import main


class TestJsonRpcParsing:
    def test_parse_valid_request(self):
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "task.run",
            "params": {"goal": "test task"}
        }
        
        response = main.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response

    def test_parse_malformed_json(self):
        request = "not valid json"
        
        with pytest.raises(json.JSONDecodeError):
            json.loads(request)

    def test_unknown_method(self):
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "unknown.method",
            "params": {}
        }
        
        response = main.handle_request(request)
        
        assert "error" in response
        assert response["error"]["code"] == -32601

    def test_config_get(self):
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "config.get",
            "params": {}
        }
        
        response = main.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 3
        assert "result" in response
        assert "rootModel" in response["result"]
        assert "subagentModel" in response["result"]

    def test_config_set(self):
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "config.set",
            "params": {"rootModel": "new-model"}
        }
        
        response = main.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 4
        assert response["result"]["status"] == "ok"

    def test_task_cancel(self):
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "task.cancel",
            "params": {}
        }
        
        response = main.handle_request(request)
        
        assert response["result"]["status"] == "cancelled"

    def test_task_run_params(self):
        request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "task.run",
            "params": {
                "goal": "test goal",
                "repo_root": "/tmp/test",
                "non_interactive": True
            }
        }
        
        response = main.handle_request(request)
        
        assert "events" in response["result"]


class TestMainEntryPoint:
    def test_run_task(self, tmp_path):
        from unittest.mock import MagicMock, patch
        import main
        
        mock_loop = MagicMock()
        mock_event_thought = MagicMock(
            type=main.EventType.THOUGHT, 
            content="thinking", 
            timestamp="2024-01-01T00:00:00"
        )
        mock_event_answer = MagicMock(
            type=main.EventType.ANSWER, 
            content="done", 
            timestamp="2024-01-01T00:00:01"
        )
        mock_loop.run.return_value = iter([mock_event_thought, mock_event_answer])
        
        with patch("main.RLMLoop", return_value=mock_loop):
            events = main.run_task("test", str(tmp_path))
            
            assert len(events) == 2
            assert events[0]["type"] == "THOUGHT"
            assert events[1]["type"] == "ANSWER"


class TestStdinHandling:
    def test_stdin_buffer_management(self):
        buffer = ""
        lines = ["line1\n", "line2\n", "partial"]
        
        for line in lines[:2]:
            buffer += line
            if buffer.endswith("\n"):
                processed = buffer.strip()
                try:
                    parsed = json.loads(processed)
                    assert isinstance(parsed, dict)
                except json.JSONDecodeError:
                    pass
                buffer = ""
        
        assert "partial" in buffer or buffer == ""