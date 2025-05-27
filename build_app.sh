#!/bin/bash

# MacMuteOnLocation Build Script
# This script builds the macOS app bundle using py2app

set -e  # Exit on any error

echo "🚀 Building MacMuteOnLocation..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected. Activating venv..."
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Virtual environment not found. Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
fi

# Check if py2app is installed
if ! python -c "import py2app" 2>/dev/null; then
    echo "⚠️  py2app not found. Installing..."
    pip install py2app
fi

# Check if app_icon.icns exists
if [ ! -f "app_icon.icns" ]; then
    echo "❌ app_icon.icns not found. Please ensure the icon file exists."
    echo "💡 You can create it from icon.iconset/ using: iconutil -c icns icon.iconset"
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist

# Build the app
echo "🔨 Building app bundle..."
python setup.py py2app

if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully!"
    echo "📱 App bundle created at: dist/MacMuteOnLocation.app"
    echo ""
    echo "🎯 Next steps:"
    echo "   • Test the app: open dist/MacMuteOnLocation.app"
    echo "   • For distribution, consider code signing and notarization"
    echo "   • See README.md for more information"
else
    echo "❌ Build failed. Check the error messages above."
    exit 1
fi