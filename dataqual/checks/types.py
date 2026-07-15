"""Type mismatch check."""

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y")

_MAX_EXAMPLES = 3


@dataclass
class TypeStats:
    column: str
    inferred_type: str
    mismatch_count: int
    mismatch_pct: float
    examples: list[str] = field(default_factory=list)


def _classify(value: str) -> str:
    try:
        float(value)
        return "numeric"
    except ValueError:
        pass
    for fmt in _DATE_FORMATS:
        try:
            datetime.strptime(value, fmt)
            return "date"
        except ValueError:
            continue
    return "string"


def check_types(df: pd.DataFrame) -> list[TypeStats]:
    """Detect per-column type mismatches.

    For text columns, each non-null value is classified as numeric, date,
    or string; the majority classification becomes the inferred type and
    values that don't match it are reported as mismatches (with up to
    three example values). Columns already stored as a concrete dtype
    (numeric, bool, datetime) cannot contain mixed values, and columns
    inferred as plain text accept any value, so both report zero.
    """
    stats = []
    for column in df.columns:
        series = df[column].dropna()
        dtype = df[column].dtype
        # Text columns are `object` on pandas 1/2, the dedicated string
        # dtype on pandas 3 — both can hide mixed value types.
        is_text = pd.api.types.is_object_dtype(dtype) or pd.api.types.is_string_dtype(dtype)
        if not is_text:
            stats.append(
                TypeStats(
                    column=column,
                    inferred_type=str(df[column].dtype),
                    mismatch_count=0,
                    mismatch_pct=0.0,
                )
            )
            continue

        values = series.astype(str)
        kinds = values.map(_classify)
        if kinds.empty:
            stats.append(
                TypeStats(column=column, inferred_type="unknown", mismatch_count=0, mismatch_pct=0.0)
            )
            continue

        inferred = kinds.mode().iloc[0]
        if inferred == "string":
            mismatched = values.iloc[0:0]
        else:
            mismatched = values[kinds != inferred]

        count = len(mismatched)
        pct = round(count / len(values) * 100, 2)
        stats.append(
            TypeStats(
                column=column,
                inferred_type=inferred,
                mismatch_count=count,
                mismatch_pct=pct,
                examples=mismatched.head(_MAX_EXAMPLES).tolist(),
            )
        )
    return stats
