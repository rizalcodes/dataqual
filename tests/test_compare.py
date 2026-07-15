import pandas as pd
import pytest

from dataqual.checks.compare import CompareError, check_compare


def _df(rows):
    return pd.DataFrame(rows)


def test_no_differences():
    df = _df({"id": [1, 2], "name": ["a", "b"]})
    stats = check_compare(df, df.copy(), key_columns=["id"])
    assert stats.added_count == 0
    assert stats.removed_count == 0
    assert stats.changed_count == 0
    assert stats.changed_samples == []


def test_added_rows_only():
    df1 = _df({"id": [1, 2], "name": ["a", "b"]})
    df2 = _df({"id": [1, 2, 3], "name": ["a", "b", "c"]})
    stats = check_compare(df1, df2, key_columns=["id"])
    assert stats.added_count == 1
    assert stats.removed_count == 0
    assert stats.changed_count == 0
    assert stats.added_samples[0]["id"] == 3
    assert stats.added_samples[0]["name"] == "c"


def test_removed_rows_only():
    df1 = _df({"id": [1, 2, 3], "name": ["a", "b", "c"]})
    df2 = _df({"id": [1, 3], "name": ["a", "c"]})
    stats = check_compare(df1, df2, key_columns=["id"])
    assert stats.removed_count == 1
    assert stats.added_count == 0
    assert stats.removed_samples[0]["id"] == 2


def test_changed_values_with_old_and_new():
    df1 = _df({"id": [1, 2], "city": ["Berlin", "Paris"], "age": [30, 40]})
    df2 = _df({"id": [1, 2], "city": ["Berlin", "Rome"], "age": [30, 41]})
    stats = check_compare(df1, df2, key_columns=["id"])
    assert stats.changed_count == 1
    row = stats.changed_samples[0]
    assert row.key == "2"
    changes = {c.column: (c.old, c.new) for c in row.changes}
    assert changes == {"city": ("Paris", "Rome"), "age": (40, 41)}


def test_nan_to_nan_is_not_a_change():
    df1 = _df({"id": [1], "x": [None]})
    df2 = _df({"id": [1], "x": [None]})
    assert check_compare(df1, df2, key_columns=["id"]).changed_count == 0


def test_schema_mismatch_reported_not_crashed():
    df1 = _df({"id": [1], "old_col": ["x"], "shared": [1]})
    df2 = _df({"id": [1], "new_col": ["y"], "shared": [1]})
    stats = check_compare(df1, df2, key_columns=["id"])
    assert stats.columns_only_in_first == ["old_col"]
    assert stats.columns_only_in_second == ["new_col"]
    assert stats.changed_count == 0  # shared columns are equal


def test_no_shared_columns_raises():
    df1 = _df({"a": [1]})
    df2 = _df({"b": [2]})
    with pytest.raises(CompareError, match="no columns in common"):
        check_compare(df1, df2)


def test_missing_key_column_raises():
    df1 = _df({"id": [1], "x": [1]})
    df2 = _df({"x": [1], "y": [2]})
    with pytest.raises(CompareError, match="Key column 'id' not found in the second"):
        check_compare(df1, df2, key_columns=["id"])


def test_non_unique_keys_raise():
    df1 = _df({"id": [1, 1], "x": [1, 2]})
    df2 = _df({"id": [1, 2], "x": [1, 2]})
    with pytest.raises(CompareError, match="not unique in the first"):
        check_compare(df1, df2, key_columns=["id"])


def test_positional_fallback():
    df1 = _df({"x": [1, 2, 3]})
    df2 = _df({"x": [1, 9, 3, 4]})
    stats = check_compare(df1, df2)
    assert stats.by_position is True
    assert stats.changed_count == 1
    assert stats.changed_samples[0].key == "row 1"
    assert stats.changed_samples[0].changes[0].old == 2
    assert stats.changed_samples[0].changes[0].new == 9
    assert stats.added_count == 1
    assert stats.added_samples[0]["x"] == 4
