# Quick Start Script for Streamlit Admin Dashboard
# Run this from project root directory

Write-Host "🍽️  Restaurant Inspector - Admin Dashboard Setup" -ForegroundColor Green
Write-Host ""

# Check if venv is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Virtual environment not activated!" -ForegroundColor Yellow
    Write-Host "Please run: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Virtual environment active: $env:VIRTUAL_ENV" -ForegroundColor Green
Write-Host ""

# Check if streamlit is installed
$streamlitInstalled = pip list | Select-String "streamlit"
if (-not $streamlitInstalled) {
    Write-Host "📦 Installing Streamlit dependencies..." -ForegroundColor Yellow
    pip install streamlit pandas plotly
    Write-Host "✅ Dependencies installed!" -ForegroundColor Green
    Write-Host ""
}

# Apply migrations
Write-Host "🔄 Applying database migrations..." -ForegroundColor Cyan
$env:PYTHONPATH = '.'
alembic upgrade head

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Migration failed. Check database connection in .env" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Migrations applied successfully!" -ForegroundColor Green
Write-Host ""

# Start Streamlit
Write-Host "🚀 Starting Streamlit Admin Dashboard..." -ForegroundColor Cyan
Write-Host "📍 URL: http://localhost:8501" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

Set-Location streamlit_app
streamlit run Home.py
