"""Create strategy_sweep_results table.

Revision ID: 002
Revises: 001
Create Date: 2025-10-19

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema - create strategy_sweep_results table."""
    # Create strategy_sweep_results table
    op.create_table(
        "strategy_sweep_results",
        # Primary key and metadata
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "sweep_run_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("sweep_config", postgresql.JSONB, nullable=False),
        # Core Strategy Parameters (5 columns)
        sa.Column("ticker", sa.String(50), nullable=False, index=True),
        sa.Column("strategy_type", sa.String(50), nullable=True),
        sa.Column("fast_period", sa.Integer, nullable=True),
        sa.Column("slow_period", sa.Integer, nullable=True),
        sa.Column("signal_period", sa.Integer, nullable=True),
        # Signal Information (2 columns)
        sa.Column("signal_entry", sa.String(50), nullable=True),
        sa.Column("signal_exit", sa.String(50), nullable=True),
        sa.Column("signal_unconfirmed", sa.String(50), nullable=True),
        # Trade Statistics (3 columns)
        sa.Column("total_open_trades", sa.Integer, nullable=True),
        sa.Column("total_trades", sa.Integer, nullable=True),
        sa.Column("score", sa.Numeric(20, 8), nullable=True),
        # Performance Metrics (5 columns)
        sa.Column("win_rate_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("profit_factor", sa.Numeric(20, 8), nullable=True),
        sa.Column("expectancy_per_trade", sa.Numeric(20, 8), nullable=True),
        sa.Column("sortino_ratio", sa.Numeric(20, 8), nullable=True),
        sa.Column("beats_bnh_pct", sa.Numeric(10, 4), nullable=True),
        # Timing Metrics (5 columns)
        sa.Column(
            "avg_trade_duration",
            sa.String(50),
            nullable=True,
        ),  # Stored as string (e.g., "5 days 3:30:00")
        sa.Column("trades_per_day", sa.Numeric(20, 8), nullable=True),
        sa.Column("trades_per_month", sa.Numeric(20, 8), nullable=True),
        sa.Column("signals_per_month", sa.Numeric(20, 8), nullable=True),
        sa.Column("expectancy_per_month", sa.Numeric(20, 8), nullable=True),
        # Period Information (3 columns)
        sa.Column("start", sa.Integer, nullable=True),
        sa.Column("end", sa.Integer, nullable=True),
        sa.Column(
            "period",
            sa.String(50),
            nullable=True,
        ),  # Stored as string (e.g., "365 days")
        # Portfolio Values (5 columns)
        sa.Column("start_value", sa.Numeric(20, 2), nullable=True),
        sa.Column("end_value", sa.Numeric(20, 2), nullable=True),
        sa.Column("total_return_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("benchmark_return_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("max_gross_exposure_pct", sa.Numeric(10, 4), nullable=True),
        # Risk and Drawdown (4 columns)
        sa.Column("total_fees_paid", sa.Numeric(20, 2), nullable=True),
        sa.Column("max_drawdown_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column(
            "max_drawdown_duration",
            sa.String(50),
            nullable=True,
        ),  # Stored as string
        sa.Column("total_closed_trades", sa.Integer, nullable=True),
        # Trade Analysis (7 columns)
        sa.Column("open_trade_pnl", sa.Numeric(20, 2), nullable=True),
        sa.Column("best_trade_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("worst_trade_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("avg_winning_trade_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("avg_losing_trade_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("avg_winning_trade_duration", sa.String(50), nullable=True),
        sa.Column("avg_losing_trade_duration", sa.String(50), nullable=True),
        # Advanced Metrics (4 columns)
        sa.Column("expectancy", sa.Numeric(20, 8), nullable=True),
        sa.Column("sharpe_ratio", sa.Numeric(20, 8), nullable=True),
        sa.Column("calmar_ratio", sa.Numeric(20, 8), nullable=True),
        sa.Column("omega_ratio", sa.Numeric(20, 8), nullable=True),
        # Risk Metrics (10 columns)
        sa.Column("skew", sa.Numeric(20, 8), nullable=True),
        sa.Column("kurtosis", sa.Numeric(20, 8), nullable=True),
        sa.Column("tail_ratio", sa.Numeric(20, 8), nullable=True),
        sa.Column("common_sense_ratio", sa.Numeric(20, 8), nullable=True),
        sa.Column("value_at_risk", sa.Numeric(20, 8), nullable=True),
        sa.Column("daily_returns", sa.Numeric(20, 8), nullable=True),
        sa.Column("annual_returns", sa.Numeric(20, 8), nullable=True),
        sa.Column("cumulative_returns", sa.Numeric(20, 8), nullable=True),
        sa.Column("annualized_return", sa.Numeric(20, 8), nullable=True),
        sa.Column("annualized_volatility", sa.Numeric(20, 8), nullable=True),
        # Signal and Position Counts (3 columns)
        sa.Column("signal_count", sa.Integer, nullable=True),
        sa.Column("position_count", sa.Integer, nullable=True),
        sa.Column("total_period", sa.Numeric(20, 8), nullable=True),
        # Universal Exit Strategy Parameters (3 columns)
        sa.Column("exit_fast_period", sa.Integer, nullable=True),
        sa.Column("exit_slow_period", sa.Numeric(20, 8), nullable=True),
        sa.Column("exit_signal_period", sa.Integer, nullable=True),
        # Extended Schema Fields (4 columns)
        sa.Column("allocation_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("stop_loss_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("last_position_open_date", sa.String(50), nullable=True),
        sa.Column("last_position_close_date", sa.String(50), nullable=True),
    )

    # Create indexes for common query patterns
    op.create_index(
        "ix_strategy_sweep_sweep_run_id",
        "strategy_sweep_results",
        ["sweep_run_id"],
    )
    op.create_index("ix_strategy_sweep_ticker", "strategy_sweep_results", ["ticker"])
    op.create_index(
        "ix_strategy_sweep_created_at",
        "strategy_sweep_results",
        ["created_at"],
    )
    op.create_index(
        "ix_strategy_sweep_ticker_strategy",
        "strategy_sweep_results",
        ["ticker", "strategy_type"],
    )


def downgrade() -> None:
    """Downgrade database schema - drop strategy_sweep_results table."""
    op.drop_index(
        "ix_strategy_sweep_ticker_strategy",
        table_name="strategy_sweep_results",
    )
    op.drop_index("ix_strategy_sweep_created_at", table_name="strategy_sweep_results")
    op.drop_index("ix_strategy_sweep_ticker", table_name="strategy_sweep_results")
    op.drop_index("ix_strategy_sweep_sweep_run_id", table_name="strategy_sweep_results")
    op.drop_table("strategy_sweep_results")
