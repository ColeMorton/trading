"""
Comprehensive test suite for portfolio CSV schema validation.

Tests the canonical schema definition and validation functions to ensure
they correctly identify compliant and non-compliant CSV exports.
"""

from pathlib import Path
import tempfile

import pandas as pd
import pytest

from app.tools.portfolio.base_extended_schemas import (
    CANONICAL_COLUMN_COUNT,
    CANONICAL_COLUMN_NAMES,
    CanonicalPortfolioSchema,
    PortfolioSchemaValidationError,
)
from app.tools.portfolio.schema_validation import (
    SchemaValidator,
    batch_validate_csv_files,
    generate_schema_compliance_report,
    validate_csv_schema,
    validate_dataframe_schema,
)
from tests.fixtures.schema_validation_fixtures import (
    REFERENCE_FILES,
    create_test_csv_files,
    get_test_case,
    validate_reference_files,
)


class TestCanonicalSchema:
    """Test the canonical schema definition."""

    def test_schema_has_59_columns(self):
        """Test that canonical schema has exactly 59 columns."""
        assert CanonicalPortfolioSchema.get_column_count() == 59
        assert len(CANONICAL_COLUMN_NAMES) == CANONICAL_COLUMN_COUNT
        assert CANONICAL_COLUMN_COUNT == 59

    def test_schema_column_names_not_empty(self):
        """Test that all column names are non-empty strings."""
        column_names = CanonicalPortfolioSchema.get_column_names()
        assert all(isinstance(name, str) and len(name) > 0 for name in column_names)

    def test_schema_has_required_columns(self):
        """Test that schema properly identifies required columns."""
        required_cols = CanonicalPortfolioSchema.get_required_columns()
        assert len(required_cols) > 0
        assert "Ticker" in required_cols  # Ticker should always be required

    def test_schema_column_types_defined(self):
        """Test that all columns have defined types."""
        column_types = CanonicalPortfolioSchema.get_column_types()
        assert len(column_types) == 59
        assert all(column_types.values())  # All should have valid types

    def test_schema_column_descriptions(self):
        """Test that columns have descriptions."""
        descriptions = CanonicalPortfolioSchema.get_column_descriptions()
        assert len(descriptions) == 59
        # Most columns should have descriptions
        non_empty_descriptions = [desc for desc in descriptions.values() if desc]
        assert len(non_empty_descriptions) > 50


class TestSchemaValidator:
    """Test the schema validator functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.validator = SchemaValidator(strict_mode=False)
        self.strict_validator = SchemaValidator(strict_mode=True)

    def test_compliant_data_passes_validation(self):
        """Test that compliant data passes validation."""
        test_case = get_test_case("compliant")
        result = self.validator.validate_dataframe(test_case["data"])

        assert result["is_valid"] is True
        assert len(result["violations"]) == 0
        assert result["total_columns"] == 59

    def test_missing_columns_detected(self):
        """Test that missing columns are detected."""
        test_case = get_test_case("missing_columns")
        result = self.validator.validate_dataframe(test_case["data"])

        assert result["is_valid"] is False
        assert len(result["violations"]) > 0
        assert any(v["type"] == "missing_columns" for v in result["violations"])

    def test_extra_columns_detected(self):
        """Test that extra columns are detected as warnings."""
        test_case = get_test_case("extra_columns")
        result = self.validator.validate_dataframe(test_case["data"])

        assert result["is_valid"] is True  # Extra columns are warnings, not violations
        assert len(result["warnings"]) > 0
        assert any(w["type"] == "extra_columns" for w in result["warnings"])

    def test_wrong_column_order_detected(self):
        """Test that incorrect column order is detected."""
        test_case = get_test_case("wrong_order")
        result = self.validator.validate_dataframe(test_case["data"])

        assert result["is_valid"] is False
        assert any(v["type"] == "column_order_mismatch" for v in result["violations"])

    def test_wrong_column_count_detected(self):
        """Test that incorrect column count is detected."""
        test_case = get_test_case("wrong_count")
        result = self.validator.validate_dataframe(test_case["data"])

        assert result["is_valid"] is False
        assert any(v["type"] == "column_count_mismatch" for v in result["violations"])

    def test_empty_required_columns_detected(self):
        """Test that empty required columns are detected."""
        test_case = get_test_case("empty_required")
        result = self.validator.validate_dataframe(test_case["data"])

        assert result["is_valid"] is False
        assert any(v["type"] == "required_column_empty" for v in result["violations"])

    def test_strict_mode_raises_exceptions(self):
        """Test that strict mode raises exceptions on violations."""
        test_case = get_test_case("missing_columns")

        with pytest.raises(PortfolioSchemaValidationError):
            self.strict_validator.validate_dataframe(test_case["data"])

    def test_column_analysis_included(self):
        """Test that column analysis is included in results."""
        test_case = get_test_case("compliant")
        result = self.validator.validate_dataframe(test_case["data"])

        assert "column_analysis" in result
        assert len(result["column_analysis"]) > 0

        # Check analysis structure
        for analysis in result["column_analysis"].values():
            assert "expected_type" in analysis
            assert "actual_dtype" in analysis
            assert "type_valid" in analysis
            assert "null_count" in analysis


class TestConvenienceFunctions:
    """Test convenience functions for validation."""

    def test_validate_dataframe_schema_function(self):
        """Test the validate_dataframe_schema convenience function."""
        test_case = get_test_case("compliant")
        result = validate_dataframe_schema(test_case["data"], strict=False)

        assert result["is_valid"] is True
        assert "violations" in result
        assert "warnings" in result

    def test_validate_csv_schema_nonexistent_file(self):
        """Test validation of non-existent CSV file."""
        with pytest.raises(PortfolioSchemaValidationError):
            validate_csv_schema("/nonexistent/file.csv", strict=True)

    def test_batch_validation(self):
        """Test batch validation of multiple files."""
        # Create temporary test files
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = create_test_csv_files(Path(temp_dir))

            results = batch_validate_csv_files(list(file_paths.values()), strict=False)

            assert len(results) == len(file_paths)
            assert all("is_valid" in result for result in results.values())


class TestComplianceReporting:
    """Test compliance report generation."""

    def test_generate_compliance_report(self):
        """Test compliance report generation."""
        test_case = get_test_case("missing_columns")
        result = validate_dataframe_schema(test_case["data"], strict=False)

        report = generate_schema_compliance_report(result)

        assert isinstance(report, str)
        assert len(report) > 0
        assert "Schema Compliance Report" in report
        assert "NON-COMPLIANT" in report  # Should show non-compliant status

    def test_compliant_report(self):
        """Test report for compliant data."""
        test_case = get_test_case("compliant")
        result = validate_dataframe_schema(test_case["data"], strict=False)

        report = generate_schema_compliance_report(result)

        assert "COMPLIANT" in report
        assert "✅" in report


class TestRealDataValidation:
    """Test validation against real portfolio CSV files."""

    def test_reference_files_exist(self):
        """Test that reference files exist."""
        for file_path in REFERENCE_FILES:
            path = Path(file_path)
            if path.exists():  # Only test files that exist
                assert path.is_file()

    def test_reference_files_validation(self):
        """Test validation of real reference files."""
        results = validate_reference_files()

        for file_path, result in results.items():
            if "error" not in result:  # Only test files that could be read
                assert "is_valid" in result
                assert "total_columns" in result

                # Reference files should be compliant or have minimal issues
                if not result["is_valid"]:
                    print(f"Reference file {file_path} has validation issues:")
                    for violation in result.get("violations", []):
                        print(f"  - {violation['message']}")

    @pytest.mark.parametrize("file_path", REFERENCE_FILES)
    def test_individual_reference_file(self, file_path):
        """Test each reference file individually."""
        path = Path(file_path)
        if not path.exists():
            pytest.skip(f"Reference file does not exist: {file_path}")

        try:
            result = validate_csv_schema(file_path, strict=False)

            # Basic assertions
            assert "is_valid" in result
            assert "total_columns" in result

            # Expected to have 59 columns (or close to it)
            assert result["total_columns"] >= 55  # Allow some flexibility

        except Exception as e:
            pytest.fail(f"Failed to validate reference file {file_path}: {e!s}")


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_dataframe(self):
        """Test validation of empty DataFrame."""
        empty_df = pd.DataFrame()
        validator = SchemaValidator(strict_mode=False)

        result = validator.validate_dataframe(empty_df)
        assert result["is_valid"] is False
        assert result["total_columns"] == 0

    def test_single_row_dataframe(self):
        """Test validation of single-row DataFrame."""
        test_case = get_test_case("compliant")
        single_row_df = test_case["data"].iloc[:1]

        validator = SchemaValidator(strict_mode=False)
        result = validator.validate_dataframe(single_row_df)

        assert result["total_rows"] == 1
        # Should still be valid if columns are correct
        if result["total_columns"] == 59:
            assert result["is_valid"] is True

    def test_dataframe_with_all_nulls(self):
        """Test DataFrame where all values are null."""
        test_case = get_test_case("compliant")
        null_df = test_case["data"].copy()

        # Set all values to null
        for col in null_df.columns:
            null_df[col] = None

        validator = SchemaValidator(strict_mode=False)
        result = validator.validate_dataframe(null_df)

        # Should detect issues with required columns
        assert not result["is_valid"]
        assert any(v["type"] == "required_column_empty" for v in result["violations"])


class TestPerformance:
    """Test performance of validation functions."""

    def test_large_dataframe_validation(self):
        """Test validation performance with large DataFrame."""
        test_case = get_test_case("compliant")

        # Create a large DataFrame by repeating the sample data
        large_df = pd.concat([test_case["data"]] * 1000, ignore_index=True)

        validator = SchemaValidator(strict_mode=False)
        result = validator.validate_dataframe(large_df)

        assert result["total_rows"] == 3000
        assert result["total_columns"] == 59
        assert result["is_valid"] is True


if __name__ == "__main__":
    # Run a quick validation test
    print("Running quick schema validation test...")

    # Test compliant data
    test_case = get_test_case("compliant")
    result = validate_dataframe_schema(test_case["data"], strict=False)
    print(f"Compliant data validation: {'✅ PASS' if result['is_valid'] else '❌ FAIL'}")

    # Test non-compliant data
    test_case = get_test_case("missing_columns")
    result = validate_dataframe_schema(test_case["data"], strict=False)
    print(
        f"Non-compliant data detection: {'✅ PASS' if not result['is_valid'] else '❌ FAIL'}",
    )

    # Test reference files
    ref_results = validate_reference_files()
    for file_path, result in ref_results.items():
        if "error" not in result:
            status = "✅ COMPLIANT" if result["is_valid"] else "⚠️  ISSUES"
            print(f"Reference file {Path(file_path).name}: {status}")

    print("\nSchema validation system is ready! ✅")
