#!/usr/bin/env python3
"""
Phase 2 CSV Migration Script

Migrates CSV files to consistent Base/Extended schemas based on directory purpose:
- csv/portfolios/ -> Base Schema (58 columns, no Allocation/Stop Loss)
- csv/portfolios_filtered/ -> Extended Schema (60 columns + Metric Type = 61 total)
- csv/portfolios_best/ -> Extended Schema with Metric Type concatenation preserved
- csv/strategies/ -> No changes (already compliant)

This script implements the Phase 2 migration plan with data integrity preservation.
"""

import csv
import json
import logging
import os
import shutil

# Add project root to path
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.append(".")

from app.tools.portfolio.base_extended_schemas import (
    BasePortfolioSchema,
    ExtendedPortfolioSchema,
    FilteredPortfolioSchema,
    SchemaTransformer,
    SchemaType,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("phase2_migration.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class CSVMigrationManager:
    """Manages CSV file migration to standardized schemas."""

    def __init__(self, dry_run: bool = True):
        """Initialize migration manager.

        Args:
            dry_run: If True, simulates migration without making changes
        """
        self.dry_run = dry_run
        self.transformer = SchemaTransformer()
        self.backup_dir = (
            Path("backups")
            / f"phase2_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.results = {
            "migration_started": datetime.now().isoformat(),
            "dry_run": dry_run,
            "directories_processed": {},
            "files_migrated": 0,
            "files_skipped": 0,
            "errors": [],
        }

        if not dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Backup directory created: {self.backup_dir}")

    def read_csv_file(
        self, file_path: Path
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Read CSV file and return data with error handling.

        Args:
            file_path: Path to CSV file

        Returns:
            Tuple of (data_rows, error_message)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                data = list(reader)
                return data, None
        except Exception as e:
            error_msg = f"Failed to read {file_path}: {str(e)}"
            logger.error(error_msg)
            return [], error_msg

    def write_csv_file(
        self, file_path: Path, data: List[Dict[str, Any]], target_schema: SchemaType
    ) -> bool:
        """Write CSV file with proper schema compliance.

        Args:
            file_path: Path to write CSV file
            data: Data to write
            target_schema: Target schema type

        Returns:
            True if successful, False otherwise
        """
        if not data:
            logger.warning(f"No data to write for {file_path}")
            return False

        try:
            # Get column order from target schema
            if target_schema == SchemaType.BASE:
                column_order = BasePortfolioSchema.get_column_names()
            elif target_schema == SchemaType.EXTENDED:
                column_order = ExtendedPortfolioSchema.get_column_names()
            elif target_schema == SchemaType.FILTERED:
                column_order = FilteredPortfolioSchema.get_column_names()
            else:
                # Use existing columns if unknown schema
                column_order = list(data[0].keys())

            # Ensure all rows have the same columns
            normalized_data = []
            for row in data:
                normalized_row = {}
                for col in column_order:
                    normalized_row[col] = row.get(col, None)
                normalized_data.append(normalized_row)

            with open(file_path, "w", newline="", encoding="utf-8") as f:
                if normalized_data:
                    writer = csv.DictWriter(f, fieldnames=column_order)
                    writer.writeheader()
                    writer.writerows(normalized_data)
                    return True
        except Exception as e:
            error_msg = f"Failed to write {file_path}: {str(e)}"
            logger.error(error_msg)
            self.results["errors"].append(error_msg)
            return False

        return False

    def backup_file(self, file_path: Path) -> bool:
        """Create backup of file before migration.

        Args:
            file_path: Path to file to backup

        Returns:
            True if backup successful, False otherwise
        """
        if self.dry_run:
            return True

        try:
            backup_path = self.backup_dir / file_path.relative_to(".")
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Backed up {file_path} to {backup_path}")
            return True
        except Exception as e:
            error_msg = f"Failed to backup {file_path}: {str(e)}"
            logger.error(error_msg)
            self.results["errors"].append(error_msg)
            return False

    def migrate_to_base_schema(self, file_path: Path) -> bool:
        """Migrate file to Base schema (remove Allocation/Stop Loss columns).

        Args:
            file_path: Path to CSV file

        Returns:
            True if migration successful, False otherwise
        """
        logger.info(f"Migrating {file_path} to Base schema")

        # Read current file
        data, error = self.read_csv_file(file_path)
        if error:
            return False

        if not data:
            logger.warning(f"Empty file: {file_path}")
            return True

        # Detect current schema
        current_schema = self.transformer.detect_schema_type(data[0])
        logger.debug(f"Current schema for {file_path}: {current_schema}")

        # Transform to base schema
        migrated_data = []
        for row in data:
            base_row = self.transformer.normalize_to_schema(row, SchemaType.BASE)
            migrated_data.append(base_row)

        # Backup and write
        if not self.backup_file(file_path):
            return False

        if not self.dry_run:
            return self.write_csv_file(file_path, migrated_data, SchemaType.BASE)
        else:
            logger.info(f"DRY RUN: Would migrate {file_path} to Base schema")
            return True

    def migrate_to_extended_schema(self, file_path: Path) -> bool:
        """Migrate file to Extended schema (ensure all 60 columns present).

        Args:
            file_path: Path to CSV file

        Returns:
            True if migration successful, False otherwise
        """
        logger.info(f"Migrating {file_path} to Extended schema")

        # Read current file
        data, error = self.read_csv_file(file_path)
        if error:
            return False

        if not data:
            logger.warning(f"Empty file: {file_path}")
            return True

        # Detect current schema
        current_schema = self.transformer.detect_schema_type(data[0])
        logger.debug(f"Current schema for {file_path}: {current_schema}")

        # Transform to extended schema
        migrated_data = []
        for row in data:
            extended_row = self.transformer.normalize_to_schema(
                row, SchemaType.EXTENDED
            )
            migrated_data.append(extended_row)

        # Backup and write
        if not self.backup_file(file_path):
            return False

        if not self.dry_run:
            return self.write_csv_file(file_path, migrated_data, SchemaType.EXTENDED)
        else:
            logger.info(f"DRY RUN: Would migrate {file_path} to Extended schema")
            return True

    def migrate_to_filtered_schema(
        self, file_path: Path, preserve_metric_type: bool = True
    ) -> bool:
        """Migrate file to Filtered schema (Extended + Metric Type).

        Args:
            file_path: Path to CSV file
            preserve_metric_type: Whether to preserve existing Metric Type values

        Returns:
            True if migration successful, False otherwise
        """
        logger.info(f"Migrating {file_path} to Filtered schema")

        # Read current file
        data, error = self.read_csv_file(file_path)
        if error:
            return False

        if not data:
            logger.warning(f"Empty file: {file_path}")
            return True

        # Detect current schema
        current_schema = self.transformer.detect_schema_type(data[0])
        logger.debug(f"Current schema for {file_path}: {current_schema}")

        # Transform to filtered schema
        migrated_data = []
        for row in data:
            # Preserve existing Metric Type if it exists and preserve_metric_type is True
            existing_metric_type = (
                row.get("Metric Type", "Most Total Return [%]")
                if preserve_metric_type
                else "Most Total Return [%]"
            )

            filtered_row = self.transformer.normalize_to_schema(
                row, SchemaType.FILTERED, metric_type=existing_metric_type
            )
            migrated_data.append(filtered_row)

        # Backup and write
        if not self.backup_file(file_path):
            return False

        if not self.dry_run:
            return self.write_csv_file(file_path, migrated_data, SchemaType.FILTERED)
        else:
            logger.info(f"DRY RUN: Would migrate {file_path} to Filtered schema")
            return True

    def migrate_directory(
        self, directory: Path, target_schema: SchemaType, **kwargs
    ) -> Dict[str, Any]:
        """Migrate all CSV files in a directory to target schema.

        Args:
            directory: Directory to migrate
            target_schema: Target schema type
            **kwargs: Additional arguments for migration functions

        Returns:
            Dictionary with migration results
        """
        logger.info(f"Migrating directory {directory} to {target_schema.value} schema")

        if not directory.exists():
            error_msg = f"Directory {directory} does not exist"
            logger.error(error_msg)
            return {"error": error_msg}

        csv_files = list(directory.glob("**/*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files in {directory}")

        results = {
            "directory": str(directory),
            "target_schema": target_schema.value,
            "total_files": len(csv_files),
            "successful_migrations": 0,
            "failed_migrations": 0,
            "skipped_files": 0,
            "errors": [],
        }

        for csv_file in csv_files:
            try:
                logger.debug(f"Processing {csv_file}")

                # Choose migration function based on target schema
                if target_schema == SchemaType.BASE:
                    success = self.migrate_to_base_schema(csv_file)
                elif target_schema == SchemaType.EXTENDED:
                    success = self.migrate_to_extended_schema(csv_file)
                elif target_schema == SchemaType.FILTERED:
                    success = self.migrate_to_filtered_schema(csv_file, **kwargs)
                else:
                    logger.warning(f"Unknown target schema: {target_schema}")
                    continue

                if success:
                    results["successful_migrations"] += 1
                    self.results["files_migrated"] += 1
                else:
                    results["failed_migrations"] += 1

            except Exception as e:
                error_msg = f"Error processing {csv_file}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                self.results["errors"].append(error_msg)
                results["failed_migrations"] += 1

        logger.info(
            f"Directory {directory} migration complete: {results['successful_migrations']} successful, {results['failed_migrations']} failed"
        )
        return results

    def run_full_migration(self) -> Dict[str, Any]:
        """Run complete Phase 2 migration across all directories.

        Returns:
            Dictionary with complete migration results
        """
        logger.info("Starting Phase 2 CSV Migration")
        logger.info(f"Dry run mode: {self.dry_run}")

        # Migration plan based on audit results and Phase 2 requirements
        migration_plan = [
            {
                "directory": Path("csv/portfolios"),
                "target_schema": SchemaType.BASE,
                "description": "Convert to Base schema (remove Allocation/Stop Loss columns)",
            },
            {
                "directory": Path("csv/portfolios_filtered"),
                "target_schema": SchemaType.FILTERED,
                "description": "Ensure complete Filtered schema (60 columns + Metric Type)",
                "preserve_metric_type": True,
            },
            {
                "directory": Path("csv/portfolios_best"),
                "target_schema": SchemaType.FILTERED,
                "description": "Standardize to Filtered schema while preserving Metric Type concatenation",
                "preserve_metric_type": True,
            }
            # Note: csv/strategies/ is already compliant per audit, no migration needed
        ]

        # Execute migration plan
        for plan_item in migration_plan:
            directory = plan_item["directory"]
            target_schema = plan_item["target_schema"]
            description = plan_item["description"]

            logger.info(f"Processing: {description}")

            # Extract kwargs for migration function
            kwargs = {
                k: v
                for k, v in plan_item.items()
                if k not in ["directory", "target_schema", "description"]
            }

            # Run migration
            dir_results = self.migrate_directory(directory, target_schema, **kwargs)
            self.results["directories_processed"][str(directory)] = dir_results

        # Save final results
        self.results["migration_completed"] = datetime.now().isoformat()
        self.results["total_errors"] = len(self.results["errors"])

        logger.info("Phase 2 CSV Migration completed")
        logger.info(f"Files migrated: {self.results['files_migrated']}")
        logger.info(f"Total errors: {self.results['total_errors']}")

        return self.results

    def save_results(self, output_path: Path):
        """Save migration results to JSON file.

        Args:
            output_path: Path to save results
        """
        try:
            with open(output_path, "w") as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Migration results saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}")


def main():
    """Main migration function."""
    import argparse

    parser = argparse.ArgumentParser(description="Phase 2 CSV Migration Script")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Simulate migration without making changes (default: True)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute actual migration (overrides --dry-run)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="phase2_migration_results.json",
        help="Output file for migration results",
    )

    args = parser.parse_args()

    # Determine if this is a dry run
    dry_run = not args.execute if args.execute else args.dry_run

    logger.info(f"Starting Phase 2 migration (dry_run={dry_run})")

    # Create migration manager and run
    manager = CSVMigrationManager(dry_run=dry_run)
    results = manager.run_full_migration()

    # Save results
    output_path = Path(args.output)
    manager.save_results(output_path)

    # Print summary
    print("\n" + "=" * 60)
    print("PHASE 2 MIGRATION SUMMARY")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")
    print(f"Files processed: {results['files_migrated']}")
    print(f"Errors: {results['total_errors']}")

    for dir_name, dir_results in results["directories_processed"].items():
        print(f"\n{dir_name}:")
        print(f"  Target: {dir_results['target_schema']} schema")
        print(f"  Total files: {dir_results['total_files']}")
        print(f"  Successful: {dir_results['successful_migrations']}")
        print(f"  Failed: {dir_results['failed_migrations']}")

    if dry_run:
        print(f"\nTo execute migration, run: python {__file__} --execute")

    return 0 if results["total_errors"] == 0 else 1


if __name__ == "__main__":
    exit(main())
