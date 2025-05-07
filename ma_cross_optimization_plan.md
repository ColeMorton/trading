# Implementation Plan: Optimizing Data Download

Focusing on system modules (`app/ma_cross/1_get_portfolios.py`, `app/strategies/update_portfolios.py` and `app/concurrency/review.py`), to ensure consistency with the broader system architecture and existing patterns.

## Problem Statement
When multiple tickers are defined in CONFIG or USE_SYNTHETIC=True, the system makes redundant calls to download data for each strategy type (SMA, EMA), causing inefficiency and potential API rate limiting issues.

## Solution Overview
Create a centralized data retrieval mechanism that fetches all required ticker data once via a single `yf.download` call per execution at the earliest stage of the workflow. This ensures that the data is cached and exported to CSV before any analysis or processing occurs. Following calls to `app/tools/get_data.py` will naturally use the cached data, enhancing efficiency and reducing redundant API calls.

## SOLID Principles Implementation
- **Single Responsibility Principle**: Each function will have a clear responsibility (e.g., data retrieval, data processing).
- **Open/Closed Principle**: IGNORE: modifying existing code.
- **Liskov Substitution Principle**: The new data retrieval function will maintain the expected input/output contracts.
- **Interface Segregation Principle**: Functions will expose only the necessary interfaces for their specific tasks.
- **Dependency Inversion Principle**: High-level modules will depend on abstractions rather than concrete implementations.

## DRY, KISS, and YAGNI Principles
- **DRY**: Eliminate duplicate data retrieval code by centralizing the logic.
- **KISS**: Maintain clear and straightforward function names and control flow.
- **YAGNI**: Focus on the immediate requirements without adding unnecessary complexity.

## System Integration Considerations
- Ensure consistency with existing modules and error handling practices.
- Support for synthetic tickers will be integrated into the new data retrieval mechanism.

This updated plan emphasizes the importance of early data retrieval and caching/exporting to CSV, aligning with the user's feedback.