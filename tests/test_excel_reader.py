import pandas as pd
import pytest

from dataqual.readers.csv_reader import ReaderError
from dataqual.readers.excel_reader import load_excel


@pytest.fixture
def xlsx_file(tmp_path):
    path = tmp_path / "data.xlsx"
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", None, "Carol"]})
    with pd.ExcelWriter(path) as writer:
        df.to_excel(writer, sheet_name="people", index=False)
        pd.DataFrame({"x": [10, 20]}).to_excel(writer, sheet_name="extra", index=False)
    return str(path)


def test_load_first_sheet_by_default(xlsx_file):
    df = load_excel(xlsx_file)
    assert list(df.columns) == ["id", "name"]
    assert len(df) == 3
    assert df["name"].isna().sum() == 1


def test_load_sheet_by_name_and_index(xlsx_file):
    assert list(load_excel(xlsx_file, sheet="extra").columns) == ["x"]
    assert list(load_excel(xlsx_file, sheet=1).columns) == ["x"]


def test_sheet_not_found(xlsx_file):
    with pytest.raises(ReaderError, match="Sheet not found"):
        load_excel(xlsx_file, sheet="nope")


def test_file_not_found():
    with pytest.raises(ReaderError, match="File not found"):
        load_excel("missing.xlsx")


def test_not_a_workbook(tmp_path):
    path = tmp_path / "fake.xlsx"
    path.write_text("this is not an xlsx file")
    with pytest.raises(ReaderError, match="not a valid .xlsx"):
        load_excel(str(path))
