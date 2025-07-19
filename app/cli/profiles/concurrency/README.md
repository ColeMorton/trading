# Concurrency Profiles

This directory contains optimized configuration profiles for concurrency analysis with a clean inheritance hierarchy that eliminates duplication.

## Directory Structure

```
concurrency/
├── base/                           # Base templates (do not use directly)
│   ├── concurrency_base.yaml      # Core settings (90% of common config)
│   ├── conservative_base.yaml     # Risk-averse defaults
│   ├── aggressive_base.yaml       # Higher risk tolerance
│   └── optimized_base.yaml        # Memory/performance optimized
├── portfolio_specific/             # Portfolio-specific configs
│   ├── risk_on.yaml              # Aggressive strategies
│   ├── protected.yaml            # Conservative strategies
│   └── live_signals.yaml         # Production trading
├── templates/                      # Documentation templates
│   └── complete_reference.yaml    # Full options reference
├── default.yaml                   # Default concurrency configuration
├── enhanced.yaml                  # Enhanced configuration with all features
└── README.md                      # This file
```

## Usage

### Quick Start

```bash
# Use default configuration
trading-cli concurrency analyze portfolio.csv

# Use portfolio-specific profile
trading-cli concurrency analyze --profile risk_on portfolio.csv

# Use conservative profile for protected portfolio
trading-cli concurrency analyze --profile protected protected.csv
```

### Profile Selection Guide

| Profile        | Use Case              | Risk Level | Memory Usage | Features                  |
| -------------- | --------------------- | ---------- | ------------ | ------------------------- |
| `default`      | General analysis      | Medium     | Low          | Basic features            |
| `risk_on`      | Aggressive strategies | High       | Medium       | Monte Carlo, optimization |
| `protected`    | Conservative trading  | Low        | Low          | VaR, strict limits        |
| `live_signals` | Production trading    | Medium     | High         | Real-time, optimized      |
| `enhanced`     | Full demonstration    | Low        | High         | All features enabled      |

## Inheritance Hierarchy

The profiles use a clean inheritance structure to eliminate duplication:

```
concurrency_base.yaml (180 lines of common config)
├── conservative_base.yaml (+30 lines of overrides)
│   └── protected.yaml (+3 lines portfolio-specific)
├── aggressive_base.yaml (+35 lines of overrides)
│   └── risk_on.yaml (+3 lines portfolio-specific)
├── optimized_base.yaml (+40 lines of overrides)
│   └── live_signals.yaml (+8 lines portfolio-specific)
└── default.yaml (+3 lines minimal overrides)
```

**Result**: 75% reduction in configuration duplication (from 1,320 to 330 total lines)

## Creating Custom Profiles

### 1. Extend a Base Template

```yaml
# my_custom_profile.yaml
metadata:
  name: my_custom_profile
  description: My custom concurrency configuration
  tags:
    - custom
    - production

inherits_from: base/conservative_base # Choose appropriate base
config_type: concurrency

config:
  # Only override what you need
  general:
    portfolio: 'my_portfolio.csv'
    initial_value: 20000.0
```

### 2. Override Specific Settings

```yaml
# high_frequency.yaml
inherits_from: base/optimized_base
config:
  general:
    csv_use_hourly: true # Use hourly data

  memory_optimization:
    chunk_size_rows: 25000 # Larger chunks for speed
```

## Base Template Features

### concurrency_base.yaml

- **Purpose**: Core configuration shared by all profiles
- **Features**: Standard settings, disabled optimization
- **Memory**: Minimal usage
- **Use**: Foundation for all other templates

### conservative_base.yaml

- **Purpose**: Risk-averse trading configurations
- **Features**: Lower risk limits, VaR calculation, longer cache
- **Memory**: Standard usage
- **Best for**: Protected portfolios, capital preservation

### aggressive_base.yaml

- **Purpose**: High-return strategy configurations
- **Features**: Monte Carlo, higher risk limits, full optimization
- **Memory**: Higher usage
- **Best for**: Risk-on portfolios, aggressive strategies

### optimized_base.yaml

- **Purpose**: Performance-optimized configurations
- **Features**: Memory optimization, parallel processing, caching
- **Memory**: Managed efficiently
- **Best for**: Live trading, large portfolios

## Configuration Options

For a complete reference of all available options, see:

- `templates/complete_reference.yaml` - Comprehensive documentation of every setting

## Migration from Old Profiles

Old profiles have been archived to `/app/cli/profiles/archived/`. The new profiles provide identical functionality with 75% less duplication.

### Mapping:

- `default_concurrency.yaml` → `default.yaml`
- `enhanced_concurrency.yaml` → `enhanced.yaml`
- `risk_on_concurrency.yaml` → `portfolio_specific/risk_on.yaml`
- `protected_concurrency.yaml` → `portfolio_specific/protected.yaml`
- `live_signals_concurrency.yaml` → `portfolio_specific/live_signals.yaml`

## Benefits

1. **75% less duplication** - From 1,320 to 330 total lines
2. **Easier maintenance** - Change base templates to update all children
3. **Clear organization** - Logical directory structure
4. **Better discovery** - ProfileManager automatically finds subdirectory profiles
5. **Consistent patterns** - All profiles follow same inheritance model
