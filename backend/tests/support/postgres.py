"""Disposable PostgreSQL cluster lifecycle for test processes."""

import shutil
import socket
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import LiteralString, cast

import psycopg

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPOSITORY_ROOT / "db/schema/schema.sql"


def _pg_ctl(root: Path, *args: str) -> None:
    # The server inherits stdout/stderr, so redirect them to a real file rather
    # than a pipe that would stay open until PostgreSQL exits.
    with (root / "pg_ctl.log").open("a", encoding="utf-8") as output:
        subprocess.run(
            ["pg_ctl", "-D", str(root / "data"), *args],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=output,
        )


@contextmanager
def temporary_postgres(
    prefix: str = "agent-chat-tests-",
) -> Iterator[tuple[str, psycopg.Connection]]:
    """Start a private cluster on a free localhost port; yield its libpq URL."""
    root = Path(tempfile.mkdtemp(prefix=prefix))
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    subprocess.run(
        [
            "initdb",
            "-D",
            str(root / "data"),
            "-A",
            "trust",
            "-U",
            "tester",
            "--no-locale",
            "--encoding=UTF8",
        ],
        check=True,
        capture_output=True,
    )
    _pg_ctl(
        root,
        "-l",
        str(root / "pg.log"),
        "-o",
        f"-p {port} -h 127.0.0.1 -k {root}",
        "-w",
        "start",
    )
    url = f"postgresql://tester@127.0.0.1:{port}/postgres"
    connection = psycopg.connect(url, autocommit=True)
    try:
        yield url, connection
    finally:
        connection.close()
        _pg_ctl(root, "-m", "immediate", "-w", "stop")
        shutil.rmtree(root, ignore_errors=True)


def apply_schema(connection: psycopg.Connection) -> None:
    """Load the committed schema; the suite never replays the migration chain."""
    # pg_dump orders SQL functions before the tables their bodies read.
    connection.execute("SET check_function_bodies = false")
    schema = SCHEMA_FILE.read_text(encoding="utf-8")
    # A trusted file from the repository, not user input.
    connection.execute(cast(LiteralString, schema))
    connection.execute("RESET check_function_bodies")
    _sync_permissions(connection)


def setup_checkpoints(url: str) -> None:
    """The four saver tables, created by the pinned SDK as `uv run db
    checkpoints` does."""
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg.rows import dict_row

    with psycopg.connect(
        url,
        autocommit=True,
        row_factory=dict_row,
        prepare_threshold=0,
        options="-csearch_path=langgraph_checkpoints,public",
    ) as connection:
        PostgresSaver(connection).setup()  # pyrefly: ignore[bad-argument-type]


def _sync_permissions(connection: psycopg.Connection) -> None:
    """Same catalog `uv run iam sync-permissions` writes (L-04)."""
    from app.modules.authorization.catalog import PERMISSIONS

    with connection.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO chat_app.permissions (resource, action, description) "
            "VALUES (%s, %s, %s) ON CONFLICT (resource, action) DO NOTHING",
            [tuple(item) for item in PERMISSIONS],
        )
