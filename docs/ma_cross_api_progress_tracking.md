# MA Cross API Progress Tracking Implementation

## Overview

This document describes the progress tracking implementation for the MA Cross API, which provides real-time updates during portfolio analysis via Server-Sent Events (SSE).

## Architecture

### Progress Tracking Components

1. **ProgressTracker Class** (`app/tools/progress_tracking.py`)
   - Tracks operation phases, steps, and messages
   - Calculates progress percentage and elapsed time
   - Supports callback functions for real-time updates
   - Rate-limits updates to prevent excessive messaging

2. **Progress Callback Integration**
   - `create_progress_callback()` creates callbacks that update task status
   - Callbacks update the global `task_status` dictionary
   - SSE endpoints stream these updates to clients

3. **Integration Points**
   - `execute_strategy()` - Top-level strategy execution
   - `process_single_ticker()` - Individual ticker processing
   - `_execute_analysis()` - Service layer coordination

## Usage

### Client-Side SSE Consumption

```python
# Stream progress updates for async analysis
async with httpx.AsyncClient() as client:
    async with client.stream('GET', f'/api/ma-cross/stream/{execution_id}') as response:
        async for line in response.aiter_lines():
            if line.startswith('data: '):
                event_data = json.loads(line[6:])
                progress_details = event_data.get('progress_details', {})
                # Access phase, current_step, total_steps, progress_percentage, etc.
```

### Progress Information Structure

```json
{
  "status": "running",
  "progress": "SMA_analysis: Processing BTC-USD (1/2)",
  "progress_details": {
    "phase": "SMA_analysis",
    "message": "Processing BTC-USD (1/2)",
    "current_step": 1,
    "total_steps": 2,
    "progress_percentage": 50.0,
    "elapsed_time": 3.14,
    "timestamp": "2025-01-28T08:00:00"
  }
}
```

## Progress Phases

1. **Initialization**: Strategy type setup
2. **{Strategy}_analysis**: Processing each strategy type (SMA, EMA)
3. **Portfolio Analysis**: Analyzing portfolios for each ticker
4. **Filtering**: Applying portfolio filters
5. **Export**: Exporting results to CSV
6. **Completed**: Analysis finished

## Benefits

- **Real-time Feedback**: Users see live progress during long-running analyses
- **Granular Updates**: Progress reported at multiple levels (strategy, ticker, phase)
- **Performance Insights**: Elapsed time helps identify bottlenecks
- **Better UX**: Progress percentage and step counts provide clear expectations

## Example Output

```
[08:09:39] Status: running | Phase: initialization | Progress: Filtering portfolios for BTC-USD (0.0%) | Steps: 0/2 (0.0%) | Elapsed: 2.1s
[08:09:40] Status: running | Phase: completed | Progress: Completed SMA analysis for 2 tickers (100.0%) | Steps: 2/2 (100.0%) | Elapsed: 3.9s
```

## Future Enhancements

1. **More Granular Tracking**: Add progress for data download and individual backtest phases
2. **ETA Calculation**: Estimate time remaining based on historical performance
3. **Progress Persistence**: Store progress in database for recovery after crashes
4. **WebSocket Support**: Alternative to SSE for bidirectional communication