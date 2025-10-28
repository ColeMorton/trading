"""Create strategy_types table and normalize strategy type references.

Revision ID: 006
Revises: 005
Create Date: 2025-10-19

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema - create strategy_types table and normalize references."""

    # 1. Create strategy_types table
    op.create_table(
        "strategy_types",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "strategy_type", sa.String(50), nullable=False, unique=True, index=True
        ),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")
        ),
    )

    # 2. Populate strategy_types table with distinct strategy types from both tables
    op.execute(
        """
        INSERT INTO strategy_types (strategy_type)
        SELECT DISTINCT strategy_type
        FROM strategy_sweep_results
        WHERE strategy_type IS NOT NULL
        UNION
        SELECT DISTINCT strategy_type
        FROM sweep_best_selections
        WHERE strategy_type IS NOT NULL
        ORDER BY 1
    """
    )

    # 3. Update strategy_sweep_results table
    # 3a. Add strategy_type_id column (nullable initially)
    op.add_column(
        "strategy_sweep_results",
        sa.Column("strategy_type_id", sa.Integer, nullable=True, index=True),
    )

    # 3b. Populate strategy_type_id in strategy_sweep_results
    op.execute(
        """
        UPDATE strategy_sweep_results sr
        SET strategy_type_id = st.id
        FROM strategy_types st
        WHERE sr.strategy_type = st.strategy_type
    """
    )

    # 3c. Make strategy_type_id NOT NULL
    op.alter_column("strategy_sweep_results", "strategy_type_id", nullable=False)

    # 3d. Add foreign key constraint with CASCADE delete
    op.create_foreign_key(
        "fk_strategy_sweep_results_strategy_type_id",
        "strategy_sweep_results",
        "strategy_types",
        ["strategy_type_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 3e. Drop old composite index that uses strategy_type
    op.drop_index(
        "ix_strategy_sweep_ticker_id_strategy", table_name="strategy_sweep_results"
    )

    # 3f. Drop the old strategy_type string column
    op.drop_column("strategy_sweep_results", "strategy_type")

    # 3g. Create new composite index with strategy_type_id
    op.create_index(
        "ix_strategy_sweep_ticker_id_strategy_type_id",
        "strategy_sweep_results",
        ["ticker_id", "strategy_type_id"],
    )

    # 4. Update sweep_best_selections table
    # 4a. Add strategy_type_id column (nullable initially)
    op.add_column(
        "sweep_best_selections",
        sa.Column("strategy_type_id", sa.Integer, nullable=True, index=True),
    )

    # 4b. Populate strategy_type_id in sweep_best_selections
    op.execute(
        """
        UPDATE sweep_best_selections sbs
        SET strategy_type_id = st.id
        FROM strategy_types st
        WHERE sbs.strategy_type = st.strategy_type
    """
    )

    # 4c. Make strategy_type_id NOT NULL
    op.alter_column("sweep_best_selections", "strategy_type_id", nullable=False)

    # 4d. Add foreign key constraint with CASCADE delete
    op.create_foreign_key(
        "fk_sweep_best_selections_strategy_type_id",
        "sweep_best_selections",
        "strategy_types",
        ["strategy_type_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 4e. Drop old constraints and indexes that use strategy_type
    op.drop_constraint(
        "uq_best_selection_per_sweep_ticker_strategy",
        "sweep_best_selections",
        type_="unique",
    )
    op.drop_index("idx_best_selections_composite", table_name="sweep_best_selections")

    # 4f. Drop the old strategy_type string column
    op.drop_column("sweep_best_selections", "strategy_type")

    # 4g. Create new unique constraint with strategy_type_id
    op.create_unique_constraint(
        "uq_best_selection_per_sweep_ticker_strategy_type_id",
        "sweep_best_selections",
        ["sweep_run_id", "ticker_id", "strategy_type_id"],
    )

    # 4h. Create new composite index with strategy_type_id
    op.create_index(
        "idx_best_selections_composite",
        "sweep_best_selections",
        ["sweep_run_id", "ticker_id", "strategy_type_id"],
    )


def downgrade() -> None:
    """Downgrade database schema - revert strategy type normalization."""

    # 1. Restore sweep_best_selections table
    # 1a. Drop new indexes and constraints
    op.drop_index("idx_best_selections_composite", table_name="sweep_best_selections")
    op.drop_constraint(
        "uq_best_selection_per_sweep_ticker_strategy_type_id",
        "sweep_best_selections",
        type_="unique",
    )

    # 1b. Add back strategy_type string column
    op.add_column(
        "sweep_best_selections",
        sa.Column("strategy_type", sa.String(50), nullable=True),
    )

    # 1c. Populate strategy_type from strategy_types table
    op.execute(
        """
        UPDATE sweep_best_selections sbs
        SET strategy_type = st.strategy_type
        FROM strategy_types st
        WHERE sbs.strategy_type_id = st.id
    """
    )

    # 1d. Make strategy_type NOT NULL
    op.alter_column("sweep_best_selections", "strategy_type", nullable=False)

    # 1e. Recreate original indexes and constraints
    op.create_index(
        "idx_best_selections_composite",
        "sweep_best_selections",
        ["sweep_run_id", "ticker_id", "strategy_type"],
    )
    op.create_unique_constraint(
        "uq_best_selection_per_sweep_ticker_strategy",
        "sweep_best_selections",
        ["sweep_run_id", "ticker_id", "strategy_type"],
    )

    # 1f. Drop foreign key constraint and strategy_type_id column
    op.drop_constraint(
        "fk_sweep_best_selections_strategy_type_id",
        "sweep_best_selections",
        type_="foreignkey",
    )
    op.drop_column("sweep_best_selections", "strategy_type_id")

    # 2. Restore strategy_sweep_results table
    # 2a. Drop new composite index
    op.drop_index(
        "ix_strategy_sweep_ticker_id_strategy_type_id",
        table_name="strategy_sweep_results",
    )

    # 2b. Add back strategy_type string column
    op.add_column(
        "strategy_sweep_results",
        sa.Column("strategy_type", sa.String(50), nullable=True),
    )

    # 2c. Populate strategy_type from strategy_types table
    op.execute(
        """
        UPDATE strategy_sweep_results sr
        SET strategy_type = st.strategy_type
        FROM strategy_types st
        WHERE sr.strategy_type_id = st.id
    """
    )

    # 2d. Recreate original composite index
    op.create_index(
        "ix_strategy_sweep_ticker_id_strategy",
        "strategy_sweep_results",
        ["ticker_id", "strategy_type"],
    )

    # 2e. Drop foreign key constraint and strategy_type_id column
    op.drop_constraint(
        "fk_strategy_sweep_results_strategy_type_id",
        "strategy_sweep_results",
        type_="foreignkey",
    )
    op.drop_column("strategy_sweep_results", "strategy_type_id")

    # 3. Drop strategy_types table
    op.drop_table("strategy_types")
