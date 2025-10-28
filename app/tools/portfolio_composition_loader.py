"""
Portfolio Composition Loader for Business-Technical Configuration Integration.

This module provides loading and resolution of portfolio configurations that separate
business concerns (asset selection, allocation) from technical concerns (execution parameters).
"""

from typing import Any

from app.tools.business_config_loader import (
    BusinessConfigurationError,
    get_business_config_loader,
)
from app.tools.structured_logging import get_logger


class PortfolioCompositionError(Exception):
    """Exception raised for portfolio composition errors."""


class PortfolioCompositionLoader:
    """Loader for composed portfolio configurations separating business and technical concerns."""

    def __init__(self):
        """Initialize the portfolio composition loader."""
        self.logger = get_logger("portfolio_composition_loader")
        self.business_loader = get_business_config_loader()

    def load_portfolio_composition(
        self,
        portfolio_name: str,
        execution_profile: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Load portfolio composition separating business and technical configurations.

        Args:
            portfolio_name: Name of the portfolio (e.g., 'risk_on', 'protected')
            execution_profile: Optional technical execution profile name

        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: (business_config, technical_config)

        Raises:
            PortfolioCompositionError: If portfolio composition cannot be loaded
        """
        try:
            # Load business portfolio configuration
            business_config = self.business_loader.get_portfolio_config(portfolio_name)

            # Load technical execution configuration if specified
            technical_config = {}
            if execution_profile:
                technical_config = self._load_execution_profile(execution_profile)

            # Validate composition
            self._validate_composition(
                business_config,
                technical_config,
                portfolio_name,
            )

            self.logger.info(
                f"Successfully loaded portfolio composition for {portfolio_name}",
            )
            return business_config, technical_config

        except Exception as e:
            if isinstance(e, PortfolioCompositionError):
                raise
            msg = f"Error loading portfolio composition for {portfolio_name}: {e!s}"
            raise PortfolioCompositionError(
                msg,
            )

    def _load_execution_profile(self, execution_profile: str) -> dict[str, Any]:
        """Load technical execution profile.

        Args:
            execution_profile: Name of execution profile

        Returns:
            Dict[str, Any]: Technical execution configuration
        """
        # Try different execution profile locations
        profile_paths = [
            f"portfolio_review/technical/{execution_profile}.yaml",
            f"concurrency/portfolio_specific/{execution_profile}.yaml",
            f"strategies/{execution_profile}.yaml",
        ]

        for profile_path in profile_paths:
            try:
                return self.business_loader.load_config(
                    f"../app/cli/profiles/{profile_path}",
                )
            except BusinessConfigurationError:
                continue

        msg = f"Execution profile not found: {execution_profile}"
        raise PortfolioCompositionError(
            msg,
        )

    def _validate_composition(
        self,
        business_config: dict[str, Any],
        technical_config: dict[str, Any],
        portfolio_name: str,
    ) -> None:
        """Validate portfolio composition for consistency.

        Args:
            business_config: Business portfolio configuration
            technical_config: Technical execution configuration
            portfolio_name: Portfolio name for error reporting
        """
        # Validate business config structure
        if "assets" not in business_config:
            msg = f"Business portfolio {portfolio_name} missing 'assets' section"
            raise PortfolioCompositionError(
                msg,
            )

        # Validate technical config references business config if present
        if technical_config and "config" in technical_config:
            config = technical_config["config"]
            if "portfolio_reference" in config:
                expected_ref = f"data/config/portfolios/{portfolio_name}.yaml"
                if config["portfolio_reference"] != expected_ref:
                    self.logger.warning(
                        f"Technical config portfolio_reference mismatch: "
                        f"expected {expected_ref}, got {config['portfolio_reference']}",
                    )

    def get_asset_execution_strategy(
        self,
        portfolio_name: str,
        ticker: str,
        execution_profile: str | None = None,
    ) -> dict[str, Any]:
        """Get execution strategy for a specific asset in a portfolio.

        Args:
            portfolio_name: Name of the portfolio
            ticker: Asset ticker symbol
            execution_profile: Optional execution profile

        Returns:
            Dict[str, Any]: Execution strategy parameters for the asset

        Raises:
            PortfolioCompositionError: If asset execution strategy cannot be found
        """
        try:
            business_config, technical_config = self.load_portfolio_composition(
                portfolio_name,
                execution_profile,
            )

            # Find asset in business config
            asset_config = self._find_asset_config(business_config, ticker)
            if not asset_config:
                msg = f"Asset {ticker} not found in portfolio {portfolio_name}"
                raise PortfolioCompositionError(
                    msg,
                )

            # Get execution strategy from technical config
            execution_strategy = {}
            if technical_config and "config" in technical_config:
                execution_strategy = self._find_execution_strategy(
                    technical_config,
                    ticker,
                )

            # Combine with asset-specific defaults from business configuration
            asset_defaults = self.business_loader.get_asset_specific_defaults(ticker)

            # Compose final execution strategy
            return {
                "ticker": ticker,
                "business_config": asset_config,
                "asset_defaults": asset_defaults,
                "execution_config": execution_strategy,
            }

        except Exception as e:
            if isinstance(e, PortfolioCompositionError):
                raise
            msg = f"Error getting execution strategy for {ticker} in {portfolio_name}: {e!s}"
            raise PortfolioCompositionError(
                msg,
            )

    def _find_asset_config(
        self,
        business_config: dict[str, Any],
        ticker: str,
    ) -> dict[str, Any] | None:
        """Find asset configuration in business portfolio config.

        Args:
            business_config: Business portfolio configuration
            ticker: Asset ticker symbol

        Returns:
            Optional[Dict[str, Any]]: Asset configuration or None if not found
        """
        assets = business_config.get("assets", [])
        for asset in assets:
            if asset.get("ticker") == ticker:
                return asset
        return None

    def _find_execution_strategy(
        self,
        technical_config: dict[str, Any],
        ticker: str,
    ) -> dict[str, Any]:
        """Find execution strategy in technical configuration.

        Args:
            technical_config: Technical execution configuration
            ticker: Asset ticker symbol

        Returns:
            Dict[str, Any]: Execution strategy configuration
        """
        config = technical_config.get("config", {})

        # Check for multi-strategy format (like investment portfolio)
        if "execution_strategies" in config:
            strategies = config["execution_strategies"]

            # Handle both single strategy and multi-strategy formats
            if isinstance(strategies, dict) and ticker in strategies:
                # Multi-strategy format: ticker -> strategies
                return strategies[ticker]
            if isinstance(strategies, list):
                # List format: find by ticker
                for strategy in strategies:
                    if strategy.get("ticker") == ticker:
                        return strategy

        # Default execution parameters
        return config.get("default_parameters", {})

    def list_portfolio_assets(self, portfolio_name: str) -> list[str]:
        """List all assets in a portfolio.

        Args:
            portfolio_name: Name of the portfolio

        Returns:
            List[str]: List of asset ticker symbols

        Raises:
            PortfolioCompositionError: If portfolio cannot be loaded
        """
        try:
            business_config, _ = self.load_portfolio_composition(portfolio_name)
            assets = business_config.get("assets", [])
            return [asset.get("ticker") for asset in assets if asset.get("ticker")]

        except Exception as e:
            msg = f"Error listing assets for portfolio {portfolio_name}: {e!s}"
            raise PortfolioCompositionError(
                msg,
            )

    def get_portfolio_allocation(self, portfolio_name: str) -> dict[str, Any]:
        """Get portfolio allocation configuration.

        Args:
            portfolio_name: Name of the portfolio

        Returns:
            Dict[str, Any]: Portfolio allocation configuration

        Raises:
            PortfolioCompositionError: If allocation cannot be retrieved
        """
        try:
            business_config, _ = self.load_portfolio_composition(portfolio_name)
            return business_config.get("allocation", {})

        except Exception as e:
            msg = f"Error getting allocation for portfolio {portfolio_name}: {e!s}"
            raise PortfolioCompositionError(
                msg,
            )

    def get_portfolio_risk_management(self, portfolio_name: str) -> dict[str, Any]:
        """Get portfolio risk management configuration.

        Args:
            portfolio_name: Name of the portfolio

        Returns:
            Dict[str, Any]: Portfolio risk management configuration
        """
        try:
            business_config, _ = self.load_portfolio_composition(portfolio_name)
            return business_config.get("risk_management", {})

        except Exception as e:
            msg = f"Error getting risk management for portfolio {portfolio_name}: {e!s}"
            raise PortfolioCompositionError(
                msg,
            )


# Singleton instance for global use
_portfolio_composition_loader = None


def get_portfolio_composition_loader() -> PortfolioCompositionLoader:
    """Get or create the singleton PortfolioCompositionLoader instance.

    Returns:
        PortfolioCompositionLoader: Singleton instance
    """
    global _portfolio_composition_loader
    if _portfolio_composition_loader is None:
        _portfolio_composition_loader = PortfolioCompositionLoader()
    return _portfolio_composition_loader


# Convenience functions for common operations


def load_portfolio_with_execution(
    portfolio_name: str,
    execution_profile: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load portfolio with business and technical configurations.

    Args:
        portfolio_name: Name of the portfolio
        execution_profile: Optional technical execution profile

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any]]: (business_config, technical_config)
    """
    loader = get_portfolio_composition_loader()
    return loader.load_portfolio_composition(portfolio_name, execution_profile)


def get_portfolio_assets(portfolio_name: str) -> list[str]:
    """Get list of assets in a portfolio.

    Args:
        portfolio_name: Name of the portfolio

    Returns:
        List[str]: List of asset ticker symbols
    """
    loader = get_portfolio_composition_loader()
    return loader.list_portfolio_assets(portfolio_name)


def get_asset_strategy(
    portfolio_name: str,
    ticker: str,
    execution_profile: str | None = None,
) -> dict[str, Any]:
    """Get execution strategy for an asset in a portfolio.

    Args:
        portfolio_name: Name of the portfolio
        ticker: Asset ticker symbol
        execution_profile: Optional execution profile

    Returns:
        Dict[str, Any]: Execution strategy configuration
    """
    loader = get_portfolio_composition_loader()
    return loader.get_asset_execution_strategy(
        portfolio_name,
        ticker,
        execution_profile,
    )
