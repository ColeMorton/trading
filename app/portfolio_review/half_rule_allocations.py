def enforce_half_rule_and_normalize(allocations):
    """
    Enforce the rule that the lowest value must be exactly half the highest value
    while preserving the relative ratios between allocations.
    Then normalize to 100%.
    """
    # Find min and max values
    min_ticker = min(allocations, key=allocations.get)
    max_ticker = max(allocations, key=allocations.get)
    min_value = allocations[min_ticker]
    max_value = allocations[max_ticker]
    
    print(f"Original min: {min_ticker} = {min_value}")
    print(f"Original max: {max_ticker} = {max_value}")
    print(f"Current ratio of min/max: {min_value/max_value}")
    
    # To preserve ratios between allocations, we add a constant 'c' where:
    # (min_value + c) / (max_value + c) = 0.5
    # Solving: c = max_value - 2*min_value
    
    c = max_value - 2*min_value
    
    # Apply transformation to all values
    adjusted = {ticker: value + c for ticker, value in allocations.items()}
    
    # Verify the ratio
    new_min = min(adjusted.values())
    new_max = max(adjusted.values())
    new_ratio = new_min / new_max
    
    print(f"Adjusted by adding constant: {c}")
    print(f"After adjustment, min/max ratio: {new_ratio}")
    
    # Normalize to sum to 100%
    total = sum(adjusted.values())
    normalized = {ticker: (value / total) * 100 for ticker, value in adjusted.items()}
    
    # Round to 2 decimal places but ensure sum equals 100%
    # First round down for all to avoid overshooting
    rounded = {ticker: int(value * 100) / 100 for ticker, value in normalized.items()}
    leftover = 100 - sum(rounded.values())
    
    # Distribute the leftover across tickers in order of fractional parts
    fractional_parts = {ticker: value - rounded[ticker] for ticker, value in normalized.items()}
    ordered_tickers = sorted(fractional_parts.keys(), key=fractional_parts.get, reverse=True)
    
    leftover_pennies = round(leftover * 100)
    for i in range(leftover_pennies):
        ticker = ordered_tickers[i % len(ordered_tickers)]
        rounded[ticker] += 0.01
    
    # Ensure final sum is exactly 100
    final_sum = sum(rounded.values())
    if abs(final_sum - 100.0) > 0.001:
        diff = 100.0 - final_sum
        # Add to the largest allocation to minimize impact
        max_ticker = max(rounded, key=rounded.get)
        rounded[max_ticker] = round(rounded[max_ticker] + diff, 2)
    
    return rounded

# Input data
allocations = {
    "COST": 33.75,
    "CRWD": 7.05,
    "EQT": 21.54,
    "GOOGL": 1.3,
    "HSY": 0.77,
    "INTU": 1.06,
    "MCO": 0.22,
    "TSLA": 34.32,
}

# Apply the rule and get final allocations
final_allocations = enforce_half_rule_and_normalize(allocations)

# Print the results in table format
print("\nFinal Allocations:")
print("| Ticker | Final Allocation (%) |")
print("|--------|---------------------|")
for ticker in sorted(final_allocations.keys()):
    print(f"| {ticker} | {final_allocations[ticker]:.2f} |")
print(f"| Total | {sum(final_allocations.values()):.2f} |")

# Verify the final min/max ratio
min_ticker = min(final_allocations, key=final_allocations.get)
max_ticker = max(final_allocations, key=final_allocations.get)
print(f"\nFinal min: {min_ticker} = {final_allocations[min_ticker]}")
print(f"Final max: {max_ticker} = {final_allocations[max_ticker]}")
print(f"Final ratio of min/max: {final_allocations[min_ticker]/final_allocations[max_ticker]}")