"""Excel (.xlsx) loader."""

from pathlib import Path
from zipfile import BadZipFile

import pandas as pd

from dataqual.readers.csv_reader import ReaderError


def load_excel(path: str, sheet: str | int | None = None) -> pd.DataFrame:
    """Load an .xlsx sheet into a DataFrame.

    sheet may be a name or a zero-based index; defaults to the first sheet.
    Raises ReaderError with a clear message if the file is missing, not a
    valid workbook, the sheet doesn't exist, or the sheet is empty.
    """
    file = Path(path)
    if not file.is_file():
        raise ReaderError(f"File not found: {path}")
    try:
        df = pd.read_excel(file, sheet_name=sheet if sheet is not None else 0, engine="openpyxl")
    except BadZipFile:
        raise ReaderError(f"File is not a valid .xlsx workbook: {path}") from None
    except ValueError as exc:
        # pandas raises ValueError for unknown sheet names/indices
        if "Worksheet" in str(exc) or "sheet" in str(exc).lower():
            raise ReaderError(f"Sheet not found in {path}: {sheet!r}") from None
        raise ReaderError(f"Could not read Excel file {path}: {exc}") from None

    if df.columns.empty:
        raise ReaderError(f"Sheet is empty: {path}" + (f" (sheet {sheet!r})" if sheet is not None else ""))
    return df
