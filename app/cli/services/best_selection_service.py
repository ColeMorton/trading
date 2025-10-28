"""
Best Selection Service

Service for determining "best" portfolio selections using parameter consistency algorithm.
"""

from collections import Counter
from typing import Any


class BestSelectionService:
    """Service for determining best portfolio selections from strategy sweep results."""

    def find_best_for_ticker_strategy(
        self, results: list[dict[str, Any]], ticker: str, strategy_type: str,
    ) -> dict[str, Any] | None:
        """
        Apply parameter consistency algorithm to find best result.

        Algorithm checks for consistent parameter combinations across top results:
        1. Top 3 all match (100% confidence)
        2. 3 of top 5 match (60-80% confidence)
        3. 5 of top 8 match (62.5% confidence)
        4. Top 2 both match (100% confidence)
        5. Fallback to highest score (0-50% confidence)

        Args:
            results: List of sweep result dictionaries
            ticker: Ticker symbol to filter by
            strategy_type: Strategy type to filter by

        Returns:
            Dictionary with best result and selection metadata, or None if no results
        """
        # Filter to specific ticker and strategy
        filtered = [
            r
            for r in results
            if r.get("ticker") == ticker and r.get("strategy_type") == strategy_type
        ]

        if not filtered:
            return None

        # Sort by score descending
        sorted_results = sorted(
            filtered, key=lambda x: float(x.get("score", 0)), reverse=True,
        )

        total_alternatives = len(sorted_results)

        # Try each criterion in order

        # 1. Top 3 all match
        if len(sorted_results) >= 3:
            result = self._check_top_n_all_match(sorted_results, 3)
            if result:
                best = result["best_result"]
                return {
                    "best_result": best,
                    "selection_algorithm": "parameter_consistency",
                    "selection_criteria": "top_3_all_match",
                    "confidence_score": 100.00,
                    "alternatives_considered": total_alternatives,
                    "winning_combination": result["combination"],
                }

        # 2. 3 of top 5 match
        if len(sorted_results) >= 5:
            result = self._check_top_n_k_match(sorted_results, 5, 3)
            if result:
                best = result["best_result"]
                match_count = result["match_count"]
                confidence = (match_count / 5) * 100  # 60% for 3/5, 80% for 4/5
                return {
                    "best_result": best,
                    "selection_algorithm": "parameter_consistency",
                    "selection_criteria": f"top_5_{match_count}_of_5",
                    "confidence_score": confidence,
                    "alternatives_considered": total_alternatives,
                    "winning_combination": result["combination"],
                }

        # 3. 5 of top 8 match
        if len(sorted_results) >= 8:
            result = self._check_top_n_k_match(sorted_results, 8, 5)
            if result:
                best = result["best_result"]
                match_count = result["match_count"]
                confidence = (match_count / 8) * 100  # 62.5% for 5/8
                return {
                    "best_result": best,
                    "selection_algorithm": "parameter_consistency",
                    "selection_criteria": f"top_8_{match_count}_of_8",
                    "confidence_score": confidence,
                    "alternatives_considered": total_alternatives,
                    "winning_combination": result["combination"],
                }

        # 4. Top 2 both match
        if len(sorted_results) >= 2:
            result = self._check_top_n_all_match(sorted_results, 2)
            if result:
                best = result["best_result"]
                return {
                    "best_result": best,
                    "selection_algorithm": "parameter_consistency",
                    "selection_criteria": "top_2_both_match",
                    "confidence_score": 100.00,
                    "alternatives_considered": total_alternatives,
                    "winning_combination": result["combination"],
                }

        # 5. Fallback to highest score
        best = sorted_results[0]
        return {
            "best_result": best,
            "selection_algorithm": "parameter_consistency",
            "selection_criteria": "highest_score_fallback",
            "confidence_score": 25.00,  # Low confidence when no pattern found
            "alternatives_considered": total_alternatives,
            "winning_combination": self._get_parameter_combination(best),
        }

    def _get_parameter_combination(self, result: dict[str, Any]) -> tuple:
        """
        Extract parameter combination from result.

        Args:
            result: Sweep result dictionary

        Returns:
            Tuple of (fast_period, slow_period, signal_period)
        """
        return (
            result.get("fast_period"),
            result.get("slow_period"),
            result.get("signal_period"),
        )

    def _check_top_n_all_match(
        self, sorted_results: list[dict[str, Any]], n: int,
    ) -> dict[str, Any] | None:
        """
        Check if all top N results have the same parameter combination.

        Args:
            sorted_results: Results sorted by score descending
            n: Number of top results to check

        Returns:
            Dictionary with best_result and combination, or None if not all match
        """
        if len(sorted_results) < n:
            return None

        top_n = sorted_results[:n]
        combinations = [self._get_parameter_combination(r) for r in top_n]

        # Check if all combinations are the same
        if len(set(combinations)) == 1:
            return {
                "best_result": top_n[0],
                "combination": combinations[0],
            }

        return None

    def _check_top_n_k_match(
        self, sorted_results: list[dict[str, Any]], n: int, k: int,
    ) -> dict[str, Any] | None:
        """
        Check if K out of top N results have the same parameter combination.

        Args:
            sorted_results: Results sorted by score descending
            n: Number of top results to analyze
            k: Minimum number that must match

        Returns:
            Dictionary with best_result, combination, and match_count, or None if threshold not met
        """
        if len(sorted_results) < n:
            return None

        top_n = sorted_results[:n]
        combinations = [self._get_parameter_combination(r) for r in top_n]

        # Count occurrences of each combination
        counter = Counter(combinations)
        most_common_combo, count = counter.most_common(1)[0]

        # Check if at least K have the same combination
        if count >= k:
            # Find the highest-scoring result with this combination
            for result in top_n:
                if self._get_parameter_combination(result) == most_common_combo:
                    return {
                        "best_result": result,
                        "combination": most_common_combo,
                        "match_count": count,
                    }

        return None
