"""Seasonality analysis command implementations."""

from pathlib import Path
from typing import List, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from app.tools.services.seasonality_expectancy_service import (
    SeasonalityExpectancyService,
)
from app.tools.services.seasonality_service import SeasonalityService

from ..models.seasonality import SeasonalityConfig, SeasonalityExpectancyConfig

# Create seasonality sub-app
app = typer.Typer(
    name="seasonality",
    help="Analyze seasonal patterns in stock price data",
    no_args_is_help=True,
)

console = Console()


@app.command()
def run(
    tickers: Optional[List[str]] = typer.Option(
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
        rprint(f"\n[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command(name="list")
def list_tickers():
    """List available tickers for seasonality analysis."""
    try:
        price_data_dir = Path("data/raw/prices")

        if not price_data_dir.exists():
            rprint("[red]Price data directory not found[/red]")
            raise typer.Exit(1)

        # Get all available tickers
        tickers = []
        for file_path in sorted(price_data_dir.glob("*_D.csv")):
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
        rprint(f"\n[red]Error: {str(e)}[/red]")
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
                    f"  Data range: {data['data_start_date']} to {data['data_end_date']}"
                )
                rprint(f"  Total periods: {data['total_periods']}")
                rprint(f"  Seasonal strength: {data['overall_seasonal_strength']:.3f}")

                if data.get("strongest_pattern"):
                    pattern = data["strongest_pattern"]
                    rprint(f"\n[yellow]Strongest Pattern:[/yellow]")
                    rprint(f"  Type: {pattern['pattern_type']}")
                    rprint(f"  Period: {pattern['period']}")
                    rprint(f"  Average return: {pattern['average_return']:.2f}%")

        else:
            rprint(f"[red]No results found for {ticker}[/red]")
            rprint(f"[dim]Looked for: {csv_file} and {json_file}[/dim]")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"\n[red]Error: {str(e)}[/red]")
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
        rprint(f"\n[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def current(
    tickers: Optional[List[str]] = typer.Option(
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
            f"🔍 [white]Quality Filters: Min samples={min_sample_size}, Min significance={min_significance}[/white]"
        )
        rprint(f"📊 [white]Display: Top {top_n} opportunities[/white]")
        rprint()

        # Run analysis
        service = SeasonalityExpectancyService(config)
        results_df = service.analyze_current_period()

        if results_df.empty:
            rprint(
                "❌ [red]No valid results found. Check data availability and quality filters.[/red]"
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

        rprint(f"\n💡 [bold yellow]Key Insights:[/bold yellow]")
        rprint(
            f"🏆 [white]Best Opportunity: {top_ticker['ticker']} ({top_ticker['expected_return']:+.2f}%)[/white]"
        )
        rprint(f"📊 [white]Average Expected Return: {avg_return:+.2f}%[/white]")
        rprint(
            f"🎯 [white]Win Rate Range: {results_df['win_rate'].min():.1%} - {results_df['win_rate'].max():.1%}[/white]"
        )

    except Exception as e:
        rprint(f"\n[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)


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
