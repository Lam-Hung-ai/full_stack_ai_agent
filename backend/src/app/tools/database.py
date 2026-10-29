"""Database development commands: uv run db export | generate | checkpoints.

- export: write db/schema/schema.sql from a database (pg_dump --schema-only).
- generate: write src/app/database/generated_tables.py with sqlacodegen.
- checkpoints: let the pinned LangGraph saver create or migrate its four tables
  in schema `langgraph_checkpoints` (database decisions, phase 4). The saver
  owns that DDL, so it is not part of the application migrations.

Always point these at a database freshly migrated with dbmate, never at a
long-lived dev database (backend/AGENTS.md section 29).
"""

import argparse
import os
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import URL, make_url

BACKEND_DIR = Path(__file__).resolve().parents[3]
APP_SCHEMA = "chat_app"
CHECKPOINT_SCHEMA = "langgraph_checkpoints"


def database_url() -> URL:
    value = os.environ.get("DATABASE_URL") or dotenv_values(BACKEND_DIR / ".env").get(
        "DATABASE_URL"
    )
    if not value:
        raise ValueError("Set DATABASE_URL in the environment or backend/.env")
    url = make_url(value)
    if url.get_backend_name() not in {"postgres", "postgresql"}:
        raise ValueError("DATABASE_URL must be a PostgreSQL URL")
    return url.set(drivername="postgresql+psycopg")


def libpq_url(url: URL) -> str:
    return url.set(drivername="postgresql").render_as_string(hide_password=False)


def generate(url: URL, output: Path) -> None:
    from sqlacodegen.cli import main as codegen

    previous_argv = sys.argv
    try:
        sys.argv = [
            "sqlacodegen",
            url.render_as_string(hide_password=False),
            "--generator",
            "tables",
            "--schemas",
            APP_SCHEMA,
            "--outfile",
            str(output),
        ]
        codegen()
    finally:
        sys.argv = previous_argv

    from sqlalchemy.types import NullType

    metadata = runpy.run_path(str(output))["metadata"]
    if not metadata.tables:
        raise ValueError(f"No tables found in {APP_SCHEMA}; apply migrations first")
    unknown = [
        f"{table.name}.{column.name}"
        for table in metadata.tables.values()
        for column in table.columns
        if isinstance(column.type, NullType)
    ]
    if unknown:
        raise ValueError(f"Unrecognized column types: {', '.join(unknown)}")
    subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--select", "I", "--fix", str(output)],
        check=True,
    )
    subprocess.run([sys.executable, "-m", "ruff", "format", str(output)], check=True)


def export(url: URL, output: Path) -> None:
    env = os.environ.copy()
    if url.password is not None:
        env["PGPASSWORD"] = url.password
    with output.open("w", encoding="utf-8") as stream:
        subprocess.run(
            [
                "pg_dump",
                "--dbname",
                libpq_url(url.set(password=None)),
                "--schema-only",
                "--no-owner",
                "--no-privileges",
                "--no-password",
                # Saver tables belong to the SDK; the empty schema stays.
                f"--exclude-table={CHECKPOINT_SCHEMA}.*",
                "--exclude-table=public.schema_migrations",
            ],
            stdout=stream,
            env=env,
            check=True,
        )


def setup_checkpoints(url: URL) -> None:
    import psycopg
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg.rows import dict_row

    with psycopg.connect(
        libpq_url(url),
        autocommit=True,
        row_factory=dict_row,
        prepare_threshold=0,
        options=f"-csearch_path={CHECKPOINT_SCHEMA},public",
    ) as connection:
        PostgresSaver(connection).setup()  # pyrefly: ignore[bad-argument-type]


def write_output(action: str, url: URL, output: Path, *, clean: bool = False) -> None:
    if clean and action != "export":
        raise ValueError("--clean is only supported for export")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=output.parent, prefix=f".{output.stem}-", suffix=output.suffix, delete=False
    ) as stream:
        temporary = Path(stream.name)
    try:
        (generate if action == "generate" else export)(url, temporary)
        if clean:
            from app.tools.clean_schema import clean_schema

            temporary.write_text(
                clean_schema(temporary.read_text(encoding="utf-8")), encoding="utf-8"
            )
        temporary.chmod(0o644)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["generate", "export", "checkpoints"])
    parser.add_argument("--output", type=Path, help="Override the output path")
    parser.add_argument(
        "--clean", action="store_true", help="Remove dump metadata (export only)"
    )
    args = parser.parse_args()
    if args.clean and args.action != "export":
        parser.error("--clean is only supported for export")
    try:
        url = database_url()
        if args.action == "checkpoints":
            setup_checkpoints(url)
            print(f"✓ Checkpoint tables ready in schema {CHECKPOINT_SCHEMA}")
            return
        output = args.output or (
            BACKEND_DIR / "src/app/database/generated_tables.py"
            if args.action == "generate"
            else BACKEND_DIR.parent / "db/schema/schema.sql"
        )
        write_output(args.action, url, output.resolve(), clean=args.clean)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    print(f"✓ Wrote {output.resolve()}")


if __name__ == "__main__":
    main()
