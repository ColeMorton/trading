"""
Test Suite for Strategy Template Generator

Comprehensive tests for the template-based strategy development system.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.tools.strategy.template import (
    ExecutionTemplate,
    IndicatorType,
    StrategyTemplateGenerator,
    StrategyType,
    TemplateConfig,
    ValidationTemplate,
)


class TestTemplateConfig:
    """Test template configuration system."""

    def test_template_config_creation(self):
        """Test basic template configuration creation."""
        config = TemplateConfig(
            strategy_name="test_strategy",
            strategy_type=StrategyType.RSI,
            description="Test RSI strategy",
            primary_indicator=IndicatorType.RSI,
            secondary_indicators=[IndicatorType.SMA],
            entry_conditions=["RSI below 30"],
            exit_conditions=["RSI above 70"],
        )

        assert config.strategy_name == "test_strategy"
        assert config.strategy_type == StrategyType.RSI
        assert config.primary_indicator == IndicatorType.RSI
        assert len(config.secondary_indicators) == 1
        assert config.stop_loss_enabled is True  # Default
        assert config.take_profit_enabled is True  # Default

    def test_template_config_defaults(self):
        """Test template configuration default values."""
        config = TemplateConfig(
            strategy_name="minimal_strategy",
            strategy_type=StrategyType.CUSTOM,
            description="Minimal strategy",
            primary_indicator=IndicatorType.SMA,
            secondary_indicators=[],
            entry_conditions=["Custom entry"],
            exit_conditions=["Custom exit"],
        )

        # Check defaults
        assert config.default_ticker == "AAPL"
        assert config.default_timeframe == "daily"
        assert config.default_lookback_period == 252
        assert config.position_sizing == "fixed"
        assert config.use_machine_learning is False

    def test_config_type_definition_generation(self):
        """Test TypedDict definition generation."""
        config = TemplateConfig(
            strategy_name="test_strategy",
            strategy_type=StrategyType.MOVING_AVERAGE,
            description="Test MA strategy",
            primary_indicator=IndicatorType.SMA,
            secondary_indicators=[],
            entry_conditions=["MA crossover"],
            exit_conditions=["MA cross under"],
        )

        typedef = config.get_config_type_definition()

        assert "class TestStrategyConfig(TypedDict):" in typedef
        assert "TICKER: List[str]" in typedef
        assert "SHORT_WINDOW: int" in typedef
        assert "LONG_WINDOW: int" in typedef

    def test_default_config_instance_generation(self):
        """Test default configuration instance generation."""
        config = TemplateConfig(
            strategy_name="test_strategy",
            strategy_type=StrategyType.RSI,
            description="Test RSI strategy",
            primary_indicator=IndicatorType.RSI,
            secondary_indicators=[],
            entry_conditions=["RSI entry"],
            exit_conditions=["RSI exit"],
        )

        instance = config.get_default_config_instance()

        assert "DEFAULT_CONFIG: TestStrategyConfig = {" in instance
        assert '"RSI_PERIOD": 14' in instance
        assert '"RSI_OVERBOUGHT": 70' in instance
        assert '"RSI_OVERSOLD": 30' in instance

    def test_strategy_specific_imports(self):
        """Test strategy-specific import generation."""
        config = TemplateConfig(
            strategy_name="test_strategy",
            strategy_type=StrategyType.MACD,
            description="Test MACD strategy",
            primary_indicator=IndicatorType.MACD,
            secondary_indicators=[IndicatorType.RSI, IndicatorType.SMA],
            entry_conditions=["MACD entry"],
            exit_conditions=["MACD exit"],
        )

        imports = config.get_strategy_specific_imports()

        assert "from ta.trend import MACD" in imports
        assert "from ta.momentum import RSIIndicator" in imports
        assert "from ta.trend import SMAIndicator" in imports


class TestExecutionTemplate:
    """Test execution template generation."""

    def setup_method(self):
        """Set up test configuration."""
        self.config = TemplateConfig(
            strategy_name="test_execution",
            strategy_type=StrategyType.RSI,
            description="Test execution strategy",
            primary_indicator=IndicatorType.RSI,
            secondary_indicators=[],
            entry_conditions=["RSI below 30"],
            exit_conditions=["RSI above 70"],
        )
        self.template = ExecutionTemplate(self.config)

    def test_main_execution_file_generation(self):
        """Test main execution file generation."""
        content = self.template.generate_main_execution_file()

        # Check for key components
        assert "Portfolio Analysis Module for TestExecution Strategy" in content
        assert "from app.strategies.test_execution.exceptions import" in content
        assert "def filter_portfolios(" in content
        assert "def execute_all_strategies(" in content
        assert "def run(" in content
        assert "def run_strategies(" in content
        assert 'if __name__ == "__main__":' in content

    def test_strategy_execution_file_generation(self):
        """Test strategy execution file generation."""
        content = self.template.generate_strategy_execution_file()

        # Check for key components
        assert "Strategy Execution Module for TestExecution Strategy" in content
        assert "def calculate_indicators(" in content
        assert "def generate_signals(" in content
        assert "def execute_strategy(" in content
        assert "def validate_strategy_config(" in content

        # Check RSI-specific content
        assert "RSIIndicator" in content
        assert "rsi_overbought" in content
        assert "rsi_oversold" in content

    def test_exceptions_file_generation(self):
        """Test exceptions file generation."""
        content = self.template.generate_exceptions_file()

        # Check for exception classes
        assert "class TestExecutionError(StrategyError):" in content
        assert "class TestExecutionConfigurationError(TestExecutionError):" in content
        assert "class TestExecutionExecutionError(TestExecutionError):" in content
        assert "class TestExecutionPortfolioError(TestExecutionError):" in content

    def test_indicator_calculation_generation(self):
        """Test indicator calculation code generation."""
        # Test different strategy types
        configs = [
            (
                StrategyType.MOVING_AVERAGE,
                ["SMA_Short", "SMA_Long", "EMA_Short", "EMA_Long"],
            ),
            (StrategyType.RSI, ["RSI"]),
            (StrategyType.MACD, ["MACD_Line", "MACD_Signal", "MACD_Histogram"]),
            (StrategyType.BOLLINGER_BANDS, ["BB_Upper", "BB_Middle", "BB_Lower"]),
        ]

        for strategy_type, expected_indicators in configs:
            config = TemplateConfig(
                strategy_name="test_strategy",
                strategy_type=strategy_type,
                description="Test strategy",
                primary_indicator=IndicatorType.SMA,
                secondary_indicators=[],
                entry_conditions=["Test entry"],
                exit_conditions=["Test exit"],
            )

            template = ExecutionTemplate(config)
            indicator_code = template._generate_indicator_calculations()

            for indicator in expected_indicators:
                assert indicator in indicator_code

    def test_signal_logic_generation(self):
        """Test signal logic generation."""
        # Test moving average signals
        ma_config = TemplateConfig(
            strategy_name="test_ma",
            strategy_type=StrategyType.MOVING_AVERAGE,
            description="Test MA strategy",
            primary_indicator=IndicatorType.SMA,
            secondary_indicators=[],
            entry_conditions=["MA crossover"],
            exit_conditions=["MA cross under"],
        )

        template = ExecutionTemplate(ma_config)
        signal_code = template._generate_signal_logic()

        assert "moving average crossover signals" in signal_code
        assert "SMA_Short" in signal_code
        assert "SMA_Long" in signal_code
        assert "Entry_Signal" in signal_code
        assert "Exit_Signal" in signal_code

    def test_config_validation_generation(self):
        """Test configuration validation code generation."""
        validation_code = self.template._generate_config_validation()

        # Check basic validation
        assert "if not config.get('TICKER'):" in validation_code
        assert "raise ValueError('TICKER is required')" in validation_code
        assert "if config.get('DIRECTION') not in ['Long', 'Short']:" in validation_code


class TestValidationTemplate:
    """Test validation template generation."""

    def setup_method(self):
        """Set up test configuration."""
        self.config = TemplateConfig(
            strategy_name="test_validation",
            strategy_type=StrategyType.RSI,
            description="Test validation strategy",
            primary_indicator=IndicatorType.RSI,
            secondary_indicators=[],
            entry_conditions=["RSI below 30"],
            exit_conditions=["RSI above 70"],
        )
        self.template = ValidationTemplate(self.config)

    def test_test_file_generation(self):
        """Test test file generation."""
        content = self.template.generate_test_file()

        # Check for test classes
        assert "class TestTestValidationConfiguration:" in content
        assert "class TestTestValidationIndicators:" in content
        assert "class TestTestValidationSignals:" in content
        assert "class TestTestValidationExecution:" in content
        assert "class TestTestValidationIntegration:" in content
        assert "class TestTestValidationPerformance:" in content

        # Check for imports
        assert "import pytest" in content
        assert "import polars as pl" in content
        assert "from app.strategies.test_validation.config_types import" in content

    def test_benchmark_file_generation(self):
        """Test benchmark file generation."""
        content = self.template.generate_benchmark_file()

        assert "Performance Benchmarks for TestValidation Strategy" in content
        assert "class TestPerformanceBenchmarks:" in content
        assert "def test_indicator_calculation_performance(" in content
        assert "def test_signal_generation_performance(" in content
        assert "def test_memory_usage(" in content
        assert "def test_multiple_ticker_performance(" in content


class TestStrategyTemplateGenerator:
    """Test the main strategy template generator."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create mock project structure
        app_dir = self.temp_path / "app"
        strategies_dir = app_dir / "strategies"
        strategies_dir.mkdir(parents=True)

        self.generator = StrategyTemplateGenerator(str(self.temp_path))

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_generator_initialization(self):
        """Test generator initialization."""
        assert self.generator.base_path == self.temp_path
        assert self.generator.strategies_path == self.temp_path / "app" / "strategies"
        assert self.generator.strategies_path.exists()

    def test_strategy_name_validation(self):
        """Test strategy name validation."""
        # Valid names
        assert self.generator.validate_strategy_name("valid_strategy") is True
        assert self.generator.validate_strategy_name("strategy123") is True
        assert self.generator.validate_strategy_name("my_rsi_strategy") is True

        # Invalid names
        with pytest.raises(ValueError, match="cannot be empty"):
            self.generator.validate_strategy_name("")

        with pytest.raises(ValueError, match="cannot start with a number"):
            self.generator.validate_strategy_name("123strategy")

        with pytest.raises(ValueError, match="reserved name"):
            self.generator.validate_strategy_name("test")

        with pytest.raises(ValueError, match="must contain only"):
            self.generator.validate_strategy_name("strategy-name")

    def test_generate_strategy_dry_run(self):
        """Test strategy generation in dry run mode."""
        config = TemplateConfig(
            strategy_name="test_dry_run",
            strategy_type=StrategyType.RSI,
            description="Test dry run strategy",
            primary_indicator=IndicatorType.RSI,
            secondary_indicators=[],
            entry_conditions=["RSI below 30"],
            exit_conditions=["RSI above 70"],
        )

        result = self.generator.generate_strategy(config, dry_run=True)

        # Should return file contents without creating files
        assert isinstance(result, dict)
        assert "1_get_portfolios.py" in result
        assert "config_types.py" in result
        assert "tools/strategy_execution.py" in result
        assert "exceptions.py" in result
        assert "test_strategy.py" in result

        # Should not create actual files
        strategy_path = self.generator.strategies_path / "test_dry_run"
        assert not strategy_path.exists()

    def test_generate_strategy_success(self):
        """Test successful strategy generation."""
        config = TemplateConfig(
            strategy_name="test_success",
            strategy_type=StrategyType.MOVING_AVERAGE,
            description="Test success strategy",
            primary_indicator=IndicatorType.SMA,
            secondary_indicators=[IndicatorType.EMA],
            entry_conditions=["MA crossover up"],
            exit_conditions=["MA crossover down"],
        )

        result = self.generator.generate_strategy(config, dry_run=False)

        # Check result structure
        assert "strategy_path" in result
        assert "files_created" in result
        assert "file_count" in result

        # Check files were created
        strategy_path = Path(result["strategy_path"])
        assert strategy_path.exists()
        assert (strategy_path / "1_get_portfolios.py").exists()
        assert (strategy_path / "config_types.py").exists()
        assert (strategy_path / "tools" / "strategy_execution.py").exists()
        assert (strategy_path / "exceptions.py").exists()
        assert (strategy_path / "__init__.py").exists()
        assert (strategy_path / "README.md").exists()

        # Check file content
        main_file = strategy_path / "1_get_portfolios.py"
        with open(main_file, "r") as f:
            content = f.read()
            assert "TestSuccess Strategy" in content
            assert "test_success" in content

    def test_generate_strategy_overwrite_protection(self):
        """Test overwrite protection."""
        config = TemplateConfig(
            strategy_name="test_overwrite",
            strategy_type=StrategyType.RSI,
            description="Test overwrite strategy",
            primary_indicator=IndicatorType.RSI,
            secondary_indicators=[],
            entry_conditions=["RSI entry"],
            exit_conditions=["RSI exit"],
        )

        # Create strategy first time
        result1 = self.generator.generate_strategy(config, dry_run=False)
        assert "strategy_path" in result1

        # Try to create again without overwrite
        with pytest.raises(FileExistsError, match="already exists"):
            self.generator.generate_strategy(config, overwrite=False, dry_run=False)

        # Should succeed with overwrite=True
        result2 = self.generator.generate_strategy(
            config, overwrite=True, dry_run=False
        )
        assert result2["strategy_path"] == result1["strategy_path"]

    def test_list_available_strategies(self):
        """Test listing available strategies."""
        # Initially empty
        strategies = self.generator.list_available_strategies()
        assert strategies == []

        # Create a strategy
        config = TemplateConfig(
            strategy_name="test_list",
            strategy_type=StrategyType.RSI,
            description="Test list strategy",
            primary_indicator=IndicatorType.RSI,
            secondary_indicators=[],
            entry_conditions=["RSI entry"],
            exit_conditions=["RSI exit"],
        )

        self.generator.generate_strategy(config, dry_run=False)

        # Should now show the strategy
        strategies = self.generator.list_available_strategies()
        assert "test_list" in strategies

    def test_get_strategy_info(self):
        """Test getting strategy information."""
        # Non-existent strategy
        info = self.generator.get_strategy_info("nonexistent")
        assert info is None

        # Create a strategy
        config = TemplateConfig(
            strategy_name="test_info",
            strategy_type=StrategyType.RSI,
            description="Test info strategy",
            primary_indicator=IndicatorType.RSI,
            secondary_indicators=[],
            entry_conditions=["RSI entry"],
            exit_conditions=["RSI exit"],
        )

        self.generator.generate_strategy(config, dry_run=False)

        # Get info
        info = self.generator.get_strategy_info("test_info")
        assert info is not None
        assert info["name"] == "test_info"
        assert info["exists"] is True
        assert info["tools_dir"] is True

        # Check file information
        files = {f["name"]: f for f in info["files"]}
        assert files["1_get_portfolios.py"]["exists"] is True
        assert files["config_types.py"]["exists"] is True
        assert files["__init__.py"]["exists"] is True


class TestIntegration:
    """Integration tests for the complete template system."""

    def setup_method(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create mock project structure
        app_dir = self.temp_path / "app"
        strategies_dir = app_dir / "strategies"
        strategies_dir.mkdir(parents=True)

        self.generator = StrategyTemplateGenerator(str(self.temp_path))

    def teardown_method(self):
        """Clean up integration test environment."""
        shutil.rmtree(self.temp_dir)

    def test_end_to_end_strategy_creation(self):
        """Test complete end-to-end strategy creation."""
        # Create comprehensive strategy configuration
        config = TemplateConfig(
            strategy_name="comprehensive_test",
            strategy_type=StrategyType.MACD,
            description="Comprehensive MACD strategy with multiple indicators",
            primary_indicator=IndicatorType.MACD,
            secondary_indicators=[
                IndicatorType.RSI,
                IndicatorType.SMA,
                IndicatorType.VOLUME,
            ],
            entry_conditions=[
                "MACD line crosses above signal line",
                "RSI is above 50 (momentum confirmation)",
                "Volume is above 20-day average",
            ],
            exit_conditions=[
                "MACD line crosses below signal line",
                "RSI reaches overbought (70+)",
                "Stop loss or take profit triggered",
            ],
            stop_loss_enabled=True,
            take_profit_enabled=True,
            position_sizing="kelly",
            default_ticker="GOOGL",
            default_timeframe="hourly",
        )

        # Generate strategy
        result = self.generator.generate_strategy(config, dry_run=False)

        # Verify all files exist and have expected content
        strategy_path = Path(result["strategy_path"])

        # Check main execution file
        main_file = strategy_path / "1_get_portfolios.py"
        with open(main_file, "r") as f:
            main_content = f.read()
            assert "Comprehensive MACD strategy" in main_content
            assert "comprehensive_test" in main_content
            assert "ComprehensiveTest" in main_content

        # Check configuration file
        config_file = strategy_path / "config_types.py"
        with open(config_file, "r") as f:
            config_content = f.read()
            assert "class ComprehensiveTestConfig(TypedDict):" in config_content
            assert "MACD_FAST" in config_content
            assert "MACD_SLOW" in config_content
            assert "MACD_SIGNAL" in config_content

        # Check strategy execution file
        execution_file = strategy_path / "tools" / "strategy_execution.py"
        with open(execution_file, "r") as f:
            execution_content = f.read()
            assert "from ta.trend import MACD" in execution_content
            assert "from ta.momentum import RSIIndicator" in execution_content
            assert "def calculate_indicators(" in execution_content
            assert "def generate_signals(" in execution_content

        # Check test file
        test_file = strategy_path / "test_strategy.py"
        with open(test_file, "r") as f:
            test_content = f.read()
            assert "class TestComprehensiveTestConfiguration:" in test_content
            assert "class TestComprehensiveTestIndicators:" in test_content
            assert "MACD_Line" in test_content

        # Check README
        readme_file = strategy_path / "README.md"
        with open(readme_file, "r") as f:
            readme_content = f.read()
            assert "# Comprehensive Test Strategy" in readme_content
            assert "MACD" in readme_content
            assert "Kelly Criterion" in readme_content

    def test_multiple_strategy_types(self):
        """Test creating multiple different strategy types."""
        strategy_configs = [
            ("rsi_strategy", StrategyType.RSI, IndicatorType.RSI),
            ("sma_strategy", StrategyType.MOVING_AVERAGE, IndicatorType.SMA),
            ("bb_strategy", StrategyType.BOLLINGER_BANDS, IndicatorType.BOLLINGER),
            ("stoch_strategy", StrategyType.STOCHASTIC, IndicatorType.STOCHASTIC),
        ]

        created_strategies = []

        for name, strategy_type, primary_indicator in strategy_configs:
            config = TemplateConfig(
                strategy_name=name,
                strategy_type=strategy_type,
                description=f"Test {strategy_type.value} strategy",
                primary_indicator=primary_indicator,
                secondary_indicators=[],
                entry_conditions=[f"{primary_indicator.value} entry condition"],
                exit_conditions=[f"{primary_indicator.value} exit condition"],
            )

            result = self.generator.generate_strategy(config, dry_run=False)
            created_strategies.append(name)

            # Verify strategy exists
            strategy_path = Path(result["strategy_path"])
            assert strategy_path.exists()
            assert (strategy_path / "1_get_portfolios.py").exists()

        # Check all strategies are listed
        available_strategies = self.generator.list_available_strategies()
        for strategy_name in created_strategies:
            assert strategy_name in available_strategies


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
