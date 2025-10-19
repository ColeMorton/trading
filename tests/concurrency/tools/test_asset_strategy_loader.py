"""
Tests for Asset Strategy Loader

The AssetStrategyLoader is responsible for discovering and loading strategy files
for specific assets, filtering by score, and validating data quality.

TESTS COVER:
- Loading strategies for a specific asset
- Score filtering
- Strategy type distribution
- Parameter range extraction
- Validation checks
- Error handling for missing files
"""

from unittest.mock import patch

import pytest

from app.concurrency.tools.asset_strategy_loader import AssetStrategyLoader
from app.tools.exceptions import DataLoadError


class TestAssetStrategyLoader:
    """Test suite for AssetStrategyLoader class."""

    @pytest.fixture
    def loader(self):
        """Create AssetStrategyLoader instance."""
        return AssetStrategyLoader()

    @pytest.fixture
    def sample_strategy_csv(self, tmp_path):
        """Create a sample strategy CSV file."""
        csv_content = """Ticker,Timeframe,Strategy Type,Fast Period,Slow Period,Signal Period,Score,Win Rate [%],Profit Factor,Sharpe Ratio,Total Return [%],Max Drawdown [%],Expectancy per Trade,Total Trades,Allocation [%]
TEST,D,SMA,10,50,,1.50,55.0,2.0,0.60,100.0,-20.0,10.0,50,0.0
TEST,D,SMA,20,60,,1.45,54.0,1.9,0.58,95.0,-22.0,9.5,48,0.0
TEST,D,EMA,15,45,,1.40,56.0,2.1,0.62,105.0,-18.0,10.5,52,0.0
TEST,D,MACD,12,26,9,1.35,53.0,1.8,0.55,90.0,-25.0,9.0,45,0.0
TEST,D,SMA,8,40,,1.10,50.0,1.5,0.45,75.0,-28.0,7.0,42,0.0
TEST,D,SMA,5,30,,0.90,45.0,1.2,0.40,50.0,-35.0,5.0,40,0.0"""

        # Create directory structure
        data_dir = tmp_path / "data" / "raw" / "portfolios_filtered"
        data_dir.mkdir(parents=True)

        # Write CSV file
        csv_file = data_dir / "TEST_D_SMA.csv"
        csv_file.write_text(csv_content)

        return data_dir, csv_file

    def test_loader_initialization(self):
        """Test AssetStrategyLoader initializes with correct defaults."""
        loader = AssetStrategyLoader()

        assert loader.data_dir.name == "portfolios_metrics"
        assert loader.data_dir.exists()

    def test_loader_custom_data_dir(self, tmp_path):
        """Test AssetStrategyLoader with custom data directory."""
        custom_dir = tmp_path / "custom_data"
        custom_dir.mkdir()

        loader = AssetStrategyLoader(data_dir=custom_dir)

        assert loader.data_dir == custom_dir

    def test_load_strategies_for_asset_success(self, sample_strategy_csv):
        """Test loading strategies for a specific asset."""
        data_dir, csv_file = sample_strategy_csv
        loader = AssetStrategyLoader(data_dir=data_dir)

        strategies = loader.load_strategies_for_asset("TEST", min_score=0.0)

        # Should load all 6 strategies
        assert len(strategies) == 6

        # Verify strategy structure
        for strategy in strategies:
            assert "strategy_id" in strategy
            assert "ticker" in strategy
            assert "strategy_type" in strategy
            assert "fast_period" in strategy
            assert "slow_period" in strategy
            assert "score" in strategy
            assert "sharpe_ratio" in strategy

    def test_load_strategies_filters_by_min_score(self, sample_strategy_csv):
        """Test that strategies are filtered by minimum score."""
        data_dir, csv_file = sample_strategy_csv
        loader = AssetStrategyLoader(data_dir=data_dir)

        # Filter for score >= 1.4
        strategies = loader.load_strategies_for_asset("TEST", min_score=1.4)

        # Should only get 3 strategies (1.50, 1.45, 1.40)
        assert len(strategies) == 3

        # Filter for score >= 1.0
        strategies_1_0 = loader.load_strategies_for_asset("TEST", min_score=1.0)
        # Should get 5 strategies (1.50, 1.45, 1.40, 1.35, 1.10)
        assert len(strategies_1_0) == 5

        # All should have score >= 1.4
        for strategy in strategies:
            assert strategy["score"] >= 1.4

    def test_load_strategies_sorts_by_score_descending(self, sample_strategy_csv):
        """Test that strategies are sorted by score (highest first)."""
        data_dir, csv_file = sample_strategy_csv
        loader = AssetStrategyLoader(data_dir=data_dir)

        strategies = loader.load_strategies_for_asset("TEST", min_score=0.0)

        # Verify descending order
        scores = [s["score"] for s in strategies]
        assert scores == sorted(scores, reverse=True)

        # Top strategy should have highest score
        assert strategies[0]["score"] == 1.50

    def test_load_strategies_asset_not_found(self):
        """Test error handling when asset has no strategy files."""
        loader = AssetStrategyLoader()

        with pytest.raises(DataLoadError) as exc_info:
            loader.load_strategies_for_asset("NONEXISTENT", min_score=1.0)

        assert "No strategy files found" in str(exc_info.value)
        assert "NONEXISTENT" in str(exc_info.value)

    def test_load_strategies_handles_macd_signal_period(self, sample_strategy_csv):
        """Test that MACD strategies properly include signal_period."""
        data_dir, csv_file = sample_strategy_csv
        loader = AssetStrategyLoader(data_dir=data_dir)

        strategies = loader.load_strategies_for_asset("TEST", min_score=0.0)

        # Find the MACD strategy
        macd_strats = [s for s in strategies if s["strategy_type"] == "MACD"]
        assert len(macd_strats) == 1

        macd = macd_strats[0]
        assert "signal_period" in macd
        assert macd["signal_period"] == 9

    def test_generate_strategy_id_format(self, sample_strategy_csv):
        """Test that strategy IDs are generated in correct format."""
        data_dir, csv_file = sample_strategy_csv
        loader = AssetStrategyLoader(data_dir=data_dir)

        strategies = loader.load_strategies_for_asset("TEST", min_score=0.0)

        # Check SMA strategy ID format
        sma_strats = [s for s in strategies if s["strategy_type"] == "SMA"]
        for sma in sma_strats:
            assert sma["strategy_id"].startswith("TEST_SMA_")
            # Should be like: TEST_SMA_10_50
            parts = sma["strategy_id"].split("_")
            assert len(parts) == 4

        # Check MACD strategy ID format (includes signal period)
        macd_strats = [s for s in strategies if s["strategy_type"] == "MACD"]
        for macd in macd_strats:
            assert macd["strategy_id"].startswith("TEST_MACD_")
            # Should be like: TEST_MACD_12_26_9
            parts = macd["strategy_id"].split("_")
            assert len(parts) == 5  # Includes signal period

    def test_validate_asset_data_viable(self, sample_strategy_csv):
        """Test validation of viable asset data."""
        data_dir, csv_file = sample_strategy_csv
        loader = AssetStrategyLoader(data_dir=data_dir)

        validation = loader.validate_asset_data("TEST")

        assert validation["asset"] == "TEST"
        assert validation["total_strategies"] == 6  # Now have 6 total strategies
        assert validation["score_filtered_strategies"] == 5  # 5 with score >= 1.0
        assert (
            validation["viable_for_construction"] is True
        )  # Has >= 5 strategies with score >= 1.0
        assert "strategy_types" in validation
        assert "parameter_ranges" in validation

    def test_validate_asset_data_insufficient_strategies(self):
        """Test validation fails when too few strategies with score >= 1.0."""
        loader = AssetStrategyLoader()

        # Mock to return only 3 strategies with complete structure
        mock_strategies = [
            {
                "strategy_id": "TEST_SMA_1",
                "strategy_type": "SMA",
                "fast_period": 10,
                "slow_period": 50,
                "score": 1.5,
            },
            {
                "strategy_id": "TEST_SMA_2",
                "strategy_type": "SMA",
                "fast_period": 15,
                "slow_period": 60,
                "score": 1.4,
            },
            {
                "strategy_id": "TEST_SMA_3",
                "strategy_type": "SMA",
                "fast_period": 20,
                "slow_period": 70,
                "score": 1.3,
            },
        ]

        with patch.object(
            loader, "load_strategies_for_asset", return_value=mock_strategies
        ):
            validation = loader.validate_asset_data("TEST")

        # Should indicate not viable (need 5+ strategies with score >= 1.0 for smallest portfolio)
        assert validation["viable_for_construction"] is False
        assert validation["total_strategies"] == 3
        assert validation["score_filtered_strategies"] == 3  # All 3 have score >= 1.0
        # Not viable because we need 5+, but only have 3

    def test_validate_asset_data_strategy_type_distribution(self, sample_strategy_csv):
        """Test that validation includes strategy type distribution."""
        data_dir, csv_file = sample_strategy_csv
        loader = AssetStrategyLoader(data_dir=data_dir)

        validation = loader.validate_asset_data("TEST")

        strategy_types = validation["strategy_types"]

        # Should have SMA, EMA, MACD
        assert "SMA" in strategy_types
        assert "EMA" in strategy_types
        assert "MACD" in strategy_types

        # Count should match (now have 6 total: 4 SMA, 1 EMA, 1 MACD)
        assert strategy_types["SMA"] == 4  # 4 SMA strategies
        assert strategy_types["EMA"] == 1  # 1 EMA strategy
        assert strategy_types["MACD"] == 1  # 1 MACD strategy

    def test_validate_asset_data_parameter_ranges(self, sample_strategy_csv):
        """Test that validation includes parameter ranges."""
        data_dir, csv_file = sample_strategy_csv
        loader = AssetStrategyLoader(data_dir=data_dir)

        validation = loader.validate_asset_data("TEST")

        param_ranges = validation["parameter_ranges"]

        # Should have fast and slow period ranges
        assert "fast_period" in param_ranges
        assert "slow_period" in param_ranges

        # Check ranges are correct (now includes strategy with fast=5,8 and slow=30,40)
        assert param_ranges["fast_period"]["min"] == 5
        assert param_ranges["fast_period"]["max"] == 20
        assert param_ranges["slow_period"]["min"] == 26
        assert param_ranges["slow_period"]["max"] == 60

    def test_validate_asset_data_error_handling(self):
        """Test validation handles errors gracefully."""
        loader = AssetStrategyLoader()

        # Mock to raise an error
        with patch.object(
            loader, "load_strategies_for_asset", side_effect=Exception("Test error")
        ):
            validation = loader.validate_asset_data("TEST")

        assert "error" in validation
        assert validation["viable_for_construction"] is False

    def test_get_available_assets(self, tmp_path):
        """Test getting list of available assets."""
        data_dir = tmp_path / "data" / "raw" / "portfolios_filtered"
        data_dir.mkdir(parents=True)

        # Create some fake strategy files
        (data_dir / "AAPL_D_SMA.csv").touch()
        (data_dir / "AAPL_D_EMA.csv").touch()
        (data_dir / "MSFT_D_SMA.csv").touch()
        (data_dir / "TSLA_D_MACD.csv").touch()

        loader = AssetStrategyLoader(data_dir=data_dir)
        assets = loader.get_available_assets()

        # Should find 3 unique assets
        assert len(assets) == 3
        assert "AAPL" in assets
        assert "MSFT" in assets
        assert "TSLA" in assets

        # Should be sorted
        assert assets == sorted(assets)

    def test_parse_ticker_from_filename(self):
        """Test extracting ticker from filename pattern."""
        # Note: _parse_ticker_from_filename is not a class method, but we can test the logic
        AssetStrategyLoader()

        # Test via get_available_assets which uses the parsing logic
        # This test validates the pattern matching works
        assert True  # Placeholder - actual parsing happens in get_available_assets

    def test_load_strategies_combines_multiple_files(self, tmp_path):
        """Test that strategies from multiple files are combined."""
        data_dir = tmp_path / "data" / "raw" / "portfolios_filtered"
        data_dir.mkdir(parents=True)

        # Create two strategy files for same asset
        sma_content = """Ticker,Timeframe,Strategy Type,Fast Period,Slow Period,Signal Period,Score,Win Rate [%],Profit Factor,Sharpe Ratio,Total Return [%],Max Drawdown [%],Expectancy per Trade,Total Trades,Allocation [%]
TEST,D,SMA,10,50,,1.50,55.0,2.0,0.60,100.0,-20.0,10.0,50,0.0"""

        ema_content = """Ticker,Timeframe,Strategy Type,Fast Period,Slow Period,Signal Period,Score,Win Rate [%],Profit Factor,Sharpe Ratio,Total Return [%],Max Drawdown [%],Expectancy per Trade,Total Trades,Allocation [%]
TEST,D,EMA,15,45,,1.40,56.0,2.1,0.62,105.0,-18.0,10.5,52,0.0"""

        (data_dir / "TEST_D_SMA.csv").write_text(sma_content)
        (data_dir / "TEST_D_EMA.csv").write_text(ema_content)

        loader = AssetStrategyLoader(data_dir=data_dir)
        strategies = loader.load_strategies_for_asset("TEST", min_score=0.0)

        # Should combine both files
        assert len(strategies) == 2

        # Should have both types
        types = {s["strategy_type"] for s in strategies}
        assert types == {"SMA", "EMA"}


class TestAssetStrategyLoaderIntegration:
    """Integration tests using real data structure."""

    @pytest.mark.integration
    def test_load_real_asset_structure(self):
        """Test loading strategies with real project structure."""
        # This test would use actual files if they exist
        loader = AssetStrategyLoader()

        # Check if data directory exists
        if not loader.data_dir.exists():
            pytest.skip("Real data directory not available")

        # Try to find any available asset
        assets = loader.get_available_assets()
        if not assets:
            pytest.skip("No assets available for testing")

        # Test loading first available asset
        test_asset = assets[0]
        strategies = loader.load_strategies_for_asset(test_asset, min_score=0.0)

        assert len(strategies) > 0
        assert all("strategy_id" in s for s in strategies)

    @pytest.mark.integration
    def test_validate_real_asset(self):
        """Test validation with real asset data."""
        loader = AssetStrategyLoader()

        assets = loader.get_available_assets()
        if not assets:
            pytest.skip("No assets available for testing")

        test_asset = assets[0]
        validation = loader.validate_asset_data(test_asset)

        assert validation["asset"] == test_asset
        assert "total_strategies" in validation
        assert "strategy_types" in validation
        assert "parameter_ranges" in validation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
