from typer.testing import CliRunner

from dataqual.cli import app

runner = CliRunner()

CSV = """id,email,name
1,a@x.com,Alice
2,b@x.com,Bob
3,a@x.com,Alicia
"""


def _write_csv(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text(CSV)
    return str(path)


def test_check_with_valid_keys(tmp_path):
    result = runner.invoke(app, ["check", "--file", _write_csv(tmp_path), "--keys", "email"])
    assert result.exit_code == 0
    assert "email" in result.output  # scope column shows the key
    assert "33.33%" in result.output  # 1 of 3 rows is a duplicate email


def test_check_with_multiple_keys(tmp_path):
    result = runner.invoke(
        app, ["check", "--file", _write_csv(tmp_path), "--keys", "email, name"]
    )
    assert result.exit_code == 0
    assert "0.00%" in result.output  # no row shares both email and name


def test_check_with_unknown_key_column(tmp_path):
    result = runner.invoke(app, ["check", "--file", _write_csv(tmp_path), "--keys", "phone"])
    assert result.exit_code == 1
    assert "phone" in result.output
    assert "not found" in result.output
    assert "KeyError" not in result.output


def test_check_with_nonexistent_config_falls_back(tmp_path):
    result = runner.invoke(
        app, ["check", "--file", _write_csv(tmp_path), "--config", "nonexistent.yaml"]
    )
    assert result.exit_code == 0
    assert "Warning" in result.output
    assert "default thresholds" in result.output
    assert "Missing Values" in result.output  # report still rendered


def test_check_report_json_writes_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["check", "--file", _write_csv(tmp_path), "--report", "json"]
    )
    assert result.exit_code == 0
    assert (tmp_path / "data_report.json").is_file()


def test_check_without_keys_uses_full_row(tmp_path):
    result = runner.invoke(app, ["check", "--file", _write_csv(tmp_path)])
    assert result.exit_code == 0
    assert "full row" in result.output


def test_check_requires_a_source():
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 1
    assert "--file or --db-url" in result.output


def test_check_rejects_both_file_and_db_url(tmp_path):
    result = runner.invoke(
        app,
        ["check", "--file", _write_csv(tmp_path), "--db-url", "postgresql://x@y/z"],
    )
    assert result.exit_code == 1
    assert "exactly one data source" in result.output


def test_check_db_url_requires_table_or_query():
    result = runner.invoke(app, ["check", "--db-url", "postgresql://x@y/z"])
    assert result.exit_code == 1
    assert "--table or --query" in result.output

    result = runner.invoke(
        app,
        ["check", "--db-url", "postgresql://x@y/z", "--table", "t", "--query", "SELECT 1"],
    )
    assert result.exit_code == 1
    assert "--table or --query" in result.output


def test_check_table_without_db_url_rejected(tmp_path):
    result = runner.invoke(
        app, ["check", "--file", _write_csv(tmp_path), "--table", "users"]
    )
    assert result.exit_code == 1
    assert "require --db-url" in result.output


def test_check_unsupported_extension(tmp_path):
    path = tmp_path / "data.parquet"
    path.write_text("x")
    result = runner.invoke(app, ["check", "--file", str(path)])
    assert result.exit_code == 1
    assert "Unsupported file type" in result.output


def test_check_xlsx_with_sheet(tmp_path):
    import pandas as pd

    path = tmp_path / "data.xlsx"
    pd.DataFrame({"a": [1, 2, 2], "b": ["x", None, "y"]}).to_excel(
        path, sheet_name="s1", index=False
    )
    result = runner.invoke(app, ["check", "--file", str(path), "--sheet", "s1"])
    assert result.exit_code == 0
    assert "Missing Values" in result.output
