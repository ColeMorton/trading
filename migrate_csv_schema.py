#!/usr/bin/env python3
"""
CSV Schema Migration Script

This script migrates all existing CSV files to include the new "Signal Unconfirmed" column.
The column is inserted after "Signal Exit" and before "Total Open Trades" with default value "None".

Usage:
    python migrate_csv_schema.py --dry-run    # Preview changes without modifying files
    python migrate_csv_schema.py              # Execute migration
    python migrate_csv_schema.py --backup     # Create backups before migration
"""

import argparse
import csv
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path to import schemas
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.tools.portfolio.base_extended_schemas import (
    BasePortfolioSchema,
    ExtendedPortfolioSchema,
    FilteredPortfolioSchema,
    ATRExtendedPortfolioSchema,
    ATRFilteredPortfolioSchema,
    SchemaTransformer,
    SchemaType,
)


class CSVMigrationError(Exception):
    """Exception raised during CSV migration."""
    pass


class CSVMigrator:
    """Handles CSV file migration to include Signal Unconfirmed column."""
    
    def __init__(self, dry_run: bool = False, create_backup: bool = False):
        self.dry_run = dry_run
        self.create_backup = create_backup
        self.transformer = SchemaTransformer()
        self.stats = {
            'files_processed': 0,
            'files_migrated': 0,
            'files_skipped': 0,
            'files_error': 0,
            'errors': []
        }
    
    def detect_csv_schema_type(self, headers: List[str]) -> SchemaType:
        """Detect the schema type from CSV headers."""
        num_columns = len(headers)
        
        # Check for filtered schemas (with Metric Type first)
        if headers and headers[0] == "Metric Type":
            if "ATR Stop Length" in headers and "ATR Stop Multiplier" in headers:
                return SchemaType.ATR_FILTERED
            else:
                return SchemaType.FILTERED
        
        # Check for ATR extended schemas
        if "ATR Stop Length" in headers and "ATR Stop Multiplier" in headers:
            if "Allocation [%]" in headers and "Stop Loss [%]" in headers:
                return SchemaType.ATR_EXTENDED
        
        # Check for extended schemas
        if "Allocation [%]" in headers and "Stop Loss [%]" in headers:
            if "ATR Stop Length" not in headers and "ATR Stop Multiplier" not in headers:
                return SchemaType.EXTENDED
        
        # Check for base schema
        if "Signal Entry" in headers and "Signal Exit" in headers:
            if ("Allocation [%]" not in headers and 
                "Stop Loss [%]" not in headers and
                "ATR Stop Length" not in headers and
                "ATR Stop Multiplier" not in headers):
                return SchemaType.BASE
        
        return SchemaType.UNKNOWN
    
    def get_expected_headers(self, schema_type: SchemaType) -> List[str]:
        """Get expected headers for a schema type after migration."""
        if schema_type == SchemaType.BASE:
            return BasePortfolioSchema.get_column_names()
        elif schema_type == SchemaType.EXTENDED:
            return ExtendedPortfolioSchema.get_column_names()
        elif schema_type == SchemaType.FILTERED:
            return FilteredPortfolioSchema.get_column_names()
        elif schema_type == SchemaType.ATR_EXTENDED:
            return ATRExtendedPortfolioSchema.get_column_names()
        elif schema_type == SchemaType.ATR_FILTERED:
            return ATRFilteredPortfolioSchema.get_column_names()
        else:
            raise CSVMigrationError(f"Unknown schema type: {schema_type}")
    
    def needs_migration(self, headers: List[str]) -> bool:
        """Check if CSV file needs migration (missing Signal Unconfirmed column)."""
        return "Signal Unconfirmed" not in headers and "Signal Exit" in headers
    
    def migrate_headers(self, headers: List[str], schema_type: SchemaType) -> List[str]:
        """Migrate headers to include Signal Unconfirmed column."""
        if "Signal Unconfirmed" in headers:
            return headers  # Already migrated
        
        # Find Signal Exit position
        try:
            signal_exit_idx = headers.index("Signal Exit")
        except ValueError:
            raise CSVMigrationError("Signal Exit column not found in headers")
        
        # Insert Signal Unconfirmed after Signal Exit
        new_headers = headers.copy()
        new_headers.insert(signal_exit_idx + 1, "Signal Unconfirmed")
        
        return new_headers
    
    def migrate_row(self, row: List[str], headers: List[str], new_headers: List[str]) -> List[str]:
        """Migrate a data row to include Signal Unconfirmed column."""
        if len(new_headers) == len(headers):
            return row  # No migration needed
        
        # Find Signal Exit position in original headers
        try:
            signal_exit_idx = headers.index("Signal Exit")
        except ValueError:
            raise CSVMigrationError("Signal Exit column not found in row")
        
        # Insert default value "None" after Signal Exit
        new_row = row.copy()
        if len(new_row) <= signal_exit_idx:
            # Pad row if necessary
            new_row.extend([''] * (signal_exit_idx + 1 - len(new_row)))
        
        new_row.insert(signal_exit_idx + 1, "None")
        
        # Ensure row has correct length
        while len(new_row) < len(new_headers):
            new_row.append('')
        
        return new_row[:len(new_headers)]
    
    def migrate_file(self, file_path: Path) -> bool:
        """Migrate a single CSV file."""
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            if not rows:
                self.stats['files_skipped'] += 1
                return False
            
            headers = rows[0]
            data_rows = rows[1:]
            
            # Detect schema type
            schema_type = self.detect_csv_schema_type(headers)
            if schema_type == SchemaType.UNKNOWN:
                print(f"⚠️  Unknown schema in {file_path}, skipping")
                self.stats['files_skipped'] += 1
                return False
            
            # Check if migration is needed
            if not self.needs_migration(headers):
                print(f"✅ Already migrated: {file_path}")
                self.stats['files_skipped'] += 1
                return False
            
            # Migrate headers
            new_headers = self.migrate_headers(headers, schema_type)
            
            # Migrate data rows
            migrated_rows = []
            for i, row in enumerate(data_rows):
                try:
                    migrated_row = self.migrate_row(row, headers, new_headers)
                    migrated_rows.append(migrated_row)
                except Exception as e:
                    raise CSVMigrationError(f"Error migrating row {i+2}: {e}")
            
            if self.dry_run:
                print(f"🔍 [DRY RUN] Would migrate: {file_path}")
                print(f"    Schema: {schema_type.value}")
                print(f"    Old columns: {len(headers)}")
                print(f"    New columns: {len(new_headers)}")
                return True
            
            # Create backup if requested
            if self.create_backup:
                backup_path = file_path.with_suffix(f'.backup{file_path.suffix}')
                shutil.copy2(file_path, backup_path)
                print(f"📁 Created backup: {backup_path}")
            
            # Write migrated file atomically
            temp_path = file_path.with_suffix('.tmp')
            try:
                with open(temp_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(new_headers)
                    writer.writerows(migrated_rows)
                
                # Atomic replace
                temp_path.replace(file_path)
                print(f"✅ Migrated: {file_path}")
                return True
                
            finally:
                # Clean up temp file if it exists
                if temp_path.exists():
                    temp_path.unlink()
        
        except Exception as e:
            error_msg = f"Error migrating {file_path}: {e}"
            self.stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    def find_csv_files(self, root_dir: Path) -> List[Path]:
        """Find all CSV files in the directory tree."""
        csv_files = []
        
        # Target directories containing strategy CSV files
        target_dirs = [
            'data/raw/portfolios_metrics',
            'data/raw/strategies',
            'data/outputs/portfolio_analysis',
            'data/outputs/ma_cross',
            'csv_backup'  # Include backup directories
        ]
        
        for target_dir in target_dirs:
            dir_path = root_dir / target_dir
            if dir_path.exists():
                csv_files.extend(dir_path.rglob('*.csv'))
        
        return sorted(csv_files)
    
    def migrate_all(self, root_dir: Path) -> None:
        """Migrate all CSV files in the project."""
        print(f"🔍 Scanning for CSV files in {root_dir}")
        csv_files = self.find_csv_files(root_dir)
        
        if not csv_files:
            print("No CSV files found.")
            return
        
        print(f"📊 Found {len(csv_files)} CSV files")
        if self.dry_run:
            print("🔍 Running in DRY RUN mode - no files will be modified")
        if self.create_backup:
            print("📁 Creating backups for modified files")
        
        print("\n" + "="*60)
        
        for file_path in csv_files:
            self.stats['files_processed'] += 1
            
            try:
                if self.migrate_file(file_path):
                    self.stats['files_migrated'] += 1
                else:
                    self.stats['files_skipped'] += 1
            except Exception as e:
                self.stats['files_error'] += 1
                error_msg = f"Unexpected error with {file_path}: {e}"
                self.stats['errors'].append(error_msg)
                print(f"❌ {error_msg}")
        
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print migration summary."""
        print("\n" + "="*60)
        print("📊 MIGRATION SUMMARY")
        print("="*60)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files migrated:  {self.stats['files_migrated']}")
        print(f"Files skipped:   {self.stats['files_skipped']}")
        print(f"Files with errors: {self.stats['files_error']}")
        
        if self.stats['errors']:
            print(f"\n❌ ERRORS ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                print(f"  • {error}")
        
        if self.stats['files_migrated'] > 0:
            if self.dry_run:
                print(f"\n🔍 DRY RUN: {self.stats['files_migrated']} files would be migrated")
            else:
                print(f"\n✅ Successfully migrated {self.stats['files_migrated']} files")
        
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Migrate CSV files to include Signal Unconfirmed column",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Preview changes without modifying files'
    )
    parser.add_argument(
        '--backup',
        action='store_true', 
        help='Create backup copies of modified files'
    )
    parser.add_argument(
        '--root',
        type=Path,
        default=PROJECT_ROOT,
        help='Root directory to scan (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Validate root directory
    if not args.root.exists():
        print(f"❌ Root directory does not exist: {args.root}")
        sys.exit(1)
    
    try:
        migrator = CSVMigrator(dry_run=args.dry_run, create_backup=args.backup)
        migrator.migrate_all(args.root)
        
        if migrator.stats['files_error'] > 0:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()