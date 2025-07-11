"""Portfolio path resolution utilities."""


def resolve_portfolio_path(portfolio_name: str) -> str:
    """
    Resolve portfolio name to include .csv extension if not present.

    Args:
        portfolio_name: Portfolio filename with or without .csv extension

    Returns:
        Portfolio filename with .csv extension

    Examples:
        >>> resolve_portfolio_path("DAILY")
        "DAILY.csv"
        >>> resolve_portfolio_path("DAILY.csv")
        "DAILY.csv"
        >>> resolve_portfolio_path("risk_on")
        "risk_on.csv"
    """
    if portfolio_name.endswith(".csv"):
        return portfolio_name
    return f"{portfolio_name}.csv"
