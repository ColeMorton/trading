"""Portfolio configuration loading utilities (Legacy Interface).

This module provides backward compatibility with the legacy portfolio loader.
It redirects all calls to the new unified implementation.

DEPRECATED: This module is maintained for backward compatibility only.
            New code should use app.tools.portfolio.loader directly.
"""

import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List

from app.tools.portfolio import StrategyConfig
from app.tools.portfolio.compatibility import load_portfolio_from_path


def load_portfolio_from_csv(
    csv_path: Path, log: Callable[[str, str], None], config: Dict[str, Any]
) -> List[StrategyConfig]:
    """
    Legacy interface for loading portfolio configuration from CSV file.

    DEPRECATED: Use app.tools.portfolio.loader.load_portfolio_from_csv instead.
    """
    warnings.warn(
        "app.concurrency.tools.portfolio_loader_legacy.load_portfolio_from_csv is deprecated. "
        "Use app.tools.portfolio.loader.load_portfolio_from_csv instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return load_portfolio_from_path(str(csv_path), log, config)


def load_portfolio_from_json(
    json_path: Path, log: Callable[[str, str], None], config: Dict[str, Any]
) -> List[StrategyConfig]:
    """
    Legacy interface for loading portfolio configuration from JSON file.

    DEPRECATED: Use app.tools.portfolio.loader.load_portfolio_from_json instead.
    """
    warnings.warn(
        "app.concurrency.tools.portfolio_loader_legacy.load_portfolio_from_json is deprecated. "
        "Use app.tools.portfolio.loader.load_portfolio_from_json instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return load_portfolio_from_path(str(json_path), log, config)


def load_portfolio(
    file_path: str, log: Callable[[str, str], None], config: Dict[str, Any]
) -> List[StrategyConfig]:
    """
    Legacy interface for loading portfolio configuration from either JSON or CSV file.

    DEPRECATED: Use app.tools.portfolio.loader.load_portfolio instead.
    """
    warnings.warn(
        "app.concurrency.tools.portfolio_loader_legacy.load_portfolio is deprecated. "
        "Use app.tools.portfolio.loader.load_portfolio instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return load_portfolio_from_path(file_path, log, config)
