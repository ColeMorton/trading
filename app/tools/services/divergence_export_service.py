"""
Divergence Export Service

Exports statistical analysis results in multiple formats (CSV, JSON, Markdown)
with comprehensive metadata and integration with existing export infrastructure.
"""

import asyncio
import csv
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from ..config.statistical_analysis_config import SPDSConfig
from ..models.correlation_models import (
    CorrelationResult,
    PatternResult,
    SignificanceTestResult,
)
from ..models.statistical_analysis_models import (
    DivergenceAnalysisResult,
    StatisticalAnalysisResult,
)


class DivergenceExportService:
    """
    Exports statistical analysis results in multiple formats.

    Provides comprehensive export capabilities including:
    - CSV export with statistical metadata
    - JSON export with nested analysis results
    - Markdown reports with human-readable summaries
    - Integration with existing export infrastructure
    """

    def __init__(self, config: SPDSConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize the Divergence Export Service

        Args:
            config: SPDS configuration instance
            logger: Logger instance for operations
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Export path - single directory for all files
        self.export_base_path = Path("./exports/statistical_analysis")

        # Create export directories
        self._ensure_export_directories()

        # Export configuration
        self.export_formats = ["csv", "json", "markdown"]
        self.include_metadata = True
        self.timestamp_format = "%Y%m%d_%H%M%S"

        self.logger.info("DivergenceExportService initialized")

    async def export_statistical_analysis(
        self,
        analysis_results: List[StatisticalAnalysisResult],
        export_name: str,
        formats: Optional[List[str]] = None,
        include_raw_data: bool = True,
    ) -> Dict[str, str]:
        """
        Export statistical analysis results in multiple formats

        Args:
            analysis_results: List of statistical analysis results
            export_name: Base name for exported files
            formats: Export formats to generate
            include_raw_data: Whether to include raw analysis data

        Returns:
            Dictionary mapping format to exported file path
        """
        try:
            if formats is None:
                formats = self.export_formats

            # Use portfolio name directly as file base
            file_base = export_name

            exported_files = {}

            self.logger.info(
                f"Exporting {len(analysis_results)} statistical analysis results"
            )

            # CSV Export
            if "csv" in formats:
                csv_path = await self._export_csv(
                    analysis_results, file_base, include_raw_data
                )
                exported_files["csv"] = str(csv_path)

            # JSON Export
            if "json" in formats:
                json_path = await self._export_json(
                    analysis_results, file_base, include_raw_data
                )
                exported_files["json"] = str(json_path)

            # Markdown Export
            if "markdown" in formats:
                md_path = await self._export_markdown(analysis_results, file_base)
                exported_files["markdown"] = str(md_path)

            # Generate export summary
            summary_path = await self._generate_export_summary(
                exported_files, file_base, analysis_results
            )
            exported_files["summary"] = str(summary_path)

            self.logger.info(f"Successfully exported to {len(exported_files)} formats")

            return exported_files

        except Exception as e:
            self.logger.error(f"Statistical analysis export failed: {e}")
            raise

    async def export_divergence_analysis(
        self,
        divergence_results: List[DivergenceAnalysisResult],
        export_name: str,
        include_recommendations: bool = True,
    ) -> Dict[str, str]:
        """
        Export divergence analysis results with exit recommendations

        Args:
            divergence_results: List of divergence analysis results
            export_name: Base name for exported files
            include_recommendations: Include exit recommendations

        Returns:
            Dictionary mapping format to exported file path
        """
        try:
            # Use portfolio name directly for divergence exports
            file_base = f"divergence_{export_name}"

            exported_files = {}

            # Prepare divergence data for export
            export_data = await self._prepare_divergence_export_data(
                divergence_results, include_recommendations
            )

            # CSV Export
            csv_path = await self._export_divergence_csv(export_data, file_base)
            exported_files["csv"] = str(csv_path)

            # JSON Export with nested structure
            json_path = await self._export_divergence_json(export_data, file_base)
            exported_files["json"] = str(json_path)

            # Executive summary report
            summary_path = await self._export_divergence_summary(export_data, file_base)
            exported_files["summary"] = str(summary_path)

            return exported_files

        except Exception as e:
            self.logger.error(f"Divergence analysis export failed: {e}")
            raise

    async def export_correlation_analysis(
        self, correlation_results: List[CorrelationResult], export_name: str
    ) -> Dict[str, str]:
        """
        Export correlation analysis results

        Args:
            correlation_results: List of correlation analysis results
            export_name: Base name for exported files

        Returns:
            Dictionary mapping format to exported file path
        """
        try:
            export_timestamp = datetime.now().strftime(self.timestamp_format)
            file_base = f"correlation_{export_name}_{export_timestamp}"

            exported_files = {}

            # Prepare correlation matrix and metadata
            correlation_data = await self._prepare_correlation_export_data(
                correlation_results
            )

            # CSV Export (correlation matrix)
            csv_path = await self._export_correlation_csv(correlation_data, file_base)
            exported_files["csv"] = str(csv_path)

            # JSON Export with metadata
            json_path = await self._export_correlation_json(correlation_data, file_base)
            exported_files["json"] = str(json_path)

            return exported_files

        except Exception as e:
            self.logger.error(f"Correlation analysis export failed: {e}")
            raise

    async def export_pattern_analysis(
        self, pattern_results: List[PatternResult], export_name: str
    ) -> Dict[str, str]:
        """
        Export pattern recognition analysis results

        Args:
            pattern_results: List of pattern analysis results
            export_name: Base name for exported files

        Returns:
            Dictionary mapping format to exported file path
        """
        try:
            export_timestamp = datetime.now().strftime(self.timestamp_format)
            file_base = f"patterns_{export_name}_{export_timestamp}"

            exported_files = {}

            # Prepare pattern data
            pattern_data = await self._prepare_pattern_export_data(pattern_results)

            # CSV Export
            csv_path = await self._export_pattern_csv(pattern_data, file_base)
            exported_files["csv"] = str(csv_path)

            # JSON Export
            json_path = await self._export_pattern_json(pattern_data, file_base)
            exported_files["json"] = str(json_path)

            return exported_files

        except Exception as e:
            self.logger.error(f"Pattern analysis export failed: {e}")
            raise

    # Helper methods for CSV export

    async def _export_csv(
        self,
        analysis_results: List[StatisticalAnalysisResult],
        file_base: str,
        include_raw_data: bool,
    ) -> Path:
        """Export statistical analysis to CSV format"""
        csv_file = self.export_base_path / f"{file_base}.csv"

        # Prepare rows for CSV
        rows = []
        for result in analysis_results:
            base_row = {
                "strategy_name": result.strategy_name,
                "ticker": result.ticker,
                "timeframe": result.timeframe,
                "analysis_timestamp": result.analysis_timestamp.isoformat(),
                "sample_size": result.sample_size,
                "sample_size_confidence": result.sample_size_confidence,
                "dual_layer_convergence_score": result.dual_layer_convergence_score,
                "asset_layer_percentile": result.asset_layer_percentile,
                "strategy_layer_percentile": result.strategy_layer_percentile,
                "exit_signal": result.exit_signal,
                "signal_confidence": result.signal_confidence,
                "exit_recommendation": result.exit_recommendation,
                "target_exit_timeframe": result.target_exit_timeframe,
                "statistical_significance": result.statistical_significance.value,
                "p_value": result.p_value,
            }

            # Add divergence metrics
            if result.divergence_metrics:
                base_row.update(
                    {
                        "z_score_divergence": result.divergence_metrics.get(
                            "z_score", ""
                        ),
                        "iqr_divergence": result.divergence_metrics.get(
                            "iqr_score", ""
                        ),
                        "rarity_score": result.divergence_metrics.get(
                            "rarity_score", ""
                        ),
                    }
                )

            # Add performance metrics
            if result.performance_metrics:
                base_row.update(
                    {
                        "current_return": result.performance_metrics.get(
                            "current_return", ""
                        ),
                        "mfe": result.performance_metrics.get("mfe", ""),
                        "mae": result.performance_metrics.get("mae", ""),
                        "unrealized_pnl": result.performance_metrics.get(
                            "unrealized_pnl", ""
                        ),
                    }
                )

            rows.append(base_row)

        # Write CSV
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            if rows:
                fieldnames = rows[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

        return csv_file

    async def _export_divergence_csv(
        self, export_data: Dict[str, Any], file_base: str
    ) -> Path:
        """Export divergence analysis to CSV"""
        csv_file = self.export_base_path / f"{file_base}.csv"

        # Flatten divergence data for CSV
        rows = []
        for result in export_data["results"]:
            row = {
                "entity_name": result["entity_name"],
                "analysis_type": result["analysis_type"],
                "divergence_score": result["divergence_score"],
                "significance_level": result["significance_level"],
                "exit_signal": result["exit_signal"],
                "confidence": result["confidence"],
                "recommendation": result.get("recommendation", ""),
                "target_timeframe": result.get("target_timeframe", ""),
                "risk_level": result.get("risk_level", ""),
                "analysis_timestamp": result["analysis_timestamp"],
            }

            # Add metrics
            if "metrics" in result:
                for metric_name, metric_value in result["metrics"].items():
                    row[f"metric_{metric_name}"] = metric_value

            rows.append(row)

        # Write CSV
        df = pd.DataFrame(rows)
        df.to_csv(csv_file, index=False)

        return csv_file

    async def _export_correlation_csv(
        self, correlation_data: Dict[str, Any], file_base: str
    ) -> Path:
        """Export correlation matrix to CSV"""
        csv_file = self.export_base_path / f"{file_base}.csv"

        # Convert correlation matrix to DataFrame
        correlation_matrix = correlation_data["correlation_matrix"]
        df = pd.DataFrame(correlation_matrix)
        df.to_csv(csv_file, index=True)

        return csv_file

    async def _export_pattern_csv(
        self, pattern_data: Dict[str, Any], file_base: str
    ) -> Path:
        """Export pattern analysis to CSV"""
        csv_file = self.export_base_path / f"{file_base}.csv"

        # Flatten pattern data
        rows = []
        for pattern in pattern_data["patterns"]:
            row = {
                "pattern_id": pattern["pattern_id"],
                "pattern_type": pattern["pattern_type"],
                "pattern_name": pattern["pattern_name"],
                "pattern_strength": pattern["pattern_strength"],
                "confidence_score": pattern["confidence_score"],
                "significance_level": pattern["significance_level"],
                "frequency": pattern["frequency"],
                "success_rate": pattern.get("success_rate", ""),
                "entities_involved": ";".join(pattern.get("entities_involved", [])),
                "detection_timestamp": pattern["detection_timestamp"],
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(csv_file, index=False)

        return csv_file

    # Helper methods for JSON export

    async def _export_json(
        self,
        analysis_results: List[StatisticalAnalysisResult],
        file_base: str,
        include_raw_data: bool,
    ) -> Path:
        """Export statistical analysis to JSON format"""
        json_file = self.export_base_path / f"{file_base}.json"

        # Prepare JSON structure
        export_data = {
            "export_metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "export_version": "1.0.0",
                "total_results": len(analysis_results),
                "include_raw_data": include_raw_data,
                "config_version": self.config.version
                if hasattr(self.config, "version")
                else "1.0.0",
            },
            "statistical_analysis_results": [],
        }

        for result in analysis_results:
            result_dict = {
                "strategy_name": result.strategy_name,
                "ticker": result.ticker,
                "timeframe": result.timeframe,
                "analysis_timestamp": result.analysis_timestamp.isoformat(),
                "sample_size": result.sample_size,
                "sample_size_confidence": result.sample_size_confidence,
                "dual_layer_convergence_score": result.dual_layer_convergence_score,
                "asset_layer_percentile": result.asset_layer_percentile,
                "strategy_layer_percentile": result.strategy_layer_percentile,
                "exit_signal": result.exit_signal,
                "signal_confidence": result.signal_confidence,
                "exit_recommendation": result.exit_recommendation,
                "target_exit_timeframe": result.target_exit_timeframe,
                "statistical_significance": result.statistical_significance.value,
                "p_value": result.p_value,
                "divergence_metrics": result.divergence_metrics,
                "performance_metrics": result.performance_metrics,
            }

            if include_raw_data and hasattr(result, "raw_analysis_data"):
                result_dict["raw_analysis_data"] = result.raw_analysis_data

            export_data["statistical_analysis_results"].append(result_dict)

        # Write JSON
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)

        return json_file

    async def _export_divergence_json(
        self, export_data: Dict[str, Any], file_base: str
    ) -> Path:
        """Export divergence analysis to JSON"""
        json_file = self.export_base_path / f"{file_base}.json"

        # Add export metadata
        export_data["export_metadata"] = {
            "export_timestamp": datetime.now().isoformat(),
            "export_type": "divergence_analysis",
            "total_results": len(export_data["results"]),
        }

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)

        return json_file

    async def _export_correlation_json(
        self, correlation_data: Dict[str, Any], file_base: str
    ) -> Path:
        """Export correlation analysis to JSON"""
        json_file = self.export_base_path / f"{file_base}.json"

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(correlation_data, f, indent=2, default=str)

        return json_file

    async def _export_pattern_json(
        self, pattern_data: Dict[str, Any], file_base: str
    ) -> Path:
        """Export pattern analysis to JSON"""
        json_file = self.export_base_path / f"{file_base}.json"

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(pattern_data, f, indent=2, default=str)

        return json_file

    # Helper methods for Markdown export

    async def _export_markdown(
        self, analysis_results: List[StatisticalAnalysisResult], file_base: str
    ) -> Path:
        """Export statistical analysis to Markdown report"""
        md_file = self.export_base_path / f"{file_base}.md"

        # Generate markdown content
        content = self._generate_markdown_report(analysis_results)

        with open(md_file, "w", encoding="utf-8") as f:
            f.write(content)

        return md_file

    async def _export_divergence_summary(
        self, export_data: Dict[str, Any], file_base: str
    ) -> Path:
        """Export divergence analysis executive summary"""
        md_file = self.export_base_path / f"{file_base}_export_summary.md"

        content = self._generate_divergence_summary_report(export_data)

        with open(md_file, "w", encoding="utf-8") as f:
            f.write(content)

        return md_file

    # Data preparation methods

    async def _prepare_divergence_export_data(
        self,
        divergence_results: List[DivergenceAnalysisResult],
        include_recommendations: bool,
    ) -> Dict[str, Any]:
        """Prepare divergence data for export"""
        export_data = {
            "analysis_metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "total_entities_analyzed": len(divergence_results),
                "include_recommendations": include_recommendations,
            },
            "results": [],
        }

        for result in divergence_results:
            result_dict = {
                "entity_name": result.entity_name,
                "analysis_type": result.analysis_type,
                "divergence_score": result.divergence_score,
                "significance_level": result.significance_level.value,
                "exit_signal": result.exit_signal,
                "confidence": result.confidence,
                "analysis_timestamp": result.analysis_timestamp.isoformat(),
                "metrics": result.metrics,
            }

            if include_recommendations and hasattr(result, "recommendation"):
                result_dict["recommendation"] = result.recommendation
                result_dict["target_timeframe"] = getattr(
                    result, "target_timeframe", ""
                )
                result_dict["risk_level"] = getattr(result, "risk_level", "")

            export_data["results"].append(result_dict)

        return export_data

    async def _prepare_correlation_export_data(
        self, correlation_results: List[CorrelationResult]
    ) -> Dict[str, Any]:
        """Prepare correlation data for export"""
        # Build correlation matrix
        entities = list(
            set(
                [r.entity_a for r in correlation_results]
                + [r.entity_b for r in correlation_results]
            )
        )

        correlation_matrix = {}
        for entity_a in entities:
            correlation_matrix[entity_a] = {}
            for entity_b in entities:
                if entity_a == entity_b:
                    correlation_matrix[entity_a][entity_b] = 1.0
                else:
                    # Find correlation between entities
                    corr_value = 0.0
                    for result in correlation_results:
                        if (
                            result.entity_a == entity_a and result.entity_b == entity_b
                        ) or (
                            result.entity_a == entity_b and result.entity_b == entity_a
                        ):
                            corr_value = result.correlation_coefficient
                            break
                    correlation_matrix[entity_a][entity_b] = corr_value

        return {
            "correlation_matrix": correlation_matrix,
            "analysis_metadata": {
                "entities_analyzed": entities,
                "total_correlations": len(correlation_results),
                "analysis_timestamp": datetime.now().isoformat(),
            },
            "correlation_details": [
                {
                    "entity_a": r.entity_a,
                    "entity_b": r.entity_b,
                    "correlation_coefficient": r.correlation_coefficient,
                    "p_value": r.p_value,
                    "significance_level": r.significance_level.value,
                    "sample_size": r.sample_size,
                    "analysis_method": r.analysis_method,
                }
                for r in correlation_results
            ],
        }

    async def _prepare_pattern_export_data(
        self, pattern_results: List[PatternResult]
    ) -> Dict[str, Any]:
        """Prepare pattern data for export"""
        return {
            "analysis_metadata": {
                "total_patterns": len(pattern_results),
                "analysis_timestamp": datetime.now().isoformat(),
            },
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_type": p.pattern_type,
                    "pattern_name": p.pattern_name,
                    "pattern_strength": p.pattern_strength,
                    "confidence_score": p.confidence_score,
                    "significance_level": p.statistical_significance.value,
                    "frequency": p.pattern_frequency,
                    "success_rate": p.success_rate,
                    "entities_involved": p.entities_involved,
                    "detection_timestamp": p.detection_timestamp.isoformat(),
                    "detection_method": p.detection_method,
                    "pattern_data": p.pattern_data,
                }
                for p in pattern_results
            ],
        }

    # Report generation methods

    def _generate_markdown_report(
        self, analysis_results: List[StatisticalAnalysisResult]
    ) -> str:
        """Generate comprehensive markdown report"""
        report_lines = [
            "# Statistical Performance Divergence Analysis Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Analyses:** {len(analysis_results)}",
            "",
            "## Executive Summary",
            "",
        ]

        # Summary statistics
        exit_signals = [r.exit_signal for r in analysis_results]
        immediate_exits = sum(1 for signal in exit_signals if "IMMEDIATELY" in signal)
        strong_sells = sum(1 for signal in exit_signals if "STRONG" in signal)
        holds = sum(1 for signal in exit_signals if signal == "HOLD")

        report_lines.extend(
            [
                f"- **Immediate Exits:** {immediate_exits} ({immediate_exits/len(analysis_results)*100:.1f}%)",
                f"- **Strong Sell Signals:** {strong_sells} ({strong_sells/len(analysis_results)*100:.1f}%)",
                f"- **Hold Positions:** {holds} ({holds/len(analysis_results)*100:.1f}%)",
                "",
                "## Detailed Analysis Results",
                "",
            ]
        )

        # Individual results
        for i, result in enumerate(analysis_results, 1):
            report_lines.extend(
                [
                    f"### {i}. {result.strategy_name} - {result.ticker}",
                    "",
                    f"- **Exit Signal:** {result.exit_signal}",
                    f"- **Confidence:** {result.signal_confidence:.1%}",
                    f"- **Dual-Layer Convergence:** {result.dual_layer_convergence_score:.3f}",
                    f"- **Statistical Significance:** {result.statistical_significance.value}",
                    f"- **Recommendation:** {result.exit_recommendation}",
                    "",
                ]
            )

        return "\n".join(report_lines)

    def _generate_divergence_summary_report(self, export_data: Dict[str, Any]) -> str:
        """Generate divergence analysis executive summary"""
        results = export_data["results"]

        report_lines = [
            "# Divergence Analysis Executive Summary",
            "",
            f"**Analysis Date:** {export_data['analysis_metadata']['analysis_timestamp']}",
            f"**Entities Analyzed:** {len(results)}",
            "",
            "## Key Findings",
            "",
        ]

        # High-priority divergences
        high_priority = [r for r in results if r["confidence"] > 0.8]
        medium_priority = [r for r in results if 0.6 <= r["confidence"] <= 0.8]

        report_lines.extend(
            [
                f"- **High Priority Divergences:** {len(high_priority)}",
                f"- **Medium Priority Divergences:** {len(medium_priority)}",
                "",
                "## Action Items",
                "",
            ]
        )

        for result in high_priority:
            report_lines.extend(
                [
                    f"- **{result['entity_name']}**: {result['exit_signal']} "
                    f"(Confidence: {result['confidence']:.1%})"
                ]
            )

        return "\n".join(report_lines)

    async def _generate_export_summary(
        self,
        exported_files: Dict[str, str],
        file_base: str,
        analysis_results: List[StatisticalAnalysisResult],
    ) -> Path:
        """Generate comprehensive SPDS analysis report"""
        summary_file = self.export_base_path / f"{file_base}.md"

        # Generate comprehensive SPDS analysis report
        summary_content = self._generate_comprehensive_spds_report(
            analysis_results, exported_files, file_base
        )

        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(summary_content)

        return summary_file

    def _generate_portfolio_analysis_summary(
        self,
        analysis_results: List[StatisticalAnalysisResult],
        exported_files: Dict[str, str],
    ) -> str:
        """Generate the full portfolio analysis summary matching console output"""

        # Extract portfolio information from file base
        portfolio_name = "portfolio.csv"  # Default fallback
        for format_type, file_path in exported_files.items():
            if "portfolio_analysis_" in file_path:
                # Extract portfolio name from file path
                parts = file_path.split("portfolio_analysis_")
                if len(parts) > 1:
                    portfolio_part = parts[1].split("_")[0]  # Get part before timestamp
                    portfolio_name = f"{portfolio_part}.csv"
                break

        # Calculate signal distribution
        signal_distribution = {}
        for result in analysis_results:
            signal = result.exit_signal
            signal_distribution[signal] = signal_distribution.get(signal, 0) + 1

        # Calculate confidence metrics
        high_confidence_count = 0
        total_results = len(analysis_results)

        for result in analysis_results:
            # Consider high confidence if signal_confidence > 80% or dual_layer_convergence_score > 0.8
            confidence_score = result.signal_confidence
            if confidence_score > 1.0:  # If it's a percentage, convert to fraction
                confidence_score = confidence_score / 100.0

            if confidence_score > 0.80 or result.dual_layer_convergence_score > 0.8:
                high_confidence_count += 1

        confidence_rate = (
            high_confidence_count / total_results if total_results > 0 else 0.0
        )

        # Count action items
        immediate_exits = signal_distribution.get("EXIT_IMMEDIATELY", 0)
        strong_sells = signal_distribution.get("STRONG_SELL", 0)
        sells = signal_distribution.get("SELL", 0)
        holds = signal_distribution.get("HOLD", 0)
        time_exits = signal_distribution.get("TIME_EXIT", 0)

        # Generate summary content matching console format
        summary_lines = [
            "📈 Portfolio Analysis Summary",
            "=" * 40,
            f"Portfolio: {portfolio_name}",
            f"Total Strategies: {total_results}",
            "Data Source: Equity Curves",  # Default - can be enhanced if needed
            "",
            "🎯 Signal Distribution:",
        ]

        # Add signal distribution
        for signal, count in signal_distribution.items():
            summary_lines.append(f"  {signal}: {count}")

        summary_lines.extend(
            [
                "",
                "📊 Analysis Quality:",
                f"  High Confidence: {high_confidence_count}",
                f"  Confidence Rate: {confidence_rate:.1%}",
                "",
                "🚨 Action Items:",
            ]
        )

        # Add action items
        if immediate_exits > 0:
            summary_lines.append(
                f"  ⚠️  {immediate_exits} strategies require IMMEDIATE EXIT"
            )
        if strong_sells > 0:
            summary_lines.append(
                f"  📉 {strong_sells} strategies show STRONG SELL signals"
            )
        if sells > 0:
            summary_lines.append(f"  ⚠️  {sells} strategies show SELL signals")
        if holds > 0:
            summary_lines.append(f"  ✅ {holds} strategies can continue (HOLD)")
        if time_exits > 0:
            summary_lines.append(f"  ⏰ {time_exits} strategies have TIME EXIT signals")

        summary_lines.extend(
            [
                "",
                "📋 Detailed Analysis Results",
                "=" * 80,
                f"{'Strategy':<25} {'Ticker':<8} {'Signal':<15} {'Confidence':<10} {'Recommendation'}",
                "-" * 80,
            ]
        )

        # Signal priority for sorting
        signal_priority = {
            "EXIT_IMMEDIATELY": 1,
            "STRONG_SELL": 2,
            "SELL": 3,
            "HOLD": 4,
            "TIME_EXIT": 5,
        }

        # Sort results by signal urgency
        sorted_results = sorted(
            analysis_results, key=lambda x: signal_priority.get(x.exit_signal, 6)
        )

        # Signal icons and recommendations
        signal_icons = {
            "EXIT_IMMEDIATELY": "🚨",
            "STRONG_SELL": "📉",
            "SELL": "⚠️",
            "HOLD": "✅",
            "TIME_EXIT": "⏰",
        }

        recommendations = {
            "EXIT_IMMEDIATELY": "Exit now",
            "STRONG_SELL": "Exit soon",
            "SELL": "Prepare to exit",
            "HOLD": "Continue holding",
            "TIME_EXIT": "Time-based exit",
        }

        # Add detailed results
        for result in sorted_results:
            signal = result.exit_signal
            confidence = result.signal_confidence
            ticker = result.ticker
            strategy_name = result.strategy_name

            signal_icon = signal_icons.get(signal, "❓")
            recommendation = recommendations.get(signal, "Unknown")

            summary_lines.append(
                f"{strategy_name:<25} {ticker:<8} {signal_icon} {signal:<13} {confidence:>6.1f}%    {recommendation}"
            )

        summary_lines.extend(
            [
                "",
                "💡 Legend:",
                "  🚨 EXIT_IMMEDIATELY - Statistical exhaustion detected",
                "  📉 STRONG_SELL - High probability of diminishing returns",
                "  ⚠️  SELL - Performance approaching statistical limits",
                "  ✅ HOLD - Continue monitoring position",
                "  ⏰ TIME_EXIT - Time-based exit criteria met",
            ]
        )

        return "\n".join(summary_lines)

    def _generate_comprehensive_spds_report(
        self,
        analysis_results: List[StatisticalAnalysisResult],
        exported_files: Dict[str, str],
        file_base: str,
    ) -> str:
        """Generate comprehensive SPDS analysis report matching console output quality"""

        # Extract portfolio name from file_base
        portfolio_name = f"{file_base}.csv"

        # Calculate portfolio metrics
        signal_distribution = {}
        total_results = len(analysis_results)
        high_confidence_count = 0

        for result in analysis_results:
            signal = result.exit_signal
            signal_distribution[signal] = signal_distribution.get(signal, 0) + 1

            # Calculate high confidence based on signal confidence and convergence
            confidence_score = result.signal_confidence
            if confidence_score > 1.0:  # Convert percentage to fraction if needed
                confidence_score = confidence_score / 100.0

            if confidence_score > 0.80 or result.dual_layer_convergence_score > 0.8:
                high_confidence_count += 1

        confidence_rate = (
            high_confidence_count / total_results if total_results > 0 else 0.0
        )

        # Count action items
        immediate_exits = signal_distribution.get("EXIT_IMMEDIATELY", 0)
        strong_sells = signal_distribution.get("STRONG_SELL", 0)
        sells = signal_distribution.get("SELL", 0)
        holds = signal_distribution.get("HOLD", 0)
        time_exits = signal_distribution.get("TIME_EXIT", 0)

        # Calculate statistical thresholds if available from analysis results
        performance_values = []
        for result in analysis_results:
            if (
                result.performance_metrics
                and "current_return" in result.performance_metrics
            ):
                performance_values.append(result.performance_metrics["current_return"])

        # Calculate percentile thresholds
        thresholds = {}
        if performance_values:
            import numpy as np

            performance_values.sort()
            thresholds = {
                "p95_exit_immediately": np.percentile(performance_values, 95)
                if len(performance_values) > 4
                else None,
                "p90_strong_sell": np.percentile(performance_values, 90)
                if len(performance_values) > 4
                else None,
                "p80_sell": np.percentile(performance_values, 80)
                if len(performance_values) > 4
                else None,
                "p70_hold": np.percentile(performance_values, 70)
                if len(performance_values) > 4
                else None,
            }

        # Generate comprehensive report
        report_lines = [
            f"# {file_base.upper()} Portfolio - SPDS Analysis Complete",
            "",
            f"**Generated**: {datetime.now().strftime('%B %d, %Y %H:%M:%S')}  ",
            f"**Portfolio**: {portfolio_name}  ",
            f"**Analysis Type**: Statistical Performance Divergence System (SPDS)  ",
            f"**Total Positions**: {total_results}  ",
            "",
            "---",
            "",
            "## 📊 Executive Summary",
            "",
            f"The {file_base} portfolio analysis reveals **{immediate_exits + strong_sells} positions requiring immediate attention** out of {total_results} total positions analyzed. ",
            f"Statistical analysis indicates **{confidence_rate:.1%} high-confidence signals** with comprehensive risk assessment completed.",
            "",
            "### Key Findings",
            "",
            f"- **Portfolio Quality**: {high_confidence_count}/{total_results} high-confidence analyses ({confidence_rate:.1%})",
            f"- **Immediate Action Required**: {immediate_exits} EXIT_IMMEDIATELY + {strong_sells} STRONG_SELL signals",
            f"- **Current Holdings**: {holds} HOLD positions can continue monitoring",
            "",
        ]

        # Add statistical thresholds if available
        if thresholds and any(v is not None for v in thresholds.values()):
            report_lines.extend(
                [
                    "### Statistical Thresholds",
                    "",
                    "| Percentile | Threshold | Action Required |",
                    "|------------|-----------|-----------------|",
                ]
            )

            if thresholds.get("p95_exit_immediately") is not None:
                report_lines.append(
                    f"| 95th | {thresholds['p95_exit_immediately']:.4f} | EXIT_IMMEDIATELY |"
                )
            if thresholds.get("p90_strong_sell") is not None:
                report_lines.append(
                    f"| 90th | {thresholds['p90_strong_sell']:.4f} | STRONG_SELL |"
                )
            if thresholds.get("p80_sell") is not None:
                report_lines.append(f"| 80th | {thresholds['p80_sell']:.4f} | SELL |")
            if thresholds.get("p70_hold") is not None:
                report_lines.append(f"| 70th | {thresholds['p70_hold']:.4f} | HOLD |")

            report_lines.extend(["", ""])

        # Exit Signal Summary Table
        report_lines.extend(
            [
                "## 🚨 Exit Signal Summary",
                "",
                "| Position | Signal Type | Action Required | Confidence | Performance |",
                "|----------|-------------|-----------------|------------|-------------|",
            ]
        )

        # Signal priority for sorting
        signal_priority = {
            "EXIT_IMMEDIATELY": 1,
            "STRONG_SELL": 2,
            "SELL": 3,
            "TIME_EXIT": 4,
            "HOLD": 5,
        }

        # Sort results by signal urgency, then by confidence
        sorted_results = sorted(
            analysis_results,
            key=lambda x: (
                signal_priority.get(x.exit_signal, 6),
                -x.signal_confidence,  # Negative for descending order
                -x.dual_layer_convergence_score,
            ),
        )

        # Add position rows to table
        for result in sorted_results:
            strategy_name = result.strategy_name
            ticker = result.ticker
            signal = result.exit_signal
            confidence = (
                f"{result.signal_confidence:.1f}%"
                if result.signal_confidence
                else "N/A"
            )

            # Get performance if available
            performance = "N/A"
            if (
                result.performance_metrics
                and "current_return" in result.performance_metrics
            ):
                perf_val = result.performance_metrics["current_return"]
                performance = (
                    f"{perf_val:+.2%}"
                    if isinstance(perf_val, (int, float))
                    else str(perf_val)
                )

            # Action text based on signal
            action_map = {
                "EXIT_IMMEDIATELY": "Take profits now",
                "STRONG_SELL": "Exit soon",
                "SELL": "Consider exit",
                "TIME_EXIT": "Extended holding period",
                "HOLD": "Continue monitoring",
            }
            action = action_map.get(signal, signal)

            # Format position name (strategy + ticker)
            position_name = (
                f"**{ticker}**"
                if signal in ["EXIT_IMMEDIATELY", "STRONG_SELL"]
                else ticker
            )

            report_lines.append(
                f"| {position_name} | **{signal}** | {action} | {confidence} | {performance} |"
            )

        report_lines.extend(
            [
                "",
                "---",
                "",
                "## 📈 Key Insights",
                "",
            ]
        )

        # Immediate action required section
        if immediate_exits > 0 or strong_sells > 0:
            report_lines.extend(
                [
                    "### 🚨 Immediate Action Required:",
                    "",
                ]
            )

            for result in sorted_results:
                if result.exit_signal == "EXIT_IMMEDIATELY":
                    ticker = result.ticker
                    performance = "N/A"
                    if (
                        result.performance_metrics
                        and "current_return" in result.performance_metrics
                    ):
                        perf_val = result.performance_metrics["current_return"]
                        performance = (
                            f"{perf_val:+.2%}"
                            if isinstance(perf_val, (int, float))
                            else str(perf_val)
                        )

                    report_lines.append(
                        f"- **{ticker}**: At 95th percentile performance ({performance}) - statistical exhaustion detected"
                    )

                elif result.exit_signal == "STRONG_SELL":
                    ticker = result.ticker
                    performance = "N/A"
                    if (
                        result.performance_metrics
                        and "current_return" in result.performance_metrics
                    ):
                        perf_val = result.performance_metrics["current_return"]
                        performance = (
                            f"{perf_val:+.2%}"
                            if isinstance(perf_val, (int, float))
                            else str(perf_val)
                        )

                    report_lines.append(
                        f"- **{ticker}**: At 90th percentile ({performance}) - approaching performance limits"
                    )

            report_lines.extend(["", ""])

        # Portfolio performance section
        report_lines.extend(
            [
                "### 📊 Portfolio Performance:",
                "",
            ]
        )

        # Calculate portfolio metrics if performance data available
        profitable_positions = 0
        total_performance = 0
        for result in sorted_results:
            if (
                result.performance_metrics
                and "current_return" in result.performance_metrics
            ):
                perf_val = result.performance_metrics["current_return"]
                if isinstance(perf_val, (int, float)):
                    total_performance += perf_val
                    if perf_val > 0:
                        profitable_positions += 1

        if total_performance != 0:
            success_rate = (
                profitable_positions / total_results if total_results > 0 else 0
            )
            avg_performance = (
                total_performance / total_results if total_results > 0 else 0
            )

            report_lines.extend(
                [
                    f"- **Total Unrealized P&L**: {total_performance:+.2%}",
                    f"- **Success Rate**: {success_rate:.1%} ({profitable_positions} of {total_results} positions profitable)",
                    f"- **Average Performance**: {avg_performance:+.2%} per position",
                ]
            )
        else:
            report_lines.extend(
                [
                    f"- **Total Positions**: {total_results}",
                    f"- **Signal Distribution**: {dict(signal_distribution)}",
                    f"- **High Confidence Rate**: {confidence_rate:.1%}",
                ]
            )

        report_lines.extend(
            [
                "",
                "### 📁 Export Files Generated:",
                "",
            ]
        )

        # List exported files
        for format_type, file_path in exported_files.items():
            if format_type != "summary":  # Don't list the summary file itself
                clean_path = file_path.replace(str(self.export_base_path) + "/", "")
                if format_type == "json":
                    report_lines.append(f"- **Statistical analysis**: `{clean_path}`")
                elif format_type == "csv":
                    report_lines.append(f"- **CSV export**: `{clean_path}`")
                elif format_type == "markdown":
                    report_lines.append(f"- **Technical report**: `{clean_path}`")

        # Add backtesting parameters if they exist
        backtesting_json = f"exports/backtesting_parameters/{file_base}.json"
        backtesting_csv = f"exports/backtesting_parameters/{file_base}.csv"
        report_lines.extend(
            [
                f"- **Backtesting parameters**: `{backtesting_json}` & `{backtesting_csv}`",
                "",
                "---",
                "",
                "## 💡 Recommendations",
                "",
            ]
        )

        # Generate specific recommendations
        recommendations = []
        for i, result in enumerate(sorted_results, 1):
            signal = result.exit_signal
            ticker = result.ticker

            if signal == "EXIT_IMMEDIATELY":
                recommendations.append(
                    f"{i}. **Consider taking profits** on {ticker} immediately (95th percentile exhaustion)"
                )
            elif signal == "STRONG_SELL":
                recommendations.append(
                    f"{i}. **Monitor {ticker} closely** for exit opportunity (approaching limits)"
                )
            elif signal == "SELL":
                recommendations.append(
                    f"{i}. **Prepare exit strategy** for {ticker} (80th percentile threshold)"
                )
            elif signal == "TIME_EXIT":
                recommendations.append(
                    f"{i}. **Review {ticker}** position due to extended holding period"
                )
            elif signal == "HOLD" and i <= 3:  # Only mention top 3 holds
                recommendations.append(
                    f"{i}. **Continue holding** {ticker} position (below statistical thresholds)"
                )

        # Limit to top 6 recommendations to avoid clutter
        for rec in recommendations[:6]:
            report_lines.append(rec)

        if len(recommendations) > 6:
            report_lines.append(
                f"... and {len(recommendations) - 6} additional positions to monitor"
            )

        report_lines.extend(
            [
                "",
                f"The {file_base} portfolio demonstrates {'strong performance with effective risk management' if confidence_rate > 0.5 else 'mixed performance requiring careful monitoring'}, validating the {'conservative' if file_base == 'protected' else 'active'} positioning strategy.",
                "",
                "---",
                "",
                "## 📋 Technical Notes",
                "",
                "### Methodology",
                "",
                "- **Dual-Layer Analysis**: Combined asset-level and strategy-level statistical analysis",
                "- **Percentile-Based Signals**: Exit signals based on performance distribution percentiles",
                "- **Confidence Weighting**: Signal reliability adjusted for sample size and convergence",
                "- **Bootstrap Validation**: Enhanced confidence for portfolios with limited sample sizes",
                "",
                "### Signal Definitions",
                "",
                "- **🚨 EXIT_IMMEDIATELY**: Statistical exhaustion detected (95th+ percentile)",
                "- **📉 STRONG_SELL**: High probability diminishing returns (90th+ percentile)",
                "- **⚠️ SELL**: Performance approaching limits (80th+ percentile)",
                "- **⏰ TIME_EXIT**: Duration-based exit criteria met",
                "- **✅ HOLD**: Continue monitoring (below 70th percentile)",
                "",
                f"*Generated by Statistical Performance Divergence System (SPDS) v2.0 on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            ]
        )

        return "\n".join(report_lines)

    # Public interface methods

    async def export_json(
        self,
        results: List[StatisticalAnalysisResult],
        portfolio_name: str,
        include_raw_data: bool = True,
    ) -> str:
        """Public method to export analysis results as JSON"""
        json_path = await self._export_json(results, portfolio_name, include_raw_data)
        return str(json_path)

    async def export_csv(
        self,
        results: List[StatisticalAnalysisResult],
        portfolio_name: str,
        include_raw_data: bool = True,
    ) -> str:
        """Public method to export analysis results as CSV"""
        csv_path = await self._export_csv(results, portfolio_name, include_raw_data)
        return str(csv_path)

    async def export_markdown(
        self, results: List[StatisticalAnalysisResult], portfolio_name: str
    ) -> str:
        """Public method to export analysis results as Markdown"""
        md_path = await self._export_markdown(results, portfolio_name)
        return str(md_path)

    def _ensure_export_directories(self):
        """Create export directory if it doesn't exist"""
        self.export_base_path.mkdir(parents=True, exist_ok=True)
