# Deploy to both GitHub and HF Spaces
# Usage: .\deploy.ps1 "your commit message"

param(
    [string]$message = "Update deployment"
)

Write-Host "Starting deployment..." -ForegroundColor Green

# Stage all changes
Write-Host "`nStaging changes..." -ForegroundColor Yellow
git add .

# Commit
Write-Host "Committing: $message" -ForegroundColor Yellow
git commit -m $message

# Push to GitHub (with docs)
Write-Host "`nPushing to GitHub..." -ForegroundColor Yellow
git push origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host "GitHub push failed!" -ForegroundColor Red
    exit 1
}

Write-Host "GitHub push successful!" -ForegroundColor Green

# Push to HF Spaces (without docs)
Write-Host "`nPushing to HF Spaces..." -ForegroundColor Yellow

# Create clean branch
git checkout --orphan hf-temp | Out-Null

# Remove ALL files from index (keep working tree)
git rm -rf . --cached --quiet

# Add only deployment files (no docs/)
git add .gitignore Dockerfile main.py pyproject.toml README.md train.py upload_model.py .env.example

# Commit
git commit -m $message

# Push to HF
git push hf hf-temp:main --force

if ($LASTEXITCODE -ne 0) {
    Write-Host "HF Spaces push failed!" -ForegroundColor Red
    git checkout main | Out-Null
    git branch -D hf-temp | Out-Null
    exit 1
}

# Cleanup
git checkout main | Out-Null
git branch -D hf-temp | Out-Null

Write-Host "HF Spaces push successful!" -ForegroundColor Green
Write-Host "`nDeployment complete!" -ForegroundColor Green
Write-Host "   GitHub: https://github.com/Yathi-Solution/resturant_inspect_ai_server" -ForegroundColor Cyan
Write-Host "   HF Spaces: https://dpratapx-restaurant-inspector-api-dev.hf.space" -ForegroundColor Cyan
