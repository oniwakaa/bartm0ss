import pytest
from unittest.mock import MagicMock, patch
from models.config import ROOT_MODEL, SUBAGENT_MODEL, ROOT_CONTEXT_LIMIT
from models.ollama_client import OllamaClient, OllamaUnavailableError, StreamChunk


class TestConfig:
    def test_default_root_model(self):
        assert ROOT_MODEL == "falcon-h1r-7b-q4_k_m"

    def test_default_subagent_model(self):
        assert SUBAGENT_MODEL == "ai21-jamba-reasoning-3b-q4_k_m"

    def test_default_context_limit(self):
        assert ROOT_CONTEXT_LIMIT == 8192


class TestOllamaClient:
    def test_stream_success(self):
        mock_ollama = MagicMock()
        mock_ollama.chat.return_value = [
            {"message": {"content": "Hello"}},
            {"message": {"content": " world"}},
            {"done": True},
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
            {"message": {"content": "Hello"}},
            {"message": {"content": " world"}},
            {"done": True},
        ]
        
        with patch("models.ollama_client.ollama", mock_ollama):
            client = OllamaClient("test-model")
            result = client.generate([{"role": "user", "content": "Hi"}])
            assert result == "Hello world"

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
        mock_ollama.chat.side_effect = Exception("model not found")
        
        with patch("models.ollama_client.ollama", mock_ollama):
            client = OllamaClient("unknown-model")
            with pytest.raises(OllamaUnavailableError) as exc_info:
                client.generate([{"role": "user", "content": "Hi"}])
            assert "not found" in str(exc_info.value)