from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS imports (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                tool_type TEXT NOT NULL DEFAULT 'generic',
                source_hash TEXT,
                uploaded_at TEXT NOT NULL,
                status TEXT NOT NULL,
                row_count INTEGER NOT NULL DEFAULT 0,
                error_count INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS work_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_id TEXT NOT NULL,
                employee_id INTEGER NOT NULL,
                task TEXT,
                entry_date TEXT,
                patient_name TEXT,
                branch TEXT,
                classification TEXT NOT NULL,
                rate REAL NOT NULL DEFAULT 0,
                mileage REAL NOT NULL DEFAULT 0,
                surcharge REAL NOT NULL DEFAULT 0,
                amount REAL NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                row_index INTEGER NOT NULL,
                raw_row_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(import_id) REFERENCES imports(id) ON DELETE CASCADE,
                FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_work_entries_import_id ON work_entries(import_id);
            CREATE INDEX IF NOT EXISTS idx_work_entries_employee_id ON work_entries(employee_id);
            CREATE INDEX IF NOT EXISTS idx_employees_name ON employees(name);
            """
        )
        _add_column_if_missing(conn, "imports", "tool_type", "TEXT NOT NULL DEFAULT 'generic'")
        _add_column_if_missing(conn, "imports", "source_hash", "TEXT")
        _add_column_if_missing(conn, "work_entries", "entry_date", "TEXT")
        _add_column_if_missing(conn, "work_entries", "patient_name", "TEXT")
        _add_column_if_missing(conn, "work_entries", "branch", "TEXT")
        _add_column_if_missing(conn, "work_entries", "is_active", "INTEGER NOT NULL DEFAULT 1")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_imports_tool_hash ON imports(tool_type, source_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_work_entries_active ON work_entries(is_active)")
        conn.commit()


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}
