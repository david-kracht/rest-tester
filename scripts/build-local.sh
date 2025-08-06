#!/bin/bash

# Script zum lokalen Testen des Build-Prozesses

set -e

echo "🔧 Installing Poetry dependencies..."
poetry install

echo "🧪 Running tests..."
if [ -d "tests" ] || find . -name "test_*.py" -o -name "*_test.py" | grep -q .; then
  poetry run pytest -v
else
  echo "No tests found, skipping test execution"
fi

echo "📦 Building package..."
poetry build

echo "✅ Build completed successfully!"
echo "📁 Built packages:"
ls -la dist/

echo ""
echo "🚀 To publish manually:"
echo "  Test PyPI: poetry publish -r testpypi"
echo "  Prod PyPI: poetry publish"
echo ""
echo "⚠️  Don't forget to configure repositories first:"
echo "  poetry config repositories.testpypi https://test.pypi.org/legacy/"
echo "  poetry config pypi-token.testpypi [YOUR_TEST_TOKEN]"
echo "  poetry config pypi-token.pypi [YOUR_PROD_TOKEN]"
