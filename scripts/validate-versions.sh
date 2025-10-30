#!/bin/bash
# Script to validate that tool versions are consistent across the project
# Checks that all version references match the canonical .versions file

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track errors
ERRORS=0
WARNINGS=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Validating Tool Version Consistency"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Load versions from canonical .versions file
if [ ! -f .versions ]; then
    echo -e "${RED}❌ ERROR: .versions file not found${NC}"
    exit 1
fi

source .versions

echo "📋 Canonical Versions (from .versions):"
echo "  Python: ${PYTHON_VERSION}"
echo "  Poetry: ${POETRY_VERSION}"
echo "  Node: ${NODE_VERSION}"
echo "  PostgreSQL: ${POSTGRES_VERSION}"
echo "  Redis: ${REDIS_VERSION}"
echo ""

# Function to check version match
check_version() {
    local file=$1
    local expected=$2
    local found=$3
    local description=$4

    if [ "$expected" != "$found" ]; then
        echo -e "${RED}❌ MISMATCH in $file${NC}"
        echo "   $description"
        echo "   Expected: $expected"
        echo "   Found: $found"
        ((ERRORS++))
        return 1
    else
        echo -e "${GREEN}✅ $file${NC}"
        return 0
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Checking Docker Configuration..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Dockerfile.api
if [ -f Dockerfile.api ]; then
    # Check Poetry version in ARG
    DOCKER_POETRY=$(grep "^ARG POETRY_VERSION=" Dockerfile.api | head -1 | cut -d'=' -f2)
    check_version "Dockerfile.api" "$POETRY_VERSION" "$DOCKER_POETRY" "Poetry ARG default"

    # Check Python version in ARG
    DOCKER_PYTHON=$(grep "^ARG PYTHON_VERSION=" Dockerfile.api | head -1 | cut -d'=' -f2)
    check_version "Dockerfile.api" "$PYTHON_VERSION" "$DOCKER_PYTHON" "Python ARG default"
else
    echo -e "${YELLOW}⚠️  Dockerfile.api not found${NC}"
    ((WARNINGS++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Checking GitHub Actions..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check composite action (source of truth for GHA)
ACTION_FILE=".github/actions/setup-python-poetry/action.yml"
if [ -f "$ACTION_FILE" ]; then
    # Extract versions using awk to handle YAML structure properly
    ACTION_POETRY=$(awk '/poetry-version:/,/default:/ {if (/default:/) print $2}' "$ACTION_FILE" | tr -d "'\"")
    check_version "$ACTION_FILE" "$POETRY_VERSION" "$ACTION_POETRY" "Poetry default in composite action"

    ACTION_PYTHON=$(awk '/python-version:/,/default:/ {if (/default:/) print $2}' "$ACTION_FILE" | head -1 | tr -d "'\"")
    check_version "$ACTION_FILE" "$PYTHON_VERSION" "$ACTION_PYTHON" "Python default in composite action"
else
    echo -e "${RED}❌ ERROR: $ACTION_FILE not found${NC}"
    ((ERRORS++))
fi

# Check for any hardcoded POETRY_VERSION in workflows (should be removed)
echo ""
echo "Checking for hardcoded versions in workflows..."
HARDCODED=$(grep -r "POETRY_VERSION:" .github/workflows/ 2>/dev/null || true)
if [ -n "$HARDCODED" ]; then
    echo -e "${YELLOW}⚠️  WARNING: Found hardcoded POETRY_VERSION in workflows:${NC}"
    echo "$HARDCODED"
    echo -e "${YELLOW}   These should use the composite action default instead${NC}"
    ((WARNINGS++))
else
    echo -e "${GREEN}✅ No hardcoded POETRY_VERSION in workflows${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 SUCCESS: All versions are consistent!${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  WARNINGS: $WARNINGS warnings found${NC}"
    echo ""
    echo "Warnings don't block builds but should be addressed."
    exit 0
else
    echo -e "${RED}❌ FAILURE: $ERRORS errors found${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Also found: $WARNINGS warnings${NC}"
    fi
    echo ""
    echo "Version Consistency Policy:"
    echo "  1. .versions file is the canonical source of truth"
    echo "  2. Dockerfile.api ARG defaults must match .versions"
    echo "  3. GitHub Actions composite action defaults must match .versions"
    echo "  4. Individual workflows should NOT hardcode versions"
    echo ""
    echo "To fix:"
    echo "  1. Update .versions file with desired versions"
    echo "  2. Update Dockerfile.api ARG defaults"
    echo "  3. Update .github/actions/setup-python-poetry/action.yml defaults"
    echo "  4. Remove POETRY_VERSION from individual workflow env sections"
    echo ""
    exit 1
fi
