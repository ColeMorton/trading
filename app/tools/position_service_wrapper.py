"""
Position Service Wrapper

Provides backward compatibility layer for legacy trade history utilities
by wrapping the unified PositionService with the old interface.
"""

from app.services import PositionService
from app.services.position_service import TradingSystemConfig

# Global service instance
_position_service = None


def get_config():
    """Get global TradingSystemConfig instance."""
    return TradingSystemConfig()


def set_config(config):
    """Set global configuration (no-op for compatibility)."""
    pass


def get_position_service():
    """Get or create global PositionService instance."""
    global _position_service
    if _position_service is None:
        _position_service = PositionService()
    return _position_service


def add_position_to_portfolio(
    ticker,
    strategy_type,
    short_window,
    long_window,
    signal_window=0,
    entry_date=None,
    entry_price=None,
    exit_date=None,
    exit_price=None,
    position_size=1.0,
    direction="Long",
    portfolio_name="live_signals",
    verify_signal=True,
    config=None,
):
    """Wrapper for PositionService.add_position_to_portfolio."""
    service = get_position_service()
    return service.add_position_to_portfolio(
        ticker=ticker,
        strategy_type=strategy_type,
        short_window=short_window,
        long_window=long_window,
        signal_window=signal_window,
        entry_date=entry_date,
        entry_price=entry_price,
        exit_date=exit_date,
        exit_price=exit_price,
        position_size=position_size,
        direction=direction,
        portfolio_name=portfolio_name,
        verify_signal=verify_signal,
    )


def create_position_record(
    ticker,
    strategy_type,
    short_window,
    long_window,
    signal_window=0,
    entry_date=None,
    entry_price=None,
    exit_date=None,
    exit_price=None,
    position_size=1.0,
    direction="Long",
):
    """Wrapper for PositionService.create_position_record."""
    service = get_position_service()
    return service.create_position_record(
        ticker=ticker,
        strategy_type=strategy_type,
        short_window=short_window,
        long_window=long_window,
        signal_window=signal_window,
        entry_date=entry_date,
        entry_price=entry_price,
        exit_date=exit_date,
        exit_price=exit_price,
        position_size=position_size,
        direction=direction,
    )


def validate_ticker(ticker):
    """Wrapper for PositionService.validate_ticker."""
    service = get_position_service()
    try:
        service.validate_ticker(ticker)
        return True
    except:
        return False


def validate_strategy_type(strategy_type):
    """Wrapper for PositionService.validate_strategy_type."""
    service = get_position_service()
    try:
        service.validate_strategy_type(strategy_type)
        return True
    except:
        return False


def assess_trade_quality(mfe, mae, exit_efficiency=None, return_pct=None):
    """Wrapper for PositionCalculator.assess_trade_quality."""
    service = get_position_service()
    return service.calculator.assess_trade_quality(mfe, mae, return_pct)