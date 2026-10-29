"""Disposable PostgreSQL fixtures used by integration and API tests."""

import os
import sys
from typing import LiteralString

import psycopg
import pytest
from psycopg import sql

from tests.support.postgres import apply_schema, temporary_postgres


@pytest.fixture(scope="session")
def pg():
    with temporary_postgres() as (url, connection):
        os.environ.update(
            DATABASE_URL=url.replace("postgresql://", "postgresql+psycopg://", 1),
            ALLOWED_ORIGINS='["http://localhost:3000"]',
            LOG_FORMAT="text",
            JWT_SECRET="test-only-signing-key-at-least-32-bytes-long",
            COOKIE_SECURE="false",
            REGISTRATION_ENABLED="true",
            AUTH_RATE_LIMIT="10000",
            # Never call a real model with the dev machine's key.
            OPENROUTER_API_KEY="",
        )
        # Settings are cached on first use and the engine is built when
        # app.database.session is imported: both must see the test database.
        from app.config.settings import get_settings

        get_settings.cache_clear()
        assert "app.database.session" not in sys.modules, (
            "app.database.session was imported before the `pg` fixture: its engine "
            "would point at the .env database instead of the test database"
        )
        apply_schema(connection)
        yield connection


@pytest.fixture
def db(pg: psycopg.Connection):
    """Empty every application table, then return a small query helper."""
    tables = pg.execute(
        "SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'chat_app'"
    ).fetchall()
    # Messages forbid TRUNCATE by trigger; replica mode skips triggers for
    # this statement only, on the test superuser's connection.
    pg.execute("SET session_replication_role = replica")
    pg.execute(
        sql.SQL("TRUNCATE {} CASCADE").format(
            sql.SQL(", ").join(sql.Identifier(schema, name) for schema, name in tables)
        )
    )
    pg.execute("RESET session_replication_role")

    def query(statement: LiteralString, params: tuple | dict = ()) -> list[dict]:
        with pg.cursor() as cursor:
            cursor.execute(statement, params)
            if cursor.description is None:
                return []
            names = [column.name for column in cursor.description]
            return [dict(zip(names, row)) for row in cursor.fetchall()]

    return query
