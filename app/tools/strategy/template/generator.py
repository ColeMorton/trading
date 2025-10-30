"""
Strategy Template Generator

Main generator class that orchestrates template-based strategy creation.
"""

import shutil
from pathlib import Path
from typing import Any

from .config_template import TemplateConfig
from .execution_template import ExecutionTemplate
from .validation_template import ValidationTemplate


class StrategyTemplateGenerator:
    """Main class for generating complete strategy implementations from templates."""

    def __init__(self, base_path: str | None = None):
        """Initialize the strategy template generator.

        Args:
            base_path: Base path for the trading project. If None, will attempt to detect.
        """
        if base_path is None:
            # Try to find project root
            current_path = Path(__file__).parent
            while current_path.parent != current_path:
                if (current_path / "app").exists() and (
                    current_path / "app" / "strategies"
                ).exists():
                    base_path = str(current_path)
                    break
                current_path = current_path.parent

            if base_path is None:
                msg = "Could not detect project root. Please provide base_path."
                raise ValueError(
                    msg,
                )

        self.base_path = Path(base_path)
        self.strategies_path = self.base_path / "app" / "strategies"

        # Ensure strategies directory exists
        self.strategies_path.mkdir(parents=True, exist_ok=True)

    def generate_strategy(
        self,
        template_config: TemplateConfig,
        overwrite: bool = False,
        dry_run: bool = False,
    ) -> dict[str, str]:
        """Generate a complete strategy implementation from template.

        Args:
            template_config: Configuration for the strategy template
            overwrite: Whether to overwrite existing strategy if it exists
            dry_run: If True, return what would be generated without creating files

        Returns:
            Dictionary mapping file paths to their contents

        Raises:
            ValueError: If strategy already exists and overwrite=False
            FileExistsError: If strategy directory exists and overwrite=False
        """
        strategy_name = template_config.strategy_name
        strategy_path = self.strategies_path / strategy_name

        # Check if strategy already exists
        if strategy_path.exists() and not overwrite:
            msg = f"Strategy '{strategy_name}' already exists. Use overwrite=True to replace."
            raise FileExistsError(
                msg,
            )

        # Generate all template content
        generated_files = self._generate_all_files(template_config)

        if dry_run:
            return generated_files

        # Create strategy directory
        if strategy_path.exists() and overwrite:
            shutil.rmtree(strategy_path)

        strategy_path.mkdir(parents=True, exist_ok=True)

        # Create tools subdirectory
        tools_path = strategy_path / "tools"
        tools_path.mkdir(exist_ok=True)

        # Write all files
        files_created = []
        for relative_path, content in generated_files.items():
            file_path = strategy_path / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            files_created.append(str(file_path))

        return {
            "strategy_path": str(strategy_path),
            "files_created": files_created,
            "file_count": len(files_created),
        }

    def _generate_all_files(self, config: TemplateConfig) -> dict[str, str]:
        """Generate all files for the strategy.

        Args:
            config: Template configuration

        Returns:
            Dictionary mapping relative file paths to their contents
        """
        execution_template = ExecutionTemplate(config)
        validation_template = ValidationTemplate(config)

        files = {}

        # 1. Main execution file
        files["1_get_portfolios.py"] = execution_template.generate_main_execution_file()

        # 2. Configuration file
        files["config_types.py"] = self._generate_config_file(config)

        # 3. Strategy execution tools
        files["tools/__init__.py"] = self._generate_tools_init()
        files["tools/strategy_execution.py"] = (
            execution_template.generate_strategy_execution_file()
        )

        # 4. Exception definitions
        files["exceptions.py"] = execution_template.generate_exceptions_file()

        # 5. Package init file
        files["__init__.py"] = self._generate_package_init(config)

        # 6. Test files
        files["test_strategy.py"] = validation_template.generate_test_file()
        files["test_performance.py"] = validation_template.generate_benchmark_file()

        # 7. README file
        files["README.md"] = self._generate_readme(config)

        return files

    def _generate_config_file(self, config: TemplateConfig) -> str:
        """Generate the configuration file."""
        strategy_name = config.strategy_name
        class_name = strategy_name.replace("_", "").title()

        # Generate imports
        imports = [
            "from typing import TypedDict, List, Union, Optional",
            "from app.tools.project_utils import get_project_root",
        ]

        return f'''"""
Configuration Types for {class_name} Strategy

Generated by Strategy Template Generator.
"""

{chr(10).join(imports)}


{config.get_config_type_definition()}


{config.get_default_config_instance()}
'''

    def _generate_tools_init(self) -> str:
        """Generate tools __init__.py file."""
        return '''"""
Strategy tools package.

Generated by Strategy Template Generator.
"""

from .strategy_execution import execute_strategy, calculate_indicators, generate_signals

__all__ = [
    "execute_strategy",
    "calculate_indicators",
    "generate_signals"
]
'''

    def _generate_package_init(self, config: TemplateConfig) -> str:
        """Generate package __init__.py file."""
        strategy_name = config.strategy_name
        class_name = strategy_name.replace("_", "").title()

        return f'''"""
{class_name} Strategy Package

{config.description}

Generated by Strategy Template Generator.
"""

from .config_types import DEFAULT_CONFIG, {class_name}Config
from .exceptions import (
    {class_name}Error,
    {class_name}ConfigurationError,
    {class_name}ExecutionError,
    {class_name}PortfolioError
)
from .tools.strategy_execution import execute_strategy

__all__ = [
    "DEFAULT_CONFIG",
    "{class_name}Config",
    "{class_name}Error",
    "{class_name}ConfigurationError",
    "{class_name}ExecutionError",
    "{class_name}PortfolioError",
    "execute_strategy"
]

__version__ = "1.0.0"
__author__ = "Strategy Template Generator"
'''

    def _generate_readme(self, config: TemplateConfig) -> str:
        """Generate README.md file."""
        strategy_name = config.strategy_name
        class_name = strategy_name.replace("_", "").title()

        # Generate parameter documentation
        param_docs = []
        for key, value in config.config_fields.items():
            param_docs.append(f"- `{key}`: {self._describe_parameter(key, value)}")

        return f"""# {class_name} Strategy

{config.description}

**Strategy Type**: {config.strategy_type.value.replace("_", " ").title()}
**Primary Indicator**: {config.primary_indicator.value.upper()}
**Secondary Indicators**: {", ".join(ind.value.upper() for ind in config.secondary_indicators)}

## Overview

This strategy was generated using the Strategy Template Generator framework. It implements a {config.strategy_type.value.replace("_", " ")} approach using {config.primary_indicator.value.upper()} as the primary technical indicator.

### Signal Generation

**Entry Conditions:**
{chr(10).join(f"- {condition}" for condition in config.entry_conditions)}

**Exit Conditions:**
{chr(10).join(f"- {condition}" for condition in config.exit_conditions)}

### Risk Management

- **Stop Loss**: {"Enabled" if config.stop_loss_enabled else "Disabled"}
- **Take Profit**: {"Enabled" if config.take_profit_enabled else "Disabled"}
- **Position Sizing**: {config.position_sizing.title()}

## Configuration

### Required Parameters

{chr(10).join(param_docs)}

### Default Configuration

```python
from app.strategies.{strategy_name}.config_types import DEFAULT_CONFIG

# Use default configuration
config = DEFAULT_CONFIG.copy()

# Customize as needed
config["TICKER"] = ["AAPL", "GOOGL", "MSFT"]
config["DIRECTION"] = "Long"
```

## Usage

### Basic Usage

```python
from app.strategies.{strategy_name} import execute_strategy
from app.strategies.{strategy_name}.config_types import DEFAULT_CONFIG

# Run strategy analysis
config = DEFAULT_CONFIG.copy()
config["TICKER"] = "AAPL"

portfolios = execute_strategy(config, "{strategy_name.upper()}", print)
```

### Command Line Usage

```bash
# Run strategy analysis
python app/strategies/{strategy_name}/1_get_portfolios.py

# Or using the main entry point
python -m app.strategies.{strategy_name}
```

### Advanced Usage

```python
from app.strategies.{strategy_name}.tools.strategy_execution import (
    calculate_indicators,
    generate_signals,
    validate_strategy_config
)

# Custom workflow
data = load_prices("AAPL")
data_with_indicators = calculate_indicators(data, config)
signals = generate_signals(data_with_indicators, config)
```

## Testing

Run the test suite to validate strategy functionality:

```bash
# Run all tests
pytest app/strategies/{strategy_name}/test_strategy.py -v

# Run performance benchmarks
pytest app/strategies/{strategy_name}/test_performance.py -v

# Run specific test categories
pytest app/strategies/{strategy_name}/test_strategy.py::Test{class_name}Configuration -v
```

## File Structure

```
app/strategies/{strategy_name}/
├── __init__.py                 # Package initialization
├── 1_get_portfolios.py        # Main execution script
├── config_types.py            # Configuration definitions
├── exceptions.py              # Strategy-specific exceptions
├── README.md                  # This documentation
├── test_strategy.py           # Comprehensive test suite
├── test_performance.py        # Performance benchmarks
└── tools/
    ├── __init__.py            # Tools package init
    └── strategy_execution.py  # Core strategy logic
```

## Integration

This strategy integrates with the unified trading framework:

- **Centralized Tools**: Uses `app.tools.strategy.*` for common functionality
- **Error Handling**: Implements standardized error hierarchy
- **Configuration**: Follows unified configuration patterns
- **Signal Processing**: Leverages `SignalProcessorFactory` for consistency
- **Portfolio Management**: Compatible with portfolio orchestration system

## Performance Characteristics

- **Data Processing**: Optimized for datasets up to 2000+ rows
- **Memory Usage**: Efficient memory management with typical usage < 100MB
- **Execution Time**: Target execution time < 5 seconds for standard analysis
- **Scalability**: Supports multiple tickers and parameter combinations

## Customization

### Adding New Indicators

1. Update `calculate_indicators()` in `tools/strategy_execution.py`
2. Add indicator imports to the file header
3. Modify signal generation logic if needed
4. Update tests to validate new indicators

### Modifying Signal Logic

1. Edit `generate_signals()` function
2. Update entry/exit conditions
3. Add corresponding test cases
4. Validate signal accuracy with backtesting

### Configuration Changes

1. Modify `config_types.py` to add new parameters
2. Update `DEFAULT_CONFIG` with appropriate defaults
3. Add validation logic in `validate_strategy_config()`
4. Update documentation and tests

## Generated Files

This strategy was automatically generated with the following specifications:

- **Generated On**: {self._get_current_timestamp()}
- **Template Version**: 1.0.0
- **Strategy Type**: {config.strategy_type.value}
- **Primary Indicator**: {config.primary_indicator.value}
- **Configuration Fields**: {len(config.config_fields)} fields
- **Risk Management**: {"Enabled" if config.stop_loss_enabled or config.take_profit_enabled else "Basic"}

## Support

For questions about this generated strategy:

1. Check the test files for usage examples
2. Review the unified framework documentation
3. Examine similar strategies for patterns
4. Refer to the Strategy Template Generator documentation

---

*This strategy was generated using the Strategy Template Generator framework to ensure consistency, reliability, and maintainability across all trading strategies.*
"""

    def _describe_parameter(self, key: str, value: Any) -> str:
        """Generate description for a configuration parameter."""
        descriptions = {
            "TICKER": "Stock symbol(s) to analyze",
            "BASE_DIR": "Project base directory path",
            "REFRESH": "Whether to refresh cached data",
            "DIRECTION": "Trading direction (Long/Short)",
            "USE_CURRENT": "Whether to use current market signals",
            "SORT_BY": "Column to sort results by",
            "SORT_ASC": "Sort in ascending order",
            "USE_YEARS": "Whether to use years-based data",
            "YEARS": "Number of years of historical data",
            "FAST_PERIOD": "Short moving average window size",
            "SLOW_PERIOD": "Long moving average window size",
            "STRATEGY_TYPES": "List of strategy types to run",
            "RSI_PERIOD": "RSI calculation period",
            "RSI_OVERBOUGHT": "RSI overbought threshold",
            "RSI_OVERSOLD": "RSI oversold threshold",
            "BB_PERIOD": "Bollinger Bands period",
            "BB_STD_DEV": "Bollinger Bands standard deviation",
            "MACD_FAST": "MACD fast EMA period",
            "MACD_SLOW": "MACD slow EMA period",
            "MACD_SIGNAL": "MACD signal line period",
            "MOMENTUM_PERIOD": "Momentum calculation period",
            "MOMENTUM_THRESHOLD": "Momentum signal threshold",
            "STOP_LOSS_PCT": "Stop loss percentage",
            "TAKE_PROFIT_PCT": "Take profit percentage",
            "POSITION_SIZE_PCT": "Position size percentage",
            "USE_KELLY_CRITERION": "Whether to use Kelly criterion for sizing",
        }

        desc = descriptions.get(key, f"Configuration parameter (default: {value})")
        return f"{desc} (default: {value})"

    def _get_current_timestamp(self) -> str:
        """Get current timestamp for documentation."""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def list_available_strategies(self) -> list[str]:
        """List all existing strategies in the strategies directory.

        Returns:
            List of strategy directory names
        """
        if not self.strategies_path.exists():
            return []

        strategies = []
        for item in self.strategies_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                # Check if it looks like a strategy (has main file)
                if (item / "1_get_portfolios.py").exists():
                    strategies.append(item.name)

        return sorted(strategies)

    def validate_strategy_name(self, name: str) -> bool:
        """Validate that a strategy name is valid.

        Args:
            name: Strategy name to validate

        Returns:
            True if name is valid

        Raises:
            ValueError: If name is invalid
        """
        if not name:
            msg = "Strategy name cannot be empty"
            raise ValueError(msg)

        if not name.replace("_", "").isalnum():
            msg = "Strategy name must contain only letters, numbers, and underscores"
            raise ValueError(
                msg,
            )

        if name[0].isdigit():
            msg = "Strategy name cannot start with a number"
            raise ValueError(msg)

        if len(name) > 50:
            msg = "Strategy name must be 50 characters or less"
            raise ValueError(msg)

        # Check for reserved names
        reserved_names = ["test", "tmp", "temp", "base", "common", "utils", "tools"]
        if name.lower() in reserved_names:
            msg = f"'{name}' is a reserved name"
            raise ValueError(msg)

        return True

    def get_strategy_info(self, strategy_name: str) -> dict[str, Any] | None:
        """Get information about an existing strategy.

        Args:
            strategy_name: Name of the strategy

        Returns:
            Dictionary with strategy information or None if not found
        """
        strategy_path = self.strategies_path / strategy_name

        if not strategy_path.exists():
            return None

        info = {
            "name": strategy_name,
            "path": str(strategy_path),
            "exists": True,
            "files": [],
        }

        # Check for main files
        main_files = [
            "1_get_portfolios.py",
            "config_types.py",
            "exceptions.py",
            "__init__.py",
            "README.md",
        ]

        for file_name in main_files:
            file_path = strategy_path / file_name
            info["files"].append(
                {
                    "name": file_name,
                    "exists": file_path.exists(),
                    "size": file_path.stat().st_size if file_path.exists() else 0,
                },
            )

        # Check tools directory
        tools_path = strategy_path / "tools"
        if tools_path.exists():
            info["tools_dir"] = True
            info["tools_files"] = [f.name for f in tools_path.iterdir() if f.is_file()]
        else:
            info["tools_dir"] = False
            info["tools_files"] = []

        return info
