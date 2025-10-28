#!/usr/bin/env python3
"""
SPDS Dependency Analysis Script

Analyzes dependencies between SPDS components to understand coupling
and identify opportunities for simplification.

Usage:
    python scripts/analyze_spds_dependencies.py
    python scripts/analyze_spds_dependencies.py --output-format json
    python scripts/analyze_spds_dependencies.py --save-graph dependencies.png
"""

import ast
from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.tree import Tree


console = Console()


@dataclass
class DependencyInfo:
    """Information about a dependency relationship."""

    from_file: str
    to_file: str
    import_type: str  # "direct", "from", "relative"
    imported_names: list[str]
    line_number: int


@dataclass
class FileInfo:
    """Information about a file and its dependencies."""

    file_path: str
    imports: list[DependencyInfo]
    imported_by: list[str]
    lines_of_code: int
    complexity_score: float


class SPDSDependencyAnalyzer:
    """Analyzes dependencies in the SPDS codebase."""

    def __init__(self):
        self.project_root = Path.cwd()
        self.spds_files: dict[str, FileInfo] = {}
        self.dependency_graph: dict[str, list[str]] = defaultdict(list)
        self.reverse_dependency_graph: dict[str, list[str]] = defaultdict(list)

    def find_spds_files(self) -> list[Path]:
        """Find all SPDS-related Python files."""
        patterns = [
            "**/*spds*",
            "**/*statistical*",
            "**/*divergence*",
            "**/*analyzer*",
            "**/*parameter*",
            "**/services/*",
            "**/analysis/*",
            "**/models/*statistical*",
            "**/config/*statistical*",
        ]

        files = set()
        for pattern in patterns:
            for path in self.project_root.glob(pattern):
                if path.is_file() and path.suffix == ".py":
                    # Filter out obviously non-SPDS files
                    if any(
                        keyword in path.name.lower()
                        for keyword in [
                            "spds",
                            "statistical",
                            "divergence",
                            "analyzer",
                            "parameter",
                        ]
                    ) or any(
                        keyword in str(path).lower()
                        for keyword in ["services", "analysis", "models", "config"]
                    ):
                        files.add(path)

        return sorted(files)

    def parse_imports(self, file_path: Path) -> list[DependencyInfo]:
        """Parse imports from a Python file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(
                            DependencyInfo(
                                from_file=str(file_path),
                                to_file=alias.name,
                                import_type="direct",
                                imported_names=[alias.name],
                                line_number=node.lineno,
                            )
                        )

                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    imported_names = [alias.name for alias in node.names]

                    imports.append(
                        DependencyInfo(
                            from_file=str(file_path),
                            to_file=module,
                            import_type="from" if node.level == 0 else "relative",
                            imported_names=imported_names,
                            line_number=node.lineno,
                        )
                    )

            return imports

        except Exception as e:
            console.print(f"[red]Error parsing {file_path}: {e}[/red]")
            return []

    def calculate_complexity_score(self, file_path: Path) -> tuple[int, float]:
        """Calculate complexity score for a file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            lines_of_code = len(
                [
                    line
                    for line in lines
                    if line.strip() and not line.strip().startswith("#")
                ]
            )

            # Simple complexity metrics
            complexity_indicators = {
                "class": 2,
                "def": 1,
                "if": 0.5,
                "for": 0.5,
                "while": 0.5,
                "try": 0.5,
                "except": 0.5,
                "async": 1,
                "await": 0.5,
            }

            complexity_score = 0
            for line in lines:
                for indicator, weight in complexity_indicators.items():
                    if indicator in line:
                        complexity_score += weight

            return lines_of_code, complexity_score

        except Exception as e:
            console.print(
                f"[red]Error calculating complexity for {file_path}: {e}[/red]"
            )
            return 0, 0

    def analyze_dependencies(self):
        """Analyze all dependencies in SPDS files."""
        console.print("[bold]🔍 Analyzing SPDS Dependencies[/bold]")
        console.print("-" * 50)

        spds_files = self.find_spds_files()
        console.print(f"Found {len(spds_files)} SPDS-related files")

        # Analyze each file
        for file_path in spds_files:
            console.print(f"[dim]Analyzing: {file_path.name}[/dim]")

            imports = self.parse_imports(file_path)
            lines_of_code, complexity_score = self.calculate_complexity_score(file_path)

            file_info = FileInfo(
                file_path=str(file_path),
                imports=imports,
                imported_by=[],
                lines_of_code=lines_of_code,
                complexity_score=complexity_score,
            )

            self.spds_files[str(file_path)] = file_info

            # Build dependency graph
            for import_info in imports:
                if self.is_spds_related(import_info.to_file):
                    self.dependency_graph[str(file_path)].append(import_info.to_file)
                    self.reverse_dependency_graph[import_info.to_file].append(
                        str(file_path)
                    )

        # Update imported_by information
        for file_path, file_info in self.spds_files.items():
            file_info.imported_by = self.reverse_dependency_graph.get(file_path, [])

        console.print(
            f"[green]✅ Analysis complete: {len(self.spds_files)} files analyzed[/green]"
        )

    def is_spds_related(self, module_name: str) -> bool:
        """Check if a module is SPDS-related."""
        spds_keywords = [
            "spds",
            "statistical",
            "divergence",
            "analyzer",
            "parameter",
            "services",
            "analysis",
            "models",
            "config",
        ]

        return any(keyword in module_name.lower() for keyword in spds_keywords)

    def find_circular_dependencies(self) -> list[list[str]]:
        """Find circular dependencies in the dependency graph."""

        def dfs(node: str, visited: set[str], path: list[str]) -> list[list[str]]:
            if node in visited:
                # Found a cycle
                cycle_start = path.index(node)
                return [path[cycle_start:] + [node]]

            visited.add(node)
            path.append(node)

            cycles = []
            for neighbor in self.dependency_graph.get(node, []):
                if neighbor in self.spds_files:  # Only consider SPDS files
                    cycles.extend(dfs(neighbor, visited.copy(), path.copy()))

            return cycles

        all_cycles = []
        for node in self.dependency_graph:
            if node in self.spds_files:
                cycles = dfs(node, set(), [])
                all_cycles.extend(cycles)

        # Remove duplicates
        unique_cycles = []
        for cycle in all_cycles:
            if cycle not in unique_cycles:
                unique_cycles.append(cycle)

        return unique_cycles

    def calculate_coupling_metrics(self) -> dict[str, dict[str, float]]:
        """Calculate coupling metrics for each file."""
        metrics = {}

        for file_path, file_info in self.spds_files.items():
            file_name = Path(file_path).name

            # Afferent coupling (how many files depend on this one)
            afferent_coupling = len(file_info.imported_by)

            # Efferent coupling (how many files this one depends on)
            efferent_coupling = len(
                [imp for imp in file_info.imports if self.is_spds_related(imp.to_file)]
            )

            # Instability (Ce / (Ca + Ce))
            total_coupling = afferent_coupling + efferent_coupling
            instability = (
                efferent_coupling / total_coupling if total_coupling > 0 else 0
            )

            # Complexity per line
            complexity_per_line = (
                file_info.complexity_score / file_info.lines_of_code
                if file_info.lines_of_code > 0
                else 0
            )

            metrics[file_name] = {
                "afferent_coupling": afferent_coupling,
                "efferent_coupling": efferent_coupling,
                "instability": instability,
                "lines_of_code": file_info.lines_of_code,
                "complexity_score": file_info.complexity_score,
                "complexity_per_line": complexity_per_line,
            }

        return metrics

    def identify_core_components(self) -> list[str]:
        """Identify core components based on coupling metrics."""
        metrics = self.calculate_coupling_metrics()

        # Score components based on:
        # 1. High afferent coupling (many files depend on it)
        # 2. Moderate efferent coupling (not too dependent on others)
        # 3. Reasonable complexity

        scored_components = []
        for file_name, metric in metrics.items():
            # Core component score
            score = (
                metric["afferent_coupling"] * 2
                + min(  # High weight for being depended upon
                    metric["efferent_coupling"], 10
                )
                * 0.5
                + min(  # Moderate weight for dependencies
                    metric["lines_of_code"] / 100, 10
                )
                * 0.3
                + min(metric["complexity_score"] / 10, 10)  # Size factor
                * 0.2  # Complexity factor
            )

            scored_components.append((file_name, score, metric))

        # Sort by score (descending)
        scored_components.sort(key=lambda x: x[1], reverse=True)

        return scored_components

    def display_analysis_results(self):
        """Display comprehensive analysis results."""
        console.print("\n[bold]📊 SPDS Dependency Analysis Results[/bold]")
        console.print("=" * 60)

        # 1. Overall Statistics
        console.print("\n[cyan]📈 Overall Statistics[/cyan]")
        total_files = len(self.spds_files)
        total_dependencies = sum(len(info.imports) for info in self.spds_files.values())
        avg_dependencies = total_dependencies / total_files if total_files > 0 else 0

        console.print(f"Total SPDS files: {total_files}")
        console.print(f"Total dependencies: {total_dependencies}")
        console.print(f"Average dependencies per file: {avg_dependencies:.1f}")

        # 2. Coupling Metrics
        console.print("\n[cyan]🔗 Coupling Metrics[/cyan]")
        metrics = self.calculate_coupling_metrics()

        table = Table(title="Component Coupling Analysis", show_header=True)
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Afferent", style="green", justify="right")
        table.add_column("Efferent", style="yellow", justify="right")
        table.add_column("Instability", style="red", justify="right")
        table.add_column("LOC", style="blue", justify="right")
        table.add_column("Complexity", style="magenta", justify="right")

        for file_name, metric in sorted(
            metrics.items(), key=lambda x: x[1]["afferent_coupling"], reverse=True
        )[:20]:
            table.add_row(
                file_name,
                str(metric["afferent_coupling"]),
                str(metric["efferent_coupling"]),
                f"{metric['instability']:.2f}",
                str(metric["lines_of_code"]),
                f"{metric['complexity_score']:.1f}",
            )

        console.print(table)

        # 3. Core Components Identification
        console.print("\n[cyan]🎯 Core Components (Top 10)[/cyan]")
        core_components = self.identify_core_components()

        core_table = Table(title="Core Components by Importance", show_header=True)
        core_table.add_column("Rank", style="cyan", justify="center")
        core_table.add_column("Component", style="white", no_wrap=True)
        core_table.add_column("Score", style="green", justify="right")
        core_table.add_column("Dependents", style="yellow", justify="right")
        core_table.add_column("Dependencies", style="red", justify="right")

        for i, (file_name, score, metric) in enumerate(core_components[:10], 1):
            core_table.add_row(
                str(i),
                file_name,
                f"{score:.1f}",
                str(metric["afferent_coupling"]),
                str(metric["efferent_coupling"]),
            )

        console.print(core_table)

        # 4. Circular Dependencies
        console.print("\n[cyan]🔄 Circular Dependencies[/cyan]")
        circular_deps = self.find_circular_dependencies()

        if circular_deps:
            console.print(
                f"[red]⚠️  Found {len(circular_deps)} circular dependencies:[/red]"
            )
            for i, cycle in enumerate(circular_deps, 1):
                cycle_display = " → ".join([Path(f).name for f in cycle])
                console.print(f"[red]{i}. {cycle_display}[/red]")
        else:
            console.print("[green]✅ No circular dependencies found[/green]")

        # 5. Dependency Tree for Core Components
        console.print("\n[cyan]🌳 Dependency Tree (Top 5 Core Components)[/cyan]")

        for i, (file_name, score, metric) in enumerate(core_components[:5], 1):
            tree = Tree(f"[bold]{file_name}[/bold] (Score: {score:.1f})")

            # Find the full path for this file
            full_path = None
            for path in self.spds_files.keys():
                if Path(path).name == file_name:
                    full_path = path
                    break

            if full_path:
                file_info = self.spds_files[full_path]

                # Add dependencies
                deps_branch = tree.add("Dependencies")
                for import_info in file_info.imports[:5]:  # Show first 5
                    if self.is_spds_related(import_info.to_file):
                        deps_branch.add(
                            f"{import_info.to_file} ({import_info.import_type})"
                        )

                # Add dependents
                dependents_branch = tree.add("Dependents")
                for dependent in file_info.imported_by[:5]:  # Show first 5
                    dependents_branch.add(Path(dependent).name)

            console.print(tree)
            console.print()

        # 6. Recommendations
        console.print("[cyan]💡 Consolidation Recommendations[/cyan]")

        # High coupling files that could be consolidated
        high_coupling_files = [
            (name, metric)
            for name, metric in metrics.items()
            if metric["efferent_coupling"] > 5 and metric["lines_of_code"] < 200
        ]

        if high_coupling_files:
            console.print(
                "[yellow]📦 Files with high coupling that could be consolidated:[/yellow]"
            )
            for name, metric in high_coupling_files[:5]:
                console.print(
                    f"[yellow]  • {name} (efferent: {metric['efferent_coupling']}, LOC: {metric['lines_of_code']})[/yellow]"
                )

        # Low coupling files that might be candidates for removal
        low_coupling_files = [
            (name, metric)
            for name, metric in metrics.items()
            if metric["afferent_coupling"] == 0 and metric["efferent_coupling"] <= 2
        ]

        if low_coupling_files:
            console.print(
                "[red]🗑️  Files with low coupling that might be removed:[/red]"
            )
            for name, metric in low_coupling_files[:5]:
                console.print(
                    f"[red]  • {name} (afferent: {metric['afferent_coupling']}, efferent: {metric['efferent_coupling']})[/red]"
                )

        console.print("\n[green]✅ Dependency analysis complete![/green]")

    def save_results(
        self, output_format: str = "json", filename: str = "spds_dependencies.json"
    ):
        """Save analysis results to file."""
        results = {
            "total_files": len(self.spds_files),
            "coupling_metrics": self.calculate_coupling_metrics(),
            "core_components": [
                {"name": name, "score": score, "metrics": metric}
                for name, score, metric in self.identify_core_components()
            ],
            "circular_dependencies": self.find_circular_dependencies(),
            "dependency_graph": {
                Path(k).name: [Path(v).name for v in vs]
                for k, vs in self.dependency_graph.items()
            },
        }

        if output_format == "json":
            with open(filename, "w") as f:
                json.dump(results, f, indent=2)
            console.print(f"[green]💾 Results saved to {filename}[/green]")


def main():
    """Main analysis execution."""
    import argparse

    parser = argparse.ArgumentParser(description="SPDS Dependency Analysis")
    parser.add_argument(
        "--output-format",
        choices=["json", "console"],
        default="console",
        help="Output format",
    )
    parser.add_argument("--save-results", type=str, help="Save results to file")

    args = parser.parse_args()

    analyzer = SPDSDependencyAnalyzer()

    try:
        analyzer.analyze_dependencies()
        analyzer.display_analysis_results()

        if args.save_results:
            analyzer.save_results(args.output_format, args.save_results)

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Analysis interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Analysis failed: {e}[/red]")
        raise


if __name__ == "__main__":
    main()
