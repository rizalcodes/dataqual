import pandas as pd

from dataqual.checks.missing import check_missing


def test_no_missing_values():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    stats = check_missing(df)
    assert [s.column for s in stats] == ["a", "b"]
    for stat in stats:
        assert stat.missing_count == 0
        assert stat.missing_pct == 0.0


def test_some_missing_values():
    df = pd.DataFrame(
        {
            "a": [1, None, 3, None],
            "b": ["x", "y", "z", "w"],
            "c": [None, None, None, 4.0],
        }
    )
    stats = {s.column: s for s in check_missing(df)}
    assert stats["a"].missing_count == 2
    assert stats["a"].missing_pct == 50.0
    assert stats["b"].missing_count == 0
    assert stats["b"].missing_pct == 0.0
    assert stats["c"].missing_count == 3
    assert stats["c"].missing_pct == 75.0


def test_percentage_rounding():
    df = pd.DataFrame({"a": [1, None, 3]})
    stats = check_missing(df)
    assert stats[0].missing_pct == 33.33
