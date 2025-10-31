"""
Tests for logging factory.

Smoke tests to verify basic logging functionality.
"""

import pytest

from app.core.logging_factory import (
    bind_context,
    clear_context,
    get_logger,
    unbind_context,
)


@pytest.mark.unit
def test_get_logger_basic():
    """Test basic logger creation."""
    logger = get_logger(__name__)
    assert logger is not None


@pytest.mark.unit
def test_get_logger_with_name():
    """Test logger creation with specific name."""
    logger = get_logger("test.module")
    assert logger is not None


@pytest.mark.unit
def test_get_logger_with_context():
    """Test logger creation with initial context."""
    logger = get_logger(__name__, request_id="123", user_id="user456")
    assert logger is not None


@pytest.mark.unit
def test_logger_info():
    """Test basic info logging."""
    logger = get_logger(__name__)
    # Should not raise
    logger.info("test_event", key="value")


@pytest.mark.unit
def test_logger_error():
    """Test error logging."""
    logger = get_logger(__name__)
    # Should not raise
    logger.error("test_error", error="something went wrong")


@pytest.mark.unit
def test_logger_warning():
    """Test warning logging."""
    logger = get_logger(__name__)
    # Should not raise
    logger.warning("test_warning", severity="medium")


@pytest.mark.unit
def test_logger_debug():
    """Test debug logging."""
    logger = get_logger(__name__)
    # Should not raise
    logger.debug("test_debug", details="debug info")


@pytest.mark.unit
def test_context_binding():
    """Test context binding."""
    logger = get_logger(__name__)

    # Bind context
    bind_context(request_id="abc123")

    # Should not raise
    logger.info("test_with_context")

    # Clear context
    clear_context()


@pytest.mark.unit
def test_context_unbinding():
    """Test selective context unbinding."""
    logger = get_logger(__name__)

    # Bind multiple context values
    bind_context(request_id="abc123", user_id="user456")

    # Should not raise
    logger.info("test_with_context")

    # Unbind one key
    unbind_context("request_id")

    # Should still work
    logger.info("test_after_unbind")

    # Clear all
    clear_context()


@pytest.mark.unit
def test_logger_with_exception():
    """Test logging with exception info."""
    logger = get_logger(__name__)

    try:
        msg = "Test error"
        raise ValueError(msg)
    except ValueError as e:
        # Should not raise
        logger.error("test_exception", error=str(e), exc_info=True)


@pytest.mark.unit
def test_multiple_loggers():
    """Test creating multiple loggers."""
    logger1 = get_logger("module1")
    logger2 = get_logger("module2")

    assert logger1 is not None
    assert logger2 is not None

    # Should not raise
    logger1.info("event1")
    logger2.info("event2")


@pytest.mark.unit
def test_logger_with_numeric_values():
    """Test logging with various numeric types."""
    logger = get_logger(__name__)

    # Should not raise
    logger.info("numeric_test", count=100, price=150.25, percentage=0.95, is_valid=True)


@pytest.mark.unit
def test_logger_with_complex_data():
    """Test logging with dict and list data."""
    logger = get_logger(__name__)

    # Should not raise
    logger.info(
        "complex_test",
        config={"setting1": "value1", "setting2": 42},
        items=["item1", "item2", "item3"],
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
