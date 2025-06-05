"""
CSV Directory Scanner for Schema Validation

This tool scans all CSV directories in the project and validates that
exported CSV files conform to the canonical 59-column schema.
"""

import csv
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.tools.portfolio.canonical_schema import (
    CANONICAL_COLUMN_COUNT,
    CANONICAL_COLUMN_NAMES,
)


class CSVDirectoryScanner:
    """Scanner for validating CSV files across project directories."""

    def __init__(self, base_path: str, log_function: Optional[callable] = None):
        """Initialize the scanner.

        Args:
            base_path: Base project directory path
            log_function: Optional logging function
        """
        self.base_path = Path(base_path)
        self.log = log_function or print

        # Define CSV directories to scan
        self.csv_directories = [
            "csv/portfolios",
            "csv/portfolios_best",
            "csv/portfolios_filtered",
            "csv/strategies",
            "csv/ma_cross",
            "csv/macd_next",
            "csv/mean_reversion",
            "csv/mean_reversion_rsi",
            "csv/mean_reversion_hammer",
            "csv/range",
        ]

    def scan_all_directories(self) -> Dict[str, Dict]:
        """Scan all CSV directories and validate schema compliance.

        Returns:
            Dictionary with validation results for each directory
        """
        results = {}

        self.log("Starting comprehensive CSV directory scan...")

        for csv_dir in self.csv_directories:
            full_path = self.base_path / csv_dir
            if full_path.exists():
                self.log(f"Scanning directory: {csv_dir}")
                results[csv_dir] = self._scan_directory(full_path)
            else:
                self.log(f"Directory not found: {csv_dir}")
                results[csv_dir] = {"status": "directory_not_found", "files": []}

        return results

    def _scan_directory(self, directory_path: Path) -> Dict:
        """Scan a single directory for CSV files and validate them.

        Args:
            directory_path: Path to the directory to scan

        Returns:
            Dictionary with scan results for the directory
        """
        directory_result = {
            "status": "scanned",
            "total_files": 0,
            "compliant_files": 0,
            "non_compliant_files": 0,
            "files": [],
        }

        # Recursively find all CSV files
        csv_files = list(directory_path.rglob("*.csv"))
        directory_result["total_files"] = len(csv_files)

        for csv_file in csv_files:
            file_result = self._validate_csv_file(csv_file)
            directory_result["files"].append(file_result)

            if file_result["is_compliant"]:
                directory_result["compliant_files"] += 1
            else:
                directory_result["non_compliant_files"] += 1

        return directory_result

    def _validate_csv_file(self, file_path: Path) -> Dict:
        """Validate a single CSV file for schema compliance.

        Args:
            file_path: Path to the CSV file

        Returns:
            Dictionary with validation results for the file
        """
        file_result = {
            "file_path": str(file_path.relative_to(self.base_path)),
            "file_size_kb": round(file_path.stat().st_size / 1024, 2),
            "is_compliant": False,
            "column_count": 0,
            "row_count": 0,
            "issues": [],
            "schema_type": "unknown",
        }

        try:
            with open(file_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader, None)

                if not headers:
                    file_result["issues"].append("Empty file or no headers")
                    return file_result

                # Count rows
                rows = list(reader)
                file_result["row_count"] = len(rows)
                file_result["column_count"] = len(headers)

                # Validate schema compliance
                if self._is_portfolio_file(file_path):
                    # Portfolio files should use canonical schema
                    file_result.update(self._validate_portfolio_schema(headers))
                elif self._is_price_data_file(file_path):
                    # Price data files should have OHLCV schema
                    file_result.update(self._validate_price_data_schema(headers))
                else:
                    # Unknown file type
                    file_result["schema_type"] = "unknown"
                    file_result["issues"].append(
                        "Unknown file type - cannot validate schema"
                    )

                # Additional validation for non-empty files
                if file_result["row_count"] == 0:
                    file_result["issues"].append("No data rows")

        except Exception as e:
            file_result["issues"].append(f"Error reading file: {str(e)}")

        return file_result

    def _is_portfolio_file(self, file_path: Path) -> bool:
        """Determine if a CSV file is a portfolio file.

        Args:
            file_path: Path to the CSV file

        Returns:
            True if it's a portfolio file
        """
        portfolio_indicators = [
            "portfolios",
            "strategies",
            "ma_cross",
            "macd",
            "mean_reversion",
            "range",
        ]

        path_str = str(file_path).lower()
        return any(indicator in path_str for indicator in portfolio_indicators)

    def _is_price_data_file(self, file_path: Path) -> bool:
        """Determine if a CSV file is a price data file.

        Args:
            file_path: Path to the CSV file

        Returns:
            True if it's a price data file
        """
        price_data_indicators = ["price_data", "ohlcv", "market_data"]

        path_str = str(file_path).lower()
        return any(indicator in path_str for indicator in price_data_indicators)

    def _validate_portfolio_schema(self, headers: List[str]) -> Dict:
        """Validate portfolio file schema against canonical standard.

        Args:
            headers: List of column headers

        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "schema_type": "portfolio",
            "is_compliant": False,
            "issues": [],
        }

        # Check column count
        if len(headers) != CANONICAL_COLUMN_COUNT:
            validation_result["issues"].append(
                f"Expected {CANONICAL_COLUMN_COUNT} columns, got {len(headers)}"
            )

        # Check column names and order
        if headers != CANONICAL_COLUMN_NAMES:
            # Find specific discrepancies
            missing_columns = set(CANONICAL_COLUMN_NAMES) - set(headers)
            extra_columns = set(headers) - set(CANONICAL_COLUMN_NAMES)

            if missing_columns:
                validation_result["issues"].append(
                    f"Missing columns: {', '.join(sorted(missing_columns))}"
                )

            if extra_columns:
                validation_result["issues"].append(
                    f"Extra columns: {', '.join(sorted(extra_columns))}"
                )

            # Check order if columns match
            if not missing_columns and not extra_columns:
                validation_result["issues"].append(
                    "Column order doesn't match canonical schema"
                )

        # Mark as compliant if no issues
        validation_result["is_compliant"] = len(validation_result["issues"]) == 0

        return validation_result

    def _validate_price_data_schema(self, headers: List[str]) -> Dict:
        """Validate price data file schema.

        Args:
            headers: List of column headers

        Returns:
            Dictionary with validation results
        """
        expected_price_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]

        validation_result = {
            "schema_type": "price_data",
            "is_compliant": False,
            "issues": [],
        }

        # Check for required price data columns
        missing_price_columns = set(expected_price_columns) - set(headers)

        if missing_price_columns:
            validation_result["issues"].append(
                f"Missing price data columns: {', '.join(sorted(missing_price_columns))}"
            )
        else:
            validation_result["is_compliant"] = True

        return validation_result

    def generate_compliance_report(self, scan_results: Dict[str, Dict]) -> str:
        """Generate a human-readable compliance report.

        Args:
            scan_results: Results from scan_all_directories()

        Returns:
            Formatted compliance report string
        """
        report_lines = ["CSV SCHEMA COMPLIANCE REPORT", "=" * 50, ""]

        total_files = 0
        total_compliant = 0
        total_non_compliant = 0

        for directory, results in scan_results.items():
            if results["status"] == "directory_not_found":
                report_lines.append(f"📁 {directory}: DIRECTORY NOT FOUND")
                continue

            directory_files = results["total_files"]
            directory_compliant = results["compliant_files"]
            directory_non_compliant = results["non_compliant_files"]

            total_files += directory_files
            total_compliant += directory_compliant
            total_non_compliant += directory_non_compliant

            compliance_rate = (
                (directory_compliant / directory_files * 100)
                if directory_files > 0
                else 0
            )

            status_emoji = (
                "✅" if compliance_rate == 100 else "⚠️" if compliance_rate > 0 else "❌"
            )

            report_lines.extend(
                [
                    f"{status_emoji} {directory}:",
                    f"   Files: {directory_files} | Compliant: {directory_compliant} | Non-compliant: {directory_non_compliant}",
                    f"   Compliance Rate: {compliance_rate:.1f}%",
                    "",
                ]
            )

            # Show details for non-compliant files
            if directory_non_compliant > 0:
                report_lines.append("   Non-compliant files:")
                for file_info in results["files"]:
                    if not file_info["is_compliant"]:
                        report_lines.append(f"     - {file_info['file_path']}")
                        for issue in file_info["issues"]:
                            report_lines.append(f"       Issue: {issue}")
                report_lines.append("")

        # Overall summary
        overall_compliance = (
            (total_compliant / total_files * 100) if total_files > 0 else 0
        )
        overall_status = (
            "✅ PASS"
            if overall_compliance == 100
            else "⚠️ PARTIAL"
            if overall_compliance > 50
            else "❌ FAIL"
        )

        report_lines.extend(
            [
                "OVERALL SUMMARY",
                "-" * 20,
                f"Total Files Scanned: {total_files}",
                f"Compliant Files: {total_compliant}",
                f"Non-compliant Files: {total_non_compliant}",
                f"Overall Compliance Rate: {overall_compliance:.1f}%",
                f"Status: {overall_status}",
                "",
            ]
        )

        return "\n".join(report_lines)


def main():
    """Main function for running the scanner as a standalone script."""
    import sys

    # Get base directory from command line or use current directory
    base_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    # Create scanner and run scan
    scanner = CSVDirectoryScanner(base_dir)
    results = scanner.scan_all_directories()

    # Generate and print report
    report = scanner.generate_compliance_report(results)
    print(report)

    # Return appropriate exit code
    total_files = sum(
        r.get("total_files", 0) for r in results.values() if isinstance(r, dict)
    )
    total_compliant = sum(
        r.get("compliant_files", 0) for r in results.values() if isinstance(r, dict)
    )

    if total_files > 0 and total_compliant == total_files:
        sys.exit(0)  # All files compliant
    else:
        sys.exit(1)  # Some files non-compliant


if __name__ == "__main__":
    main()
