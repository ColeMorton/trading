# CLI Configuration Profiles

This directory contains YAML configuration profiles for the unified trading CLI system.

## Directory Structure

```
app/cli/profiles/
├── README.md              # This file
├── strategies/            # Strategy-specific profiles
│   ├── ma_cross_portfolio.yaml    # Production MA Cross portfolio analysis
│   ├── ma_cross_crypto.yaml       # Crypto-focused MA Cross analysis
│   ├── ma_cross_dev.yaml          # Development/testing profile
│   └── ...                        # Additional strategy profiles
├── portfolio/             # Portfolio-specific profiles (future)
├── concurrency/           # Concurrency analysis profiles (future)
└── tools/                 # Tools command profiles (future)
```

## Usage

### Load a Profile with CLI

```bash
# Run strategy analysis with a profile
trading-cli strategy run --profile ma_cross_portfolio

# Run parameter sweep with a profile
trading-cli strategy sweep --profile ma_cross_crypto

# Test with development profile
trading-cli strategy run --profile ma_cross_dev --dry-run
```

### Available Strategy Profiles

| Profile              | Description                                   | Use Case                             |
| -------------------- | --------------------------------------------- | ------------------------------------ |
| `ma_cross_portfolio` | Production analysis with specific ticker list | Matches `1_get_portfolios.py` CONFIG |
| `ma_cross_crypto`    | Crypto-focused analysis                       | Cryptocurrency trading               |
| `ma_cross_dev`       | Development/testing                           | Quick testing with relaxed filters   |

### Profile Format

Each profile follows this structure:

```yaml
name: 'profile_name'
description: 'Profile description'
config_type: 'strategy' # or "portfolio", "concurrency", "tools"
tags: ['tag1', 'tag2']

config:
  # Configuration parameters that map to CLI options
  ticker: ['AAPL', 'MSFT']
  windows: 89
  strategy_types: ['SMA', 'EMA']
  # ... additional parameters
```

## Related Configurations

- **Strategy-specific configs**: `app/strategies/*/config/*.yaml`
- **CLI system configs**: `app/cli/config/`
- **Python equivalents**: See individual strategy modules (e.g., `app/strategies/ma_cross/1_get_portfolios.py`)

## Adding New Profiles

1. Create a new YAML file in the appropriate subdirectory
2. Follow the naming convention: `{strategy}_{purpose}.yaml`
3. Include descriptive name, description, and tags
4. Test with `--dry-run` before using in production
