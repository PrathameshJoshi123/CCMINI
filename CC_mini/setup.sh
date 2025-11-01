#!/bin/bash

# NotesLLM Frontend Setup Script
# This script automates the initial setup process

echo "🚀 NotesLLM Frontend Setup"
echo "=========================="
echo ""

# Check Node.js version
echo "📦 Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version must be 18 or higher. Current version: $(node --version)"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"
echo ""

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo "🔧 Creating .env.local file..."
    cp .env.example .env.local
    echo "✅ .env.local created"
    echo ""
    echo "📝 You can edit .env.local to configure:"
    echo "   - VITE_API_BASE_URL (default: http://localhost:8000)"
    echo "   - VITE_POLLING_INTERVAL (default: 5000ms)"
    echo "   - VITE_MAX_FILE_SIZE (default: 50MB)"
else
    echo "✅ .env.local already exists"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Ensure your backend is running at http://localhost:8000"
echo "   2. Start the development server:"
echo "      npm run dev"
echo ""
echo "   3. Open http://localhost:5173 in your browser"
echo ""
echo "📚 Documentation:"
echo "   - README.md - Full documentation"
echo "   - GETTING_STARTED.md - Quick start guide"
echo "   - PROJECT_SUMMARY.md - Project overview"
echo ""
echo "Happy coding! 🚀"
