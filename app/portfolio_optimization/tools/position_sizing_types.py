"""Type definitions for position sizing calculations."""

from typing import TypedDict, List, Dict

class Asset(TypedDict):
    """Configuration type definition for an asset.
    
    Required Fields:
        ticker (str): Asset ticker symbol
        leverage (float): Leverage ratio for the asset
        weight (float): Target portfolio weight as a percentage
    """
    ticker: str
    leverage: float
    weight: float

class PositionSizingConfig(TypedDict):
    """Configuration type definition for position sizing.
    
    Required Fields:
        total_value (float): Total portfolio value
        use_ema (bool): Whether to use EMA for price calculations
        ema_period (int): Period for EMA calculation if used
    """
    total_value: float
    use_ema: bool
    ema_period: int

class AssetMetrics(TypedDict):
    """Metrics calculated for each asset.
    
    Required Fields:
        initial_value (float): Initial (pre-leverage) position value
        leveraged_value (float): Position value after applying leverage
        position_size (float): Actual position size in units
        allocation (float): Actual portfolio allocation percentage
        var_cvar (Dict[float, tuple[float, float]]): VaR and CVaR at each confidence level
    """
    initial_value: float
    leveraged_value: float
    position_size: float
    allocation: float
    var_cvar: Dict[float, tuple[float, float]]