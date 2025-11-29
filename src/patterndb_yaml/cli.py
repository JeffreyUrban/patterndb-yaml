"""Command-line interface for patterndb-yaml."""

import json
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Optional, TextIO

import typer
import yaml
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table

from . import __version__
from .pattern_generator import generate_from_yaml
from .patterndb_yaml import (
    PatterndbYaml,
)

app = typer.Typer(
    name="patterndb-yaml",
    help="Normalize log lines using pattern-based rules",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
)

console = Console(stderr=True)  # All output to stderr to preserve stdout for data


def version_callback(value: bool) -> None:
    """Print version and exit if --version flag is provided."""
    if value:
        typer.echo(f"patterndb-yaml version {__version__}")
        raise typer.Exit()


def placeholder(stream: TextIO) -> Iterator[str]:
    """Read placeholder from stream

    Args:
        stream: Input stream (file or stdin)

    Yields:
        placeholder
    """
    for _line in stream:
        yield "placeholder"


def validate_arguments(
    stats_format: str,
) -> None:
    """Validate argument combinations and constraints.

    Args:
        stats_format: Statistics output format

    Raises:
        typer.BadParameter: If validation fails with clear message
    """

    # Validate stats format
    valid_formats = {"table", "json"}
    if stats_format not in valid_formats:
        raise typer.BadParameter(
            f"--stats-format must be one of {valid_formats}, got '{stats_format}'"
        )


@app.command()
def main(
    input_file: Optional[Path] = typer.Argument(
        None,
        help="Input file to normalize (reads from stdin if not specified)",
        exists=True,
        dir_okay=False,
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    # Input Format
    rules_file: Path = typer.Option(
        ...,
        "--rules",
        "-r",
        help="Path to normalization rules YAML file",
        rich_help_panel="Input Format",
        exists=True,
        dir_okay=False,
    ),
    # StdErr Control
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress statistics output to stderr",
        rich_help_panel="StdErr Control",
    ),
    progress: bool = typer.Option(
        False,
        "--progress",
        "-p",
        help="Show progress indicator (auto-disabled for pipes)",
        rich_help_panel="StdErr Control",
    ),
    stats_format: str = typer.Option(
        "table",
        "--stats-format",
        help="Statistics output format: 'table' (default, Rich table) or 'json' (machine-readable)",
        rich_help_panel="StdErr Control",
    ),
    explain: bool = typer.Option(
        False,
        "--explain",
        "-e",
        help="Show explanations to stderr for why lines were kept or skipped",
        rich_help_panel="StdErr Control",
    ),
    # XML Generation
    generate_xml: bool = typer.Option(
        False,
        "--generate-xml",
        help="Generate syslog-ng XML from rules file and output to stdout (no processing)",
        rich_help_panel="XML Generation",
    ),
) -> None:
    """
    Normalize log lines using pattern-based transformation rules.

    Reads input lines, applies normalization rules from YAML configuration,
    and outputs normalized lines. Rules can match patterns, extract fields,
    and apply transformations.

    \b
    Quick Start:
        patterndb-yaml --rules rules.yaml input.log > output.log    # Normalize a file
        cat input.log | patterndb-yaml --rules rules.yaml           # Use in pipeline
        patterndb-yaml --rules rules.yaml --generate-xml > out.xml  # Export syslog-ng XML

    \b
    More Examples:
        patterndb-yaml --rules rules.yaml --progress input.log > output.log   # Show progress
        patterndb-yaml --rules rules.yaml --quiet input.log > output.log      # No statistics
        patterndb-yaml --rules examples/normalization_rules.yaml input.log    # Use example rules

    \b
    Documentation:
        https://github.com/JeffreyUrban/patterndb-yaml

    \b
    Report Issues:
        https://github.com/JeffreyUrban/patterndb-yaml/issues
    """
    # Check if running interactively with no input
    if input_file is None and sys.stdin.isatty():
        console.print("[yellow]No input provided.[/yellow]")
        console.print("\n[bold]Usage:[/bold] patterndb-yaml --rules RULES.yaml [FILE]")
        console.print("\n[bold]Examples:[/bold]")
        console.print("  patterndb-yaml --rules rules.yaml input.log > output.log")
        console.print("  cat input.log | patterndb-yaml --rules rules.yaml")
        console.print("  patterndb-yaml --rules rules.yaml --generate-xml > patterns.xml")
        console.print("\n[dim]For full help: patterndb-yaml --help[/dim]")
        raise typer.Exit(0)

    # Validate arguments
    validate_arguments(
        stats_format,
    )

    # Disable progress if outputting to a pipe
    show_progress = progress and sys.stdout.isatty()

    # Handle --generate-xml mode
    if generate_xml:
        try:
            with open(rules_file) as f:
                rules_data = yaml.safe_load(f)
            xml_content = generate_from_yaml(rules_data)
            print(xml_content)
        except typer.Exit:
            raise
        except Exception as e:
            console.print(f"[red]Error generating XML:[/red] {e}")
            raise typer.Exit(1) from e
        raise typer.Exit(0)

    # Create processor
    processor = PatterndbYaml(
        rules_path=rules_file,
        explain=explain,
    )

    try:
        if show_progress:
            # Determine total lines for file input (for determinate progress)
            total_lines = None
            if input_file:
                # Count lines in file for progress bar
                with input_file.open("r") as f:
                    total_lines = sum(1 for _ in f)

            # Create progress display
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
                transient=True,
            ) as progress_bar:
                task = progress_bar.add_task(
                    "Normalizing lines...",
                    total=total_lines,
                )

                def update_progress(line_num: int, lines_unmatched: int) -> None:
                    desc = (
                        f"Normalizing lines... ({line_num} processed, {lines_unmatched} unmatched)"
                    )
                    progress_bar.update(
                        task,
                        completed=line_num,
                        description=desc,
                    )

                # Process with progress
                if input_file:
                    with input_file.open("r") as f:
                        processor.process(f, sys.stdout, progress_callback=update_progress)
                else:
                    processor.process(sys.stdin, sys.stdout, progress_callback=update_progress)
        else:
            # Process without progress
            if input_file:
                with input_file.open("r") as f:
                    processor.process(f, sys.stdout, progress_callback=None)
            else:
                processor.process(sys.stdin, sys.stdout, progress_callback=None)

        # Print stats to stderr unless quiet
        if not quiet:
            if stats_format == "json":
                print_stats_json(processor)
            else:
                print_stats(processor)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        # Flush what we have
        processor.flush(sys.stdout)
        if not quiet:
            if stats_format == "json":
                print_stats_json(processor)
            else:
                console.print("[dim]Partial statistics:[/dim]")
                print_stats(processor)
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


def print_stats(processor: PatterndbYaml) -> None:
    """Print normalization statistics using rich."""
    stats = processor.get_stats()

    if stats["lines_processed"] == 0:
        console.print("[yellow]No lines processed[/yellow]")
        return

    # Create stats table
    table = Table(title="Normalization Statistics", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", justify="right", style="green")

    table.add_row("Lines Processed", f"{stats['lines_processed']:,}")
    table.add_row("Lines Matched", f"{stats['lines_matched']:,}")
    table.add_row("Match Rate", f"{stats['match_rate']:.1%}")

    console.print()
    console.print(table)
    console.print()


def print_stats_json(processor: PatterndbYaml) -> None:
    """Print normalization statistics as JSON to stderr."""
    stats = processor.get_stats()

    output = {
        "statistics": stats,
        "configuration": {
            "rules_path": str(processor.rules_path),
        },
    }

    # Print to stderr (console already configured for stderr)
    print(json.dumps(output, indent=2), file=sys.stderr)


if __name__ == "__main__":
    app()
