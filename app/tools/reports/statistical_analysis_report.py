"""
Statistical Analysis Report Generator

Generates comprehensive markdown reports with statistical analysis insights,
performance summaries, and actionable recommendations.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
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


class StatisticalAnalysisReportGenerator:
    """
    Generates comprehensive statistical analysis reports.

    Provides markdown report generation including:
    - Executive summary with key findings
    - Detailed statistical analysis results
    - Performance attribution analysis
    - Risk assessment and recommendations
    - Exportable charts and visualizations
    """

    def __init__(self, config: SPDSConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize the Statistical Analysis Report Generator

        Args:
            config: SPDS configuration instance
            logger: Logger instance for operations
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Report configuration
        self.reports_path = Path("./reports/statistical_analysis")
        self.reports_path.mkdir(parents=True, exist_ok=True)

        # Report templates
        self.template_styles = {
            "executive": "executive_summary",
            "detailed": "detailed_analysis",
            "technical": "technical_deep_dive",
        }

        self.logger.info("StatisticalAnalysisReportGenerator initialized")

    async def generate_comprehensive_report(
        self,
        analysis_results: List[StatisticalAnalysisResult],
        report_name: str = "statistical_analysis_report",
        report_style: str = "detailed",
    ) -> str:
        """
        Generate comprehensive statistical analysis report

        Args:
            analysis_results: Statistical analysis results
            report_name: Report filename base
            report_style: Report style (executive, detailed, technical)

        Returns:
            Path to generated report file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.reports_path / f"{report_name}_{timestamp}.md"

            self.logger.info(
                f"Generating {report_style} report for {len(analysis_results)} analyses"
            )

            # Generate report content based on style
            if report_style == "executive":
                content = await self._generate_executive_summary_report(
                    analysis_results
                )
            elif report_style == "technical":
                content = await self._generate_technical_report(analysis_results)
            else:  # detailed
                content = await self._generate_detailed_report(analysis_results)

            # Write report
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"Report generated: {report_file}")

            return str(report_file)

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            raise

    async def generate_performance_report(
        self,
        performance_data: Dict[str, Any],
        report_name: str = "performance_analysis",
    ) -> str:
        """
        Generate performance-focused report

        Args:
            performance_data: Performance analysis data
            report_name: Report filename base

        Returns:
            Path to generated report file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.reports_path / f"{report_name}_{timestamp}.md"

            content = await self._generate_performance_report_content(performance_data)

            with open(report_file, "w", encoding="utf-8") as f:
                f.write(content)

            return str(report_file)

        except Exception as e:
            self.logger.error(f"Performance report generation failed: {e}")
            raise

    async def generate_exit_efficiency_report(
        self,
        efficiency_data: Dict[str, Any],
        report_name: str = "exit_efficiency_analysis",
    ) -> str:
        """
        Generate exit efficiency analysis report

        Args:
            efficiency_data: Exit efficiency analysis data
            report_name: Report filename base

        Returns:
            Path to generated report file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.reports_path / f"{report_name}_{timestamp}.md"

            content = await self._generate_exit_efficiency_content(efficiency_data)

            with open(report_file, "w", encoding="utf-8") as f:
                f.write(content)

            return str(report_file)

        except Exception as e:
            self.logger.error(f"Exit efficiency report generation failed: {e}")
            raise

    async def generate_correlation_report(
        self,
        correlation_results: List[CorrelationResult],
        report_name: str = "correlation_analysis",
    ) -> str:
        """
        Generate correlation analysis report

        Args:
            correlation_results: Correlation analysis results
            report_name: Report filename base

        Returns:
            Path to generated report file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.reports_path / f"{report_name}_{timestamp}.md"

            content = await self._generate_correlation_report_content(
                correlation_results
            )

            with open(report_file, "w", encoding="utf-8") as f:
                f.write(content)

            return str(report_file)

        except Exception as e:
            self.logger.error(f"Correlation report generation failed: {e}")
            raise

    async def generate_pattern_analysis_report(
        self,
        pattern_results: List[PatternResult],
        report_name: str = "pattern_analysis",
    ) -> str:
        """
        Generate pattern analysis report

        Args:
            pattern_results: Pattern analysis results
            report_name: Report filename base

        Returns:
            Path to generated report file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.reports_path / f"{report_name}_{timestamp}.md"

            content = await self._generate_pattern_report_content(pattern_results)

            with open(report_file, "w", encoding="utf-8") as f:
                f.write(content)

            return str(report_file)

        except Exception as e:
            self.logger.error(f"Pattern analysis report generation failed: {e}")
            raise

    # Report content generation methods

    async def _generate_executive_summary_report(
        self, analysis_results: List[StatisticalAnalysisResult]
    ) -> str:
        """Generate executive summary report"""

        # Calculate summary statistics
        total_analyses = len(analysis_results)
        exit_signals = [r.exit_signal for r in analysis_results]
        immediate_exits = sum(1 for signal in exit_signals if "IMMEDIATELY" in signal)
        strong_sells = sum(1 for signal in exit_signals if "STRONG" in signal)

        avg_confidence = np.mean([r.signal_confidence for r in analysis_results])
        avg_convergence = np.mean(
            [r.dual_layer_convergence_score for r in analysis_results]
        )

        # High-priority positions
        high_priority = [
            r
            for r in analysis_results
            if r.signal_confidence >= 0.85 and "EXIT" in r.exit_signal
        ]

        content = f"""# Statistical Performance Divergence Analysis
## Executive Summary

**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Positions Analyzed:** {total_analyses}
**Analysis Framework:** Statistical Performance Divergence System v1.0

---

## Key Findings

### 🔴 Immediate Action Required
- **{immediate_exits} positions** require immediate exit (statistical exhaustion detected)
- **{strong_sells} positions** show strong sell signals
- **{len(high_priority)} high-priority alerts** need attention within 24 hours

### 📊 Portfolio Health Metrics
- **Average Signal Confidence:** {avg_confidence:.1%}
- **Average Dual-Layer Convergence:** {avg_convergence:.3f}
- **Statistical Validity:** {sum(1 for r in analysis_results if r.sample_size >= 30)} positions with high confidence

### 🎯 Performance Indicators
- **Exit Efficiency Target:** 85% (vs 57% baseline)
- **Statistical Significance:** {sum(1 for r in analysis_results if r.p_value < 0.05)} positions show significant patterns

---

## Priority Actions

### Immediate Exits (Next Trading Session)
"""

        # Add immediate exit positions
        immediate_positions = [
            r for r in analysis_results if "IMMEDIATELY" in r.exit_signal
        ]
        for i, position in enumerate(immediate_positions[:5], 1):
            content += f"""
**{i}. {position.strategy_name} - {position.ticker}**
- Confidence: {position.signal_confidence:.1%}
- Dual-Layer Score: {position.dual_layer_convergence_score:.3f}
- Recommendation: {position.exit_recommendation}
"""

        content += f"""
### Strong Sell Signals (2-3 Trading Days)
"""

        # Add strong sell positions
        strong_positions = [r for r in analysis_results if "STRONG" in r.exit_signal]
        for i, position in enumerate(strong_positions[:5], 1):
            content += f"""
**{i}. {position.strategy_name} - {position.ticker}**
- Confidence: {position.signal_confidence:.1%}
- Target Exit: {position.target_exit_timeframe}
- Asset Layer: {position.asset_layer_percentile:.0f}th percentile
"""

        content += f"""
---

## Risk Assessment

### Portfolio Risk Factors
- **High-Risk Positions:** {sum(1 for r in analysis_results if r.signal_confidence >= 0.90)}
- **Extended Holdings:** Positions held >45 days require review
- **Concentration Risk:** Monitor position sizing relative to statistical confidence

### Recommendations
1. **Execute immediate exits** for positions with 95%+ convergence scores
2. **Implement trailing stops** for strong sell positions
3. **Increase monitoring frequency** for all flagged positions
4. **Review position sizing** based on statistical confidence levels

---

## Statistical Framework Performance

### Key Metrics
- **Dual-Layer Analysis:** Asset + Strategy convergence validation
- **Multi-Timeframe Validation:** Cross-timeframe statistical confirmation
- **Bootstrap Enhancement:** Small sample size validation
- **Sample Size Confidence:** Weighted by statistical validity

### System Reliability
- **High Confidence:** {sum(1 for r in analysis_results if r.sample_size >= 30)} positions
- **Medium Confidence:** {sum(1 for r in analysis_results if 15 <= r.sample_size < 30)} positions
- **Bootstrap Enhanced:** {sum(1 for r in analysis_results if r.sample_size < 15)} positions

---

*Generated by Statistical Performance Divergence System*
*For detailed analysis, see full technical report*
"""

        return content

    async def _generate_detailed_report(
        self, analysis_results: List[StatisticalAnalysisResult]
    ) -> str:
        """Generate detailed analysis report"""

        content = f"""# Statistical Performance Divergence Analysis
## Detailed Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Positions:** {len(analysis_results)}
**Analysis Framework:** SPDS v1.0

---

## Executive Summary

{await self._generate_summary_section(analysis_results)}

---

## Position Analysis

"""

        # Group positions by signal type
        signal_groups = {
            "EXIT_IMMEDIATELY": [],
            "STRONG_SELL": [],
            "SELL": [],
            "HOLD": [],
        }

        for result in analysis_results:
            if "IMMEDIATELY" in result.exit_signal:
                signal_groups["EXIT_IMMEDIATELY"].append(result)
            elif "STRONG" in result.exit_signal:
                signal_groups["STRONG_SELL"].append(result)
            elif result.exit_signal == "SELL":
                signal_groups["SELL"].append(result)
            else:
                signal_groups["HOLD"].append(result)

        # Generate sections for each signal type
        for signal_type, positions in signal_groups.items():
            if positions:
                content += await self._generate_signal_group_section(
                    signal_type, positions
                )

        content += """
---

## Statistical Analysis Methodology

### Dual-Layer Analysis Framework
1. **Asset Layer (Layer 1):** Asset return distribution analysis across multiple timeframes
2. **Strategy Layer (Layer 2):** Strategy-specific performance analysis using trade history or equity curves
3. **Convergence Analysis:** Statistical alignment between asset and strategy layers

### Signal Generation Process
1. **Percentile Analysis:** Current performance vs historical distributions
2. **Multi-Timeframe Validation:** Cross-timeframe statistical confirmation
3. **Confidence Weighting:** Sample size-adjusted signal strength
4. **Risk Assessment:** VaR-integrated decision making

### Key Metrics
- **Dual-Layer Convergence Score:** Alignment between asset and strategy analysis
- **Signal Confidence:** Sample size and statistical validity weighted confidence
- **Statistical Significance:** P-value based significance testing
- **Exit Recommendation:** Actionable guidance with timing

---

## Risk Management

### Position Risk Assessment
- Monitor positions with confidence >85% for immediate action
- Review positions held >45 days regardless of signal strength
- Implement position sizing based on statistical confidence

### Portfolio Risk Metrics
- **Concentration Risk:** Avoid over-allocation to single strategy/asset
- **Statistical Risk:** Lower confidence positions require closer monitoring
- **Temporal Risk:** Extended holdings may require time-based exits

---

*Statistical Performance Divergence System - Comprehensive Analysis*
"""

        return content

    async def _generate_technical_report(
        self, analysis_results: List[StatisticalAnalysisResult]
    ) -> str:
        """Generate technical deep-dive report"""

        content = f"""# Statistical Performance Divergence Analysis
## Technical Deep-Dive Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Analysis Count:** {len(analysis_results)}
**Framework Version:** SPDS v1.0

---

## Technical Summary

### Statistical Methodology
- **Dual-Layer Architecture:** Asset distribution + Strategy performance analysis
- **Multi-Timeframe Validation:** D, 3D, W, 2W timeframe convergence
- **Bootstrap Enhancement:** Small sample size validation (n<30)
- **Significance Testing:** P-value based statistical validation

### Data Sources
- **Asset Layer:** Return distribution database (./data/raw/reports/return_distribution/)
- **Strategy Layer:** {'Trade history (./data/raw/positions/)' if self.config.USE_TRADE_HISTORY else 'Equity curves (./data/outputs/portfolio_analysis/)'}
- **Sample Sizes:** {np.mean([r.sample_size for r in analysis_results]):.1f} average observations

---

## Detailed Position Analysis

"""

        # Technical analysis for each position
        for i, result in enumerate(analysis_results, 1):
            content += f"""
### {i}. {result.strategy_name} - {result.ticker} ({result.timeframe})

**Statistical Metrics:**
- Sample Size: {result.sample_size} (Confidence: {result.sample_size_confidence:.1%})
- Dual-Layer Convergence: {result.dual_layer_convergence_score:.4f}
- Asset Layer Percentile: {result.asset_layer_percentile:.2f}
- Strategy Layer Percentile: {result.strategy_layer_percentile:.2f}
- P-value: {result.p_value:.4f}
- Statistical Significance: {result.statistical_significance}

**Exit Signal Analysis:**
- Signal: {result.exit_signal}
- Confidence: {result.signal_confidence:.4f}
- Recommendation: {result.exit_recommendation}
- Target Timeframe: {result.target_exit_timeframe}

**Performance Metrics:**
"""

            if result.performance_metrics:
                for metric, value in result.performance_metrics.items():
                    content += f"- {metric}: {value}\n"

            if result.divergence_metrics:
                content += "\n**Divergence Analysis:**\n"
                for metric, value in result.divergence_metrics.items():
                    content += f"- {metric}: {value}\n"

            content += "\n---\n"

        content += """
## Statistical Validation

### Sample Size Distribution
"""

        # Sample size analysis
        sample_sizes = [r.sample_size for r in analysis_results]
        content += f"""
- **High Confidence (n≥30):** {sum(1 for s in sample_sizes if s >= 30)} positions
- **Medium Confidence (15≤n<30):** {sum(1 for s in sample_sizes if 15 <= s < 30)} positions
- **Low Confidence (n<15):** {sum(1 for s in sample_sizes if s < 15)} positions
- **Average Sample Size:** {np.mean(sample_sizes):.1f}
- **Median Sample Size:** {np.median(sample_sizes):.1f}

### Signal Distribution
"""

        # Signal analysis
        signals = [r.exit_signal for r in analysis_results]
        signal_counts = {}
        for signal in signals:
            signal_counts[signal] = signal_counts.get(signal, 0) + 1

        for signal, count in signal_counts.items():
            percentage = count / len(signals) * 100
            content += f"- **{signal}:** {count} positions ({percentage:.1f}%)\n"

        content += f"""

### Confidence Analysis
- **Average Confidence:** {np.mean([r.signal_confidence for r in analysis_results]):.4f}
- **High Confidence (>0.85):** {sum(1 for r in analysis_results if r.signal_confidence > 0.85)} positions
- **Statistical Significance (p<0.05):** {sum(1 for r in analysis_results if r.p_value < 0.05)} positions

---

## Implementation Notes

### Configuration Parameters
- USE_TRADE_HISTORY: {self.config.USE_TRADE_HISTORY}
- Timeframes Analyzed: {', '.join(self.config.TIMEFRAMES)}
- Percentile Thresholds: {', '.join(f'{k}: {v}' for k, v in self.config.PERCENTILE_THRESHOLDS.items())}

### Performance Targets
- Exit Efficiency Target: 85% (vs 57% baseline)
- Portfolio Health Target: 85+ (vs 68 baseline)
- Signal Confidence Target: >80%

---

*Technical Analysis by Statistical Performance Divergence System*
"""

        return content

    async def _generate_summary_section(
        self, analysis_results: List[StatisticalAnalysisResult]
    ) -> str:
        """Generate summary section"""
        immediate_exits = sum(
            1 for r in analysis_results if "IMMEDIATELY" in r.exit_signal
        )
        strong_sells = sum(1 for r in analysis_results if "STRONG" in r.exit_signal)

        return f"""
### Key Findings
- **{immediate_exits} immediate exits** detected (statistical exhaustion)
- **{strong_sells} strong sell signals** identified
- **{np.mean([r.signal_confidence for r in analysis_results]):.1%}** average signal confidence
- **{sum(1 for r in analysis_results if r.p_value < 0.05)}** statistically significant patterns

### Portfolio Health
- **Total Positions:** {len(analysis_results)}
- **High Confidence Signals:** {sum(1 for r in analysis_results if r.signal_confidence >= 0.85)}
- **Statistical Validity:** {sum(1 for r in analysis_results if r.sample_size >= 30)} positions with robust data
"""

    async def _generate_signal_group_section(
        self, signal_type: str, positions: List[StatisticalAnalysisResult]
    ) -> str:
        """Generate section for signal group"""

        section_titles = {
            "EXIT_IMMEDIATELY": "🔴 Immediate Exit Signals",
            "STRONG_SELL": "🟡 Strong Sell Signals",
            "SELL": "🟠 Sell Signals",
            "HOLD": "🟢 Hold Positions",
        }

        content = f"""
### {section_titles.get(signal_type, signal_type)} ({len(positions)} positions)

"""

        for i, position in enumerate(positions[:10], 1):  # Limit to top 10
            content += f"""
**{i}. {position.strategy_name} - {position.ticker}**
- Confidence: {position.signal_confidence:.1%}
- Dual-Layer Score: {position.dual_layer_convergence_score:.3f}
- Asset/Strategy Percentiles: {position.asset_layer_percentile:.0f}/{position.strategy_layer_percentile:.0f}
- Recommendation: {position.exit_recommendation}
- Target: {position.target_exit_timeframe}

"""

        if len(positions) > 10:
            content += f"*... and {len(positions) - 10} additional positions*\n"

        return content

    async def _generate_performance_report_content(
        self, performance_data: Dict[str, Any]
    ) -> str:
        """Generate performance report content"""

        return f"""# Portfolio Performance Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Performance Summary

### Overall Metrics
- **Total Positions:** {performance_data.get('total_positions', 0)}
- **Portfolio Value:** ${performance_data.get('total_value', 0):,.2f}
- **Unrealized P&L:** {performance_data.get('unrealized_pnl_pct', 0):.2%}
- **Exit Efficiency:** {performance_data.get('exit_efficiency', 0):.1%}

### Performance Statistics
- **Win Rate:** {performance_data.get('win_rate', 0):.1%}
- **Profit Factor:** {performance_data.get('profit_factor', 0):.2f}
- **Sharpe Ratio:** {performance_data.get('sharpe_ratio', 0):.2f}
- **Max Drawdown:** {performance_data.get('max_drawdown', 0):.2%}

## Strategy Attribution

{self._format_attribution_table(performance_data.get('strategy_attribution', {}))}

## Risk Analysis

### Risk Metrics
- **Portfolio Health Score:** {performance_data.get('portfolio_health_score', 0):.1f}/100
- **Risk Level:** {performance_data.get('risk_level', 'UNKNOWN')}

### Recommendations
{chr(10).join([f'- {rec}' for rec in performance_data.get('recommendations', [])])}

---

*Generated by Statistical Performance Divergence System*
"""

    async def _generate_exit_efficiency_content(
        self, efficiency_data: Dict[str, Any]
    ) -> str:
        """Generate exit efficiency report content"""

        return f"""# Exit Efficiency Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Exit Efficiency Overview

### Current Performance
- **Current Efficiency:** {efficiency_data.get('current_efficiency', 0):.1%}
- **Baseline Efficiency:** {efficiency_data.get('baseline_efficiency', 0.57):.1%}
- **Improvement:** {efficiency_data.get('improvement', 0):+.1%}
- **Target Efficiency:** {efficiency_data.get('target_efficiency', 0.85):.1%}
- **Progress to Target:** {efficiency_data.get('progress_to_target', 0):.1%}

### Efficiency Trend
**Trend Direction:** {efficiency_data.get('efficiency_trend', 'stable').title()}

## Strategy Breakdown

### Efficiency by Strategy
{self._format_efficiency_table(efficiency_data.get('efficiency_by_strategy', {}))}

### Efficiency by Timeframe
{self._format_efficiency_table(efficiency_data.get('efficiency_by_timeframe', {}))}

## Recommendations

1. **Focus on underperforming strategies** with efficiency <70%
2. **Implement statistical exit signals** for improved timing
3. **Monitor efficiency trends** for early intervention
4. **Optimize position sizing** based on efficiency metrics

---

*Exit Efficiency Analysis by SPDS*
"""

    async def _generate_correlation_report_content(
        self, correlation_results: List[CorrelationResult]
    ) -> str:
        """Generate correlation analysis report content"""

        return f"""# Correlation Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Correlations Analyzed:** {len(correlation_results)}

## Correlation Summary

### Key Findings
- **Strong Correlations (>0.7):** {sum(1 for r in correlation_results if abs(r.correlation_coefficient) > 0.7)}
- **Moderate Correlations (0.5-0.7):** {sum(1 for r in correlation_results if 0.5 <= abs(r.correlation_coefficient) <= 0.7)}
- **Weak Correlations (<0.5):** {sum(1 for r in correlation_results if abs(r.correlation_coefficient) < 0.5)}

## Correlation Analysis

"""

        # Sort by absolute correlation strength
        sorted_correlations = sorted(
            correlation_results,
            key=lambda x: abs(x.correlation_coefficient),
            reverse=True,
        )

        for i, corr in enumerate(sorted_correlations[:20], 1):  # Top 20
            significance = "✓" if corr.p_value < 0.05 else "○"
            content += f"""
**{i}. {corr.entity_a} ↔ {corr.entity_b}**
- Correlation: {corr.correlation_coefficient:.3f} {significance}
- P-value: {corr.p_value:.4f}
- Sample Size: {corr.sample_size}
- Method: {corr.analysis_method}

"""

        content += """
## Risk Implications

### Portfolio Diversification
- **High correlations** indicate concentration risk
- **Consider reducing** exposure to highly correlated assets
- **Monitor correlation changes** over time

---

*Correlation Analysis by Statistical Performance Divergence System*
"""

        return content

    async def _generate_pattern_report_content(
        self, pattern_results: List[PatternResult]
    ) -> str:
        """Generate pattern analysis report content"""

        pattern_types = {}
        for pattern in pattern_results:
            pattern_type = pattern.pattern_type
            if pattern_type not in pattern_types:
                pattern_types[pattern_type] = []
            pattern_types[pattern_type].append(pattern)

        content = f"""# Pattern Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Patterns Identified:** {len(pattern_results)}

## Pattern Summary

### Pattern Types Detected
"""

        for pattern_type, patterns in pattern_types.items():
            avg_strength = np.mean([p.pattern_strength for p in patterns])
            content += f"- **{pattern_type.title()}:** {len(patterns)} patterns (avg strength: {avg_strength:.2f})\n"

        content += """
## Detailed Pattern Analysis

"""

        # Sort by pattern strength
        sorted_patterns = sorted(
            pattern_results,
            key=lambda x: x.pattern_strength * x.confidence_score,
            reverse=True,
        )

        for i, pattern in enumerate(sorted_patterns[:15], 1):  # Top 15
            content += f"""
### {i}. {pattern.pattern_name}
- **Type:** {pattern.pattern_type}
- **Strength:** {pattern.pattern_strength:.3f}
- **Confidence:** {pattern.confidence_score:.3f}
- **Frequency:** {pattern.pattern_frequency}
- **Success Rate:** {pattern.success_rate:.1%} (if available)
- **Entities:** {', '.join(pattern.entities_involved[:3])}{'...' if len(pattern.entities_involved) > 3 else ''}
- **Detection Method:** {pattern.detection_method}

"""

        content += """
## Pattern Implications

### Trading Applications
- **Strong patterns** (strength >0.7) provide reliable signals
- **High-frequency patterns** indicate recurring opportunities
- **Cross-entity patterns** suggest systematic market behavior

### Risk Considerations
- **Pattern degradation** requires continuous monitoring
- **False patterns** from small sample sizes need validation
- **Market regime changes** can invalidate historical patterns

---

*Pattern Analysis by Statistical Performance Divergence System*
"""

        return content

    def _format_attribution_table(self, attribution: Dict[str, Any]) -> str:
        """Format attribution data as table"""
        if not attribution:
            return "No attribution data available."

        table = "| Strategy | Total Return | Avg Return | Trade Count | Win Rate |\n"
        table += "|----------|--------------|------------|-------------|----------|\n"

        for strategy, data in attribution.items():
            table += f"| {strategy} | {data.get('total_return', 0):.2%} | "
            table += (
                f"{data.get('average_return', 0):.2%} | {data.get('trade_count', 0)} | "
            )
            table += f"{data.get('win_rate', 0):.1%} |\n"

        return table

    def _format_efficiency_table(self, efficiency: Dict[str, float]) -> str:
        """Format efficiency data as table"""
        if not efficiency:
            return "No efficiency data available."

        table = "| Category | Efficiency |\n"
        table += "|----------|------------|\n"

        for category, eff in efficiency.items():
            table += f"| {category} | {eff:.1%} |\n"

        return table
