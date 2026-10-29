"""Database connection, configured from the project's `.env` file."""

import os

import psycopg
from dotenv import load_dotenv


def connect(*, readonly: bool = False, dbname: str | None = None) -> psycopg.Connection:
    """A connection to the Drakkar database (`POSTGRES_DB`), or to `dbname` on the same server."""
    load_dotenv()
    options = "-c default_transaction_read_only=on" if readonly else ""
    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=dbname or os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ.get("POSTGRES_PASSWORD"),
        options=options,
    )
