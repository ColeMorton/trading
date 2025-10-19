"""
Simplified Analysis Result for Enhanced Parameter Support

This module provides a simplified result structure for the enhanced
parameter analyzers that doesn't require the full complexity of the
StatisticalAnalysisResult model.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SimpleAnalysisResult(BaseModel):
    """Simplified analysis result for enhanced parameter analyzers."""

    # Basic identification
    strategy_name: str = Field(description="Strategy or analysis identifier")
    ticker: str = Field(description="Asset ticker")
    analysis_timestamp: str = Field(description="Analysis timestamp (ISO format)")

    # Core analysis results
    exit_signal: str = Field(
        description="Recommendation signal (supports BUY/SELL/HOLD)"
    )
    confidence_level: float = Field(
        ge=0.0, le=1.0, description="Confidence level (0-1)"
    )
    p_value: float = Field(ge=0.0, le=1.0, description="Statistical p-value")
    sample_size: int = Field(ge=0, description="Sample size used in analysis")

    # Data source and analysis mode
    data_source: str = Field(description="Primary data source used")
    analysis_mode: str = Field(description="Type of analysis performed")

    # Additional metrics (flexible)
    metrics: dict[str, Any] = Field(
        default_factory=dict, description="Additional analysis metrics"
    )

    class Config:
        """Pydantic configuration."""

        extra = "allow"
        use_enum_values = True


def convert_to_standard_result(simple_result: SimpleAnalysisResult) -> dict[str, Any]:
    """
    Convert SimpleAnalysisResult to a format compatible with existing output functions.

    Args:
        simple_result: Simplified analysis result

    Returns:
        Dictionary compatible with existing SPDS output functions
    """

    # Create a mock object that behaves like StatisticalAnalysisResult for display purposes
    class MockResult:
        def __init__(self, simple_result: SimpleAnalysisResult):
            self.strategy_name = simple_result.strategy_name
            self.ticker = simple_result.ticker
            # Handle exit_signal - create object with signal_type for export compatibility
            self.exit_signal = self._create_exit_signal_mock(simple_result.exit_signal)
            self.confidence = (
                simple_result.confidence_level * 100
            )  # Convert to percentage
            self.confidence_level = simple_result.confidence_level * 100
            self.overall_confidence = simple_result.confidence_level * 100
            self.p_value = simple_result.p_value
            self.sample_size = simple_result.sample_size
            self.data_source = simple_result.data_source
            # Handle analysis_timestamp conversion for export compatibility
            if isinstance(simple_result.analysis_timestamp, str):
                # Already ISO format string, convert to datetime for compatibility
                from datetime import datetime

                self.analysis_timestamp = datetime.fromisoformat(
                    simple_result.analysis_timestamp.replace("Z", "+00:00")
                )
            else:
                self.analysis_timestamp = simple_result.analysis_timestamp
            self.divergence_metrics = simple_result.metrics
            self.analysis_mode = simple_result.analysis_mode

            # Add required attributes for export compatibility
            self.timeframe = "D"  # Default timeframe for enhanced analysis
            self.performance_metrics = {}  # Empty dict for enhanced analysis
            self.sample_size_confidence = (
                0.95  # Default confidence level for enhanced analysis
            )

            # Add strategy_analysis attribute for export compatibility
            self.strategy_analysis = self._create_strategy_analysis_mock(simple_result)

            # Add dual_layer_convergence attribute for export compatibility
            self.dual_layer_convergence = self._create_dual_layer_convergence_mock()

            # Add recommendation as an alias for exit_signal
            self.recommendation = self.exit_signal

        def _create_strategy_analysis_mock(self, simple_result: SimpleAnalysisResult):
            """Create a minimal strategy_analysis object for export compatibility."""

            class StrategyAnalysisMock:
                def __init__(self):
                    self.timeframe = "D"  # Default timeframe for enhanced analysis
                    self.trade_history_analysis = (
                        None  # Not applicable for enhanced analysis
                    )
                    self.equity_analysis = None  # Not applicable for enhanced analysis
                    self.dual_source_convergence = (
                        None  # Not applicable for enhanced analysis
                    )

            return StrategyAnalysisMock()

        def _create_dual_layer_convergence_mock(self):
            """Create a minimal dual_layer_convergence object for export compatibility."""

            class DualLayerConvergenceMock:
                def __init__(self):
                    self.sample_size = 0  # Enhanced analysis doesn't use dual layer
                    self.convergence_score = (
                        0.0  # Use 0.0 instead of None to avoid comparison errors
                    )
                    self.asset_layer_percentile = (
                        0.0  # Use 0.0 instead of None to avoid comparison errors
                    )
                    self.strategy_layer_percentile = (
                        0.0  # Use 0.0 instead of None to avoid comparison errors
                    )

            return DualLayerConvergenceMock()

        def _create_exit_signal_mock(self, exit_signal_value: str):
            """Create an exit signal object with signal_type for export compatibility."""

            class ExitSignalMock:
                def __init__(self, signal_value: str):
                    # Create a nested signal_type object that has a value attribute
                    class SignalTypeMock:
                        def __init__(self, value: str):
                            self.value = value

                        def __str__(self):
                            return self.value

                    # Create a nested statistical_validity object that has a value attribute
                    class StatisticalValidityMock:
                        def __init__(self, value: str):
                            self.value = value

                        def __str__(self):
                            return self.value

                    self.signal_type = SignalTypeMock(
                        signal_value
                    )  # Required for export with .value access
                    self.statistical_validity = StatisticalValidityMock(
                        "ENHANCED_ANALYSIS"
                    )  # For export compatibility
                    # Also preserve the string value for direct access
                    self.value = signal_value

                def __str__(self):
                    return self.value

                def __eq__(self, other):
                    if isinstance(other, str):
                        return self.value == other
                    return self.value == getattr(other, "value", other)

            return ExitSignalMock(exit_signal_value)

    return MockResult(simple_result)


def create_simple_result(
    strategy_name: str,
    ticker: str,
    exit_signal: str = "HOLD",
    confidence_level: float = 0.75,
    p_value: float = 0.15,
    sample_size: int = 20,
    data_source: str = "ENHANCED_ANALYSIS",
    analysis_mode: str = "ENHANCED_PARAMETER",
    **additional_metrics,
) -> SimpleAnalysisResult:
    """
    Create a simple analysis result with default values.

    Args:
        strategy_name: Strategy or analysis identifier
        ticker: Asset ticker
        exit_signal: Exit signal recommendation
        confidence_level: Confidence level (0-1)
        p_value: Statistical p-value
        sample_size: Sample size used
        data_source: Primary data source
        analysis_mode: Type of analysis
        **additional_metrics: Additional metrics to include

    Returns:
        SimpleAnalysisResult object
    """
    return SimpleAnalysisResult(
        strategy_name=strategy_name,
        ticker=ticker,
        analysis_timestamp=datetime.now().isoformat(),
        exit_signal=exit_signal,
        confidence_level=confidence_level,
        p_value=p_value,
        sample_size=sample_size,
        data_source=data_source,
        analysis_mode=analysis_mode,
        metrics=additional_metrics,
    )
