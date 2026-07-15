"""Typer commands for dataqual."""

from pathlib import Path

import typer
from rich.console import Console

from dataqual.checks.compare import CompareError, check_compare
from dataqual.checks.duplicates import check_duplicates
from dataqual.checks.missing import check_missing
from dataqual.checks.outliers import check_outliers
from dataqual.checks.types import check_types
from dataqual.config import ConfigError, Thresholds, load_config
from dataqual.readers.csv_reader import ReaderError, load_csv
from dataqual.readers.excel_reader import load_excel
from dataqual.readers.postgres_reader import load_postgres
from dataqual.report.html_report import generate_html_report
from dataqual.report.json_report import generate_json_report
from dataqual.report.terminal_report import (
    render_compare_report,
    render_duplicates_report,
    render_missing_report,
    render_outliers_report,
    render_types_report,
)

app = typer.Typer(help="Audit datasets for quality issues.")
console = Console()

REPORT_FORMATS = ("terminal", "html", "json")


@app.callback()
def main() -> None:
    """dataqual — dataset quality auditing."""


def _load_source(
    file: str | None,
    db_url: str | None,
    sheet: str | None,
    table: str | None,
    query: str | None,
):
    """Validate source options and load the DataFrame; returns (df, source_label).

    Raises ReaderError for anything the user needs to fix.
    """
    if (file is None) == (db_url is None):
        raise ReaderError("Provide exactly one data source: --file or --db-url.")

    if db_url is not None:
        if sheet is not None:
            raise ReaderError("--sheet only applies to .xlsx files.")
        if (table is None) == (query is None):
            raise ReaderError("With --db-url, provide exactly one of --table or --query.")
        label = table if table is not None else "query"
        return load_postgres(db_url, table=table, query=query), label

    if table is not None or query is not None:
        raise ReaderError("--table and --query require --db-url.")

    suffix = Path(file).suffix.lower()
    if suffix == ".csv":
        if sheet is not None:
            raise ReaderError("--sheet only applies to .xlsx files.")
        return load_csv(file), file
    if suffix == ".xlsx":
        sheet_arg: str | int | None = sheet
        if sheet is not None and sheet.isdigit():
            sheet_arg = int(sheet)
        return load_excel(file, sheet=sheet_arg), file
    raise ReaderError(f"Unsupported file type '{suffix or file}': expected .csv or .xlsx.")


@app.command()
def check(
    file: str | None = typer.Option(
        None, "--file", help="Path to the dataset to audit (.csv or .xlsx)."
    ),
    db_url: str | None = typer.Option(
        None,
        "--db-url",
        help="PostgreSQL connection URL (postgresql://user:pass@host:5432/db). "
        "Use with --table or --query instead of --file.",
    ),
    sheet: str | None = typer.Option(
        None, "--sheet", help="Excel sheet name or zero-based index (default: first sheet)."
    ),
    table: str | None = typer.Option(
        None, "--table", help="Database table to audit (requires --db-url)."
    ),
    query: str | None = typer.Option(
        None, "--query", help="SQL query whose result to audit (requires --db-url)."
    ),
    report: str = typer.Option(
        "terminal", "--report", help="Report format: terminal, html, or json."
    ),
    keys: str | None = typer.Option(
        None,
        "--keys",
        help="Comma-separated column names to detect duplicates on "
        "(e.g. --keys \"email,phone\"). Defaults to full-row duplicates.",
    ),
    config: str | None = typer.Option(
        None,
        "--config",
        help="Path to a YAML config file with threshold overrides.",
    ),
) -> None:
    """Run quality checks on a dataset."""
    if report not in REPORT_FORMATS:
        console.print(
            f"[red]Error:[/red] Unknown report format '{report}'. "
            f"Available formats: {', '.join(REPORT_FORMATS)}."
        )
        raise typer.Exit(code=1)

    try:
        thresholds = load_config(config)
    except ConfigError as exc:
        console.print(f"[yellow]Warning:[/yellow] {exc} Using default thresholds.")
        thresholds = Thresholds()

    try:
        df, source = _load_source(file, db_url, sheet, table, query)
    except ReaderError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from None

    key_columns = None
    if keys is not None:
        key_columns = [k.strip() for k in keys.split(",") if k.strip()]
        unknown = [k for k in key_columns if k not in df.columns]
        if unknown:
            console.print(
                f"[red]Error:[/red] Column(s) not found in {source}: "
                f"{', '.join(unknown)}. Available columns: {', '.join(df.columns)}"
            )
            raise typer.Exit(code=1)

    missing = check_missing(df)
    duplicates = check_duplicates(df, key_columns=key_columns)
    types = check_types(df)
    outliers = check_outliers(df)

    stem = Path(file).stem if file is not None else (table or "query")

    if report == "html":
        output = Path.cwd() / f"{stem}_report.html"
        generate_html_report(
            source, missing, duplicates, types, outliers, output, thresholds=thresholds
        )
        console.print(f"HTML report written to [bold]{output}[/bold]")
        return

    if report == "json":
        output = Path.cwd() / f"{stem}_report.json"
        generate_json_report(source, missing, duplicates, types, outliers, output)
        console.print(f"JSON report written to [bold]{output}[/bold]")
        return

    render_missing_report(missing, console=console, alert_threshold=thresholds.missing)
    render_duplicates_report(
        duplicates, console=console, alert_threshold=thresholds.duplicate
    )
    render_types_report(types, console=console, alert_threshold=thresholds.type_mismatch)
    render_outliers_report(outliers, console=console, alert_threshold=thresholds.outlier)


def _load_file(path: str, sheet: str | None = None):
    """Load a .csv or .xlsx file for compare mode (file-based sources only)."""
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return load_csv(path)
    if suffix == ".xlsx":
        sheet_arg: str | int | None = sheet
        if sheet is not None and sheet.isdigit():
            sheet_arg = int(sheet)
        return load_excel(path, sheet=sheet_arg)
    raise ReaderError(f"Unsupported file type '{suffix or path}': expected .csv or .xlsx.")


@app.command()
def compare(
    file1: str = typer.Option(..., "--file1", help="Baseline dataset (.csv or .xlsx)."),
    file2: str = typer.Option(..., "--file2", help="Dataset to compare against it (.csv or .xlsx)."),
    keys: str | None = typer.Option(
        None,
        "--keys",
        help="Comma-separated key column(s) that identify a row across both files "
        "(recommended). Without keys, rows are matched by position.",
    ),
) -> None:
    """Compare two datasets: rows added, removed, and changed."""
    try:
        df1 = _load_file(file1)
        df2 = _load_file(file2)
    except ReaderError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from None

    key_columns = None
    if keys is not None:
        key_columns = [k.strip() for k in keys.split(",") if k.strip()]

    try:
        stats = check_compare(df1, df2, key_columns=key_columns)
    except CompareError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from None

    render_compare_report(stats, console=console)


if __name__ == "__main__":
    app()
