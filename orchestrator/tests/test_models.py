import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import os
from models.config import (
    ROOT_MODEL,
    SUBAGENT_MODEL,
    ROOT_CONTEXT_LIMIT,
    SUBAGENT_CONTEXT_LIMIT,
    MAX_OUTPUT_TOKENS,
    DEFAULT_TEMPERATURE,
)
from models.ollama_client import OllamaClient, OllamaUnavailableError, StreamChunk


class MockMessage:
    def __init__(self, content=""):
        self.content = content


class MockChatResponse:
    def __init__(self, content="", done=False):
        self.message = MockMessage(content)
        self.done = done


class TestConfig:
    def test_default_root_model(self):
        assert ROOT_MODEL == "hf.co/tiiuae/Falcon-H1R-7B-GGUF:Q4_K_M"

    def test_default_subagent_model(self):
        assert SUBAGENT_MODEL == "hf.co/bartowski/ai21labs_AI21-Jamba2-3B-GGUF:Q8_0"

    def test_default_context_limit(self):
        assert ROOT_CONTEXT_LIMIT == 8192

    def test_default_max_output_tokens(self):
        assert MAX_OUTPUT_TOKENS == 1024

    def test_default_temperature(self):
        assert DEFAULT_TEMPERATURE == 0.7


class TestOllamaClient:
    def test_stream_success(self):
        mock_ollama = MagicMock()
        mock_ollama.chat.return_value = [
            MockChatResponse(content="Hello"),
            MockChatResponse(content=" world"),
            MockChatResponse(content="", done=True),
        ]
        
        with patch("models.ollama_client.ollama", mock_ollama):
            client = OllamaClient("test-model")
            chunks = list(client.stream([{"role": "user", "content": "Hi"}]))
            
            assert len(chunks) == 3
            assert chunks[0].content == "Hello"
            assert chunks[1].content == " world"
            assert chunks[2].done is True

    def test_generate_success(self):
        mock_ollama = MagicMock()
        mock_ollama.chat.return_value = [
            MockChatResponse(content="Hello"),
            MockChatResponse(content=" world"),
            MockChatResponse(content="", done=True),
        ]
        
        with patch("models.ollama_client.ollama", mock_ollama):
            client = OllamaClient("test-model")
            result = client.generate([{"role": "user", "content": "Hi"}])
            assert result == "Hello world"

    def test_generate_with_options(self):
        mock_ollama = MagicMock()
        mock_ollama.chat.return_value = [
            MockChatResponse(content="Response"),
            MockChatResponse(content="", done=True),
        ]
        
        with patch("models.ollama_client.ollama", mock_ollama):
            client = OllamaClient("test-model")
            result = client.generate(
                [{"role": "user", "content": "Hi"}],
                max_tokens=500,
                temperature=0.3
            )
            assert result == "Response"
            
            call_args = mock_ollama.chat.call_args
            assert call_args.kwargs["options"]["num_predict"] == 500
            assert call_args.kwargs["options"]["temperature"] == 0.3

    def test_connection_error(self):
        mock_ollama = MagicMock()
        mock_ollama.chat.side_effect = Exception("Connection refused")
        
        with patch("models.ollama_client.ollama", mock_ollama):
            client = OllamaClient("test-model")
            with pytest.raises(OllamaUnavailableError) as exc_info:
                client.generate([{"role": "user", "content": "Hi"}])
            assert "server not running" in str(exc_info.value)

    def test_model_not_found_error(self):
        mock_ollama = MagicMock()
        mock_ollama.chat.side_effect = Exception("model 'unknown-model' not found")
        
        with patch("models.ollama_client.ollama", mock_ollama):
            client = OllamaClient("unknown-model")
            with pytest.raises(OllamaUnavailableError) as exc_info:
                client.generate([{"role": "user", "content": "Hi"}])
            assert "not found" in str(exc_info.value)

    def test_stream_empty_response(self):
        mock_ollama = MagicMock()
        mock_ollama.chat.return_value = [MockChatResponse(content="", done=True)]
        
        with patch("models.ollama_client.ollama", mock_ollama):
            client = OllamaClient("test-model")
            chunks = list(client.stream([{"role": "user", "content": "Hi"}]))
            assert len(chunks) == 1
            assert chunks[0].content == ""
            assert chunks[0].done is True

    def test_generate_empty_response(self):
        mock_ollama = MagicMock()
        mock_ollama.chat.return_value = [MockChatResponse(content="", done=True)]
        
        with patch("models.ollama_client.ollama", mock_ollama):
            client = OllamaClient("test-model")
            result = client.generate([{"role": "user", "content": "Hi"}])
            assert result == ""