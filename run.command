#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found."
    echo "Please go to the 'setup' folder and run 'install.command' first."
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Starting QPE Simulation..."
python main.py || python3 main.py

echo "Application closed."