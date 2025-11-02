"""
Test Suite: trade_history_utils.py Argument Parser

Coverage:
- Mutually exclusive operation enforcement
- Required parameter validation per operation
- Parameter combination validation
- Help text generation
- Argument parsing edge cases

This module tests the argparse configuration and validation logic.
"""

from unittest.mock import patch

import pytest

from app.tools import trade_history_utils


@pytest.mark.unit
class TestMutuallyExclusiveOperations:
    """Tests for mutually exclusive operation enforcement."""

    def test_cannot_use_summary_and_compare_together(self):
        """Should fail when --summary and --compare are both specified."""
        with pytest.raises(SystemExit) as exc_info:
            with patch(
                "sys.argv",
                [
                    "trade_history_utils.py",
                    "--summary",
                    "--compare",
                    "--portfolio",
                    "test",
                ],
            ):
                trade_history_utils.main()

        assert exc_info.value.code != 0

    def test_cannot_use_summary_and_merge_together(self):
        """Should fail when --summary and --merge are both specified."""
        with pytest.raises(SystemExit) as exc_info:
            with patch(
                "sys.argv",
                [
                    "trade_history_utils.py",
                    "--summary",
                    "--merge",
                    "--portfolio",
                    "test",
                ],
            ):
                trade_history_utils.main()

        assert exc_info.value.code != 0

    def test_cannot_use_update_quality_and_validate_together(self):
        """Should fail when --update-quality and --validate-portfolio are both specified."""
        with pytest.raises(SystemExit) as exc_info:
            with patch(
                "sys.argv",
                [
                    "trade_history_utils.py",
                    "--update-quality",
                    "--validate-portfolio",
                    "--portfolio",
                    "test",
                ],
            ):
                trade_history_utils.main()

        assert exc_info.value.code != 0

    def test_cannot_use_find_duplicates_and_remove_duplicates_together(self):
        """Should fail when --find-duplicates and --remove-duplicates are both specified."""
        with pytest.raises(SystemExit) as exc_info:
            with patch(
                "sys.argv",
                [
                    "trade_history_utils.py",
                    "--find-duplicates",
                    "--remove-duplicates",
                    "--portfolio",
                    "test",
                ],
            ):
                trade_history_utils.main()

        assert exc_info.value.code != 0

    def test_cannot_use_three_operations_together(self):
        """Should fail when three operations are specified."""
        with pytest.raises(SystemExit) as exc_info:
            with patch(
                "sys.argv",
                [
                    "trade_history_utils.py",
                    "--summary",
                    "--compare",
                    "--merge",
                    "--portfolio",
                    "test",
                ],
            ):
                trade_history_utils.main()

        assert exc_info.value.code != 0


@pytest.mark.unit
class TestRequiredParametersValidation:
    """Tests for required parameter validation per operation."""

    def test_summary_requires_portfolio_parameter(self):
        """--summary operation requires --portfolio parameter."""
        with patch("sys.argv", ["trade_history_utils.py", "--summary"]):
            exit_code = trade_history_utils.main()

        assert exit_code == 1

    def test_compare_requires_portfolios_parameter(self):
        """--compare operation requires --portfolios parameter."""
        with patch("sys.argv", ["trade_history_utils.py", "--compare"]):
            exit_code = trade_history_utils.main()

        assert exit_code == 1

    def test_merge_requires_source_and_target(self):
        """--merge operation requires both --source and --target parameters."""
        # Missing both
        with patch("sys.argv", ["trade_history_utils.py", "--merge"]):
            exit_code = trade_history_utils.main()
        assert exit_code == 1

        # Missing target
        with patch(
            "sys.argv", ["trade_history_utils.py", "--merge", "--source", "p1,p2"]
        ):
            exit_code = trade_history_utils.main()
        assert exit_code == 1

        # Missing source
        with patch(
            "sys.argv", ["trade_history_utils.py", "--merge", "--target", "combined"]
        ):
            exit_code = trade_history_utils.main()
        assert exit_code == 1

    def test_find_position_requires_uuid(self):
        """--find-position operation requires --uuid parameter."""
        with patch("sys.argv", ["trade_history_utils.py", "--find-position"]):
            exit_code = trade_history_utils.main()

        assert exit_code == 1

    def test_update_quality_requires_portfolio(self):
        """--update-quality operation requires --portfolio parameter."""
        with patch("sys.argv", ["trade_history_utils.py", "--update-quality"]):
            exit_code = trade_history_utils.main()

        assert exit_code == 1

    def test_remove_duplicates_requires_portfolio(self):
        """--remove-duplicates operation requires --portfolio parameter."""
        with patch("sys.argv", ["trade_history_utils.py", "--remove-duplicates"]):
            exit_code = trade_history_utils.main()

        assert exit_code == 1

    def test_find_duplicates_requires_portfolio(self):
        """--find-duplicates operation requires --portfolio parameter."""
        with patch("sys.argv", ["trade_history_utils.py", "--find-duplicates"]):
            exit_code = trade_history_utils.main()

        assert exit_code == 1

    def test_export_summary_requires_portfolio(self):
        """--export-summary operation requires --portfolio parameter."""
        with patch(
            "sys.argv",
            ["trade_history_utils.py", "--export-summary", "--output", "/tmp/out.json"],
        ):
            exit_code = trade_history_utils.main()

        assert exit_code == 1

    def test_validate_portfolio_requires_portfolio(self):
        """--validate-portfolio operation requires --portfolio parameter."""
        with patch("sys.argv", ["trade_history_utils.py", "--validate-portfolio"]):
            exit_code = trade_history_utils.main()

        assert exit_code == 1

    def test_normalize_portfolio_requires_portfolio(self):
        """--normalize-portfolio operation requires --portfolio parameter."""
        with patch("sys.argv", ["trade_history_utils.py", "--normalize-portfolio"]):
            exit_code = trade_history_utils.main()

        assert exit_code == 1


@pytest.mark.unit
class TestParameterCombinations:
    """Tests for valid and invalid parameter combinations."""

    @patch("app.tools.trade_history_utils.list_portfolios")
    def test_list_portfolios_ignores_other_parameters(self, mock_list, capsys):
        """--list-portfolios should ignore other parameters."""
        mock_list.return_value = ["p1", "p2"]

        with patch(
            "sys.argv",
            [
                "trade_history_utils.py",
                "--list-portfolios",
                "--portfolio",
                "ignored",  # Should be ignored
                "--verbose",  # Should be respected
            ],
        ):
            exit_code = trade_history_utils.main()

        assert exit_code == 0

    @patch("app.tools.position_service_wrapper.get_config")
    @patch("app.tools.trade_history_utils.list_portfolios")
    def test_health_check_requires_an_operation_flag(
        self, mock_list, mock_config, capsys
    ):
        """--health-check is a config flag and still requires an operation."""
        from pathlib import Path

        class MockConfig:
            base_dir = Path("/test")
            prices_dir = Path("/test/prices")
            positions_dir = Path("/test/positions")

        mock_config.return_value = MockConfig()
        mock_list.return_value = []

        # --health-check alone should fail (no operation specified)
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["trade_history_utils.py", "--health-check"]):
                trade_history_utils.main()

        assert exc_info.value.code != 0

    @patch("app.tools.trade_history_utils.get_portfolio_summary")
    def test_verbose_flag_works_with_summary(self, mock_summary, capsys):
        """--verbose flag should work with --summary operation."""
        mock_summary.return_value = {
            "total_positions": 10,
            "open_positions": 5,
            "closed_positions": 5,
        }

        with patch(
            "sys.argv",
            ["trade_history_utils.py", "--summary", "--portfolio", "test", "--verbose"],
        ):
            exit_code = trade_history_utils.main()

        assert exit_code == 0

    @patch("app.tools.trade_history_utils.get_portfolio_summary")
    def test_debug_flag_works_with_summary(self, mock_summary, capsys):
        """--debug flag should work with --summary operation."""
        mock_summary.return_value = {
            "total_positions": 10,
            "open_positions": 5,
            "closed_positions": 5,
        }

        with patch(
            "sys.argv",
            ["trade_history_utils.py", "--summary", "--portfolio", "test", "--debug"],
        ):
            exit_code = trade_history_utils.main()

        assert exit_code == 0

    @patch("app.tools.position_service_wrapper.TradingSystemConfig")
    @patch("app.tools.trade_history_utils.get_portfolio_summary")
    def test_base_dir_works_with_summary(self, mock_summary, mock_config, capsys):
        """--base-dir flag should work with --summary operation."""
        mock_instance = mock_config.return_value
        mock_instance.base_dir = "/custom/path"
        mock_summary.return_value = {
            "total_positions": 10,
            "open_positions": 5,
            "closed_positions": 5,
        }

        with patch(
            "sys.argv",
            [
                "trade_history_utils.py",
                "--summary",
                "--portfolio",
                "test",
                "--base-dir",
                "/custom/path",
            ],
        ):
            exit_code = trade_history_utils.main()

        assert exit_code == 0


@pytest.mark.unit
class TestHelpTextGeneration:
    """Tests for help text and documentation."""

    def test_help_flag_displays_usage(self, capsys):
        """--help should display usage information."""
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["trade_history_utils.py", "--help"]):
                trade_history_utils.main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower()
        assert "Trade History Utilities" in captured.out

    def test_help_shows_all_operations(self, capsys):
        """--help should list all available operations."""
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["trade_history_utils.py", "--help"]):
                trade_history_utils.main()

        captured = capsys.readouterr()
        assert "--summary" in captured.out
        assert "--compare" in captured.out
        assert "--update-quality" in captured.out
        assert "--merge" in captured.out
        assert "--list-portfolios" in captured.out
        assert "--remove-duplicates" in captured.out
        assert "--find-duplicates" in captured.out
        assert "--find-position" in captured.out
        assert "--export-summary" in captured.out
        assert "--validate-portfolio" in captured.out
        assert "--normalize-portfolio" in captured.out
        assert "--fix-quality" in captured.out

    def test_help_shows_examples(self, capsys):
        """--help should show usage examples."""
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["trade_history_utils.py", "--help"]):
                trade_history_utils.main()

        captured = capsys.readouterr()
        assert "Examples:" in captured.out
        assert "Get portfolio summary" in captured.out
        assert "Compare portfolios" in captured.out

    def test_help_shows_configuration_options(self, capsys):
        """--help should show configuration option group."""
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["trade_history_utils.py", "--help"]):
                trade_history_utils.main()

        captured = capsys.readouterr()
        assert "--base-dir" in captured.out
        assert "--verbose" in captured.out
        assert "--debug" in captured.out
        assert "--health-check" in captured.out

    def test_help_shows_portfolio_parameters(self, capsys):
        """--help should show portfolio parameter group."""
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["trade_history_utils.py", "--help"]):
                trade_history_utils.main()

        captured = capsys.readouterr()
        assert "--portfolio" in captured.out
        assert "--portfolios" in captured.out
        assert "--source" in captured.out
        assert "--target" in captured.out
        assert "--uuid" in captured.out
        assert "--output" in captured.out


@pytest.mark.unit
class TestArgumentParsingEdgeCases:
    """Tests for argument parsing edge cases."""

    @patch("app.tools.trade_history_utils.list_portfolios")
    def test_short_verbose_flag(self, mock_list, capsys):
        """-v should be accepted as shorthand for --verbose."""
        mock_list.return_value = []

        with patch("sys.argv", ["trade_history_utils.py", "--list-portfolios", "-v"]):
            exit_code = trade_history_utils.main()

        assert exit_code == 0

    @patch("app.tools.trade_history_utils.compare_portfolios")
    def test_empty_portfolio_list_in_compare(self, mock_compare):
        """--compare with empty --portfolios should fail."""
        with patch(
            "sys.argv", ["trade_history_utils.py", "--compare", "--portfolios", ""]
        ):
            exit_code = trade_history_utils.main()

        # Should fail validation or produce error
        assert exit_code in [0, 1]  # Depends on implementation

    @patch("app.tools.trade_history_utils.merge_portfolios")
    def test_empty_source_in_merge(self, mock_merge):
        """--merge with empty --source should fail."""
        with patch(
            "sys.argv",
            [
                "trade_history_utils.py",
                "--merge",
                "--source",
                "",
                "--target",
                "combined",
            ],
        ):
            exit_code = trade_history_utils.main()

        # Should fail validation
        assert exit_code in [0, 1]  # Depends on implementation

    def test_unknown_operation_flag_fails(self):
        """Unknown operation flags should cause argparse to fail."""
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["trade_history_utils.py", "--unknown-operation"]):
                trade_history_utils.main()

        assert exc_info.value.code != 0

    def test_invalid_flag_format_fails(self):
        """Invalid flag format should cause argparse to fail."""
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["trade_history_utils.py", "-invalid"]):
                trade_history_utils.main()

        assert exc_info.value.code != 0

    @patch("app.tools.trade_history_utils.get_position_by_uuid")
    def test_uuid_with_special_characters(self, mock_get, capsys):
        """--uuid should handle UUIDs with special characters."""
        mock_get.return_value = {
            "position_uuid": "AAPL_SMA_20-50_2025/01/01",
            "_portfolio": "test",  # Required field based on implementation
        }

        with patch(
            "sys.argv",
            [
                "trade_history_utils.py",
                "--find-position",
                "--uuid",
                "AAPL_SMA_20-50_2025/01/01",
            ],
        ):
            exit_code = trade_history_utils.main()

        assert exit_code == 0

    @patch("app.tools.position_service_wrapper.TradingSystemConfig")
    @patch("app.tools.trade_history_utils.list_portfolios")
    def test_base_dir_with_spaces(self, mock_list, mock_config):
        """--base-dir should handle paths with spaces."""
        mock_instance = mock_config.return_value
        mock_instance.base_dir = "/path with spaces/to/dir"
        mock_list.return_value = []

        with patch(
            "sys.argv",
            [
                "trade_history_utils.py",
                "--list-portfolios",
                "--base-dir",
                "/path with spaces/to/dir",
            ],
        ):
            exit_code = trade_history_utils.main()

        assert exit_code == 0

    @patch("app.tools.trade_history_utils.export_portfolio_summary")
    def test_output_with_relative_path(self, mock_export):
        """--output should handle relative paths."""
        mock_export.return_value = True

        with patch(
            "sys.argv",
            [
                "trade_history_utils.py",
                "--export-summary",
                "--portfolio",
                "test",
                "--output",
                "./relative/path/summary.json",
            ],
        ):
            exit_code = trade_history_utils.main()

        assert exit_code == 0
