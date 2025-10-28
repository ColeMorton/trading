"""
SPDS Export Service - Simplified Export System

Consolidates all SPDS export functionality into a single, unified service.
Replaces multiple export services with a simple, comprehensive exporter.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .models.spds_models import AnalysisResult, BatchAnalysisResult, SPDSConfig


class SPDSExporter:
    """
    Simplified SPDS export service.

    Handles all export formats and destinations in a single, cohesive service.
    """

    def __init__(self, config: SPDSConfig):
        """Initialize the SPDS exporter."""
        self.config = config
        self.export_dir = Path(config.export_directory)
        self.export_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for different export types
        self.analysis_dir = self.export_dir / "analysis"
        self.backtesting_dir = self.export_dir / "backtesting"
        self.reports_dir = self.export_dir / "reports"

        for directory in [self.analysis_dir, self.backtesting_dir, self.reports_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    async def export_analysis_results(
        self,
        results: dict[str, AnalysisResult],
        filename_prefix: str = "analysis",
    ) -> dict[str, str]:
        """
        Export analysis results in all supported formats.

        Args:
            results: Dictionary of analysis results
            filename_prefix: Prefix for export filenames

        Returns:
            Dictionary mapping format to exported file path
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{filename_prefix}_{timestamp}"

        exported_files = {}

        # Export JSON format
        json_file = await self._export_json(results, base_filename)
        exported_files["json"] = str(json_file)

        # Export CSV format
        csv_file = await self._export_csv(results, base_filename)
        exported_files["csv"] = str(csv_file)

        # Export Markdown report
        markdown_file = await self._export_markdown(results, base_filename)
        exported_files["markdown"] = str(markdown_file)

        # Export backtesting parameters
        backtesting_file = await self._export_backtesting_parameters(
            results,
            base_filename,
        )
        exported_files["backtesting"] = str(backtesting_file)

        # Export Excel format (comprehensive)
        excel_file = await self._export_excel(results, base_filename)
        exported_files["excel"] = str(excel_file)

        return exported_files

    async def export_batch_results(
        self,
        batch_result: BatchAnalysisResult,
    ) -> dict[str, str]:
        """Export batch analysis results."""
        filename_prefix = f"batch_{batch_result.request.analysis_type}"

        # Export individual results
        exported_files = await self.export_analysis_results(
            batch_result.results,
            filename_prefix,
        )

        # Export batch summary
        summary_file = await self._export_batch_summary(batch_result, filename_prefix)
        exported_files["batch_summary"] = str(summary_file)

        return exported_files

    async def _export_json(
        self,
        results: dict[str, AnalysisResult],
        base_filename: str,
    ) -> Path:
        """Export results in JSON format."""
        json_file = self.analysis_dir / f"{base_filename}.json"

        # Convert results to serializable format
        serializable_results = {}
        for key, result in results.items():
            serializable_results[key] = result.to_dict()

        # Add metadata
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "total_results": len(results),
                "config_version": self.config.to_dict(),
                "export_format": "json",
            },
            "results": serializable_results,
        }

        with open(json_file, "w") as f:
            json.dump(export_data, f, indent=2)

        return json_file

    async def _export_csv(
        self,
        results: dict[str, AnalysisResult],
        base_filename: str,
    ) -> Path:
        """Export results in CSV format."""
        csv_file = self.analysis_dir / f"{base_filename}.csv"

        # Prepare data for CSV
        rows = []
        for result in results.values():
            row = {
                "position_uuid": result.position_uuid,
                "strategy_name": result.strategy_name,
                "ticker": result.ticker,
                "exit_signal": result.exit_signal.signal_type.value,
                "exit_confidence": result.exit_signal.confidence,
                "recommended_action": result.exit_signal.recommended_action,
                "risk_level": result.exit_signal.risk_level,
                "overall_confidence": result.confidence_level,
                "analysis_timestamp": result.analysis_timestamp,
                # Statistical metrics
                "win_rate": result.statistical_metrics.get("win_rate", 0.0),
                "total_return": result.statistical_metrics.get("total_return", 0.0),
                "total_trades": result.statistical_metrics.get("total_trades", 0),
                "sharpe_ratio": result.statistical_metrics.get("sharpe_ratio", 0.0),
                "max_drawdown": result.statistical_metrics.get("max_drawdown", 0.0),
                "unrealized_pnl": result.statistical_metrics.get("unrealized_pnl", 0.0),
                # Component scores
                "risk_score": result.component_scores.get("risk_score", 0.0),
                "momentum_score": result.component_scores.get("momentum_score", 0.0),
                "trend_score": result.component_scores.get("trend_score", 0.0),
                "overall_score": result.component_scores.get("overall_score", 0.0),
                # Divergence metrics
                "z_score_return": result.divergence_metrics.get("z_score_return", 0.0),
                "percentile_return": result.divergence_metrics.get(
                    "percentile_return",
                    0.0,
                ),
                "outlier_score": result.divergence_metrics.get("outlier_score", 0.0),
                # Metadata
                "data_sources": ",".join(
                    [k for k, v in result.data_sources_used.items() if v],
                ),
                "warnings_count": len(result.warnings),
                "execution_time_ms": result.execution_time_ms or 0.0,
            }
            rows.append(row)

        # Write CSV file
        if rows:
            df = pd.DataFrame(rows)
            df.to_csv(csv_file, index=False)

        return csv_file

    async def _export_markdown(
        self,
        results: dict[str, AnalysisResult],
        base_filename: str,
    ) -> Path:
        """Export results in Markdown format."""
        markdown_file = self.reports_dir / f"{base_filename}.md"

        # Generate markdown content
        lines = []
        lines.append("# SPDS Analysis Report")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Total Results**: {len(results)}")
        lines.append("")

        # Summary statistics
        signal_counts: dict[str, int] = {}
        total_confidence = 0
        for result in results.values():
            signal_type = result.exit_signal.signal_type.value
            signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1
            total_confidence += result.confidence_level

        avg_confidence = total_confidence / len(results) if results else 0

        lines.append("## Summary")
        lines.append(f"- **Average Confidence**: {avg_confidence:.1f}%")
        lines.append("- **Signal Distribution**:")
        for signal_type, count in signal_counts.items():
            percentage = (count / len(results)) * 100 if results else 0
            lines.append(f"  - {signal_type}: {count} ({percentage:.1f}%)")
        lines.append("")

        # Individual results
        lines.append("## Individual Results")
        lines.append("")

        # Sort results by confidence (descending)
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1].exit_signal.confidence,
            reverse=True,
        )

        for position_uuid, result in sorted_results:
            lines.append(f"### {result.strategy_name} ({result.ticker})")
            lines.append(f"**Position UUID**: `{position_uuid}`")
            lines.append(f"**Exit Signal**: {result.exit_signal.signal_type.value}")
            lines.append(f"**Confidence**: {result.exit_signal.confidence:.1f}%")
            lines.append(f"**Risk Level**: {result.exit_signal.risk_level}")
            lines.append(
                f"**Recommended Action**: {result.exit_signal.recommended_action}",
            )
            lines.append("")
            lines.append(f"**Reasoning**: {result.exit_signal.reasoning}")
            lines.append("")

            # Key metrics
            lines.append("**Key Metrics**:")
            lines.append(
                f"- Win Rate: {result.statistical_metrics.get('win_rate', 0.0):.1%}",
            )
            lines.append(
                f"- Total Return: {result.statistical_metrics.get('total_return', 0.0):.2%}",
            )
            lines.append(
                f"- Sharpe Ratio: {result.statistical_metrics.get('sharpe_ratio', 0.0):.2f}",
            )
            lines.append(
                f"- Max Drawdown: {result.statistical_metrics.get('max_drawdown', 0.0):.1%}",
            )
            lines.append(
                f"- Total Trades: {result.statistical_metrics.get('total_trades', 0)}",
            )
            lines.append("")

            # Component scores
            lines.append("**Component Scores**:")
            for score_name, score_value in result.component_scores.items():
                if score_name != "volatility_regime":
                    lines.append(
                        f"- {score_name.replace('_', ' ').title()}: {score_value:.1f}",
                    )
            lines.append("")

            # Warnings
            if result.warnings:
                lines.append("**Warnings**:")
                for warning in result.warnings:
                    lines.append(f"- {warning}")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Write markdown file
        with open(markdown_file, "w") as f:
            f.write("\n".join(lines))

        return markdown_file

    async def _export_backtesting_parameters(
        self,
        results: dict[str, AnalysisResult],
        base_filename: str,
    ) -> Path:
        """Export backtesting parameters."""
        backtesting_file = self.backtesting_dir / f"{base_filename}_parameters.json"

        # Extract backtesting parameters from results
        backtesting_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "total_strategies": len(results),
                "config": self.config.to_dict(),
            },
            "parameters": {},
        }

        for position_uuid, result in results.items():
            # Extract strategy parameters
            strategy_params = {
                "ticker": result.ticker,
                "strategy_name": result.strategy_name,
                "position_uuid": position_uuid,
                # Exit thresholds
                "exit_immediately_threshold": self.config.percentile_thresholds[
                    "exit_immediately"
                ],
                "exit_soon_threshold": self.config.percentile_thresholds["exit_soon"],
                # Risk parameters
                "max_drawdown_threshold": self.config.max_drawdown_threshold,
                "min_win_rate": self.config.min_win_rate,
                "min_trades": self.config.min_trades_threshold,
                # Statistical parameters
                "z_score_threshold": self.config.z_score_threshold,
                "convergence_threshold": self.config.convergence_threshold,
                # Current analysis results
                "current_exit_signal": result.exit_signal.signal_type.value,
                "current_confidence": result.exit_signal.confidence,
                "current_risk_level": result.exit_signal.risk_level,
                # Performance metrics
                "historical_win_rate": result.statistical_metrics.get("win_rate", 0.0),
                "historical_return": result.statistical_metrics.get(
                    "total_return",
                    0.0,
                ),
                "historical_sharpe": result.statistical_metrics.get(
                    "sharpe_ratio",
                    0.0,
                ),
                "historical_drawdown": result.statistical_metrics.get(
                    "max_drawdown",
                    0.0,
                ),
                # Component weights (for backtesting)
                "risk_weight": 0.25,
                "momentum_weight": 0.20,
                "trend_weight": 0.20,
                "risk_adjusted_weight": 0.15,
                "mean_reversion_weight": 0.10,
                "volume_weight": 0.10,
            }

            backtesting_data["parameters"][position_uuid] = strategy_params

        with open(backtesting_file, "w") as f:
            json.dump(backtesting_data, f, indent=2)

        return backtesting_file

    async def _export_excel(
        self,
        results: dict[str, AnalysisResult],
        base_filename: str,
    ) -> Path:
        """Export results in Excel format with multiple sheets."""
        excel_file = self.analysis_dir / f"{base_filename}.xlsx"

        try:
            with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
                # Summary sheet
                summary_data = self._create_summary_data(results)
                summary_df = pd.DataFrame([summary_data])
                summary_df.to_excel(writer, sheet_name="Summary", index=False)

                # Main results sheet
                main_data = []
                for position_uuid, result in results.items():
                    row = {
                        "Position_UUID": position_uuid,
                        "Strategy_Name": result.strategy_name,
                        "Ticker": result.ticker,
                        "Exit_Signal": result.exit_signal.signal_type.value,
                        "Exit_Confidence": result.exit_signal.confidence,
                        "Risk_Level": result.exit_signal.risk_level,
                        "Overall_Confidence": result.confidence_level,
                        "Win_Rate": result.statistical_metrics.get("win_rate", 0.0),
                        "Total_Return": result.statistical_metrics.get(
                            "total_return",
                            0.0,
                        ),
                        "Sharpe_Ratio": result.statistical_metrics.get(
                            "sharpe_ratio",
                            0.0,
                        ),
                        "Max_Drawdown": result.statistical_metrics.get(
                            "max_drawdown",
                            0.0,
                        ),
                        "Total_Trades": result.statistical_metrics.get(
                            "total_trades",
                            0,
                        ),
                        "Risk_Score": result.component_scores.get("risk_score", 0.0),
                        "Momentum_Score": result.component_scores.get(
                            "momentum_score",
                            0.0,
                        ),
                        "Trend_Score": result.component_scores.get("trend_score", 0.0),
                        "Overall_Score": result.component_scores.get(
                            "overall_score",
                            0.0,
                        ),
                        "Outlier_Score": result.divergence_metrics.get(
                            "outlier_score",
                            0.0,
                        ),
                        "Percentile_Return": result.divergence_metrics.get(
                            "percentile_return",
                            0.0,
                        ),
                    }
                    main_data.append(row)

                main_df = pd.DataFrame(main_data)
                main_df.to_excel(writer, sheet_name="Results", index=False)

                # Component scores sheet
                component_data = []
                for position_uuid, result in results.items():
                    for score_name, score_value in result.component_scores.items():
                        component_data.append(
                            {
                                "Position_UUID": position_uuid,
                                "Component": score_name,
                                "Score": score_value,
                            },
                        )

                component_df = pd.DataFrame(component_data)
                component_df.to_excel(
                    writer,
                    sheet_name="Component_Scores",
                    index=False,
                )

                # Warnings sheet
                warnings_data = []
                for position_uuid, result in results.items():
                    for warning in result.warnings:
                        warnings_data.append(
                            {"Position_UUID": position_uuid, "Warning": warning},
                        )

                if warnings_data:
                    warnings_df = pd.DataFrame(warnings_data)
                    warnings_df.to_excel(writer, sheet_name="Warnings", index=False)

        except ImportError:
            # Fallback to CSV if openpyxl not available
            return await self._export_csv(results, base_filename)

        return excel_file

    async def _export_batch_summary(
        self,
        batch_result: BatchAnalysisResult,
        base_filename: str,
    ) -> Path:
        """Export batch analysis summary."""
        summary_file = self.reports_dir / f"{base_filename}_summary.json"

        summary_data = {
            "batch_metadata": {
                "analysis_type": batch_result.request.analysis_type,
                "total_parameters": len(batch_result.request.parameters),
                "execution_time_seconds": batch_result.execution_time_seconds,
                "export_timestamp": datetime.now().isoformat(),
            },
            "summary_statistics": batch_result.summary,
            "errors": batch_result.errors,
            "warnings": batch_result.warnings,
            "request_details": {
                "parameters": batch_result.request.parameters,
                "config": batch_result.request.config.to_dict(),
                "parallel_processing": batch_result.request.parallel_processing,
            },
        }

        with open(summary_file, "w") as f:
            json.dump(summary_data, f, indent=2)

        return summary_file

    def _create_summary_data(
        self,
        results: dict[str, AnalysisResult],
    ) -> dict[str, Any]:
        """Create summary data for results."""
        if not results:
            return {"total_results": 0}

        # Signal distribution
        signal_counts: dict[str, int] = {}
        confidence_sum = 0

        for result in results.values():
            signal_type = result.exit_signal.signal_type.value
            signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1
            confidence_sum += result.confidence_level

        # Performance metrics
        returns = [
            r.statistical_metrics.get("total_return", 0.0) for r in results.values()
        ]
        win_rates = [
            r.statistical_metrics.get("win_rate", 0.0) for r in results.values()
        ]

        return {
            "total_results": len(results),
            "average_confidence": confidence_sum / len(results),
            "signal_distribution": signal_counts,
            "average_return": sum(returns) / len(returns) if returns else 0.0,
            "average_win_rate": sum(win_rates) / len(win_rates) if win_rates else 0.0,
            "high_risk_positions": len(
                [r for r in results.values() if r.exit_signal.risk_level == "HIGH"],
            ),
            "exit_signals": len(
                [
                    r
                    for r in results.values()
                    if r.exit_signal.signal_type.value
                    in ["EXIT_SOON", "EXIT_IMMEDIATELY"]
                ],
            ),
            "export_timestamp": datetime.now().isoformat(),
        }

    def get_export_directory(self) -> Path:
        """Get the export directory path."""
        return self.export_dir

    def clean_old_exports(self, days_old: int = 30):
        """Clean export files older than specified days."""
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)

        for export_dir in [self.analysis_dir, self.backtesting_dir, self.reports_dir]:
            for file_path in export_dir.glob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()

    def get_export_summary(self) -> dict[str, Any]:
        """Get summary of export directory contents."""
        return {
            "export_directory": str(self.export_dir),
            "subdirectories": {
                "analysis": str(self.analysis_dir),
                "backtesting": str(self.backtesting_dir),
                "reports": str(self.reports_dir),
            },
            "file_counts": {
                "analysis": len(list(self.analysis_dir.glob("*"))),
                "backtesting": len(list(self.backtesting_dir.glob("*"))),
                "reports": len(list(self.reports_dir.glob("*"))),
            },
            "total_files": len(list(self.export_dir.rglob("*"))),
        }


# Convenience functions
async def export_results(
    results: dict[str, AnalysisResult],
    config: SPDSConfig,
    filename_prefix: str = "analysis",
) -> dict[str, str]:
    """Convenience function to export analysis results."""
    exporter = SPDSExporter(config)
    return await exporter.export_analysis_results(results, filename_prefix)


async def export_batch_results(batch_result: BatchAnalysisResult) -> dict[str, str]:
    """Convenience function to export batch analysis results."""
    exporter = SPDSExporter(batch_result.request.config)
    return await exporter.export_batch_results(batch_result)


# Export the main classes and functions
__all__ = ["SPDSExporter", "export_batch_results", "export_results"]
