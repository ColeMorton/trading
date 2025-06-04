"""
GraphQL Mutation Resolvers

This module contains all GraphQL mutation resolvers.
"""

from .analysis_mutations import (
    cancel_analysis,
    execute_ma_cross_analysis,
    get_analysis_status,
)
from .portfolio_mutations import (
    add_strategy_to_portfolio,
    create_portfolio,
    delete_portfolio,
    remove_strategy_from_portfolio,
    update_portfolio,
)
from .strategy_mutations import (
    create_strategy,
    create_strategy_configuration,
    delete_strategy,
    delete_strategy_configuration,
    update_strategy,
    update_strategy_configuration,
)

__all__ = [
    "create_portfolio",
    "update_portfolio",
    "delete_portfolio",
    "add_strategy_to_portfolio",
    "remove_strategy_from_portfolio",
    "create_strategy",
    "update_strategy",
    "delete_strategy",
    "create_strategy_configuration",
    "update_strategy_configuration",
    "delete_strategy_configuration",
    "execute_ma_cross_analysis",
    "get_analysis_status",
    "cancel_analysis",
]
