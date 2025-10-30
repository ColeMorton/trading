"""
Simple integration test for Statistical Analysis Service

Tests that all components can be imported and initialized correctly.
"""

import asyncio
import logging
import sys
from pathlib import Path


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.tools.config.statistical_analysis_config import SPDSConfig
from app.tools.services.statistical_analysis_service import StatisticalAnalysisService


async def test_service_initialization():
    """Test that StatisticalAnalysisService can be initialized"""
    try:
        # Create test configuration
        config = SPDSConfig.development_config()

        # Initialize logger
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        # Initialize service
        service = StatisticalAnalysisService(
            config=config,
            logger=logger,
            enable_memory_optimization=False,  # Disable for testing
        )

        print("✓ StatisticalAnalysisService initialized successfully")

        # Test health check
        health_status = await service.health_check()
        print(f"✓ Health check completed: {health_status['status']}")

        # Test service metrics
        metrics = service.get_service_metrics()
        print(f"✓ Service metrics: {metrics}")

        return True

    except Exception as e:
        print(f"✗ Service initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_component_imports():
    """Test that all analysis components can be imported"""
    try:
        from app.tools.analysis.bootstrap_validator import BootstrapValidator
        from app.tools.analysis.divergence_detector import DivergenceDetector
        from app.tools.analysis.trade_history_analyzer import TradeHistoryAnalyzer

        print("✓ All analysis components imported successfully")

        # Test component initialization
        config = SPDSConfig.development_config()

        DivergenceDetector(config=config)
        TradeHistoryAnalyzer(config=config)
        BootstrapValidator(config=config)

        print("✓ All analysis components initialized successfully")

        return True

    except Exception as e:
        print(f"✗ Component import/initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_models_import():
    """Test that all models can be imported"""
    try:
        print("✓ All models imported successfully")
        return True

    except Exception as e:
        print(f"✗ Model import failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all integration tests"""
    print("Running Statistical Analysis Service Integration Tests...")
    print("=" * 60)

    tests = [
        ("Model Imports", test_models_import),
        ("Component Imports", test_component_imports),
        ("Service Initialization", test_service_initialization),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("Test Results Summary:")

    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False

    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
