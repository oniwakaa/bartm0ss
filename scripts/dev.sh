#!/bin/bash
set -e

echo "Starting bartm0ss development environment..."

ORCHESTRATOR_PID=""
CLI_PID=""

cleanup() {
    echo "Stopping..."
    [ -n "$ORCHESTRATOR_PID" ] && kill $ORCHESTRATOR_PID 2>/dev/null
    [ -n "$CLI_PID" ] && kill $CLI_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

echo "Starting Python orchestrator..."
cd "$(dirname "$0")/../orchestrator"
python main.py &
ORCHESTRATOR_PID=$!

sleep 1

echo "Starting Node.js CLI..."
cd ../cli
bun run dev &
CLI_PID=$!

wait $CLI_PID