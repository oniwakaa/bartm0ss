import os
from typing import Iterator, Optional
from dataclasses import dataclass

try:
    import ollama
except ImportError:
    ollama = None


class OllamaUnavailableError(Exception):
    pass


@dataclass
class StreamChunk:
    content: str
    done: bool = False


class OllamaClient:
    def __init__(self, model: str):
        if ollama is None:
            raise OllamaUnavailableError(
                "ollama Python SDK not installed. Run: pip install ollama"
            )
        self.model = model
        self._client = ollama

    def stream(
        self,
        messages: list[dict],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Iterator[StreamChunk]:
        try:
            response = self._client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={
                    "num_predict": max_tokens or 1024,
                    "temperature": temperature or 0.7,
                },
            )
            for chunk in response:
                if "message" in chunk and "content" in chunk["message"]:
                    yield StreamChunk(content=chunk["message"]["content"])
                if chunk.get("done", False):
                    yield StreamChunk(content="", done=True)
        except Exception as e:
            error_msg = str(e).lower()
            if "connection" in error_msg or "refused" in error_msg:
                raise OllamaUnavailableError(
                    f"Ollama server not running. Start with: ollama serve"
                )
            if "model" in error_msg and "not found" in error_msg:
                raise OllamaUnavailableError(
                    f"Model '{self.model}' not found. Pull with: ollama pull {self.model}"
                )
            raise OllamaUnavailableError(f"Ollama error: {e}")

    def generate(
        self,
        messages: list[dict],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        chunks = []
        for chunk in self.stream(messages, max_tokens, temperature):
            if not chunk.done and chunk.content:
                chunks.append(chunk.content)
        return "".join(chunks)