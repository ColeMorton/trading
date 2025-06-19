# Signal Configuration System

## Overview

The Signal Configuration module provides a centralized system for managing all configurable parameters in the signal processing pipeline. It replaces magic numbers with named constants, documents the purpose and impact of each parameter, and implements validation to ensure parameter values are within acceptable ranges.

## Key Features

- **Typed Configuration**: Uses TypedDict for clear definition of configuration parameters
- **Default Values**: Provides sensible defaults for all parameters
- **Parameter Validation**: Validates parameter values to prevent errors
- **Configuration Management**: Load and save configurations from/to JSON files
- **Documentation**: Comprehensive documentation of each parameter's purpose and impact
- **Modular Design**: Separate configuration sections for different aspects of signal processing

## Configuration Categories

The configuration system is divided into five main categories:

1. **Signal Metrics Configuration**: Parameters for calculating signal metrics
2. **Signal Filter Configuration**: Parameters for filtering signals
3. **Signal Quality Configuration**: Parameters for calculating signal quality scores
4. **Horizon Analysis Configuration**: Parameters for analyzing different time horizons
5. **Signal Conversion Configuration**: Parameters for converting signals to positions

## Usage Examples

### Basic Usage

```python
from app.tools.signal_config import SignalConfigManager
from app.tools.setup_logging import setup_logging

# Set up logging
log, _, _, _ = setup_logging("my_strategy", Path("./logs"), "my_strategy.log")

# Create config manager with default values
config_manager = SignalConfigManager(log)

# Update specific parameters
config_manager.update_metrics_config({
    "ANNUALIZATION_FACTOR": 252,  # Daily data
    "HORIZONS": [1, 5, 10, 20]
})

config_manager.update_filter_config({
    "USE_RSI": True,
    "RSI_THRESHOLD": 70,
    "DIRECTION": "Long"
})

# Get combined configuration for use in processing
combined_config = config_manager.get_combined_config()
```

### Loading from File

```python
from app.tools.signal_config import load_config_from_file

# Load configuration from file
config_manager = load_config_from_file("config/signal_config.json", log)

# Get specific configuration section
metrics_config = config_manager.metrics_config
filter_config = config_manager.filter_config
```

### Creating Default Configuration File

```python
from app.tools.signal_config import create_default_config_file

# Create a default configuration file
success = create_default_config_file("config/default_signal_config.json", log)
```

### Saving Configuration

```python
# Save current configuration to file
success = config_manager.save_config_to_file("config/my_signal_config.json")
```

## Configuration Parameters

### Signal Metrics Configuration

| Parameter            | Type        | Default       | Description                            | Impact                                                         |
| -------------------- | ----------- | ------------- | -------------------------------------- | -------------------------------------------------------------- |
| SIGNAL_COLUMN        | str         | "Signal"      | Name of the signal column              | Identifies which column contains signal values                 |
| DATE_COLUMN          | str         | "Date"        | Name of the date column                | Identifies which column contains date values                   |
| RETURN_COLUMN        | str         | "Return"      | Name of the return column              | Identifies which column contains return values                 |
| ANNUALIZATION_FACTOR | int         | 252           | Number of periods in a year            | Scales metrics to annual basis (252 for daily, 12 for monthly) |
| MIN_SAMPLE_SIZE      | int         | 20            | Minimum sample size for metrics        | Prevents unreliable metrics from small samples                 |
| HORIZONS             | List[int]   | [1, 3, 5, 10] | Time horizons to analyze               | Determines which holding periods are analyzed                  |
| NORMALIZATION_METHOD | str         | "min_max"     | Method for normalizing metrics         | Affects how metrics are scaled for comparison                  |
| FEATURE_RANGE        | List[float] | [0, 1]        | Target range for min-max normalization | Determines the scale of normalized metrics                     |

### Signal Filter Configuration

| Parameter             | Type  | Default | Description                            | Impact                                              |
| --------------------- | ----- | ------- | -------------------------------------- | --------------------------------------------------- |
| USE_RSI               | bool  | False   | Whether to enable RSI filtering        | Controls whether RSI filter is applied              |
| RSI_THRESHOLD         | int   | 70      | RSI threshold value                    | Determines RSI filter sensitivity                   |
| RSI_COLUMN            | str   | "RSI"   | Name of the RSI column                 | Identifies which column contains RSI values         |
| USE_VOLUME_FILTER     | bool  | None    | Whether to enable volume filtering     | Controls whether volume filter is applied           |
| MIN_VOLUME            | int   | None    | Minimum required volume                | Sets the volume threshold for filtering             |
| VOLUME_COLUMN         | str   | None    | Name of the volume column              | Identifies which column contains volume values      |
| USE_VOLATILITY_FILTER | bool  | None    | Whether to enable volatility filtering | Controls whether volatility filter is applied       |
| MIN_ATR               | float | None    | Minimum required ATR value             | Sets the lower ATR threshold for filtering          |
| MAX_ATR               | float | None    | Maximum allowed ATR value              | Sets the upper ATR threshold for filtering          |
| ATR_COLUMN            | str   | None    | Name of the ATR column                 | Identifies which column contains ATR values         |
| DIRECTION             | str   | "Long"  | Trading direction                      | Determines how filters are applied (long vs. short) |

### Signal Quality Configuration

| Parameter              | Type  | Default | Description                                      | Impact                                                     |
| ---------------------- | ----- | ------- | ------------------------------------------------ | ---------------------------------------------------------- |
| WIN_RATE_WEIGHT        | float | 0.4     | Weight of win rate in quality score              | Determines importance of win rate in quality score         |
| PROFIT_FACTOR_WEIGHT   | float | 0.3     | Weight of profit factor in quality score         | Determines importance of profit factor in quality score    |
| RISK_REWARD_WEIGHT     | float | 0.2     | Weight of risk-reward ratio in quality score     | Determines importance of risk-reward in quality score      |
| POSITIVE_RETURN_WEIGHT | float | 0.1     | Weight of positive return check in quality score | Determines importance of positive return in quality score  |
| PROFIT_FACTOR_CAP      | float | 5.0     | Maximum value for profit factor normalization    | Prevents extremely high profit factors from skewing scores |
| QUALITY_SCORE_SCALE    | float | 10.0    | Scale factor for quality score                   | Determines the range of quality scores (0 to SCALE)        |

### Horizon Analysis Configuration

| Parameter          | Type      | Default       | Description                                      | Impact                                                     |
| ------------------ | --------- | ------------- | ------------------------------------------------ | ---------------------------------------------------------- |
| HORIZONS           | List[int] | [1, 3, 5, 10] | Time horizons to analyze                         | Determines which holding periods are analyzed              |
| MIN_SAMPLE_SIZE    | int       | 20            | Minimum sample size for horizon metrics          | Prevents unreliable metrics from small samples             |
| SHARPE_WEIGHT      | float     | 0.6           | Weight of Sharpe ratio in best horizon selection | Determines importance of Sharpe ratio in horizon selection |
| WIN_RATE_WEIGHT    | float     | 0.3           | Weight of win rate in best horizon selection     | Determines importance of win rate in horizon selection     |
| SAMPLE_SIZE_WEIGHT | float     | 0.1           | Weight of sample size in best horizon selection  | Determines importance of sample size in horizon selection  |
| SAMPLE_SIZE_FACTOR | int       | 100           | Sample size normalization factor                 | Scales sample size for comparison (sample_size / FACTOR)   |

### Signal Conversion Configuration

| Parameter       | Type | Default    | Description                     | Impact                                                   |
| --------------- | ---- | ---------- | ------------------------------- | -------------------------------------------------------- |
| STRATEGY_TYPE   | str  | "MA Cross" | Type of strategy                | Used for tracking and identification                     |
| DIRECTION       | str  | "Long"     | Trading direction               | Determines how signals are converted to positions        |
| USE_RSI         | bool | False      | Whether to enable RSI filtering | Controls whether RSI filter is applied during conversion |
| RSI_THRESHOLD   | int  | 70         | RSI threshold value             | Determines RSI filter sensitivity during conversion      |
| SIGNAL_COLUMN   | str  | "Signal"   | Name of the signal column       | Identifies which column contains signal values           |
| POSITION_COLUMN | str  | "Position" | Name of the position column     | Determines where position values are stored              |
| DATE_COLUMN     | str  | "Date"     | Name of the date column         | Identifies which column contains date values             |

## Configuration File Format

The configuration file uses JSON format with the following structure:

```json
{
  "signal_metrics": {
    "SIGNAL_COLUMN": "Signal",
    "DATE_COLUMN": "Date",
    "RETURN_COLUMN": "Return",
    "ANNUALIZATION_FACTOR": 252,
    "MIN_SAMPLE_SIZE": 20,
    "HORIZONS": [1, 3, 5, 10],
    "NORMALIZATION_METHOD": "min_max",
    "FEATURE_RANGE": [0, 1]
  },
  "signal_filter": {
    "USE_RSI": false,
    "RSI_THRESHOLD": 70,
    "RSI_COLUMN": "RSI",
    "DIRECTION": "Long"
  },
  "signal_quality": {
    "WIN_RATE_WEIGHT": 0.4,
    "PROFIT_FACTOR_WEIGHT": 0.3,
    "RISK_REWARD_WEIGHT": 0.2,
    "POSITIVE_RETURN_WEIGHT": 0.1,
    "PROFIT_FACTOR_CAP": 5.0,
    "QUALITY_SCORE_SCALE": 10.0
  },
  "horizon_analysis": {
    "HORIZONS": [1, 3, 5, 10],
    "MIN_SAMPLE_SIZE": 20,
    "SHARPE_WEIGHT": 0.6,
    "WIN_RATE_WEIGHT": 0.3,
    "SAMPLE_SIZE_WEIGHT": 0.1,
    "SAMPLE_SIZE_FACTOR": 100
  },
  "signal_conversion": {
    "STRATEGY_TYPE": "MA Cross",
    "DIRECTION": "Long",
    "USE_RSI": false,
    "RSI_THRESHOLD": 70,
    "SIGNAL_COLUMN": "Signal",
    "POSITION_COLUMN": "Position",
    "DATE_COLUMN": "Date"
  }
}
```

## Best Practices

1. **Configuration Management**: Keep configuration files in a dedicated directory (e.g., `config/`)
2. **Version Control**: Include configuration files in version control to track changes
3. **Environment-Specific Configs**: Create different configuration files for different environments (development, testing, production)
4. **Documentation**: Document any non-standard parameter values with comments
5. **Validation**: Always validate configuration values before using them
6. **Defaults**: Provide sensible defaults for all parameters
7. **Logging**: Log configuration changes and validation issues
