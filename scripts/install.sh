#!/bin/bash
set -e

echo "Installing bartm0ss dependencies..."

if ! command -v brew &> /dev/null; then
    echo "Error: Homebrew not installed. Visit https://brew.sh"
    exit 1
fi

echo "Installing CLI tools..."
brew install ripgrep tree-sitter ollama || true

echo "Pulling Ollama models (this may take a while)..."
ollama pull falcon-h1r-7b-q4_k_m 2>/dev/null || echo "Note: Model may need manual pull: ollama pull falcon-h1r-7b"
ollama pull ai21-jamba-reasoning-3b-q4_k_m 2>/dev/null || echo "Note: Model may need manual pull"

echo "Installing Python dependencies..."
pip install ollama tree-sitter-python pytest || pip3 install ollama tree-sitter-python pytest

echo "Installing Node.js CLI dependencies..."
cd cli && bun install || npm install

echo ""
echo "Setup complete! Run 'bartm0ss task \"your goal\"' to start."