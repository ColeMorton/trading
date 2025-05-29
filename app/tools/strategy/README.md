# Strategy Factory Pattern

This module implements the Strategy Factory pattern for trading strategies, following SOLID principles.

## Architecture

### Core Components

1. **BaseStrategy** (`base.py`): Abstract base class defining the strategy interface
2. **Concrete Strategies** (`concrete.py`): SMA and EMA strategy implementations
3. **StrategyFactory** (`factory.py`): Factory for creating strategy instances
4. **Integration** (`calculate_ma_and_signals.py`): Backward-compatible integration

### Benefits

- **Open/Closed Principle**: Easy to add new strategies without modifying existing code
- **Single Responsibility**: Each strategy class has one clear purpose
- **Dependency Inversion**: High-level modules depend on abstractions, not concrete implementations
- **Testability**: Each component can be tested independently

## Usage

### Basic Usage

```python
from app.tools.strategy.factory import factory

# Create a strategy instance
strategy = factory.create_strategy("SMA")

# Execute strategy
result = strategy.calculate(data, short_window=20, long_window=50, config=config, log=log)
```

### Adding a New Strategy

1. Create a new strategy class inheriting from `BaseStrategy`:

```python
from app.tools.strategy.base import BaseStrategy
import polars as pl

class WMAStrategy(BaseStrategy):
    """Weighted Moving Average strategy."""
    
    def calculate(self, data, short_window, long_window, config, log):
        # Implement WMA calculation logic
        pass
```

2. Register the strategy with the factory:

```python
from app.tools.strategy.factory import factory
from mymodule import WMAStrategy

factory.register_strategy("WMA", WMAStrategy)
```

3. Use the new strategy:

```python
strategy = factory.create_strategy("WMA")
result = strategy.calculate(data, 10, 30, config, log)
```

## Backward Compatibility

The existing `calculate_ma_and_signals` function has been updated to use the factory pattern internally, maintaining full backward compatibility:

```python
# This still works exactly as before
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals

result = calculate_ma_and_signals(data, 20, 50, config, log, "SMA")
```

## Testing

Run the comprehensive test suite:

```bash
poetry run pytest tests/test_strategy_factory.py -v
```

## Design Decisions

1. **Singleton Factory**: Ensures consistent strategy registration across the application
2. **Case-Insensitive Strategy Names**: Improves usability ("sma", "SMA", "Sma" all work)
3. **Validation in Base Class**: Common validation logic is shared across all strategies
4. **Clear Error Messages**: Factory provides helpful error messages when unknown strategies are requested