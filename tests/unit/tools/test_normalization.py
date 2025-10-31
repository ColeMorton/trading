"""
Unit tests for the normalization module.
"""

import unittest

import numpy as np
import pandas as pd
import polars as pl
import pytest

from app.tools.normalization import (
    Normalizer,
    min_max_normalize,
    normalize_metrics_dict,
    z_score_normalize,
)


@pytest.mark.unit
class TestNormalization(unittest.TestCase):
    """Test cases for the normalization module."""

    def setUp(self):
        """Set up test fixtures."""
        self.normalizer = Normalizer()

        # Create test data
        self.test_array = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        self.test_series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        self.test_list = [1.0, 2.0, 3.0, 4.0, 5.0]

        # Create test metrics
        self.test_metrics = {
            "avg_return": 0.05,
            "win_rate": 0.6,
            "profit_factor": 2.5,
            "sharpe_ratio": 1.2,
            "signal_quality_score": 7.5,
            "signal_count": 100,  # This should not be normalized
            "strategy_id": "test",  # This should not be normalized
        }

    def test_min_max_scale_numpy(self):
        """Test min_max_scale with numpy array."""
        # Test default range (0-1)
        result = self.normalizer.min_max_scale(self.test_array)
        expected = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        np.testing.assert_array_almost_equal(result, expected)

        # Test custom range (-1 to 1)
        result = self.normalizer.min_max_scale(self.test_array, feature_range=(-1, 1))
        expected = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_min_max_scale_pandas(self):
        """Test min_max_scale with pandas Series."""
        # Test default range (0-1)
        result = self.normalizer.min_max_scale(self.test_series)
        expected = pd.Series([0.0, 0.25, 0.5, 0.75, 1.0])
        pd.testing.assert_series_equal(result, expected)

        # Test custom range (-1 to 1)
        result = self.normalizer.min_max_scale(self.test_series, feature_range=(-1, 1))
        expected = pd.Series([-1.0, -0.5, 0.0, 0.5, 1.0])
        pd.testing.assert_series_equal(result, expected)

    def test_min_max_scale_list(self):
        """Test min_max_scale with list."""
        # Test default range (0-1)
        result = self.normalizer.min_max_scale(self.test_list)
        expected = [0.0, 0.25, 0.5, 0.75, 1.0]
        self.assertEqual(result, expected)

        # Test custom range (-1 to 1)
        result = self.normalizer.min_max_scale(self.test_list, feature_range=(-1, 1))
        expected = [-1.0, -0.5, 0.0, 0.5, 1.0]
        self.assertEqual(result, expected)

    def test_min_max_scale_edge_cases(self):
        """Test min_max_scale with edge cases."""
        # Test empty array
        result = self.normalizer.min_max_scale([])
        self.assertEqual(result, [])

        # Test single value
        result = self.normalizer.min_max_scale([5.0])
        self.assertEqual(result, [0.5])  # Midpoint of default range

        # Test constant array
        result = self.normalizer.min_max_scale([3.0, 3.0, 3.0])
        self.assertEqual(result, [0.5, 0.5, 0.5])  # Midpoint of default range

    def test_z_score_normalize(self):
        """Test z_score_normalize."""
        # Test with numpy array
        result = self.normalizer.z_score_normalize(self.test_array)
        expected = np.array([-1.41421356, -0.70710678, 0.0, 0.70710678, 1.41421356])
        np.testing.assert_array_almost_equal(result, expected)

        # Test with pandas Series
        result = self.normalizer.z_score_normalize(self.test_series)
        expected = pd.Series([-1.41421356, -0.70710678, 0.0, 0.70710678, 1.41421356])
        pd.testing.assert_series_equal(result, expected, check_exact=False)

        # Test with list
        result = self.normalizer.z_score_normalize(self.test_list)
        expected = [-1.41421356, -0.70710678, 0.0, 0.70710678, 1.41421356]
        self.assertEqual(len(result), len(expected))
        for r, e in zip(result, expected, strict=False):
            self.assertAlmostEqual(r, e, places=6)

    def test_robust_scale(self):
        """Test robust_scale."""
        # Create data with outliers
        data_with_outliers = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 100.0])

        # Test with numpy array
        result = self.normalizer.robust_scale(data_with_outliers)
        # The median is 3.5, and the IQR is 3.0
        expected = np.array(
            [-0.83333333, -0.5, -0.16666667, 0.16666667, 0.5, 32.16666667],
        )
        np.testing.assert_array_almost_equal(result, expected)

        # Test with clipping
        result = self.normalizer.robust_scale(
            data_with_outliers,
            clip=True,
            clip_range=(-3, 3),
        )
        expected = np.array([-0.83333333, -0.5, -0.16666667, 0.16666667, 0.5, 3.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_normalize_metrics(self):
        """Test normalize_metrics."""
        # Test with min_max normalization
        result = self.normalizer.normalize_metrics(self.test_metrics)

        # Check that numeric metrics are normalized
        self.assertTrue(0 <= result["avg_return"] <= 1)
        self.assertTrue(0 <= result["win_rate"] <= 1)
        self.assertTrue(0 <= result["profit_factor"] <= 1)
        self.assertTrue(0 <= result["sharpe_ratio"] <= 1)
        self.assertTrue(0 <= result["signal_quality_score"] <= 1)

        # Check that non-numeric metrics are not normalized
        self.assertEqual(result["signal_count"], 100)
        self.assertEqual(result["strategy_id"], "test")

    def test_normalize_dataframe(self):
        """Test normalize_dataframe."""
        # Create test DataFrame
        df_pd = pd.DataFrame(
            {
                "A": [1.0, 2.0, 3.0, 4.0, 5.0],
                "B": [10.0, 20.0, 30.0, 40.0, 50.0],
                "C": ["a", "b", "c", "d", "e"],  # Non-numeric column
            },
        )

        # Test with pandas DataFrame
        result = self.normalizer.normalize_dataframe(df_pd, columns=["A", "B"])

        # Check that numeric columns are normalized
        self.assertTrue((result["A"] >= 0).all() and (result["A"] <= 1).all())
        self.assertTrue((result["B"] >= 0).all() and (result["B"] <= 1).all())

        # Check that non-numeric columns are not normalized
        self.assertEqual(list(result["C"]), ["a", "b", "c", "d", "e"])

        # Test with polars DataFrame
        df_pl = pl.from_pandas(df_pd)
        result = self.normalizer.normalize_dataframe(df_pl, columns=["A", "B"])

        # Convert back to pandas for easier testing
        result_pd = result.to_pandas()

        # Check that numeric columns are normalized
        self.assertTrue((result_pd["A"] >= 0).all() and (result_pd["A"] <= 1).all())
        self.assertTrue((result_pd["B"] >= 0).all() and (result_pd["B"] <= 1).all())

        # Check that non-numeric columns are not normalized
        self.assertEqual(list(result_pd["C"]), ["a", "b", "c", "d", "e"])

    def test_convenience_functions(self):
        """Test convenience functions."""
        # Test min_max_normalize
        result = min_max_normalize(self.test_array)
        expected = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        np.testing.assert_array_almost_equal(result, expected)

        # Test z_score_normalize
        result = z_score_normalize(self.test_array)
        expected = np.array([-1.41421356, -0.70710678, 0.0, 0.70710678, 1.41421356])
        np.testing.assert_array_almost_equal(result, expected)

        # Test normalize_metrics_dict
        result = normalize_metrics_dict(self.test_metrics)

        # Check that numeric metrics are normalized
        self.assertTrue(0 <= result["avg_return"] <= 1)
        self.assertTrue(0 <= result["win_rate"] <= 1)
        self.assertTrue(0 <= result["profit_factor"] <= 1)
        self.assertTrue(0 <= result["sharpe_ratio"] <= 1)
        self.assertTrue(0 <= result["signal_quality_score"] <= 1)

        # Check that non-numeric metrics are not normalized
        self.assertEqual(result["signal_count"], 100)
        self.assertEqual(result["strategy_id"], "test")


if __name__ == "__main__":
    unittest.main()
