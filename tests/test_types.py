import pandas as pd

from dataqual.checks.types import check_types


def test_no_mismatches():
    df = pd.DataFrame({"num": [1, 2, 3], "text": ["x", "y", "z"]})
    stats = {s.column: s for s in check_types(df)}
    assert stats["num"].mismatch_count == 0
    assert stats["num"].mismatch_pct == 0.0
    assert stats["text"].inferred_type == "string"
    assert stats["text"].mismatch_count == 0


def test_numeric_column_with_strings():
    df = pd.DataFrame({"age": ["34", "28", "unknown", "45", "n/a"]})
    stats = check_types(df)[0]
    assert stats.inferred_type == "numeric"
    assert stats.mismatch_count == 2
    assert stats.mismatch_pct == 40.0
    assert sorted(stats.examples) == ["n/a", "unknown"]


def test_date_column_with_bad_values():
    df = pd.DataFrame(
        {"joined": ["2024-01-05", "2024-02-10", "2024-03-15", "not a date"]}
    )
    stats = check_types(df)[0]
    assert stats.inferred_type == "date"
    assert stats.mismatch_count == 1
    assert stats.examples == ["not a date"]


def test_examples_capped_at_three():
    df = pd.DataFrame({"n": ["1", "2", "3", "4", "a", "b", "c", "d"]})
    stats = check_types(df)[0]
    assert stats.inferred_type == "numeric"
    assert stats.mismatch_count == 4
    assert len(stats.examples) == 3
