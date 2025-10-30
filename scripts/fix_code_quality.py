#!/usr/bin/env python3
"""
Gradual Code Quality Improvement Script

This script helps systematically fix Ruff linting issues by:
1. Categorizing issues by severity and type
2. Allowing incremental fixes by category
3. Tracking progress over time
4. Providing safe auto-fixes where possible

Usage:
    python scripts/fix_code_quality.py --analyze              # Show issue breakdown
    python scripts/fix_code_quality.py --fix-safe             # Auto-fix safe issues
    python scripts/fix_code_quality.py --fix-category F841    # Fix specific category
    python scripts/fix_code_quality.py --fix-file app/api/   # Fix specific directory
    python scripts/fix_code_quality.py --track               # Track progress over time
"""

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


# Color codes for terminal output
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


# Issue categories with descriptions and priority
ISSUE_CATEGORIES = {
    # High Priority - Likely bugs
    "F": {
        "name": "Pyflakes (Errors)",
        "priority": 1,
        "safe_autofix": False,
        "description": "Undefined variables, unused imports, etc.",
    },
    # Medium Priority - Code quality
    "UP": {
        "name": "pyupgrade (Modernization)",
        "priority": 2,
        "safe_autofix": True,
        "description": "Modernize Python syntax (e.g., Dict → dict)",
    },
    "B": {
        "name": "bugbear (Bug Prevention)",
        "priority": 2,
        "safe_autofix": False,
        "description": "Common bugs and anti-patterns",
    },
    # Lower Priority - Style
    "SIM": {
        "name": "simplify (Code Simplification)",
        "priority": 3,
        "safe_autofix": False,
        "description": "Simplify code patterns",
    },
    "PTH": {
        "name": "pathlib (Path Usage)",
        "priority": 3,
        "safe_autofix": False,
        "description": "Use pathlib instead of os.path",
    },
    "RET": {
        "name": "return (Return Statements)",
        "priority": 3,
        "safe_autofix": False,
        "description": "Improve return statement patterns",
    },
    "E": {
        "name": "pycodestyle (Style Errors)",
        "priority": 4,
        "safe_autofix": True,
        "description": "PEP 8 style violations",
    },
    "W": {
        "name": "pycodestyle (Style Warnings)",
        "priority": 4,
        "safe_autofix": True,
        "description": "PEP 8 style warnings",
    },
    "RUF": {
        "name": "Ruff-specific",
        "priority": 3,
        "safe_autofix": False,
        "description": "Ruff-specific rules",
    },
}


def run_ruff_check(
    path: str = ".", fix: bool = False, output_format: str = "json"
) -> subprocess.CompletedProcess:
    """Run ruff check and return results."""
    cmd = ["poetry", "run", "ruff", "check", path]

    if fix:
        cmd.append("--fix")

    if output_format == "json":
        cmd.extend(["--output-format", "json"])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            check=False,
        )
        return result
    except Exception as e:
        print(f"{Colors.RED}Error running ruff: {e}{Colors.RESET}")
        sys.exit(1)


def parse_ruff_output(output: str) -> list[dict]:
    """Parse JSON output from ruff."""
    if not output.strip():
        return []

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        print(
            f"{Colors.YELLOW}Warning: Could not parse ruff output as JSON{Colors.RESET}"
        )
        return []


def categorize_issues(issues: list[dict]) -> dict[str, list[dict]]:
    """Categorize issues by rule code prefix."""
    categorized = defaultdict(list)

    for issue in issues:
        code = issue.get("code", "UNKNOWN")
        # Get the prefix (e.g., "F" from "F841")
        prefix = (
            code.split(code.lstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))[0]
            if code
            else "UNKNOWN"
        )
        categorized[prefix].append(issue)

    return categorized


def analyze_issues() -> dict:
    """Analyze all issues and return statistics."""
    print(f"{Colors.BLUE}Analyzing code quality issues...{Colors.RESET}\n")

    result = run_ruff_check(".", fix=False, output_format="json")
    issues = parse_ruff_output(result.stdout)

    if not issues:
        print(
            f"{Colors.GREEN}✅ No issues found! Code quality is excellent.{Colors.RESET}"
        )
        return {}

    categorized = categorize_issues(issues)

    # Count by specific rule code
    code_counts = defaultdict(int)
    for issue in issues:
        code_counts[issue.get("code", "UNKNOWN")] += 1

    # Count by file
    file_counts = defaultdict(int)
    for issue in issues:
        file_counts[issue.get("filename", "unknown")] += 1

    stats = {
        "total": len(issues),
        "by_category": {k: len(v) for k, v in categorized.items()},
        "by_code": dict(code_counts),
        "by_file": dict(file_counts),
        "categorized": categorized,
    }

    return stats


def print_analysis(stats: dict):
    """Print a formatted analysis of issues."""
    if not stats:
        return

    print(f"{Colors.BOLD}=== Code Quality Analysis ==={Colors.RESET}\n")
    print(f"Total issues: {Colors.YELLOW}{stats['total']}{Colors.RESET}\n")

    # Print by category
    print(f"{Colors.BOLD}Issues by Category:{Colors.RESET}")
    sorted_categories = sorted(
        stats["by_category"].items(),
        key=lambda x: (
            ISSUE_CATEGORIES.get(x[0], {}).get("priority", 999),
            -x[1],
        ),
    )

    for prefix, count in sorted_categories:
        cat_info = ISSUE_CATEGORIES.get(prefix, {})
        name = cat_info.get("name", prefix)
        priority = cat_info.get("priority", "?")
        safe = "✓" if cat_info.get("safe_autofix") else "✗"

        color = (
            Colors.RED
            if priority == 1
            else Colors.YELLOW
            if priority == 2
            else Colors.CYAN
        )
        print(
            f"  {color}[{prefix}]{Colors.RESET} {name:30} {count:5} issues  (Priority: {priority}, Auto-fix: {safe})"
        )

    print()

    # Print top 10 specific issues
    print(f"{Colors.BOLD}Top 10 Most Common Issues:{Colors.RESET}")
    sorted_codes = sorted(stats["by_code"].items(), key=lambda x: -x[1])[:10]
    for code, count in sorted_codes:
        print(f"  {Colors.CYAN}{code:10}{Colors.RESET} {count:5} occurrences")

    print()

    # Print top 10 files with most issues
    print(f"{Colors.BOLD}Top 10 Files with Most Issues:{Colors.RESET}")
    sorted_files = sorted(stats["by_file"].items(), key=lambda x: -x[1])[:10]
    for filename, count in sorted_files:
        short_name = filename[-60:] if len(filename) > 60 else filename
        print(f"  {Colors.MAGENTA}{short_name:62}{Colors.RESET} {count:3} issues")

    print()

    # Provide recommendations
    print(f"{Colors.BOLD}Recommendations:{Colors.RESET}")
    for prefix, count in sorted_categories[:3]:
        cat_info = ISSUE_CATEGORIES.get(prefix, {})
        if cat_info.get("safe_autofix"):
            print(
                f"  {Colors.GREEN}✓{Colors.RESET} Run: {Colors.CYAN}python scripts/fix_code_quality.py --fix-category {prefix}{Colors.RESET}"
            )
        else:
            print(
                f"  {Colors.YELLOW}!{Colors.RESET} Review: {Colors.CYAN}python scripts/fix_code_quality.py --show-category {prefix}{Colors.RESET}"
            )


def fix_safe_issues():
    """Auto-fix issues that are safe to fix automatically."""
    print(f"{Colors.BLUE}Fixing safe issues with --unsafe-fixes...{Colors.RESET}\n")

    # Run with unsafe fixes enabled for more comprehensive fixes
    result = subprocess.run(
        ["poetry", "run", "ruff", "check", "--fix", "--unsafe-fixes", "app", "tests"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
        check=False,
    )

    if result.returncode == 0:
        print(f"{Colors.GREEN}✅ All safe issues fixed!{Colors.RESET}")
    else:
        print(
            f"{Colors.YELLOW}Fixed some issues. Run analyze to see remaining.{Colors.RESET}"
        )

    # Show what was fixed
    if result.stdout:
        print(f"\n{result.stdout}")


def fix_category(category: str):
    """Fix issues in a specific category."""
    print(f"{Colors.BLUE}Fixing category: {category}...{Colors.RESET}\n")

    # First, get all issues in this category
    result = run_ruff_check(".", fix=False, output_format="json")
    issues = parse_ruff_output(result.stdout)
    categorized = categorize_issues(issues)

    if category not in categorized:
        print(f"{Colors.YELLOW}No issues found in category: {category}{Colors.RESET}")
        return

    cat_issues = categorized[category]
    print(f"Found {len(cat_issues)} issues in category {category}")

    # Get all unique codes in this category
    codes = {issue.get("code") for issue in cat_issues}

    print(f"{Colors.CYAN}Issue types in this category:{Colors.RESET}")
    for code in sorted(codes):
        count = sum(1 for i in cat_issues if i.get("code") == code)
        print(f"  {code}: {count} occurrences")

    print(f"\n{Colors.YELLOW}Attempting to fix with --unsafe-fixes...{Colors.RESET}")

    # Try to fix with select
    result = subprocess.run(
        [
            "poetry",
            "run",
            "ruff",
            "check",
            "--fix",
            "--unsafe-fixes",
            "--select",
            category,
            "app",
            "tests",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
        check=False,
    )

    print(f"{Colors.GREEN}✅ Attempted fixes for category {category}{Colors.RESET}")
    print(
        f"{Colors.CYAN}Run 'python scripts/fix_code_quality.py --analyze' to see results{Colors.RESET}"
    )


def fix_file(path: str):
    """Fix issues in a specific file or directory."""
    print(f"{Colors.BLUE}Fixing issues in: {path}...{Colors.RESET}\n")

    result = subprocess.run(
        ["poetry", "run", "ruff", "check", "--fix", "--unsafe-fixes", path],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
        check=False,
    )

    if result.returncode == 0:
        print(f"{Colors.GREEN}✅ Fixed issues in {path}{Colors.RESET}")
    else:
        print(
            f"{Colors.YELLOW}Fixed some issues in {path}. Some may remain.{Colors.RESET}"
        )


def show_category(category: str):
    """Show all issues in a specific category."""
    result = run_ruff_check(".", fix=False, output_format="json")
    issues = parse_ruff_output(result.stdout)
    categorized = categorize_issues(issues)

    if category not in categorized:
        print(f"{Colors.YELLOW}No issues found in category: {category}{Colors.RESET}")
        return

    cat_issues = categorized[category]
    print(
        f"\n{Colors.BOLD}Issues in category {category}:{Colors.RESET} ({len(cat_issues)} total)\n"
    )

    # Group by code
    by_code = defaultdict(list)
    for issue in cat_issues:
        by_code[issue.get("code")].append(issue)

    for code in sorted(by_code.keys()):
        code_issues = by_code[code]
        print(f"{Colors.CYAN}{code}{Colors.RESET} ({len(code_issues)} occurrences):")

        # Show first 5 examples
        for issue in code_issues[:5]:
            filename = issue.get("filename", "unknown")
            line = issue.get("location", {}).get("row", "?")
            message = issue.get("message", "")
            print(f"  {filename}:{line} - {message}")

        if len(code_issues) > 5:
            print(f"  ... and {len(code_issues) - 5} more")
        print()


def track_progress():
    """Track progress over time."""
    progress_file = Path("scripts/.code_quality_progress.json")

    # Get current stats
    stats = analyze_issues()
    if not stats:
        print(f"{Colors.GREEN}No issues to track!{Colors.RESET}")
        return

    # Load historical data
    history = []
    if progress_file.exists():
        with open(progress_file) as f:
            history = json.load(f)

    # Add current snapshot
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "total": stats["total"],
        "by_category": stats["by_category"],
    }
    history.append(snapshot)

    # Save updated history
    with open(progress_file, "w") as f:
        json.dump(history, f, indent=2)

    print(f"{Colors.BOLD}Progress Tracking:{Colors.RESET}\n")

    if len(history) > 1:
        prev = history[-2]
        curr = history[-1]

        diff = curr["total"] - prev["total"]
        color = Colors.GREEN if diff < 0 else Colors.RED if diff > 0 else Colors.YELLOW

        print(f"Previous: {prev['total']} issues")
        print(f"Current:  {curr['total']} issues")
        print(f"Change:   {color}{diff:+d}{Colors.RESET} issues\n")

        # Show category changes
        print(f"{Colors.BOLD}Changes by Category:{Colors.RESET}")
        all_cats = set(prev["by_category"].keys()) | set(curr["by_category"].keys())
        for cat in sorted(all_cats):
            prev_count = prev["by_category"].get(cat, 0)
            curr_count = curr["by_category"].get(cat, 0)
            cat_diff = curr_count - prev_count

            if cat_diff != 0:
                color = Colors.GREEN if cat_diff < 0 else Colors.RED
                print(
                    f"  {cat:5} {prev_count:5} → {curr_count:5}  {color}{cat_diff:+d}{Colors.RESET}"
                )
    else:
        print("First tracking snapshot recorded!")

    print(f"\n{Colors.CYAN}Progress saved to: {progress_file}{Colors.RESET}")


def main():
    parser = argparse.ArgumentParser(
        description="Gradually fix code quality issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--analyze", action="store_true", help="Analyze and categorize all issues"
    )
    parser.add_argument("--fix-safe", action="store_true", help="Auto-fix safe issues")
    parser.add_argument(
        "--fix-category",
        metavar="CATEGORY",
        help="Fix issues in a specific category (e.g., F, UP, B)",
    )
    parser.add_argument(
        "--fix-file", metavar="PATH", help="Fix issues in a specific file or directory"
    )
    parser.add_argument(
        "--show-category", metavar="CATEGORY", help="Show all issues in a category"
    )
    parser.add_argument("--track", action="store_true", help="Track progress over time")

    args = parser.parse_args()

    # If no arguments, show help and analyze
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n" + "=" * 80 + "\n")
        stats = analyze_issues()
        print_analysis(stats)
        return

    if args.analyze:
        stats = analyze_issues()
        print_analysis(stats)

    if args.fix_safe:
        fix_safe_issues()

    if args.fix_category:
        fix_category(args.fix_category)

    if args.fix_file:
        fix_file(args.fix_file)

    if args.show_category:
        show_category(args.show_category)

    if args.track:
        track_progress()


if __name__ == "__main__":
    main()
