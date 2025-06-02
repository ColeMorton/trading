#!/usr/bin/env python3
"""
Test Script for Phase 1: Data Validation and Alignment Framework

This script tests the newly implemented validation framework against
the actual portfolio data to demonstrate the identified issues.
"""

import sys
from pathlib import Path
import json

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.concurrency.tools.validation import PortfolioMetricsValidator, validate_portfolio_metrics
from app.concurrency.tools.cross_validator import CSVJSONCrossValidator, CrossValidationConfig, run_cross_validation
from app.tools.setup_logging import setup_logging


def main():
    """Run Phase 1 validation tests."""
    # Setup logging
    from app.tools.setup_logging import setup_logging
    
    def simple_log(message, level):
        print(f"[{level.upper()}] {message}")
    
    log = simple_log
    
    print("🔍 Phase 1 Validation Framework Test")
    print("=" * 50)
    
    # Define test data paths
    csv_path = "csv/strategies/portfolio_d_20250530.csv"
    json_path = "json/concurrency/portfolio_d_20250530.json"
    
    # Check if files exist
    if not Path(csv_path).exists():
        print(f"❌ CSV file not found: {csv_path}")
        return False
    
    if not Path(json_path).exists():
        print(f"❌ JSON file not found: {json_path}")
        return False
    
    print(f"📊 Testing with:")
    print(f"   CSV: {csv_path}")
    print(f"   JSON: {json_path}")
    print()
    
    # Load JSON metrics
    try:
        with open(json_path, 'r') as f:
            json_metrics = json.load(f)
        print("✅ JSON metrics loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load JSON metrics: {e}")
        return False
    
    # Test 1: Basic Portfolio Metrics Validation
    print("\n🧪 Test 1: Basic Portfolio Metrics Validation")
    print("-" * 45)
    
    try:
        validation_summary = validate_portfolio_metrics(csv_path, json_metrics, log)
        
        print(f"📈 Results:")
        print(f"   Total checks: {validation_summary.total_checks}")
        print(f"   Passed: {validation_summary.passed_checks}")
        print(f"   Failed: {validation_summary.failed_checks}")
        print(f"   Critical failures: {validation_summary.critical_failures}")
        print(f"   Success rate: {validation_summary.success_rate:.1%}")
        
        if validation_summary.critical_failures > 0:
            print(f"\n⚠️  Critical Issues Found:")
            for result in validation_summary.results:
                if not result.passed and result.severity == "critical":
                    print(f"   • {result.check_name}: {result.error_message}")
        
        print("✅ Basic validation completed")
        
    except Exception as e:
        print(f"❌ Basic validation failed: {e}")
        return False
    
    # Test 2: Cross-Validation with Detailed Analysis
    print("\n🔬 Test 2: CSV-JSON Cross-Validation")
    print("-" * 40)
    
    try:
        # Create output path for detailed report
        report_path = "logs/phase1_cross_validation_report.md"
        
        cross_validation_report = run_cross_validation(
            csv_path=csv_path,
            json_metrics=json_metrics,
            output_path=report_path,
            log=log
        )
        
        print(f"📊 Cross-Validation Results:")
        print(f"   Data quality score: {cross_validation_report.data_quality_score:.2f} / 1.00")
        print(f"   Ticker comparisons: {len(cross_validation_report.ticker_comparisons)}")
        print(f"   Portfolio issues: {len(cross_validation_report.portfolio_level_issues)}")
        print(f"   Recommendations: {len(cross_validation_report.recommendations)}")
        
        if cross_validation_report.portfolio_level_issues:
            print(f"\n🚨 Portfolio-Level Issues Found:")
            for issue in cross_validation_report.portfolio_level_issues[:3]:  # Show first 3
                print(f"   • {issue}")
            if len(cross_validation_report.portfolio_level_issues) > 3:
                print(f"   ... and {len(cross_validation_report.portfolio_level_issues) - 3} more")
        
        if cross_validation_report.recommendations:
            print(f"\n💡 Top Recommendations:")
            for rec in cross_validation_report.recommendations[:3]:  # Show first 3
                print(f"   • {rec}")
            if len(cross_validation_report.recommendations) > 3:
                print(f"   ... and {len(cross_validation_report.recommendations) - 3} more")
        
        print(f"\n📋 Detailed report saved to: {report_path}")
        print("✅ Cross-validation completed")
        
    except Exception as e:
        print(f"❌ Cross-validation failed: {e}")
        return False
    
    # Test 3: Specific Issue Detection
    print("\n🎯 Test 3: Specific Issue Detection")
    print("-" * 38)
    
    try:
        # Test for signal count inflation
        portfolio_signals = json_metrics.get('portfolio_metrics', {}).get('signals', {}).get('summary', {}).get('total', {}).get('value', 0)
        quality_signals = json_metrics.get('portfolio_metrics', {}).get('signal_quality', {}).get('signal_count', {}).get('value', 0)
        
        print(f"🔢 Signal Count Analysis:")
        print(f"   Portfolio total signals: {portfolio_signals:,}")
        print(f"   Signal quality count: {quality_signals:,}")
        
        if portfolio_signals > 10000:
            print(f"   ⚠️  Potential signal count inflation detected!")
        
        # Test for expectancy magnitude
        portfolio_expectancy = json_metrics.get('portfolio_metrics', {}).get('efficiency', {}).get('expectancy', {}).get('value', 0)
        print(f"\n💰 Expectancy Analysis:")
        print(f"   Portfolio expectancy: {portfolio_expectancy:.2f}")
        
        if abs(portfolio_expectancy) > 100:
            print(f"   ⚠️  Expectancy magnitude appears unrealistic!")
        
        # Test for Sharpe ratio signs
        ticker_metrics = json_metrics.get('ticker_metrics', {})
        print(f"\n📊 Performance Sign Analysis:")
        
        for ticker, metrics in ticker_metrics.items():
            sharpe = metrics.get('signal_quality_metrics', {}).get('sharpe_ratio', 0)
            win_rate = metrics.get('signal_quality_metrics', {}).get('win_rate', 0)
            profit_factor = metrics.get('signal_quality_metrics', {}).get('profit_factor', 0)
            
            print(f"   {ticker}: Sharpe={sharpe:.3f}, Win Rate={win_rate:.1%}, PF={profit_factor:.2f}")
            
            if sharpe < 0 and win_rate > 0.6:
                print(f"      ⚠️  Negative Sharpe with high win rate - possible calculation error!")
        
        print("✅ Specific issue detection completed")
        
    except Exception as e:
        print(f"❌ Specific issue detection failed: {e}")
        return False
    
    # Summary
    print("\n🎉 Phase 1 Testing Summary")
    print("=" * 30)
    
    print("✅ All validation framework components tested successfully")
    print("✅ Issues identified and documented in detail")
    print("✅ Recommendations generated for fixes")
    
    print(f"\n📋 Next Steps:")
    print(f"   1. Review detailed report: logs/phase1_cross_validation_report.md")
    print(f"   2. Proceed to Phase 2: Signal Processing Reform")
    print(f"   3. Implement fixes based on validation results")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)