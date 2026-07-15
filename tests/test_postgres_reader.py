from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError, ProgrammingError

from dataqual.readers.csv_reader import ReaderError
from dataqual.readers.postgres_reader import load_postgres

DB_URL = "postgresql://user:s3cretpw@localhost:5432/mydb"


def test_requires_exactly_one_of_table_or_query():
    with pytest.raises(ReaderError, match="exactly one"):
        load_postgres(DB_URL)
    with pytest.raises(ReaderError, match="exactly one"):
        load_postgres(DB_URL, table="users", query="SELECT 1")


def test_invalid_table_name_rejected():
    with pytest.raises(ReaderError, match="Invalid table name"):
        load_postgres(DB_URL, table="users; DROP TABLE users")


def test_connection_failure_is_clean_and_does_not_leak_password():
    with patch("dataqual.readers.postgres_reader.create_engine") as create_engine:
        engine = MagicMock()
        engine.connect.side_effect = OperationalError(
            "SELECT * FROM users", {}, Exception("connection refused")
        )
        create_engine.return_value = engine
        with pytest.raises(ReaderError) as excinfo:
            load_postgres(DB_URL, table="users")
    message = str(excinfo.value)
    assert "Could not connect" in message
    assert "s3cretpw" not in message
    assert "Traceback" not in message


def test_invalid_query_is_clean():
    with patch("dataqual.readers.postgres_reader.create_engine") as create_engine, patch(
        "dataqual.readers.postgres_reader.pd.read_sql"
    ) as read_sql:
        create_engine.return_value = MagicMock()
        read_sql.side_effect = ProgrammingError(
            "SELEC oops", {}, Exception('syntax error at or near "SELEC"')
        )
        with pytest.raises(ReaderError) as excinfo:
            load_postgres(DB_URL, query="SELEC oops")
    message = str(excinfo.value)
    assert "Failed to load query" in message
    assert "syntax error" in message
    assert "s3cretpw" not in message


def test_missing_table_is_clean():
    with patch("dataqual.readers.postgres_reader.create_engine") as create_engine, patch(
        "dataqual.readers.postgres_reader.pd.read_sql"
    ) as read_sql:
        create_engine.return_value = MagicMock()
        read_sql.side_effect = ProgrammingError(
            "SELECT * FROM ghosts", {}, Exception('relation "ghosts" does not exist')
        )
        with pytest.raises(ReaderError, match="table 'ghosts'"):
            load_postgres(DB_URL, table="ghosts")


def test_invalid_url_message_does_not_echo_url():
    with pytest.raises(ReaderError) as excinfo:
        load_postgres("definitely not a url", table="users")
    assert "s3cret" not in str(excinfo.value)
    assert "Invalid database URL" in str(excinfo.value)
