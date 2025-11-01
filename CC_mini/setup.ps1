# NotesLLM Frontend Setup Script (PowerShell)
# This script automates the initial setup process for Windows

Write-Host "🚀 NotesLLM Frontend Setup" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan
Write-Host ""

# Check Node.js installation
Write-Host "📦 Checking Node.js version..." -ForegroundColor Yellow

try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js version: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
Write-Host ""

# Create .env.local if it doesn't exist
if (-not (Test-Path .env.local)) {
    Write-Host "🔧 Creating .env.local file..." -ForegroundColor Yellow
    Copy-Item .env.example .env.local
    Write-Host "✅ .env.local created" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 You can edit .env.local to configure:" -ForegroundColor Yellow
    Write-Host "   - VITE_API_BASE_URL (default: http://localhost:8000)"
    Write-Host "   - VITE_POLLING_INTERVAL (default: 5000ms)"
    Write-Host "   - VITE_MAX_FILE_SIZE (default: 50MB)"
} else {
    Write-Host "✅ .env.local already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "✨ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Ensure your backend is running at http://localhost:8000"
Write-Host "   2. Start the development server:"
Write-Host "      npm run dev" -ForegroundColor Yellow
Write-Host ""
Write-Host "   3. Open http://localhost:5173 in your browser"
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   - README.md - Full documentation"
Write-Host "   - GETTING_STARTED.md - Quick start guide"
Write-Host "   - PROJECT_SUMMARY.md - Project overview"
Write-Host ""
Write-Host "Happy coding! 🚀" -ForegroundColor Green
