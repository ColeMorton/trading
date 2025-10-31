"""Create metric_types and strategy_sweep_result_metrics tables.

Revision ID: 003
Revises: 002
Create Date: 2025-10-19

This migration creates a normalized structure for metric type classifications,
replacing the comma-separated string field with proper relational tables.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


# Comprehensive list of metric type classifications
METRIC_TYPES_SEED_DATA = [
    # Return Metrics
    ("Most Total Return [%]", "return", "Highest total return percentage"),
    ("Median Total Return [%]", "return", "Median total return percentage"),
    ("Mean Total Return [%]", "return", "Average total return percentage"),
    ("Most Annualized Return", "return", "Highest annualized return"),
    ("Median Annualized Return", "return", "Median annualized return"),
    ("Mean Annualized Return", "return", "Average annualized return"),
    ("Most Cumulative Returns", "return", "Highest cumulative returns"),
    ("Median Cumulative Returns", "return", "Median cumulative returns"),
    # Risk-Adjusted Metrics
    ("Most Sharpe Ratio", "risk", "Highest Sharpe ratio (risk-adjusted return)"),
    ("Median Sharpe Ratio", "risk", "Median Sharpe ratio"),
    ("Mean Sharpe Ratio", "risk", "Average Sharpe ratio"),
    ("Most Sortino Ratio", "risk", "Highest Sortino ratio (downside deviation)"),
    ("Median Sortino Ratio", "risk", "Median Sortino ratio"),
    ("Mean Sortino Ratio", "risk", "Average Sortino ratio"),
    ("Most Calmar Ratio", "risk", "Highest Calmar ratio (return/max drawdown)"),
    ("Median Calmar Ratio", "risk", "Median Calmar ratio"),
    ("Mean Calmar Ratio", "risk", "Average Calmar ratio"),
    ("Most Omega Ratio", "risk", "Highest Omega ratio"),
    ("Median Omega Ratio", "risk", "Median Omega ratio"),
    ("Mean Omega Ratio", "risk", "Average Omega ratio"),
    # Drawdown Metrics
    ("Most Max Drawdown [%]", "risk", "Largest maximum drawdown percentage"),
    ("Median Max Drawdown [%]", "risk", "Median maximum drawdown percentage"),
    ("Mean Max Drawdown [%]", "risk", "Average maximum drawdown percentage"),
    ("Least Max Drawdown [%]", "risk", "Smallest maximum drawdown percentage"),
    # Trade Statistics
    ("Most Total Trades", "trade", "Highest number of total trades"),
    ("Median Total Trades", "trade", "Median number of total trades"),
    ("Mean Total Trades", "trade", "Average number of total trades"),
    ("Most Win Rate [%]", "trade", "Highest win rate percentage"),
    ("Median Win Rate [%]", "trade", "Median win rate percentage"),
    ("Mean Win Rate [%]", "trade", "Average win rate percentage"),
    ("Most Profit Factor", "trade", "Highest profit factor"),
    ("Median Profit Factor", "trade", "Median profit factor"),
    ("Mean Profit Factor", "trade", "Average profit factor"),
    # Expectancy Metrics
    ("Most Expectancy per Trade", "trade", "Highest expected profit per trade"),
    ("Median Expectancy per Trade", "trade", "Median expected profit per trade"),
    ("Mean Expectancy per Trade", "trade", "Average expected profit per trade"),
    ("Most Expectancy Per Month", "timing", "Highest expected profit per month"),
    ("Median Expectancy Per Month", "timing", "Median expected profit per month"),
    ("Mean Expectancy Per Month", "timing", "Average expected profit per month"),
    # Timing Metrics
    ("Most Trades Per Day", "timing", "Highest trades per day frequency"),
    ("Median Trades Per Day", "timing", "Median trades per day frequency"),
    ("Mean Trades Per Day", "timing", "Average trades per day frequency"),
    ("Most Trades Per Month", "timing", "Highest trades per month frequency"),
    ("Median Trades Per Month", "timing", "Median trades per month frequency"),
    ("Mean Trades Per Month", "timing", "Average trades per month frequency"),
    ("Most Signals Per Month", "timing", "Highest signals per month frequency"),
    ("Median Signals Per Month", "timing", "Median signals per month frequency"),
    ("Mean Signals Per Month", "timing", "Average signals per month frequency"),
    # Trade Duration Metrics
    ("Most Avg Trade Duration", "timing", "Longest average trade duration"),
    ("Median Avg Trade Duration", "timing", "Median average trade duration"),
    ("Mean Avg Trade Duration", "timing", "Average trade duration"),
    (
        "Most Avg Winning Trade Duration",
        "timing",
        "Longest average winning trade duration",
    ),
    ("Mean Avg Winning Trade Duration", "timing", "Average winning trade duration"),
    (
        "Most Avg Losing Trade Duration",
        "timing",
        "Longest average losing trade duration",
    ),
    ("Mean Avg Losing Trade Duration", "timing", "Average losing trade duration"),
    # Trade Performance Metrics
    ("Most Avg Winning Trade [%]", "trade", "Highest average winning trade percentage"),
    (
        "Median Avg Winning Trade [%]",
        "trade",
        "Median average winning trade percentage",
    ),
    ("Mean Avg Winning Trade [%]", "trade", "Average winning trade percentage"),
    (
        "Most Avg Losing Trade [%]",
        "trade",
        "Highest average losing trade percentage (least negative)",
    ),
    ("Median Avg Losing Trade [%]", "trade", "Median average losing trade percentage"),
    ("Mean Avg Losing Trade [%]", "trade", "Average losing trade percentage"),
    ("Most Best Trade [%]", "trade", "Highest best single trade percentage"),
    ("Most Worst Trade [%]", "trade", "Worst single trade percentage"),
    # Volatility Metrics
    ("Most Annualized Volatility", "risk", "Highest annualized volatility"),
    ("Median Annualized Volatility", "risk", "Median annualized volatility"),
    ("Mean Annualized Volatility", "risk", "Average annualized volatility"),
    ("Least Annualized Volatility", "risk", "Lowest annualized volatility"),
    # Distribution Metrics
    ("Most Skew", "risk", "Highest return distribution skewness"),
    ("Median Skew", "risk", "Median return distribution skewness"),
    ("Mean Skew", "risk", "Average return distribution skewness"),
    ("Most Kurtosis", "risk", "Highest return distribution kurtosis"),
    ("Median Kurtosis", "risk", "Median return distribution kurtosis"),
    ("Mean Kurtosis", "risk", "Average return distribution kurtosis"),
    # Risk Metrics
    ("Most Value at Risk", "risk", "Highest value at risk"),
    ("Median Value at Risk", "risk", "Median value at risk"),
    ("Mean Value at Risk", "risk", "Average value at risk"),
    ("Most Tail Ratio", "risk", "Highest tail ratio"),
    ("Median Tail Ratio", "risk", "Median tail ratio"),
    ("Mean Tail Ratio", "risk", "Average tail ratio"),
    ("Most Common Sense Ratio", "risk", "Highest common sense ratio"),
    # Performance vs Benchmark
    ("Most Beats BNH [%]", "return", "Highest performance vs buy-and-hold percentage"),
    ("Median Beats BNH [%]", "return", "Median performance vs buy-and-hold percentage"),
    ("Mean Beats BNH [%]", "return", "Average performance vs buy-and-hold percentage"),
    # Other Metrics
    ("Most Score", "composite", "Highest composite score"),
    ("Median Score", "composite", "Median composite score"),
    ("Mean Score", "composite", "Average composite score"),
]


def upgrade() -> None:
    """Upgrade database schema - create metric_types and junction table."""

    # Add metric_type column to strategy_sweep_results if it doesn't exist
    # This column stores the legacy comma-separated string for backward compatibility
    op.add_column(
        "strategy_sweep_results",
        sa.Column("metric_type", sa.String(500), nullable=True),
    )

    # Create metric_types reference table
    op.create_table(
        "metric_types",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create index on name for fast lookups
    op.create_index("ix_metric_types_name", "metric_types", ["name"])
    op.create_index("ix_metric_types_category", "metric_types", ["category"])

    # Create junction table for many-to-many relationship
    op.create_table(
        "strategy_sweep_result_metrics",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("sweep_result_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric_type_id", sa.Integer, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["sweep_result_id"],
            ["strategy_sweep_results.id"],
            name="fk_sweep_result_metrics_result_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["metric_type_id"],
            ["metric_types.id"],
            name="fk_sweep_result_metrics_type_id",
        ),
    )

    # Create unique constraint to prevent duplicate metric assignments
    op.create_unique_constraint(
        "uq_sweep_result_metric",
        "strategy_sweep_result_metrics",
        ["sweep_result_id", "metric_type_id"],
    )

    # Create indexes for efficient queries
    op.create_index(
        "ix_sweep_result_metrics_result",
        "strategy_sweep_result_metrics",
        ["sweep_result_id"],
    )
    op.create_index(
        "ix_sweep_result_metrics_type",
        "strategy_sweep_result_metrics",
        ["metric_type_id"],
    )

    # Populate metric_types with seed data
    connection = op.get_bind()
    for name, category, description in METRIC_TYPES_SEED_DATA:
        connection.execute(
            sa.text(
                "INSERT INTO metric_types (name, category, description) "
                "VALUES (:name, :category, :description)",
            ),
            {"name": name, "category": category, "description": description},
        )

    # Migrate existing data from metric_type string column to junction table
    # This handles existing records that have comma-separated metric_type values
    connection.execute(
        sa.text(
            """
            INSERT INTO strategy_sweep_result_metrics (sweep_result_id, metric_type_id)
            SELECT DISTINCT
                ssr.id,
                mt.id
            FROM strategy_sweep_results ssr
            CROSS JOIN LATERAL unnest(string_to_array(ssr.metric_type, ',')) AS metric_name
            JOIN metric_types mt ON TRIM(metric_name) = mt.name
            WHERE ssr.metric_type IS NOT NULL
              AND ssr.metric_type != ''
            ON CONFLICT (sweep_result_id, metric_type_id) DO NOTHING
        """,
        ),
    )


def downgrade() -> None:
    """Downgrade database schema - drop metric_types and junction table."""
    # Drop junction table first (due to foreign keys)
    op.drop_index(
        "ix_sweep_result_metrics_type",
        table_name="strategy_sweep_result_metrics",
    )
    op.drop_index(
        "ix_sweep_result_metrics_result",
        table_name="strategy_sweep_result_metrics",
    )
    op.drop_constraint(
        "uq_sweep_result_metric",
        "strategy_sweep_result_metrics",
        type_="unique",
    )
    op.drop_constraint(
        "fk_sweep_result_metrics_type_id",
        "strategy_sweep_result_metrics",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_sweep_result_metrics_result_id",
        "strategy_sweep_result_metrics",
        type_="foreignkey",
    )
    op.drop_table("strategy_sweep_result_metrics")

    # Drop metric_types table
    op.drop_index("ix_metric_types_category", table_name="metric_types")
    op.drop_index("ix_metric_types_name", table_name="metric_types")
    op.drop_table("metric_types")

    # Remove metric_type column from strategy_sweep_results
    op.drop_column("strategy_sweep_results", "metric_type")
