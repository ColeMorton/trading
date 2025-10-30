#!/bin/bash
# Test GitHub Actions workflows locally using act
# https://github.com/nektos/act

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if act is installed
if ! command -v act &> /dev/null; then
    print_error "act is not installed!"
    echo ""
    echo "Install act with:"
    echo "  macOS: brew install act"
    echo "  Linux: curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash"
    echo ""
    echo "Documentation: https://github.com/nektos/act"
    exit 1
fi

# Check if .secrets file exists
if [ ! -f ".secrets" ]; then
    print_warning ".secrets file not found"
    echo "Copy .secrets.example to .secrets and fill in your values:"
    echo "  cp .secrets.example .secrets"
    echo ""
    print_warning "Continuing without secrets..."
    echo ""
fi

# Parse arguments
WORKFLOW=""
JOB=""
EVENT=""
EVENT_FILE=""
DRY_RUN=false
LIST=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--workflow)
            WORKFLOW="$2"
            shift 2
            ;;
        -j|--job)
            JOB="$2"
            shift 2
            ;;
        -e|--event)
            EVENT="$2"
            shift 2
            ;;
        -f|--event-file)
            EVENT_FILE="$2"
            shift 2
            ;;
        -n|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -l|--list)
            LIST=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -w, --workflow FILE    Workflow file to run (e.g., ci-cd.yml)"
            echo "  -j, --job NAME         Specific job to run"
            echo "  -e, --event TYPE       Event type (push, pull_request, workflow_dispatch)"
            echo "  -f, --event-file FILE  Event payload JSON file"
            echo "  -n, --dry-run          Show what would run without executing"
            echo "  -l, --list             List all workflows and jobs"
            echo "  -v, --verbose          Show verbose output"
            echo "  -h, --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --list"
            echo "  $0 --workflow ci-cd.yml --job lint --dry-run"
            echo "  $0 --job test-backend"
            echo "  $0 --event push --event-file .github/workflows/events/push-develop.json"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# List workflows
if [ "$LIST" = true ]; then
    print_step "Available workflows and jobs:"
    echo ""
    act -l
    exit 0
fi

# Build act command
ACT_CMD="act"

# Add workflow file if specified
if [ -n "$WORKFLOW" ]; then
    ACT_CMD="$ACT_CMD -W .github/workflows/$WORKFLOW"
fi

# Add job if specified
if [ -n "$JOB" ]; then
    ACT_CMD="$ACT_CMD -j $JOB"
fi

# Add event if specified
if [ -n "$EVENT" ]; then
    ACT_CMD="$ACT_CMD $EVENT"
fi

# Add event file if specified
if [ -n "$EVENT_FILE" ]; then
    if [ ! -f "$EVENT_FILE" ]; then
        print_error "Event file not found: $EVENT_FILE"
        exit 1
    fi
    ACT_CMD="$ACT_CMD -e $EVENT_FILE"
fi

# Add dry-run flag
if [ "$DRY_RUN" = true ]; then
    ACT_CMD="$ACT_CMD -n"
fi

# Add verbose flag
if [ "$VERBOSE" = true ]; then
    ACT_CMD="$ACT_CMD -v"
fi

# Run act
print_step "Running: $ACT_CMD"
echo ""

eval $ACT_CMD

if [ $? -eq 0 ]; then
    echo ""
    print_success "Workflow completed successfully!"
else
    echo ""
    print_error "Workflow failed!"
    exit 1
fi
