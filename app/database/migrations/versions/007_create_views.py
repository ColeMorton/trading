"""Create database views for strategy analysis.

Revision ID: 007
Revises: 006
Create Date: 2025-10-19

"""

from alembic import op


# revision identifiers
revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all analysis views."""
    
    # Read and execute each view SQL file
    import os
    from pathlib import Path
    
    # Get the path to the sql/views directory
    project_root = Path(__file__).parent.parent.parent.parent.parent
    views_dir = project_root / "sql" / "views"
    
    # Execute view files in order
    view_files = [
        "01_core_operational_views.sql",
        "02_performance_views.sql",
        "03_sweep_analysis_views.sql",
        "04_trade_efficiency_views.sql",
        "05_metric_analysis_views.sql",
    ]
    
    for view_file in view_files:
        view_path = views_dir / view_file
        if view_path.exists():
            with open(view_path, 'r') as f:
                sql = f.read()
                # Execute the SQL (which contains CREATE OR REPLACE VIEW statements)
                op.execute(sql)


def downgrade() -> None:
    """Drop all analysis views."""
    
    # Drop views in reverse order of dependencies
    views_to_drop = [
        # Metric analysis views
        "v_metric_leaders_by_category",
        "v_metric_type_summary",
        "v_strategies_by_metric_type",
        
        # Trade efficiency views
        "v_expectancy_analysis",
        "v_trade_duration_analysis",
        "v_win_rate_analysis",
        "v_trade_efficiency_analysis",
        
        # Sweep analysis views
        "v_sweep_coverage",
        "v_parameter_evolution",
        "v_sweep_comparison",
        "v_sweep_run_summary",
        
        # Performance views
        "v_consistency_analysis",
        "v_parameter_performance_summary",
        "v_risk_adjusted_rankings",
        "v_top_performers_by_ticker",
        
        # Core operational views
        "v_top_10_overall",
        "v_latest_best_results",
        "v_best_results_per_sweep",
        "v_best_by_sweep_and_ticker",
    ]
    
    for view_name in views_to_drop:
        op.execute(f"DROP VIEW IF EXISTS {view_name} CASCADE")

