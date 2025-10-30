"""
Sweep results endpoints.

This router provides endpoints for querying detailed strategy sweep results
from the database, complementing the job-based sweep execution endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import APIKey, validate_api_key
from ..models.schemas import (
    BestResultsResponse,
    SweepResultDetail,
    SweepResultsResponse,
    SweepSummaryResponse,
)


router = APIRouter()


@router.get("/", response_model=list[SweepSummaryResponse])
async def list_sweeps(
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(validate_api_key)],
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum number of sweeps to return"),
    ] = 10,
):
    """
    List all sweep runs with summary statistics.

    Returns overview information for each sweep run including:
    - Best result and ticker
    - Result count and statistics
    - Run date
    """
    query = text(
        """
        SELECT
            sweep_run_id::text,
            run_date,
            result_count,
            ticker_count,
            strategy_count,
            avg_score,
            max_score,
            median_score,
            overall_best_ticker,
            overall_best_strategy,
            overall_best_score,
            overall_best_fast,
            overall_best_slow,
            overall_best_sharpe,
            overall_best_return
        FROM v_sweep_run_summary
        ORDER BY run_date DESC
        LIMIT :limit
    """,
    )

    result = await db.execute(query, {"limit": limit})
    rows = result.fetchall()

    return [
        SweepSummaryResponse(
            sweep_run_id=row[0],
            run_date=row[1],
            result_count=row[2],
            ticker_count=row[3],
            strategy_count=row[4],
            avg_score=float(row[5]) if row[5] else None,
            max_score=float(row[6]) if row[6] else None,
            median_score=float(row[7]) if row[7] else None,
            best_ticker=row[8],
            best_strategy=row[9],
            best_score=float(row[10]) if row[10] else None,
            best_fast_period=row[11],
            best_slow_period=row[12],
            best_sharpe_ratio=float(row[13]) if row[13] else None,
            best_total_return_pct=float(row[14]) if row[14] else None,
        )
        for row in rows
    ]


@router.get("/latest", response_model=BestResultsResponse)
async def get_latest_sweep_results(
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(validate_api_key)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of top results to return")
    ] = 10,
):
    """
    Get best results from the most recent sweep run.

    Returns top N performing strategies from the latest sweep,
    useful for quickly seeing current best performers.
    """
    query = text(
        """
        SELECT
            id::text,
            sweep_run_id::text,
            run_date,
            ticker,
            strategy_type,
            fast_period,
            slow_period,
            signal_period,
            score,
            sharpe_ratio,
            sortino_ratio,
            total_return_pct,
            win_rate_pct,
            profit_factor,
            max_drawdown_pct,
            total_trades,
            expectancy_per_trade,
            rank_for_ticker
        FROM v_latest_best_results
        ORDER BY score DESC
        LIMIT :limit
    """,
    )

    result = await db.execute(query, {"limit": limit})
    rows = result.fetchall()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sweep results found",
        )

    # Get sweep run info from first row
    sweep_run_id = rows[0][1]
    run_date = rows[0][2]

    results = [
        SweepResultDetail(
            result_id=row[0],
            ticker=row[3],
            strategy_type=row[4],
            fast_period=row[5],
            slow_period=row[6],
            signal_period=row[7],
            score=float(row[8]) if row[8] else None,
            sharpe_ratio=float(row[9]) if row[9] else None,
            sortino_ratio=float(row[10]) if row[10] else None,
            total_return_pct=float(row[11]) if row[11] else None,
            win_rate_pct=float(row[12]) if row[12] else None,
            profit_factor=float(row[13]) if row[13] else None,
            max_drawdown_pct=float(row[14]) if row[14] else None,
            total_trades=row[15],
            expectancy_per_trade=float(row[16]) if row[16] else None,
            rank_for_ticker=row[17],
        )
        for row in rows
    ]

    return BestResultsResponse(
        sweep_run_id=sweep_run_id,
        run_date=run_date,
        total_results=len(results),
        results=results,
    )


@router.get("/{sweep_run_id}", response_model=SweepResultsResponse)
async def get_sweep_results(
    sweep_run_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(validate_api_key)],
    ticker: Annotated[
        str | None, Query(description="Filter by specific ticker")
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=500, description="Maximum results to return")
    ] = 50,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
):
    """
    Get detailed results for a specific sweep run.

    Returns all backtest results with full metrics for the specified sweep.
    Supports filtering by ticker and pagination.

    Example:
        GET /api/v1/sweeps/{sweep_run_id}?ticker=AAPL&limit=20
    """
    # Build query based on filters
    if ticker:
        query = text(
            """
            SELECT
                sr.id::text,
                t.ticker,
                st.strategy_type,
                sr.fast_period,
                sr.slow_period,
                sr.signal_period,
                sr.score,
                sr.sharpe_ratio,
                sr.sortino_ratio,
                sr.calmar_ratio,
                sr.total_return_pct,
                sr.annualized_return,
                sr.win_rate_pct,
                sr.profit_factor,
                sr.expectancy_per_trade,
                sr.max_drawdown_pct,
                sr.max_drawdown_duration,
                sr.total_trades,
                sr.total_closed_trades,
                sr.trades_per_month,
                sr.avg_trade_duration,
                sr.created_at
            FROM strategy_sweep_results sr
            JOIN tickers t ON sr.ticker_id = t.id
            JOIN strategy_types st ON sr.strategy_type_id = st.id
            WHERE sr.sweep_run_id::text LIKE :sweep_run_id || '%'
              AND t.ticker = :ticker
            ORDER BY sr.score DESC
            LIMIT :limit OFFSET :offset
        """,
        )
        params = {
            "sweep_run_id": sweep_run_id,
            "ticker": ticker,
            "limit": limit,
            "offset": offset,
        }
    else:
        query = text(
            """
            SELECT
                sr.id::text,
                t.ticker,
                st.strategy_type,
                sr.fast_period,
                sr.slow_period,
                sr.signal_period,
                sr.score,
                sr.sharpe_ratio,
                sr.sortino_ratio,
                sr.calmar_ratio,
                sr.total_return_pct,
                sr.annualized_return,
                sr.win_rate_pct,
                sr.profit_factor,
                sr.expectancy_per_trade,
                sr.max_drawdown_pct,
                sr.max_drawdown_duration,
                sr.total_trades,
                sr.total_closed_trades,
                sr.trades_per_month,
                sr.avg_trade_duration,
                sr.created_at
            FROM strategy_sweep_results sr
            JOIN tickers t ON sr.ticker_id = t.id
            JOIN strategy_types st ON sr.strategy_type_id = st.id
            WHERE sr.sweep_run_id::text LIKE :sweep_run_id || '%'
            ORDER BY sr.score DESC
            LIMIT :limit OFFSET :offset
        """,
        )
        params = {"sweep_run_id": sweep_run_id, "limit": limit, "offset": offset}

    result = await db.execute(query, params)
    rows = result.fetchall()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No results found for sweep run {sweep_run_id}",
        )

    # Get total count
    # Note: String concatenation is safe here as it's adding a static clause, not user input
    count_query = text(
        """
        SELECT COUNT(*)
        FROM strategy_sweep_results sr
        JOIN tickers t ON sr.ticker_id = t.id
        WHERE sr.sweep_run_id::text LIKE :sweep_run_id || '%'
        """
        + (" AND t.ticker = :ticker" if ticker else ""),  # nosec B608
    )

    count_result = await db.execute(
        count_query,
        (
            {"sweep_run_id": sweep_run_id, "ticker": ticker}
            if ticker
            else {"sweep_run_id": sweep_run_id}
        ),
    )
    total_count = count_result.scalar()

    results = [
        SweepResultDetail(
            result_id=row[0],
            ticker=row[1],
            strategy_type=row[2],
            fast_period=row[3],
            slow_period=row[4],
            signal_period=row[5],
            score=float(row[6]) if row[6] else None,
            sharpe_ratio=float(row[7]) if row[7] else None,
            sortino_ratio=float(row[8]) if row[8] else None,
            calmar_ratio=float(row[9]) if row[9] else None,
            total_return_pct=float(row[10]) if row[10] else None,
            annualized_return=float(row[11]) if row[11] else None,
            win_rate_pct=float(row[12]) if row[12] else None,
            profit_factor=float(row[13]) if row[13] else None,
            expectancy_per_trade=float(row[14]) if row[14] else None,
            max_drawdown_pct=float(row[15]) if row[15] else None,
            max_drawdown_duration=row[16],
            total_trades=row[17],
            total_closed_trades=row[18],
            trades_per_month=float(row[19]) if row[19] else None,
            avg_trade_duration=row[20],
        )
        for row in rows
    ]

    return SweepResultsResponse(
        sweep_run_id=sweep_run_id,
        total_count=total_count,
        returned_count=len(results),
        offset=offset,
        limit=limit,
        results=results,
    )


@router.get("/{sweep_run_id}/best", response_model=BestResultsResponse)
async def get_best_results_for_sweep(
    sweep_run_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(validate_api_key)],
    ticker: Annotated[
        str | None, Query(description="Filter by specific ticker")
    ] = None,
):
    """
    Get the best result(s) for a specific sweep run.

    Without ticker filter: Returns the single best result across all tickers.
    With ticker filter: Returns the best result for that specific ticker.

    This is the most common query pattern for sweep results.

    Examples:
        GET /api/v1/sweeps/{sweep_run_id}/best
        GET /api/v1/sweeps/{sweep_run_id}/best?ticker=AAPL
    """
    if ticker:
        # Best for specific ticker
        query = text(
            """
            SELECT
                best_result_id::text,
                sweep_run_id::text,
                run_date,
                ticker,
                strategy_type,
                fast_period,
                slow_period,
                signal_period,
                score,
                sharpe_ratio,
                sortino_ratio,
                total_return_pct,
                win_rate_pct,
                profit_factor,
                max_drawdown_pct,
                total_trades,
                expectancy_per_trade
            FROM v_best_by_sweep_and_ticker
            WHERE sweep_run_id::text LIKE :sweep_run_id || '%'
              AND ticker = :ticker
        """,
        )
        params = {"sweep_run_id": sweep_run_id, "ticker": ticker}
    else:
        # Best overall
        query = text(
            """
            SELECT
                overall_best_id::text,
                sweep_run_id::text,
                run_date,
                overall_best_ticker,
                overall_best_strategy,
                overall_best_fast,
                overall_best_slow,
                NULL::integer as signal_period,
                overall_best_score,
                overall_best_sharpe,
                NULL::numeric as sortino_ratio,
                overall_best_return,
                NULL::numeric as win_rate_pct,
                NULL::numeric as profit_factor,
                NULL::numeric as max_drawdown_pct,
                NULL::integer as total_trades,
                NULL::numeric as expectancy_per_trade
            FROM v_best_results_per_sweep
            WHERE sweep_run_id::text LIKE :sweep_run_id || '%'
        """,
        )
        params = {"sweep_run_id": sweep_run_id}

    result = await db.execute(query, params)
    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No results found for sweep run {sweep_run_id}"
            + (f" and ticker {ticker}" if ticker else ""),
        )

    result_detail = SweepResultDetail(
        result_id=row[0],
        ticker=row[3],
        strategy_type=row[4],
        fast_period=row[5],
        slow_period=row[6],
        signal_period=row[7],
        score=float(row[8]) if row[8] else None,
        sharpe_ratio=float(row[9]) if row[9] else None,
        sortino_ratio=float(row[10]) if row[10] else None,
        total_return_pct=float(row[11]) if row[11] else None,
        win_rate_pct=float(row[12]) if row[12] else None,
        profit_factor=float(row[13]) if row[13] else None,
        max_drawdown_pct=float(row[14]) if row[14] else None,
        total_trades=row[15],
        expectancy_per_trade=float(row[16]) if row[16] else None,
    )

    return BestResultsResponse(
        sweep_run_id=row[1],
        run_date=row[2],
        total_results=1,
        results=[result_detail],
    )


@router.get("/{sweep_run_id}/best-per-ticker", response_model=BestResultsResponse)
async def get_best_per_ticker(
    sweep_run_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(validate_api_key)],
):
    """
    Get the best result for each ticker in a sweep run.

    Returns one optimal result per ticker tested in the sweep.
    Useful for comparing best strategies across multiple tickers.

    Example:
        GET /api/v1/sweeps/{sweep_run_id}/best-per-ticker
    """
    query = text(
        """
        SELECT
            best_result_id::text,
            sweep_run_id::text,
            run_date,
            ticker,
            strategy_type,
            fast_period,
            slow_period,
            signal_period,
            score,
            sharpe_ratio,
            sortino_ratio,
            total_return_pct,
            win_rate_pct,
            profit_factor,
            max_drawdown_pct,
            total_trades,
            expectancy_per_trade
        FROM v_best_by_sweep_and_ticker
        WHERE sweep_run_id::text LIKE :sweep_run_id || '%'
        ORDER BY score DESC
    """,
    )

    result = await db.execute(query, {"sweep_run_id": sweep_run_id})
    rows = result.fetchall()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No results found for sweep run {sweep_run_id}",
        )

    results = [
        SweepResultDetail(
            result_id=row[0],
            ticker=row[3],
            strategy_type=row[4],
            fast_period=row[5],
            slow_period=row[6],
            signal_period=row[7],
            score=float(row[8]) if row[8] else None,
            sharpe_ratio=float(row[9]) if row[9] else None,
            sortino_ratio=float(row[10]) if row[10] else None,
            total_return_pct=float(row[11]) if row[11] else None,
            win_rate_pct=float(row[12]) if row[12] else None,
            profit_factor=float(row[13]) if row[13] else None,
            max_drawdown_pct=float(row[14]) if row[14] else None,
            total_trades=row[15],
            expectancy_per_trade=float(row[16]) if row[16] else None,
        )
        for row in rows
    ]

    return BestResultsResponse(
        sweep_run_id=rows[0][1],
        run_date=rows[0][2],
        total_results=len(results),
        results=results,
    )
