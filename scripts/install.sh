#!/bin/bash
set -e

echo "=========================================="
echo "bartm0ss Development Environment Setup"
echo "=========================================="

if ! command -v brew &> /dev/null; then
    echo "Error: Homebrew not installed. Visit https://brew.sh"
    exit 1
fi

echo ""
echo "[1/6] Installing CLI tools..."
brew install ripgrep tree-sitter ollama || echo "Note: Some tools may already be installed"

echo ""
echo "[2/6] Installing LSP servers and formatters..."
npm install -g pyright typescript-language-server prettier 2>/dev/null || echo "Note: LSP servers may already be installed"

echo ""
echo "[3/6] Installing Python dependencies..."
pip install --user ollama tree-sitter-python pytest pytest-cov black ruff mypy 2>/dev/null || pip3 install --user ollama tree-sitter-python pytest pytest-cov black ruff mypy 2>/dev/null || echo "Note: Python packages may need sudo"

echo ""
echo "[4/6] Pulling Ollama models..."
echo "Note: This may take a while for large models."
ollama pull falcon-h1r-7b 2>/dev/null || echo "Note: Model 'falcon-h1r-7b' may need manual pull: ollama pull falcon-h1r-7b"
ollama pull ai21-jamba-reasoning-3b 2>/dev/null || echo "Note: Model 'ai21-jamba-reasoning-3b' may need manual pull"

echo ""
echo "[5/6] Installing Node.js CLI dependencies..."
cd cli
if command -v bun &> /dev/null; then
    bun install 2>/dev/null || npm install
elif command -v npm &> /dev/null; then
    npm install
else
    echo "Warning: Neither bun nor npm found. Please install Node.js."
fi
cd ..

echo ""
echo "[6/6] Creating .bartm0ss directory..."
mkdir -p .bartm0ss

echo ""
echo "=========================================="
echo "Setup complete!"
echo ""
echo "Quick start:"
echo "  cd orchestrator && pytest -v        # Run Python tests"
echo "  cd cli && bun run dev               # Start CLI in dev mode"
echo "  ./scripts/dev.sh                    # Start full dev environment"
echo ""
echo "Model availability:"
echo "  ollama list                         # Check installed models"
echo "  ollama pull falcon-h1r-7b           # Pull root LM if missing"
echo "  ollama pull ai21-jamba-reasoning-3b # Pull sub-agent LM if missing"
echo "=========================================="