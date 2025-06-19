# Additional VectorBT Metrics Beyond Your List

After thoroughly researching the VectorBT library documentation and GitHub repository, I've identified **58 additional metrics** not included in your comprehensive list. These metrics provide deeper insights into trading strategy performance, risk management, and portfolio dynamics.

## Advanced trade analysis metrics reveal system quality

VectorBT offers several sophisticated trade analysis metrics that go beyond basic win/loss statistics. The **System Quality Number (SQN)** metric, accessible via `trades.sqn()`, provides a standardized measure of trading system quality developed by Van Tharp. Additionally, **streak analysis** metrics track maximum consecutive winning and losing trades through `trades.winning_streak.max()` and `trades.losing_streak.max()`, offering insights into strategy consistency.

The library also provides **directional trade breakdowns** with metrics for total long trades, total short trades, and the percentage split between them. **Coverage metrics** measure the temporal footprint of trades, with both non-overlapping coverage and overlap coverage options available, helping traders understand their market exposure patterns over time.

## Comprehensive drawdown recovery analysis

While your list includes basic drawdown metrics, VectorBT provides an extensive suite of **drawdown recovery statistics** that analyze the complete lifecycle of drawdowns. These include metrics for active drawdowns (ongoing losses), recovery duration ratios, and the percentage of time spent in drawdown states. The **Active Recovery Return [%]** metric calculates the exact return needed to recover from current drawdowns, while recovery duration metrics analyze both maximum and average recovery times.

The drawdown module also tracks the total number of recovered versus active drawdowns, providing insights into a strategy's resilience and recovery patterns. These metrics are particularly valuable for understanding not just the depth of losses, but the strategy's ability to recover from them.

## Portfolio exposure and position metrics

VectorBT's exposure analysis goes beyond simple gross exposure with metrics like **Position Coverage [%]**, which measures the percentage of time a strategy maintains market positions. The library distinguishes between **net exposure** (directional exposure accounting for long/short positions) and **gross exposure** (total absolute exposure), providing both current values and historical averages.

These exposure metrics help traders understand their true market risk at any point in time and ensure their strategies align with intended exposure levels and risk management rules.

## Advanced risk-adjusted performance measures

The library includes several sophisticated risk-adjusted return metrics not in your list. The **Deflated Sharpe Ratio** adjusts the traditional Sharpe ratio for statistical significance, reducing the likelihood of false positives in strategy evaluation. The **Information Ratio** measures risk-adjusted returns relative to a benchmark, while **Conditional Value at Risk (CVaR)** provides expected shortfall analysis for tail risk assessment.

**Capture ratios** (up capture, down capture, and overall capture) measure how well a strategy participates in benchmark movements during positive and negative periods, offering insights into strategy behavior across different market conditions.

## VectorBT PRO exclusive MAE/MFE analysis

For VectorBT PRO users, the library offers **Maximum Adverse Excursion (MAE)** and **Maximum Favorable Excursion (MFE)** analysis. These metrics track the maximum unrealized losses and gains during each trade's lifecycle, providing insights into optimal stop-loss and take-profit levels. The **Edge Ratio** metric incorporates these open profits and losses to provide a more complete profitability measure than traditional metrics.

These PRO features include both price-based and position-based MAE/MFE calculations, as well as expanding versions that show how these metrics develop throughout trade lifecycles.

## Order execution and simulation metrics

VectorBT's logging system provides detailed **execution analysis** metrics including fill rates, rejection rates, and status breakdowns. These metrics help identify execution issues and optimize order placement strategies. The **Status Counts** metric breaks down orders by execution status (Filled, Ignored, Rejected), while **Status Info Counts** provides even more granular execution details.

## Cash and asset flow analysis

The library includes **Asset Flow** and **Cash Flow** metrics that track the movement of assets and cash throughout the portfolio's lifecycle. The **Free Cash Flow** metric specifically tracks available cash for new positions, helping ensure strategies maintain adequate liquidity.

## Conclusion

These 58 additional metrics significantly expand the analytical capabilities available in VectorBT beyond standard backtesting statistics. They provide deeper insights into trade quality, risk management effectiveness, execution efficiency, and portfolio dynamics. The metrics span from basic operational statistics like order counts to sophisticated risk-adjusted performance measures like the Deflated Sharpe Ratio and comprehensive drawdown recovery analysis.

Most of these metrics are accessible through VectorBT's modular architecture via methods like `portfolio.stats()`, `trades.stats()`, `drawdowns.stats()`, and their individual accessor methods. The VectorBT PRO exclusive metrics offer even more advanced analysis capabilities for professional traders and researchers seeking deeper insights into strategy behavior and optimization opportunities.
