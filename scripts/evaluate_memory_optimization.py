#!/usr/bin/env python3
"""
Evaluate Memory Optimization Components

Analyzes the memory optimization files to determine if the complexity
is justified by the benefits.
"""

import ast
import json
import time
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.tree import Tree


console = Console()


class MemoryOptimizationEvaluator:
    """Evaluates the memory optimization components."""

    def __init__(self):
        self.processing_dir = Path("app/tools/processing")
        self.memory_files = []
        self.analysis_results = {}

    def analyze_memory_files(self):
        """Analyze all memory optimization files."""
        console.print("[bold]🔍 Analyzing Memory Optimization Components[/bold]")
        console.print("-" * 60)

        # Find all memory optimization files
        memory_patterns = [
            "*memory*",
            "*cache*",
            "*stream*",
            "*batch*",
            "*parallel*",
            "*performance*",
            "*mmap*",
            "*optimizer*",
        ]

        for pattern in memory_patterns:
            for file_path in self.processing_dir.glob(pattern):
                if file_path.is_file() and file_path.suffix == ".py":
                    self.memory_files.append(file_path)

        console.print(f"Found {len(self.memory_files)} memory optimization files")

        # Analyze each file
        for file_path in self.memory_files:
            self.analyze_file(file_path)

        # Display results
        self.display_analysis()

        # Generate recommendations
        self.generate_recommendations()

    def analyze_file(self, file_path: Path):
        """Analyze a single memory optimization file."""
        try:
            with open(file_path) as f:
                content = f.read()

            # Parse the file
            tree = ast.parse(content)

            # Analyze the file
            analysis = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "lines_of_code": len(content.splitlines()),
                "classes": [],
                "functions": [],
                "imports": [],
                "complexity_score": 0,
                "dependencies": [],
                "usage_patterns": [],
            }

            # Extract information from AST
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis["classes"].append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    analysis["functions"].append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append(alias.name)
                        if alias.name not in analysis["dependencies"]:
                            analysis["dependencies"].append(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    analysis["imports"].append(node.module)
                    if node.module not in analysis["dependencies"]:
                        analysis["dependencies"].append(node.module)

            # Calculate complexity score
            analysis["complexity_score"] = (
                len(analysis["classes"]) * 3
                + len(analysis["functions"]) * 1
                + len(analysis["imports"]) * 0.5
                + analysis["lines_of_code"] * 0.01
            )

            # Analyze usage patterns
            analysis["usage_patterns"] = self.analyze_usage_patterns(content)

            self.analysis_results[file_path.name] = analysis

        except Exception as e:
            console.print(f"[red]Error analyzing {file_path}: {e}[/red]")

    def analyze_usage_patterns(self, content: str) -> list[str]:
        """Analyze usage patterns in the code."""
        patterns = []

        # Look for performance-related patterns
        performance_keywords = [
            "cache",
            "pool",
            "memory",
            "gc",
            "optimize",
            "profile",
            "benchmark",
            "performance",
            "efficiency",
            "speed",
        ]

        for keyword in performance_keywords:
            if keyword in content.lower():
                patterns.append(f"Uses {keyword}")

        # Look for complexity patterns
        if "class" in content and "def __init__" in content:
            patterns.append("Object-oriented design")

        if "async def" in content:
            patterns.append("Async operations")

        if "with" in content:
            patterns.append("Context managers")

        return patterns

    def display_analysis(self):
        """Display analysis results."""
        console.print("\n[bold]📊 Memory Optimization File Analysis[/bold]")

        # Create analysis table
        table = Table(title="Memory Optimization Components", show_header=True)
        table.add_column("File", style="cyan", no_wrap=True)
        table.add_column("LOC", style="yellow", justify="right")
        table.add_column("Classes", style="green", justify="right")
        table.add_column("Functions", style="blue", justify="right")
        table.add_column("Complexity", style="red", justify="right")
        table.add_column("Main Purpose", style="white")

        # Sort by complexity
        sorted_files = sorted(
            self.analysis_results.items(),
            key=lambda x: x[1]["complexity_score"],
            reverse=True,
        )

        for file_name, analysis in sorted_files:
            main_purpose = self.infer_main_purpose(file_name, analysis)

            table.add_row(
                file_name,
                str(analysis["lines_of_code"]),
                str(len(analysis["classes"])),
                str(len(analysis["functions"])),
                f"{analysis['complexity_score']:.1f}",
                main_purpose,
            )

        console.print(table)

        # Show total statistics
        total_loc = sum(a["lines_of_code"] for a in self.analysis_results.values())
        total_classes = sum(len(a["classes"]) for a in self.analysis_results.values())
        total_functions = sum(
            len(a["functions"]) for a in self.analysis_results.values()
        )
        total_complexity = sum(
            a["complexity_score"] for a in self.analysis_results.values()
        )

        console.print("\n[bold]📈 Total Statistics[/bold]")
        console.print(f"Total files: {len(self.analysis_results)}")
        console.print(f"Total lines of code: {total_loc:,}")
        console.print(f"Total classes: {total_classes}")
        console.print(f"Total functions: {total_functions}")
        console.print(f"Total complexity score: {total_complexity:.1f}")

        # Show dependency analysis
        self.show_dependency_analysis()

    def infer_main_purpose(self, file_name: str, analysis: dict) -> str:
        """Infer the main purpose of a memory optimization file."""
        if "memory_optimizer" in file_name:
            return "Object pooling & GC management"
        if "cache" in file_name:
            return "Caching mechanism"
        if "stream" in file_name:
            return "Streaming data processing"
        if "batch" in file_name:
            return "Batch processing"
        if "parallel" in file_name:
            return "Parallel execution"
        if "performance" in file_name:
            return "Performance monitoring"
        if "mmap" in file_name:
            return "Memory-mapped file access"
        if "data_converter" in file_name:
            return "Data format conversion"
        if "auto_tuner" in file_name:
            return "Automatic performance tuning"
        # Try to infer from classes and functions
        classes = analysis.get("classes", [])
        analysis.get("functions", [])

        if any("Cache" in c for c in classes):
            return "Caching"
        if any("Pool" in c for c in classes):
            return "Object pooling"
        if any("Stream" in c for c in classes):
            return "Streaming"
        if any("Batch" in c for c in classes):
            return "Batch processing"
        return "General optimization"

    def show_dependency_analysis(self):
        """Show dependency analysis."""
        console.print("\n[bold]🔗 Dependency Analysis[/bold]")

        # Create dependency tree
        tree = Tree("Memory Optimization Dependencies")

        # Common dependencies
        all_deps = set()
        for analysis in self.analysis_results.values():
            all_deps.update(analysis["dependencies"])

        # Categorize dependencies
        standard_libs = set()
        third_party = set()
        internal = set()

        for dep in all_deps:
            if dep in [
                "os",
                "sys",
                "time",
                "logging",
                "pathlib",
                "collections",
                "contextlib",
                "gc",
                "weakref",
            ]:
                standard_libs.add(dep)
            elif dep in ["pandas", "numpy", "polars", "psutil"]:
                third_party.add(dep)
            else:
                internal.add(dep)

        if standard_libs:
            std_branch = tree.add("Standard Library")
            for lib in sorted(standard_libs):
                std_branch.add(lib)

        if third_party:
            third_branch = tree.add("Third Party")
            for lib in sorted(third_party):
                third_branch.add(lib)

        if internal:
            internal_branch = tree.add("Internal")
            for lib in sorted(internal):
                internal_branch.add(lib)

        console.print(tree)

    def generate_recommendations(self):
        """Generate recommendations based on analysis."""
        console.print("\n[bold]💡 Recommendations[/bold]")

        total_loc = sum(a["lines_of_code"] for a in self.analysis_results.values())
        total_complexity = sum(
            a["complexity_score"] for a in self.analysis_results.values()
        )

        # Categorize files by importance
        high_complexity = [
            f for f, a in self.analysis_results.items() if a["complexity_score"] > 50
        ]
        medium_complexity = [
            f
            for f, a in self.analysis_results.items()
            if 20 <= a["complexity_score"] <= 50
        ]
        low_complexity = [
            f for f, a in self.analysis_results.items() if a["complexity_score"] < 20
        ]

        console.print("📊 **Complexity Analysis**:")
        console.print(
            f"  • High complexity ({len(high_complexity)} files): {', '.join(high_complexity)}"
        )
        console.print(
            f"  • Medium complexity ({len(medium_complexity)} files): {', '.join(medium_complexity)}"
        )
        console.print(
            f"  • Low complexity ({len(low_complexity)} files): {', '.join(low_complexity)}"
        )

        # Generate specific recommendations
        recommendations = []

        if total_loc > 2000:
            recommendations.append(
                "🔴 **High Complexity**: 2000+ lines of code for memory optimization"
            )

        if len(self.analysis_results) > 8:
            recommendations.append(
                "🟡 **File Proliferation**: 8+ files for memory optimization"
            )

        if len(high_complexity) > 3:
            recommendations.append(
                "🟠 **Complex Components**: Multiple high-complexity files"
            )

        # Core vs peripheral analysis
        core_files = [
            "memory_optimizer.py",
            "cache_manager.py",
            "streaming_processor.py",
        ]
        peripheral_files = [f for f in self.analysis_results if f not in core_files]

        if len(peripheral_files) > 5:
            recommendations.append(
                "🟡 **Peripheral Files**: Consider consolidating auxiliary components"
            )

        # Consolidation recommendations
        console.print("\n📋 **Consolidation Recommendations**:")

        if len(self.analysis_results) > 6:
            console.print(
                "1. **Reduce File Count**: Consider consolidating to 3-4 core files:"
            )
            console.print(
                "   • `memory_manager.py` - Combines optimizer + cache + monitor"
            )
            console.print(
                "   • `stream_processor.py` - Combines streaming + batch processing"
            )
            console.print("   • `performance_tools.py` - Combines monitoring + tuning")

        if total_complexity > 200:
            console.print(
                "2. **Simplify Implementation**: Consider using established libraries:"
            )
            console.print("   • Use `functools.lru_cache` instead of custom caching")
            console.print(
                "   • Use `concurrent.futures` instead of custom parallel processing"
            )
            console.print("   • Use `pandas` chunking instead of custom streaming")

        # ROI analysis
        console.print("\n💰 **Return on Investment Analysis**:")
        console.print("Current investment:")
        console.print(f"  • {len(self.analysis_results)} files to maintain")
        console.print(f"  • {total_loc:,} lines of code")
        console.print(f"  • {total_complexity:.1f} complexity points")

        console.print("\nClaimed benefit:")
        console.print("  • 84.9% memory reduction")
        console.print("  • Question: Is this benefit realized in practice?")
        console.print("  • Question: Does it justify the maintenance cost?")

        # Final recommendation
        if total_complexity > 300 or len(self.analysis_results) > 10:
            console.print("\n🎯 **Final Recommendation**: **CONSOLIDATE**")
            console.print(
                "The memory optimization system is over-engineered for statistical analysis."
            )
            console.print(
                "Recommend reducing to 2-3 core files with established libraries."
            )
        elif total_complexity > 150 or len(self.analysis_results) > 6:
            console.print("\n🎯 **Final Recommendation**: **SIMPLIFY**")
            console.print("The memory optimization system needs simplification.")
            console.print("Consider consolidating peripheral components.")
        else:
            console.print("\n🎯 **Final Recommendation**: **ACCEPTABLE**")
            console.print("The memory optimization system is at reasonable complexity.")

        # Save analysis results
        self.save_analysis()

    def save_analysis(self):
        """Save analysis results to file."""
        results_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_files": len(self.analysis_results),
                "total_lines": sum(
                    a["lines_of_code"] for a in self.analysis_results.values()
                ),
                "total_classes": sum(
                    len(a["classes"]) for a in self.analysis_results.values()
                ),
                "total_functions": sum(
                    len(a["functions"]) for a in self.analysis_results.values()
                ),
                "total_complexity": sum(
                    a["complexity_score"] for a in self.analysis_results.values()
                ),
            },
            "file_analysis": self.analysis_results,
            "recommendations": {
                "complexity_level": (
                    "HIGH" if len(self.analysis_results) > 8 else "MEDIUM"
                ),
                "consolidation_needed": len(self.analysis_results) > 6,
                "target_file_count": 3 if len(self.analysis_results) > 8 else 4,
                "estimated_loc_reduction": (
                    "50-70%" if len(self.analysis_results) > 8 else "30-50%"
                ),
            },
        }

        with open("memory_optimization_analysis.json", "w") as f:
            json.dump(results_data, f, indent=2)

        console.print(
            "\n[green]💾 Analysis saved to: memory_optimization_analysis.json[/green]"
        )


def main():
    """Run memory optimization evaluation."""
    evaluator = MemoryOptimizationEvaluator()
    evaluator.analyze_memory_files()


if __name__ == "__main__":
    main()
