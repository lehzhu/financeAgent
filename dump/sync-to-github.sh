#!/bin/bash

# Auto-sync script for financeAgent repository
# This script automatically adds, commits, and pushes changes to GitHub

echo "🔄 Starting auto-sync to GitHub..."

# Check if there are any changes
if [[ -n $(git status --porcelain) ]]; then
    echo "📝 Changes detected, adding and committing..."
    
    # Add all changes
    git add .
    
    # Commit with timestamp
    git commit -m "Auto-sync: $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Push to GitHub
    echo "🚀 Pushing to GitHub..."
    git push origin master
    
    echo "✅ Successfully synced to GitHub!"
else
    echo "📋 No changes to sync."
fi

echo "🔗 Repository: https://github.com/lehzhu/financeAgent"
