"""
Tests for the signal conversion module.
"""

import unittest
import pandas as pd
import polars as pl
import numpy as np
from datetime import datetime, timedelta
from app.tools.signal_conversion import (
    SignalAudit,
    convert_signals_to_positions,
    analyze_signal_conversion,
    export_signal_audit
)


class MockLogger:
    """Mock logger for testing."""
    
    def __init__(self):
        self.logs = []
    
    def __call__(self, message, level="info"):
        self.logs.append((message, level))


class TestSignalAudit(unittest.TestCase):
    """Test cases for the SignalAudit class."""
    
    def test_add_signal(self):
        """Test adding signals to the audit trail."""
        audit = SignalAudit()
        
        # Add some signals
        audit.add_signal(
            date=datetime(2023, 1, 1),
            value=1,
            source="MA Cross"
        )
        audit.add_signal(
            date=datetime(2023, 1, 2),
            value=-1,
            source="RSI Filter"
        )
        
        # Verify signals were added
        self.assertEqual(len(audit.signals), 2)
        self.assertEqual(audit.signals[0]["value"], 1)
        self.assertEqual(audit.signals[1]["source"], "RSI Filter")
    
    def test_add_conversion(self):
        """Test recording signal conversions."""
        audit = SignalAudit()
        
        # Add a conversion
        audit.add_conversion(
            date=datetime(2023, 1, 1),
            signal_value=1,
            position_value=1,
            reason="Standard signal shift"
        )
        
        # Verify conversion was added
        self.assertEqual(len(audit.conversions), 1)
        self.assertEqual(audit.conversions[0]["signal_value"], 1)
        self.assertEqual(audit.conversions[0]["reason"], "Standard signal shift")
    
    def test_add_rejection(self):
        """Test recording signal rejections."""
        audit = SignalAudit()
        
        # Add a rejection
        audit.add_rejection(
            date=datetime(2023, 1, 1),
            signal_value=1,
            reason="RSI below threshold"
        )
        
        # Verify rejection was added
        self.assertEqual(len(audit.rejections), 1)
        self.assertEqual(audit.rejections[0]["signal_value"], 1)
        self.assertEqual(audit.rejections[0]["reason"], "RSI below threshold")
    
    def test_get_conversion_rate(self):
        """Test calculating the conversion rate."""
        audit = SignalAudit()
        
        # Add signals and conversions
        for i in range(10):
            audit.add_signal(
                date=datetime(2023, 1, 1) + timedelta(days=i),
                value=1 if i % 2 == 0 else 0,  # 5 non-zero signals
                source="MA Cross"
            )
            
        # Add 3 conversions
        for i in range(3):
            audit.add_conversion(
                date=datetime(2023, 1, 1) + timedelta(days=i),
                signal_value=1,
                position_value=1,
                reason="Standard signal shift"
            )
        
        # Verify conversion rate
        self.assertEqual(audit.get_conversion_rate(), 3/5)
    
    def test_get_rejection_reasons(self):
        """Test summarizing rejection reasons."""
        audit = SignalAudit()
        
        # Add rejections with different reasons
        audit.add_rejection(
            date=datetime(2023, 1, 1),
            signal_value=1,
            reason="RSI below threshold"
        )
        audit.add_rejection(
            date=datetime(2023, 1, 2),
            signal_value=1,
            reason="RSI below threshold"
        )
        audit.add_rejection(
            date=datetime(2023, 1, 3),
            signal_value=-1,
            reason="Stop loss triggered"
        )
        
        # Verify rejection reasons
        reasons = audit.get_rejection_reasons()
        self.assertEqual(reasons["RSI below threshold"], 2)
        self.assertEqual(reasons["Stop loss triggered"], 1)
    
    def test_to_dataframe(self):
        """Test converting the audit trail to a DataFrame."""
        audit = SignalAudit()
        
        # Add signals, conversions, and rejections
        audit.add_signal(
            date=datetime(2023, 1, 1),
            value=1,
            source="MA Cross"
        )
        audit.add_conversion(
            date=datetime(2023, 1, 2),
            signal_value=1,
            position_value=1,
            reason="Standard signal shift"
        )
        audit.add_rejection(
            date=datetime(2023, 1, 3),
            signal_value=-1,
            reason="RSI below threshold"
        )
        
        # Convert to DataFrame
        df = audit.to_dataframe()
        
        # Verify DataFrame
        self.assertEqual(len(df), 3)
        self.assertEqual(df["event_type"].tolist(), ["Signal", "Conversion", "Rejection"])


class TestSignalConversion(unittest.TestCase):
    """Test cases for signal conversion functions."""
    
    def test_convert_signals_to_positions_pandas(self):
        """Test converting signals to positions with pandas DataFrame."""
        # Create test data
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        data = pd.DataFrame({
            'Date': dates,
            'Signal': [0, 1, 0, -1, 0, 1, 0, 0, -1, 0],
            'RSI': [50, 75, 50, 25, 50, 65, 50, 50, 35, 50]
        })
        
        # Create config and logger
        config = {
            'STRATEGY_TYPE': 'MA Cross',
            'DIRECTION': 'Long',
            'USE_RSI': False
        }
        log = MockLogger()
        
        # Convert signals to positions
        result, audit = convert_signals_to_positions(data, config, log)
        
        # Verify positions
        expected_positions = [0, 0, 1, 0, -1, 0, 1, 0, 0, -1]
        self.assertEqual(result['Position'].tolist(), expected_positions)
        
        # Verify audit trail
        self.assertEqual(len(audit.signals), 4)  # 4 non-zero signals
        self.assertEqual(len(audit.conversions), 4)  # All signals converted
        self.assertEqual(len(audit.rejections), 0)  # No rejections
    
    def test_convert_signals_to_positions_polars(self):
        """Test converting signals to positions with polars DataFrame."""
        # Create test data
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        data_pd = pd.DataFrame({
            'Date': dates,
            'Signal': [0, 1, 0, -1, 0, 1, 0, 0, -1, 0],
            'RSI': [50, 75, 50, 25, 50, 65, 50, 50, 35, 50]
        })
        data = pl.from_pandas(data_pd)
        
        # Create config and logger
        config = {
            'STRATEGY_TYPE': 'MA Cross',
            'DIRECTION': 'Long',
            'USE_RSI': False
        }
        log = MockLogger()
        
        # Convert signals to positions
        result, audit = convert_signals_to_positions(data, config, log)
        
        # Verify positions
        expected_positions = [0, 0, 1, 0, -1, 0, 1, 0, 0, -1]
        self.assertEqual(result['Position'].to_list(), expected_positions)
        
        # Verify audit trail
        self.assertEqual(len(audit.signals), 4)  # 4 non-zero signals
        self.assertEqual(len(audit.conversions), 4)  # All signals converted
        self.assertEqual(len(audit.rejections), 0)  # No rejections
    
    def test_rsi_filter(self):
        """Test RSI filtering of signals."""
        # Create test data
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        data = pd.DataFrame({
            'Date': dates,
            'Signal': [0, 1, 0, -1, 0, 1, 0, 0, -1, 0],
            'RSI': [50, 65, 50, 25, 50, 65, 50, 50, 35, 50]
        })
        
        # Create config with RSI filter
        config = {
            'STRATEGY_TYPE': 'MA Cross',
            'DIRECTION': 'Long',
            'USE_RSI': True,
            'RSI_THRESHOLD': 70  # Should filter out all signals since all RSI values are below 70
        }
        log = MockLogger()
        
        # Convert signals to positions
        result, audit = convert_signals_to_positions(data, config, log)
        
        # Verify positions (all signals should be filtered out)
        expected_positions = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.assertEqual(result['Position'].tolist(), expected_positions)
        
        # Verify audit trail
        self.assertEqual(len(audit.signals), 4)  # 4 non-zero signals
        self.assertEqual(len(audit.conversions), 0)  # 0 signals converted
        self.assertEqual(len(audit.rejections), 4)  # 4 rejections
        self.assertEqual(audit.get_conversion_rate(), 0.0)  # 0% conversion rate
    
    def test_analyze_signal_conversion(self):
        """Test analyzing signal conversion metrics."""
        audit = SignalAudit()
        
        # Add signals, conversions, and rejections
        for i in range(10):
            audit.add_signal(
                date=datetime(2023, 1, 1) + timedelta(days=i),
                value=1 if i < 8 else 0,  # 8 non-zero signals
                source="MA Cross"
            )
            
        # Add 6 conversions
        for i in range(6):
            audit.add_conversion(
                date=datetime(2023, 1, 1) + timedelta(days=i),
                signal_value=1,
                position_value=1,
                reason="Standard signal shift"
            )
            
        # Add 2 rejections
        for i in range(6, 8):
            audit.add_rejection(
                date=datetime(2023, 1, 1) + timedelta(days=i),
                signal_value=1,
                reason="RSI below threshold"
            )
        
        # Analyze conversion metrics
        log = MockLogger()
        metrics = analyze_signal_conversion(audit, log)
        
        # Verify metrics
        self.assertEqual(metrics["signal_count"], 10)
        self.assertEqual(metrics["non_zero_signal_count"], 8)
        self.assertEqual(metrics["position_count"], 6)
        self.assertEqual(metrics["rejection_count"], 2)
        self.assertEqual(metrics["conversion_rate"], 6/8)
        self.assertEqual(metrics["rejection_rate"], 2/8)


if __name__ == "__main__":
    unittest.main()