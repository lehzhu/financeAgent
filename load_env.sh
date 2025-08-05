#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    echo "🔑 Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded!"
    echo "🔍 OPENAI_API_KEY is $([ -n "$OPENAI_API_KEY" ] && echo "set" || echo "not set")"
else
    echo "❌ .env file not found!"
    echo "Please create a .env file with your OPENAI_API_KEY"
fi
