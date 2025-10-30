#!/usr/bin/env bash
#
# Comprehensive commit verification script
# Runs all pre-commit hooks plus additional security checks
#
# Usage:
#   ./scripts/verify-commit.sh           # Run all checks
#   ./scripts/verify-commit.sh --quick   # Run only critical checks
#   ./scripts/verify-commit.sh --security-only  # Run only security checks
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Emojis
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
LOCK="🔒"
ROCKET="🚀"

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0

# Functions
print_header() {
    echo -e "\n${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE} $1${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
    ((CHECKS_PASSED++))
}

print_error() {
    echo -e "${RED}${CROSS} $1${NC}"
    ((CHECKS_FAILED++))
}

print_warning() {
    echo -e "${YELLOW}${WARNING} $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

run_check() {
    local check_name="$1"
    local check_command="$2"
    local is_critical="${3:-false}"

    echo -e "\n${BOLD}Running: ${check_name}${NC}"
    if eval "$check_command"; then
        print_success "$check_name passed"
        return 0
    else
        if [ "$is_critical" = "true" ]; then
            print_error "$check_name FAILED (CRITICAL)"
            return 1
        else
            print_warning "$check_name failed (non-blocking)"
            return 0
        fi
    fi
}

# Parse command line arguments
MODE="full"
if [ $# -gt 0 ]; then
    case "$1" in
        --quick)
            MODE="quick"
            ;;
        --security-only)
            MODE="security"
            ;;
        --help)
            echo "Usage: $0 [--quick|--security-only|--help]"
            echo ""
            echo "Options:"
            echo "  --quick          Run only critical checks (fast)"
            echo "  --security-only  Run only security scanning"
            echo "  --help           Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
fi

print_header "${LOCK} Security & Quality Verification"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository"
    exit 1
fi

# Check if poetry is available
if ! command -v poetry &> /dev/null; then
    print_error "Poetry is not installed. Please install it first."
    exit 1
fi

# Main checks
case "$MODE" in
    security)
        print_header "${LOCK} Running Security Checks Only"

        # 1. Bandit security scan (CRITICAL)
        run_check "${LOCK} Bandit Security Scan" \
            "poetry run bandit -r app/ -ll --exclude app/trading_bot/trendspider/" \
            "true" || exit 1

        # 2. Check for secrets/keys
        run_check "${LOCK} Detect Private Keys" \
            "! git diff --cached --name-only | xargs grep -l 'BEGIN.*PRIVATE KEY' 2>/dev/null" \
            "true" || exit 1

        # 3. Check for TODO security markers
        run_check "${WARNING} Check Security TODOs" \
            "! git diff --cached | grep -i 'TODO.*security\|FIXME.*security\|XXX.*security' 2>/dev/null" \
            "false"
        ;;

    quick)
        print_header "${ROCKET} Running Quick Critical Checks"

        # 1. Ruff format check
        run_check "Ruff Format Check" \
            "poetry run ruff format --check app/ tests/" \
            "true" || exit 1

        # 2. Ruff linting
        run_check "Ruff Linting" \
            "poetry run ruff check app/ tests/" \
            "true" || exit 1

        # 3. Bandit security scan (CRITICAL)
        run_check "${LOCK} Bandit Security Scan" \
            "poetry run bandit -r app/ -ll --exclude app/trading_bot/trendspider/" \
            "true" || exit 1
        ;;

    full)
        print_header "${ROCKET} Running Full Verification Suite"

        # 1. Pre-commit hooks
        print_info "Running all pre-commit hooks..."
        if poetry run pre-commit run --all-files; then
            print_success "Pre-commit hooks passed"
        else
            print_error "Pre-commit hooks failed"
            echo ""
            print_info "Run 'poetry run pre-commit run --all-files' to see details"
            exit 1
        fi

        # 2. Additional security checks
        print_header "${LOCK} Additional Security Checks"

        # Check for hardcoded secrets patterns
        run_check "Check for Hardcoded Secrets" \
            "! git diff --cached | grep -iE 'password.*=.*['\''\"]\w+|api[_-]?key.*=.*['\''\"]\w+|secret.*=.*['\''\"]\w+' 2>/dev/null" \
            "true" || exit 1

        # Check for print statements (debugging leftovers)
        run_check "Check for Debug Print Statements" \
            "! git diff --cached app/ | grep -E '^\+.*print\(' 2>/dev/null | grep -v '# noqa: T201'" \
            "false"

        # Check for large files
        run_check "Check for Large Files (>1MB)" \
            "! git diff --cached --name-only | xargs ls -lh 2>/dev/null | awk '{if(\$5~/M/ && \$5+0>1) print}' | grep ." \
            "true" || exit 1
        ;;
esac

# Summary
print_header "Verification Summary"
echo -e "${BOLD}Checks Passed:${NC} ${GREEN}${CHECKS_PASSED}${NC}"
echo -e "${BOLD}Checks Failed:${NC} ${RED}${CHECKS_FAILED}${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}${CHECK} ${BOLD}All checks passed! Safe to commit.${NC}\n"
    exit 0
else
    echo -e "${RED}${CROSS} ${BOLD}Some checks failed. Please fix the issues before committing.${NC}\n"
    exit 1
fi
