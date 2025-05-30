"""Tests for the concurrency error handling system.

Tests all components of the unified error handling framework including
exceptions, context managers, decorators, recovery mechanisms, and registry.
"""

import pytest
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, call
from datetime import datetime, timedelta

from app.concurrency.error_handling import (
    # Exceptions
    ConcurrencyError,
    StrategyProcessingError,
    PermutationAnalysisError,
    ConcurrencyAnalysisError,
    ReportGenerationError,
    VisualizationError,
    OptimizationError,
    DataAlignmentError,
    ValidationError,
    
    # Context managers
    concurrency_error_context,
    strategy_processing_context,
    permutation_analysis_context,
    report_generation_context,
    batch_operation_context,
    
    # Decorators
    handle_concurrency_errors,
    validate_inputs,
    retry_on_failure,
    track_performance,
    require_fields,
    
    # Recovery
    ErrorRecoveryPolicy,
    RecoveryStrategy,
    RecoveryAction,
    create_recovery_policy,
    apply_error_recovery,
    get_recovery_policy,
    create_fallback_function,
    
    # Registry
    ErrorRegistry,
    get_error_registry,
    track_error,
    get_error_stats,
    ErrorRecord,
    ErrorStats
)


class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_concurrency_error_basic(self):
        """Test basic ConcurrencyError functionality."""
        error = ConcurrencyError("Test error")
        assert str(error) == "Test error"
        assert error.context == {}
        assert error.module == "concurrency"
    
    def test_concurrency_error_with_context(self):
        """Test ConcurrencyError with context data."""
        context = {"key": "value", "number": 42}
        error = ConcurrencyError("Test error", context)
        assert error.context == context
    
    def test_strategy_processing_error(self):
        """Test StrategyProcessingError specifics."""
        error = StrategyProcessingError("Strategy failed", "BTC-USD")
        assert error.strategy_id == "BTC-USD"
        assert error.context["strategy_id"] == "BTC-USD"
    
    def test_permutation_analysis_error(self):
        """Test PermutationAnalysisError specifics."""
        error = PermutationAnalysisError("Analysis failed", 100, 50)
        assert error.permutation_count == 100
        assert error.current_permutation == 50
        assert error.context["permutation_count"] == 100
        assert error.context["current_permutation"] == 50
    
    def test_validation_error_specifics(self):
        """Test ValidationError specifics."""
        error = ValidationError("Invalid input", "field_name", "str", 123)
        assert error.field_name == "field_name"
        assert error.expected_type == "str"
        assert error.actual_value == 123
        assert error.context["field_name"] == "field_name"
        assert error.context["expected_type"] == "str"
        assert error.context["actual_value"] == "123"


class TestContextManagers:
    """Test error context managers."""
    
    def test_concurrency_error_context_success(self):
        """Test context manager with successful operation."""
        log_mock = Mock()
        
        with concurrency_error_context("test operation", log_mock):
            pass  # Successful operation
        
        log_mock.assert_has_calls([
            call("Starting test operation", "debug"),
            call("Completed test operation", "debug")
        ])
    
    def test_concurrency_error_context_with_error(self):
        """Test context manager with error."""
        log_mock = Mock()
        
        with pytest.raises(ConcurrencyError):
            with concurrency_error_context("test operation", log_mock):
                raise ValueError("Test error")
        
        assert log_mock.call_count >= 2  # Start + error logs
    
    def test_concurrency_error_context_with_mapping(self):
        """Test context manager with error mapping."""
        log_mock = Mock()
        error_mapping = {ValueError: StrategyProcessingError}
        
        with pytest.raises(StrategyProcessingError):
            with concurrency_error_context("test operation", log_mock, error_mapping):
                raise ValueError("Test error")
    
    def test_concurrency_error_context_with_recovery(self):
        """Test context manager with recovery function."""
        log_mock = Mock()
        recovery_func = Mock(return_value="recovered")
        
        with concurrency_error_context("test operation", log_mock, recovery_func=recovery_func):
            raise ValueError("Test error")
        
        recovery_func.assert_called_once()
        log_mock.assert_any_call("Attempting recovery for test operation", "info")
        log_mock.assert_any_call("Recovery successful for test operation", "info")
    
    def test_strategy_processing_context(self):
        """Test strategy processing context manager."""
        log_mock = Mock()
        
        with pytest.raises(StrategyProcessingError):
            with strategy_processing_context("BTC-USD", "loading", log_mock):
                raise ValueError("Strategy load failed")
    
    def test_permutation_analysis_context(self):
        """Test permutation analysis context manager."""
        log_mock = Mock()
        
        with pytest.raises(PermutationAnalysisError):
            with permutation_analysis_context(100, 50, "analysis", log_mock):
                raise RuntimeError("Analysis failed")
    
    def test_batch_operation_context_success(self):
        """Test batch operation context with all successes."""
        log_mock = Mock()
        
        with batch_operation_context("batch test", 5, log_mock) as tracker:
            for i in range(5):
                tracker.record_success()
        
        summary = tracker.get_summary()
        assert summary["successes"] == 5
        assert summary["failures"] == 0
        assert summary["success_rate"] == 1.0
    
    def test_batch_operation_context_with_errors(self):
        """Test batch operation context with some errors."""
        log_mock = Mock()
        
        with batch_operation_context("batch test", 5, log_mock, max_failures=3) as tracker:
            tracker.record_success()
            tracker.record_error(ValueError("Error 1"), 1)
            tracker.record_success()
            tracker.record_error(RuntimeError("Error 2"), 3)
        
        summary = tracker.get_summary()
        assert summary["successes"] == 2
        assert summary["failures"] == 2
        assert len(summary["errors"]) == 2
    
    def test_batch_operation_context_max_failures(self):
        """Test batch operation context exceeding max failures."""
        log_mock = Mock()
        
        with pytest.raises(ConcurrencyError):
            with batch_operation_context("batch test", 5, log_mock, max_failures=2) as tracker:
                tracker.record_error(ValueError("Error 1"))
                tracker.record_error(ValueError("Error 2"))
                tracker.record_error(ValueError("Error 3"))  # Should trigger exception


class TestDecorators:
    """Test error handling decorators."""
    
    def test_handle_concurrency_errors_success(self):
        """Test decorator with successful function."""
        log_mock = Mock()
        
        @handle_concurrency_errors("test operation")
        def test_func(log):
            return "success"
        
        result = test_func(log_mock)
        assert result == "success"
    
    def test_handle_concurrency_errors_with_error(self):
        """Test decorator with error."""
        log_mock = Mock()
        
        @handle_concurrency_errors("test operation")
        def test_func(log):
            raise ValueError("Test error")
        
        with pytest.raises(ConcurrencyError):
            test_func(log_mock)
    
    def test_handle_concurrency_errors_with_mapping(self):
        """Test decorator with error mapping."""
        log_mock = Mock()
        error_mapping = {ValueError: StrategyProcessingError}
        
        @handle_concurrency_errors("test operation", error_mapping)
        def test_func(log):
            raise ValueError("Test error")
        
        with pytest.raises(StrategyProcessingError):
            test_func(log_mock)
    
    def test_validate_inputs_success(self):
        """Test input validation decorator with valid inputs."""
        @validate_inputs(
            value=lambda x: isinstance(x, int) and x > 0,
            name=lambda x: isinstance(x, str) and len(x) > 0
        )
        def test_func(value, name):
            return f"{name}: {value}"
        
        result = test_func(42, "test")
        assert result == "test: 42"
    
    def test_validate_inputs_failure(self):
        """Test input validation decorator with invalid inputs."""
        @validate_inputs(
            value=lambda x: isinstance(x, int) and x > 0
        )
        def test_func(value):
            return value
        
        with pytest.raises(ValidationError):
            test_func(-1)
    
    def test_retry_on_failure_success_first_try(self):
        """Test retry decorator with success on first try."""
        log_mock = Mock()
        
        @retry_on_failure(max_retries=3)
        def test_func(log):
            return "success"
        
        result = test_func(log_mock)
        assert result == "success"
    
    def test_retry_on_failure_success_after_retries(self):
        """Test retry decorator with success after retries."""
        log_mock = Mock()
        call_count = 0
        
        @retry_on_failure(max_retries=3, delay=0.01)
        def test_func(log):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = test_func(log_mock)
        assert result == "success"
        assert call_count == 3
    
    def test_retry_on_failure_max_retries_exceeded(self):
        """Test retry decorator with max retries exceeded."""
        log_mock = Mock()
        
        @retry_on_failure(max_retries=2, delay=0.01)
        def test_func(log):
            raise ValueError("Persistent error")
        
        with pytest.raises(ValueError):
            test_func(log_mock)
    
    def test_track_performance(self):
        """Test performance tracking decorator."""
        log_mock = Mock()
        
        @track_performance("test operation", performance_threshold=0.1)
        def test_func(log):
            time.sleep(0.05)
            return "done"
        
        result = test_func(log_mock)
        assert result == "done"
        # Should log performance but not warning (under threshold)
    
    def test_require_fields_success(self):
        """Test require fields decorator with valid data."""
        @require_fields("required_field", "another_field")
        def test_func(data):
            return data
        
        data = {"required_field": "value", "another_field": "value2"}
        result = test_func(data)
        assert result == data
    
    def test_require_fields_missing(self):
        """Test require fields decorator with missing data."""
        @require_fields("required_field", "another_field")
        def test_func(data):
            return data
        
        data = {"required_field": "value"}  # Missing another_field
        with pytest.raises(ValidationError):
            test_func(data)


class TestErrorRecovery:
    """Test error recovery mechanisms."""
    
    def test_create_recovery_policy(self):
        """Test recovery policy creation."""
        policy = create_recovery_policy(
            strategy=RecoveryStrategy.RETRY,
            max_retries=5,
            retry_delay=2.0
        )
        
        assert policy.strategy == RecoveryStrategy.RETRY
        assert policy.max_retries == 5
        assert policy.retry_delay == 2.0
    
    def test_apply_error_recovery_retry_success(self):
        """Test error recovery with retry strategy - success case."""
        log_mock = Mock()
        call_count = 0
        
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        policy = create_recovery_policy(RecoveryStrategy.RETRY, max_retries=3, retry_delay=0.01)
        result = apply_error_recovery(test_func, policy, log_mock, "test operation")
        
        assert result == "success"
        assert call_count == 3
    
    def test_apply_error_recovery_fallback(self):
        """Test error recovery with fallback strategy."""
        log_mock = Mock()
        
        def test_func():
            raise ValueError("Error")
        
        def fallback_func():
            return "fallback result"
        
        policy = create_recovery_policy(
            RecoveryStrategy.FALLBACK,
            fallback_func=fallback_func,
            applicable_exceptions=[ValueError]
        )
        result = apply_error_recovery(test_func, policy, log_mock, "test operation")
        
        assert result == "fallback result"
    
    def test_apply_error_recovery_skip(self):
        """Test error recovery with skip strategy."""
        log_mock = Mock()
        
        def test_func():
            raise ValueError("Error")
        
        policy = create_recovery_policy(
            RecoveryStrategy.SKIP,
            action_on_failure=RecoveryAction.CONTINUE,
            applicable_exceptions=[ValueError]
        )
        result = apply_error_recovery(test_func, policy, log_mock, "test operation")
        
        assert result is None
    
    def test_apply_error_recovery_default_value(self):
        """Test error recovery with default value."""
        log_mock = Mock()
        
        def test_func():
            raise ValueError("Error")
        
        policy = create_recovery_policy(
            RecoveryStrategy.FALLBACK,
            default_value="default",
            action_on_failure=RecoveryAction.USE_DEFAULT,
            applicable_exceptions=[ValueError]
        )
        result = apply_error_recovery(test_func, policy, log_mock, "test operation")
        
        assert result == "default"
    
    def test_get_recovery_policy(self):
        """Test getting default recovery policies."""
        policy = get_recovery_policy("strategy_processing")
        assert policy is not None
        assert policy.strategy == RecoveryStrategy.RETRY
        
        policy = get_recovery_policy("nonexistent")
        assert policy is None
    
    def test_create_fallback_function(self):
        """Test creating fallback functions."""
        fallback = create_fallback_function("fallback_value")
        result = fallback()
        assert result == "fallback_value"


class TestErrorRegistry:
    """Test error registry functionality."""
    
    def test_error_registry_initialization(self):
        """Test error registry initialization."""
        registry = ErrorRegistry(max_records=100)
        assert registry.max_records == 100
        assert len(registry.errors) == 0
    
    def test_record_error(self):
        """Test recording errors in registry."""
        registry = ErrorRegistry()
        error = ValueError("Test error")
        context = {"key": "value"}
        
        registry.record_error(error, "test operation", context)
        
        assert len(registry.errors) == 1
        record = registry.errors[0]
        assert record.error_type == "ValueError"
        assert record.error_message == "Test error"
        assert record.operation == "test operation"
        assert record.context == context
    
    def test_record_operation(self):
        """Test recording successful operations."""
        registry = ErrorRegistry()
        
        registry.record_operation("test operation")
        registry.record_operation("test operation")
        registry.record_operation("other operation")
        
        assert registry.operation_counts["test operation"] == 2
        assert registry.operation_counts["other operation"] == 1
    
    def test_get_error_stats(self):
        """Test getting error statistics."""
        registry = ErrorRegistry()
        
        # Record some errors
        registry.record_error(ValueError("Error 1"), "op1")
        registry.record_error(ValueError("Error 2"), "op1")
        registry.record_error(RuntimeError("Error 3"), "op2")
        
        # Record some operations
        registry.record_operation("op1")
        registry.record_operation("op2")
        
        stats = registry.get_error_stats()
        
        assert stats.total_errors == 3
        assert stats.errors_by_type["ValueError"] == 2
        assert stats.errors_by_type["RuntimeError"] == 1
        assert stats.errors_by_operation["op1"] == 2
        assert stats.errors_by_operation["op2"] == 1
        assert len(stats.most_common_errors) > 0
    
    def test_get_errors_by_operation(self):
        """Test filtering errors by operation."""
        registry = ErrorRegistry()
        
        registry.record_error(ValueError("Error 1"), "op1")
        registry.record_error(RuntimeError("Error 2"), "op2")
        registry.record_error(ValueError("Error 3"), "op1")
        
        op1_errors = registry.get_errors_by_operation("op1")
        assert len(op1_errors) == 2
        assert all(error.operation == "op1" for error in op1_errors)
    
    def test_get_errors_by_type(self):
        """Test filtering errors by type."""
        registry = ErrorRegistry()
        
        registry.record_error(ValueError("Error 1"), "op1")
        registry.record_error(RuntimeError("Error 2"), "op2")
        registry.record_error(ValueError("Error 3"), "op1")
        
        value_errors = registry.get_errors_by_type("ValueError")
        assert len(value_errors) == 2
        assert all(error.error_type == "ValueError" for error in value_errors)
    
    def test_max_records_limit(self):
        """Test that registry respects max records limit."""
        registry = ErrorRegistry(max_records=3)
        
        # Record more errors than the limit
        for i in range(5):
            registry.record_error(ValueError(f"Error {i}"), f"op{i}")
        
        # Should only keep the most recent 3
        assert len(registry.errors) == 3
        assert registry.errors[0].error_message == "Error 2"
        assert registry.errors[-1].error_message == "Error 4"
    
    def test_export_errors(self):
        """Test exporting errors to file."""
        registry = ErrorRegistry()
        
        registry.record_error(ValueError("Error 1"), "op1")
        registry.record_error(RuntimeError("Error 2"), "op2")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name
        
        try:
            registry.export_errors(export_path)
            
            # Verify export file contents
            with open(export_path, 'r') as f:
                data = json.load(f)
            
            assert "errors" in data
            assert "stats" in data
            assert data["error_count"] == 2
            assert len(data["errors"]) == 2
            
        finally:
            Path(export_path).unlink(missing_ok=True)
    
    def test_clear_old_errors(self):
        """Test clearing old errors."""
        registry = ErrorRegistry()
        
        # Create errors with different timestamps
        old_error = ErrorRecord(
            timestamp=datetime.now() - timedelta(hours=25),
            operation="old_op",
            error_type="ValueError",
            error_message="Old error",
            context={}
        )
        new_error = ErrorRecord(
            timestamp=datetime.now(),
            operation="new_op",
            error_type="RuntimeError",
            error_message="New error",
            context={}
        )
        
        registry.errors = [old_error, new_error]
        
        cleared_count = registry.clear_old_errors(hours_back=24)
        
        assert cleared_count == 1
        assert len(registry.errors) == 1
        assert registry.errors[0].operation == "new_op"


class TestGlobalRegistry:
    """Test global registry functions."""
    
    def test_track_error_global(self):
        """Test tracking error in global registry."""
        error = ValueError("Test error")
        track_error(error, "test operation", {"key": "value"})
        
        stats = get_error_stats()
        assert stats.total_errors >= 1
    
    def test_export_error_report_global(self):
        """Test exporting error report from global registry."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name
        
        try:
            # Track an error first
            track_error(ValueError("Test error"), "test operation")
            
            # Export report
            from app.concurrency.error_handling.registry import export_error_report
            export_error_report(export_path)
            
            # Verify export file exists and contains data
            assert Path(export_path).exists()
            with open(export_path, 'r') as f:
                data = json.load(f)
            assert "errors" in data
            assert "stats" in data
            
        finally:
            Path(export_path).unlink(missing_ok=True)


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_context_manager_with_registry(self):
        """Test that context managers track errors in registry."""
        log_mock = Mock()
        
        # Get initial error count
        initial_stats = get_error_stats()
        initial_count = initial_stats.total_errors
        
        with pytest.raises(ConcurrencyError):
            with concurrency_error_context("integration test", log_mock):
                raise ValueError("Integration test error")
        
        # Check that error was tracked
        new_stats = get_error_stats()
        assert new_stats.total_errors > initial_count
    
    def test_decorator_with_recovery(self):
        """Test decorator combined with recovery mechanisms."""
        log_mock = Mock()
        
        policy = create_recovery_policy(
            RecoveryStrategy.RETRY,
            max_retries=2,
            retry_delay=0.01,
            applicable_exceptions=[ValueError]
        )
        
        call_count = 0
        
        @handle_concurrency_errors("test operation")
        def test_func(log):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Retryable error")
            return "success"
        
        # Apply recovery to the decorated function
        result = apply_error_recovery(
            lambda: test_func(log_mock),
            policy,
            log_mock,
            "decorated function"
        )
        
        assert result == "success"
        assert call_count == 3