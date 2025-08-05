#!/bin/bash

# Activation script for financeAgent virtual environment
echo "🐍 Activating financeAgent virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated!"
echo "📦 Modal version: $(python -c 'import modal; print(modal.__version__)')"
echo ""
echo "To deactivate, run: deactivate"
echo "To use modal commands, run: python -m modal [command]"
