"""A fresh test database per test, copied from a template built once per session.

The template is `schema.sql` and `fixture.sql` (`build_fixture.py`), loaded into
`<POSTGRES_DB>_test_template` on the server of `.env`. Each test gets its own copy,
`<POSTGRES_DB>_test`, so tests can commit.
"""

import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from dotenv import load_dotenv

from drakkar.db import connect

HERE = Path(__file__).parent

# Every connection of the tests, commands included, goes to the test database, never to Drakkar.
load_dotenv()
TEMPLATE = f"{os.environ['POSTGRES_DB']}_test_template"
os.environ["POSTGRES_DB"] = TEMPLATE.removesuffix("_template")


def _admin(sql: str) -> None:
    with connect(dbname="postgres") as conn:
        conn.autocommit = True
        conn.execute(sql)  # type: ignore[arg-type]


@pytest.fixture(scope="session")
def template() -> Iterator[str]:
    name = TEMPLATE
    _admin(f"DROP DATABASE IF EXISTS {name}")
    _admin(f"CREATE DATABASE {name}")
    for path in ("schema.sql", "fixture.sql"):
        subprocess.run(
            [
                "psql",
                "-q",
                "-v",
                "ON_ERROR_STOP=1",
                "-h",
                os.environ["POSTGRES_HOST"],
                "-p",
                os.environ["POSTGRES_PORT"],
                "-U",
                os.environ["POSTGRES_USER"],
                "-d",
                name,
                "-f",
                str(HERE / path),
            ],
            env={**os.environ, "PGPASSWORD": os.environ.get("POSTGRES_PASSWORD", "")},
            check=True,
            capture_output=True,
        )
    yield name
    _admin(f"DROP DATABASE IF EXISTS {name}")


@pytest.fixture
def dbname(template: str) -> Iterator[str]:
    """A fresh copy of the template (`POSTGRES_DB` points to it)."""
    name = os.environ["POSTGRES_DB"]
    _admin(f"DROP DATABASE IF EXISTS {name}")
    _admin(f"CREATE DATABASE {name} TEMPLATE {template}")
    yield name
    _admin(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


@pytest.fixture
def conn(dbname: str) -> Iterator[psycopg.Connection]:
    with connect(dbname=dbname) as conn:
        yield conn
