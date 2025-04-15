"""
Unit tests for the error handling module.
"""

import unittest
import numpy as np
import pandas as pd
import polars as pl
from typing import Dict, Any, Optional

from app.tools.error_handling import (
    ErrorHandler,
    DataValidationError,
    ConfigurationError,
    CalculationError,
    Result,
    validate_dataframe,
    validate_config,
    with_fallback
)


class TestErrorHandling(unittest.TestCase):
    """Test cases for the error handling module."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        
        # Create test data
        self.test_df_pd = pd.DataFrame({
            "A": [1, 2, 3],
            "B": [4, 5, 6],
            "C": [7, 8, 9]
        })
        
        self.test_df_pl = pl.DataFrame({
            "A": [1, 2, 3],
            "B": [4, 5, 6],
            "C": [7, 8, 9]
        })
        
        self.test_config = {
            "required_key1": "value1",
            "required_key2": "value2",
            "optional_key": "value3"
        }
        
        self.test_array = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    
    def test_validate_dataframe_success(self):
        """Test validate_dataframe with valid data."""
        # Test with pandas DataFrame
        try:
            self.error_handler.validate_dataframe(
                self.test_df_pd,
                ["A", "B"],
                "Test pandas DataFrame"
            )
            # If no exception is raised, the test passes
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"validate_dataframe raised {type(e).__name__} unexpectedly!")
        
        # Test with polars DataFrame
        try:
            self.error_handler.validate_dataframe(
                self.test_df_pl,
                ["A", "B"],
                "Test polars DataFrame"
            )
            # If no exception is raised, the test passes
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"validate_dataframe raised {type(e).__name__} unexpectedly!")
    
    def test_validate_dataframe_failure(self):
        """Test validate_dataframe with invalid data."""
        # Test with missing columns
        with self.assertRaises(DataValidationError):
            self.error_handler.validate_dataframe(
                self.test_df_pd,
                ["A", "D"],  # D is not in the DataFrame
                "Test DataFrame with missing columns"
            )
        
        # Test with None DataFrame
        with self.assertRaises(DataValidationError):
            self.error_handler.validate_dataframe(
                None,
                ["A", "B"],
                "None DataFrame"
            )
        
        # Test with empty DataFrame
        with self.assertRaises(DataValidationError):
            self.error_handler.validate_dataframe(
                pd.DataFrame(),
                ["A", "B"],
                "Empty DataFrame"
            )
    
    def test_validate_config_success(self):
        """Test validate_config with valid config."""
        try:
            self.error_handler.validate_config(
                self.test_config,
                ["required_key1", "required_key2"],
                ["optional_key"],
                "Test config"
            )
            # If no exception is raised, the test passes
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"validate_config raised {type(e).__name__} unexpectedly!")
    
    def test_validate_config_failure(self):
        """Test validate_config with invalid config."""
        # Test with missing required keys
        with self.assertRaises(ConfigurationError):
            self.error_handler.validate_config(
                self.test_config,
                ["required_key1", "missing_key"],  # missing_key is not in the config
                ["optional_key"],
                "Test config with missing keys"
            )
        
        # Test with None config
        with self.assertRaises(ConfigurationError):
            self.error_handler.validate_config(
                None,
                ["required_key1", "required_key2"],
                ["optional_key"],
                "None config"
            )
    
    def test_validate_numeric_array_success(self):
        """Test validate_numeric_array with valid data."""
        try:
            self.error_handler.validate_numeric_array(
                self.test_array,
                "Test array"
            )
            # If no exception is raised, the test passes
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"validate_numeric_array raised {type(e).__name__} unexpectedly!")
    
    def test_validate_numeric_array_failure(self):
        """Test validate_numeric_array with invalid data."""
        # Test with non-numeric array
        with self.assertRaises(DataValidationError):
            self.error_handler.validate_numeric_array(
                np.array(["a", "b", "c"]),
                "Non-numeric array"
            )
        
        # Test with array containing NaN
        with self.assertRaises(DataValidationError):
            self.error_handler.validate_numeric_array(
                np.array([1.0, np.nan, 3.0]),
                "Array with NaN",
                allow_nan=False
            )
        
        # Test with array containing infinity
        with self.assertRaises(DataValidationError):
            self.error_handler.validate_numeric_array(
                np.array([1.0, np.inf, 3.0]),
                "Array with infinity",
                allow_inf=False
            )
        
        # Test with array that's too short
        with self.assertRaises(DataValidationError):
            self.error_handler.validate_numeric_array(
                np.array([1.0]),
                "Short array",
                min_length=2
            )
    
    def test_handle_calculation_error(self):
        """Test handle_calculation_error."""
        # Test with fallback value
        error = ValueError("Test error")
        context = {"function": "test_function", "args": [1, 2, 3]}
        fallback_value = 42
        
        result = self.error_handler.handle_calculation_error(
            error,
            context,
            fallback_value
        )
        
        self.assertEqual(result, fallback_value)
        
        # Test without fallback value
        with self.assertRaises(CalculationError):
            self.error_handler.handle_calculation_error(
                error,
                context
            )
    
    def test_with_error_handling_decorator(self):
        """Test with_error_handling decorator."""
        # Define a function that raises an error
        @self.error_handler.with_error_handling(fallback_value=42)
        def function_that_raises():
            raise ValueError("Test error")
        
        # Define a function that returns a value
        @self.error_handler.with_error_handling(fallback_value=42)
        def function_that_returns():
            return 100
        
        # Test function that raises an error
        result = function_that_raises()
        self.assertEqual(result, 42)  # Should return fallback value
        
        # Test function that returns a value
        result = function_that_returns()
        self.assertEqual(result, 100)  # Should return actual value
    
    def test_result_class(self):
        """Test Result class."""
        # Test successful result
        ok_result = Result.ok(42)
        self.assertTrue(ok_result.is_ok())
        self.assertFalse(ok_result.is_err())
        self.assertEqual(ok_result.unwrap(), 42)
        self.assertEqual(ok_result.unwrap_or(0), 42)
        
        # Test error result
        error = ValueError("Test error")
        err_result = Result.err(error)
        self.assertFalse(err_result.is_ok())
        self.assertTrue(err_result.is_err())
        with self.assertRaises(ValueError):
            err_result.unwrap()
        self.assertEqual(err_result.unwrap_or(0), 0)
        
        # Test map method
        mapped_ok = ok_result.map(lambda x: x * 2)
        self.assertTrue(mapped_ok.is_ok())
        self.assertEqual(mapped_ok.unwrap(), 84)
        
        mapped_err = err_result.map(lambda x: x * 2)
        self.assertTrue(mapped_err.is_err())
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        # Test validate_dataframe
        result = validate_dataframe(
            self.test_df_pd,
            ["A", "B"],
            "Test DataFrame"
        )
        self.assertTrue(result)
        
        result = validate_dataframe(
            self.test_df_pd,
            ["A", "D"],  # D is not in the DataFrame
            "Test DataFrame with missing columns"
        )
        self.assertFalse(result)
        
        # Test validate_config
        result = validate_config(
            self.test_config,
            ["required_key1", "required_key2"],
            ["optional_key"],
            "Test config"
        )
        self.assertTrue(result)
        
        result = validate_config(
            self.test_config,
            ["required_key1", "missing_key"],  # missing_key is not in the config
            ["optional_key"],
            "Test config with missing keys"
        )
        self.assertFalse(result)
        
        # Test with_fallback decorator
        @with_fallback(42)
        def function_that_raises():
            raise ValueError("Test error")
        
        result = function_that_raises()
        self.assertEqual(result, 42)  # Should return fallback value


if __name__ == "__main__":
    unittest.main()