#!/bin/bash

# Helper script to initialize git and push Autonomous Lead Enrichment Agent to GitHub

if [ -z "$1" ]; then
    echo "================================================================="
    echo "❌ Usage: ./push_to_github.sh <YOUR_GITHUB_REPO_URL>"
    echo "Example: ./push_to_github.sh https://github.com/username/lead-enrichment-agent.git"
    echo "================================================================="
    exit 1
fi

REPO_URL=$1

echo "🚀 Initializing Git repository..."
git init

echo "📦 Staging all project files..."
git add .

echo "📝 Creating initial commit..."
git commit -m "Initial commit: Autonomous Lead Enrichment Agent pipeline"

echo "🔗 Linking remote repository: $REPO_URL"
git remote remove origin 2>/dev/null
git remote add origin "$REPO_URL"

echo "⬆️ Pushing code to main branch..."
git branch -M main
git push -u origin main

echo ""
echo "================================================================="
echo "✅ Successfully pushed Autonomous Lead Enrichment Agent to GitHub!"
echo "URL: $REPO_URL"
echo "================================================================="
