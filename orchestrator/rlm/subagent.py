from typing import Optional
from pathlib import Path
from .context import Context
from .parser import parse_lm_output, LMOutput
from models.ollama_client import OllamaClient, OllamaUnavailableError
from models.config import ROOT_MODEL, ROOT_CONTEXT_LIMIT, MAX_OUTPUT_TOKENS
import os


class SubAgentSpawner:
    def __init__(self, prompts_dir: Optional[str] = None):
        base = Path(__file__).parent.parent.parent
        self.prompts_dir = Path(prompts_dir or base / "prompts")
        self._client: Optional[OllamaClient] = None

    def _get_client(self) -> OllamaClient:
        if self._client is None:
            from models.config import SUBAGENT_MODEL
            self._client = OllamaClient(SUBAGENT_MODEL)
        return self._client

    def load_template(self, name: str) -> str:
        template_path = self.prompts_dir / f"subagent_{name}.txt"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        return template_path.read_text()

    def spawn(
        self,
        query: str,
        snippet_content: str,
        template_name: str,
        context: Context,
        max_tokens: int = 512,
    ) -> str:
        task_id = context.add_task(query)
        try:
            template = self.load_template(template_name)
            prompt = template.replace("{{query}}", query).replace(
                "{{snippet}}", snippet_content[:2000]
            )
            client = self._get_client()
            result = client.generate([{"role": "user", "content": prompt}], max_tokens)
            context.resolve_task(task_id, result)
            return task_id
        except OllamaUnavailableError as e:
            context.fail_task(task_id, str(e))
            return task_id
        except Exception as e:
            context.fail_task(task_id, f"Sub-agent error: {e}")
            return task_id