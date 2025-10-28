#!/usr/bin/env python3
"""
Cleanup script to remove CSV and JSON files older than specified age.

IMPORTANT: This script ONLY removes files explicitly listed in .cleanupwhitelist
Always run with --dry-run first to see what would be deleted.

SAFETY FEATURES:
- WHITELIST APPROACH: Only files matching patterns in .cleanupwhitelist are cleaned
- Interactive environments: Prompts for confirmation before deletion
- Non-interactive (CI/pre-commit): Automatically runs in --dry-run mode for safety
- Use --auto-confirm to skip confirmation in automated environments

Protected by design:
- Root directory files (script only scans data/outputs/ and json/ subdirectories)
- Dot directories (.claude, .git, etc.) - completely skipped
- data/raw/strategies/ directory (active portfolio directory - protected)
- ALL files not explicitly whitelisted in .cleanupwhitelist

Safe to clean (when explicitly whitelisted):
- data/raw/price_data/ files (regenerated automatically)
- data/outputs/*/equity_data/ files (generated during analysis)
- data/outputs/cache/ directory (automatically generated)
- data/outputs/experimental/temp/ directory (temporary files)
- Files with temp/tmp in name (temporary files)
"""

import argparse
from datetime import datetime
import fnmatch
import os
from pathlib import Path
import sys
import time


def is_interactive_environment() -> bool:
    """Check if we're running in an interactive environment."""
    # Check if stdin is a TTY (terminal)
    if not sys.stdin.isatty():
        return False

    # Check for common non-interactive environment variables
    non_interactive_vars = [
        "CI",  # Generic CI indicator
        "GITHUB_ACTIONS",  # GitHub Actions
        "PRE_COMMIT",  # Pre-commit hook
        "BUILD_ID",  # Jenkins
        "TRAVIS",  # Travis CI
        "CIRCLECI",  # Circle CI
    ]

    for var in non_interactive_vars:
        if os.environ.get(var):
            return False

    return True


def load_whitelist_patterns(base_path: Path) -> list:
    """Load patterns from .cleanupwhitelist file - ONLY these files are safe to clean."""
    whitelist_file = base_path / ".cleanupwhitelist"
    patterns = []

    if whitelist_file.exists():
        try:
            with open(whitelist_file) as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except Exception as e:
            print(f"Warning: Could not read .cleanupwhitelist file: {e}")
    else:
        print(
            "Warning: .cleanupwhitelist file not found. No files will be cleaned for safety."
        )

    return patterns


def is_whitelisted(file_path: Path, base_path: Path, whitelist_patterns: list) -> bool:
    """Check if a file is whitelisted for cleanup based on patterns."""
    relative_path = file_path.relative_to(base_path)
    relative_path_str = str(relative_path)

    for pattern in whitelist_patterns:
        if fnmatch.fnmatch(relative_path_str, pattern):
            return True
        # Also check against the file name only
        if fnmatch.fnmatch(file_path.name, pattern):
            return True

    return False


def cleanup_old_files(
    base_path: str, exclude_dirs: list, max_age_days: int = 7, dry_run: bool = False
):
    """Remove ONLY whitelisted files older than max_age_days from data/outputs/ and json/ directories."""
    cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
    removed_count = 0
    total_size_removed = 0

    base_path = Path(base_path)
    exclude_paths = [base_path / exclude_dir for exclude_dir in exclude_dirs]

    # Load whitelist patterns from .cleanupwhitelist file - ONLY these files can be cleaned
    whitelist_patterns = load_whitelist_patterns(base_path)

    if not whitelist_patterns:
        print("⚠️  No whitelist patterns found. Exiting for safety.")
        return 0, 0

    # Only scan data/outputs/ and json/ directories (not root or other directories)
    target_dirs = [base_path / "csv", base_path / "json"]
    target_dirs = [d for d in target_dirs if d.exists() and d.is_dir()]

    print(
        f"{'DRY RUN: ' if dry_run else ''}Cleaning up WHITELISTED files older than {max_age_days} days..."
    )
    print(f"Base path: {base_path}")
    print(f"Target directories: {[str(d.relative_to(base_path)) for d in target_dirs]}")
    print(f"Excluding directories: {exclude_dirs}")
    if whitelist_patterns:
        print(f"Whitelist patterns (ONLY these can be cleaned): {whitelist_patterns}")
    print(f"Cutoff date: {datetime.fromtimestamp(cutoff_time)}")
    print("-" * 60)

    for target_dir in target_dirs:
        for root, dirs, files in os.walk(target_dir):
            current_path = Path(root)

            # Skip excluded directories
            if any(
                current_path.is_relative_to(exclude_path)
                for exclude_path in exclude_paths
            ):
                continue

            # Skip dot directories (like .claude, .git, etc.)
            if any(part.startswith(".") for part in current_path.parts):
                continue

            for file in files:
                if file.endswith((".csv", ".json")):
                    file_path = current_path / file

                    # ONLY clean files that are explicitly whitelisted
                    if not is_whitelisted(file_path, base_path, whitelist_patterns):
                        continue

                    try:
                        stat_info = file_path.stat()
                        if stat_info.st_mtime < cutoff_time:
                            file_age_days = (time.time() - stat_info.st_mtime) / (
                                24 * 60 * 60
                            )
                            file_size = stat_info.st_size

                            if dry_run:
                                print(
                                    f"Would remove: {file_path} (age: {file_age_days:.1f} days, size: {file_size} bytes)"
                                )
                            else:
                                file_path.unlink()
                                print(
                                    f"Removed: {file_path} (age: {file_age_days:.1f} days)"
                                )

                            removed_count += 1
                            total_size_removed += file_size

                    except (OSError, FileNotFoundError) as e:
                        print(f"Warning: Could not process {file_path}: {e}")
                        continue

    print("-" * 60)
    action = "Would remove" if dry_run else "Removed"
    print(
        f"Cleanup {'preview' if dry_run else 'complete'}: {action} {removed_count} files, "
        f"{total_size_removed / (1024*1024):.1f}MB {'would be ' if dry_run else ''}freed"
    )

    return removed_count, total_size_removed


def main():
    parser = argparse.ArgumentParser(description="Clean up old CSV and JSON files")
    parser.add_argument(
        "--base-path",
        default="/Users/colemorton/Projects/trading",
        help="Base directory to clean (default: current trading project)",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=["data/raw/strategies"],
        help="Directories to exclude from cleanup (default: data/raw/strategies)",
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=7,
        help="Maximum age in days for files to keep (default: 7)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--auto-confirm",
        action="store_true",
        help="Skip interactive confirmation (for automated environments)",
    )

    args = parser.parse_args()

    if not Path(args.base_path).exists():
        print(f"Error: Base path {args.base_path} does not exist")
        sys.exit(1)

    # Safety warning for non-dry-run mode
    if not args.dry_run:
        print("⚠️  WARNING: You are about to permanently delete files!")
        print("⚠️  This action cannot be undone.")
        print("⚠️  Consider running with --dry-run first to preview changes.")

        # Check if we need confirmation
        if args.auto_confirm:
            print("✅ Auto-confirmed (--auto-confirm flag)")
        elif not is_interactive_environment():
            print(
                "🔧 Non-interactive environment detected - running in dry-run mode for safety"
            )
            print("   Use --auto-confirm flag to skip this safety check")
            args.dry_run = True  # Force dry-run in non-interactive environments
        else:
            # Interactive environment - prompt for confirmation
            try:
                response = input("\nContinue? (yes/no): ").lower().strip()
                if response not in ["yes", "y"]:
                    print("Cleanup cancelled.")
                    sys.exit(0)
            except (EOFError, KeyboardInterrupt):
                print("\nCleanup cancelled.")
                sys.exit(0)

    try:
        removed_count, total_size = cleanup_old_files(
            args.base_path, args.exclude, args.max_age, args.dry_run
        )

        if args.dry_run:
            print("\nTo actually perform cleanup, run without --dry-run flag")

    except KeyboardInterrupt:
        print("\nCleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during cleanup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
