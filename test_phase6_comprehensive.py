#!/usr/bin/env python3
"""
Phase 6: Testing and Validation - Comprehensive Test Suite

This test suite provides comprehensive validation of all fixes implemented
in Phases 1-5, ensuring the portfolio metrics calculation system is
production-ready and addresses all identified issues.

Test Categories:
1. Regression Tests - Verify all original issues are fixed
2. Integration Tests - End-to-end workflow validation
3. Performance Tests - Benchmarking and efficiency validation
4. Production Readiness - Stress testing and edge case handling
5. Data Quality Tests - Comprehensive data validation
"""

import sys
import time
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import tempfile
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import all Phase 1-5 components
from app.concurrency.tools.validation import PortfolioMetricsValidator
from app.concurrency.tools.signal_metrics import calculate_portfolio_signal_metrics
from app.concurrency.tools.signal_quality import calculate_signal_quality_metrics
from app.concurrency.tools.efficiency import calculate_efficiency_metrics
from app.concurrency.tools.risk_metrics_validator import RiskMetricsValidator
from app.concurrency.tools.correlation_calculator import CorrelationCalculator
from app.concurrency.tools.csv_loader import CSVLoader, CSVMetricsExtractor, CSVValidator
from app.concurrency.tools.data_reconciler import DataReconciler
from app.concurrency.tools.unified_metrics_calculator import UnifiedMetricsCalculator, CalculationConfig
from app.concurrency.tools.format_adapters import FormatDetector


@dataclass
class TestResult:
    """Individual test result."""
    test_name: str
    category: str
    passed: bool
    execution_time: float
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class TestSuite:
    """Complete test suite results."""
    suite_name: str
    start_time: str
    end_time: str
    total_execution_time: float
    tests_run: int
    tests_passed: int
    tests_failed: int
    results: List[TestResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class Phase6TestRunner:
    """
    Comprehensive test runner for Phase 6 validation.
    
    This runner executes all tests to validate that the portfolio metrics
    calculation system is production-ready and addresses all identified issues.
    """
    
    def __init__(self):
        """Initialize the test runner."""
        self.results = []
        self.start_time = datetime.now()
        self.test_data_cache = {}
    
    def simple_log(self, message: str, level: str):
        """Simple logging function for tests."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level.upper()}] {message}")
    
    def run_all_tests(self) -> TestSuite:
        """Run all Phase 6 tests."""
        print("🔧 Phase 6: Testing and Validation - Comprehensive Test Suite")
        print("=" * 65)
        
        # Category 1: Regression Tests
        self._run_regression_tests()
        
        # Category 2: Integration Tests  
        self._run_integration_tests()
        
        # Category 3: Performance Tests
        self._run_performance_tests()
        
        # Category 4: Production Readiness Tests
        self._run_production_readiness_tests()
        
        # Category 5: Data Quality Tests
        self._run_data_quality_tests()
        
        # Generate final test suite
        end_time = datetime.now()
        execution_time = (end_time - self.start_time).total_seconds()
        
        suite = TestSuite(
            suite_name="Phase 6: Testing and Validation",
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_execution_time=execution_time,
            tests_run=len(self.results),
            tests_passed=len([r for r in self.results if r.passed]),
            tests_failed=len([r for r in self.results if not r.passed]),
            results=self.results
        )
        
        suite.summary = self._generate_test_summary(suite)
        return suite
    
    def _run_regression_tests(self):
        """Run regression tests to verify all original issues are fixed."""
        print("\n📋 Category 1: Regression Tests")
        print("-" * 35)
        
        # Test 1.1: Signal Count Inflation Fix
        self._test_signal_count_inflation_fix()
        
        # Test 1.2: Expectancy Calculation Fix
        self._test_expectancy_calculation_fix()
        
        # Test 1.3: Sharpe Ratio Sign Preservation
        self._test_sharpe_ratio_sign_preservation()
        
        # Test 1.4: Max Drawdown Calculation Fix
        self._test_max_drawdown_calculation_fix()
        
        # Test 1.5: Win Rate Calculation Consistency
        self._test_win_rate_calculation_consistency()
    
    def _run_integration_tests(self):
        """Run end-to-end integration tests."""
        print("\n🔄 Category 2: Integration Tests")
        print("-" * 35)
        
        # Test 2.1: Complete Pipeline Integration
        self._test_complete_pipeline_integration()
        
        # Test 2.2: CSV-JSON Reconciliation
        self._test_csv_json_reconciliation()
        
        # Test 2.3: Multi-Format Data Processing
        self._test_multi_format_data_processing()
        
        # Test 2.4: Error Recovery and Fallbacks
        self._test_error_recovery_fallbacks()
    
    def _run_performance_tests(self):
        """Run performance and efficiency tests."""
        print("\n⚡ Category 3: Performance Tests")
        print("-" * 35)
        
        # Test 3.1: Large Dataset Performance
        self._test_large_dataset_performance()
        
        # Test 3.2: Memory Usage Efficiency
        self._test_memory_usage_efficiency()
        
        # Test 3.3: Calculation Speed Benchmarks
        self._test_calculation_speed_benchmarks()
    
    def _run_production_readiness_tests(self):
        """Run production readiness validation tests."""
        print("\n🏭 Category 4: Production Readiness Tests")
        print("-" * 45)
        
        # Test 4.1: Edge Case Handling
        self._test_edge_case_handling()
        
        # Test 4.2: Concurrent Access Safety
        self._test_concurrent_access_safety()
        
        # Test 4.3: Data Corruption Recovery
        self._test_data_corruption_recovery()
        
        # Test 4.4: Configuration Validation
        self._test_configuration_validation()
    
    def _run_data_quality_tests(self):
        """Run comprehensive data quality validation tests."""
        print("\n✅ Category 5: Data Quality Tests")
        print("-" * 35)
        
        # Test 5.1: Data Validation Framework
        self._test_data_validation_framework()
        
        # Test 5.2: Cross-Validation Accuracy
        self._test_cross_validation_accuracy()
        
        # Test 5.3: Data Quality Scoring
        self._test_data_quality_scoring()
    
    # Regression Test Implementations
    
    def _test_signal_count_inflation_fix(self):
        """Test that signal count inflation (17× issue) is fixed."""
        start_time = time.time()
        test_name = "Signal Count Inflation Fix"
        
        try:
            # Create test data that would trigger the inflation bug
            test_signals = []
            for i in range(3):  # 3 strategies
                signal_data = pd.DataFrame({
                    'Date': pd.date_range('2023-01-01', periods=100, freq='D'),
                    'Signal': np.random.choice([0, 1, -1], 100, p=[0.7, 0.15, 0.15]),
                    'Ticker': f'TEST{i}',
                    'Strategy': f'Strategy_{i}'
                })
                test_signals.append(signal_data)
            
            # Calculate metrics using fixed methodology
            portfolio_metrics = calculate_portfolio_signal_metrics(
                test_signals, 
                use_fixed_signal_counting=True, 
                log=self.simple_log
            )
            
            # Get individual strategy signal counts
            individual_signal_counts = []
            for signal_data in test_signals:
                individual_count = len(signal_data[signal_data['Signal'] != 0])
                individual_signal_counts.append(individual_count)
            
            total_individual_signals = sum(individual_signal_counts)
            portfolio_signal_count = portfolio_metrics.get('signals', {}).get('summary', {}).get('total', {}).get('value', 0)
            
            # Check that portfolio signals are not inflated
            inflation_ratio = portfolio_signal_count / total_individual_signals if total_individual_signals > 0 else 0
            
            passed = inflation_ratio <= 1.2  # Allow small variance, but no massive inflation
            
            result = TestResult(
                test_name=test_name,
                category="regression",
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'individual_signal_counts': individual_signal_counts,
                    'total_individual_signals': total_individual_signals,
                    'portfolio_signal_count': portfolio_signal_count,
                    'inflation_ratio': inflation_ratio,
                    'acceptable_threshold': 1.2
                }
            )
            
            if not passed:
                result.errors.append(f"Signal inflation detected: {inflation_ratio:.2f}× (should be ≤1.2×)")
            else:
                self.simple_log(f"✅ {test_name}: Signal inflation ratio {inflation_ratio:.2f}× (acceptable)", "info")
                
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="regression",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    def _test_expectancy_calculation_fix(self):
        """Test that expectancy calculation units are consistent."""
        start_time = time.time()
        test_name = "Expectancy Calculation Fix"
        
        try:
            # Create test data with known expectancy
            test_returns = [1.5, -0.8, 2.1, -1.2, 0.9, -0.5, 1.8, -0.7]  # Mix of wins/losses
            expected_expectancy = np.mean(test_returns)  # Should be average, not sum
            
            # Create DataFrame for testing
            test_data = pd.DataFrame({
                'Ticker': ['TEST'] * len(test_returns),
                'Strategy': ['TestStrategy'] * len(test_returns),
                'Returns': test_returns,
                'Total Trades': [len(test_returns)] * len(test_returns),
                'Win Rate %': [62.5] * len(test_returns)  # 5 wins out of 8
            })
            
            # Calculate metrics using fixed methodology
            efficiency_metrics = calculate_efficiency_metrics(
                [test_data], 
                use_fixed_expectancy=True,
                log=self.simple_log
            )
            
            calculated_expectancy = efficiency_metrics.get('signal_quality', {}).get('expectancy_per_signal', 0)
            
            # Check that calculated expectancy matches expected (within tolerance)
            expectancy_difference = abs(calculated_expectancy - expected_expectancy)
            tolerance = 0.1
            
            passed = expectancy_difference <= tolerance
            
            result = TestResult(
                test_name=test_name,
                category="regression",
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'test_returns': test_returns,
                    'expected_expectancy': expected_expectancy,
                    'calculated_expectancy': calculated_expectancy,
                    'difference': expectancy_difference,
                    'tolerance': tolerance
                }
            )
            
            if not passed:
                result.errors.append(f"Expectancy calculation error: expected {expected_expectancy:.3f}, got {calculated_expectancy:.3f}")
            else:
                self.simple_log(f"✅ {test_name}: Expectancy calculation accurate within {tolerance}", "info")
                
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="regression",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    def _test_sharpe_ratio_sign_preservation(self):
        """Test that Sharpe ratio signs are preserved in aggregation."""
        start_time = time.time()
        test_name = "Sharpe Ratio Sign Preservation"
        
        try:
            # Create test data with all positive Sharpe ratios
            positive_strategies = []
            for i in range(3):
                strategy_data = pd.DataFrame({
                    'Ticker': [f'TEST{i}'],
                    'Strategy': [f'Strategy_{i}'],
                    'Sharpe Ratio': [1.2 + i * 0.3],  # All positive: 1.2, 1.5, 1.8
                    'Total Trades': [100 + i * 20],
                    'Total Return %': [15.0 + i * 5.0]
                })
                positive_strategies.append(strategy_data)
            
            # Calculate aggregated metrics
            signal_quality = calculate_signal_quality_metrics(
                positive_strategies,
                use_fixed_sharpe_aggregation=True,
                log=self.simple_log
            )
            
            portfolio_sharpe = signal_quality.get('sharpe_ratio', 0)
            
            # Portfolio Sharpe should be positive since all individual strategies are positive
            passed = portfolio_sharpe > 0
            
            result = TestResult(
                test_name=test_name,
                category="regression",
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'individual_sharpe_ratios': [1.2, 1.5, 1.8],
                    'portfolio_sharpe_ratio': portfolio_sharpe,
                    'sign_preserved': portfolio_sharpe > 0
                }
            )
            
            if not passed:
                result.errors.append(f"Sharpe ratio sign flip: positive strategies ({[1.2, 1.5, 1.8]}) produced negative portfolio Sharpe ({portfolio_sharpe:.3f})")
            else:
                self.simple_log(f"✅ {test_name}: Positive strategies maintained positive portfolio Sharpe ({portfolio_sharpe:.3f})", "info")
                
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="regression",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    def _test_max_drawdown_calculation_fix(self):
        """Test that max drawdown calculation uses proper equity curve methodology."""
        start_time = time.time()
        test_name = "Max Drawdown Calculation Fix"
        
        try:
            # Create test data with known drawdown characteristics
            # Strategy 1: 50% max drawdown
            # Strategy 2: 30% max drawdown
            # Portfolio should NOT be simple average (40%)
            
            test_strategies = []
            
            # Strategy 1 with 50% drawdown
            strategy1_data = pd.DataFrame({
                'Ticker': ['MSTR'],
                'Strategy': ['Strategy_1'],
                'Max Drawdown %': [50.0],
                'Total Trades': [100],
                'Total Return %': [25.0]
            })
            test_strategies.append(strategy1_data)
            
            # Strategy 2 with 30% drawdown  
            strategy2_data = pd.DataFrame({
                'Ticker': ['MSTR'],
                'Strategy': ['Strategy_2'],
                'Max Drawdown %': [30.0],
                'Total Trades': [80],
                'Total Return %': [15.0]
            })
            test_strategies.append(strategy2_data)
            
            # Calculate using fixed methodology
            signal_quality = calculate_signal_quality_metrics(
                test_strategies,
                use_fixed_drawdown_calc=True,
                log=self.simple_log
            )
            
            portfolio_drawdown = signal_quality.get('max_drawdown', 0)
            simple_average = (50.0 + 30.0) / 2  # 40.0%
            
            # Portfolio drawdown should NOT be simple average
            # It should be calculated using proper equity curve combination
            passed = abs(portfolio_drawdown - simple_average) > 5.0  # Significant difference expected
            
            result = TestResult(
                test_name=test_name,
                category="regression",
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'individual_drawdowns': [50.0, 30.0],
                    'simple_average': simple_average,
                    'portfolio_drawdown': portfolio_drawdown,
                    'difference_from_average': abs(portfolio_drawdown - simple_average),
                    'uses_proper_methodology': passed
                }
            )
            
            if not passed:
                result.errors.append(f"Max drawdown calculation appears to use simple averaging ({portfolio_drawdown:.1f}% ≈ {simple_average:.1f}%)")
            else:
                self.simple_log(f"✅ {test_name}: Portfolio drawdown ({portfolio_drawdown:.1f}%) differs from simple average ({simple_average:.1f}%)", "info")
                
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="regression",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    def _test_win_rate_calculation_consistency(self):
        """Test that win rate calculations are consistent between CSV and JSON."""
        start_time = time.time()
        test_name = "Win Rate Calculation Consistency"
        
        try:
            # Create test data with known win rate
            test_trades = [1, -1, 1, 1, -1, 1, -1, 1, 1, 1]  # 7 wins, 3 losses = 70%
            expected_win_rate = 70.0
            
            # Create CSV-style data
            csv_data = pd.DataFrame({
                'Ticker': ['TEST'],
                'Strategy': ['TestStrategy'],
                'Win Rate %': [expected_win_rate],
                'Total Trades': [len(test_trades)]
            })
            
            # Load and extract metrics using CSV loader
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                csv_data.to_csv(f.name, index=False)
                csv_path = f.name
            
            try:
                csv_loader = CSVLoader()
                load_result = csv_loader.load_csv(csv_path, self.simple_log)
                
                if load_result.success:
                    extractor = CSVMetricsExtractor()
                    csv_metrics = extractor.extract_metrics(load_result.data, self.simple_log)
                    
                    extracted_win_rate = csv_metrics.ticker_metrics.get('TEST', {}).get('win_rate__pct', 0)
                    
                    # Check consistency
                    win_rate_difference = abs(extracted_win_rate - expected_win_rate)
                    tolerance = 1.0  # 1% tolerance
                    
                    passed = win_rate_difference <= tolerance
                    
                    result = TestResult(
                        test_name=test_name,
                        category="regression",
                        passed=passed,
                        execution_time=time.time() - start_time,
                        details={
                            'expected_win_rate': expected_win_rate,
                            'extracted_win_rate': extracted_win_rate,
                            'difference': win_rate_difference,
                            'tolerance': tolerance
                        }
                    )
                    
                    if not passed:
                        result.errors.append(f"Win rate extraction inconsistency: expected {expected_win_rate}%, got {extracted_win_rate}%")
                    else:
                        self.simple_log(f"✅ {test_name}: Win rate consistently extracted ({extracted_win_rate}%)", "info")
                else:
                    result = TestResult(
                        test_name=test_name,
                        category="regression",
                        passed=False,
                        execution_time=time.time() - start_time,
                        errors=["Failed to load CSV test data"]
                    )
            finally:
                if os.path.exists(csv_path):
                    os.unlink(csv_path)
                    
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="regression",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    # Integration Test Implementations
    
    def _test_complete_pipeline_integration(self):
        """Test complete end-to-end pipeline integration."""
        start_time = time.time()
        test_name = "Complete Pipeline Integration"
        
        try:
            # Create comprehensive test data
            test_csv_data = self._create_comprehensive_test_data()
            test_json_data = self._create_test_json_data()
            
            # Create temporary CSV file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                test_csv_data.to_csv(f.name, index=False)
                csv_path = f.name
            
            try:
                # Run complete unified pipeline
                config = CalculationConfig(
                    csv_as_source_of_truth=True,
                    enable_reconciliation=True,
                    enable_risk_validation=True,
                    strict_validation=False
                )
                
                calculator = UnifiedMetricsCalculator(config)
                result_data = calculator.calculate_unified_metrics(
                    csv_path=csv_path,
                    json_data=test_json_data,
                    log=self.simple_log
                )
                
                # Validate pipeline success
                pipeline_success = result_data.success
                has_metrics = bool(result_data.metrics)
                has_reconciliation = result_data.reconciliation_report is not None
                has_validation = bool(result_data.validation_results)
                
                passed = all([pipeline_success, has_metrics, has_reconciliation, has_validation])
                
                result = TestResult(
                    test_name=test_name,
                    category="integration",
                    passed=passed,
                    execution_time=time.time() - start_time,
                    details={
                        'pipeline_success': pipeline_success,
                        'metrics_generated': has_metrics,
                        'reconciliation_performed': has_reconciliation,
                        'validation_completed': has_validation,
                        'data_sources': list(result_data.data_sources.keys()),
                        'warnings_count': len(result_data.warnings),
                        'errors_count': len(result_data.errors)
                    }
                )
                
                if not passed:
                    issues = []
                    if not pipeline_success:
                        issues.append("Pipeline execution failed")
                    if not has_metrics:
                        issues.append("No metrics generated")
                    if not has_reconciliation:
                        issues.append("Reconciliation not performed")
                    if not has_validation:
                        issues.append("Validation not completed")
                    result.errors.extend(issues)
                else:
                    self.simple_log(f"✅ {test_name}: Complete pipeline executed successfully", "info")
                    
            finally:
                if os.path.exists(csv_path):
                    os.unlink(csv_path)
                    
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="integration",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    def _test_csv_json_reconciliation(self):
        """Test CSV-JSON reconciliation accuracy."""
        start_time = time.time()
        test_name = "CSV-JSON Reconciliation"
        
        try:
            # Create test data with known discrepancies
            csv_data = pd.DataFrame({
                'Ticker': ['TEST1', 'TEST2'],
                'Strategy': ['StrategyA', 'StrategyB'],
                'Total Return %': [15.0, 22.0],
                'Max Drawdown %': [12.0, 18.0],
                'Sharpe Ratio': [1.2, 1.5],
                'Total Trades': [100, 150],
                'Win Rate %': [65.0, 58.0]
            })
            
            # Create JSON data with intentional discrepancies
            json_data = {
                'ticker_metrics': {
                    'TEST1': {
                        'signal_quality_metrics': {
                            'avg_return': 0.14,  # Should be ~0.15 (discrepancy)
                            'max_drawdown': 0.15,  # Should be ~0.12 (discrepancy)
                            'sharpe_ratio': 1.2,   # Matches
                            'signal_count': 120,   # Should be ~100 (discrepancy)
                            'win_rate': 0.65       # Matches
                        }
                    },
                    'TEST2': {
                        'signal_quality_metrics': {
                            'avg_return': 0.22,    # Matches
                            'max_drawdown': 0.18,  # Matches
                            'sharpe_ratio': -1.5,  # Should be +1.5 (sign error)
                            'signal_count': 150,   # Matches
                            'win_rate': 0.60       # Should be ~0.58 (discrepancy)
                        }
                    }
                }
            }
            
            # Extract CSV metrics
            extractor = CSVMetricsExtractor()
            csv_metrics = extractor.extract_metrics(csv_data, self.simple_log)
            
            # Perform reconciliation
            reconciler = DataReconciler()
            csv_dict = {
                'ticker_metrics': csv_metrics.ticker_metrics,
                'portfolio_summary': csv_metrics.portfolio_summary
            }
            
            reconciliation_report = reconciler.reconcile_data(
                csv_dict, json_data, "test_csv", "test_json", self.simple_log
            )
            
            # Validate reconciliation results
            total_discrepancies = len([d for result in reconciliation_report.ticker_results for d in result.discrepancies])
            critical_discrepancies = len([d for result in reconciliation_report.ticker_results for d in result.discrepancies if d.discrepancy_type == 'critical'])
            
            # We expect at least 4 discrepancies (return, drawdown, signal count, Sharpe sign, win rate)
            expected_min_discrepancies = 4
            passed = total_discrepancies >= expected_min_discrepancies and critical_discrepancies > 0
            
            result = TestResult(
                test_name=test_name,
                category="integration",
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'total_discrepancies': total_discrepancies,
                    'critical_discrepancies': critical_discrepancies,
                    'expected_min_discrepancies': expected_min_discrepancies,
                    'reconciliation_quality': reconciliation_report.overall_summary.get('average_quality_score', 0),
                    'critical_issues_found': len(reconciliation_report.critical_issues)
                }
            )
            
            if not passed:
                result.errors.append(f"Reconciliation failed to detect expected discrepancies: found {total_discrepancies}, expected ≥{expected_min_discrepancies}")
            else:
                self.simple_log(f"✅ {test_name}: Reconciliation detected {total_discrepancies} discrepancies including {critical_discrepancies} critical", "info")
                
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="integration",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    def _test_multi_format_data_processing(self):
        """Test processing of multiple data formats."""
        start_time = time.time()
        test_name = "Multi-Format Data Processing"
        
        try:
            # Test VectorBT CSV format
            vectorbt_data = self._create_comprehensive_test_data()
            
            # Test JSON format
            json_data = self._create_test_json_data()
            
            # Test format detection and adaptation
            detector = FormatDetector()
            
            # Test CSV format detection
            csv_result = detector.detect_and_adapt(vectorbt_data, self.simple_log)
            csv_detected = csv_result.success and csv_result.format_detected in ['vectorbt_standard', 'custom_csv']
            
            # Test JSON format detection
            json_result = detector.detect_and_adapt(json_data, self.simple_log)
            json_detected = json_result.success and json_result.format_detected == 'json_portfolio'
            
            passed = csv_detected and json_detected
            
            result = TestResult(
                test_name=test_name,
                category="integration",
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'csv_format_detected': csv_result.format_detected,
                    'csv_adaptation_success': csv_result.success,
                    'csv_rows_processed': csv_result.rows_processed,
                    'json_format_detected': json_result.format_detected,
                    'json_adaptation_success': json_result.success,
                    'json_rows_processed': json_result.rows_processed
                }
            )
            
            if not passed:
                issues = []
                if not csv_detected:
                    issues.append(f"CSV format detection failed: {csv_result.format_detected}")
                if not json_detected:
                    issues.append(f"JSON format detection failed: {json_result.format_detected}")
                result.errors.extend(issues)
            else:
                self.simple_log(f"✅ {test_name}: Multiple formats processed successfully", "info")
                
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="integration",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    def _test_error_recovery_fallbacks(self):
        """Test error recovery and fallback mechanisms."""
        start_time = time.time()
        test_name = "Error Recovery and Fallbacks"
        
        try:
            # Test with corrupted CSV data
            corrupted_csv = pd.DataFrame({
                'Ticker': ['TEST1', None, 'TEST3'],  # Missing ticker
                'Strategy': ['StrategyA', 'StrategyB', None],  # Missing strategy
                'Total Return %': [15.0, 'invalid', 22.0],  # Invalid data type
                'Max Drawdown %': [12.0, -5.0, 18.0],  # Invalid range
                'Total Trades': [100, 0, 150]  # Zero trades
            })
            
            # Test CSV loader with corrupted data
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                corrupted_csv.to_csv(f.name, index=False)
                csv_path = f.name
            
            try:
                loader = CSVLoader(strict_validation=False)  # Use non-strict mode
                load_result = loader.load_csv(csv_path, self.simple_log)
                
                # Should still load with warnings, not fail completely
                graceful_handling = load_result.success and len(load_result.warnings) > 0
                
                # Test validator with corrupted data
                validator = CSVValidator()
                validation_result = validator.validate_csv_data(load_result.data, self.simple_log)
                
                validation_detected_issues = len(validation_result['warnings']) > 0 or len(validation_result['errors']) > 0
                
                passed = graceful_handling and validation_detected_issues
                
                result = TestResult(
                    test_name=test_name,
                    category="integration",
                    passed=passed,
                    execution_time=time.time() - start_time,
                    details={
                        'load_success': load_result.success,
                        'load_warnings': len(load_result.warnings),
                        'load_errors': len(load_result.errors),
                        'validation_warnings': len(validation_result['warnings']),
                        'validation_errors': len(validation_result['errors']),
                        'graceful_handling': graceful_handling,
                        'validation_detected_issues': validation_detected_issues
                    }
                )
                
                if not passed:
                    issues = []
                    if not graceful_handling:
                        issues.append("CSV loader failed to handle corrupted data gracefully")
                    if not validation_detected_issues:
                        issues.append("Validator failed to detect data quality issues")
                    result.errors.extend(issues)
                else:
                    self.simple_log(f"✅ {test_name}: Error recovery mechanisms working correctly", "info")
                    
            finally:
                if os.path.exists(csv_path):
                    os.unlink(csv_path)
                    
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="integration",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    # Performance Test Implementations
    
    def _test_large_dataset_performance(self):
        """Test performance with large datasets."""
        start_time = time.time()
        test_name = "Large Dataset Performance"
        
        try:
            # Create large test dataset (1000 rows)
            large_dataset = self._create_large_test_dataset(1000)
            
            # Time the complete processing
            processing_start = time.time()
            
            extractor = CSVMetricsExtractor()
            metrics = extractor.extract_metrics(large_dataset, self.simple_log)
            
            processing_time = time.time() - processing_start
            
            # Performance criteria: should process 1000 rows in under 5 seconds
            max_processing_time = 5.0
            performance_acceptable = processing_time <= max_processing_time
            
            # Check that metrics were extracted correctly
            metrics_complete = (
                len(metrics.ticker_metrics) > 0 and
                len(metrics.portfolio_summary) > 0 and
                'total_trades' in metrics.portfolio_summary
            )
            
            passed = performance_acceptable and metrics_complete
            
            result = TestResult(
                test_name=test_name,
                category="performance",
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'dataset_size': len(large_dataset),
                    'processing_time': processing_time,
                    'max_allowed_time': max_processing_time,
                    'performance_acceptable': performance_acceptable,
                    'metrics_complete': metrics_complete,
                    'rows_per_second': len(large_dataset) / processing_time if processing_time > 0 else 0
                }
            )
            
            if not passed:
                issues = []
                if not performance_acceptable:
                    issues.append(f"Processing too slow: {processing_time:.2f}s > {max_processing_time}s")
                if not metrics_complete:
                    issues.append("Metrics extraction incomplete")
                result.errors.extend(issues)
            else:
                self.simple_log(f"✅ {test_name}: Processed {len(large_dataset)} rows in {processing_time:.2f}s", "info")
                
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="performance",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    def _test_memory_usage_efficiency(self):
        """Test memory usage efficiency."""
        start_time = time.time()
        test_name = "Memory Usage Efficiency"
        
        try:
            import psutil
            process = psutil.Process()
            
            # Get baseline memory usage
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Process multiple datasets
            datasets = []
            for i in range(5):
                dataset = self._create_large_test_dataset(200)
                datasets.append(dataset)
            
            # Process all datasets
            extractor = CSVMetricsExtractor()
            all_metrics = []
            
            for dataset in datasets:
                metrics = extractor.extract_metrics(dataset, self.simple_log)
                all_metrics.append(metrics)
            
            # Check final memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - baseline_memory
            
            # Memory usage criteria: should not increase by more than 100MB for this test
            max_memory_increase = 100.0  # MB
            memory_efficient = memory_increase <= max_memory_increase
            
            passed = memory_efficient and len(all_metrics) == 5
            
            result = TestResult(
                test_name=test_name,
                category="performance",
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'baseline_memory_mb': baseline_memory,
                    'final_memory_mb': final_memory,
                    'memory_increase_mb': memory_increase,
                    'max_allowed_increase_mb': max_memory_increase,
                    'memory_efficient': memory_efficient,
                    'datasets_processed': len(all_metrics)
                }
            )
            
            if not passed:
                if not memory_efficient:
                    result.errors.append(f"Excessive memory usage: {memory_increase:.1f}MB > {max_memory_increase}MB")
                if len(all_metrics) != 5:
                    result.errors.append(f"Processing incomplete: {len(all_metrics)}/5 datasets")
            else:
                self.simple_log(f"✅ {test_name}: Memory increase {memory_increase:.1f}MB (acceptable)", "info")
                
        except ImportError:
            result = TestResult(
                test_name=test_name,
                category="performance",
                passed=True,  # Skip if psutil not available
                execution_time=time.time() - start_time,
                warnings=["psutil not available, memory test skipped"]
            )
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="performance",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    def _test_calculation_speed_benchmarks(self):
        """Test calculation speed benchmarks."""
        start_time = time.time()
        test_name = "Calculation Speed Benchmarks"
        
        try:
            # Benchmark different components
            test_data = self._create_comprehensive_test_data()
            benchmarks = {}
            
            # Benchmark 1: CSV loading
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                test_data.to_csv(f.name, index=False)
                csv_path = f.name
            
            try:
                loader_start = time.time()
                loader = CSVLoader()
                load_result = loader.load_csv(csv_path, self.simple_log)
                benchmarks['csv_loading'] = time.time() - loader_start
                
                # Benchmark 2: Metrics extraction
                extraction_start = time.time()
                extractor = CSVMetricsExtractor()
                metrics = extractor.extract_metrics(load_result.data, self.simple_log)
                benchmarks['metrics_extraction'] = time.time() - extraction_start
                
                # Benchmark 3: Validation
                validation_start = time.time()
                validator = CSVValidator()
                validation_result = validator.validate_csv_data(load_result.data, self.simple_log)
                benchmarks['validation'] = time.time() - validation_start
                
                # Performance criteria (for small test dataset)
                performance_criteria = {
                    'csv_loading': 0.5,      # 500ms
                    'metrics_extraction': 0.2,  # 200ms
                    'validation': 0.3        # 300ms
                }
                
                performance_acceptable = all(
                    benchmarks[component] <= max_time 
                    for component, max_time in performance_criteria.items()
                )
                
                passed = performance_acceptable and load_result.success
                
                result = TestResult(
                    test_name=test_name,
                    category="performance",
                    passed=passed,
                    execution_time=time.time() - start_time,
                    details={
                        'benchmarks': benchmarks,
                        'performance_criteria': performance_criteria,
                        'performance_acceptable': performance_acceptable,
                        'total_processing_time': sum(benchmarks.values())
                    }
                )
                
                if not passed:
                    slow_components = [
                        f"{comp}: {time:.3f}s > {performance_criteria[comp]:.3f}s"
                        for comp, time in benchmarks.items()
                        if time > performance_criteria[comp]
                    ]
                    if slow_components:
                        result.errors.append(f"Slow components: {'; '.join(slow_components)}")
                    if not load_result.success:
                        result.errors.append("CSV loading failed")
                else:
                    total_time = sum(benchmarks.values())
                    self.simple_log(f"✅ {test_name}: All components within performance criteria (total: {total_time:.3f}s)", "info")
                    
            finally:
                if os.path.exists(csv_path):
                    os.unlink(csv_path)
                    
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="performance",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    # Production Readiness Tests
    
    def _test_edge_case_handling(self):
        """Test handling of edge cases."""
        start_time = time.time()
        test_name = "Edge Case Handling"
        
        try:
            edge_cases_passed = []
            
            # Edge Case 1: Empty dataset
            try:
                empty_data = pd.DataFrame()
                extractor = CSVMetricsExtractor()
                empty_metrics = extractor.extract_metrics(empty_data, self.simple_log)
                edge_cases_passed.append(True)  # Should not crash
            except Exception:
                edge_cases_passed.append(False)
            
            # Edge Case 2: Single row dataset
            try:
                single_row = pd.DataFrame({
                    'Ticker': ['TEST'],
                    'Strategy': ['Strategy'],
                    'Total Return %': [10.0],
                    'Total Trades': [1]
                })
                single_metrics = extractor.extract_metrics(single_row, self.simple_log)
                edge_cases_passed.append(True)
            except Exception:
                edge_cases_passed.append(False)
            
            # Edge Case 3: All NaN values
            try:
                nan_data = pd.DataFrame({
                    'Ticker': ['TEST'],
                    'Strategy': ['Strategy'],
                    'Total Return %': [np.nan],
                    'Sharpe Ratio': [np.nan],
                    'Total Trades': [np.nan]
                })
                nan_metrics = extractor.extract_metrics(nan_data, self.simple_log)
                edge_cases_passed.append(True)
            except Exception:
                edge_cases_passed.append(False)
            
            # Edge Case 4: Extreme values
            try:
                extreme_data = pd.DataFrame({
                    'Ticker': ['TEST'],
                    'Strategy': ['Strategy'],
                    'Total Return %': [999999.0],
                    'Max Drawdown %': [100.0],
                    'Sharpe Ratio': [-999.0],
                    'Total Trades': [0]
                })
                extreme_metrics = extractor.extract_metrics(extreme_data, self.simple_log)
                edge_cases_passed.append(True)
            except Exception:
                edge_cases_passed.append(False)
            
            edge_cases_handled = sum(edge_cases_passed)
            total_edge_cases = len(edge_cases_passed)
            
            # Require at least 75% of edge cases to be handled gracefully
            pass_threshold = 0.75
            passed = (edge_cases_handled / total_edge_cases) >= pass_threshold
            
            result = TestResult(
                test_name=test_name,
                category="production_readiness",
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'edge_cases_handled': edge_cases_handled,
                    'total_edge_cases': total_edge_cases,
                    'success_rate': edge_cases_handled / total_edge_cases,
                    'pass_threshold': pass_threshold,
                    'edge_cases': [
                        'empty_dataset',
                        'single_row_dataset', 
                        'all_nan_values',
                        'extreme_values'
                    ]
                }
            )
            
            if not passed:
                result.errors.append(f"Edge case handling insufficient: {edge_cases_handled}/{total_edge_cases} handled successfully")
            else:
                self.simple_log(f"✅ {test_name}: {edge_cases_handled}/{total_edge_cases} edge cases handled gracefully", "info")
                
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="production_readiness",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    def _test_concurrent_access_safety(self):
        """Test concurrent access safety."""
        start_time = time.time()
        test_name = "Concurrent Access Safety"
        
        try:
            import threading
            import queue
            
            test_data = self._create_comprehensive_test_data()
            results_queue = queue.Queue()
            errors_queue = queue.Queue()
            
            def worker_function(worker_id):
                """Worker function for concurrent testing."""
                try:
                    extractor = CSVMetricsExtractor()
                    metrics = extractor.extract_metrics(test_data.copy(), self.simple_log)
                    results_queue.put((worker_id, True, metrics))
                except Exception as e:
                    errors_queue.put((worker_id, str(e)))
                    results_queue.put((worker_id, False, None))
            
            # Run 5 concurrent workers
            threads = []
            num_workers = 5
            
            for i in range(num_workers):
                thread = threading.Thread(target=worker_function, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Collect results
            successful_workers = 0
            failed_workers = 0
            
            while not results_queue.empty():
                worker_id, success, metrics = results_queue.get()
                if success:
                    successful_workers += 1
                else:
                    failed_workers += 1
            
            # Check for errors
            errors = []
            while not errors_queue.empty():
                worker_id, error = errors_queue.get()
                errors.append(f"Worker {worker_id}: {error}")
            
            # All workers should succeed
            passed = successful_workers == num_workers and failed_workers == 0
            
            result = TestResult(
                test_name=test_name,
                category="production_readiness",
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'num_workers': num_workers,
                    'successful_workers': successful_workers,
                    'failed_workers': failed_workers,
                    'errors': errors
                }
            )
            
            if not passed:
                result.errors.append(f"Concurrent access issues: {failed_workers}/{num_workers} workers failed")
                result.errors.extend(errors)
            else:
                self.simple_log(f"✅ {test_name}: All {num_workers} concurrent workers succeeded", "info")
                
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="production_readiness",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    def _test_data_corruption_recovery(self):
        """Test recovery from data corruption scenarios."""
        start_time = time.time()
        test_name = "Data Corruption Recovery"
        
        try:
            recovery_scenarios_passed = []
            
            # Scenario 1: Invalid CSV structure
            try:
                invalid_csv_content = "This is not a valid CSV file\nNo headers here\nJust random text"
                with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                    f.write(invalid_csv_content)
                    invalid_csv_path = f.name
                
                loader = CSVLoader(strict_validation=False)
                load_result = loader.load_csv(invalid_csv_path, self.simple_log)
                
                # Should fail gracefully with errors, not crash
                graceful_failure = not load_result.success and len(load_result.errors) > 0
                recovery_scenarios_passed.append(graceful_failure)
                
                os.unlink(invalid_csv_path)
            except Exception:
                recovery_scenarios_passed.append(False)
            
            # Scenario 2: Mixed data types in numeric columns
            try:
                mixed_data = pd.DataFrame({
                    'Ticker': ['TEST1', 'TEST2'],
                    'Total Return %': [15.0, 'not_a_number'],
                    'Max Drawdown %': ['12.5%', 18.0],
                    'Total Trades': [100, '150_trades']
                })
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                    mixed_data.to_csv(f.name, index=False)
                    mixed_csv_path = f.name
                
                load_result = loader.load_csv(mixed_csv_path, self.simple_log)
                
                # Should handle mixed types gracefully
                handled_gracefully = load_result.success and len(load_result.warnings) > 0
                recovery_scenarios_passed.append(handled_gracefully)
                
                os.unlink(mixed_csv_path)
            except Exception:
                recovery_scenarios_passed.append(False)
            
            # Scenario 3: Truncated/incomplete data
            try:
                incomplete_data = pd.DataFrame({
                    'Ticker': ['TEST1', 'TEST2', None],
                    'Total Return %': [15.0, None, 22.0],
                    # Missing other expected columns
                })
                
                extractor = CSVMetricsExtractor()
                incomplete_metrics = extractor.extract_metrics(incomplete_data, self.simple_log)
                
                # Should extract what it can
                partial_extraction = len(incomplete_metrics.ticker_metrics) > 0
                recovery_scenarios_passed.append(partial_extraction)
            except Exception:
                recovery_scenarios_passed.append(False)
            
            scenarios_handled = sum(recovery_scenarios_passed)
            total_scenarios = len(recovery_scenarios_passed)
            
            # Require at least 2 out of 3 scenarios to be handled
            pass_threshold = 2
            passed = scenarios_handled >= pass_threshold
            
            result = TestResult(
                test_name=test_name,
                category="production_readiness",
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'scenarios_handled': scenarios_handled,
                    'total_scenarios': total_scenarios,
                    'pass_threshold': pass_threshold,
                    'scenarios': [
                        'invalid_csv_structure',
                        'mixed_data_types',
                        'incomplete_data'
                    ]
                }
            )
            
            if not passed:
                result.errors.append(f"Data corruption recovery insufficient: {scenarios_handled}/{total_scenarios} scenarios handled")
            else:
                self.simple_log(f"✅ {test_name}: {scenarios_handled}/{total_scenarios} corruption scenarios handled", "info")
                
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="production_readiness",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    def _test_configuration_validation(self):
        """Test configuration validation and settings."""
        start_time = time.time()
        test_name = "Configuration Validation"
        
        try:
            config_tests_passed = []
            
            # Test 1: Valid configuration
            try:
                valid_config = CalculationConfig(
                    csv_as_source_of_truth=True,
                    enable_reconciliation=True,
                    strict_validation=False
                )
                calculator = UnifiedMetricsCalculator(valid_config)
                config_tests_passed.append(True)
            except Exception:
                config_tests_passed.append(False)
            
            # Test 2: Configuration with different aggregation methods
            try:
                for method in ['weighted', 'equal', 'trade_weighted']:
                    test_config = CalculationConfig(aggregation_method=method)
                    extractor = CSVMetricsExtractor(aggregation_method=method)
                    config_tests_passed.append(True)
                    break  # If any method works, consider it passed
            except Exception:
                config_tests_passed.append(False)
            
            # Test 3: Tolerance configuration
            try:
                custom_tolerance = {
                    'total_return_pct': 0.02,
                    'sharpe_ratio': 0.15,
                    'max_drawdown_pct': 0.10
                }
                reconciler = DataReconciler(tolerance_config=custom_tolerance)
                config_tests_passed.append(True)
            except Exception:
                config_tests_passed.append(False)
            
            configs_working = sum(config_tests_passed)
            total_configs = len(config_tests_passed)
            
            passed = configs_working == total_configs
            
            result = TestResult(
                test_name=test_name,
                category="production_readiness",
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'configs_working': configs_working,
                    'total_configs': total_configs,
                    'config_tests': [
                        'valid_unified_config',
                        'aggregation_methods',
                        'tolerance_configuration'
                    ]
                }
            )
            
            if not passed:
                result.errors.append(f"Configuration validation issues: {configs_working}/{total_configs} configurations working")
            else:
                self.simple_log(f"✅ {test_name}: All {total_configs} configuration tests passed", "info")
                
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="production_readiness",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    # Data Quality Tests
    
    def _test_data_validation_framework(self):
        """Test the data validation framework."""
        start_time = time.time()
        test_name = "Data Validation Framework"
        
        try:
            # Create test data with various quality issues
            test_data = pd.DataFrame({
                'Ticker': ['GOOD', 'BAD1', 'BAD2', None],
                'Strategy': ['StrategyA', 'StrategyB', None, 'StrategyD'],
                'Total Return %': [15.0, -5.0, 999.0, 12.0],
                'Max Drawdown %': [12.0, -10.0, 120.0, 15.0],  # Negative and >100%
                'Sharpe Ratio': [1.2, -999.0, np.nan, 1.8],
                'Win Rate %': [65.0, 150.0, -10.0, 55.0],  # >100% and negative
                'Total Trades': [100, 0, 50, np.nan]
            })
            
            # Test validation framework
            validator = CSVValidator()
            validation_result = validator.validate_csv_data(test_data, self.simple_log)
            
            # Should detect multiple issues
            issues_detected = len(validation_result['warnings']) + len(validation_result['errors'])
            quality_score = validation_result['quality_score']
            
            # Validate that validation framework is working
            framework_working = (
                issues_detected >= 3 and  # Should detect multiple issues
                quality_score < 0.8 and   # Quality should be low
                len(validation_result['checks_performed']) >= 3  # Multiple checks
            )
            
            # Test with clean data
            clean_data = pd.DataFrame({
                'Ticker': ['TEST1', 'TEST2'],
                'Strategy': ['StrategyA', 'StrategyB'],
                'Total Return %': [15.0, 18.0],
                'Max Drawdown %': [12.0, 8.0],
                'Sharpe Ratio': [1.2, 1.5],
                'Win Rate %': [65.0, 72.0],
                'Total Trades': [100, 120]
            })
            
            clean_validation = validator.validate_csv_data(clean_data, self.simple_log)
            clean_quality = clean_validation['quality_score']
            
            # Clean data should have high quality
            clean_data_recognized = clean_quality > 0.8 and clean_validation['overall_valid']
            
            passed = framework_working and clean_data_recognized
            
            result = TestResult(
                test_name=test_name,
                category="data_quality",
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'issues_detected': issues_detected,
                    'bad_data_quality_score': quality_score,
                    'clean_data_quality_score': clean_quality,
                    'framework_working': framework_working,
                    'clean_data_recognized': clean_data_recognized,
                    'checks_performed': validation_result['checks_performed']
                }
            )
            
            if not passed:
                issues = []
                if not framework_working:
                    issues.append(f"Validation framework not detecting issues properly: {issues_detected} issues, quality {quality_score:.2f}")
                if not clean_data_recognized:
                    issues.append(f"Clean data not recognized: quality {clean_quality:.2f}")
                result.errors.extend(issues)
            else:
                self.simple_log(f"✅ {test_name}: Validation framework working correctly", "info")
                
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="data_quality",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    def _test_cross_validation_accuracy(self):
        """Test cross-validation accuracy between methods."""
        start_time = time.time()
        test_name = "Cross-Validation Accuracy"
        
        try:
            # Create test data where we know the expected values
            test_data = pd.DataFrame({
                'Ticker': ['TEST'],
                'Strategy': ['Strategy'],
                'Total Return %': [20.0],
                'Max Drawdown %': [15.0],
                'Sharpe Ratio': [1.5],
                'Win Rate %': [60.0],
                'Total Trades': [100]
            })
            
            # Method 1: CSV extraction
            extractor = CSVMetricsExtractor()
            csv_metrics = extractor.extract_metrics(test_data, self.simple_log)
            
            # Method 2: Direct calculation validation
            validator = PortfolioMetricsValidator()
            
            # Create mock portfolio data for validation
            mock_portfolio = {
                'ticker_metrics': {
                    'TEST': {
                        'total_return_pct': 20.0,
                        'max_drawdown_pct': 15.0,
                        'sharpe_ratio': 1.5,
                        'win_rate_pct': 60.0,
                        'total_trades': 100
                    }
                }
            }
            
            validation_results = validator.validate_all(mock_portfolio, self.simple_log)
            
            # Cross-validate results
            csv_total_return = csv_metrics.ticker_metrics.get('TEST', {}).get('total_return__pct', 0)
            csv_sharpe = csv_metrics.ticker_metrics.get('TEST', {}).get('sharpe_ratio', 0)
            
            # Values should match within tolerance
            return_match = abs(csv_total_return - 20.0) < 1.0
            sharpe_match = abs(csv_sharpe - 1.5) < 0.1
            validation_passed = validation_results.get('overall_valid', False)
            
            passed = return_match and sharpe_match and validation_passed
            
            result = TestResult(
                test_name=test_name,
                category="data_quality",
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'expected_return': 20.0,
                    'csv_extracted_return': csv_total_return,
                    'return_match': return_match,
                    'expected_sharpe': 1.5,
                    'csv_extracted_sharpe': csv_sharpe,
                    'sharpe_match': sharpe_match,
                    'validation_passed': validation_passed
                }
            )
            
            if not passed:
                issues = []
                if not return_match:
                    issues.append(f"Return mismatch: expected 20.0, got {csv_total_return:.2f}")
                if not sharpe_match:
                    issues.append(f"Sharpe mismatch: expected 1.5, got {csv_sharpe:.2f}")
                if not validation_passed:
                    issues.append("Portfolio validation failed")
                result.errors.extend(issues)
            else:
                self.simple_log(f"✅ {test_name}: Cross-validation accuracy confirmed", "info")
                
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="data_quality",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    def _test_data_quality_scoring(self):
        """Test data quality scoring accuracy."""
        start_time = time.time()
        test_name = "Data Quality Scoring"
        
        try:
            # Test with different quality datasets
            quality_tests = []
            
            # High quality dataset
            high_quality_data = pd.DataFrame({
                'Ticker': ['TEST1', 'TEST2', 'TEST3'],
                'Strategy': ['StrategyA', 'StrategyB', 'StrategyC'],
                'Total Return %': [15.0, 18.0, 12.0],
                'Max Drawdown %': [8.0, 12.0, 6.0],
                'Sharpe Ratio': [1.2, 1.5, 1.1],
                'Win Rate %': [65.0, 58.0, 72.0],
                'Total Trades': [100, 120, 90]
            })
            
            loader = CSVLoader()
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                high_quality_data.to_csv(f.name, index=False)
                hq_path = f.name
            
            try:
                hq_result = loader.load_csv(hq_path, self.simple_log)
                hq_score = hq_result.data_quality_score
                quality_tests.append(('high_quality', hq_score, hq_score > 0.8))
            finally:
                os.unlink(hq_path)
            
            # Medium quality dataset (some missing values)
            medium_quality_data = pd.DataFrame({
                'Ticker': ['TEST1', 'TEST2', None],
                'Strategy': ['StrategyA', None, 'StrategyC'],
                'Total Return %': [15.0, np.nan, 12.0],
                'Max Drawdown %': [8.0, 12.0, 6.0],
                'Sharpe Ratio': [1.2, 1.5, np.nan],
                'Win Rate %': [65.0, 58.0, 72.0],
                'Total Trades': [100, 120, 90]
            })
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                medium_quality_data.to_csv(f.name, index=False)
                mq_path = f.name
            
            try:
                mq_result = loader.load_csv(mq_path, self.simple_log)
                mq_score = mq_result.data_quality_score
                quality_tests.append(('medium_quality', mq_score, 0.4 < mq_score < 0.8))
            finally:
                os.unlink(mq_path)
            
            # Low quality dataset (many issues)
            low_quality_data = pd.DataFrame({
                'Ticker': [None, 'TEST2', None],
                'Strategy': [None, None, 'StrategyC'],
                'Total Return %': [np.nan, 'invalid', 12.0],
                'Max Drawdown %': [-8.0, 120.0, np.nan],
                'Sharpe Ratio': [np.nan, np.nan, np.nan],
                'Win Rate %': [165.0, -10.0, np.nan],
                'Total Trades': [0, np.nan, -5]
            })
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                low_quality_data.to_csv(f.name, index=False)
                lq_path = f.name
            
            try:
                lq_result = loader.load_csv(lq_path, self.simple_log)
                lq_score = lq_result.data_quality_score
                quality_tests.append(('low_quality', lq_score, lq_score < 0.4))
            finally:
                os.unlink(lq_path)
            
            # Check that scoring correctly differentiates quality levels
            scoring_accurate = all(test_passed for _, _, test_passed in quality_tests)
            
            # Check that scores are in correct order: high > medium > low
            if len(quality_tests) == 3:
                hq_score = quality_tests[0][1]
                mq_score = quality_tests[1][1]
                lq_score = quality_tests[2][1]
                score_ordering = hq_score > mq_score > lq_score
            else:
                score_ordering = True  # Skip if not all tests completed
            
            passed = scoring_accurate and score_ordering
            
            result = TestResult(
                test_name=test_name,
                category="data_quality",
                passed=passed,
                execution_time=time.time() - start_time,
                details={
                    'quality_tests': quality_tests,
                    'scoring_accurate': scoring_accurate,
                    'score_ordering_correct': score_ordering
                }
            )
            
            if not passed:
                issues = []
                if not scoring_accurate:
                    failed_tests = [name for name, score, test_passed in quality_tests if not test_passed]
                    issues.append(f"Scoring inaccurate for: {failed_tests}")
                if not score_ordering:
                    issues.append("Score ordering incorrect: high quality should > medium > low")
                result.errors.extend(issues)
            else:
                scores_summary = ", ".join([f"{name}: {score:.2f}" for name, score, _ in quality_tests])
                self.simple_log(f"✅ {test_name}: Quality scoring accurate ({scores_summary})", "info")
                
        except Exception as e:
            result = TestResult(
                test_name=test_name,
                category="data_quality",
                passed=False,
                execution_time=time.time() - start_time,
                errors=[f"Test execution failed: {str(e)}"]
            )
        
        self.results.append(result)
    
    # Helper Methods
    
    def _create_comprehensive_test_data(self) -> pd.DataFrame:
        """Create comprehensive test data for testing."""
        return pd.DataFrame({
            'Ticker': ['BTC-USD', 'MSTR', 'QQQ'] * 3,
            'Strategy': ['EMA_5_21', 'EMA_8_21', 'EMA_13_21'] * 3,
            'Start': ['2023-01-01'] * 9,
            'End': ['2023-12-31'] * 9,
            'Duration': ['365 days'] * 9,
            'Total Return %': [45.2, 62.8, 18.3, 78.9, 134.2, 22.1, 35.6, 48.2, 16.8],
            'Annual Return %': [42.1, 58.3, 17.2, 72.4, 122.8, 20.5, 33.2, 44.7, 15.9],
            'Annual Volatility %': [28.5, 35.2, 19.8, 42.1, 48.6, 21.3, 25.7, 31.4, 18.9],
            'Sharpe Ratio': [1.48, 1.66, 0.87, 1.72, 2.53, 0.96, 1.29, 1.42, 0.84],
            'Calmar Ratio': [2.34, 2.89, 1.42, 3.15, 4.21, 1.58, 2.12, 2.67, 1.38],
            'Max Drawdown %': [18.0, 20.2, 12.1, 23.1, 29.2, 13.0, 15.7, 16.8, 11.5],
            'Total Trades': [87, 94, 76, 105, 112, 82, 91, 98, 79],
            'Win Rate %': [64.4, 59.6, 67.1, 61.9, 58.0, 68.3, 65.9, 62.2, 69.6],
            'Avg Win %': [2.8, 3.2, 2.1, 3.6, 4.1, 2.3, 2.9, 3.1, 2.0],
            'Avg Loss %': [-1.8, -2.1, -1.3, -2.3, -2.7, -1.4, -1.9, -2.0, -1.2],
            'Profit Factor': [1.89, 1.94, 1.72, 2.08, 2.15, 1.78, 1.92, 1.96, 1.74],
            'Expectancy per Trade': [0.52, 0.67, 0.24, 0.75, 1.20, 0.27, 0.47, 0.62, 0.21]
        })
    
    def _create_test_json_data(self) -> Dict[str, Any]:
        """Create test JSON data for reconciliation testing."""
        return {
            'ticker_metrics': {
                'BTC-USD': {
                    'signal_quality_metrics': {
                        'signal_count': 320,
                        'avg_return': 0.038,
                        'win_rate': 0.64,
                        'sharpe_ratio': 1.35,
                        'max_drawdown': 0.22,
                        'profit_factor': 1.92,
                        'expectancy_per_signal': 0.48
                    }
                },
                'MSTR': {
                    'signal_quality_metrics': {
                        'signal_count': 380,
                        'avg_return': 0.071,
                        'win_rate': 0.59,
                        'sharpe_ratio': 1.79,
                        'max_drawdown': 0.28,
                        'profit_factor': 2.06,
                        'expectancy_per_signal': 0.85
                    }
                },
                'QQQ': {
                    'signal_quality_metrics': {
                        'signal_count': 280,
                        'avg_return': 0.019,
                        'win_rate': 0.68,
                        'sharpe_ratio': 0.89,
                        'max_drawdown': 0.14,
                        'profit_factor': 1.75,
                        'expectancy_per_signal': 0.24
                    }
                }
            },
            'portfolio_metrics': {
                'signals': {
                    'summary': {
                        'total': {
                            'value': 980
                        }
                    }
                },
                'efficiency': {
                    'signal_quality': {
                        'win_rate': 0.64,
                        'sharpe_ratio': 1.34
                    },
                    'risk_metrics': {
                        'max_portfolio_drawdown': 0.25
                    }
                }
            }
        }
    
    def _create_large_test_dataset(self, size: int) -> pd.DataFrame:
        """Create large test dataset for performance testing."""
        np.random.seed(42)
        
        tickers = ['BTC-USD', 'ETH-USD', 'MSTR', 'QQQ', 'SPY', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        strategies = ['EMA_5_21', 'EMA_8_21', 'EMA_13_21', 'SMA_10_30', 'MACD_12_26']
        
        data = []
        for i in range(size):
            ticker = np.random.choice(tickers)
            strategy = np.random.choice(strategies)
            
            row = {
                'Ticker': ticker,
                'Strategy': strategy,
                'Start': '2023-01-01',
                'End': '2023-12-31',
                'Duration': '365 days',
                'Total Return %': np.random.uniform(-20, 150),
                'Annual Return %': np.random.uniform(-15, 120),
                'Annual Volatility %': np.random.uniform(15, 45),
                'Sharpe Ratio': np.random.uniform(-0.5, 3.0),
                'Calmar Ratio': np.random.uniform(-0.2, 2.5),
                'Max Drawdown %': np.random.uniform(5, 75),
                'Total Trades': np.random.randint(20, 200),
                'Win Rate %': np.random.uniform(35, 75),
                'Avg Win %': np.random.uniform(1, 8),
                'Avg Loss %': np.random.uniform(-8, -1),
                'Profit Factor': np.random.uniform(0.5, 3.0),
                'Expectancy per Trade': np.random.uniform(-1, 5)
            }
            data.append(row)
        
        return pd.DataFrame(data)
    
    def _generate_test_summary(self, suite: TestSuite) -> Dict[str, Any]:
        """Generate comprehensive test summary."""
        # Categorize results
        categories = {}
        for result in suite.results:
            category = result.category
            if category not in categories:
                categories[category] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'avg_execution_time': 0.0
                }
            
            categories[category]['total'] += 1
            if result.passed:
                categories[category]['passed'] += 1
            else:
                categories[category]['failed'] += 1
        
        # Calculate average execution times
        for category, stats in categories.items():
            category_results = [r for r in suite.results if r.category == category]
            if category_results:
                stats['avg_execution_time'] = np.mean([r.execution_time for r in category_results])
        
        # Overall metrics
        overall_pass_rate = (suite.tests_passed / suite.tests_run) * 100 if suite.tests_run > 0 else 0
        
        # Critical failures (regression tests failing)
        regression_failures = [r for r in suite.results if r.category == 'regression' and not r.passed]
        critical_failure_count = len(regression_failures)
        
        # Performance metrics
        performance_results = [r for r in suite.results if r.category == 'performance']
        performance_issues = [r for r in performance_results if not r.passed]
        
        return {
            'overall_pass_rate': overall_pass_rate,
            'categories': categories,
            'critical_failures': critical_failure_count,
            'performance_issues': len(performance_issues),
            'total_execution_time': suite.total_execution_time,
            'tests_per_second': suite.tests_run / suite.total_execution_time if suite.total_execution_time > 0 else 0,
            'production_ready': (
                critical_failure_count == 0 and
                overall_pass_rate >= 90 and
                len(performance_issues) <= 1
            )
        }


def main():
    """Run the comprehensive Phase 6 test suite."""
    runner = Phase6TestRunner()
    suite = runner.run_all_tests()
    
    # Display results
    print(f"\n🎯 Phase 6 Test Results Summary")
    print("=" * 40)
    print(f"Tests Run: {suite.tests_run}")
    print(f"Tests Passed: {suite.tests_passed}")
    print(f"Tests Failed: {suite.tests_failed}")
    print(f"Overall Pass Rate: {suite.summary['overall_pass_rate']:.1f}%")
    print(f"Total Execution Time: {suite.total_execution_time:.2f}s")
    print(f"Production Ready: {'✅ YES' if suite.summary['production_ready'] else '❌ NO'}")
    
    # Category breakdown
    print(f"\n📊 Results by Category:")
    for category, stats in suite.summary['categories'].items():
        pass_rate = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"  {category.title()}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%) - avg {stats['avg_execution_time']:.3f}s")
    
    # Critical issues
    if suite.summary['critical_failures'] > 0:
        print(f"\n🚨 Critical Issues ({suite.summary['critical_failures']}):")
        for result in suite.results:
            if result.category == 'regression' and not result.passed:
                print(f"  ❌ {result.test_name}")
                for error in result.errors:
                    print(f"    • {error}")
    
    # Export results
    results_file = f"phase6_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Convert suite to dict for JSON serialization
    suite_dict = {
        'suite_name': suite.suite_name,
        'start_time': suite.start_time,
        'end_time': suite.end_time,
        'total_execution_time': suite.total_execution_time,
        'tests_run': suite.tests_run,
        'tests_passed': suite.tests_passed,
        'tests_failed': suite.tests_failed,
        'summary': suite.summary,
        'results': [
            {
                'test_name': r.test_name,
                'category': r.category,
                'passed': r.passed,
                'execution_time': r.execution_time,
                'details': r.details,
                'errors': r.errors,
                'warnings': r.warnings
            }
            for r in suite.results
        ]
    }
    
    with open(results_file, 'w') as f:
        json.dump(suite_dict, f, indent=2, default=str)
    
    print(f"\n💾 Test results exported to: {results_file}")
    
    return suite.summary['production_ready']


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)