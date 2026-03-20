from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class LMOutput:
    thought: Optional[str] = None
    command: Optional[str] = None
    answer: Optional[str] = None
    parse_error: Optional[str] = None


def parse_lm_output(raw: str) -> LMOutput:
    if not raw or not raw.strip():
        return LMOutput(parse_error="Empty input")

    thought = None
    command = None
    answer = None

    thought_match = re.search(r"THOUGHT:\s*(.*?)(?=COMMAND:|ANSWER:|$)", raw, re.DOTALL)
    if thought_match:
        thought = thought_match.group(1).strip()

    command_match = re.search(r"COMMAND:\s*(.*?)(?=ANSWER:|THOUGHT:|$)", raw, re.DOTALL)
    if command_match:
        cmd_raw = command_match.group(1).strip()
        if cmd_raw.upper() == "NONE":
            command = None
        else:
            cmd_line = cmd_raw.split("\n")[0].strip()
            if cmd_line:
                command = cmd_line
            else:
                return LMOutput(parse_error="COMMAND section empty")

    answer_match = re.search(r"ANSWER:\s*(.*?)(?=COMMAND:|THOUGHT:|$)", raw, re.DOTALL)
    if answer_match:
        answer = answer_match.group(1).strip()

    if thought is None and command is None and answer is None:
        return LMOutput(parse_error="No THOUGHT, COMMAND, or ANSWER found")

    return LMOutput(thought=thought, command=command, answer=answer)