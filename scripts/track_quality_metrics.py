"""Track code quality metrics over time.

This script collects complexity, maintainability, dead code, and architecture
metrics using radon, vulture, and import-linter. Results are stored in
data/analysis/quality-history.jsonl for tracking trends.

Usage:
    poetry run python scripts/track_quality_metrics.py
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd: str) -> str:
    """Run shell command and return stdout."""
    try:
        result = subprocess.run(
            cmd,
            check=False,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"⚠️  Command timed out: {cmd}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"⚠️  Command failed: {cmd}\n  Error: {e}", file=sys.stderr)
        return ""


def collect_metrics() -> dict:
    """Collect all code quality metrics."""
    print("📊 Collecting code quality metrics...")

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "git_sha": run_command("git rev-parse HEAD").strip(),
        "branch": run_command("git branch --show-current").strip(),
    }

    # Radon complexity - count functions with CC > 20
    print("  → Analyzing complexity (radon cc)...")
    cc_output = run_command("poetry run radon cc app/ --json 2>/dev/null")
    try:
        cc_data = json.loads(cc_output or "{}")
        high_complexity_funcs = [
            f
            for file_funcs in cc_data.values()
            for f in file_funcs
            if isinstance(f, dict) and f.get("complexity", 0) > 20
        ]
        metrics["complexity"] = {
            "high_complexity_functions": len(high_complexity_funcs),
            "total_files_analyzed": len(cc_data),
        }
    except (json.JSONDecodeError, TypeError) as e:
        print(f"  ⚠️  Failed to parse radon cc output: {e}", file=sys.stderr)
        metrics["complexity"] = {"high_complexity_functions": -1, "error": str(e)}

    # Radon maintainability - count files with MI < 20
    print("  → Analyzing maintainability (radon mi)...")
    mi_output = run_command("poetry run radon mi app/ --json 2>/dev/null")
    try:
        mi_data = json.loads(mi_output or "[]")
        low_mi_files = [f for f in mi_data if f.get("mi", 100) < 20]
        metrics["maintainability"] = {
            "low_mi_files": len(low_mi_files),
            "total_files_analyzed": len(mi_data),
        }
    except (json.JSONDecodeError, TypeError) as e:
        print(f"  ⚠️  Failed to parse radon mi output: {e}", file=sys.stderr)
        metrics["maintainability"] = {"low_mi_files": -1, "error": str(e)}

    # Vulture dead code - count instances
    print("  → Detecting dead code (vulture)...")
    vulture_output = run_command(
        "poetry run vulture app/ --min-confidence 80 "
        "--exclude '*/migrations/*,*/tests/*' 2>/dev/null"
    )
    dead_code_count = vulture_output.count("unused")
    metrics["dead_code"] = {
        "instances": dead_code_count,
        "sample": vulture_output.split("\n")[:5] if dead_code_count > 0 else [],
    }

    # Import-linter architecture violations
    print("  → Checking architecture (import-linter)...")
    importlinter_output = run_command("poetry run lint-imports 2>&1")
    # Count "BROKEN" contracts
    broken_contracts = importlinter_output.count("BROKEN")
    metrics["architecture"] = {
        "broken_contracts": broken_contracts,
        "has_violations": broken_contracts > 0,
    }

    return metrics


def save_metrics(metrics: dict) -> None:
    """Save metrics to history file."""
    history_file = Path("data/analysis/quality-history.jsonl")
    history_file.parent.mkdir(parents=True, exist_ok=True)

    with open(history_file, "a") as f:
        f.write(json.dumps(metrics) + "\n")

    print(f"\n✅ Metrics saved to {history_file}")


def display_summary(metrics: dict) -> None:
    """Display metrics summary."""
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 Code Quality Metrics Summary")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Timestamp: {metrics['timestamp']}")
    print(f"Branch: {metrics['branch']}")
    print(f"Commit: {metrics['git_sha'][:8]}")
    print()

    complexity = metrics.get("complexity", {})
    print(
        f"High Complexity Functions (CC > 20): "
        f"{complexity.get('high_complexity_functions', 'N/A')}"
    )

    maintainability = metrics.get("maintainability", {})
    print(
        f"Low Maintainability Files (MI < 20): "
        f"{maintainability.get('low_mi_files', 'N/A')}"
    )

    dead_code = metrics.get("dead_code", {})
    print(f"Dead Code Instances: {dead_code.get('instances', 'N/A')}")

    architecture = metrics.get("architecture", {})
    broken = architecture.get("broken_contracts", "N/A")
    print(f"Broken Architecture Contracts: {broken}")

    print("\n📈 Targets:")
    print("  - High Complexity Functions: < 50")
    print("  - Low Maintainability Files: < 10")
    print("  - Dead Code Instances: 0")
    print("  - Broken Contracts: 0")
    print()


def main():
    """Main entry point."""
    print("🔍 Tracking Code Quality Metrics\n")

    try:
        metrics = collect_metrics()
        save_metrics(metrics)
        display_summary(metrics)

        # Exit with warning if quality issues found
        issues = []
        if metrics.get("complexity", {}).get("high_complexity_functions", 0) > 50:
            issues.append("High complexity")
        if metrics.get("maintainability", {}).get("low_mi_files", 0) > 10:
            issues.append("Low maintainability")
        if metrics.get("dead_code", {}).get("instances", 0) > 0:
            issues.append("Dead code")
        if metrics.get("architecture", {}).get("broken_contracts", 0) > 0:
            issues.append("Architecture violations")

        if issues:
            print(f"⚠️  Quality issues detected: {', '.join(issues)}")
            print("   Run 'make analyze-all' for detailed analysis")
            return 1

        print("✅ All quality metrics within target thresholds!")
        return 0

    except Exception as e:
        print(f"❌ Failed to collect metrics: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
