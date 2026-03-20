# bartm0ss - Local-first agentic coding CLI
# Install dependencies for both backend and frontend

# Python backend
cd orchestrator && pip install -r requirements.txt

# Node.js CLI
cd ../cli && npm install

echo ""
echo "Dependencies installed."
echo "To pull Ollama models: ollama pull falcon-h1r-7b"