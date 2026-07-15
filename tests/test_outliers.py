import pandas as pd

from dataqual.checks.outliers import check_outliers


def test_no_outliers():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
    stats = check_outliers(df)
    assert len(stats) == 1
    assert stats[0].column == "a"
    assert stats[0].outlier_count == 0
    assert stats[0].outlier_pct == 0.0
    assert stats[0].examples == []


def test_clear_outlier_detected():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 100]})
    stats = check_outliers(df)[0]
    assert stats.outlier_count == 1
    assert stats.outlier_pct == 20.0
    assert stats.examples == [100]


def test_non_numeric_columns_skipped():
    df = pd.DataFrame(
        {
            "num": [1, 2, 3, 4, 100],
            "text": ["a", "b", "c", "d", "e"],
            "flag": [True, False, True, False, True],
        }
    )
    stats = check_outliers(df)
    assert [s.column for s in stats] == ["num"]


def test_nan_values_ignored():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0, None, 100.0]})
    stats = check_outliers(df)[0]
    assert stats.outlier_count == 1
    # pct relative to total rows (6), not non-null count
    assert stats.outlier_pct == 16.67
