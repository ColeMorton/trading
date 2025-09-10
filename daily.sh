#!/usr/bin/env bash
# Script: daily.sh
# Purpose: Daily execution of trading-cli commands via YAML configuration
# Requirements: bash 4+, yq, poetry, trading-cli
# Compatibility: Linux, macOS

# Strict error handling
set -euo pipefail
IFS=$'\n\t'

# Global configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly DEFAULT_CONFIG_FILE="${SCRIPT_DIR}/daily-config.yaml"
CONFIG_FILE="${DEFAULT_CONFIG_FILE}"
readonly LOG_DIR="${SCRIPT_DIR}/logs/daily"
LOG_FILE="${LOG_DIR}/daily_$(date '+%Y%m%d').log"
readonly LOCK_FILE="${SCRIPT_DIR}/.daily_execution.lock"
readonly MAX_LOG_FILES=30
readonly COMMAND_TIMEOUT_DEFAULT=600
readonly TEST_CONFIG_FILE="${SCRIPT_DIR}/daily-test-config.yaml"
TEST_LOG_FILE="${LOG_DIR}/test_$(date '+%Y%m%d_%H%M%S').log"

# Allowed trading-cli commands (security whitelist)
readonly -a ALLOWED_COMMANDS=(
    "strategy" "portfolio" "concurrency" "spds" "trade-history"
    "positions" "seasonality" "tools" "config" "status" "init" "version"
)

# Initialize logging
init_logging() {
    mkdir -p "${LOG_DIR}"

    # Clean up old log files
    find "${LOG_DIR}" -name "daily_*.log" -mtime +${MAX_LOG_FILES} -delete 2>/dev/null || true

    # Initialize log file
    {
        echo "========================================="
        echo "Daily Trading CLI Execution Started"
        echo "Date: $(date '+%Y-%m-%d %H:%M:%S %Z')"
        echo "PID: $$"
        echo "========================================="
    } > "${LOG_FILE}"
}

# Logging function with levels
log() {
    local level=$(echo "${1}" | tr '[:lower:]' '[:upper:]')  # Convert to uppercase (portable)
    local message="${2}"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"

    echo "[${timestamp}] [${level}] ${message}" | tee -a "${LOG_FILE}"

    # Also log to stderr for ERROR and WARN levels
    if [[ "${level}" =~ ^(ERROR|WARN)$ ]]; then
        echo "[${timestamp}] [${level}] ${message}" >&2
    fi
}

# Error handling function
error_exit() {
    local message="${1:-Unknown error}"
    local exit_code="${2:-1}"

    log "ERROR" "${message}"
    log "ERROR" "Script execution failed with exit code ${exit_code}"

    # Clean up lock file on error
    cleanup_lock

    exit "${exit_code}"
}

# Cleanup function for graceful shutdown
cleanup() {
    log "INFO" "Cleaning up resources..."
    cleanup_lock
    log "INFO" "Daily trading CLI execution completed"
}

# Lock file management
create_lock() {
    if [[ -f "${LOCK_FILE}" ]]; then
        local lock_pid
        lock_pid=$(cat "${LOCK_FILE}" 2>/dev/null || echo "unknown")

        # Check if process is still running
        if kill -0 "${lock_pid}" 2>/dev/null; then
            error_exit "Another instance is already running (PID: ${lock_pid})" 2
        else
            log "WARN" "Stale lock file found, removing..."
            rm -f "${LOCK_FILE}"
        fi
    fi

    echo $$ > "${LOCK_FILE}"
    log "INFO" "Created lock file with PID $$"
}

cleanup_lock() {
    if [[ -f "${LOCK_FILE}" ]]; then
        rm -f "${LOCK_FILE}"
        log "INFO" "Removed lock file"
    fi
}

# Signal handlers
trap cleanup EXIT
trap 'error_exit "Script interrupted by user" 130' INT
trap 'error_exit "Script terminated" 143' TERM

# Dependency validation
validate_dependencies() {
    local missing_deps=()

    # Check required commands
    local required_commands=("yq" "poetry" "timeout")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "${cmd}" >/dev/null 2>&1; then
            missing_deps+=("${cmd}")
        fi
    done

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        error_exit "Missing required dependencies: ${missing_deps[*]}" 3
    fi

    # Validate trading-cli is available
    if ! poetry run trading-cli --help >/dev/null 2>&1; then
        error_exit "trading-cli not available or not properly configured" 4
    fi

    log "INFO" "All dependencies validated successfully"
}

# Configuration validation
validate_config() {
    if [[ ! -f "${CONFIG_FILE}" ]]; then
        error_exit "Configuration file not found: ${CONFIG_FILE}" 5
    fi

    # Validate YAML structure
    if ! yq eval '.' "${CONFIG_FILE}" >/dev/null 2>&1; then
        error_exit "Invalid YAML syntax in configuration file" 6
    fi

    # Validate required fields exist
    local required_fields=("metadata.name" "config.commands")
    for field in "${required_fields[@]}"; do
        if ! yq eval ".${field}" "${CONFIG_FILE}" >/dev/null 2>&1; then
            error_exit "Missing required field in config: ${field}" 7
        fi
    done

    # Validate commands structure
    local command_count
    command_count=$(yq eval '.config.commands | length' "${CONFIG_FILE}")

    if [[ ${command_count} -eq 0 ]]; then
        error_exit "No commands defined in configuration" 8
    fi

    log "INFO" "Configuration validated successfully (${command_count} commands)"
}

# Command validation against security whitelist
validate_command() {
    local command="${1}"
    local main_command

    # Debug logging (only for test mode)
    if [[ "${TEST_MODE:-false}" == "true" ]]; then
        echo "DEBUG: validate_command called with: $command" >> "${TEST_LOG_FILE}"
    fi

    # Extract main command, handling poetry run prefix and global flags
    if [[ "${command}" =~ ^poetry[[:space:]]+run[[:space:]]+trading-cli[[:space:]]+(.+) ]]; then
        # Parse the rest of the command after "poetry run trading-cli "
        local cmd_rest="${BASH_REMATCH[1]}"

        # Debug logging
        if [[ "${TEST_MODE:-false}" == "true" ]]; then
            echo "DEBUG: cmd_rest = '$cmd_rest'" >> "${TEST_LOG_FILE}"
        fi

        # Skip global flags (--quiet, --verbose, --show-output, etc.) to find subcommand
        # Use bash parameter expansion to split on spaces
        local IFS=' '
        local tokens=($cmd_rest)
        for token in "${tokens[@]}"; do
            # Debug logging
            if [[ "${TEST_MODE:-false}" == "true" ]]; then
                echo "DEBUG: checking token = '$token'" >> "${TEST_LOG_FILE}"
            fi

            # If token doesn't start with -- or -, it's the subcommand
            if [[ ! "${token}" =~ ^-- ]] && [[ ! "${token}" =~ ^- ]]; then
                main_command="${token}"
                if [[ "${TEST_MODE:-false}" == "true" ]]; then
                    echo "DEBUG: found main_command = '$main_command'" >> "${TEST_LOG_FILE}"
                fi
                break
            fi
        done
    elif [[ "${command}" =~ ^trading-cli[[:space:]]+(.+) ]]; then
        # Handle direct trading-cli commands (same logic)
        local cmd_rest="${BASH_REMATCH[1]}"
        local IFS=' '
        local tokens=($cmd_rest)
        for token in "${tokens[@]}"; do
            if [[ ! "${token}" =~ ^-- ]] && [[ ! "${token}" =~ ^- ]]; then
                main_command="${token}"
                break
            fi
        done
    else
        if [[ "${TEST_MODE:-false}" == "true" ]]; then
            echo "DEBUG: command does not match expected pattern" >> "${TEST_LOG_FILE}"
        fi
        return 1
    fi

    # Ensure we found a main command
    if [[ -z "${main_command}" ]]; then
        if [[ "${TEST_MODE:-false}" == "true" ]]; then
            echo "DEBUG: main_command is empty, returning 1" >> "${TEST_LOG_FILE}"
        fi
        return 1
    fi

    # Debug logging
    if [[ "${TEST_MODE:-false}" == "true" ]]; then
        echo "DEBUG: checking main_command '$main_command' against allowed list" >> "${TEST_LOG_FILE}"
    fi

    # Check if main command is in allowed list
    for allowed in "${ALLOWED_COMMANDS[@]}"; do
        if [[ "${main_command}" == "${allowed}" ]]; then
            if [[ "${TEST_MODE:-false}" == "true" ]]; then
                echo "DEBUG: matched allowed command '$allowed'" >> "${TEST_LOG_FILE}"
            fi
            return 0
        fi
    done

    if [[ "${TEST_MODE:-false}" == "true" ]]; then
        echo "DEBUG: main_command '$main_command' not found in allowed list" >> "${TEST_LOG_FILE}"
    fi
    return 1
}

# Execute a single command with timeout and error handling
execute_command() {
    local name="${1}"
    local command="${2}"
    local enabled="${3}"
    local timeout_value="${4:-${COMMAND_TIMEOUT_DEFAULT}}"

    # Skip if disabled
    if [[ "$(echo "${enabled}" | tr '[:upper:]' '[:lower:]')" != "true" ]]; then
        log "INFO" "SKIPPED: ${name} (disabled)"
        return 0
    fi

    # Validate command security
    if ! validate_command "${command}"; then
        log "ERROR" "SECURITY: Command not allowed: ${command}"
        return 1
    fi

    # Execute with timeout and logging
    log "INFO" "STARTING: ${name}"
    log "DEBUG" "COMMAND: ${command}"
    log "DEBUG" "TIMEOUT: ${timeout_value}s"

    local start_time
    start_time=$(date +%s)

    # Create temporary files for output capture
    local stdout_file="${LOG_DIR}/cmd_stdout_$$.tmp"
    local stderr_file="${LOG_DIR}/cmd_stderr_$$.tmp"

    # Execute command with timeout
    if timeout "${timeout_value}" bash -c "cd '${SCRIPT_DIR}' && ${command}" \
        >"${stdout_file}" 2>"${stderr_file}"; then

        local end_time
        end_time=$(date +%s)
        local duration=$((end_time - start_time))

        log "INFO" "SUCCESS: ${name} (${duration}s)"

        # Log output if verbose or if there was any stderr
        if [[ -s "${stderr_file}" ]]; then
            log "WARN" "Command produced warnings:"
            while IFS= read -r line; do
                log "WARN" "  ${line}"
            done < "${stderr_file}"
        fi

        # Clean up temporary files
        rm -f "${stdout_file}" "${stderr_file}"
        return 0

    else
        local exit_code=$?
        local end_time
        end_time=$(date +%s)
        local duration=$((end_time - start_time))

        log "ERROR" "FAILED: ${name} (${duration}s, exit code: ${exit_code})"

        # Log stderr for debugging
        if [[ -s "${stderr_file}" ]]; then
            log "ERROR" "Error output:"
            while IFS= read -r line; do
                log "ERROR" "  ${line}"
            done < "${stderr_file}"
        fi

        # Clean up temporary files
        rm -f "${stdout_file}" "${stderr_file}"
        return ${exit_code}
    fi
}

# Main execution function
main() {
    # Initialize
    init_logging
    log "INFO" "Starting daily trading CLI automation"

    # Validate environment
    validate_dependencies
    validate_config

    # Create lock file
    create_lock

    # Load configuration
    local config_name
    config_name=$(yq eval '.metadata.name // "unnamed"' "${CONFIG_FILE}")
    log "INFO" "Loaded configuration: ${config_name}"

    # Execute commands sequentially
    local command_count
    command_count=$(yq eval '.config.commands | length' "${CONFIG_FILE}")

    local success_count=0
    local failure_count=0

    for ((i=0; i<command_count; i++)); do
        local name
        local command
        local enabled
        local timeout_value

        # Extract command details
        name=$(yq eval ".config.commands[${i}].name // \"Command ${i}\"" "${CONFIG_FILE}")
        command=$(yq eval ".config.commands[${i}].command" "${CONFIG_FILE}")
        enabled=$(yq eval ".config.commands[${i}].enabled" "${CONFIG_FILE}")
        timeout_value=$(yq eval ".config.commands[${i}].timeout // ${COMMAND_TIMEOUT_DEFAULT}" "${CONFIG_FILE}")

        # Handle null enabled field (default to true)
        if [[ "${enabled}" == "null" ]] || [[ -z "${enabled}" ]]; then
            enabled="true"
        fi

        # Validate command is not null
        if [[ "${command}" == "null" ]] || [[ -z "${command}" ]]; then
            log "ERROR" "Invalid command at index ${i}: command is null or empty"
            ((failure_count++))
            continue
        fi

        # Execute command
        if execute_command "${name}" "${command}" "${enabled}" "${timeout_value}"; then
            ((success_count++))
        else
            ((failure_count++))

            # Check if we should continue on failure
            local continue_on_failure
            continue_on_failure=$(yq eval ".config.commands[${i}].continue_on_failure // true" "${CONFIG_FILE}")

            if [[ "$(echo "${continue_on_failure}" | tr '[:upper:]' '[:lower:]')" != "true" ]]; then
                log "ERROR" "Command failed and continue_on_failure is false, stopping execution"
                break
            fi
        fi
    done

    # Final summary
    log "INFO" "Execution summary: ${success_count} succeeded, ${failure_count} failed"

    # Send notifications if configured
    send_notifications "${success_count}" "${failure_count}"

    # Exit with appropriate code
    if [[ ${failure_count} -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Notification system (placeholder for future enhancement)
send_notifications() {
    local success_count="${1}"
    local failure_count="${2}"

    # Check if notifications are configured
    local notification_enabled
    notification_enabled=$(yq eval '.config.notifications.enabled // false' "${CONFIG_FILE}" 2>/dev/null || echo "false")

    if [[ "$(echo "${notification_enabled}" | tr '[:upper:]' '[:lower:]')" != "true" ]]; then
        return 0
    fi

    log "INFO" "Notifications configured but not yet implemented"
    # TODO: Implement email/webhook notifications based on config
}

# Help function
show_help() {
    cat << 'EOF'
Daily Trading CLI Automation Script

USAGE:
    ./daily.sh [OPTIONS]

OPTIONS:
    --config FILE    Use alternative configuration file (default: daily-config.yaml)
    --dry-run        Validate configuration and show commands without executing
    --help           Show this help message
    --version        Show script version

TESTING:
    ./daily.sh test [TEST_OPTIONS]

TEST OPTIONS:
    --quick          Run quick validation tests only
    --config-only    Test configuration syntax only
    --dependencies   Test system dependencies only
    --cli-commands   Test trading-cli command validation only
    --with-pytest    Include full pytest suite execution
    --test-config FILE  Use alternative test configuration file

EXAMPLES:
    ./daily.sh                              # Run with default configuration
    ./daily.sh --config custom.yaml        # Run with custom configuration
    ./daily.sh --dry-run                    # Test configuration without executing

CONFIGURATION:
    The script reads commands from daily-config.yaml by default.
    See daily-config.yaml for configuration format and examples.

LOGGING:
    Logs are written to logs/daily/daily_YYYYMMDD.log
    Log files are automatically rotated (kept for 30 days)

CRON USAGE:
    # Add to crontab for daily execution at 6 AM
    0 6 * * * /path/to/daily.sh >/dev/null 2>&1

EXIT CODES:
    0 - All commands succeeded
    1 - One or more commands failed
    2 - Another instance already running
    3-8 - Configuration or dependency errors
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            test)
                TEST_MODE=true
                shift
                # Parse test-specific arguments
                parse_test_args "$@"
                return 0
                ;;
            --help)
                show_help
                exit 0
                ;;
            --version)
                echo "${SCRIPT_NAME} version 1.0"
                exit 0
                ;;
            *)
                error_exit "Unknown option: $1. Use --help for usage information." 64
                ;;
        esac
    done
}

# Dry run function for testing configuration
dry_run() {
    log "INFO" "DRY RUN MODE - Configuration validation only"

    validate_dependencies
    validate_config

    local command_count
    command_count=$(yq eval '.config.commands | length' "${CONFIG_FILE}")

    log "INFO" "Configuration is valid with ${command_count} commands:"

    for ((i=0; i<command_count; i++)); do
        local name
        local command
        local enabled
        local timeout_value

        name=$(yq eval ".config.commands[${i}].name // \"Command ${i}\"" "${CONFIG_FILE}")
        command=$(yq eval ".config.commands[${i}].command" "${CONFIG_FILE}")
        enabled=$(yq eval ".config.commands[${i}].enabled" "${CONFIG_FILE}")
        timeout_value=$(yq eval ".config.commands[${i}].timeout // ${COMMAND_TIMEOUT_DEFAULT}" "${CONFIG_FILE}")

        # Handle null enabled field (default to true)
        if [[ "${enabled}" == "null" ]] || [[ -z "${enabled}" ]]; then
            enabled="true"
        fi

        local status="ENABLED"
        if [[ "$(echo "${enabled}" | tr '[:upper:]' '[:lower:]')" != "true" ]]; then
            status="DISABLED"
        fi

        # Validate command security
        if ! validate_command "${command}"; then
            status="SECURITY_VIOLATION"
        fi

        log "INFO" "  [${status}] ${name}: ${command} (timeout: ${timeout_value}s)"
    done

    log "INFO" "Dry run completed successfully"
}

# Check if running in cron environment
is_cron_environment() {
    # Check for typical cron environment indicators
    [[ -z "${TERM:-}" ]] && [[ -z "${DISPLAY:-}" ]] && [[ "${PWD}" != "${HOME}" ]]
}

# Test utility function for tracking test results
track_test_result() {
    local test_name="${1}"
    local success="${2}"
    local total_var="${3}"
    local passed_var="${4}"
    local failed_var="${5}"

    # Increment total tests (using nameref would be ideal but not portable)
    eval "${total_var}=\$((\$${total_var} + 1))"

    if [[ "${success}" == "true" ]]; then
        eval "${passed_var}=\$((\$${passed_var} + 1))"
        log "INFO" "✅ PASSED: ${test_name}"
    else
        eval "${failed_var}=\$((\$${failed_var} + 1))"
        log "ERROR" "❌ FAILED: ${test_name}"
    fi
}

# Quick validation tests
run_quick_tests() {
    local total_var="${1}"
    local passed_var="${2}"
    local failed_var="${3}"

    log "INFO" "Running quick validation tests..."

    # Test 1: Script syntax validation
    if bash -n "${SCRIPT_DIR}/daily.sh"; then
        track_test_result "Script Syntax Validation" "true" "${total_var}" "${passed_var}" "${failed_var}"
    else
        track_test_result "Script Syntax Validation" "false" "${total_var}" "${passed_var}" "${failed_var}"
    fi

    # Test 2: Help system
    if ./daily.sh --help >/dev/null 2>&1; then
        track_test_result "Help System" "true" "${total_var}" "${passed_var}" "${failed_var}"
    else
        track_test_result "Help System" "false" "${total_var}" "${passed_var}" "${failed_var}"
    fi

    # Test 3: Version command
    if ./daily.sh --version >/dev/null 2>&1; then
        track_test_result "Version Command" "true" "${total_var}" "${passed_var}" "${failed_var}"
    else
        track_test_result "Version Command" "false" "${total_var}" "${passed_var}" "${failed_var}"
    fi
}

# Configuration testing
run_config_tests() {
    local config_file="${1}"
    local total_var="${2}"
    local passed_var="${3}"
    local failed_var="${4}"

    log "INFO" "Running configuration tests..."

    # Test 1: Default config exists
    if [[ -f "${CONFIG_FILE}" ]]; then
        track_test_result "Default Config Exists" "true" "${total_var}" "${passed_var}" "${failed_var}"
    else
        track_test_result "Default Config Exists" "false" "${total_var}" "${passed_var}" "${failed_var}"
    fi

    # Test 2: Test config exists (if specified)
    if [[ -f "${config_file}" ]]; then
        track_test_result "Test Config Exists" "true" "${total_var}" "${passed_var}" "${failed_var}"

        # Test 3: YAML syntax validation
        if yq eval '.' "${config_file}" >/dev/null 2>&1; then
            track_test_result "YAML Syntax Validation" "true" "${total_var}" "${passed_var}" "${failed_var}"

            # Test 4: Required fields validation
            local required_fields=("metadata.name" "config.commands")
            local field_test_passed=true

            for field in "${required_fields[@]}"; do
                if ! yq eval ".${field}" "${config_file}" >/dev/null 2>&1; then
                    field_test_passed=false
                    break
                fi
            done

            track_test_result "Required Fields Validation" "${field_test_passed}" "${total_var}" "${passed_var}" "${failed_var}"
        else
            track_test_result "YAML Syntax Validation" "false" "${total_var}" "${passed_var}" "${failed_var}"
        fi
    else
        track_test_result "Test Config Exists" "false" "${total_var}" "${passed_var}" "${failed_var}"
    fi
}

# Dependency testing
run_dependency_tests() {
    local total_var="${1}"
    local passed_var="${2}"
    local failed_var="${3}"

    log "INFO" "Running dependency tests..."

    # Test required commands
    local required_commands=("yq" "poetry" "timeout")
    for cmd in "${required_commands[@]}"; do
        if command -v "${cmd}" >/dev/null 2>&1; then
            track_test_result "Dependency: ${cmd}" "true" "${total_var}" "${passed_var}" "${failed_var}"
        else
            track_test_result "Dependency: ${cmd}" "false" "${total_var}" "${passed_var}" "${failed_var}"
        fi
    done

    # Test trading-cli availability
    if poetry run trading-cli --help >/dev/null 2>&1; then
        track_test_result "Trading CLI Availability" "true" "${total_var}" "${passed_var}" "${failed_var}"
    else
        track_test_result "Trading CLI Availability" "false" "${total_var}" "${passed_var}" "${failed_var}"
    fi
}

# CLI command validation testing
run_cli_command_tests() {
    local config_file="${1}"
    local total_var="${2}"
    local passed_var="${3}"
    local failed_var="${4}"

    log "INFO" "Running CLI command validation tests..."

    if [[ ! -f "${config_file}" ]]; then
        track_test_result "CLI Command Tests" "false" "${total_var}" "${passed_var}" "${failed_var}"
        return
    fi

    # Get command count
    local command_count
    command_count=$(yq eval '.config.commands | length' "${config_file}")

    # Test each enabled command for security validation
    local all_commands_valid=true
    for ((i=0; i<command_count; i++)); do
        local command
        local enabled
        command=$(yq eval ".config.commands[${i}].command" "${config_file}")
        enabled=$(yq eval ".config.commands[${i}].enabled" "${config_file}")

        # Handle null enabled field (default to true)
        if [[ "${enabled}" == "null" ]] || [[ -z "${enabled}" ]]; then
            enabled="true"
        fi

        # Skip disabled commands
        if [[ "$(echo "${enabled}" | tr '[:upper:]' '[:lower:]')" != "true" ]]; then
            continue
        fi

        if [[ "${command}" == "null" ]] || [[ -z "${command}" ]]; then
            continue
        fi

        if ! validate_command "${command}"; then
            all_commands_valid=false
            log "ERROR" "Invalid enabled command at index ${i}: ${command}"
        fi
    done

    track_test_result "CLI Command Security Validation" "${all_commands_valid}" "${total_var}" "${passed_var}" "${failed_var}"

    # Test dry-run execution of enabled commands
    local dry_run_success=true
    if ./daily.sh --config "${config_file}" --dry-run >/dev/null 2>&1; then
        track_test_result "Dry Run Execution" "true" "${total_var}" "${passed_var}" "${failed_var}"
    else
        track_test_result "Dry Run Execution" "false" "${total_var}" "${passed_var}" "${failed_var}"
    fi
}

# Comprehensive testing including pytest
run_comprehensive_tests() {
    local config_file="${1}"
    local total_var="${2}"
    local passed_var="${3}"
    local failed_var="${4}"

    log "INFO" "Running comprehensive tests including pytest..."

    # Run all other test categories first
    run_dependency_tests "${total_var}" "${passed_var}" "${failed_var}"
    run_config_tests "${config_file}" "${total_var}" "${passed_var}" "${failed_var}"
    run_cli_command_tests "${config_file}" "${total_var}" "${passed_var}" "${failed_var}"

    # Run pytest suite
    log "INFO" "Executing pytest suite..."
    if poetry run pytest tests/ --maxfail=5 -q >/dev/null 2>&1; then
        track_test_result "Pytest Suite" "true" "${total_var}" "${passed_var}" "${failed_var}"
    else
        track_test_result "Pytest Suite" "false" "${total_var}" "${passed_var}" "${failed_var}"
    fi
}

# Generate test report
generate_test_report() {
    local total_tests="${1}"
    local passed_tests="${2}"
    local failed_tests="${3}"

    log "INFO" "========================================="
    log "INFO" "DAILY.SH TEST EXECUTION SUMMARY"
    log "INFO" "========================================="
    log "INFO" "Total Tests: ${total_tests}"
    log "INFO" "✅ Passed: ${passed_tests}"
    log "INFO" "❌ Failed: ${failed_tests}"

    if [[ ${failed_tests} -gt 0 ]]; then
        log "ERROR" "Some tests failed. Check log for details: ${TEST_LOG_FILE}"
    else
        log "INFO" "All tests passed successfully!"
    fi

    log "INFO" "Test log: ${TEST_LOG_FILE}"
}

# Test argument parsing
parse_test_args() {
    local TEST_QUICK=false
    local TEST_CONFIG_ONLY=false
    local TEST_DEPENDENCIES=false
    local TEST_CLI_COMMANDS=false
    local TEST_WITH_PYTEST=false
    local TEST_CONFIG_CUSTOM=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick)
                TEST_QUICK=true
                shift
                ;;
            --config-only)
                TEST_CONFIG_ONLY=true
                shift
                ;;
            --dependencies)
                TEST_DEPENDENCIES=true
                shift
                ;;
            --cli-commands)
                TEST_CLI_COMMANDS=true
                shift
                ;;
            --with-pytest)
                TEST_WITH_PYTEST=true
                shift
                ;;
            --test-config)
                TEST_CONFIG_CUSTOM="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                error_exit "Unknown test option: $1. Use --help for usage information." 64
                ;;
        esac
    done

    # Set test mode flag for global use
    TEST_MODE=true

    # Execute test mode with parsed options
    run_test_mode "${TEST_QUICK}" "${TEST_CONFIG_ONLY}" "${TEST_DEPENDENCIES}" \
                  "${TEST_CLI_COMMANDS}" "${TEST_WITH_PYTEST}" "${TEST_CONFIG_CUSTOM}"
}

# Test mode execution
run_test_mode() {
    local test_quick="${1}"
    local test_config_only="${2}"
    local test_dependencies="${3}"
    local test_cli_commands="${4}"
    local test_with_pytest="${5}"
    local test_config_custom="${6}"

    # Initialize test logging
    init_test_logging

    # Override LOG_FILE for test mode
    LOG_FILE="${TEST_LOG_FILE}"

    log "INFO" "Starting daily.sh testing mode"

    local test_config="${TEST_CONFIG_FILE}"
    if [[ -n "${test_config_custom}" ]]; then
        test_config="${test_config_custom}"
    fi

    local total_tests=0
    local passed_tests=0
    local failed_tests=0

    # Run selected test categories
    if [[ "${test_quick}" == "true" ]]; then
        run_quick_tests total_tests passed_tests failed_tests
    elif [[ "${test_config_only}" == "true" ]]; then
        run_config_tests "${test_config}" total_tests passed_tests failed_tests
    elif [[ "${test_dependencies}" == "true" ]]; then
        run_dependency_tests total_tests passed_tests failed_tests
    elif [[ "${test_cli_commands}" == "true" ]]; then
        run_cli_command_tests "${test_config}" total_tests passed_tests failed_tests
    elif [[ "${test_with_pytest}" == "true" ]]; then
        run_comprehensive_tests "${test_config}" total_tests passed_tests failed_tests
    else
        # Default: run all tests except pytest
        run_dependency_tests total_tests passed_tests failed_tests
        run_config_tests "${test_config}" total_tests passed_tests failed_tests
        run_cli_command_tests "${test_config}" total_tests passed_tests failed_tests
    fi

    # Generate test report
    generate_test_report "${total_tests}" "${passed_tests}" "${failed_tests}"

    # Exit with appropriate code
    if [[ ${failed_tests} -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Initialize test logging
init_test_logging() {
    mkdir -p "${LOG_DIR}"

    {
        echo "========================================="
        echo "Daily.sh Testing Mode Started"
        echo "Date: $(date '+%Y-%m-%d %H:%M:%S %Z')"
        echo "PID: $$"
        echo "========================================="
    } > "${TEST_LOG_FILE}"
}

# Main entry point
main_entry() {
    # Initialize variables
    local DRY_RUN=false
    local TEST_MODE=false

    # Set working directory to script directory
    cd "${SCRIPT_DIR}"

    # Parse command line arguments
    parse_args "$@"

    # Handle test mode (already handled in parse_args via return)
    if [[ "${TEST_MODE}" == "true" ]]; then
        return 0  # Test mode handled in parse_args
    fi

    # Handle dry run mode
    if [[ "${DRY_RUN}" == "true" ]]; then
        dry_run
        exit 0
    fi

    # Execute main function
    main
}

# Execute main entry point with all arguments
main_entry "$@"
