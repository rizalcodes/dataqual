"""Missing value check."""

from dataclasses import dataclass

import pandas as pd


@dataclass
class MissingStats:
    column: str
    missing_count: int
    missing_pct: float


def check_missing(df: pd.DataFrame) -> list[MissingStats]:
    """Return missing-value stats (count and percentage) per column."""
    total_rows = len(df)
    stats = []
    for column in df.columns:
        count = int(df[column].isna().sum())
        pct = round(count / total_rows * 100, 2) if total_rows else 0.0
        stats.append(MissingStats(column=column, missing_count=count, missing_pct=pct))
    return stats
