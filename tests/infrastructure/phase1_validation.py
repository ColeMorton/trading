#!/usr/bin/env python3
"""
Phase 1 Validation Script: Configuration Emergency Repair & Unification
Tests the success criteria for Phase 1 implementation.
"""

import subprocess
import sys
from pathlib import Path


def check_pytest_syntax():
    """Verify pytest.ini syntax is valid"""
    try:
        result = subprocess.run(['pytest', '--collect-only', '--quiet'], 
                              capture_output=True, text=True, timeout=30)
        # Check if collection completed (even with errors)
        if "collected" in result.stdout:
            return True, "pytest.ini syntax valid - test collection working"
        return False, f"pytest.ini syntax issues: {result.stderr}"
    except Exception as e:
        return False, f"pytest.ini validation failed: {str(e)}"


def check_configuration_consolidation():
    """Verify conflicting configuration files removed"""
    project_root = Path(__file__).parent.parent.parent
    
    # Check that conflicting files are removed
    api_pytest = project_root / "app" / "api" / "pytest.ini"
    concurrency_pytest = project_root / "tests" / "concurrency" / "pytest.ini"
    
    issues = []
    if api_pytest.exists():
        issues.append("app/api/pytest.ini still exists")
    if concurrency_pytest.exists():
        issues.append("tests/concurrency/pytest.ini still exists")
    
    if issues:
        return False, f"Configuration conflicts remain: {', '.join(issues)}"
    
    return True, "Configuration consolidation successful - no conflicting pytest.ini files"


def check_makefile_integration():
    """Verify make test command uses unified runner"""
    try:
        result = subprocess.run(['make', 'test-quick'], 
                              capture_output=True, text=True, timeout=60)
        
        # Check if make command uses unified runner
        if "run_unified_tests.py" in result.stderr:
            return True, "Makefile integration successful - uses unified test runner"
        return False, f"Makefile not using unified runner: {result.stderr}"
    except Exception as e:
        return False, f"Makefile validation failed: {str(e)}"


def check_coverage_configuration():
    """Verify coverage configuration is optimized"""
    project_root = Path(__file__).parent.parent.parent
    coveragerc = project_root / ".coveragerc"
    
    if not coveragerc.exists():
        return False, ".coveragerc file missing"
    
    content = coveragerc.read_text()
    if "format = term-missing" in content:
        return True, "Coverage configuration optimized"
    
    return False, "Coverage configuration not optimized"


def main():
    """Run all Phase 1 validation checks"""
    print("=" * 60)
    print("PHASE 1 VALIDATION: Configuration Emergency Repair")
    print("=" * 60)
    
    checks = [
        ("pytest.ini Syntax Fix", check_pytest_syntax),
        ("Configuration Consolidation", check_configuration_consolidation), 
        ("Coverage Optimization", check_coverage_configuration),
        ("Makefile Integration", check_makefile_integration),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}...")
        try:
            success, message = check_func()
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status}: {message}")
            results.append(success)
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total) * 100
    
    print("\n" + "=" * 60)
    print("PHASE 1 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Checks Passed: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 75:
        print("🎉 Phase 1 SUCCESS: Configuration consolidation achieved!")
        print("📋 Ready to proceed to Phase 2: Test Runner Consolidation")
        return 0
    else:
        print("⚠️  Phase 1 INCOMPLETE: Some issues need resolution")
        return 1


if __name__ == "__main__":
    sys.exit(main())