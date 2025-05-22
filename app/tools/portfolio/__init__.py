"""Portfolio tools package.

This package provides tools for portfolio management, including:
- Loading portfolio configurations from files
- Processing portfolio data
- Calculating portfolio metrics
- Selecting optimal portfolios
- Managing allocation percentages
"""

from app.tools.portfolio.loader import (
    load_portfolio,
    load_portfolio_from_json,
    load_portfolio_from_csv
)

from app.tools.portfolio.paths import (
    resolve_portfolio_path,
    get_project_root
)

from app.tools.portfolio.format import (
    standardize_portfolio_columns,
    convert_csv_to_strategy_config
)

from app.tools.portfolio.validation import (
    validate_portfolio_schema,
    validate_strategy_config,
    validate_portfolio_configs
)

from app.tools.portfolio.types import StrategyConfig

from app.tools.portfolio.collection import (
    sort_portfolios,
    export_best_portfolios,
    combine_strategy_portfolios
)

from app.tools.portfolio.selection import get_best_portfolio

from app.tools.portfolio.processing import process_single_ticker

# Import enhanced loader functions
from app.tools.portfolio.enhanced_loader import (
    load_portfolio_with_logging,
    portfolio_context,
    PortfolioLoadError
)

# Import schema detection functions
from app.tools.portfolio.schema_detection import (
    SchemaVersion,
    detect_schema_version,
    detect_schema_version_from_file,
    normalize_portfolio_data
)

# Import allocation utility functions
from app.tools.portfolio.allocation import (
    validate_allocations,
    normalize_allocations,
    distribute_missing_allocations,
    ensure_allocation_sum_100_percent,
    calculate_position_sizes,
    get_allocation_summary
)

__all__ = [
    # Loader functions
    'load_portfolio',
    'load_portfolio_from_json',
    'load_portfolio_from_csv',
    
    # Path resolution functions
    'resolve_portfolio_path',
    'get_project_root',
    
    # Format conversion functions
    'standardize_portfolio_columns',
    'convert_csv_to_strategy_config',
    
    # Validation functions
    'validate_portfolio_schema',
    'validate_strategy_config',
    'validate_portfolio_configs',
    
    # Type definitions
    'StrategyConfig',
    
    # Collection functions
    'sort_portfolios',
    'export_best_portfolios',
    'combine_strategy_portfolios',
    
    # Selection functions
    'get_best_portfolio',
    
    # Processing functions
    'process_single_ticker',
    
    # Enhanced loader functions
    'load_portfolio_with_logging',
    'portfolio_context',
    'PortfolioLoadError',
    
    # Schema detection functions
    'SchemaVersion',
    'detect_schema_version',
    'detect_schema_version_from_file',
    'normalize_portfolio_data',
    
    # Allocation utility functions
    'validate_allocations',
    'normalize_allocations',
    'distribute_missing_allocations',
    'ensure_allocation_sum_100_percent',
    'calculate_position_sizes',
    'get_allocation_summary'
]