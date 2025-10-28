"""Seasonality analysis command implementations."""

from pathlib import Path

from rich import print as rprint
from rich.console import Console
from rich.table import Table
import typer

from app.tools.services.portfolio_seasonality_service import PortfolioSeasonalityService
from app.tools.services.seasonality_expectancy_service import (
    SeasonalityExpectancyService,
)
from app.tools.services.seasonality_service import SeasonalityService

from ..models.seasonality import (
    PortfolioSeasonalityConfig,
    SeasonalityConfig,
    SeasonalityExpectancyConfig,
)


# Create seasonality sub-app
app = typer.Typer(
    name="seasonality",
    help="Analyze seasonal patterns in stock price data",
    no_args_is_help=True,
)

console = Console()


@app.command()
def run(
    tickers: list[str] | None = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Specific tickers to analyze (comma-separated or multiple flags)",
    ),
    min_years: float = typer.Option(
        3.0,
        "--min-years",
        "-y",
        help="Minimum years of data required for analysis",
    ),
    time_period: int = typer.Option(
        1,
        "--time-period",
        "-tp",
        help="Number of days for return calculations (1 for daily returns)",
    ),
    confidence_level: float = typer.Option(
        0.95,
        "--confidence-level",
        "-c",
        help="Confidence level for statistical tests (0-1)",
    ),
    output_format: str = typer.Option(
        "csv",
        "--output-format",
        "-f",
        help="Output format (csv or json)",
    ),
    detrend: bool = typer.Option(
        True,
        "--detrend/--no-detrend",
        help="Remove trend before analyzing seasonality",
    ),
    min_sample_size: int = typer.Option(
        10,
        "--min-sample-size",
        "-s",
        help="Minimum sample size for pattern analysis",
    ),
):
    """Run seasonality analysis on stock price data."""
    try:
        # Process ticker input
        ticker_list = None
        if tickers:
            ticker_list = []
            for ticker_arg in tickers:
                # Handle comma-separated values
                ticker_list.extend([t.strip() for t in ticker_arg.split(",")])

        # Create configuration
        config = SeasonalityConfig(
            tickers=ticker_list,
            min_years=min_years,
            time_period_days=time_period,  # Add this line
            confidence_level=confidence_level,
            output_format=output_format,
            detrend_data=detrend,
            min_sample_size=min_sample_size,
        )

        # Display configuration
        rprint("\n[bold cyan]Seasonality Analysis Configuration:[/bold cyan]")
        if ticker_list:
            rprint(f"  Tickers: {', '.join(ticker_list)}")
        else:
            rprint("  Tickers: [yellow]All available[/yellow]")
        rprint(f"  Minimum years: {min_years}")
        rprint(f"  Time period: {time_period} days")  # Add this line
        rprint(f"  Confidence level: {confidence_level}")
        rprint(f"  Output format: {output_format}")
        rprint(f"  Detrend data: {detrend}")
        rprint(f"  Min sample size: {min_sample_size}")
        rprint()

        # Run analysis
        service = SeasonalityService(config)
        results = service.run_analysis()

        # Show completion message
        if results:
            rprint(f"\n[green]✓ Successfully analyzed {len(results)} ticker(s)[/green]")
        else:
            rprint("\n[yellow]No tickers were analyzed[/yellow]")

    except Exception as e:
        rprint(f"\n[red]Error: {e!s}[/red]")
        raise typer.Exit(1)


@app.command(name="list")
def list_tickers():
    """List available tickers for seasonality analysis."""
    try:
        prices_dir = Path("data/raw/prices")

        if not prices_dir.exists():
            rprint("[red]Price data directory not found[/red]")
            raise typer.Exit(1)

        # Get all available tickers
        tickers = []
        for file_path in sorted(prices_dir.glob("*_D.csv")):
            ticker = file_path.stem.replace("_D", "")
            # Get file size and modification time
            stat = file_path.stat()
            size_mb = stat.st_size / (1024 * 1024)
            tickers.append((ticker, size_mb, stat.st_mtime))

        if not tickers:
            rprint("[yellow]No price data files found[/yellow]")
            return

        # Create table
        table = Table(
            title=f"Available Tickers ({len(tickers)} total)",
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("Ticker", style="cyan", no_wrap=True)
        table.add_column("File Size", style="green", justify="right")
        table.add_column("Last Modified", style="yellow")

        # Add rows (show first 50)
        from datetime import datetime

        for ticker, size, mtime in tickers[:50]:
            mod_date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
            table.add_row(ticker, f"{size:.1f} MB", mod_date)

        if len(tickers) > 50:
            table.add_row("...", "...", "...")
            table.add_row(
                f"[dim]({len(tickers) - 50} more)[/dim]",
                "[dim]...[/dim]",
                "[dim]...[/dim]",
            )

        console.print(table)

    except Exception as e:
        rprint(f"\n[red]Error: {e!s}[/red]")
        raise typer.Exit(1)


@app.command()
def results(
    ticker: str = typer.Argument(..., help="Ticker symbol to view results for"),
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format (table or raw)",
    ),
):
    """View seasonality analysis results for a specific ticker."""
    try:
        seasonality_dir = Path("data/raw/seasonality")

        # Check for results file
        csv_file = seasonality_dir / f"{ticker}_seasonality.csv"
        json_file = seasonality_dir / f"{ticker}_seasonality.json"

        if csv_file.exists():
            import pandas as pd

            df = pd.read_csv(csv_file)

            if format == "raw":
                rprint(df.to_string())
            else:
                # Create formatted table
                table = Table(
                    title=f"Seasonality Patterns for {ticker}",
                    show_header=True,
                    header_style="bold magenta",
                )

                table.add_column("Pattern", style="cyan")
                table.add_column("Period", style="white")
                table.add_column("Avg Return", style="green", justify="right")
                table.add_column("Win Rate", style="yellow", justify="right")
                table.add_column("Significance", style="red", justify="right")
                table.add_column("Samples", style="blue", justify="right")

                for _, row in df.iterrows():
                    table.add_row(
                        row["Pattern_Type"],
                        row["Period"],
                        f"{row['Average_Return']:.2f}%",
                        f"{row['Win_Rate']:.2%}",
                        f"{row['Statistical_Significance']:.3f}",
                        str(row["Sample_Size"]),
                    )

                console.print(table)

        elif json_file.exists():
            import json

            with open(json_file) as f:
                data = json.load(f)

            if format == "raw":
                rprint(data)
            else:
                rprint(f"[cyan]Results for {ticker}:[/cyan]")
                rprint(
                    f"  Data range: {data['data_start_date']} to {data['data_end_date']}",
                )
                rprint(f"  Total periods: {data['total_periods']}")
                rprint(f"  Seasonal strength: {data['overall_seasonal_strength']:.3f}")

                if data.get("strongest_pattern"):
                    pattern = data["strongest_pattern"]
                    rprint("\n[yellow]Strongest Pattern:[/yellow]")
                    rprint(f"  Type: {pattern['pattern_type']}")
                    rprint(f"  Period: {pattern['period']}")
                    rprint(f"  Average return: {pattern['average_return']:.2f}%")

        else:
            rprint(f"[red]No results found for {ticker}[/red]")
            rprint(f"[dim]Looked for: {csv_file} and {json_file}[/dim]")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"\n[red]Error: {e!s}[/red]")
        raise typer.Exit(1)


@app.command()
def clean():
    """Clean up seasonality results directory."""
    try:
        seasonality_dir = Path("data/raw/seasonality")

        if not seasonality_dir.exists():
            rprint("[yellow]Seasonality directory does not exist[/yellow]")
            return

        # Count files
        files = list(seasonality_dir.glob("*"))
        if not files:
            rprint("[yellow]No files to clean[/yellow]")
            return

        # Confirm deletion
        if typer.confirm(f"Delete {len(files)} seasonality result file(s)?"):
            for file in files:
                file.unlink()
            rprint(f"[green]✓ Deleted {len(files)} file(s)[/green]")
        else:
            rprint("[yellow]Cleanup cancelled[/yellow]")

    except Exception as e:
        rprint(f"\n[red]Error: {e!s}[/red]")
        raise typer.Exit(1)


@app.command()
def current(
    tickers: list[str] | None = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Specific tickers to analyze (comma-separated or multiple flags)",
    ),
    days: int = typer.Option(
        30,
        "--days",
        "-d",
        help="Number of days for hold period",
    ),
    min_sample_size: int = typer.Option(
        50,
        "--min-sample-size",
        "-s",
        help="Minimum sample size for reliable patterns",
    ),
    min_significance: float = typer.Option(
        0.5,
        "--min-significance",
        "-sig",
        help="Minimum statistical significance threshold (0-1)",
    ),
    top_n: int = typer.Option(
        20,
        "--top-n",
        "-n",
        help="Number of top results to display",
    ),
    no_csv: bool = typer.Option(
        False,
        "--no-csv",
        help="Skip CSV report generation",
    ),
    no_markdown: bool = typer.Option(
        False,
        "--no-markdown",
        help="Skip markdown report generation",
    ),
):
    """Generate current seasonality expectancy analysis for specified hold period."""
    try:
        # Process ticker input
        ticker_list = None
        if tickers:
            ticker_list = []
            for ticker_arg in tickers:
                # Handle comma-separated values
                ticker_list.extend([t.strip() for t in ticker_arg.split(",")])

        # Create configuration
        config = SeasonalityExpectancyConfig(
            tickers=ticker_list,
            days=days,
            min_sample_size=min_sample_size,
            min_significance=min_significance,
            top_n_results=top_n,
            save_csv=not no_csv,
            save_markdown=not no_markdown,
        )

        # Display configuration
        rprint("\n[bold cyan]🎯 Seasonality Expectancy Analysis[/bold cyan]")
        rprint("=" * 50)
        if ticker_list:
            rprint(f"🎯 [white]Tickers: {', '.join(ticker_list)}[/white]")
        else:
            rprint("🎯 [white]Tickers: [yellow]All available[/yellow][/white]")
        rprint(f"📅 [white]Hold Period: {days} days from today[/white]")
        rprint(
            f"🔍 [white]Quality Filters: Min samples={min_sample_size}, Min significance={min_significance}[/white]",
        )
        rprint(f"📊 [white]Display: Top {top_n} opportunities[/white]")
        rprint()

        # Run analysis
        service = SeasonalityExpectancyService(config)
        results_df = service.analyze_current_period()

        if results_df.empty:
            rprint(
                "❌ [red]No valid results found. Check data availability and quality filters.[/red]",
            )
            raise typer.Exit(1)

        # Display results table
        _display_expectancy_results(results_df.head(10))

        # Generate reports
        csv_path = None
        md_path = None

        if config.save_csv:
            csv_path = service.generate_csv_report(results_df)

        if config.save_markdown:
            md_path = service.generate_markdown_report(results_df)

        # Summary
        rprint("\n[bold green]✨ Analysis Complete![/bold green]")
        rprint(f"📈 [cyan]{len(results_df)} tickers analyzed successfully[/cyan]")

        if csv_path:
            rprint(f"📊 [green]Full results: {csv_path.name}[/green]")
        if md_path:
            rprint(f"📝 [green]Summary report: {md_path.name}[/green]")

        # Key insights
        top_ticker = results_df.iloc[0]
        avg_return = results_df["expected_return"].mean()

        rprint("\n💡 [bold yellow]Key Insights:[/bold yellow]")
        rprint(
            f"🏆 [white]Best Opportunity: {top_ticker['ticker']} ({top_ticker['expected_return']:+.2f}%)[/white]",
        )
        rprint(f"📊 [white]Average Expected Return: {avg_return:+.2f}%[/white]")
        rprint(
            f"🎯 [white]Win Rate Range: {results_df['win_rate'].min():.1%} - {results_df['win_rate'].max():.1%}[/white]",
        )

    except Exception as e:
        rprint(f"\n[red]Error: {e!s}[/red]")
        raise typer.Exit(1)


@app.command()
def portfolio(
    portfolio_name: str = typer.Argument(
        ...,
        help="Portfolio filename from data/raw/strategies/ directory",
    ),
    default_time_period: int = typer.Option(
        21,
        "--default-days",
        "-d",
        help="Default time period in days when no signal entry exists",
    ),
    time_period: int | None = typer.Option(
        None,
        "--time-period",
        "-tp",
        help="Override time period for ALL tickers (ignores signal entry and default)",
    ),
    confidence_level: float = typer.Option(
        0.95,
        "--confidence-level",
        "-c",
        help="Confidence level for statistical tests (0-1)",
    ),
    output_format: str = typer.Option(
        "csv",
        "--output-format",
        "-f",
        help="Output format (csv or json)",
    ),
    detrend: bool = typer.Option(
        True,
        "--detrend/--no-detrend",
        help="Remove trend before analyzing seasonality",
    ),
    min_sample_size: int = typer.Option(
        10,
        "--min-sample-size",
        "-s",
        help="Minimum sample size for pattern analysis",
    ),
    include_holidays: bool = typer.Option(
        False,
        "--include-holidays",
        help="Include holiday effect analysis",
    ),
):
    """Run seasonality analysis on all tickers in a portfolio with intelligent time period determination."""
    try:
        # Create configuration
        config = PortfolioSeasonalityConfig(
            portfolio=portfolio_name,
            default_time_period_days=default_time_period,
            time_period_days=time_period,
            confidence_level=confidence_level,
            output_format=output_format,
            detrend_data=detrend,
            min_sample_size=min_sample_size,
            include_holidays=include_holidays,
        )

        # Display initial configuration
        rprint("\n[bold cyan]Portfolio Seasonality Analysis[/bold cyan]")
        rprint(f"  Portfolio: [yellow]{portfolio_name}[/yellow]")
        if time_period is not None:
            rprint(
                f"  [bold red]Time period: {time_period} days (ALL TICKERS)[/bold red]",
            )
        else:
            rprint(f"  Default time period: [green]{default_time_period} days[/green]")
        rprint(f"  Confidence level: {confidence_level}")
        rprint(f"  Output format: {output_format}")
        rprint(f"  Detrend data: {detrend}")
        rprint(f"  Min sample size: {min_sample_size}")
        if include_holidays:
            rprint("  [yellow]Including holiday effects[/yellow]")
        rprint()

        # Run analysis
        service = PortfolioSeasonalityService(config)
        results = service.run_analysis()

        # Display results table
        if results["display_data"]:
            _display_portfolio_results(results["display_data"], portfolio_name)

        # Display summary
        rprint("\n[bold green]✨ Analysis Complete![/bold green]")
        rprint(f"📊 [cyan]Portfolio: {results['portfolio']}[/cyan]")
        rprint(f"🎯 [green]Total tickers: {results['total_tickers']}[/green]")
        rprint(
            f"✅ [green]Successful analyses: {results['successful_analyses']}[/green]",
        )

        # Show any errors
        failed_count = results["total_tickers"] - results["successful_analyses"]
        if failed_count > 0:
            rprint(f"❌ [red]Failed analyses: {failed_count}[/red]")

            # List failed tickers
            failed_tickers = [
                ticker
                for ticker, result in results["ticker_results"].items()
                if "error" in result
            ]
            if failed_tickers:
                rprint(f"   [red]Failed tickers: {', '.join(failed_tickers[:5])}[/red]")
                if len(failed_tickers) > 5:
                    rprint(f"   [red]   ... and {len(failed_tickers) - 5} more[/red]")

        # Show time period breakdown
        override_based = sum(
            1
            for result in results["ticker_results"].values()
            if result.get("analysis_source") == "override"
        )
        signal_based = sum(
            1
            for result in results["ticker_results"].values()
            if result.get("analysis_source") == "signal_entry"
        )
        default_based = sum(
            1
            for result in results["ticker_results"].values()
            if result.get("analysis_source") == "default"
        )

        rprint("\n[bold yellow]📈 Time Period Analysis:[/bold yellow]")
        if override_based > 0:
            rprint(
                f"🎯 [red]{override_based} tickers used OVERRIDE time period ({time_period} days)[/red]",
            )
        else:
            rprint(
                f"🎯 [green]{signal_based} tickers used signal-based time periods[/green]",
            )
            rprint(
                f"⏰ [yellow]{default_based} tickers used default {default_time_period}-day period[/yellow]",
            )

        # Display tickers with positive expectancy
        if results["display_data"]:
            positive_expectancy_tickers = [
                row["ticker"]
                for row in results["display_data"]
                if isinstance(row.get("expectancy"), int | float)
                and row["expectancy"] > 0
            ]

            if positive_expectancy_tickers:
                rprint(
                    f"\n[bold green]✨ Tickers with Positive Expectancy ({len(positive_expectancy_tickers)}):[/bold green]",
                )
                rprint(f"[cyan]{','.join(positive_expectancy_tickers)}[/cyan]")

    except Exception as e:
        rprint(f"\n[red]Error: {e!s}[/red]")
        raise typer.Exit(1)


def _display_portfolio_results(display_data, portfolio_name):
    """Display portfolio seasonality results in a formatted table."""
    if not display_data:
        return

    table = Table(
        title=f"Portfolio Seasonality Analysis: {portfolio_name}",
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Ticker", style="bold white", no_wrap=True)
    table.add_column("Years", style="cyan", justify="right")
    table.add_column("Seasonal Strength", style="yellow", justify="right")
    table.add_column("Best Pattern", style="blue")
    table.add_column("Period", style="white")
    table.add_column("Avg Return", style="green", justify="right")
    table.add_column("Win Rate", style="magenta", justify="right")
    table.add_column("Expectancy", style="bright_green", justify="right")
    table.add_column("Time Period", style="dim", justify="right")

    for row in display_data:
        # Color the average return based on value
        avg_return = row.get("avg_return", "N/A")
        if isinstance(avg_return, int | float):
            return_color = "green" if avg_return > 0 else "red"
            avg_return_str = f"[{return_color}]{avg_return:+.2f}%[/{return_color}]"
        else:
            avg_return_str = str(avg_return)

        # Format win rate
        win_rate = row.get("win_rate", "N/A")
        if isinstance(win_rate, int | float):
            win_rate_str = f"{win_rate:.1%}"
        else:
            win_rate_str = str(win_rate)

        # Format seasonal strength
        seasonal_strength = row.get("seasonal_strength", "N/A")
        if isinstance(seasonal_strength, int | float):
            seasonal_strength_str = f"{seasonal_strength:.3f}"
        else:
            seasonal_strength_str = str(seasonal_strength)

        # Format expectancy
        expectancy = row.get("expectancy", "N/A")
        if isinstance(expectancy, int | float):
            expectancy_color = "bright_green" if expectancy > 0 else "red"
            expectancy_str = (
                f"[{expectancy_color}]{expectancy:+.2f}%[/{expectancy_color}]"
            )
        else:
            expectancy_str = str(expectancy)

        # Format time period with source indicator
        time_period_days = row.get("time_period_days", "N/A")
        analysis_source = row.get("analysis_source", "default")
        if analysis_source == "signal_entry":
            time_period_str = f"{time_period_days}d 🎯"
        else:
            time_period_str = f"{time_period_days}d"

        table.add_row(
            row.get("ticker", "N/A"),
            str(row.get("years", "N/A")),
            seasonal_strength_str,
            row.get("strongest_pattern", "N/A"),
            row.get("period", "N/A"),
            avg_return_str,
            win_rate_str,
            expectancy_str,
            time_period_str,
        )

    console.print(table)


def _display_expectancy_results(results_df):
    """Display expectancy analysis results in a formatted table."""
    if results_df.empty:
        return

    table = Table(
        title="🎯 Top Seasonality Opportunities",
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Rank", style="cyan", no_wrap=True, justify="center")
    table.add_column("Ticker", style="bold white", no_wrap=True)
    table.add_column("Expected Return", style="green", justify="right")
    table.add_column("Asset Class", style="blue")
    table.add_column("Win Rate", style="yellow", justify="right")
    table.add_column("Confidence", style="white")
    table.add_column("Risk Score", style="red", justify="right")

    for _, row in results_df.iterrows():
        # Color expected return based on value
        return_color = "green" if row["expected_return"] > 0 else "red"
        expected_return_str = (
            f"[{return_color}]{row['expected_return']:+.2f}%[/{return_color}]"
        )

        # Color confidence
        conf_colors = {
            "Very High": "bright_green",
            "High": "green",
            "Medium": "yellow",
            "Low": "red",
        }
        conf_color = conf_colors.get(row["confidence"], "white")
        confidence_str = f"[{conf_color}]{row['confidence']}[/{conf_color}]"

        table.add_row(
            str(int(row["rank"])),
            row["ticker"],
            expected_return_str,
            row["asset_class"],
            f"{row['win_rate']:.1%}",
            confidence_str,
            f"{row['risk_adjusted_score']:.3f}",
        )

    console.print(table)
