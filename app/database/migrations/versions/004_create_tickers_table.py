"""Create tickers table and normalize ticker references.

Revision ID: 004
Revises: 003
Create Date: 2025-10-19

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema - create tickers table and normalize references."""

    # 1. Create tickers table
    op.create_table(
        "tickers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ticker", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # 2. Populate tickers table with distinct tickers from strategy_sweep_results
    op.execute(
        """
        INSERT INTO tickers (ticker)
        SELECT DISTINCT ticker
        FROM strategy_sweep_results
        WHERE ticker IS NOT NULL
        ORDER BY ticker
    """,
    )

    # 3. Add ticker_id column to strategy_sweep_results (nullable initially)
    op.add_column(
        "strategy_sweep_results",
        sa.Column("ticker_id", sa.Integer, nullable=True, index=True),
    )

    # 4. Populate ticker_id in strategy_sweep_results
    op.execute(
        """
        UPDATE strategy_sweep_results sr
        SET ticker_id = t.id
        FROM tickers t
        WHERE sr.ticker = t.ticker
    """,
    )

    # 5. Make ticker_id NOT NULL
    op.alter_column("strategy_sweep_results", "ticker_id", nullable=False)

    # 6. Add foreign key constraint with CASCADE delete
    op.create_foreign_key(
        "fk_strategy_sweep_results_ticker_id",
        "strategy_sweep_results",
        "tickers",
        ["ticker_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 7. Drop the old ticker string column
    op.drop_index("ix_strategy_sweep_ticker", table_name="strategy_sweep_results")
    op.drop_index(
        "ix_strategy_sweep_ticker_strategy",
        table_name="strategy_sweep_results",
    )
    op.drop_column("strategy_sweep_results", "ticker")

    # 8. Recreate composite index with ticker_id
    op.create_index(
        "ix_strategy_sweep_ticker_id_strategy",
        "strategy_sweep_results",
        ["ticker_id", "strategy_type"],
    )


def downgrade() -> None:
    """Downgrade database schema - revert ticker normalization."""

    # 1. Drop composite index
    op.drop_index(
        "ix_strategy_sweep_ticker_id_strategy",
        table_name="strategy_sweep_results",
    )

    # 2. Add back ticker string column
    op.add_column(
        "strategy_sweep_results",
        sa.Column("ticker", sa.String(50), nullable=True, index=True),
    )

    # 3. Populate ticker from tickers table
    op.execute(
        """
        UPDATE strategy_sweep_results sr
        SET ticker = t.ticker
        FROM tickers t
        WHERE sr.ticker_id = t.id
    """,
    )

    # 4. Make ticker NOT NULL
    op.alter_column("strategy_sweep_results", "ticker", nullable=False)

    # 5. Recreate original indexes
    op.create_index("ix_strategy_sweep_ticker", "strategy_sweep_results", ["ticker"])
    op.create_index(
        "ix_strategy_sweep_ticker_strategy",
        "strategy_sweep_results",
        ["ticker", "strategy_type"],
    )

    # 6. Drop foreign key constraint and ticker_id column
    op.drop_constraint(
        "fk_strategy_sweep_results_ticker_id",
        "strategy_sweep_results",
        type_="foreignkey",
    )
    op.drop_column("strategy_sweep_results", "ticker_id")

    # 7. Drop tickers table
    op.drop_table("tickers")
