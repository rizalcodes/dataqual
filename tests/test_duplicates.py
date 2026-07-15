import pandas as pd

from dataqual.checks.duplicates import check_duplicates


def test_no_duplicates():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    stats = check_duplicates(df)
    assert stats.total_rows == 3
    assert stats.duplicate_count == 0
    assert stats.duplicate_pct == 0.0
    assert stats.sample_indices == []
    assert stats.sample_truncated is False


def test_full_row_duplicates():
    df = pd.DataFrame(
        {
            "a": [1, 2, 1, 2],
            "b": ["x", "y", "x", "y"],
        }
    )
    stats = check_duplicates(df)
    assert stats.duplicate_count == 2
    assert stats.duplicate_pct == 50.0
    assert stats.sample_indices == [2, 3]


def test_key_column_duplicates():
    df = pd.DataFrame(
        {
            "email": ["a@x.com", "b@x.com", "a@x.com"],
            "name": ["Alice", "Bob", "Alicia"],
        }
    )
    assert check_duplicates(df).duplicate_count == 0
    stats = check_duplicates(df, key_columns=["email"])
    assert stats.duplicate_count == 1
    assert stats.sample_indices == [2]
    assert stats.key_columns == ["email"]


def test_null_keys_are_not_duplicates_of_each_other():
    df = pd.DataFrame(
        {
            "email": [None, None, "a@x.com", "a@x.com", None],
            "name": ["Bob", "Carol", "Alice", "Alicia", "Dan"],
        }
    )
    stats = check_duplicates(df, key_columns=["email"])
    # Only the real a@x.com match counts; the three null-email rows don't.
    assert stats.duplicate_count == 1
    assert stats.sample_indices == [3]
    # pct is still relative to all 5 rows, not just the 2 with keys.
    assert stats.duplicate_pct == 20.0


def test_null_in_any_key_column_excludes_row():
    df = pd.DataFrame(
        {
            "email": ["a@x.com", "a@x.com", "a@x.com"],
            "phone": ["123", None, None],
        }
    )
    stats = check_duplicates(df, key_columns=["email", "phone"])
    assert stats.duplicate_count == 0


def test_sample_is_capped():
    df = pd.DataFrame({"a": [1] * 6})
    stats = check_duplicates(df, max_sample=3)
    assert stats.duplicate_count == 5
    assert stats.sample_indices == [1, 2, 3]
    assert stats.sample_truncated is True
