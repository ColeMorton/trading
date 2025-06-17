#!/usr/bin/env python3
"""
Cleanup script to remove CSV and JSON files older than 1 week.
Excludes files in csv/strategies/ directory and patterns listed in .cleanupignore file.
"""

import argparse
import fnmatch
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path


def load_ignore_patterns(base_path: Path) -> list:
    """Load patterns from .cleanupignore file."""
    ignore_file = base_path / ".cleanupignore"
    patterns = []
    
    if ignore_file.exists():
        try:
            with open(ignore_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        patterns.append(line)
        except Exception as e:
            print(f"Warning: Could not read .cleanupignore file: {e}")
    
    return patterns


def is_ignored(file_path: Path, base_path: Path, ignore_patterns: list) -> bool:
    """Check if a file should be ignored based on patterns."""
    relative_path = file_path.relative_to(base_path)
    relative_path_str = str(relative_path)
    
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(relative_path_str, pattern):
            return True
        # Also check against the file name only
        if fnmatch.fnmatch(file_path.name, pattern):
            return True
    
    return False


def cleanup_old_files(
    base_path: str, exclude_dirs: list, max_age_days: int = 7, dry_run: bool = False
):
    """Remove CSV and JSON files older than max_age_days from csv/ and json/ directories only."""
    cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
    removed_count = 0
    total_size_removed = 0

    base_path = Path(base_path)
    exclude_paths = [base_path / exclude_dir for exclude_dir in exclude_dirs]
    
    # Load ignore patterns from .cleanupignore file
    ignore_patterns = load_ignore_patterns(base_path)

    # Only scan csv/ and json/ directories
    target_dirs = [base_path / "csv", base_path / "json"]
    target_dirs = [d for d in target_dirs if d.exists()]

    print(
        f"{'DRY RUN: ' if dry_run else ''}Cleaning up files older than {max_age_days} days..."
    )
    print(f"Base path: {base_path}")
    print(f"Target directories: {[str(d.relative_to(base_path)) for d in target_dirs]}")
    print(f"Excluding directories: {exclude_dirs}")
    if ignore_patterns:
        print(f"Ignore patterns: {ignore_patterns}")
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

            for file in files:
                if file.endswith((".csv", ".json")):
                    file_path = current_path / file
                    
                    # Check if file should be ignored
                    if is_ignored(file_path, base_path, ignore_patterns):
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
        default=["csv/strategies"],
        help="Directories to exclude from cleanup (default: csv/strategies)",
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

    args = parser.parse_args()

    if not Path(args.base_path).exists():
        print(f"Error: Base path {args.base_path} does not exist")
        sys.exit(1)

    try:
        removed_count, total_size = cleanup_old_files(
            args.base_path, args.exclude, args.max_age, args.dry_run
        )

        if args.dry_run:
            print(f"\nTo actually perform cleanup, run without --dry-run flag")

    except KeyboardInterrupt:
        print("\nCleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error during cleanup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
