#!/bin/bash

# Google File Search RAG System Setup Script

echo "🚀 Setting up Google File Search RAG System..."
echo "================================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found. Please install Python 3."
    exit 1
fi

echo "✅ Python 3 found"

# Create virtual environment (optional but recommended)
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your GEMINI_API_KEY"
    echo "   Get your API key from: https://aistudio.google.com/apikey"
    echo ""
fi

# Create data directories
echo "📁 Setting up data directories..."
mkdir -p data/documents
mkdir -p data/processed

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your GEMINI_API_KEY"
echo "2. Add some documents to data/documents/"
echo "3. Run the basic example:"
echo "   python examples/basic_rag.py"
echo ""
echo "Or use the CLI interface:"
echo "   python main.py --help"
echo ""
echo "Example commands:"
echo "   python main.py create-store my-docs"
echo "   python main.py upload-dir data/documents my-docs"
echo "   python main.py search \"What is this about?\" my-docs"
echo "   python main.py interactive my-docs"