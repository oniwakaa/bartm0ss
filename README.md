# bartm0ss

A local-first, offline-capable agentic coding CLI using the RLM (Recursive Language Model) paradigm.

## Overview

bartm0ss amplifies small hybrid SSM+Transformer models (3B–7B parameters) to approach the effective coding performance of larger models—running entirely on a 16GB Apple Silicon Mac.

## Architecture

- **CLI Frontend**: TypeScript/Node.js with React + Ink v5
- **Backend Orchestrator**: Python 3.11+ 
- **Models**: Falcon H1R 7B (root) + Jamba Reasoning 3B (sub-agent) via Ollama
- **IPC**: JSON-RPC 2.0 over stdin/stdout

## Requirements

- macOS on Apple Silicon
- 16GB RAM (minimum)
- Homebrew

## Installation

```bash
./scripts/install.sh
```

## Usage

```bash
# Run a non-interactive task
bartm0ss task "add a retry helper to utils.py"

# Interactive chat mode
bartm0ss chat

# Review a file
bartm0ss review src/main.py

# Refactor a file
bartm0ss refactor src/main.py
```

## Development

```bash
# Start development environment
./scripts/dev.sh

# Run Python tests
cd orchestrator && pytest -v

# Run CLI in dev mode
cd cli && bun run dev
```

## Project Structure

```
bartm0ss/
├── cli/                 # TypeScript CLI frontend
│   ├── src/
│   │   ├── components/  # Ink components (TaskView, StatusBar, etc.)
│   │   ├── ipc/         # JSON-RPC client
│   │   └── index.ts     # Entry point
│   └── package.json
│
├── orchestrator/        # Python backend
│   ├── main.py          # JSON-RPC server
│   ├── rlm/             # RLM control loop
│   ├── tools/           # CLI tools (codesearch, codepeek, etc.)
│   ├── grounding/       # Safety sandbox
│   ├── models/          # Ollama client
│   └── tests/           # pytest tests
│
└── prompts/             # LM prompt templates
```

## License

MIT