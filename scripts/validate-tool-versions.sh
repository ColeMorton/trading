#!/bin/bash
# Validates that all tools run through Poetry for version consistency

echo "🔍 Validating Poetry-first tool usage..."

ERRORS=0

# Check if any direct tool calls exist in scripts and Makefiles
echo "Checking for direct tool calls..."

# Search for problematic patterns
if grep -r "^\s*black " scripts/ Makefile tests/Makefile 2>/dev/null | grep -v "poetry run"; then
    echo "❌ Found direct 'black' calls (should be 'poetry run black')"
    ERRORS=$((ERRORS + 1))
fi

if grep -r "^\s*isort " scripts/ Makefile tests/Makefile 2>/dev/null | grep -v "poetry run"; then
    echo "❌ Found direct 'isort' calls (should be 'poetry run isort')"
    ERRORS=$((ERRORS + 1))
fi

if grep -r "^\s*flake8 " scripts/ Makefile tests/Makefile 2>/dev/null | grep -v "poetry run"; then
    echo "❌ Found direct 'flake8' calls (should be 'poetry run flake8')"
    ERRORS=$((ERRORS + 1))
fi

if grep -r "^\s*mypy " scripts/ Makefile tests/Makefile 2>/dev/null | grep -v "poetry run"; then
    echo "❌ Found direct 'mypy' calls (should be 'poetry run mypy')"
    ERRORS=$((ERRORS + 1))
fi

if grep -r "^\s*ruff " scripts/ Makefile tests/Makefile 2>/dev/null | grep -v "poetry run"; then
    echo "❌ Found direct 'ruff' calls (should be 'poetry run ruff')"
    ERRORS=$((ERRORS + 1))
fi

# Check for python -m calls (exclude this script)
if grep -r "python -m black" scripts/ Makefile tests/Makefile 2>/dev/null | grep -v "validate-tool-versions.sh"; then
    echo "❌ Found 'python -m black' calls (should be 'poetry run black')"
    ERRORS=$((ERRORS + 1))
fi

if grep -r "python -m isort" scripts/ Makefile tests/Makefile 2>/dev/null | grep -v "validate-tool-versions.sh"; then
    echo "❌ Found 'python -m isort' calls (should be 'poetry run isort')"
    ERRORS=$((ERRORS + 1))
fi

if grep -r "python -m flake8" scripts/ Makefile tests/Makefile 2>/dev/null | grep -v "validate-tool-versions.sh"; then
    echo "❌ Found 'python -m flake8' calls (should be 'poetry run flake8')"
    ERRORS=$((ERRORS + 1))
fi

if grep -r "python -m mypy" scripts/ Makefile tests/Makefile 2>/dev/null | grep -v "validate-tool-versions.sh"; then
    echo "❌ Found 'python -m mypy' calls (should be 'poetry run mypy')"
    ERRORS=$((ERRORS + 1))
fi

# Check Poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found! Install with: curl -sSL https://install.python-poetry.org | python3 -"
    ERRORS=$((ERRORS + 1))
fi

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo "❌ pyproject.toml not found!"
    ERRORS=$((ERRORS + 1))
fi

# Check if poetry.lock exists
if [ ! -f "poetry.lock" ]; then
    echo "❌ poetry.lock not found! Run 'poetry install'"
    ERRORS=$((ERRORS + 1))
fi

# Check tool versions are consistent
echo "Checking tool versions..."
if command -v poetry &> /dev/null; then
    echo "Poetry version: $(poetry --version)"
    echo "Black version: $(poetry run black --version 2>/dev/null || echo 'Not installed')"
    echo "isort version: $(poetry run isort --version 2>/dev/null || echo 'Not installed')"
    echo "mypy version: $(poetry run mypy --version 2>/dev/null || echo 'Not installed')"
    echo "ruff version: $(poetry run ruff --version 2>/dev/null || echo 'Not installed')"
fi

if [ $ERRORS -eq 0 ]; then
    echo "✅ All tools correctly use Poetry!"
    echo "✅ Poetry-first strategy is properly implemented"
    exit 0
else
    echo "❌ Found $ERRORS violations of Poetry-first policy"
    echo ""
    echo "Fix these issues by:"
    echo "1. Replace direct tool calls with 'poetry run <tool>'"
    echo "2. Use 'make' commands instead of direct calls"
    echo "3. Ensure Poetry is installed and dependencies are up to date"
    exit 1
fi
