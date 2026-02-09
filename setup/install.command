#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Navigate to the project root (one level up)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Setting up QPE Simulator in: $PROJECT_ROOT"

# Create venv if it doesn't exist
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$PROJECT_ROOT/venv"
fi

echo "Activating virtual environment..."
source "$PROJECT_ROOT/venv/bin/activate"

echo "Installing dependencies..."
pip install -r "$PROJECT_ROOT/requirements.txt"

echo "Setup complete. You can close this window."
