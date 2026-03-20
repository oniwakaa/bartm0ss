
# PLAN.md — bartm0ss
> Authoritative project context file for the coding AI agent.
> Read this at the start of every session. Do not re-read raw chat history.
> All architectural decisions are recorded here.
> Sections marked [DECISION NEEDED] require human input before proceeding.

---

## 1. Project Overview

**bartm0ss** is a local-first, offline-capable agentic coding CLI that uses
the Recursive Language Models (RLM) paradigm (Zhang & Khattab, 2025,
arxiv:2512.24601) to amplify small hybrid SSM+Transformer models (3B–7B
parameters) to approach the effective coding performance of 13B–30B parameter
models — within a purpose-built scaffolding environment.

The system uses a **dual-model architecture**:
- **Root LM:** Falcon H1R 7B (Q4_K_M GGUF) — planning, code reasoning,
  patch generation, sub-goal decomposition.
- **Sub-agent LM:** Jamba Reasoning 3B (Q4_K_M GGUF) — cheap, fast
  extraction tasks: summarize file, peek span, grep pattern, extract symbols.

Models run **sequentially** (never simultaneously) via Ollama on a
16 GB Apple Silicon Mac. All inference is local; no cloud API is used
in the core runtime.

**Target users:** Solo engineers and small teams (1–3 people) on macOS
Apple Silicon requiring a capable local coding agent with zero cloud
dependency.

**Primary use cases:**
1. Implement a function or feature across one or more files.
2. Fix a failing test using LSP diagnostics and test runner output.
3. Refactor a file or module using diff-based, LSP-validated edits.
4. Long-context agentic tasks: search a monorepo, aggregate symbols,
   migrate an API usage pattern.

---

## 2. Tech Stack & Environment

### Languages & Runtimes
| Layer | Language | Runtime |
|-------|----------|---------|
| CLI Frontend | TypeScript | Node.js 20+ |
| Backend Orchestrator | Python | 3.11+ |
| Shell tools | zsh/bash | macOS (Apple Silicon) |

### CLI Frontend (Node.js)
- **UI framework:** React + Ink v5 — same stack used by Claude Code and OpenCode
- **Build tool:** Bun
- **Package manager:** npm (distribution) / bun (dev workflow)
- **Language:** TypeScript, strict mode

### IPC Between Frontend and Backend
- **Protocol:** JSON-RPC 2.0 over stdin/stdout
- The Node.js CLI spawns the Python orchestrator as a child process
- The orchestrator streams structured events back: THOUGHT, COMMAND,
  ANSWER, TOOL_RESULT
- Mirrors the cross-process bridge pattern used in OpenCode

### Backend (Python)
- **LLM inference:** Ollama Python SDK — primary; `llama-cpp-python` as fallback
- **Models:**
  - Root LM: Falcon H1R 7B @ Q4_K_M GGUF
    (source: `unsloth/Falcon-H1R-7B-GGUF` or `tiiuae/Falcon-H1R-7B-GGUF`)
  - Sub-agent: AI21 Jamba Reasoning 3B @ Q4_K_M GGUF
    (source: `bartowski/ai21labs_AI21-Jamba-Reasoning-3B-GGUF`)
- **AST / code analysis:** `tree-sitter` Python bindings
- **Code search:** `ripgrep` (`rg`) via subprocess
- **LSP integration:** `pygls` or direct LSP subprocess
  - [DECISION NEEDED: which LSP servers to require in Phase 1,
    e.g., `pyright` for Python, `typescript-language-server` for TS]
- **Diff/patch:** `gitpython` + `difflib`
- **Formatting:** `black` / `ruff` for Python targets
  - [DECISION NEEDED: formatter for non-Python files, e.g., `prettier`]
- **Testing:** `pytest`

### Required External CLI Tools (pre-installed via Homebrew)
- `rg` — ripgrep, fast code search: `brew install ripgrep`
- `tree-sitter` CLI: `brew install tree-sitter`
- `ollama`: `brew install ollama`
- Language LSP servers: [DECISION NEEDED — scope for Phase 1]

### RAM Budget (16 GB unified memory)
| Component | Estimated RAM |
|-----------|--------------|
| Falcon H1R 7B @ Q4_K_M | ~4.5–5 GB |
| Jamba 3B @ Q4_K_M | ~2–2.5 GB |
| OS + REPL + Node CLI overhead | ~3–4 GB |
| **Total peak (sequential)** | **~8–9 GB ✅** |

Models are never loaded simultaneously. Ollama handles load/unload
between root LM and sub-agent calls.

---

## 3. Architecture Overview

### Component Diagram

```
┌──────────────────────────────────────────────────────────┐
│             bartm0ss CLI (Node.js / TypeScript)           │
│            React + Ink v5 — Terminal UI (TUI)            │
│                                                          │
│  Modes: chat | task "<goal>" | review | refactor         │
│  Streams THOUGHT / COMMAND / ANSWER lines to terminal    │
│  User can approve or block commands (interactive mode)   │
└──────────────────────┬───────────────────────────────────┘
                       │ JSON-RPC 2.0 over stdin/stdout
                       ▼
┌──────────────────────────────────────────────────────────┐
│           RLM Orchestrator (Python 3.11+)                │
│                                                          │
│  - Manages RLM control loop (depth-1 recursion)          │
│  - Holds Context object: repo index, snippets, tasks     │
│  - Parses LM output: THOUGHT / COMMAND / ANSWER          │
│  - Spawns sub-agent calls via SubAgentSpawner            │
│  - Enforces safety sandbox on every COMMAND              │
└──────┬───────────────────────┬───────────────────────────┘
       │ Ollama API calls       │ CLI tool subprocess calls
       ▼                       ▼
┌─────────────────┐   ┌────────────────────────────────────┐
│  Ollama Runtime │   │        CLI Tool Layer              │
│                 │   │                                    │
│ - Falcon H1R 7B │   │  codesearch  → rg subprocess       │
│   (Root LM)     │   │  codepeek    → file read + slice   │
│                 │   │  codeoutline → tree-sitter AST     │
│ - Jamba 3B      │   │  codestats   → wc / git log        │
│   (Sub-agent)   │   │  apply-diff  → patch + git         │
│                 │   │  lsp-check   → LSP subprocess      │
│  Sequential;    │   │  run-tests   → pytest / npm test   │
│  never parallel │   │  docsearch   → local doc index     │
└─────────────────┘   └────────────────────────────────────┘
                                   │
                       ┌───────────▼───────────┐
                       │   Grounding & Safety   │
                       │                        │
                       │ - Command allowlist     │
                       │ - No rm -rf, no net    │
                       │ - Path whitelist        │
                       │ - Dry-run / approval   │
                       │ - Diff → LSP → tests   │
                       │ - Full command log      │
                       └────────────────────────┘
```

### Data Flow Narrative

1. **CLI → Orchestrator:** The Ink TUI sends a task string or chat
   message to the Python orchestrator via JSON-RPC 2.0 over stdin/stdout.
   The orchestrator streams structured events back (THOUGHT, COMMAND,
   ANSWER, TOOL_RESULT), which the TUI renders in real time.

2. **Orchestrator → LM:** The RLM loop sends short, context-bounded
   prompts to the Root LM (Falcon H1R 7B) via Ollama. The model outputs
   THOUGHT / COMMAND / ANSWER blocks. Commands are parsed and dispatched
   to the CLI Tool Layer. Results are stored in the Context object by ID —
   never re-injected as raw text into the next prompt.

3. **Sub-agent calls:** On a `subagent` command, the Orchestrator loads
   Jamba 3B via Ollama, runs a narrow extraction prompt, stores the result
   by task ID in the Context, then returns control to the Root LM.

---

## 4. Project Structure

```
bartm0ss/
├── cli/                        # Node.js / TypeScript CLI frontend
│   ├── src/
│   │   ├── app.tsx             # Root Ink app component
│   │   ├── components/
│   │   │   ├── TaskView.tsx    # Streams THOUGHT/COMMAND/ANSWER
│   │   │   ├── CommandPrompt.tsx  # User input + approval/block UI
│   │   │   ├── DiffView.tsx    # Renders unified diffs
│   │   │   └── StatusBar.tsx   # Current model, mode, task state
│   │   ├── ipc/
│   │   │   ├── rpc-client.ts   # JSON-RPC 2.0 client over stdin/stdout
│   │   │   └── types.ts        # Shared RPC message type definitions
│   │   └── index.ts            # CLI entrypoint (bin: bartm0ss)
│   ├── package.json
│   ├── tsconfig.json
│   └── bunfig.toml
│
├── orchestrator/               # Python RLM backend
│   ├── main.py                 # JSON-RPC 2.0 server entrypoint
│   ├── rlm/
│   │   ├── loop.py             # RLM control loop (depth-1)
│   │   ├── context.py          # Context: repo index, snippets, tasks
│   │   ├── parser.py           # THOUGHT/COMMAND/ANSWER output parser
│   │   └── subagent.py         # Sub-agent spawner (Jamba 3B calls)
│   ├── tools/
│   │   ├── codesearch.py       # rg subprocess wrapper
│   │   ├── codepeek.py         # File read + line-range slice
│   │   ├── codeoutline.py      # tree-sitter AST symbol extraction
│   │   ├── codestats.py        # File/repo stats
│   │   ├── apply_diff.py       # Unified diff application
│   │   ├── lsp_check.py        # LSP subprocess diagnostics
│   │   ├── run_tests.py        # pytest / npm test runner
│   │   └── docsearch.py        # Local doc index search
│   ├── grounding/
│   │   ├── sandbox.py          # Command allowlist + path whitelist
│   │   ├── safety.py           # Dry-run mode, command log
│   │   └── validator.py        # Post-diff LSP + test validation
│   ├── models/
│   │   ├── ollama_client.py    # Ollama Python SDK wrapper
│   │   └── config.py           # Model names, quant levels, context limits
│   └── tests/
│       ├── test_rlm_loop.py
│       ├── test_tools.py
│       ├── test_parser.py
│       ├── test_subagent.py
│       └── test_grounding.py
│
├── prompts/                    # LM prompt templates (plain text / Jinja2)
│   ├── root_lm_system.txt      # Root LM system prompt
│   ├── subagent_summarize.txt  # Sub-agent: summarize file
│   ├── subagent_extract.txt    # Sub-agent: extract symbols/contracts
│   └── subagent_peek.txt       # Sub-agent: answer question about a span
│
├── scripts/
│   ├── install.sh              # Installs brew deps + pulls Ollama models
│   └── dev.sh                  # Starts orchestrator + CLI in dev mode
│
├── PLAN.md                     # This file
└── README.md
```

---

## 5. Backend Development Plan

> Implement modules strictly in the order listed.
> Do not start a module until all modules it depends on pass
> their acceptance criteria.

---

### Module 1 — `models/config.py` & `models/ollama_client.py`
**Responsibility:** Wrap Ollama inference; provide a single unified
interface for both Root LM and sub-agent LM calls.

**Inputs:**
- Model identifier (root or sub-agent), list of role/content message
  dicts, max tokens, temperature, stream flag.

**Outputs:**
- A streaming generator of token chunks on success.
- A typed `OllamaUnavailableError` on connection failure or
  model-not-found.

**Acceptance criteria:**
1. Successfully streams tokens from Falcon H1R 7B via local Ollama.
2. Successfully streams tokens from Jamba 3B via local Ollama.
3. Raises `OllamaUnavailableError` with a descriptive message if Ollama
   is not running or the model has not been pulled.
4. Unit tests mock the Ollama SDK and cover: success stream, connection
   error, model-not-found error.
5. All model identifiers and context limits are overridable via
   environment variables (`BARTM0SS_ROOT_MODEL`,
   `BARTM0SS_SUBAGENT_MODEL`).

**Task order:**
1. `config.py` — constants and env var overrides
2. `ollama_client.py` — thin SDK wrapper
3. Custom error classes
4. Unit tests

---

### Module 2 — `rlm/context.py`
**Responsibility:** Maintain the persistent RLM context object across
the loop: repo index references, snippet cache, active sub-tasks, and
their results. The Context object is the single source of truth passed
through every RLM iteration.

**Inputs:**
- Repo root path, file metadata, snippet text, sub-task queries and
  results.

**Outputs:**
- Snippet IDs and task IDs (stable string references).
- A short summary prompt string that the Root LM receives as its
  context header — always within a fixed token budget, using IDs
  instead of raw text.

**Acceptance criteria:**
1. The summary prompt produced by the Context object never exceeds
   512 tokens, enforced by hard truncation and ID references.
2. Snippet IDs remain stable for the full session with no re-keying.
3. Sub-task lifecycle is tracked: pending → resolved.
4. Unit tests cover: add/get snippet, task lifecycle, summary prompt
   token budget enforcement.

**Task order:**
1. `FileMetadata` and `SubTask` data classes
2. `Context` class with CRUD methods
3. Summary prompt builder with token budget enforcement
4. Unit tests

---

### Module 3 — CLI Tool Layer (`tools/`)
**Responsibility:** Each tool is a standalone Python module with a
single `run(args) -> ToolResult` entry point. Tools are dispatched by
the RLM loop after parsing a `COMMAND:` line. All tools return
plain-text output; no JSON schemas are exposed to the LM.

**Shared `ToolResult` contract:**
- `output` — plain text, hard-truncated to 2000 characters
- `success` — boolean
- `error` — string or None; always set on failure, never raises
  unhandled exceptions

**Tool specifications:**

| Tool | CLI invocation style | Underlying mechanism |
|------|---------------------|----------------------|
| `codesearch` | `codesearch "pattern" [path]` | `rg` subprocess |
| `codepeek` | `codepeek filepath start_line [n_lines]` | File read + slice |
| `codeoutline` | `codeoutline filepath` | tree-sitter AST |
| `codestats` | `codestats filepath` | `wc` + `git log` |
| `apply-diff` | `apply-diff filepath` with diff on stdin | `difflib` + `gitpython` |
| `lsp-check` | `lsp-check filepath` | LSP subprocess |
| `run-tests` | `run-tests [target]` | `pytest` or `npm test` |
| `docsearch` | `docsearch "query"` | Local doc index |

**Acceptance criteria (all tools):**
1. Output is always ≤ 2000 characters; excess is truncated with a
   clear truncation marker.
2. Never raises an unhandled exception; always returns a `ToolResult`
   with `success=False` and a descriptive `error` string on failure.
3. `codesearch` and `codepeek` tested against a fixture repo directory.
4. `apply-diff` tested: valid patch applied correctly; invalid patch
   returns error without modifying the file.
5. `lsp_check` and `run_tests` tested with subprocess mocks.

**Task order:**
1. `codesearch.py`
2. `codepeek.py`
3. `codeoutline.py`
4. `codestats.py`
5. `apply_diff.py`
6. `lsp_check.py`
7. `run_tests.py`
8. `docsearch.py` — implement last; blocked on doc index decision

---

### Module 4 — `grounding/` (Sandbox, Safety, Validator)
**Responsibility:** Wrap every command execution in safety enforcement,
path whitelisting, dry-run/approval flow, command logging, and
post-edit validation.

**Components:**

- **`sandbox.py`**
  - Maintains an explicit allowlist of permitted commands:
    `codesearch`, `codepeek`, `codeoutline`, `codestats`,
    `apply-diff`, `lsp-check`, `run-tests`, `docsearch`, `subagent`
  - Validates that all file paths target are within the repo root
  - Rejects any command not in the allowlist with a typed error
  - No network access permitted from any tool

- **`safety.py`**
  - Logs every command and its result to `.bartm0ss/command_log.jsonl`
  - In interactive mode: prompts user approval for all `apply-diff`
    commands before execution
  - In non-interactive mode: executes all allowlisted commands
    automatically

- **`validator.py`**
  - Runs `lsp-check` and `run-tests` automatically after every
    successful `apply-diff`
  - Returns a structured `ValidationResult`: LSP errors, test summary,
    overall pass/fail
  - The RLM loop feeds the validation summary back into the next
    Root LM prompt as a TOOL_RESULT

**Acceptance criteria:**
1. Any command not in the allowlist is rejected; error propagates to
   the RLM loop and is shown in the TUI.
2. Any path outside `repo_root` is rejected; no writes occur.
3. Command log file is created on first run and appended atomically.
4. In interactive mode, `apply-diff` always blocks until user approves
   or rejects.
5. `validator.py` is invoked automatically post-diff; its output is
   always surfaced to the next LM prompt.
6. Unit tests cover: allowlist rejection, path traversal rejection,
   log file creation, interactive approval flow (mocked stdin).

**Task order:**
1. `sandbox.py` — allowlist + path validation
2. `safety.py` — logging + interactive approval
3. `validator.py` — post-edit LSP + test validation
4. Unit tests

---

### Module 5 — `rlm/parser.py`
**Responsibility:** Parse raw LM output into structured
THOUGHT / COMMAND / ANSWER blocks. This is the sole entry point for
interpreting model output; no other module parses LM text directly.

**Inputs:** Raw string token stream from the Root LM.

**Outputs:**
- A parsed `LMOutput` object containing optional `thought`, `command`,
  and `answer` fields.
- On parse failure: returns a `LMOutput` with `parse_error` set and
  all fields empty; never raises.

**Accepted output format from LM:**
```
THOUGHT: <free-form reasoning>
COMMAND: <single CLI command line> | NONE
ANSWER: <optional natural language response to user>
```

**Acceptance criteria:**
1. Correctly parses all three sections when all are present.
2. Correctly parses partial outputs (e.g., only THOUGHT + COMMAND,
   no ANSWER).
3. On malformed output, sets `parse_error` and logs a warning; does
   not crash the loop.
4. COMMAND value is always a single line; multi-line commands are
   rejected as malformed.
5. Unit tests cover: full parse, partial parse, malformed input,
   empty input, COMMAND: NONE.

**Task order:**
1. `LMOutput` data class
2. Parser logic
3. Malformed input handling
4. Unit tests

---

### Module 6 — `rlm/subagent.py`
**Responsibility:** Handle sub-agent spawning. On a `subagent` command,
load Jamba 3B via Ollama, run a narrow extraction prompt against a
specified snippet or file view, store the result in Context, and return
the task ID to the RLM loop.

**Inputs:**
- Query string, snippet/view ID from Context, sub-agent prompt template
  name (summarize / extract / peek).

**Outputs:**
- Task ID string pointing to the resolved result in Context.
- On failure: task is marked failed with an error string; never raises.

**Acceptance criteria:**
1. Uses Jamba 3B exclusively (never the Root LM) for sub-agent calls.
2. Prompt sent to Jamba 3B is always ≤ `SUBAGENT_CONTEXT_LIMIT` tokens.
3. Result is stored in Context and retrievable by task ID.
4. On Ollama failure, task is marked failed; RLM loop continues.
5. Unit tests mock `ollama_client` and cover: successful sub-call,
   prompt truncation, Ollama failure, result storage.

**Task order:**
1. Prompt template loader (reads from `prompts/`)
2. Sub-agent call logic using `ollama_client`
3. Context result storage
4. Failure handling
5. Unit tests

---

### Module 7 — `rlm/loop.py`
**Responsibility:** The core RLM control loop. Manages the iterative
cycle: build prompt → call Root LM → parse output → dispatch command →
store result → repeat. Enforces iteration limits and produces a final
ANSWER when the model emits one or the limit is reached.

**Inputs:**
- Task string from the CLI, initialized Context object, max iteration
  limit (default: 20).

**Outputs:**
- A stream of `LoopEvent` objects (THOUGHT, COMMAND, TOOL_RESULT,
  ANSWER, ERROR) sent to `main.py` for JSON-RPC forwarding to the CLI.

**Loop invariants:**
- The Root LM never receives raw file content or raw snippet text
  directly in the prompt — only IDs and the Context summary.
- Every COMMAND passes through `sandbox.py` before execution.
- Every `apply-diff` COMMAND triggers `validator.py` post-execution.
- Sub-agent results are stored in Context and referenced by ID in the
  next Root LM prompt.
- Maximum recursion depth is 1 (sub-agents do not spawn further
  sub-agents in Phase 1).

**Acceptance criteria:**
1. Loop terminates when the Root LM emits `ANSWER:` or when the
   iteration limit is reached (whichever comes first).
2. On iteration limit: emits a `LOOP_LIMIT` event and a partial answer.
3. All commands pass through `sandbox.py`; rejected commands emit an
   error event and the loop continues.
4. `apply-diff` always triggers `validator.py`; result is included in
   the next prompt.
5. Integration tests cover: single-step task (no tools), multi-step
   task (codesearch → codepeek → apply-diff), sub-agent call, command
   rejection, iteration limit.

**Task order:**
1. `LoopEvent` data class and event types
2. Prompt builder (uses Context summary + last TOOL_RESULT)
3. Main loop logic
4. Sub-agent dispatch integration
5. Iteration limit enforcement
6. Integration tests

---

### Module 8 — `main.py`
**Responsibility:** JSON-RPC 2.0 server. Reads requests from stdin,
routes them to the RLM loop or configuration handlers, streams
`LoopEvent` objects back to stdout as JSON-RPC notifications.

**Methods exposed:**
- `task.run` — starts a new RLM loop for a given task string
- `task.cancel` — cancels the active loop
- `config.get` — returns current model config
- `config.set` — overrides model config at runtime

**Acceptance criteria:**
1. Correctly parses JSON-RPC 2.0 requests from stdin.
2. Streams loop events as JSON-RPC notifications to stdout in real time.
3. Handles malformed JSON input gracefully (returns JSON-RPC error
   response; does not crash).
4. `task.cancel` cleanly terminates an in-flight Ollama stream.
5. Integration test: send a `task.run` request, assert ordered sequence
   of THOUGHT → COMMAND → TOOL_RESULT → ANSWER events on stdout.

**Task order:**
1. JSON-RPC 2.0 message parsing and routing
2. `task.run` handler with loop event streaming
3. `task.cancel` handler
4. `config.get` / `config.set` handlers
5. Integration test

---

## 6. Backend Acceptance Gate

The agent must not begin any frontend work until **all** of the
following checks pass:

1. `pytest orchestrator/tests/ -v` — all unit and integration tests
   pass with zero failures and zero errors.
2. Manual smoke test: run `main.py` directly, send a `task.run`
   JSON-RPC request via stdin with a simple task ("list all Python
   files in this repo"), verify a valid ANSWER event is received on
   stdout.
3. `codesearch`, `codepeek`, and `apply-diff` tools verified against a
   real fixture repo: a search returns results, a peek returns the
   correct lines, a diff is applied and then validated by `lsp-check`.
4. Sub-agent smoke test: trigger a `subagent` command from the RLM loop
   with a summarization task, verify the result is stored in Context
   and referenced in the next Root LM prompt.
5. Safety check: attempt a command not in the allowlist and a path
   outside repo root — both must be rejected without crashing the loop.

---

## 7. Frontend (CLI) Development Plan

> Begin only after the Backend Acceptance Gate is fully passed.

### CLI Framework
- **Runtime:** Node.js 20+
- **UI library:** React + Ink v5
- **Build tool:** Bun
- **Language:** TypeScript (strict mode)
- **Entry point:** `cli/src/index.ts`, exposed as binary `bartm0ss`

### Supported Modes & Commands
| Mode | Invocation | Description |
|------|-----------|-------------|
| `task` | `bartm0ss task "<goal>"` | Runs a non-interactive agentic task |
| `chat` | `bartm0ss chat` | Interactive back-and-forth with the RLM loop |
| `review` | `bartm0ss review [file]` | Reviews a file and suggests improvements |
| `refactor` | `bartm0ss refactor [file]` | Refactors a file using diff-based edits |

### IPC Connection
- On startup, the CLI spawns `python orchestrator/main.py` as a child
  process.
- Communicates via JSON-RPC 2.0 over stdin/stdout of that child process.
- The `rpc-client.ts` module handles message serialization, streaming
  event parsing, and error recovery.
- If the orchestrator process exits unexpectedly, the CLI displays an
  error and exits cleanly.

### Components

**`TaskView.tsx`**
- Renders a live-streaming view of THOUGHT / COMMAND / TOOL_RESULT /
  ANSWER events from the orchestrator.
- THOUGHT lines are shown in a muted color (grey).
- COMMAND lines are shown in a highlighted color with the command text.
- TOOL_RESULT lines are shown in a code block style.
- ANSWER text is rendered in full, primary color.

**`CommandPrompt.tsx`**
- In interactive mode: when an `apply-diff` COMMAND event arrives,
  pauses rendering and shows a prompt asking the user to approve
  (press Y) or reject (press N).
- Sends the approval decision back to the orchestrator via
  JSON-RPC (`task.approve` / `task.reject`).

**`DiffView.tsx`**
- Renders unified diffs inline using color coding:
  added lines in green, removed lines in red, context lines in white.
- Shown before the approval prompt for `apply-diff` commands.

**`StatusBar.tsx`**
- Persistent bottom bar showing: active model name, current mode,
  task iteration count, and overall status (running / waiting /
  done / error).

### Key UX Flows

**Flow 1 — Non-interactive task:**
1. User runs `bartm0ss task "add a retry helper to utils.py"`
2. CLI spawns orchestrator and sends `task.run` RPC request.
3. TUI renders THOUGHT / COMMAND / TOOL_RESULT events as they stream.
4. On ANSWER event: final answer is displayed; process exits cleanly.

**Flow 2 — Interactive apply-diff:**
1. RLM loop emits an `apply-diff` COMMAND event.
2. `DiffView` renders the unified diff.
3. `CommandPrompt` shows: "Apply this diff? [Y/n]"
4. If Y: orchestrator applies the diff, runs validator, streams result.
5. If N: orchestrator skips the diff, emits a TOOL_RESULT with
   "User rejected diff", loop continues.

**Flow 3 — Chat mode:**
1. User runs `bartm0ss chat`.
2. TUI shows an input prompt.
3. User types a message; CLI sends `task.run` with the message.
4. Events stream as in Flow 1.
5. On ANSWER, the input prompt returns for the next message.
6. User exits with Ctrl+C or typing `exit`.

### Acceptance criteria (CLI)
1. `bartm0ss task "<goal>"` runs end-to-end and displays a final ANSWER.
2. Diff approval prompt correctly blocks execution and resumes on Y/N.
3. Status bar updates in real time throughout a task.
4. If the orchestrator process is not available, a clear error is shown
   and the CLI exits with a non-zero code.
5. Ctrl+C in any mode cleanly cancels the active task (sends
   `task.cancel` RPC) and exits.
6. All three TUI components render correctly in a standard macOS terminal.

---

## 8. Testing Strategy

### Unit Tests (Backend — `pytest`)
- `test_tools.py` — each tool against fixture files; covers success,
  truncation, and error paths.
- `test_parser.py` — covers all parse variants and malformed inputs.
- `test_rlm_loop.py` — loop with mocked Ollama client; covers
  single-step, multi-step, sub-agent, rejection, and iteration limit.
- `test_subagent.py` — sub-agent spawner with mocked Ollama; covers
  success, truncation, and failure paths.
- `test_grounding.py` — sandbox, safety, and validator with mocked
  tools and subprocess.

### Integration Tests (Backend)
- Full `main.py` server: send JSON-RPC `task.run` over stdin, assert
  correct event sequence on stdout.
- `apply-diff` → `lsp-check` → `run-tests` pipeline on a real fixture
  repo with a known-good and a known-bad patch.

### End-to-End Test (CLI → Backend)
- Spawn `bartm0ss task "count all TODO comments in the fixture repo"`,
  run against a prepared fixture repo with a known TODO count, assert
  the ANSWER contains the correct number.
- Run in non-interactive mode (no approval prompts) using an environment
  flag: `BARTM0SS_NON_INTERACTIVE=1`.

---

## 9. Open Decisions & Risks

### Unresolved Decisions
| Decision | Options | Impact |
|----------|---------|--------|
| LSP servers for Phase 1 | `pyright` only vs `pyright` + `typescript-language-server` | Scope of supported languages in Phase 1 |
| Non-Python file formatter | `prettier` vs none in Phase 1 | Code quality of TS/JS edits |
| Doc index format for `docsearch` | SQLite FTS vs plain grep vs embeddings | Quality of documentation lookups |
| Ollama vs llama.cpp as primary | Ollama SDK (easier lifecycle mgmt) vs `llama-cpp-python` (more control) | RAM management and model switching reliability |

### Known Risks & Mitigations
| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Falcon H1R 7B fails to reliably emit THOUGHT/COMMAND/ANSWER format | Medium | Iterate on `root_lm_system.txt` prompt; add a retry with a stricter re-prompt on parse failure |
| Jamba 3B sub-agent calls increase latency beyond acceptable UX | Medium | Cap sub-agent calls per loop iteration (max 3); show a spinner in the TUI during sub-agent calls |
| `apply-diff` produces patches that break LSP/tests consistently | High | Implement automatic re-prompt with diagnostics as a recovery step; cap retries at 2 |
| Ollama model switching overhead is too slow on 16 GB Mac | Medium | Benchmark early in Week 1–2; if too slow, keep both models loaded and use `llama-cpp-python` with manual memory management |
| OLMo Hybrid 7B becomes available in GGUF before Phase 1 ends | Low | Architecture is model-swappable via config; evaluate as a drop-in root LM replacement if GGUF appears |

---

## 10. Agent Instructions

### Working Conventions
- **Branch naming:** `feat/<module-name>`, `fix/<issue-description>`,
  `test/<module-name>`
- **Commit style:** Conventional Commits — e.g.,
  `feat(tools): add codepeek module`,
  `fix(parser): handle empty COMMAND line`,
  `test(rlm): add iteration limit integration test`
- **File naming:** Python — snake_case; TypeScript — PascalCase for
  components, camelCase for utilities.
- **No code without tests:** Every new module must have corresponding
  tests before being marked complete.
- **No inline comments explaining intent** — code should be
  self-documenting; only add comments for non-obvious algorithm steps.
- **Environment variables** for all model names, context limits, and
  runtime paths — no hardcoded values outside `config.py`.

### Handling Blockers & Ambiguity
- If a `[DECISION NEEDED]` section blocks implementation, add a
  `TODO: DECISION NEEDED — <description>` comment at the exact
  call site, implement a sensible default, and log a warning at
  runtime when the default is used.
- If Ollama behaves unexpectedly in local testing, fall back to
  `llama-cpp-python` and note the discrepancy in a `NOTES.md` file
  at the repo root.
- Do not invent architectural decisions not present in this document.
  If truly stuck, pause and surface the question with full context.

### Iteration Checkpoints
Pause and report back to the human at the following points:

1. **After Module 1** — confirm both models load and stream correctly
   via Ollama on the target Mac before building anything else.
2. **After Module 3** — confirm all tools return correct output on
   the fixture repo before proceeding to the RLM loop.
3. **After the Backend Acceptance Gate** — run the full gate checklist,
   report results, and get explicit sign-off before starting the CLI.
4. **After CLI Flow 1 passes end-to-end** — demo the working
   `bartm0ss task` command and get feedback before polishing
   remaining flows.
```