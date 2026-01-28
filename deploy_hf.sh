#!/bin/bash

# Hugging Face Deployment Script
# This script helps you deploy to HF Spaces

set -e

echo "🚀 Deploying to Hugging Face Spaces"
echo ""

# Check if HF username is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide your Hugging Face username"
    echo "Usage: ./deploy_hf.sh YOUR_USERNAME"
    exit 1
fi

HF_USERNAME=$1
SPACE_NAME="intelligent-data-room"
HF_REPO="https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"

echo "📦 Deploying to: $HF_REPO"
echo ""

# Check if git remote exists
if git remote get-url hf > /dev/null 2>&1; then
    echo "✓ HF remote already exists"
else
    echo "➕ Adding HF remote..."
    git remote add hf $HF_REPO
fi

# Copy README for HF Space
echo "📝 Preparing README..."
cp README_HF_SPACE.md README.md

# Ensure required files exist
echo "✓ Checking files..."
if [ ! -f "Dockerfile" ]; then
    echo "❌ Error: Dockerfile not found"
    exit 1
fi

if [ ! -d "backend" ]; then
    echo "❌ Error: backend directory not found"
    exit 1
fi

# Stage files
echo "📦 Staging files..."
git add Dockerfile .dockerignore backend/ README.md

# Commit
echo "💾 Committing..."
git commit -m "Deploy to Hugging Face Spaces" || echo "No changes to commit"

# Push
echo "🚀 Pushing to Hugging Face..."
git push hf main

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "📊 Your Space: https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"
echo "📖 Docs: https://$HF_USERNAME-$SPACE_NAME.hf.space/docs"
echo "🏥 Health: https://$HF_USERNAME-$SPACE_NAME.hf.space/health"
echo ""
echo "⏳ Build will take ~5-10 minutes"
echo "📝 Don't forget to add secrets in Space Settings!"
echo ""
