#!/bin/bash
# Release script for fastapi-sse-events
# Usage: ./release.sh [patch|minor|major]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get current version
CURRENT_VERSION=$(grep -Po '(?<=version = ")[^"]*' pyproject.toml)

echo -e "${GREEN}FastAPI SSE Events - Release Script${NC}"
echo -e "${YELLOW}Current version: $CURRENT_VERSION${NC}"
echo ""

# Parse version bump type
BUMP_TYPE=${1:-patch}

if [[ ! "$BUMP_TYPE" =~ ^(patch|minor|major)$ ]]; then
    echo -e "${RED}Error: Invalid bump type. Use: patch, minor, or major${NC}"
    exit 1
fi

echo -e "${YELLOW}Preparing $BUMP_TYPE release...${NC}"
echo ""

# Run checks
echo "🔍 Running pre-release checks..."
echo ""

echo "  ✓ Running tests..."
pytest tests/ -v -q || { echo -e "${RED}Tests failed!${NC}"; exit 1; }

echo "  ✓ Running linting..."
ruff check fastapi_sse_events/ tests/ examples/ || { echo -e "${RED}Linting failed!${NC}"; exit 1; }

echo "  ✓ Checking formatting..."
ruff format --check fastapi_sse_events/ tests/ examples/ || { echo -e "${RED}Formatting check failed!${NC}"; exit 1; }

echo "  ✓ Running type checks..."
mypy fastapi_sse_events/ || { echo -e "${RED}Type checking failed!${NC}"; exit 1; }

echo ""
echo -e "${GREEN}✓ All checks passed!${NC}"
echo ""

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info

# Build package
echo "📦 Building package..."
python -m build

# Check package
echo "🔎 Checking package..."
twine check dist/*

echo ""
echo -e "${GREEN}✓ Package built successfully!${NC}"
echo ""

# Show what will be published
echo "📋 Package contents:"
tar -tzf dist/*.tar.gz | head -20
echo "..."
echo ""

# Confirm publication
echo -e "${YELLOW}Ready to publish version $CURRENT_VERSION to PyPI${NC}"
echo ""
read -p "Continue with publication? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Publication cancelled."
    exit 0
fi

# Publish to PyPI
echo "🚀 Publishing to PyPI..."
twine upload dist/*

echo ""
echo -e "${GREEN}✓ Successfully published version $CURRENT_VERSION!${NC}"
echo ""
echo "Next steps:"
echo "  1. Create a git tag: git tag v$CURRENT_VERSION"
echo "  2. Push the tag: git push origin v$CURRENT_VERSION"
echo "  3. Create a GitHub release with the tag"
echo "  4. Update CHANGELOG.md for the next version"
echo ""
echo -e "${GREEN}Release complete! 🎉${NC}"
