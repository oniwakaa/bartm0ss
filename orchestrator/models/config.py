import os

ROOT_MODEL = os.environ.get(
    "BARTM0SS_ROOT_MODEL", "hf.co/tiiuae/Falcon-H1R-7B-GGUF:Q4_K_M"
)
SUBAGENT_MODEL = os.environ.get(
    "BARTM0SS_SUBAGENT_MODEL", "hf.co/bartowski/ai21labs_AI21-Jamba2-3B-GGUF:Q8_0"
)

ROOT_CONTEXT_LIMIT = int(os.environ.get("BARTM0SS_ROOT_CONTEXT_LIMIT", "8192"))
SUBAGENT_CONTEXT_LIMIT = int(os.environ.get("BARTM0SS_SUBAGENT_CONTEXT_LIMIT", "4096"))

MAX_OUTPUT_TOKENS = int(os.environ.get("BARTM0SS_MAX_OUTPUT_TOKENS", "1024"))

DEFAULT_TEMPERATURE = 0.7