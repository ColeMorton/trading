# Signal Filtering Module

## Overview

The Signal Filtering module provides a centralized, pipeline-based approach to filtering trading signals. It ensures consistent application of filters across the entire application and provides comprehensive tracking of filter effects.

## Key Features

- **Pipeline Architecture**: Apply multiple filters in sequence with a single function call
- **Extensible Framework**: Easily add custom filters by implementing the `FilterInterface`
- **Comprehensive Tracking**: Detailed statistics on filter performance and rejection reasons
- **Standard Filters**: Pre-built filters for common filtering needs (RSI, Volume, Volatility)
- **Consistent API**: Uniform interface for all filtering operations

## Usage Examples

### Basic Usage

```python
from app.tools.signal_filtering import filter_signals
from app.tools.setup_logging import setup_logging

# Set up logging
log, _, _, _ = setup_logging("my_strategy", Path("./logs"), "my_strategy.log")

# Define configuration
config = {
    'USE_RSI': True,
    'RSI_THRESHOLD': 70,
    'DIRECTION': 'Long',
    'USE_VOLUME_FILTER': True,
    'MIN_VOLUME': 100000
}

# Apply filters
filtered_data, stats = filter_signals(data, config, log)

# Log statistics
log(f"Filtering complete: {stats['remaining_signals']} of {stats['total_signals']} signals passed", "info")
```

### Custom Pipeline

```python
from app.tools.signal_filtering import SignalFilterPipeline, RSIFilter, VolumeFilter

# Create custom pipeline
pipeline = SignalFilterPipeline(log)
pipeline.add_filter(RSIFilter(log))
pipeline.add_filter(VolumeFilter(log))

# Apply custom pipeline
filtered_data = pipeline.apply_filters(data, config)

# Get statistics
stats = pipeline.get_pipeline_stats()
```

### Creating Custom Filters

```python
from app.tools.signal_filtering import BaseFilter

class MyCustomFilter(BaseFilter):
    def __init__(self, log=None):
        super().__init__("MyCustom", log)

    def apply(self, data, config):
        # Extract configuration
        use_filter = config.get('USE_MY_CUSTOM_FILTER', False)
        threshold = config.get('MY_CUSTOM_THRESHOLD', 0.5)
        signal_column = config.get('SIGNAL_COLUMN', 'Signal')

        # Skip if disabled
        if not use_filter:
            return data

        # Convert to pandas for processing
        is_polars = isinstance(data, pl.DataFrame)
        if is_polars:
            df = data.to_pandas()
        else:
            df = data

        # Count signals before filtering
        self.total_signals = int(np.sum(df[signal_column] != 0))

        # Create a copy of the original signals
        original_signals = df[signal_column].copy()

        # Apply custom filtering logic
        # ...

        # Count filtered signals
        self.filtered_signals = int(np.sum(original_signals != 0) - np.sum(df[signal_column] != 0))

        # Track rejection reason
        self._track_rejection("Custom rejection reason", self.filtered_signals)

        # Convert back to polars if needed
        if is_polars:
            return pl.from_pandas(df)
        return df
```

## Standard Filters

### RSI Filter

Filters signals based on Relative Strength Index (RSI) values.

**Configuration Parameters:**

- `USE_RSI` (bool): Whether to enable RSI filtering
- `RSI_THRESHOLD` (int): RSI threshold value (default: 70)
- `DIRECTION` (str): Trading direction ('Long' or 'Short')
- `SIGNAL_COLUMN` (str): Name of the signal column (default: 'Signal')
- `RSI_COLUMN` (str): Name of the RSI column (default: 'RSI')

**Behavior:**

- For long positions: Signals are filtered out if RSI < threshold
- For short positions: Signals are filtered out if RSI > (100 - threshold)

### Volume Filter

Filters signals based on trading volume thresholds.

**Configuration Parameters:**

- `USE_VOLUME_FILTER` (bool): Whether to enable volume filtering
- `MIN_VOLUME` (int): Minimum required volume
- `VOLUME_COLUMN` (str): Name of the volume column (default: 'Volume')
- `SIGNAL_COLUMN` (str): Name of the signal column (default: 'Signal')

**Behavior:**

- Signals are filtered out if volume < MIN_VOLUME

### Volatility Filter

Filters signals based on Average True Range (ATR) volatility thresholds.

**Configuration Parameters:**

- `USE_VOLATILITY_FILTER` (bool): Whether to enable volatility filtering
- `MIN_ATR` (float): Minimum required ATR value
- `MAX_ATR` (float): Maximum allowed ATR value
- `ATR_COLUMN` (str): Name of the ATR column (default: 'ATR')
- `SIGNAL_COLUMN` (str): Name of the signal column (default: 'Signal')

**Behavior:**

- Signals are filtered out if ATR < MIN_ATR or ATR > MAX_ATR

## Filter Statistics

The filtering module provides detailed statistics on filter performance:

```python
stats = {
    "total_filters": 3,
    "total_signals": 100,
    "remaining_signals": 65,
    "overall_pass_rate": 0.65,
    "filter_stats": [
        {
            "filter_name": "RSI",
            "total_signals": 100,
            "filtered_signals": 20,
            "pass_rate": 0.8,
            "rejection_reasons": {
                "RSI below threshold": 20
            }
        },
        {
            "filter_name": "Volume",
            "total_signals": 80,
            "filtered_signals": 10,
            "pass_rate": 0.875,
            "rejection_reasons": {
                "Insufficient volume": 10
            }
        },
        {
            "filter_name": "Volatility",
            "total_signals": 70,
            "filtered_signals": 5,
            "pass_rate": 0.929,
            "rejection_reasons": {
                "Low volatility": 3,
                "High volatility": 2
            }
        }
    ]
}
```

## Integration with Signal Conversion

The filtering module is designed to work seamlessly with the Signal Conversion module:

```python
from app.tools.signal_filtering import filter_signals
from app.tools.signal_conversion import convert_signals_to_positions

# Filter signals
filtered_data, filter_stats = filter_signals(data, config, log)

# Convert filtered signals to positions
positioned_data, audit = convert_signals_to_positions(filtered_data, config, log)
```

## Best Practices

1. **Configuration Management**: Keep filter configuration parameters in a centralized configuration system
2. **Filter Order**: Consider the order of filters in the pipeline (more restrictive filters should come later)
3. **Logging**: Enable detailed logging to track filter performance and diagnose issues
4. **Statistics Analysis**: Regularly review filter statistics to optimize filter parameters
5. **Custom Filters**: Create custom filters for strategy-specific filtering needs
