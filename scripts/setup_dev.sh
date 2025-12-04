#!/bin/bash
set -e

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing development dependencies..."
pip install --upgrade pip
pip install flake8 pytest mypy types-PyYAML types-jsonschema

echo "Installing project dependencies..."
if [ -f pyproject.toml ]; then
    pip install -e .
fi

echo "Setup complete."
