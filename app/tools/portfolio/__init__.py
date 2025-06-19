"""Portfolio tools package.

This package provides tools for portfolio management, including:
- Loading portfolio configurations from files
- Processing portfolio data
- Calculating portfolio metrics
- Selecting optimal portfolios
- Managing allocation percentages
- Position sizing schema extensions and integration
"""

# Import allocation utility functions
from app.tools.portfolio.allocation import (
    calculate_position_sizes,
    distribute_missing_allocations,
    ensure_allocation_sum_100_percent,
    get_allocation_summary,
    normalize_allocations,
    validate_allocations,
)
from app.tools.portfolio.collection import (
    combine_strategy_portfolios,
    export_best_portfolios,
    sort_portfolios,
)

# Import enhanced loader functions
from app.tools.portfolio.enhanced_loader import (
    PortfolioLoadError,
    load_portfolio_with_logging,
    portfolio_context,
)
from app.tools.portfolio.format import (
    convert_csv_to_strategy_config,
    standardize_portfolio_columns,
)
from app.tools.portfolio.loader import (
    load_portfolio,
    load_portfolio_from_csv,
    load_portfolio_from_json,
)
from app.tools.portfolio.paths import get_project_root, resolve_portfolio_path
from app.tools.portfolio.position_sizing_integration import (
    PositionSizingPortfolioIntegration,
)

# Import position sizing extensions
from app.tools.portfolio.position_sizing_schema_extension import (
    PositionSizingPortfolioRow,
    PositionSizingSchema,
    PositionSizingSchemaValidator,
)

# Import schema detection functions
from app.tools.portfolio.schema_detection import (
    SchemaVersion,
    detect_schema_version,
    detect_schema_version_from_file,
    normalize_portfolio_data,
)
from app.tools.portfolio.selection import get_best_portfolio
from app.tools.portfolio.types import StrategyConfig
from app.tools.portfolio.validation import (
    validate_portfolio_configs,
    validate_portfolio_schema,
    validate_strategy_config,
)

__all__ = [
    # Loader functions
    "load_portfolio",
    "load_portfolio_from_json",
    "load_portfolio_from_csv",
    # Path resolution functions
    "resolve_portfolio_path",
    "get_project_root",
    # Format conversion functions
    "standardize_portfolio_columns",
    "convert_csv_to_strategy_config",
    # Validation functions
    "validate_portfolio_schema",
    "validate_strategy_config",
    "validate_portfolio_configs",
    # Type definitions
    "StrategyConfig",
    # Collection functions
    "sort_portfolios",
    "export_best_portfolios",
    "combine_strategy_portfolios",
    # Selection functions
    "get_best_portfolio",
    # Enhanced loader functions
    "load_portfolio_with_logging",
    "portfolio_context",
    "PortfolioLoadError",
    # Schema detection functions
    "SchemaVersion",
    "detect_schema_version",
    "detect_schema_version_from_file",
    "normalize_portfolio_data",
    # Allocation utility functions
    "validate_allocations",
    "normalize_allocations",
    "distribute_missing_allocations",
    "ensure_allocation_sum_100_percent",
    "calculate_position_sizes",
    "get_allocation_summary",
    # Position sizing extensions
    "PositionSizingSchema",
    "PositionSizingSchemaValidator",
    "PositionSizingPortfolioRow",
    "PositionSizingPortfolioIntegration",
]
