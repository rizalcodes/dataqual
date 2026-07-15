"""CSV loader."""

from pathlib import Path

import pandas as pd


class ReaderError(Exception):
    """Raised when a dataset cannot be loaded; message is CLI-friendly."""


def load_csv(path: str) -> pd.DataFrame:
    """Load a CSV file into a DataFrame.

    Raises ReaderError with a clear message if the file is missing,
    empty, or unparseable.
    """
    file = Path(path)
    if not file.is_file():
        raise ReaderError(f"File not found: {path}")
    try:
        return pd.read_csv(file)
    except pd.errors.EmptyDataError:
        raise ReaderError(f"File is empty: {path}") from None
    except pd.errors.ParserError as exc:
        raise ReaderError(f"Could not parse CSV file {path}: {exc}") from None
