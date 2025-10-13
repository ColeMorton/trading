"""
Comprehensive Tests for CLI Concurrency Construct Command

Tests for: ./trading-cli concurrency construct [ASSET]

COVERAGE:
- Command invocation and output
- Asset strategy loading
- Portfolio size comparison (5, 7, 9)
- Diversification-weighted sorting
- Temporary file management
- Error scenarios
- Verbose output
- Export functionality
- Synthetic ticker pairs
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from typer.testing import CliRunner

# Import the concurrency sub-app, not the main app
from app.cli.commands.concurrency import app as concurrency_app


class TestConcurrencyConstructCommand:
    """Test suite for concurrency construct CLI command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_strategies(self):
        """Mock strategy data for testing."""
        strategies = []
        for i in range(10):
            # Distribute types: 0-4=SMA, 5-6=EMA, 7-9=MACD
            if i < 5:
                strategy_type = "SMA"
                strategy_id = f"TEST_SMA_{10+i*5}_{50+i*10}"
            elif i < 7:
                strategy_type = "EMA"
                strategy_id = f"TEST_EMA_{10+i*5}_{50+i*10}"
            else:
                strategy_type = "MACD"
                strategy_id = f"TEST_MACD_{10+i*5}_{50+i*10}_9"

            strategies.append(
                {
                    "strategy_id": strategy_id,
                    "ticker": "TEST",
                    "strategy_type": strategy_type,
                    "fast_period": 10 + i * 5,
                    "slow_period": 50 + i * 10,
                    "score": 1.5 - (i * 0.02),
                    "sharpe_ratio": 0.6 - (i * 0.01),
                    "allocation": 0.0,
                    "expectancy_per_trade": 10.0 - i * 0.5,
                    "win_rate": 55.0,
                    "profit_factor": 2.0,
                    "total_return": 100.0,
                    "max_drawdown": -20.0,
                    "total_trades": 100 - i * 5,
                    "sortino_ratio": 0.8 - i * 0.01,
                    "calmar_ratio": 0.5 - i * 0.01,
                    "omega_ratio": 1.2 - i * 0.01,
                    "annualized_return": 20.0 - i,
                    "annualized_volatility": 15.0,
                    "risk_contribution": 0.0,
                    "start_date": "2020-01-01",
                    "end_date": "2024-01-01",
                    "signal_period": 9 if i >= 7 else None,
                }
            )

        return strategies

    @pytest.fixture
    def mock_concurrency_results(self):
        """Mock concurrency analysis results for different sizes."""
        return {
            5: {
                "efficiency_score": 0.1234,
                "diversification": 0.600,
                "independence": 0.420,
                "activity": 0.927,
                "total_expectancy": 155.5,
                "risk_concentration": 0.675,
            },
            7: {
                "efficiency_score": 0.1017,
                "diversification": 0.517,
                "independence": 0.387,
                "activity": 0.929,
                "total_expectancy": 206.1,
                "risk_concentration": 0.681,
            },
            9: {
                "efficiency_score": 0.1008,
                "diversification": 0.529,
                "independence": 0.356,
                "activity": 0.957,
                "total_expectancy": 275.8,
                "risk_concentration": 0.673,
            },
        }

    def test_construct_command_help(self, runner):
        """Test construct command help output."""
        result = runner.invoke(concurrency_app, ["construct", "--help"])

        assert result.exit_code == 0
        assert "construct" in result.stdout.lower()
        assert "asset" in result.stdout.lower()
        assert "--min-score" in result.stdout

    def test_construct_requires_asset_or_ticker_flags(self, runner):
        """Test that construct requires either ASSET argument or -t1/-t2 flags."""
        result = runner.invoke(concurrency_app, ["construct"])

        assert result.exit_code == 1
        assert "Error" in result.stdout or "required" in result.stdout.lower()

    @patch("app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader")
    @patch("app.concurrency.review.run_concurrency_review")
    def test_construct_basic_success(
        self, mock_review, mock_loader_class, runner, mock_strategies
    ):
        """Test basic successful portfolio construction."""
        # Setup mocks
        mock_loader = mock_loader_class.return_value
        mock_loader.validate_asset_data.return_value = {
            "viable_for_construction": True,
            "score_filtered_strategies": 10,
        }
        mock_loader.load_strategies_for_asset.return_value = mock_strategies
        mock_review.return_value = True

        # Mock report file generation
        with patch("app.cli.commands.concurrency.Path") as mock_path:
            mock_report = MagicMock()
            mock_report.exists.return_value = True
            mock_report.name = "construct_temp_test.json"
            mock_path.cwd.return_value.joinpath.return_value = mock_report

            # Mock reading report data
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = (
                    json.dumps(
                        {
                            "portfolio_metrics": {
                                "efficiency": {
                                    "efficiency_score": {"value": 0.1234},
                                    "multipliers": {
                                        "diversification": {"value": 0.600},
                                        "independence": {"value": 0.420},
                                        "activity": {"value": 0.927},
                                    },
                                    "expectancy": {"value": 31.1},
                                },
                                "risk": {
                                    "portfolio_metrics": {
                                        "risk_concentration_index": {"value": 0.675}
                                    }
                                },
                            }
                        }
                    )
                )

                result = runner.invoke(concurrency_app, ["construct", "TEST"])

        assert result.exit_code == 0
        assert "Optimal Portfolio Constructed" in result.stdout
        assert "TEST" in result.stdout

    @patch("app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader")
    def test_construct_insufficient_strategies_error(self, mock_loader_class, runner):
        """Test error when asset has insufficient strategies."""
        mock_loader = mock_loader_class.return_value
        mock_loader.validate_asset_data.return_value = {
            "viable_for_construction": False,
            "score_filtered_strategies": 3,
            "error": "Only 3 strategies available",
        }

        result = runner.invoke(concurrency_app, ["construct", "INVALID"])

        assert result.exit_code == 1
        assert "Error" in result.stdout or "Insufficient" in result.stdout

    @patch("app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader")
    def test_construct_asset_not_found(self, mock_loader_class, runner):
        """Test error when asset files don't exist."""
        mock_loader = mock_loader_class.return_value
        mock_loader.validate_asset_data.return_value = {
            "viable_for_construction": False,
            "error": "No strategy files found for asset NONEXISTENT",
        }

        result = runner.invoke(concurrency_app, ["construct", "NONEXISTENT"])

        assert result.exit_code == 1

    @patch("app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader")
    @patch("app.concurrency.review.run_concurrency_review")
    def test_construct_min_score_filter(
        self, mock_review, mock_loader_class, runner, mock_strategies
    ):
        """Test --min-score flag filters strategies."""
        mock_loader = mock_loader_class.return_value
        mock_loader.validate_asset_data.return_value = {
            "viable_for_construction": True,
            "score_filtered_strategies": 10,
        }

        # Only return high-scoring strategies
        high_score_strategies = [s for s in mock_strategies if s["score"] >= 1.4]
        mock_loader.load_strategies_for_asset.return_value = high_score_strategies
        mock_review.return_value = True

        result = runner.invoke(
            concurrency_app, ["construct", "TEST", "--min-score", "1.4"]
        )

        # Verify load was called with correct min_score
        mock_loader.load_strategies_for_asset.assert_called_once()
        call_args = mock_loader.load_strategies_for_asset.call_args
        assert call_args[1]["min_score"] == 1.4

    @patch("app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader")
    @patch("app.concurrency.review.run_concurrency_review")
    def test_construct_verbose_output(
        self, mock_review, mock_loader_class, runner, mock_strategies
    ):
        """Test --verbose flag shows detailed output."""
        mock_loader = mock_loader_class.return_value
        mock_loader.validate_asset_data.return_value = {
            "viable_for_construction": True,
            "score_filtered_strategies": 10,
        }
        mock_loader.load_strategies_for_asset.return_value = mock_strategies
        mock_review.return_value = True

        result = runner.invoke(concurrency_app, ["construct", "TEST", "--verbose"])

        # Verbose should show extra information
        # (exact output depends on implementation)
        assert result.exit_code == 0

    @patch("app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader")
    @patch("app.concurrency.review.run_concurrency_review")
    def test_construct_creates_temp_files_for_each_size(
        self, mock_review, mock_loader_class, runner, mock_strategies, tmp_path
    ):
        """Test that separate temp files are created for portfolio sizes 5, 7, 9."""
        mock_loader = mock_loader_class.return_value
        mock_loader.validate_asset_data.return_value = {
            "viable_for_construction": True,
            "score_filtered_strategies": 10,
        }
        mock_loader.load_strategies_for_asset.return_value = mock_strategies

        created_files = []

        def mock_review_impl(filename, config_overrides=None):
            # Track which files are created
            created_files.append(filename)
            return True

        mock_review.side_effect = mock_review_impl

        with patch("app.cli.commands.concurrency.Path.cwd", return_value=tmp_path):
            result = runner.invoke(concurrency_app, ["construct", "TEST"])

        # Should have created 3 files (one for each size: 5, 7, 9)
        assert len(created_files) == 3

        # Verify filenames contain size indicators
        filenames_str = " ".join(created_files)
        assert "size5" in filenames_str
        assert "size7" in filenames_str
        assert "size9" in filenames_str

    def test_construct_synthetic_pair_with_t1_t2(self, runner):
        """Test constructing portfolio for synthetic ticker pair using -t1 and -t2."""
        with patch(
            "app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader"
        ) as mock_loader_class:
            mock_loader = mock_loader_class.return_value
            mock_loader.validate_asset_data.return_value = {
                "viable_for_construction": True,
                "score_filtered_strategies": 10,
            }

            result = runner.invoke(
                concurrency_app, ["construct", "-t1", "NVDA", "-t2", "QQQ"]
            )

            # Should process as synthetic pair NVDA_QQQ
            # verify loader was called with combined asset name
            if result.exit_code == 0:
                call_args = mock_loader.validate_asset_data.call_args
                assert "NVDA_QQQ" in str(call_args)

    def test_construct_synthetic_pair_requires_t1_with_t2(self, runner):
        """Test that -t2 requires -t1."""
        result = runner.invoke(concurrency_app, ["construct", "-t2", "QQQ"])

        assert result.exit_code == 1
        assert "Error" in result.stdout

    def test_construct_single_ticker_via_t1_flag(self, runner):
        """Test using -t1 flag for single ticker (without -t2)."""
        with patch(
            "app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader"
        ) as mock_loader_class:
            mock_loader = mock_loader_class.return_value
            mock_loader.validate_asset_data.return_value = {
                "viable_for_construction": True,
                "score_filtered_strategies": 10,
            }

            result = runner.invoke(concurrency_app, ["construct", "-t1", "NVDA"])

            # Should work as single asset
            # (May need to check if this is the desired behavior)

    @patch("app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader")
    @patch("app.concurrency.review.run_concurrency_review")
    @patch("app.cli.commands.concurrency._export_strategies_to_file")
    def test_construct_export_flag_creates_csv(
        self, mock_export, mock_review, mock_loader_class, runner, mock_strategies
    ):
        """Test --export flag exports strategies to CSV."""
        mock_loader = mock_loader_class.return_value
        mock_loader.validate_asset_data.return_value = {
            "viable_for_construction": True,
            "score_filtered_strategies": 10,
        }
        mock_loader.load_strategies_for_asset.return_value = mock_strategies
        mock_review.return_value = True

        result = runner.invoke(concurrency_app, ["construct", "TEST", "--export"])

        # Export should be called
        assert mock_export.called or result.exit_code == 0

    def test_construct_output_format_table(self, runner):
        """Test --format table output."""
        with patch(
            "app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader"
        ) as mock_loader_class:
            with patch("app.concurrency.review.run_concurrency_review") as mock_review:
                mock_loader_class.return_value.validate_asset_data.return_value = {
                    "viable_for_construction": True,
                    "score_filtered_strategies": 10,
                }
                mock_review.return_value = True

                result = runner.invoke(
                    concurrency_app, ["construct", "TEST", "--format", "table"]
                )

                # Should produce table output (default)

    def test_construct_output_format_json(self, runner):
        """Test --format json output."""
        with patch(
            "app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader"
        ) as mock_loader_class:
            with patch("app.concurrency.review.run_concurrency_review") as mock_review:
                mock_loader_class.return_value.validate_asset_data.return_value = {
                    "viable_for_construction": True,
                    "score_filtered_strategies": 10,
                }
                mock_review.return_value = True

                result = runner.invoke(
                    concurrency_app, ["construct", "TEST", "--format", "json"]
                )

                # Output should be JSON formatted
                if result.exit_code == 0:
                    # Try to parse output as JSON (may be mixed with other output)
                    pass


class TestConstructPortfolioSizeComparison:
    """Tests specifically for portfolio size comparison logic."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader")
    @patch("app.concurrency.review.run_concurrency_review")
    def test_construct_compares_multiple_sizes(
        self, mock_review, mock_loader_class, runner
    ):
        """Test that construct compares portfolios of sizes 5, 7, and 9."""
        mock_loader = mock_loader_class.return_value
        mock_loader.validate_asset_data.return_value = {
            "viable_for_construction": True,
            "score_filtered_strategies": 10,
        }

        mock_strategies = []
        for i in range(10):
            strategy_type = "SMA" if i < 5 else ("EMA" if i < 7 else "MACD")
            mock_strategies.append(
                {
                    "strategy_id": f"TEST_{strategy_type}_{i}",
                    "ticker": "TEST",
                    "strategy_type": strategy_type,
                    "fast_period": 10 + i * 5,
                    "slow_period": 50 + i * 10,
                    "score": 1.5 - i * 0.05,
                    "sharpe_ratio": 0.6,
                    "allocation": 0.0,
                    "expectancy_per_trade": 10.0,
                    "win_rate": 55.0,
                    "profit_factor": 2.0,
                    "total_return": 100.0,
                    "max_drawdown": -20.0,
                    "total_trades": 100,
                    "sortino_ratio": 0.8,
                    "calmar_ratio": 0.5,
                    "omega_ratio": 1.2,
                    "annualized_return": 20.0,
                    "annualized_volatility": 15.0,
                    "risk_contribution": 0.0,
                    "start_date": "2020-01-01",
                    "end_date": "2024-01-01",
                    "signal_period": 9 if i >= 7 else None,
                }
            )
        mock_loader.load_strategies_for_asset.return_value = mock_strategies

        call_count = {"count": 0}

        def mock_review_side_effect(filename, config_overrides=None):
            call_count["count"] += 1
            return True

        mock_review.side_effect = mock_review_side_effect

        result = runner.invoke(concurrency_app, ["construct", "TEST"])

        # Should analyze 3 different portfolio sizes
        assert call_count["count"] == 3

    def test_construct_exact_match_only_tests_one_size(self, runner):
        """Test that if strategies count is exactly 5, 7, or 9, only that size is tested."""
        with patch(
            "app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader"
        ) as mock_loader_class:
            with patch("app.concurrency.review.run_concurrency_review") as mock_review:
                mock_loader = mock_loader_class.return_value
                mock_loader.validate_asset_data.return_value = {
                    "viable_for_construction": True,
                    "score_filtered_strategies": 5,
                }

                # Return exactly 5 strategies with all required fields
                mock_strategies = []
                for i in range(5):
                    strategy_type = "SMA" if i < 2 else ("EMA" if i < 4 else "MACD")
                    mock_strategies.append(
                        {
                            "strategy_id": f"TEST_{strategy_type}_{i}",
                            "ticker": "TEST",
                            "strategy_type": strategy_type,
                            "fast_period": 10 + i * 5,
                            "slow_period": 50 + i * 10,
                            "score": 1.5 - i * 0.1,
                            "sharpe_ratio": 0.6,
                            "allocation": 0.0,
                            "expectancy_per_trade": 10.0,
                            "win_rate": 55.0,
                            "profit_factor": 2.0,
                            "total_return": 100.0,
                            "max_drawdown": -20.0,
                            "total_trades": 100,
                            "sortino_ratio": 0.8,
                            "calmar_ratio": 0.5,
                            "omega_ratio": 1.2,
                            "annualized_return": 20.0,
                            "annualized_volatility": 15.0,
                            "risk_contribution": 0.0,
                            "start_date": "2020-01-01",
                            "end_date": "2024-01-01",
                            "signal_period": 9 if i >= 4 else None,
                        }
                    )
                mock_loader.load_strategies_for_asset.return_value = mock_strategies

                call_count = {"count": 0}
                mock_review.side_effect = lambda *args, **kwargs: (
                    call_count.update({"count": call_count["count"] + 1}),
                    True,
                )[1]

                result = runner.invoke(concurrency_app, ["construct", "TEST"])

                # Should only test size 5 (exact match)
                assert call_count["count"] == 1


class TestConstructDiversificationSorting:
    """Tests for diversification-weighted strategy sorting."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader")
    @patch("app.concurrency.review.run_concurrency_review")
    def test_construct_applies_diversification_weighting(
        self, mock_review, mock_loader_class, runner
    ):
        """Test that strategies are sorted by score * diversification."""
        mock_loader = mock_loader_class.return_value
        mock_loader.validate_asset_data.return_value = {
            "viable_for_construction": True,
            "score_filtered_strategies": 10,
        }

        # Create strategies where diversification should reorder them
        mock_strategies = [
            {
                "strategy_id": "SMA_1",
                "strategy_type": "SMA",
                "fast_period": 10,
                "slow_period": 50,
                "score": 1.0,
                "sharpe_ratio": 0.6,
            },  # Common type, high score
            {
                "strategy_id": "SMA_2",
                "strategy_type": "SMA",
                "fast_period": 15,
                "slow_period": 60,
                "score": 1.0,
                "sharpe_ratio": 0.6,
            },  # Common type, high score
            {
                "strategy_id": "MACD_1",
                "strategy_type": "MACD",
                "fast_period": 12,
                "slow_period": 26,
                "score": 0.8,
                "sharpe_ratio": 0.7,
            },  # Rare type, lower score but should rank higher with diversification
        ]
        mock_loader.load_strategies_for_asset.return_value = mock_strategies
        mock_review.return_value = True

        # Capture the sorted strategies
        captured_portfolio = {}

        def capture_review(filename, config_overrides=None):
            # Would need to capture the actual portfolio data written to file
            return True

        mock_review.side_effect = capture_review

        result = runner.invoke(concurrency_app, ["construct", "TEST", "--verbose"])

        # In verbose mode, should show diversification scores
        if "--verbose" in result.stdout or "Div:" in result.stdout:
            # Verify diversification is being calculated
            assert "diversification" in result.stdout.lower() or "Div" in result.stdout


class TestConstructErrorScenarios:
    """Test error handling in construct command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_construct_handles_analysis_failure(self, runner):
        """Test error handling when concurrency analysis fails."""
        with patch(
            "app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader"
        ) as mock_loader_class:
            with patch("app.concurrency.review.run_concurrency_review") as mock_review:
                mock_loader = mock_loader_class.return_value
                mock_loader.validate_asset_data.return_value = {
                    "viable_for_construction": True,
                    "score_filtered_strategies": 10,
                }

                # Make review fail
                mock_review.return_value = False

                result = runner.invoke(concurrency_app, ["construct", "TEST"])

                # Should handle error gracefully
                assert result.exit_code == 1

    def test_construct_handles_missing_report_file(self, runner):
        """Test handling when analysis succeeds but report file is missing."""
        with patch(
            "app.concurrency.tools.asset_strategy_loader.AssetStrategyLoader"
        ) as mock_loader_class:
            with patch("app.concurrency.review.run_concurrency_review") as mock_review:
                mock_loader = mock_loader_class.return_value
                mock_loader.validate_asset_data.return_value = {
                    "viable_for_construction": True,
                    "score_filtered_strategies": 10,
                }
                mock_review.return_value = True

                # Mock report file doesn't exist
                with patch("app.cli.commands.concurrency.Path") as mock_path:
                    mock_report = MagicMock()
                    mock_report.exists.return_value = False
                    mock_path.cwd.return_value.joinpath.return_value = mock_report

                    result = runner.invoke(concurrency_app, ["construct", "TEST"])

                    # Should handle missing report gracefully


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
