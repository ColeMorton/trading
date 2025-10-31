"""
Focused test for Monte Carlo recommended parameters enhancement.

This test specifically validates the enhancement logic without dependencies
on the full report generation system.
"""

import unittest
from unittest.mock import Mock

import pytest


# Test the enhancement logic in isolation
def enhance_recommended_parameters(strategy_data, parameter_variations, log_func):
    """
    Test version of the enhancement logic from generator.py
    """
    if strategy_data["recommended_parameters"] is not None:
        # Find the matching parameter result for recommended parameters
        recommended_details = None
        for param_data in parameter_variations:
            if (
                param_data["parameter_combination"]
                == strategy_data["recommended_parameters"]
            ):
                recommended_details = param_data
                break

        # Transform recommended_parameters from simple tuple to detailed object
        if recommended_details:
            # Calculate composite score for validation
            composite_score = (
                recommended_details.get("stability_score", 0.0) * 0.4
                + recommended_details.get("parameter_robustness", 0.0) * 0.4
                + recommended_details.get("regime_consistency", 0.0) * 0.2
            )

            strategy_data["recommended_parameters"] = {
                "parameters": strategy_data["recommended_parameters"],
                "stability_score": recommended_details["stability_score"],
                "parameter_robustness": recommended_details["parameter_robustness"],
                "regime_consistency": recommended_details["regime_consistency"],
                "is_stable": recommended_details["is_stable"],
                "composite_score": round(composite_score, 6),
                "selection_reason": "Highest weighted composite score (stability*0.4 + robustness*0.4 + consistency*0.2)",
                "validated": True,
            }
            log_func(
                f"Enhanced recommended_parameters with detailed metrics (composite score: {composite_score:.4f})",
                "debug",
            )
        else:
            # Convert to structured format even without details
            strategy_data["recommended_parameters"] = {
                "parameters": strategy_data["recommended_parameters"],
                "stability_score": None,
                "parameter_robustness": None,
                "regime_consistency": None,
                "is_stable": None,
                "composite_score": None,
                "selection_reason": "Data unavailable - no matching parameter analysis found",
                "validated": False,
            }
            log_func(
                f"Warning: No detailed metrics found for recommended parameters {strategy_data['recommended_parameters']}",
                "warning",
            )

    return strategy_data


@pytest.mark.integration
class TestMonteCarloEnhancementFocused(unittest.TestCase):
    """Focused test for Monte Carlo enhancement logic."""

    def test_recommended_parameters_with_matching_variation(self):
        """Test enhancement when recommended parameters match a tested variation."""
        # Setup test data
        strategy_data = {
            "strategy_id": "BTC-USD_EMA_5_68_0",
            "recommended_parameters": [5, 65],
        }

        parameter_variations = [
            {
                "parameter_combination": [5, 65],
                "stability_score": 0.7313931686091366,
                "parameter_robustness": 0.6505276554661957,
                "regime_consistency": 0.99,
                "is_stable": True,
            },
        ]

        mock_log = Mock()

        # Apply enhancement
        result = enhance_recommended_parameters(
            strategy_data,
            parameter_variations,
            mock_log,
        )

        # Verify enhanced structure
        recommended = result["recommended_parameters"]
        self.assertIsInstance(recommended, dict)
        self.assertEqual(recommended["parameters"], [5, 65])
        self.assertEqual(recommended["stability_score"], 0.7313931686091366)
        self.assertEqual(recommended["parameter_robustness"], 0.6505276554661957)
        self.assertEqual(recommended["regime_consistency"], 0.99)
        self.assertTrue(recommended["is_stable"])
        self.assertTrue(recommended["validated"])

        # Verify composite score calculation
        expected_composite = (
            0.7313931686091366 * 0.4 + 0.6505276554661957 * 0.4 + 0.99 * 0.2
        )
        self.assertAlmostEqual(
            recommended["composite_score"],
            expected_composite,
            places=5,
        )

        # Verify logging
        debug_calls = [
            call
            for call in mock_log.call_args_list
            if len(call[0]) > 1 and call[0][1] == "debug"
        ]
        self.assertTrue(len(debug_calls) > 0, "Should log successful enhancement")

    def test_recommended_parameters_without_matching_variation(self):
        """Test enhancement when recommended parameters don't match any tested variation."""
        # Setup test data with non-matching parameters
        strategy_data = {
            "strategy_id": "BTC-USD_EMA_5_68_0",
            "recommended_parameters": [7, 70],  # Different from variations
        }

        parameter_variations = [
            {
                "parameter_combination": [5, 65],
                "stability_score": 0.7313931686091366,
                "parameter_robustness": 0.6505276554661957,
                "regime_consistency": 0.99,
                "is_stable": True,
            },
        ]

        mock_log = Mock()

        # Apply enhancement
        result = enhance_recommended_parameters(
            strategy_data,
            parameter_variations,
            mock_log,
        )

        # Verify structure with null values
        recommended = result["recommended_parameters"]
        self.assertIsInstance(recommended, dict)
        self.assertEqual(recommended["parameters"], [7, 70])
        self.assertIsNone(recommended["stability_score"])
        self.assertIsNone(recommended["parameter_robustness"])
        self.assertIsNone(recommended["regime_consistency"])
        self.assertIsNone(recommended["is_stable"])
        self.assertIsNone(recommended["composite_score"])
        self.assertFalse(recommended["validated"])
        self.assertIn("Data unavailable", recommended["selection_reason"])

        # Verify warning logging
        warning_calls = [
            call
            for call in mock_log.call_args_list
            if len(call[0]) > 1 and call[0][1] == "warning"
        ]
        self.assertTrue(
            len(warning_calls) > 0,
            "Should log warning for missing metrics",
        )

    def test_recommended_parameters_none(self):
        """Test enhancement when recommended parameters is None."""
        strategy_data = {
            "strategy_id": "BTC-USD_EMA_5_68_0",
            "recommended_parameters": None,
        }

        parameter_variations = []
        mock_log = Mock()

        # Apply enhancement
        result = enhance_recommended_parameters(
            strategy_data,
            parameter_variations,
            mock_log,
        )

        # Should remain None and not be modified
        self.assertIsNone(result["recommended_parameters"])

    def test_composite_score_calculation(self):
        """Test that composite score is calculated correctly."""
        strategy_data = {
            "strategy_id": "TEST_STRATEGY",
            "recommended_parameters": [10, 20],
        }

        parameter_variations = [
            {
                "parameter_combination": [10, 20],
                "stability_score": 0.8,
                "parameter_robustness": 0.6,
                "regime_consistency": 0.9,
                "is_stable": True,
            },
        ]

        mock_log = Mock()

        # Apply enhancement
        result = enhance_recommended_parameters(
            strategy_data,
            parameter_variations,
            mock_log,
        )

        # Verify composite score: 0.8*0.4 + 0.6*0.4 + 0.9*0.2 = 0.32 + 0.24 + 0.18 = 0.74
        expected_composite = 0.74
        self.assertAlmostEqual(
            result["recommended_parameters"]["composite_score"],
            expected_composite,
            places=6,
        )

    def test_structure_consistency(self):
        """Test that enhanced structure maintains consistent field names."""
        strategy_data = {
            "strategy_id": "TEST_STRATEGY",
            "recommended_parameters": [15, 30],
        }

        parameter_variations = [
            {
                "parameter_combination": [15, 30],
                "stability_score": 0.75,
                "parameter_robustness": 0.65,
                "regime_consistency": 0.85,
                "is_stable": True,
            },
        ]

        mock_log = Mock()

        # Apply enhancement
        result = enhance_recommended_parameters(
            strategy_data,
            parameter_variations,
            mock_log,
        )

        recommended = result["recommended_parameters"]

        # Verify all required fields exist
        required_fields = [
            "parameters",
            "stability_score",
            "parameter_robustness",
            "regime_consistency",
            "is_stable",
            "composite_score",
            "selection_reason",
            "validated",
        ]

        for field in required_fields:
            self.assertIn(field, recommended, f"Missing required field: {field}")

        # Verify field types
        self.assertIsInstance(recommended["parameters"], list)
        self.assertIsInstance(recommended["stability_score"], (int, float))
        self.assertIsInstance(recommended["parameter_robustness"], (int, float))
        self.assertIsInstance(recommended["regime_consistency"], (int, float))
        self.assertIsInstance(recommended["is_stable"], bool)
        self.assertIsInstance(recommended["composite_score"], (int, float))
        self.assertIsInstance(recommended["selection_reason"], str)
        self.assertIsInstance(recommended["validated"], bool)


if __name__ == "__main__":
    unittest.main()
