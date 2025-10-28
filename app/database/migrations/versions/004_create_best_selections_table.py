"""Create sweep_best_selections and selection_algorithms tables.

Revision ID: 005
Revises: 004
Create Date: 2025-10-19

This migration creates tables to track "best portfolio" selections from strategy sweeps,
including the selection algorithm metadata and confidence scores.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


# Selection algorithm constants
SELECTION_ALGORITHMS = [
    (
        "top_3_all_match",
        "Top 3 All Match",
        "All top 3 results have same parameter combination",
        100.00,
        100.00,
    ),
    (
        "top_5_3_of_5",
        "Top 5 - 3 of 5 Match",
        "3 out of top 5 results have same combination",
        60.00,
        80.00,
    ),
    (
        "top_8_5_of_8",
        "Top 8 - 5 of 8 Match",
        "5 out of top 8 results have same combination",
        62.50,
        75.00,
    ),
    (
        "top_2_both_match",
        "Top 2 Both Match",
        "Both top 2 results have same combination",
        100.00,
        100.00,
    ),
    (
        "highest_score_fallback",
        "Highest Score Fallback",
        "No consistent pattern, selected highest score",
        0.00,
        50.00,
    ),
]


def upgrade() -> None:
    """Upgrade database schema - create best selections and algorithms tables."""

    # Create selection_algorithms reference table
    op.create_table(
        "selection_algorithms",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("algorithm_code", sa.String(50), nullable=False, unique=True),
        sa.Column("algorithm_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("min_confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("max_confidence", sa.Numeric(5, 2), nullable=True),
    )

    # Create index on algorithm_code
    op.create_index(
        "ix_selection_algorithms_code",
        "selection_algorithms",
        ["algorithm_code"],
    )

    # Populate selection_algorithms with predefined values
    connection = op.get_bind()
    for (
        algorithm_code,
        algorithm_name,
        description,
        min_conf,
        max_conf,
    ) in SELECTION_ALGORITHMS:
        connection.execute(
            sa.text(
                "INSERT INTO selection_algorithms "
                "(algorithm_code, algorithm_name, description, min_confidence, max_confidence) "
                "VALUES (:code, :name, :desc, :min_conf, :max_conf)",
            ),
            {
                "code": algorithm_code,
                "name": algorithm_name,
                "desc": description,
                "min_conf": min_conf,
                "max_conf": max_conf,
            },
        )

    # Create sweep_best_selections table
    op.create_table(
        "sweep_best_selections",
        # Primary key
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        # Core identifiers
        sa.Column(
            "sweep_run_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
        ),
        sa.Column("ticker_id", sa.Integer, nullable=False, index=True),
        sa.Column("strategy_type", sa.String(50), nullable=False),
        sa.Column(
            "best_result_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
        ),
        # Selection algorithm metadata
        sa.Column("selection_algorithm", sa.String(50), nullable=False),
        sa.Column("selection_criteria", sa.String(100), nullable=False),
        sa.Column("confidence_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("alternatives_considered", sa.Integer, nullable=True),
        # Winning parameter combination (denormalized for quick queries)
        sa.Column("winning_fast_period", sa.Integer, nullable=True),
        sa.Column("winning_slow_period", sa.Integer, nullable=True),
        sa.Column("winning_signal_period", sa.Integer, nullable=True),
        # Result snapshot (at time of selection)
        sa.Column("result_score", sa.Numeric(20, 8), nullable=True),
        sa.Column("result_sharpe_ratio", sa.Numeric(20, 8), nullable=True),
        sa.Column("result_total_return_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("result_win_rate_pct", sa.Numeric(10, 4), nullable=True),
        # Audit timestamp
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Foreign keys
        sa.ForeignKeyConstraint(
            ["best_result_id"],
            ["strategy_sweep_results.id"],
            name="fk_best_selections_result_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ticker_id"],
            ["tickers.id"],
            name="fk_best_selections_ticker_id",
        ),
    )

    # Create unique constraint: one best per sweep + ticker + strategy
    op.create_unique_constraint(
        "uq_best_selection_per_sweep_ticker_strategy",
        "sweep_best_selections",
        ["sweep_run_id", "ticker_id", "strategy_type"],
    )

    # Create composite index for efficient queries
    op.create_index(
        "idx_best_selections_composite",
        "sweep_best_selections",
        ["sweep_run_id", "ticker_id", "strategy_type"],
    )


def downgrade() -> None:
    """Downgrade database schema - drop best selections and algorithms tables."""
    # Drop sweep_best_selections table first (due to foreign keys)
    op.drop_index("idx_best_selections_composite", table_name="sweep_best_selections")
    op.drop_constraint(
        "uq_best_selection_per_sweep_ticker_strategy",
        "sweep_best_selections",
        type_="unique",
    )
    op.drop_constraint(
        "fk_best_selections_ticker_id",
        "sweep_best_selections",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_best_selections_result_id",
        "sweep_best_selections",
        type_="foreignkey",
    )
    op.drop_table("sweep_best_selections")

    # Drop selection_algorithms table
    op.drop_index("ix_selection_algorithms_code", table_name="selection_algorithms")
    op.drop_table("selection_algorithms")
