"""Tiny, safe SQLite schema patcher.

This project started without migrations. When we add new columns, existing
SQLite databases won't automatically update.

We keep this minimal: add missing columns with ALTER TABLE and (optionally)
create helpful indexes.
"""

from __future__ import annotations

from typing import Iterable, Tuple

from ..extensions import db


def _sqlite_has_column(table: str, column: str) -> bool:
    rows = db.session.execute(db.text(f"PRAGMA table_info(\"{table}\")")).all()
    return any(r[1] == column for r in rows)  # r[1] is column name


def _sqlite_add_column(table: str, ddl_fragment: str) -> None:
    # ddl_fragment like: 'email VARCHAR(255)'
    db.session.execute(db.text(f"ALTER TABLE \"{table}\" ADD COLUMN {ddl_fragment}"))


def ensure_sqlite_schema() -> None:
    """Ensure required columns exist for SQLite DBs.

    Safe to run multiple times.
    """

    if db.engine.url.drivername != "sqlite":
        return

    # (table, column, ddl_fragment)
    needed: Iterable[Tuple[str, str, str]] = [
        ("user", "email", "email VARCHAR(255)"),

        ("exercise", "level", "level VARCHAR(32)"),
        ("exercise", "require_if", "require_if BOOLEAN DEFAULT 0"),
        ("exercise", "require_else", "require_else BOOLEAN DEFAULT 0"),
        ("exercise", "allow_elif", "allow_elif BOOLEAN DEFAULT 1"),
        ("exercise", "require_for", "require_for BOOLEAN DEFAULT 0"),
        ("exercise", "require_while", "require_while BOOLEAN DEFAULT 0"),
        ("exercise", "forbid_for", "forbid_for BOOLEAN DEFAULT 0"),
        ("exercise", "forbid_while", "forbid_while BOOLEAN DEFAULT 0"),
        ("exercise", "require_function", "require_function BOOLEAN DEFAULT 0"),
        ("exercise", "function_name", "function_name VARCHAR(64)"),
        ("exercise", "require_print", "require_print BOOLEAN DEFAULT 0"),
        ("exercise", "forbid_print", "forbid_print BOOLEAN DEFAULT 0"),
        ("exercise", "require_input", "require_input BOOLEAN DEFAULT 0"),
    ]

    for table, col, ddl in needed:
        if not _sqlite_has_column(table, col):
            _sqlite_add_column(table, ddl)

    # helpful index for email uniqueness lookups (won't error if exists)
    db.session.execute(
        db.text("CREATE UNIQUE INDEX IF NOT EXISTS ix_user_email ON user (email)")
    )

    db.session.commit()
