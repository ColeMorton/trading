"""
Performance Monitoring Dashboard

This module creates a performance monitoring dashboard using log analysis
to visualize system performance metrics and trends.
"""

import json
import logging
import statistics
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class LogAnalyzer:
    """Analyzes performance logs for dashboard creation."""

    def __init__(self, log_file: Path | None = None):
        """Initialize log analyzer."""
        self.log_file = log_file or Path("logs/performance_metrics.jsonl")
        self.parsed_metrics: list[dict[str, Any]] = []
        self.metric_trends: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

    def load_logs(self, hours_back: int = 24) -> int:
        """Load and parse performance logs."""
        if not self.log_file.exists():
            logger.warning(f"Log file not found: {self.log_file}")
            return 0

        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        parsed_count = 0

        try:
            with open(self.log_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        log_entry = json.loads(line)

                        # Parse timestamp
                        if "timestamp" in log_entry:
                            timestamp = datetime.fromisoformat(log_entry["timestamp"])

                            if timestamp >= cutoff_time:
                                self.parsed_metrics.append(log_entry)
                                self._update_trends(log_entry)
                                parsed_count += 1

                    except (json.JSONDecodeError, ValueError) as e:
                        logger.debug(f"Failed to parse log line: {e}")
                        continue

            logger.info(f"Loaded {parsed_count} performance metrics from logs")
            return parsed_count

        except Exception as e:
            logger.exception(f"Failed to load logs: {e}")
            return 0

    def _update_trends(self, log_entry: dict[str, Any]):
        """Update metric trends from log entry."""
        if log_entry.get("event_type") == "performance_metric":
            metric_name = log_entry.get("name", "unknown")
            metric_value = log_entry.get("value", 0)
            timestamp = log_entry.get("timestamp")

            self.metric_trends[metric_name].append(
                {
                    "timestamp": timestamp,
                    "value": metric_value,
                    "category": log_entry.get("category", "unknown"),
                    "tags": log_entry.get("tags", {}),
                },
            )

    def get_metric_summary(self, metric_name: str, hours: int = 1) -> dict[str, Any]:
        """Get summary statistics for a specific metric."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        metric_data = [
            entry
            for entry in self.metric_trends[metric_name]
            if datetime.fromisoformat(entry["timestamp"]) >= cutoff_time
        ]

        if not metric_data:
            return {"error": f"No data available for metric: {metric_name}"}

        values = [entry["value"] for entry in metric_data]

        summary = {
            "metric_name": metric_name,
            "period_hours": hours,
            "sample_count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "median": statistics.median(values),
            "latest": values[-1] if values else None,
            "first": values[0] if values else None,
            "trend": self._calculate_trend(values),
        }

        if len(values) > 1:
            summary["std"] = statistics.stdev(values)
            summary["percentile_95"] = self._percentile(values, 95)
            summary["percentile_99"] = self._percentile(values, 99)

        return summary

    def get_operation_analysis(self, hours: int = 24) -> dict[str, Any]:
        """Analyze operation performance from logs."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        operations = defaultdict(list)
        alerts = []

        for log_entry in self.parsed_metrics:
            timestamp = datetime.fromisoformat(log_entry["timestamp"])
            if timestamp < cutoff_time:
                continue

            if log_entry.get("event_type") == "performance_metric":
                # Group by operation tag
                tags = log_entry.get("tags", {})
                operation = tags.get("operation", "unknown")

                if operation != "unknown":
                    operations[operation].append(log_entry)

            elif log_entry.get("event_type") == "performance_alert":
                alerts.append(log_entry)

        # Analyze each operation
        operation_analysis = {}
        for operation, metrics in operations.items():
            duration_metrics = [
                m for m in metrics if m.get("name") == "operation_duration_ms"
            ]

            if duration_metrics:
                durations = [m["value"] for m in duration_metrics]

                operation_analysis[operation] = {
                    "total_executions": len(durations),
                    "avg_duration_ms": statistics.mean(durations),
                    "max_duration_ms": max(durations),
                    "min_duration_ms": min(durations),
                    "p95_duration_ms": self._percentile(durations, 95),
                    "error_count": len(
                        [
                            m
                            for m in metrics
                            if "error" in m.get("tags", {}).get("has_errors", "")
                        ],
                    ),
                    "last_execution": max(m["timestamp"] for m in duration_metrics),
                }

        return {
            "period_hours": hours,
            "operations": operation_analysis,
            "total_alerts": len(alerts),
            "alert_summary": self._summarize_alerts(alerts),
        }

    def get_system_health_score(self) -> dict[str, Any]:
        """Calculate overall system health score."""
        # Load recent data
        self.load_logs(hours_back=1)

        health_factors = {}

        # Performance factor (based on operation durations)
        duration_data = self.get_metric_summary("operation_duration_ms", hours=1)
        if "avg" in duration_data:
            # Target: < 2500ms, Good: < 5000ms, Poor: > 10000ms
            avg_duration = duration_data["avg"]
            if avg_duration < 2500:
                performance_score = 100
            elif avg_duration < 5000:
                performance_score = 80 - ((avg_duration - 2500) / 2500) * 30
            elif avg_duration < 10000:
                performance_score = 50 - ((avg_duration - 5000) / 5000) * 30
            else:
                performance_score = max(0, 20 - ((avg_duration - 10000) / 10000) * 20)

            health_factors["performance"] = {
                "score": max(0, min(100, performance_score)),
                "avg_duration_ms": avg_duration,
                "target_ms": 2500,
            }

        # Memory factor
        memory_data = self.get_metric_summary("memory_usage_mb", hours=1)
        if "avg" in memory_data:
            # Target: < 250MB, Good: < 500MB, Poor: > 1000MB
            avg_memory = memory_data["avg"]
            if avg_memory < 250:
                memory_score = 100
            elif avg_memory < 500:
                memory_score = 80 - ((avg_memory - 250) / 250) * 30
            elif avg_memory < 1000:
                memory_score = 50 - ((avg_memory - 500) / 500) * 30
            else:
                memory_score = max(0, 20 - ((avg_memory - 1000) / 1000) * 20)

            health_factors["memory"] = {
                "score": max(0, min(100, memory_score)),
                "avg_usage_mb": avg_memory,
                "target_mb": 250,
            }

        # Cache efficiency factor
        cache_data = self.get_metric_summary("cache_hit_rate", hours=1)
        if "avg" in cache_data:
            cache_hit_rate = cache_data["avg"]
            cache_score = cache_hit_rate * 100  # Convert to percentage

            health_factors["cache"] = {
                "score": max(0, min(100, cache_score)),
                "hit_rate": cache_hit_rate,
                "target_rate": 0.8,
            }

        # Error rate factor
        operation_analysis = self.get_operation_analysis(hours=1)
        total_errors = sum(
            op_data.get("error_count", 0)
            for op_data in operation_analysis.get("operations", {}).values()
        )
        total_executions = sum(
            op_data.get("total_executions", 0)
            for op_data in operation_analysis.get("operations", {}).values()
        )

        if total_executions > 0:
            error_rate = total_errors / total_executions
            error_score = max(0, (1 - error_rate) * 100)

            health_factors["reliability"] = {
                "score": error_score,
                "error_rate": error_rate,
                "target_rate": 0.05,
            }

        # Calculate overall health score
        if health_factors:
            overall_score = statistics.mean(
                [factor["score"] for factor in health_factors.values()],
            )
        else:
            overall_score = 0

        # Determine health status
        if overall_score >= 90:
            status = "excellent"
        elif overall_score >= 75:
            status = "good"
        elif overall_score >= 50:
            status = "fair"
        elif overall_score >= 25:
            status = "poor"
        else:
            status = "critical"

        return {
            "overall_score": overall_score,
            "status": status,
            "factors": health_factors,
            "recommendations": self._get_health_recommendations(health_factors),
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend direction from values."""
        if len(values) < 2:
            return "stable"

        # Simple linear trend
        n = len(values)
        x_values = list(range(n))

        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)

        numerator = sum(
            (x - x_mean) * (y - y_mean) for x, y in zip(x_values, values, strict=False)
        )
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        # Classify trend
        if abs(slope) < 0.01 * y_mean:  # Less than 1% change per unit
            return "stable"
        if slope > 0:
            return "increasing"
        return "decreasing"

    def _percentile(self, values: list[float], percentile: int) -> float:
        """Calculate percentile value."""
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)

        if index.is_integer():
            return sorted_values[int(index)]
        lower = sorted_values[int(index)]
        upper = sorted_values[int(index) + 1]
        return lower + (upper - lower) * (index - int(index))

    def _summarize_alerts(self, alerts: list[dict[str, Any]]) -> dict[str, int]:
        """Summarize alerts by severity."""
        summary: dict[str, int] = defaultdict(int)

        for alert in alerts:
            severity = alert.get("severity", "unknown")
            summary[severity] += 1

        return dict(summary)

    def _get_health_recommendations(self, health_factors: dict[str, Any]) -> list[str]:
        """Get health improvement recommendations."""
        recommendations = []

        for factor_name, factor_data in health_factors.items():
            score = factor_data["score"]

            if factor_name == "performance" and score < 75:
                recommendations.append(
                    "Consider enabling auto-tuning to optimize thread pool sizes",
                )
                recommendations.append(
                    "Review slow operations and enable pre-computation for common queries",
                )

            if factor_name == "memory" and score < 75:
                recommendations.append(
                    "Enable memory optimization features like DataFrame optimization",
                )
                recommendations.append(
                    "Consider reducing cache size or increasing memory cleanup frequency",
                )

            if factor_name == "cache" and score < 75:
                recommendations.append(
                    "Review cache warming strategies to improve hit rates",
                )
                recommendations.append("Increase cache size if memory allows")

            if factor_name == "reliability" and score < 75:
                recommendations.append(
                    "Investigate error patterns and improve error handling",
                )
                recommendations.append(
                    "Enable streaming processing for large file operations",
                )

        return recommendations


class DashboardGenerator:
    """Generates HTML dashboard for performance monitoring."""

    def __init__(self, log_analyzer: LogAnalyzer | None = None):
        """Initialize dashboard generator."""
        self.log_analyzer = log_analyzer or LogAnalyzer()

    def generate_dashboard(self, output_file: Path, hours_back: int = 24) -> str:
        """Generate HTML dashboard."""
        # Load data
        self.log_analyzer.load_logs(hours_back)

        # Get dashboard data
        health_score = self.log_analyzer.get_system_health_score()
        operation_analysis = self.log_analyzer.get_operation_analysis(hours_back)

        # Key metrics
        key_metrics = [
            "operation_duration_ms",
            "memory_usage_mb",
            "cache_hit_rate",
            "cpu_usage_percent",
        ]

        metric_summaries = {}
        for metric in key_metrics:
            metric_summaries[metric] = self.log_analyzer.get_metric_summary(
                metric,
                hours=1,
            )

        # Generate HTML
        html_content = self._generate_html_content(
            health_score,
            operation_analysis,
            metric_summaries,
            hours_back,
        )

        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(html_content)

        logger.info(f"Performance dashboard generated: {output_file}")
        return str(output_file)

    def _generate_html_content(
        self,
        health_score: dict[str, Any],
        operation_analysis: dict[str, Any],
        metric_summaries: dict[str, Any],
        hours_back: int,
    ) -> str:
        """Generate HTML content for dashboard."""

        # Health status styling
        status_colors = {
            "excellent": "#28a745",
            "good": "#6f42c1",
            "fair": "#ffc107",
            "poor": "#fd7e14",
            "critical": "#dc3545",
        }

        status_color = status_colors.get(
            health_score.get("status", "unknown"),
            "#6c757d",
        )

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading System Performance Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            color: #212529;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 0;
            opacity: 0.9;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }}
        .health-card {{
            border-left-color: {status_color};
        }}
        .card h3 {{
            margin: 0 0 15px 0;
            color: #495057;
        }}
        .health-score {{
            font-size: 3em;
            font-weight: bold;
            color: {status_color};
            text-align: center;
            margin: 20px 0;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            background-color: {status_color};
            color: white;
            border-radius: 20px;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.8em;
        }}
        .metric-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .metric-row:last-child {{
            border-bottom: none;
        }}
        .metric-value {{
            font-weight: bold;
            color: #495057;
        }}
        .trend-up {{
            color: #28a745;
        }}
        .trend-down {{
            color: #dc3545;
        }}
        .trend-stable {{
            color: #6c757d;
        }}
        .recommendations {{
            background: #e7f3ff;
            border-left: 4px solid #007bff;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }}
        .recommendations h4 {{
            margin: 0 0 10px 0;
            color: #007bff;
        }}
        .recommendations ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .operations-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .operations-table th,
        .operations-table td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }}
        .operations-table th {{
            background-color: #f8f9fa;
            font-weight: bold;
            color: #495057;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Trading System Performance Dashboard</h1>
        <p>Last {hours_back} hours | Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="dashboard-grid">
        <!-- System Health -->
        <div class="card health-card">
            <h3>System Health</h3>
            <div class="health-score">{health_score.get('overall_score', 0):.0f}</div>
            <div style="text-align: center;">
                <span class="status-badge">{health_score.get('status', 'unknown').upper()}</span>
            </div>
        </div>

        <!-- Performance Metrics -->
        <div class="card">
            <h3>Performance Metrics</h3>
            {self._generate_metrics_html(metric_summaries)}
        </div>

        <!-- Operation Analysis -->
        <div class="card">
            <h3>Operations ({operation_analysis.get('period_hours', 0)}h)</h3>
            <div class="metric-row">
                <span>Total Operations</span>
                <span class="metric-value">{sum(op.get('total_executions', 0) for op in operation_analysis.get('operations', {}).values())}</span>
            </div>
            <div class="metric-row">
                <span>Total Alerts</span>
                <span class="metric-value">{operation_analysis.get('total_alerts', 0)}</span>
            </div>
            {self._generate_operations_table(operation_analysis.get('operations', {}))}
        </div>

        <!-- Health Factors -->
        <div class="card">
            <h3>Health Factors</h3>
            {self._generate_health_factors_html(health_score.get('factors', {}))}
        </div>
    </div>

    <!-- Recommendations -->
    {self._generate_recommendations_html(health_score.get('recommendations', []))}

    <div class="footer">
        <p>Trading System Performance Dashboard - Phase 4 Advanced Optimization</p>
    </div>
</body>
</html>
"""

    def _generate_metrics_html(self, metric_summaries: dict[str, Any]) -> str:
        """Generate HTML for metrics section."""
        html = ""

        for metric_name, summary in metric_summaries.items():
            if "avg" not in summary:
                continue

            # Format metric name
            display_name = metric_name.replace("_", " ").title()

            # Format value based on metric type
            avg_value = summary["avg"]
            if "ms" in metric_name:
                value_str = f"{avg_value:.1f}ms"
            elif "mb" in metric_name:
                value_str = f"{avg_value:.1f}MB"
            elif "rate" in metric_name:
                value_str = f"{avg_value:.1%}"
            elif "percent" in metric_name:
                value_str = f"{avg_value:.1f}%"
            else:
                value_str = f"{avg_value:.2f}"

            # Trend indicator
            trend = summary.get("trend", "stable")
            trend_class = f"trend-{trend.replace('ing', '')}"
            trend_symbol = {"increasing": "↗", "decreasing": "↘", "stable": "→"}.get(
                trend,
                "→",
            )

            html += f"""
            <div class="metric-row">
                <span>{display_name}</span>
                <span class="metric-value {trend_class}">{value_str} {trend_symbol}</span>
            </div>
            """

        return html

    def _generate_operations_table(self, operations: dict[str, Any]) -> str:
        """Generate HTML table for operations."""
        if not operations:
            return "<p>No operation data available</p>"

        html = """
        <table class="operations-table">
            <thead>
                <tr>
                    <th>Operation</th>
                    <th>Executions</th>
                    <th>Avg Duration</th>
                    <th>Errors</th>
                </tr>
            </thead>
            <tbody>
        """

        for operation, data in operations.items():
            html += f"""
            <tr>
                <td>{operation}</td>
                <td>{data.get('total_executions', 0)}</td>
                <td>{data.get('avg_duration_ms', 0):.1f}ms</td>
                <td>{data.get('error_count', 0)}</td>
            </tr>
            """

        html += """
            </tbody>
        </table>
        """

        return html

    def _generate_health_factors_html(self, health_factors: dict[str, Any]) -> str:
        """Generate HTML for health factors."""
        html = ""

        for factor_name, factor_data in health_factors.items():
            score = factor_data.get("score", 0)

            # Color based on score
            if score >= 90:
                color = "#28a745"
            elif score >= 75:
                color = "#6f42c1"
            elif score >= 50:
                color = "#ffc107"
            else:
                color = "#dc3545"

            html += f"""
            <div class="metric-row">
                <span>{factor_name.title()}</span>
                <span class="metric-value" style="color: {color};">{score:.0f}%</span>
            </div>
            """

        return html

    def _generate_recommendations_html(self, recommendations: list[str]) -> str:
        """Generate HTML for recommendations."""
        if not recommendations:
            return ""

        html = """
        <div class="recommendations">
            <h4>🎯 Performance Recommendations</h4>
            <ul>
        """

        for recommendation in recommendations:
            html += f"<li>{recommendation}</li>"

        html += """
            </ul>
        </div>
        """

        return html


# Global dashboard instance
_global_dashboard: DashboardGenerator | None = None


def get_dashboard_generator(
    log_analyzer: LogAnalyzer | None = None,
) -> DashboardGenerator:
    """Get or create global dashboard generator."""
    global _global_dashboard

    if _global_dashboard is None:
        _global_dashboard = DashboardGenerator(log_analyzer)

    return _global_dashboard


def generate_performance_dashboard(
    output_file: Path | None = None,
    hours_back: int = 24,
) -> str:
    """Generate performance dashboard HTML file."""
    if output_file is None:
        output_file = Path("reports/performance_dashboard.html")

    dashboard = get_dashboard_generator()
    return dashboard.generate_dashboard(output_file, hours_back)


def analyze_performance_logs(
    log_file: Path | None = None,
    hours_back: int = 24,
) -> dict[str, Any]:
    """Analyze performance logs and return summary."""
    analyzer = LogAnalyzer(log_file)
    analyzer.load_logs(hours_back)

    return {
        "health_score": analyzer.get_system_health_score(),
        "operation_analysis": analyzer.get_operation_analysis(hours_back),
        "key_metrics": {
            metric: analyzer.get_metric_summary(metric, hours=1)
            for metric in ["operation_duration_ms", "memory_usage_mb", "cache_hit_rate"]
        },
    }
