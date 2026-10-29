"""db/schema/schema.sql must be exactly what the repository migrations produce.

The suite bootstraps from schema.sql for speed, so the migration chain runs
nowhere else. This test builds an empty database, lets dbmate apply every
migration, exports it again and compares with the committed file. It catches
migrations that do not apply from scratch, wrong file order, and generated
files exported from a dev database with its own history.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

from sqlalchemy.engine import make_url

from app.tools.database import setup_checkpoints, write_output

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "db/migrations"
SCHEMA_FILE = REPO_ROOT / "db/schema/schema.sql"
CHECK_DATABASE = "migration_drift_check"
SAVER_TABLES = [
    ("checkpoint_blobs",),
    ("checkpoint_migrations",),
    ("checkpoint_writes",),
    ("checkpoints",),
]


def test_every_migration_has_dbmate_markers():
    """Without markers dbmate silently ignores the file's content."""
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    assert files, "no migration found"
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert "-- migrate:up" in text, f"{path.name} lacks '-- migrate:up'"
        assert "-- migrate:down" in text, f"{path.name} lacks '-- migrate:down'"
        # dbmate already wraps each migration in a transaction.
        assert not re.search(r"(?m)^(BEGIN|COMMIT);", text), (
            f"{path.name} opens its own transaction; dbmate already wraps it"
        )


def test_migrations_reproduce_committed_schema(pg, tmp_path):
    dbmate = shutil.which("dbmate")
    assert dbmate, "dbmate is not on PATH; it is the project's migration runner"

    pg.execute(f"DROP DATABASE IF EXISTS {CHECK_DATABASE}")
    pg.execute(f"CREATE DATABASE {CHECK_DATABASE}")
    target = make_url(os.environ["DATABASE_URL"]).set(database=CHECK_DATABASE)
    libpq = target.set(drivername="postgresql").render_as_string(hide_password=False)

    result = subprocess.run(
        [
            dbmate,
            "--url",
            libpq + "?sslmode=disable",
            "--migrations-dir",
            str(MIGRATIONS_DIR),
            # schema.sql is only written by `uv run db export --clean`.
            "--no-dump-schema",
            "up",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"dbmate up failed:\n{result.stdout}\n{result.stderr}"
    )

    # The saver tables are excluded from the export, so creating them must not
    # change the comparison; it also proves the SDK setup works on this schema.
    setup_checkpoints(target)

    exported = tmp_path / "schema.sql"
    write_output("export", target, exported, clean=True)
    assert exported.read_text(encoding="utf-8") == SCHEMA_FILE.read_text(
        encoding="utf-8"
    ), (
        "db/schema/schema.sql differs from applying the migrations. Apply them to a "
        "clean database, then run `uv run db export --clean` and `uv run db "
        "generate`; never hand-edit the generated files."
    )

    import psycopg

    with psycopg.connect(libpq) as connection:
        tables = connection.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'langgraph_checkpoints' ORDER BY 1"
        ).fetchall()
    assert tables == SAVER_TABLES
