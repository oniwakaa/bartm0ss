import os

ROOT_MODEL = os.environ.get(
    "BARTM0SS_ROOT_MODEL", "falcon-h1r-7b-q4_k_m"
)
SUBAGENT_MODEL = os.environ.get(
    "BARTM0SS_SUBAGENT_MODEL", "ai21-jamba-reasoning-3b-q4_k_m"
)

ROOT_CONTEXT_LIMIT = int(os.environ.get("BARTM0SS_ROOT_CONTEXT_LIMIT", "8192"))
SUBAGENT_CONTEXT_LIMIT = int(os.environ.get("BARTM0SS_SUBAGENT_CONTEXT_LIMIT", "4096"))

MAX_OUTPUT_TOKENS = int(os.environ.get("BARTM0SS_MAX_OUTPUT_TOKENS", "1024"))

DEFAULT_TEMPERATURE = 0.7