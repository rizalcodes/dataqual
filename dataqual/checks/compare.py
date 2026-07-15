"""Dataset comparison (diff) check."""

from dataclasses import dataclass, field

import pandas as pd

_MAX_SAMPLES = 5


class CompareError(Exception):
    """Raised when two datasets cannot be meaningfully compared; CLI-friendly."""


@dataclass
class CellChange:
    column: str
    old: object
    new: object


@dataclass
class ChangedRow:
    key: str  # key value(s), or "row N" in positional mode
    changes: list[CellChange]


@dataclass
class CompareStats:
    added_count: int
    removed_count: int
    changed_count: int
    added_samples: list[dict] = field(default_factory=list)
    removed_samples: list[dict] = field(default_factory=list)
    changed_samples: list[ChangedRow] = field(default_factory=list)
    by_position: bool = False
    key_columns: list[str] | None = None
    columns_only_in_first: list[str] = field(default_factory=list)
    columns_only_in_second: list[str] = field(default_factory=list)


def _values_equal(a, b) -> bool:
    if pd.isna(a) and pd.isna(b):
        return True
    try:
        return bool(a == b)
    except (TypeError, ValueError):
        return False


def _row_dict(row: pd.Series) -> dict:
    return {k: (None if pd.isna(v) else v) for k, v in row.items()}


def _diff_rows(old: pd.Series, new: pd.Series, columns: list[str]) -> list[CellChange]:
    return [
        CellChange(column=c, old=_row_dict(old)[c], new=_row_dict(new)[c])
        for c in columns
        if not _values_equal(old[c], new[c])
    ]


def check_compare(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    key_columns: list[str] | None = None,
) -> CompareStats:
    """Diff two DataFrames: rows added, removed, and changed.

    With key_columns, rows are matched by key across the two datasets
    (key values must be unique and non-null within each dataset).
    WITHOUT key_columns, rows are matched by POSITION: row i of df1 is
    compared to row i of df2, and extra trailing rows count as added or
    removed. Positional matching cannot tell a changed row from a
    removed-plus-added one, so provide keys whenever the data has an
    identifier.

    Columns present in only one dataset are reported (schema mismatch)
    and excluded from the value comparison; only shared columns are
    diffed. Raises CompareError if there are no shared columns, if a key
    column is missing from either dataset, or if keys are not unique.
    """
    cols1, cols2 = list(df1.columns), list(df2.columns)
    shared = [c for c in cols1 if c in cols2]
    only_first = [c for c in cols1 if c not in cols2]
    only_second = [c for c in cols2 if c not in cols1]
    if not shared:
        raise CompareError(
            "The two datasets have no columns in common — nothing to compare. "
            f"First has: {', '.join(cols1)}. Second has: {', '.join(cols2)}."
        )

    if key_columns:
        return _compare_by_keys(df1, df2, key_columns, shared, only_first, only_second)
    return _compare_by_position(df1, df2, shared, only_first, only_second)


def _compare_by_keys(df1, df2, key_columns, shared, only_first, only_second):
    for k in key_columns:
        for label, df in (("first", df1), ("second", df2)):
            if k not in df.columns:
                raise CompareError(f"Key column '{k}' not found in the {label} dataset.")
    for label, df in (("first", df1), ("second", df2)):
        keyed = df.dropna(subset=key_columns)
        if keyed.duplicated(subset=key_columns).any():
            raise CompareError(
                f"Key columns ({', '.join(key_columns)}) are not unique in the "
                f"{label} dataset — cannot match rows reliably. "
                "Use 'check' with --keys to find the duplicates."
            )

    d1 = df1.dropna(subset=key_columns).set_index(key_columns)
    d2 = df2.dropna(subset=key_columns).set_index(key_columns)
    value_cols = [c for c in shared if c not in key_columns]

    removed_keys = d1.index.difference(d2.index)
    added_keys = d2.index.difference(d1.index)
    common_keys = d1.index.intersection(d2.index)

    changed = []
    for key in common_keys:
        diffs = _diff_rows(d1.loc[key], d2.loc[key], value_cols)
        if diffs:
            key_str = ", ".join(str(k) for k in key) if isinstance(key, tuple) else str(key)
            changed.append(ChangedRow(key=key_str, changes=diffs))

    return CompareStats(
        added_count=len(added_keys),
        removed_count=len(removed_keys),
        changed_count=len(changed),
        added_samples=[_row_dict(r) for _, r in d2.loc[added_keys].reset_index().head(_MAX_SAMPLES).iterrows()],
        removed_samples=[_row_dict(r) for _, r in d1.loc[removed_keys].reset_index().head(_MAX_SAMPLES).iterrows()],
        changed_samples=changed[:_MAX_SAMPLES],
        by_position=False,
        key_columns=list(key_columns),
        columns_only_in_first=only_first,
        columns_only_in_second=only_second,
    )


def _compare_by_position(df1, df2, shared, only_first, only_second):
    overlap = min(len(df1), len(df2))
    changed = []
    for i in range(overlap):
        diffs = _diff_rows(df1.iloc[i], df2.iloc[i], shared)
        if diffs:
            changed.append(ChangedRow(key=f"row {i}", changes=diffs))

    removed_rows = df1.iloc[overlap:]
    added_rows = df2.iloc[overlap:]
    return CompareStats(
        added_count=len(added_rows),
        removed_count=len(removed_rows),
        changed_count=len(changed),
        added_samples=[_row_dict(r) for _, r in added_rows.head(_MAX_SAMPLES).iterrows()],
        removed_samples=[_row_dict(r) for _, r in removed_rows.head(_MAX_SAMPLES).iterrows()],
        changed_samples=changed[:_MAX_SAMPLES],
        by_position=True,
        key_columns=None,
        columns_only_in_first=only_first,
        columns_only_in_second=only_second,
    )
