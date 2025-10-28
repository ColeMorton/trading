"""
Integration tests for logging flow.

Tests end-to-end logging with console display.
"""

import pytest

from app.core.logging_factory import bind_context, clear_context, get_logger
from app.ui.console_display import ConsoleDisplay


def test_basic_logging_flow():
    """Test basic logging and display flow."""
    logger = get_logger(__name__)
    console = ConsoleDisplay(quiet=True)  # Quiet to avoid test output

    # Start operation
    console.show_progress("Starting operation")
    logger.info("operation_started", operation="test")

    # Do work
    logger.info("processing", items=10)

    # Complete
    console.show_success("Operation completed")
    logger.info("operation_completed", success=True)


def test_logging_with_context():
    """Test logging with context binding."""
    logger = get_logger(__name__)

    # Bind context
    bind_context(operation_id="test_123", user="test_user")

    # Log with context
    logger.info("context_test", action="testing")

    # Clear context
    clear_context()


def test_error_flow():
    """Test error logging and display flow."""
    logger = get_logger(__name__)
    console = ConsoleDisplay(quiet=True)

    try:
        # Simulate error
        msg = "Test error"
        raise ValueError(msg)
    except ValueError as e:
        console.show_error(f"Error occurred: {e!s}")
        logger.error("error_occurred", error=str(e), exc_info=True)


def test_multi_phase_operation():
    """Test multi-phase operation with logging and display."""
    logger = get_logger(__name__)
    console = ConsoleDisplay(quiet=True)

    # Phase 1
    console.show_heading("Phase 1: Data Loading", level=2)
    logger.info("phase_started", phase="data_loading")
    logger.info("phase_completed", phase="data_loading", duration=1.5)

    # Phase 2
    console.show_heading("Phase 2: Processing", level=2)
    logger.info("phase_started", phase="processing")
    logger.info("phase_completed", phase="processing", duration=3.2)

    # Phase 3
    console.show_heading("Phase 3: Export", level=2)
    logger.info("phase_started", phase="export")
    logger.info("phase_completed", phase="export", duration=0.8)

    # Summary
    console.show_completion_banner("All phases completed")
    logger.info("operation_completed", total_duration=5.5)


def test_structured_logging_data():
    """Test structured logging with various data types."""
    logger = get_logger(__name__)

    # Log with structured data
    logger.info(
        "trading_signal",
        ticker="AAPL",
        signal="BUY",
        price=150.25,
        quantity=100,
        confidence=0.85,
        indicators=["SMA", "RSI", "MACD"],
        metadata={"source": "algorithm", "version": "1.0"},
    )


def test_performance_monitoring_flow():
    """Test performance monitoring integration."""
    from app.monitoring.performance_logger import PerformanceLogger

    perf_logger = PerformanceLogger(
        __name__,
        performance_mode="minimal",
        show_resources=False,
    )

    # Start monitoring
    perf_logger.start_execution_monitoring("test_operation")

    # Execute phases
    perf_logger.start_phase("phase1", "Test phase 1")
    # Simulate work
    import time

    time.sleep(0.1)
    perf_logger.end_phase(success=True)

    perf_logger.start_phase("phase2", "Test phase 2")
    time.sleep(0.1)
    perf_logger.end_phase(success=True)

    # Complete
    perf_logger.complete_execution_monitoring()


def test_console_and_logger_separation():
    """Test that console and logger are properly separated."""
    logger = get_logger(__name__)
    console = ConsoleDisplay(quiet=True)

    # These are separate concerns
    console.show_info("User-facing message")  # Display only
    logger.info("audit_event", event_type="test")  # Log only

    # Should both work without interfering
    console.show_success("Task completed")
    logger.info("task_completed", task_id="123")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
