# Changes Log

### Removed "_CURRENT" Suffix from CSV Filenames

Modified CSV export functionality to remove the "_CURRENT" suffix from filenames for cleaner and more consistent file naming.

#### Files Changed:
1. `app/tools/export_csv.py`
   - Removed "_CURRENT" suffix from `_get_filename_components` function
   - Simplified filename generation while maintaining all other naming conventions
   - Change affects all CSV exports that previously used the "_CURRENT" suffix

#### Key Changes:
- Removed conditional addition of "_CURRENT" suffix
- Maintained all other filename components (date, time, strategy type)
- Simplified file naming while preserving functionality

### Fixed Portfolio Selection Module

Fixed issues in portfolio_selection.py:
- Corrected indentation of sorting logic
- Removed redundant sort call after sort_portfolios
- Improved code structure and readability
- Fixed dictionary syntax for column renaming
- Added clearer section comments

### Consolidated Portfolio Sorting Logic

Created a centralized portfolio sorting function and updated all portfolio-related modules to use it consistently.

#### Files Changed:
1. `app/ema_cross/tools/portfolio_collection.py`
   - Added new `sort_portfolios` function as the central sorting implementation
   - Function handles both DataFrame and List inputs
   - Uses consistent config.get('SORT_BY', 'Total Return [%]') logic
   - Updated `export_best_portfolios` to use the new sorting function

2. `app/ema_cross/tools/filter_portfolios.py`
   - Updated `_prepare_result_df` to use centralized sorting
   - Removed duplicate sorting logic

3. `app/ema_cross/tools/parameter_sensitivity.py`
   - Added import for centralized sorting function
   - Updated `analyze_parameter_sensitivity` to use centralized sorting
   - Removed duplicate sorting logic

4. `app/ema_cross/tools/portfolio_selection.py`
   - Added import for centralized sorting function
   - Updated `get_best_portfolio` to use centralized sorting
   - Removed duplicate sorting logic

#### Key Changes:
- Created a single source of truth for portfolio sorting in `sort_portfolios` function
- Ensured consistent default sorting by 'Total Return [%]'
- Standardized config key usage ('SORT_BY')
- Improved maintainability by centralizing sorting logic
- Added support for both DataFrame and List inputs in sorting function

#### Verification:
All portfolio-related modules now use the same centralized sorting function, ensuring consistent behavior across the application.