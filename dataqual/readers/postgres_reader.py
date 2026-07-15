"""PostgreSQL loader."""

import re

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ArgumentError, OperationalError, SQLAlchemyError

from dataqual.readers.csv_reader import ReaderError

# schema-qualified identifiers like public.users are allowed
_TABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$")


def load_postgres(
    db_url: str,
    table: str | None = None,
    query: str | None = None,
) -> pd.DataFrame:
    """Load a full table or a custom query result from PostgreSQL.

    Provide exactly one of table or query. Error messages never include
    the connection URL, which may contain a password.
    """
    if (table is None) == (query is None):
        raise ReaderError("Provide exactly one of a table name or a SQL query.")

    if table is not None:
        if not _TABLE_NAME.match(table):
            raise ReaderError(f"Invalid table name: {table}")
        sql = f"SELECT * FROM {table}"  # noqa: S608 — identifier validated above
    else:
        sql = query

    try:
        engine = create_engine(db_url)
    except (ArgumentError, ValueError):
        raise ReaderError(
            "Invalid database URL (expected e.g. postgresql://user:pass@host:5432/dbname)."
        ) from None

    try:
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn)
    except OperationalError as exc:
        raise ReaderError(f"Could not connect to database: {exc.orig}") from None
    except SQLAlchemyError as exc:
        detail = getattr(exc, "orig", None) or exc
        what = f"table '{table}'" if table is not None else "query"
        raise ReaderError(f"Failed to load {what}: {detail}") from None
    finally:
        engine.dispose()
