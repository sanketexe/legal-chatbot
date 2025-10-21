# LegalCounsel AI - Quick Start Script
Write-Host "🏛️ Starting LegalCounsel AI..." -ForegroundColor Blue

# Set API key
$env:GEMINI_API_KEY="AIzaSyCyczq89UskHYsSjm_5ga5XtqLTDbPvx3k"

# Check if required packages are installed
Write-Host "📦 Checking dependencies..." -ForegroundColor Yellow
$packages = @("flask", "flask-cors", "flask-sqlalchemy", "flask-jwt-extended", "bcrypt", "python-dotenv", "google-generativeai")

foreach ($package in $packages) {
    $installed = pip show $package 2>$null
    if (-not $installed) {
        Write-Host "❌ $package not found. Installing..." -ForegroundColor Red
        pip install $package
    } else {
        Write-Host "✅ $package installed" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "🚀 Starting LegalCounsel AI Application..." -ForegroundColor Green
Write-Host "🌐 Web Application: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "👤 Default Login: admin / admin123" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Run the application
python app_with_db.py