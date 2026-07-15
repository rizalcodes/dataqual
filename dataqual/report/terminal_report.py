"""Rich terminal report."""

from rich.console import Console
from rich.table import Table

from dataqual.checks.compare import CompareStats
from dataqual.checks.duplicates import DuplicateStats
from dataqual.checks.missing import MissingStats
from dataqual.checks.outliers import OutlierStats
from dataqual.checks.types import TypeStats
from dataqual.config import (
    DUPLICATE_ALERT_THRESHOLD,
    MISSING_ALERT_THRESHOLD,
    OUTLIER_ALERT_THRESHOLD,
    TYPE_MISMATCH_ALERT_THRESHOLD,
)


def _style_for(pct: float, alert_threshold: float) -> str:
    if pct == 0:
        return "green"
    if pct < alert_threshold:
        return "yellow"
    return "red"


def render_missing_report(
    stats: list[MissingStats],
    console: Console | None = None,
    alert_threshold: float = MISSING_ALERT_THRESHOLD,
) -> None:
    """Render missing-value stats as a Rich table."""
    console = console or Console()
    table = Table(title="Missing Values")
    table.add_column("Column Name")
    table.add_column("Missing Count", justify="right")
    table.add_column("Missing %", justify="right")

    for stat in stats:
        style = _style_for(stat.missing_pct, alert_threshold)
        table.add_row(
            stat.column,
            str(stat.missing_count),
            f"{stat.missing_pct:.2f}%",
            style=style,
        )
    console.print(table)


def render_duplicates_report(
    stats: DuplicateStats,
    console: Console | None = None,
    alert_threshold: float = DUPLICATE_ALERT_THRESHOLD,
) -> None:
    """Render duplicate-row stats as a Rich table."""
    console = console or Console()
    scope = ", ".join(stats.key_columns) if stats.key_columns else "full row"
    table = Table(title="Duplicate Rows")
    table.add_column("Scope")
    table.add_column("Duplicate Count", justify="right")
    table.add_column("Duplicate %", justify="right")
    table.add_column("Row Indices")

    indices = ", ".join(str(i) for i in stats.sample_indices)
    if stats.sample_truncated:
        indices += ", …"
    table.add_row(
        scope,
        str(stats.duplicate_count),
        f"{stats.duplicate_pct:.2f}%",
        indices or "—",
        style=_style_for(stats.duplicate_pct, alert_threshold),
    )
    console.print(table)


def render_types_report(
    stats: list[TypeStats],
    console: Console | None = None,
    alert_threshold: float = TYPE_MISMATCH_ALERT_THRESHOLD,
) -> None:
    """Render type-mismatch stats as a Rich table."""
    console = console or Console()
    table = Table(title="Type Mismatches")
    table.add_column("Column Name")
    table.add_column("Inferred Type")
    table.add_column("Mismatch Count", justify="right")
    table.add_column("Mismatch %", justify="right")
    table.add_column("Examples")

    for stat in stats:
        style = _style_for(stat.mismatch_pct, alert_threshold)
        table.add_row(
            stat.column,
            stat.inferred_type,
            str(stat.mismatch_count),
            f"{stat.mismatch_pct:.2f}%",
            ", ".join(stat.examples) or "—",
            style=style,
        )
    console.print(table)


def render_outliers_report(
    stats: list[OutlierStats],
    console: Console | None = None,
    alert_threshold: float = OUTLIER_ALERT_THRESHOLD,
) -> None:
    """Render outlier stats as a Rich table."""
    console = console or Console()
    table = Table(title="Outliers (IQR)")
    table.add_column("Column Name")
    table.add_column("Outlier Count", justify="right")
    table.add_column("Outlier %", justify="right")
    table.add_column("Expected Range")
    table.add_column("Examples")

    if not stats:
        console.print("[dim]Outliers (IQR): no numeric columns to check.[/dim]")
        return

    for stat in stats:
        style = _style_for(stat.outlier_pct, alert_threshold)
        table.add_row(
            stat.column,
            str(stat.outlier_count),
            f"{stat.outlier_pct:.2f}%",
            f"{stat.lower_bound:g} – {stat.upper_bound:g}",
            ", ".join(str(v) for v in stat.examples) or "—",
            style=style,
        )
    console.print(table)


def render_compare_report(stats: CompareStats, console: Console | None = None) -> None:
    """Render dataset diff results as Rich tables."""
    console = console or Console()

    if stats.columns_only_in_first or stats.columns_only_in_second:
        console.print("[yellow]Schema mismatch:[/yellow] comparing shared columns only.")
        if stats.columns_only_in_first:
            console.print(f"  Only in first: {', '.join(stats.columns_only_in_first)}")
        if stats.columns_only_in_second:
            console.print(f"  Only in second: {', '.join(stats.columns_only_in_second)}")

    if stats.by_position:
        console.print(
            "[dim]No --keys given — rows matched by position, not identity. "
            "A changed row may appear as removed+added.[/dim]"
        )

    summary = Table(title="Comparison Summary")
    summary.add_column("Change")
    summary.add_column("Rows", justify="right")
    summary.add_row("Added", str(stats.added_count), style="green" if stats.added_count else "dim")
    summary.add_row("Removed", str(stats.removed_count), style="red" if stats.removed_count else "dim")
    summary.add_row("Changed", str(stats.changed_count), style="yellow" if stats.changed_count else "dim")
    console.print(summary)

    def _sample_table(title: str, rows: list[dict], total: int, style: str) -> None:
        if not rows:
            return
        suffix = f" (showing {len(rows)} of {total})" if total > len(rows) else ""
        table = Table(title=f"{title}{suffix}")
        for col in rows[0]:
            table.add_column(str(col))
        for row in rows:
            table.add_row(*(str(v) if v is not None else "—" for v in row.values()), style=style)
        console.print(table)

    _sample_table("Added Rows", stats.added_samples, stats.added_count, "green")
    _sample_table("Removed Rows", stats.removed_samples, stats.removed_count, "red")

    if stats.changed_samples:
        total = stats.changed_count
        shown = len(stats.changed_samples)
        suffix = f" (showing {shown} of {total})" if total > shown else ""
        key_label = ", ".join(stats.key_columns) if stats.key_columns else "Position"
        table = Table(title=f"Changed Rows{suffix}")
        table.add_column(key_label)
        table.add_column("Column")
        table.add_column("Old Value")
        table.add_column("New Value")
        for row in stats.changed_samples:
            for i, change in enumerate(row.changes):
                table.add_row(
                    row.key if i == 0 else "",
                    change.column,
                    str(change.old) if change.old is not None else "—",
                    str(change.new) if change.new is not None else "—",
                    style="yellow",
                )
        console.print(table)
