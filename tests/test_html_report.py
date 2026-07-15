import pandas as pd

from dataqual.checks.duplicates import check_duplicates
from dataqual.checks.missing import check_missing
from dataqual.checks.outliers import check_outliers
from dataqual.checks.types import check_types
from dataqual.report.html_report import generate_html_report


def _report_for(df, tmp_path, source="data.csv"):
    out = tmp_path / "report.html"
    generate_html_report(
        source,
        check_missing(df),
        check_duplicates(df),
        check_types(df),
        check_outliers(df),
        out,
    )
    return out.read_text(encoding="utf-8")


def test_report_contains_all_sections(tmp_path):
    df = pd.DataFrame(
        {
            "id": [1, 2, 2, 4, 100],
            "email": ["a@x.com", None, "b@x.com", "c@x.com", "d@x.com"],
        }
    )
    html = _report_for(df, tmp_path, source="mydata.csv")
    assert html.startswith("<!DOCTYPE html>")
    for section in ("Missing Values", "Duplicate Rows", "Type Mismatches", "Outliers (IQR)"):
        assert section in html
    assert "mydata.csv" in html
    assert "1 missing value" in html


def test_report_handles_no_issues(tmp_path):
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    html = _report_for(df, tmp_path)
    assert "0 missing values" in html
    assert "0 duplicate rows" in html
    assert 'class="alert"' not in html


def test_report_escapes_html_in_values(tmp_path):
    df = pd.DataFrame({"<script>": ["1", "2", "<b>bad</b>"]})
    html = _report_for(df, tmp_path)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
