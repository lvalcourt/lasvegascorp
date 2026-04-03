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

            CREATE TABLE IF NOT EXISTS payment_imports (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                source_hash TEXT,
                uploaded_at TEXT NOT NULL,
                status TEXT NOT NULL,
                row_count INTEGER NOT NULL DEFAULT 0,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS company_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                legal_name TEXT,
                tax_id TEXT,
                address_line1 TEXT,
                address_line2 TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                email TEXT,
                phone TEXT,
                is_default INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS payees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                tax_id TEXT,
                payee_type TEXT NOT NULL DEFAULT 'contractor',
                address_line1 TEXT,
                address_line2 TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                email TEXT,
                phone TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS payer_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER,
                name TEXT NOT NULL,
                tax_id TEXT,
                address_line1 TEXT,
                address_line2 TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                email TEXT,
                phone TEXT,
                is_default INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(company_id) REFERENCES company_profiles(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS payment_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_import_id TEXT NOT NULL,
                payee_id INTEGER NOT NULL,
                payment_date TEXT,
                amount REAL NOT NULL DEFAULT 0,
                category TEXT,
                document_type TEXT,
                reference_number TEXT,
                tax_year INTEGER,
                notes TEXT,
                source_row_json TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY(payment_import_id) REFERENCES payment_imports(id) ON DELETE CASCADE,
                FOREIGN KEY(payee_id) REFERENCES payees(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_payment_imports_uploaded_at ON payment_imports(uploaded_at);
            CREATE INDEX IF NOT EXISTS idx_payment_imports_hash ON payment_imports(source_hash);
            CREATE INDEX IF NOT EXISTS idx_payees_name ON payees(name);
            CREATE INDEX IF NOT EXISTS idx_company_profiles_default ON company_profiles(is_default);
            CREATE INDEX IF NOT EXISTS idx_payment_records_import_id ON payment_records(payment_import_id);
            CREATE INDEX IF NOT EXISTS idx_payment_records_payee_id ON payment_records(payee_id);
            CREATE INDEX IF NOT EXISTS idx_payment_records_tax_year ON payment_records(tax_year);
            CREATE INDEX IF NOT EXISTS idx_payment_records_active ON payment_records(is_active);
            """
        )
        _add_column_if_missing(conn, "imports", "tool_type", "TEXT NOT NULL DEFAULT 'generic'")
        _add_column_if_missing(conn, "imports", "source_hash", "TEXT")
        _add_column_if_missing(conn, "work_entries", "entry_date", "TEXT")
        _add_column_if_missing(conn, "work_entries", "patient_name", "TEXT")
        _add_column_if_missing(conn, "work_entries", "branch", "TEXT")
        _add_column_if_missing(conn, "work_entries", "is_active", "INTEGER NOT NULL DEFAULT 1")
        _add_column_if_missing(conn, "payment_imports", "source_hash", "TEXT")
        _add_column_if_missing(conn, "payment_imports", "notes", "TEXT")
        _add_column_if_missing(conn, "payees", "tax_id", "TEXT")
        _add_column_if_missing(conn, "payees", "payee_type", "TEXT NOT NULL DEFAULT 'contractor'")
        _add_column_if_missing(conn, "payees", "address_line1", "TEXT")
        _add_column_if_missing(conn, "payees", "address_line2", "TEXT")
        _add_column_if_missing(conn, "payees", "city", "TEXT")
        _add_column_if_missing(conn, "payees", "state", "TEXT")
        _add_column_if_missing(conn, "payees", "zip_code", "TEXT")
        _add_column_if_missing(conn, "payees", "email", "TEXT")
        _add_column_if_missing(conn, "payees", "phone", "TEXT")
        _add_column_if_missing(conn, "payees", "created_at", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(conn, "company_profiles", "legal_name", "TEXT")
        _add_column_if_missing(conn, "company_profiles", "tax_id", "TEXT")
        _add_column_if_missing(conn, "company_profiles", "address_line1", "TEXT")
        _add_column_if_missing(conn, "company_profiles", "address_line2", "TEXT")
        _add_column_if_missing(conn, "company_profiles", "city", "TEXT")
        _add_column_if_missing(conn, "company_profiles", "state", "TEXT")
        _add_column_if_missing(conn, "company_profiles", "zip_code", "TEXT")
        _add_column_if_missing(conn, "company_profiles", "email", "TEXT")
        _add_column_if_missing(conn, "company_profiles", "phone", "TEXT")
        _add_column_if_missing(conn, "company_profiles", "is_default", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(conn, "company_profiles", "created_at", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(conn, "company_profiles", "updated_at", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(conn, "payer_profiles", "company_id", "INTEGER")
        _add_column_if_missing(conn, "payer_profiles", "tax_id", "TEXT")
        _add_column_if_missing(conn, "payer_profiles", "address_line1", "TEXT")
        _add_column_if_missing(conn, "payer_profiles", "address_line2", "TEXT")
        _add_column_if_missing(conn, "payer_profiles", "city", "TEXT")
        _add_column_if_missing(conn, "payer_profiles", "state", "TEXT")
        _add_column_if_missing(conn, "payer_profiles", "zip_code", "TEXT")
        _add_column_if_missing(conn, "payer_profiles", "email", "TEXT")
        _add_column_if_missing(conn, "payer_profiles", "phone", "TEXT")
        _add_column_if_missing(conn, "payer_profiles", "is_default", "INTEGER NOT NULL DEFAULT 1")
        _add_column_if_missing(conn, "payer_profiles", "created_at", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(conn, "payer_profiles", "updated_at", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(conn, "payment_records", "category", "TEXT")
        _add_column_if_missing(conn, "payment_records", "document_type", "TEXT")
        _add_column_if_missing(conn, "payment_records", "reference_number", "TEXT")
        _add_column_if_missing(conn, "payment_records", "tax_year", "INTEGER")
        _add_column_if_missing(conn, "payment_records", "notes", "TEXT")
        _add_column_if_missing(conn, "payment_records", "source_row_json", "TEXT")
        _add_column_if_missing(conn, "payment_records", "is_active", "INTEGER NOT NULL DEFAULT 1")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_imports_tool_hash ON imports(tool_type, source_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_work_entries_active ON work_entries(is_active)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_company_profiles_name ON company_profiles(name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_payer_profiles_default ON payer_profiles(is_default)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_payer_profiles_company_id ON payer_profiles(company_id)")
        conn.commit()


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}
