"""
Signal Conversion Module.

This module provides standardized functions for converting signals to trades,
ensuring consistency and traceability throughout the system.
"""

from typing import Dict, Any, List, Optional, Callable, Tuple, Union
import numpy as np
import pandas as pd
import polars as pl


class SignalAudit:
    """Class to track signal audit information.
    
    This class maintains a record of signals, their conversion status,
    and reasons for any filtering or rejection.
    """
    
    def __init__(self):
        """Initialize the signal audit trail."""
        self.signals = []
        self.conversions = []
        self.rejections = []
        
    def add_signal(self, date, value, source):
        """Add a signal to the audit trail.
        
        Args:
            date: Date/time of the signal
            value: Signal value (typically 1, -1, or 0)
            source: Source of the signal (e.g., "MA Cross", "RSI Filter")
        """
        self.signals.append({
            "date": date,
            "value": value,
            "source": source
        })
        
    def add_conversion(self, date, signal_value, position_value, reason):
        """Record a successful signal-to-position conversion.
        
        Args:
            date: Date/time of the conversion
            signal_value: Original signal value
            position_value: Resulting position value
            reason: Reason for the conversion
        """
        self.conversions.append({
            "date": date,
            "signal_value": signal_value,
            "position_value": position_value,
            "reason": reason
        })
        
    def add_rejection(self, date, signal_value, reason):
        """Record a rejected signal.
        
        Args:
            date: Date/time of the rejection
            signal_value: Signal value that was rejected
            reason: Reason for the rejection
        """
        self.rejections.append({
            "date": date,
            "signal_value": signal_value,
            "reason": reason
        })
        
    def get_conversion_rate(self):
        """Calculate the signal-to-trade conversion rate.
        
        Returns:
            float: Percentage of signals that were converted to trades
        """
        if not self.signals:
            return 0.0
            
        # Count non-zero signals (actual entry/exit signals)
        non_zero_signals = sum(1 for s in self.signals if s["value"] != 0)
        
        if non_zero_signals == 0:
            return 0.0
            
        return len(self.conversions) / non_zero_signals if non_zero_signals > 0 else 0.0
        
    def get_rejection_reasons(self):
        """Get a summary of rejection reasons.
        
        Returns:
            Dict[str, int]: Count of each rejection reason
        """
        reasons = {}
        for rejection in self.rejections:
            reason = rejection["reason"]
            reasons[reason] = reasons.get(reason, 0) + 1
        return reasons
        
    def get_summary(self):
        """Get a summary of the signal audit.
        
        Returns:
            Dict[str, Any]: Summary statistics
        """
        return {
            "total_signals": len(self.signals),
            "non_zero_signals": sum(1 for s in self.signals if s["value"] != 0),
            "conversions": len(self.conversions),
            "rejections": len(self.rejections),
            "conversion_rate": self.get_conversion_rate(),
            "rejection_reasons": self.get_rejection_reasons()
        }
        
    def to_dataframe(self):
        """Convert the audit trail to a DataFrame.
        
        Returns:
            pd.DataFrame: Audit trail as a DataFrame
        """
        # Combine signals, conversions, and rejections into a single timeline
        events = []
        
        for signal in self.signals:
            events.append({
                "date": signal["date"],
                "event_type": "Signal",
                "value": signal["value"],
                "source": signal["source"],
                "reason": None
            })
            
        for conversion in self.conversions:
            events.append({
                "date": conversion["date"],
                "event_type": "Conversion",
                "value": conversion["position_value"],
                "source": None,
                "reason": conversion["reason"]
            })
            
        for rejection in self.rejections:
            events.append({
                "date": rejection["date"],
                "event_type": "Rejection",
                "value": rejection["signal_value"],
                "source": None,
                "reason": rejection["reason"]
            })
            
        # Convert to DataFrame and sort by date
        df = pd.DataFrame(events)
        if not df.empty:
            df = df.sort_values("date")
            
        return df


def convert_signals_to_positions(
    data: Union[pl.DataFrame, pd.DataFrame],
    config: Dict[str, Any],
    log: Callable[[str, str], None],
    audit: Optional[SignalAudit] = None
) -> Tuple[Union[pl.DataFrame, pd.DataFrame], SignalAudit]:
    """Convert signals to positions with comprehensive tracking and filtering.
    
    This function applies various filters to signals before converting them to positions,
    tracking each step in the process for auditability.
    
    Args:
        data: DataFrame containing at minimum a 'Date' and 'Signal' column
        config: Configuration dictionary containing filtering parameters
        log: Logging function for recording events and errors
        audit: Optional SignalAudit object for tracking (created if not provided)
        
    Returns:
        Tuple containing:
            - DataFrame with added 'Position' column
            - SignalAudit object with tracking information
    """
    # Create audit object if not provided
    if audit is None:
        audit = SignalAudit()
        
    # Convert to pandas if polars
    is_polars = isinstance(data, pl.DataFrame)
    if is_polars:
        data_pd = data.to_pandas()
    else:
        data_pd = data
        
    log(f"Converting signals to positions with {len(data_pd)} rows", "info")
    
    # Extract configuration parameters
    strategy_type = config.get('STRATEGY_TYPE', 'MA Cross')
    direction = config.get('DIRECTION', 'Long')
    use_rsi = config.get('USE_RSI', False)
    rsi_threshold = config.get('RSI_THRESHOLD', 70)
    stop_loss = config.get('STOP_LOSS')
    
    # Record all signals in the audit trail
    for idx, row in data_pd.iterrows():
        if 'Signal' in row and row['Signal'] != 0:
            audit.add_signal(
                date=row['Date'],
                value=row['Signal'],
                source=strategy_type
            )
    
    # Apply RSI filter if configured
    if use_rsi and 'RSI' in data_pd.columns:
        log(f"Applying RSI filter with threshold {rsi_threshold}", "info")
        
        # Create a copy of the original signals for comparison
        original_signals = data_pd['Signal'].copy()
        
        # Apply RSI filter based on direction
        if direction == 'Long':
            # For long positions, only enter when RSI >= threshold
            data_pd.loc[(data_pd['Signal'] != 0) & (data_pd['RSI'] < rsi_threshold), 'Signal'] = 0
        else:
            # For short positions, only enter when RSI <= (100 - threshold)
            data_pd.loc[(data_pd['Signal'] != 0) & (data_pd['RSI'] > (100 - rsi_threshold)), 'Signal'] = 0
            
        # Record rejections in the audit trail
        for idx, row in data_pd.iterrows():
            if original_signals[idx] != 0 and row['Signal'] == 0:
                audit.add_rejection(
                    date=row['Date'],
                    signal_value=original_signals[idx],
                    reason=f"RSI Filter: {'below' if direction == 'Long' else 'above'} threshold"
                )
                
        log(f"RSI filter rejected {sum(original_signals != 0) - sum(data_pd['Signal'] != 0)} signals", "info")
    
    # Create Position column (shifted Signal)
    log("Creating Position column from Signal", "info")
    data_pd['Position'] = data_pd['Signal'].shift(1).fillna(0)
    
    # Record conversions in the audit trail
    for idx, row in data_pd.iterrows():
        if idx > 0 and data_pd.iloc[idx-1]['Signal'] != 0:
            audit.add_conversion(
                date=row['Date'],
                signal_value=data_pd.iloc[idx-1]['Signal'],
                position_value=row['Position'],
                reason="Standard signal shift"
            )
    
    # Log conversion statistics
    summary = audit.get_summary()
    log(f"Signal conversion complete: {summary['conversions']} positions from {summary['non_zero_signals']} signals "
        f"({summary['conversion_rate']*100:.1f}% conversion rate)", "info")
    
    if summary['rejections'] > 0:
        log(f"Rejected {summary['rejections']} signals: {audit.get_rejection_reasons()}", "info")
    
    # Convert back to polars if needed
    if is_polars:
        result = pl.from_pandas(data_pd)
    else:
        result = data_pd
        
    return result, audit


def analyze_signal_conversion(
    audit: SignalAudit,
    log: Callable[[str, str], None]
) -> Dict[str, Any]:
    """Analyze signal conversion metrics.
    
    Args:
        audit: SignalAudit object with tracking information
        log: Logging function for recording events and errors
        
    Returns:
        Dict[str, Any]: Dictionary of signal conversion metrics
    """
    summary = audit.get_summary()
    
    # Calculate additional metrics
    metrics = {
        "signal_count": summary["total_signals"],
        "non_zero_signal_count": summary["non_zero_signals"],
        "position_count": summary["conversions"],
        "rejection_count": summary["rejections"],
        "conversion_rate": summary["conversion_rate"],
        "rejection_rate": summary["rejections"] / summary["non_zero_signals"] if summary["non_zero_signals"] > 0 else 0.0,
        "rejection_reasons": summary["rejection_reasons"]
    }
    
    # Log the metrics
    log(f"Signal conversion metrics: {metrics['conversion_rate']*100:.1f}% conversion rate, "
        f"{metrics['rejection_rate']*100:.1f}% rejection rate", "info")
    
    return metrics


def export_signal_audit(
    audit: SignalAudit,
    filename: str,
    log: Callable[[str, str], None]
) -> bool:
    """Export the signal audit trail to a CSV file.
    
    Args:
        audit: SignalAudit object with tracking information
        filename: Path to save the CSV file
        log: Logging function for recording events and errors
        
    Returns:
        bool: True if export successful, False otherwise
    """
    try:
        df = audit.to_dataframe()
        df.to_csv(filename, index=False)
        log(f"Exported signal audit trail to {filename}", "info")
        return True
    except Exception as e:
        log(f"Failed to export signal audit trail: {str(e)}", "error")
        return False