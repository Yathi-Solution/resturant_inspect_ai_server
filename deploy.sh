#!/bin/bash
# Deploy to both GitHub and HF Spaces
# Usage: ./deploy.sh "your commit message"

MESSAGE="${1:-Update deployment}"

echo "🚀 Starting deployment..."

# Stage all changes
echo ""
echo "📦 Staging changes..."
git add .

# Commit
echo "💾 Committing: $MESSAGE"
git commit -m "$MESSAGE"

# Push to GitHub (with docs)
echo ""
echo "📤 Pushing to GitHub..."
git push origin main

if [ $? -ne 0 ]; then
    echo "❌ GitHub push failed!"
    exit 1
fi

echo "✅ GitHub push successful!"

# Push to HF Spaces (without docs)
echo ""
echo "🤗 Pushing to HF Spaces..."

# Create clean branch
git checkout --orphan hf-temp > /dev/null 2>&1

# Remove ALL files from index (keep working tree)
git rm -rf . --cached --quiet

# Add only deployment files (no docs/)
git add .gitignore Dockerfile main.py pyproject.toml README.md train.py upload_model.py .env.example

# Commit
git commit -m "$MESSAGE" > /dev/null 2>&1

# Push to HF
git push hf hf-temp:main --force

if [ $? -ne 0 ]; then
    echo "❌ HF Spaces push failed!"
    git checkout main -f > /dev/null 2>&1
    git branch -D hf-temp 2>/dev/null
    exit 1
fi

# Cleanup
git checkout main -f > /dev/null 2>&1
git branch -D hf-temp 2>/dev/null

echo "✅ HF Spaces push successful!"
echo ""
echo "🎉 Deployment complete!"
echo "   GitHub: https://github.com/Yathi-Solution/resturant_inspect_ai_server"
echo "   HF Spaces: https://dpratapx-restaurant-inspector-api-dev.hf.space"
