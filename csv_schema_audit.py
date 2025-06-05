#!/usr/bin/env python3
"""
Comprehensive CSV Schema Audit Tool

This script conducts a thorough audit of all CSV files across the project to:
1. Identify schema inconsistencies
2. Analyze column count distributions
3. Generate compliance reports
4. Prepare migration recommendations

Uses the existing SchemaTransformer from Phase 1 for schema detection.
"""

import csv
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app.tools.portfolio.base_extended_schemas import (
        BasePortfolioSchema,
        ExtendedPortfolioSchema,
        FilteredPortfolioSchema,
        SchemaTransformer,
        SchemaType,
    )

    SCHEMA_DETECTION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import schema detection: {e}")
    SCHEMA_DETECTION_AVAILABLE = False


@dataclass
class FileAuditResult:
    """Results of auditing a single CSV file."""

    file_path: str
    column_count: int
    schema_type: Optional[str]
    compliance_status: str  # "compliant", "non_compliant", "error"
    issues: List[str]
    columns: List[str]
    expected_columns: Optional[int] = None
    missing_columns: List[str] = None
    extra_columns: List[str] = None


@dataclass
class DirectoryAuditSummary:
    """Summary statistics for a directory."""

    directory: str
    total_files: int
    compliant_files: int
    non_compliant_files: int
    error_files: int
    column_count_distribution: Dict[int, int]
    schema_type_distribution: Dict[str, int]
    common_issues: Dict[str, int]


class CSVSchemaAuditor:
    """Comprehensive CSV schema auditor."""

    def __init__(self):
        self.transformer = SchemaTransformer() if SCHEMA_DETECTION_AVAILABLE else None
        self.audit_results: Dict[str, List[FileAuditResult]] = {}

        # Expected schema configurations
        self.expected_schemas = {
            "csv/portfolios": {"type": "base", "columns": 58},
            "csv/portfolios_filtered": {
                "type": "filtered",
                "columns": 61,
            },  # With Metric Type
            "csv/portfolios_best": {"type": "filtered", "columns": 61},
            "csv/strategies": {"type": "mixed", "columns": "variable"},
        }

    def audit_file(self, file_path: str) -> FileAuditResult:
        """Audit a single CSV file."""
        issues = []
        schema_type = None
        compliance_status = "error"
        columns = []
        column_count = 0

        try:
            # Read file headers
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                try:
                    headers = next(reader)
                    columns = [col.strip() for col in headers]
                    column_count = len(columns)
                except StopIteration:
                    issues.append("Empty file")
                    return FileAuditResult(
                        file_path=file_path,
                        column_count=0,
                        schema_type=None,
                        compliance_status="error",
                        issues=issues,
                        columns=[],
                    )

            # Detect schema if available
            if self.transformer and SCHEMA_DETECTION_AVAILABLE:
                try:
                    detected_schema = self.transformer.detect_schema_type_from_columns(
                        columns
                    )
                    schema_type = detected_schema
                except Exception as e:
                    issues.append(f"Schema detection failed: {str(e)}")

            # Determine compliance based on directory expectations
            directory_path = str(Path(file_path).parent.relative_to(project_root))
            expected_config = self._get_expected_config(directory_path)

            # Check compliance
            missing_columns = []
            extra_columns = []
            expected_columns = None

            if expected_config:
                expected_type = expected_config.get("type")
                expected_col_count = expected_config.get("columns")

                if isinstance(expected_col_count, int):
                    expected_columns = expected_col_count
                    if column_count != expected_col_count:
                        issues.append(
                            f"Column count mismatch: expected {expected_col_count}, got {column_count}"
                        )

                # Check schema type alignment
                if expected_type != "mixed" and schema_type:
                    if (
                        (expected_type == "base" and schema_type not in ["base"])
                        or (
                            expected_type == "extended"
                            and schema_type not in ["extended", "filtered"]
                        )
                        or (
                            expected_type == "filtered"
                            and schema_type not in ["filtered"]
                        )
                    ):
                        issues.append(
                            f"Schema type mismatch: expected {expected_type}, detected {schema_type}"
                        )

            # Additional validation
            self._validate_column_names(columns, issues)
            self._check_for_duplicates(columns, issues)

            # Determine compliance status
            if not issues:
                compliance_status = "compliant"
            else:
                compliance_status = "non_compliant"

        except Exception as e:
            issues.append(f"File read error: {str(e)}")
            compliance_status = "error"

        return FileAuditResult(
            file_path=file_path,
            column_count=column_count,
            schema_type=schema_type,
            compliance_status=compliance_status,
            issues=issues,
            columns=columns,
            expected_columns=expected_columns,
            missing_columns=missing_columns,
            extra_columns=extra_columns,
        )

    def _get_expected_config(self, directory_path: str) -> Optional[Dict]:
        """Get expected configuration for a directory."""
        for pattern, config in self.expected_schemas.items():
            if directory_path.startswith(pattern) or pattern in directory_path:
                return config
        return None

    def _validate_column_names(self, columns: List[str], issues: List[str]):
        """Validate column names for common issues."""
        # Check for empty column names
        if any(not col.strip() for col in columns):
            issues.append("Contains empty column names")

        # Check for suspicious characters
        suspicious_chars = ["#", "@", "$", "&"]
        for col in columns:
            if any(char in col for char in suspicious_chars):
                issues.append(f"Suspicious characters in column: {col}")

        # Check for very long column names (potential data leakage)
        for col in columns:
            if len(col) > 100:
                issues.append(f"Unusually long column name: {col[:50]}...")

    def _check_for_duplicates(self, columns: List[str], issues: List[str]):
        """Check for duplicate column names."""
        seen = set()
        duplicates = set()
        for col in columns:
            if col in seen:
                duplicates.add(col)
            seen.add(col)

        if duplicates:
            issues.append(f"Duplicate columns: {', '.join(sorted(duplicates))}")

    def audit_directory(self, directory_path: str) -> List[FileAuditResult]:
        """Audit all CSV files in a directory."""
        results = []

        if not os.path.exists(directory_path):
            print(f"Directory not found: {directory_path}")
            return results

        # Find all CSV files recursively
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.endswith(".csv"):
                    file_path = os.path.join(root, file)
                    result = self.audit_file(file_path)
                    results.append(result)

        return results

    def generate_directory_summary(
        self, results: List[FileAuditResult], directory: str
    ) -> DirectoryAuditSummary:
        """Generate summary statistics for a directory."""
        total_files = len(results)
        compliant_files = len(
            [r for r in results if r.compliance_status == "compliant"]
        )
        non_compliant_files = len(
            [r for r in results if r.compliance_status == "non_compliant"]
        )
        error_files = len([r for r in results if r.compliance_status == "error"])

        # Column count distribution
        column_counts = [r.column_count for r in results]
        column_count_distribution = dict(Counter(column_counts))

        # Schema type distribution
        schema_types = [r.schema_type or "unknown" for r in results]
        schema_type_distribution = dict(Counter(schema_types))

        # Common issues
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)
        common_issues = dict(Counter(all_issues))

        return DirectoryAuditSummary(
            directory=directory,
            total_files=total_files,
            compliant_files=compliant_files,
            non_compliant_files=non_compliant_files,
            error_files=error_files,
            column_count_distribution=column_count_distribution,
            schema_type_distribution=schema_type_distribution,
            common_issues=common_issues,
        )

    def audit_all_directories(self) -> Dict[str, DirectoryAuditSummary]:
        """Audit all target directories."""
        target_directories = [
            "csv/portfolios",
            "csv/portfolios_filtered",
            "csv/portfolios_best",
            "csv/strategies",
        ]

        summaries = {}

        for directory in target_directories:
            full_path = project_root / directory
            print(f"Auditing directory: {directory}")

            results = self.audit_directory(str(full_path))
            self.audit_results[directory] = results

            summary = self.generate_directory_summary(results, directory)
            summaries[directory] = summary

            print(f"  Found {summary.total_files} CSV files")
            print(f"  Compliant: {summary.compliant_files}")
            print(f"  Non-compliant: {summary.non_compliant_files}")
            print(f"  Errors: {summary.error_files}")
            print()

        return summaries

    def generate_audit_report(self, summaries: Dict[str, DirectoryAuditSummary]) -> str:
        """Generate comprehensive audit report."""
        report = []
        report.append("# CSV Schema Audit Report")
        report.append("=" * 50)
        report.append("")

        # Executive Summary
        total_files = sum(s.total_files for s in summaries.values())
        total_compliant = sum(s.compliant_files for s in summaries.values())
        total_non_compliant = sum(s.non_compliant_files for s in summaries.values())
        total_errors = sum(s.error_files for s in summaries.values())

        compliance_rate = (
            (total_compliant / total_files * 100) if total_files > 0 else 0
        )

        report.append("## Executive Summary")
        report.append(f"- Total CSV files analyzed: {total_files}")
        report.append(f"- Compliant files: {total_compliant} ({compliance_rate:.1f}%)")
        report.append(f"- Non-compliant files: {total_non_compliant}")
        report.append(f"- Error files: {total_errors}")
        report.append("")

        # Directory Analysis
        for directory, summary in summaries.items():
            report.append(f"## Directory: {directory}")
            report.append(
                f"**Expected Schema**: {self.expected_schemas.get(directory, {}).get('type', 'unknown')}"
            )
            report.append(
                f"**Expected Columns**: {self.expected_schemas.get(directory, {}).get('columns', 'unknown')}"
            )
            report.append("")

            # Basic Stats
            report.append("### Statistics")
            report.append(f"- Total files: {summary.total_files}")
            report.append(f"- Compliant: {summary.compliant_files}")
            report.append(f"- Non-compliant: {summary.non_compliant_files}")
            report.append(f"- Errors: {summary.error_files}")
            report.append("")

            # Column Distribution
            if summary.column_count_distribution:
                report.append("### Column Count Distribution")
                for count, files in sorted(summary.column_count_distribution.items()):
                    report.append(f"- {count} columns: {files} files")
                report.append("")

            # Schema Distribution
            if summary.schema_type_distribution:
                report.append("### Schema Type Distribution")
                for schema_type, files in sorted(
                    summary.schema_type_distribution.items()
                ):
                    report.append(f"- {schema_type}: {files} files")
                report.append("")

            # Common Issues
            if summary.common_issues:
                report.append("### Most Common Issues")
                sorted_issues = sorted(
                    summary.common_issues.items(), key=lambda x: x[1], reverse=True
                )
                for issue, count in sorted_issues[:10]:  # Top 10 issues
                    report.append(f"- {issue}: {count} files")
                report.append("")

            # Non-compliant files
            non_compliant = [
                r
                for r in self.audit_results[directory]
                if r.compliance_status == "non_compliant"
            ]
            if non_compliant:
                report.append("### Non-Compliant Files")
                for result in non_compliant[:10]:  # First 10 non-compliant files
                    rel_path = os.path.relpath(result.file_path, project_root)
                    report.append(f"- `{rel_path}` ({result.column_count} cols)")
                    for issue in result.issues[:3]:  # First 3 issues
                        report.append(f"  - {issue}")
                if len(non_compliant) > 10:
                    report.append(f"  - ... and {len(non_compliant) - 10} more files")
                report.append("")

            report.append("---")
            report.append("")

        # Migration Recommendations
        report.append("## Migration Recommendations")
        report.append("")

        priority_order = []

        for directory, summary in summaries.items():
            if summary.non_compliant_files > 0:
                severity = self._calculate_severity(summary)
                priority_order.append((directory, severity, summary))

        # Sort by severity (high to low)
        priority_order.sort(key=lambda x: x[1], reverse=True)

        for i, (directory, severity, summary) in enumerate(priority_order, 1):
            severity_text = (
                "HIGH" if severity >= 0.7 else "MEDIUM" if severity >= 0.4 else "LOW"
            )
            report.append(f"### Priority {i}: {directory} ({severity_text})")
            report.append(f"- Non-compliant files: {summary.non_compliant_files}")
            report.append(f"- Error files: {summary.error_files}")

            # Suggest actions
            expected_config = self.expected_schemas.get(directory, {})
            expected_type = expected_config.get("type")

            if expected_type == "base":
                report.append("- **Action**: Migrate to Base schema (58 columns)")
            elif expected_type == "extended":
                report.append("- **Action**: Migrate to Extended schema (60 columns)")
            elif expected_type == "filtered":
                report.append("- **Action**: Migrate to Filtered schema (61 columns)")
            elif expected_type == "mixed":
                report.append(
                    "- **Action**: Standardize to appropriate schema based on content"
                )

            report.append("")

        return "\n".join(report)

    def _calculate_severity(self, summary: DirectoryAuditSummary) -> float:
        """Calculate severity score for migration priority."""
        if summary.total_files == 0:
            return 0.0

        # Factors affecting severity:
        # 1. Percentage of non-compliant files
        # 2. Number of error files
        # 3. Diversity of column counts (indicating inconsistency)

        non_compliance_rate = summary.non_compliant_files / summary.total_files
        error_rate = summary.error_files / summary.total_files

        # Column count diversity (higher = more inconsistent)
        unique_counts = len(summary.column_count_distribution)
        diversity_factor = min(unique_counts / 5, 1.0)  # Normalize to 0-1

        # Weighted score
        severity = 0.5 * non_compliance_rate + 0.3 * error_rate + 0.2 * diversity_factor

        return severity

    def export_detailed_results(self, output_file: str):
        """Export detailed results to JSON for further analysis."""
        export_data = {
            "audit_timestamp": "",
            "total_files": 0,
            "directories": {},
            "non_compliant_files": [],
        }

        # Calculate totals
        total_files = sum(len(results) for results in self.audit_results.values())
        export_data["total_files"] = total_files

        # Directory summaries
        for directory, results in self.audit_results.items():
            summary = self.generate_directory_summary(results, directory)
            export_data["directories"][directory] = {
                "total_files": summary.total_files,
                "compliant_files": summary.compliant_files,
                "non_compliant_files": summary.non_compliant_files,
                "error_files": summary.error_files,
                "column_count_distribution": summary.column_count_distribution,
                "schema_type_distribution": summary.schema_type_distribution,
                "common_issues": summary.common_issues,
            }

        # Detailed non-compliant files
        for directory, results in self.audit_results.items():
            for result in results:
                if result.compliance_status != "compliant":
                    export_data["non_compliant_files"].append(
                        {
                            "file_path": os.path.relpath(
                                result.file_path, project_root
                            ),
                            "directory": directory,
                            "column_count": result.column_count,
                            "schema_type": result.schema_type,
                            "compliance_status": result.compliance_status,
                            "issues": result.issues,
                            "expected_columns": result.expected_columns,
                        }
                    )

        # Save to file
        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        print(f"Detailed results exported to: {output_file}")


def main():
    """Main execution function."""
    print("CSV Schema Audit Tool")
    print("=" * 50)

    if not SCHEMA_DETECTION_AVAILABLE:
        print(
            "Warning: Schema detection not available. Limited analysis will be performed."
        )
        print()

    auditor = CSVSchemaAuditor()

    # Run comprehensive audit
    print("Starting comprehensive audit...")
    summaries = auditor.audit_all_directories()

    # Generate report
    print("Generating audit report...")
    report = auditor.generate_audit_report(summaries)

    # Save report
    report_file = project_root / "csv_schema_audit_report.md"
    with open(report_file, "w") as f:
        f.write(report)

    print(f"Audit report saved to: {report_file}")

    # Export detailed results
    json_file = project_root / "csv_schema_audit_results.json"
    auditor.export_detailed_results(str(json_file))

    # Print summary to console
    print("\n" + "=" * 50)
    print("AUDIT SUMMARY")
    print("=" * 50)

    total_files = sum(s.total_files for s in summaries.values())
    total_compliant = sum(s.compliant_files for s in summaries.values())
    compliance_rate = (total_compliant / total_files * 100) if total_files > 0 else 0

    print(f"Total files analyzed: {total_files}")
    print(f"Overall compliance rate: {compliance_rate:.1f}%")
    print()

    for directory, summary in summaries.items():
        dir_compliance = (
            (summary.compliant_files / summary.total_files * 100)
            if summary.total_files > 0
            else 0
        )
        print(
            f"{directory}: {dir_compliance:.1f}% compliant ({summary.compliant_files}/{summary.total_files})"
        )

    print(f"\nFull report: {report_file}")
    print(f"Detailed data: {json_file}")


if __name__ == "__main__":
    main()
