"""Self-contained HTML report (inline CSS, works offline)."""

from html import escape
from pathlib import Path

from dataqual.checks.duplicates import DuplicateStats
from dataqual.checks.missing import MissingStats
from dataqual.checks.outliers import OutlierStats
from dataqual.checks.types import TypeStats
from dataqual.config import Thresholds

_CSS = """
body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
       margin: 2rem auto; max-width: 60rem; padding: 0 1rem; color: #1a1a2e; }
h1 { font-size: 1.5rem; }
h2 { font-size: 1.15rem; margin-top: 2rem; border-bottom: 2px solid #e0e0e8;
     padding-bottom: 0.3rem; }
p.summary { background: #f4f4f8; padding: 0.8rem 1rem; border-radius: 6px; }
table { border-collapse: collapse; width: 100%; margin-top: 0.8rem; }
th, td { text-align: left; padding: 0.45rem 0.7rem; border-bottom: 1px solid #e0e0e8;
         font-size: 0.92rem; }
th { background: #f4f4f8; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
tr.ok td { background: #eaf7ee; }
tr.warn td { background: #fdf6e3; }
tr.alert td { background: #fdeaea; }
p.none { color: #777; font-style: italic; }
"""


def _row_class(pct: float, alert_threshold: float) -> str:
    if pct == 0:
        return "ok"
    if pct < alert_threshold:
        return "warn"
    return "alert"


def _table(headers: list[str], rows: list[tuple[str, list[str]]]) -> str:
    """Build a table; rows are (css_class, cells). Cells are pre-escaped."""
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = []
    for css, cells in rows:
        tds = "".join(
            f'<td class="num">{c}</td>' if c.endswith("%") or c.isdigit() else f"<td>{c}</td>"
            for c in cells
        )
        body.append(f'<tr class="{css}">{tds}</tr>')
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def generate_html_report(
    source: str,
    missing: list[MissingStats],
    duplicates: DuplicateStats,
    types: list[TypeStats],
    outliers: list[OutlierStats],
    output_path: str | Path,
    thresholds: Thresholds | None = None,
) -> Path:
    """Write a single self-contained HTML report; returns the output path."""
    thresholds = thresholds or Thresholds()
    missing_total = sum(s.missing_count for s in missing)
    mismatch_total = sum(s.mismatch_count for s in types)
    outlier_total = sum(s.outlier_count for s in outliers)
    summary = (
        f"{missing_total} missing value{'s' if missing_total != 1 else ''}, "
        f"{duplicates.duplicate_count} duplicate row{'s' if duplicates.duplicate_count != 1 else ''}, "
        f"{mismatch_total} type mismatch{'es' if mismatch_total != 1 else ''}, "
        f"{outlier_total} outlier{'s' if outlier_total != 1 else ''}"
    )

    missing_table = _table(
        ["Column Name", "Missing Count", "Missing %"],
        [
            (
                _row_class(s.missing_pct, thresholds.missing),
                [escape(s.column), str(s.missing_count), f"{s.missing_pct:.2f}%"],
            )
            for s in missing
        ],
    )

    scope = ", ".join(duplicates.key_columns) if duplicates.key_columns else "full row"
    indices = ", ".join(str(i) for i in duplicates.sample_indices)
    if duplicates.sample_truncated:
        indices += ", …"
    duplicates_table = _table(
        ["Scope", "Duplicate Count", "Duplicate %", "Row Indices"],
        [
            (
                _row_class(duplicates.duplicate_pct, thresholds.duplicate),
                [
                    escape(scope),
                    str(duplicates.duplicate_count),
                    f"{duplicates.duplicate_pct:.2f}%",
                    escape(indices) or "&mdash;",
                ],
            )
        ],
    )

    types_table = _table(
        ["Column Name", "Inferred Type", "Mismatch Count", "Mismatch %", "Examples"],
        [
            (
                _row_class(s.mismatch_pct, thresholds.type_mismatch),
                [
                    escape(s.column),
                    escape(s.inferred_type),
                    str(s.mismatch_count),
                    f"{s.mismatch_pct:.2f}%",
                    escape(", ".join(s.examples)) or "&mdash;",
                ],
            )
            for s in types
        ],
    )

    if outliers:
        outliers_table = _table(
            ["Column Name", "Outlier Count", "Outlier %", "Expected Range", "Examples"],
            [
                (
                    _row_class(s.outlier_pct, thresholds.outlier),
                    [
                        escape(s.column),
                        str(s.outlier_count),
                        f"{s.outlier_pct:.2f}%",
                        f"{s.lower_bound:g} &ndash; {s.upper_bound:g}",
                        escape(", ".join(str(v) for v in s.examples)) or "&mdash;",
                    ],
                )
                for s in outliers
            ],
        )
    else:
        outliers_table = '<p class="none">No numeric columns to check.</p>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>dataqual report — {escape(source)}</title>
<style>{_CSS}</style>
</head>
<body>
<h1>dataqual report</h1>
<p class="summary"><strong>Source:</strong> {escape(source)}<br>
<strong>Summary:</strong> {summary}</p>
<h2>Missing Values</h2>
{missing_table}
<h2>Duplicate Rows</h2>
{duplicates_table}
<h2>Type Mismatches</h2>
{types_table}
<h2>Outliers (IQR)</h2>
{outliers_table}
</body>
</html>
"""
    path = Path(output_path)
    path.write_text(html, encoding="utf-8")
    return path
