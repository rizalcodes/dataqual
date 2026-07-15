import json

import pandas as pd

from dataqual.checks.duplicates import check_duplicates
from dataqual.checks.missing import check_missing
from dataqual.checks.outliers import check_outliers
from dataqual.checks.types import check_types
from dataqual.report.json_report import generate_json_report


def _generate(df, tmp_path, source="data.csv"):
    out = tmp_path / "report.json"
    text = generate_json_report(
        source,
        check_missing(df),
        check_duplicates(df),
        check_types(df),
        check_outliers(df),
        out,
    )
    return text, out


def test_json_is_valid_and_structured(tmp_path):
    df = pd.DataFrame(
        {
            "id": [1, 2, 2, 4, 100],
            "email": ["a@x.com", None, "b@x.com", "c@x.com", "d@x.com"],
        }
    )
    text, out = _generate(df, tmp_path, source="mydata.csv")
    data = json.loads(text)  # parseable
    assert json.loads(out.read_text(encoding="utf-8")) == data  # file matches

    assert set(data) == {"source", "summary", "missing", "duplicates", "types", "outliers"}
    assert data["source"] == "mydata.csv"
    assert data["summary"]["missing_values"] == 1
    assert isinstance(data["missing"], list)
    assert isinstance(data["duplicates"], dict)

    email_row = next(m for m in data["missing"] if m["column"] == "email")
    assert email_row["missing_count"] == 1
    assert email_row["missing_pct"] == 20.0


def test_json_no_issues(tmp_path):
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    text, _ = _generate(df, tmp_path)
    data = json.loads(text)
    assert data["summary"] == {
        "missing_values": 0,
        "duplicate_rows": 0,
        "type_mismatches": 0,
        "outliers": 0,
    }


def test_json_without_output_path_returns_string_only():
    df = pd.DataFrame({"a": [1, 2, 3]})
    text = generate_json_report(
        "x.csv",
        check_missing(df),
        check_duplicates(df),
        check_types(df),
        check_outliers(df),
    )
    assert json.loads(text)["source"] == "x.csv"
