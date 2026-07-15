"""Duplicate row check."""

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class DuplicateStats:
    total_rows: int
    duplicate_count: int
    duplicate_pct: float
    sample_indices: list[int] = field(default_factory=list)
    sample_truncated: bool = False
    key_columns: list[str] | None = None


def check_duplicates(
    df: pd.DataFrame,
    key_columns: list[str] | None = None,
    max_sample: int = 10,
) -> DuplicateStats:
    """Detect duplicate rows.

    With key_columns, rows are considered duplicates when they match on
    just those columns; otherwise the full row must match. The first
    occurrence is not counted as a duplicate. Rows with a null in any
    key column are excluded from the comparison (a missing value means
    "unknown", not "same value"), but duplicate_pct stays relative to
    the full row count.
    """
    total_rows = len(df)
    candidates = df.dropna(subset=key_columns) if key_columns else df
    duplicated = candidates.duplicated(subset=key_columns, keep="first")
    indices = candidates.index[duplicated].tolist()
    count = len(indices)
    pct = round(count / total_rows * 100, 2) if total_rows else 0.0
    return DuplicateStats(
        total_rows=total_rows,
        duplicate_count=count,
        duplicate_pct=pct,
        sample_indices=indices[:max_sample],
        sample_truncated=count > max_sample,
        key_columns=list(key_columns) if key_columns else None,
    )
