from typing import TypedDict, List, Dict, NotRequired

class PortfolioAsset(TypedDict):
    """
    Represents an asset in the portfolio.

    Required Fields:
        ticker (str): The ticker symbol of the asset.
        leverage (float): The leverage applied to the asset.
        weight (float): The weight of the asset in the portfolio.
    """
    ticker: str
    leverage: float
    weight: float

class PortfolioConfig(TypedDict):
    """
    Represents the portfolio configuration.

    Required Fields:
        initial_value (float): The initial value of the portfolio.
        target_value (float): The target value of the portfolio.
        use_target_value (bool): Whether to use the target value.
        portfolio (List[PortfolioAsset]): A list of portfolio assets.
    """
    initial_value: float
    target_value: float
    use_target_value: bool
    portfolio: List[PortfolioAsset]

class PortfolioMetrics(TypedDict):
    """
    Represents the portfolio metrics.

    Required Fields:
        annualized_return (float): The annualized return of the portfolio.
        downside_volatility (float): The downside volatility of the portfolio.
        sortino_ratio (float): The Sortino ratio of the portfolio.
        var_95 (float): The Value at Risk (VaR) at 95% confidence level.
        cvar_95 (float): The Conditional Value at Risk (CVaR) at 95% confidence level.
        var_99 (float): The Value at Risk (VaR) at 99% confidence level.
        cvar_99 (float): The Conditional Value at Risk (CVaR) at 99% confidence level.
    """
    annualized_return: float
    downside_volatility: float
    sortino_ratio: float
    var_95: float
    cvar_95: float
    var_99: float
    cvar_99: float

class AssetMetrics(TypedDict):
    """
    Represents the metrics for a single asset.

    Required Fields:
        weight (float): The weight of the asset in the portfolio.
        annualized_return (float): The annualized return of the asset.
        downside_volatility (float): The downside volatility of the asset.
        sortino_ratio (float): The Sortino ratio of the asset.
        var (float): The Value at Risk (VaR) of the asset.
        cvar (float): The Conditional Value at Risk (CVaR) of the asset.
    """
    weight: float
    annualized_return: float
    downside_volatility: float
    sortino_ratio: float
    var: float
    cvar: float

class AnalysisOutput(TypedDict):
    """
    Represents the output of the portfolio analysis.

    Required Fields:
        initial_value (float): The initial value of the portfolio.
        target_value (float): The target value of the portfolio.
        use_target_value (bool): Whether to use the target value.
        portfolio (List[PortfolioAsset]): The portfolio configuration.
        portfolio_metrics (PortfolioMetrics): The portfolio metrics.
        asset_metrics (Dict[str, AssetMetrics]): The asset metrics.
    """
    initial_value: float
    target_value: float
    use_target_value: bool
    portfolio: List[PortfolioAsset]
    portfolio_metrics: PortfolioMetrics
    asset_metrics: Dict[str, AssetMetrics]

class PositionSizingConfig(TypedDict):
    """
    Represents the position sizing configuration.

    Required Fields:
        use_ema (bool): Whether to use EMA for price calculations.
        ema_period (int): The period for EMA if used.
        var_confidence_levels (List[float]): A list of VaR confidence levels.
    """
    use_ema: bool
    ema_period: int
    var_confidence_levels: List[float]

class SizingAssetMetrics(TypedDict):
    """
    Represents the metrics for a single asset in the position sizing output.

    Required Fields:
        ticker (str): The ticker symbol of the asset.
        initial_value (float): The initial value of the asset.
        leveraged_value (float): The leveraged value of the asset.
        position_size (float): The position size of the asset.
        allocation (float): The allocation of the asset in the portfolio.
    """
    ticker: str
    initial_value: float
    leveraged_value: float
    position_size: float
    allocation: float

class SizingOutput(TypedDict):
    """
    Represents the output of the position sizing calculation.

    Required Fields:
        initial_value (float): The initial value of the portfolio.
        target_value (float): The target value of the portfolio.
        use_target_value (bool): Whether to use the target value.
        portfolio (List[PortfolioAsset]): The portfolio configuration.
        position_sizing_config (PositionSizingConfig): The position sizing configuration.
        total_leveraged_value (float): The total leveraged value of the portfolio.
        initial_portfolio_value (float): The initial portfolio value.
        asset_metrics (List[SizingAssetMetrics]): The asset metrics for each asset in the portfolio.
    """
    initial_value: float
    target_value: float
    use_target_value: bool
    portfolio: List[PortfolioAsset]
    position_sizing_config: PositionSizingConfig
    total_leveraged_value: float
    initial_portfolio_value: float
    asset_metrics: List[SizingAssetMetrics]