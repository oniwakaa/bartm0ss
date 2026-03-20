from dataclasses import dataclass
from typing import Iterator, Optional
from enum import Enum
from .context import Context
from .parser import parse_lm_output
from .subagent import SubAgentSpawner
from models.ollama_client import OllamaClient, OllamaUnavailableError
from models.config import ROOT_MODEL, ROOT_CONTEXT_LIMIT, MAX_OUTPUT_TOKENS, DEFAULT_TEMPERATURE
from grounding.sandbox import Sandbox
from grounding.validator import Validator
from pathlib import Path


class EventType(str, Enum):
    THOUGHT = "THOUGHT"
    COMMAND = "COMMAND"
    TOOL_RESULT = "TOOL_RESULT"
    ANSWER = "ANSWER"
    ERROR = "ERROR"
    LOOP_LIMIT = "LOOP_LIMIT"


@dataclass
class LoopEvent:
    type: EventType
    content: str
    timestamp: str


class RLMLoop:
    def __init__(
        self,
        repo_root: str,
        max_iterations: int = 20,
        non_interactive: bool = False,
    ):
        self.repo_root = Path(repo_root).resolve()
        self.context = Context(repo_root=str(self.repo_root))
        self.max_iterations = max_iterations
        self.non_interactive = non_interactive
        self.sandbox = Sandbox(str(self.repo_root))
        self.validator = Validator(str(self.repo_root))
        self._client: Optional[OllamaClient] = None
        self._subagent: Optional[SubAgentSpawner] = None
        self._cancelled = False

    def _get_client(self) -> OllamaClient:
        if self._client is None:
            self._client = OllamaClient(ROOT_MODEL)
        return self._client

    def _get_subagent(self) -> SubAgentSpawner:
        if self._subagent is None:
            self._subagent = SubAgentSpawner()
        return self._subagent

    def _load_system_prompt(self) -> str:
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        system_path = prompts_dir / "root_lm_system.txt"
        if system_path.exists():
            return system_path.read_text()
        return "You are a coding assistant. Respond with THOUGHT, COMMAND, and ANSWER blocks."

    def cancel(self) -> None:
        self._cancelled = True

    def run(self, task: str) -> Iterator[LoopEvent]:
        from datetime import datetime

        def event(type_: EventType, content: str) -> LoopEvent:
            return LoopEvent(type=type_, content=content, timestamp=datetime.now().isoformat())

        client = self._get_client()
        system_prompt = self._load_system_prompt()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Task: {task}\n\n{self.context.build_summary_prompt()}"},
        ]

        iteration = 0
        while iteration < self.max_iterations and not self._cancelled:
            iteration += 1
            try:
                raw_output = client.generate(messages, MAX_OUTPUT_TOKENS, DEFAULT_TEMPERATURE)
            except OllamaUnavailableError as e:
                yield event(EventType.ERROR, str(e))
                return

            parsed = parse_lm_output(raw_output)

            if parsed.parse_error:
                yield event(EventType.ERROR, f"Parse error: {parsed.parse_error}")
                messages.append({"role": "assistant", "content": raw_output})
                messages.append({"role": "user", "content": "Format error. Use THOUGHT/COMMAND/ANSWER format."})
                continue

            if parsed.thought:
                yield event(EventType.THOUGHT, parsed.thought)

            if parsed.answer:
                yield event(EventType.ANSWER, parsed.answer)
                return

            if parsed.command:
                yield event(EventType.COMMAND, parsed.command)
                tool_result = self._dispatch_command(parsed.command)
                yield event(EventType.TOOL_RESULT, tool_result)
                messages.append({"role": "assistant", "content": raw_output})
                messages.append({"role": "user", "content": f"Result: {tool_result}"})

        if self._cancelled:
            yield event(EventType.ERROR, "Task cancelled")
        else:
            yield event(EventType.LOOP_LIMIT, f"Reached {self.max_iterations} iterations")

    def _dispatch_command(self, command: str) -> str:
        if not self.sandbox.is_allowed(command):
            return f"Command rejected: not in allowlist"

        result = self.sandbox.execute(command)
        if command.startswith("apply-diff"):
            validation = self.validator.run()
            result = f"{result}\nValidation: {validation}"

        return result