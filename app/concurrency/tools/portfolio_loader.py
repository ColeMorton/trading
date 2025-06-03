"""Portfolio configuration loading utilities.

DEPRECATED: This module is maintained for backward compatibility only.
            New code should use app.tools.portfolio.loader directly.

This module is now a thin wrapper around the unified portfolio loader implementation.
It imports and re-exports the functions from app.concurrency.tools.portfolio_loader_legacy
to maintain backward compatibility.
"""

import warnings

warnings.warn(
    "app.concurrency.tools.portfolio_loader is deprecated. "
    "Use app.tools.portfolio.loader instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export the legacy functions for backward compatibility
from app.concurrency.tools.portfolio_loader_legacy import (
    load_portfolio,
    load_portfolio_from_csv,
    load_portfolio_from_json,
)

__all__ = ["load_portfolio_from_csv", "load_portfolio_from_json", "load_portfolio"]
