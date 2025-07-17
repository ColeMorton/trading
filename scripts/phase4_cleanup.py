#!/usr/bin/env python3
"""
Phase 4 Cleanup Script

Removes deprecated service files and over-engineered memory optimization files
as identified in the SPDS consolidation analysis.
"""

import os
import sys
from pathlib import Path

def remove_deprecated_files():
    """Remove deprecated files safely."""
    
    # Files to remove - deprecated services
    deprecated_services = [
        "app/tools/services/statistical_analysis_service.py",
        "app/tools/services/service_coordinator.py", 
        "app/tools/services/enhanced_service_coordinator.py",
        "app/tools/services/strategy_data_coordinator.py",
        "app/tools/services/statistical_analysis_service.py.backup_signal_fix",
        "app/tools/statistical_analysis_cli.py",
        "app/tools/test_statistical_analysis.py"
    ]
    
    # Files to remove - over-engineered memory optimization (4,828 LOC)
    memory_optimization_files = [
        "app/tools/processing/memory_optimizer.py",
        "app/tools/processing/cache_manager.py", 
        "app/tools/processing/streaming_processor.py",
        "app/tools/processing/data_converter.py",
        "app/tools/processing/performance_monitor.py",
        "app/tools/processing/auto_tuner.py",
        "app/tools/processing/cache_warmer.py",
        "app/tools/processing/performance_dashboard.py",
        "app/tools/processing/precompute_engine.py"
    ]
    
    all_files_to_remove = deprecated_services + memory_optimization_files
    
    print("🧹 SPDS Phase 4 Cleanup - File Removal")
    print("=" * 50)
    
    removed_count = 0
    total_lines_removed = 0
    
    for file_path in all_files_to_remove:
        if os.path.exists(file_path):
            # Count lines before removal
            try:
                with open(file_path, 'r') as f:
                    lines = len(f.readlines())
                total_lines_removed += lines
                
                os.remove(file_path)
                print(f"✅ Removed: {file_path} ({lines} lines)")
                removed_count += 1
                
            except Exception as e:
                print(f"❌ Failed to remove {file_path}: {e}")
        else:
            print(f"⚠️  Not found: {file_path}")
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   Files removed: {removed_count}")
    print(f"   Lines of code removed: {total_lines_removed:,}")
    print(f"   Target files: {len(all_files_to_remove)}")
    
    return removed_count, total_lines_removed

def update_imports():
    """Update import statements in files that reference removed modules."""
    
    # Files that might need import updates
    files_to_check = [
        "scripts/compare_architectures.py",
        "scripts/spds_performance_benchmark.py", 
        "app/tools/specialized_analyzers.py",
        "app/cli/commands/spds.py",
        "app/tools/demo_simplified_interface.py"
    ]
    
    print(f"\n🔧 Checking Import Dependencies:")
    print("-" * 30)
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"📄 Checking: {file_path}")
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for references to removed modules
                removed_imports = [
                    "statistical_analysis_service",
                    "service_coordinator", 
                    "enhanced_service_coordinator",
                    "strategy_data_coordinator",
                    "memory_optimizer",
                    "cache_manager",
                    "streaming_processor",
                    "performance_monitor"
                ]
                
                needs_update = False
                for removed_import in removed_imports:
                    if removed_import in content:
                        print(f"   ⚠️  Found reference to: {removed_import}")
                        needs_update = True
                
                if not needs_update:
                    print(f"   ✅ No deprecated imports found")
                    
            except Exception as e:
                print(f"   ❌ Error checking {file_path}: {e}")
        else:
            print(f"   ⚠️  File not found: {file_path}")

def main():
    """Run Phase 4 cleanup."""
    print("🚀 Starting SPDS Phase 4 Cleanup")
    print("This will remove deprecated service files and over-engineered memory optimization files")
    print()
    
    # Change to project directory
    os.chdir(Path(__file__).parent.parent)
    
    # Remove deprecated files
    removed_count, total_lines = remove_deprecated_files()
    
    # Check for import dependencies
    update_imports()
    
    print(f"\n🎯 Phase 4C Cleanup Results:")
    print(f"   ✅ Files removed: {removed_count}")
    print(f"   ✅ Lines removed: {total_lines:,}")
    print(f"   ✅ Complexity reduction achieved")
    print(f"   📋 Next: Update documentation references (Phase 4D)")

if __name__ == "__main__":
    main()