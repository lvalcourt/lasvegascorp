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

            CREATE TABLE IF NOT EXISTS app_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                must_change_password INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                failed_login_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                last_login_at TEXT,
                password_updated_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS app_sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES app_users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS auth_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                actor_user_id INTEGER,
                action TEXT NOT NULL,
                detail TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES app_users(id) ON DELETE SET NULL,
                FOREIGN KEY(actor_user_id) REFERENCES app_users(id) ON DELETE SET NULL
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

            CREATE TABLE IF NOT EXISTS business_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT NOT NULL,
                source_id TEXT,
                payee_id INTEGER,
                company_id INTEGER,
                transaction_type TEXT NOT NULL DEFAULT 'payment',
                status TEXT NOT NULL DEFAULT 'posted',
                transaction_date TEXT,
                due_date TEXT,
                amount REAL NOT NULL DEFAULT 0,
                category TEXT,
                reference_number TEXT,
                document_type TEXT,
                notes TEXT,
                tax_year INTEGER,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(payee_id) REFERENCES payees(id) ON DELETE SET NULL,
                FOREIGN KEY(company_id) REFERENCES company_profiles(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS business_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                kind TEXT NOT NULL DEFAULT 'expense',
                description TEXT,
                color_token TEXT,
                is_default INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS expense_documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                source_hash TEXT,
                uploaded_at TEXT NOT NULL,
                status TEXT NOT NULL,
                linked_transaction_id INTEGER,
                suggested_category TEXT,
                payee_id INTEGER,
                company_id INTEGER,
                notes TEXT
                ,
                FOREIGN KEY(linked_transaction_id) REFERENCES business_transactions(id) ON DELETE SET NULL,
                FOREIGN KEY(payee_id) REFERENCES payees(id) ON DELETE SET NULL,
                FOREIGN KEY(company_id) REFERENCES company_profiles(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_payment_imports_uploaded_at ON payment_imports(uploaded_at);
            CREATE INDEX IF NOT EXISTS idx_payment_imports_hash ON payment_imports(source_hash);
            CREATE INDEX IF NOT EXISTS idx_app_users_email ON app_users(email);
            CREATE INDEX IF NOT EXISTS idx_app_sessions_user_id ON app_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_app_sessions_expires_at ON app_sessions(expires_at);
            CREATE INDEX IF NOT EXISTS idx_auth_audit_log_user_id ON auth_audit_log(user_id);
            CREATE INDEX IF NOT EXISTS idx_payees_name ON payees(name);
            CREATE INDEX IF NOT EXISTS idx_company_profiles_default ON company_profiles(is_default);
            CREATE INDEX IF NOT EXISTS idx_payment_records_import_id ON payment_records(payment_import_id);
            CREATE INDEX IF NOT EXISTS idx_payment_records_payee_id ON payment_records(payee_id);
            CREATE INDEX IF NOT EXISTS idx_payment_records_tax_year ON payment_records(tax_year);
            CREATE INDEX IF NOT EXISTS idx_payment_records_active ON payment_records(is_active);
            CREATE INDEX IF NOT EXISTS idx_business_transactions_payee_id ON business_transactions(payee_id);
            CREATE INDEX IF NOT EXISTS idx_business_transactions_type ON business_transactions(transaction_type);
            CREATE INDEX IF NOT EXISTS idx_business_transactions_date ON business_transactions(transaction_date);
            CREATE INDEX IF NOT EXISTS idx_business_transactions_active ON business_transactions(is_active);
            CREATE INDEX IF NOT EXISTS idx_business_categories_kind ON business_categories(kind);
            CREATE INDEX IF NOT EXISTS idx_expense_documents_uploaded_at ON expense_documents(uploaded_at);
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
        _add_column_if_missing(conn, "app_users", "display_name", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(conn, "app_users", "role", "TEXT NOT NULL DEFAULT 'viewer'")
        _add_column_if_missing(conn, "app_users", "password_hash", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(conn, "app_users", "password_salt", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(conn, "app_users", "must_change_password", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(conn, "app_users", "is_active", "INTEGER NOT NULL DEFAULT 1")
        _add_column_if_missing(conn, "app_users", "failed_login_attempts", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(conn, "app_users", "locked_until", "TEXT")
        _add_column_if_missing(conn, "app_users", "last_login_at", "TEXT")
        _add_column_if_missing(conn, "app_users", "password_updated_at", "TEXT")
        _add_column_if_missing(conn, "app_users", "created_at", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(conn, "app_users", "updated_at", "TEXT NOT NULL DEFAULT ''")
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
        _add_column_if_missing(conn, "business_transactions", "source_id", "TEXT")
        _add_column_if_missing(conn, "business_transactions", "payee_id", "INTEGER")
        _add_column_if_missing(conn, "business_transactions", "company_id", "INTEGER")
        _add_column_if_missing(conn, "business_transactions", "transaction_type", "TEXT NOT NULL DEFAULT 'payment'")
        _add_column_if_missing(conn, "business_transactions", "status", "TEXT NOT NULL DEFAULT 'posted'")
        _add_column_if_missing(conn, "business_transactions", "transaction_date", "TEXT")
        _add_column_if_missing(conn, "business_transactions", "due_date", "TEXT")
        _add_column_if_missing(conn, "business_transactions", "amount", "REAL NOT NULL DEFAULT 0")
        _add_column_if_missing(conn, "business_transactions", "category", "TEXT")
        _add_column_if_missing(conn, "business_transactions", "reference_number", "TEXT")
        _add_column_if_missing(conn, "business_transactions", "document_type", "TEXT")
        _add_column_if_missing(conn, "business_transactions", "notes", "TEXT")
        _add_column_if_missing(conn, "business_transactions", "tax_year", "INTEGER")
        _add_column_if_missing(conn, "business_transactions", "is_active", "INTEGER NOT NULL DEFAULT 1")
        _add_column_if_missing(conn, "business_transactions", "created_at", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(conn, "business_transactions", "updated_at", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(conn, "business_categories", "name", "TEXT")
        _add_column_if_missing(conn, "business_categories", "kind", "TEXT NOT NULL DEFAULT 'expense'")
        _add_column_if_missing(conn, "business_categories", "description", "TEXT")
        _add_column_if_missing(conn, "business_categories", "color_token", "TEXT")
        _add_column_if_missing(conn, "business_categories", "is_default", "INTEGER NOT NULL DEFAULT 0")
        _add_column_if_missing(conn, "business_categories", "created_at", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(conn, "business_categories", "updated_at", "TEXT NOT NULL DEFAULT ''")
        _add_column_if_missing(conn, "expense_documents", "source_hash", "TEXT")
        _add_column_if_missing(conn, "expense_documents", "linked_transaction_id", "INTEGER")
        _add_column_if_missing(conn, "expense_documents", "suggested_category", "TEXT")
        _add_column_if_missing(conn, "expense_documents", "payee_id", "INTEGER")
        _add_column_if_missing(conn, "expense_documents", "company_id", "INTEGER")
        _add_column_if_missing(conn, "expense_documents", "notes", "TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_imports_tool_hash ON imports(tool_type, source_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_work_entries_active ON work_entries(is_active)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_company_profiles_name ON company_profiles(name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_payer_profiles_default ON payer_profiles(is_default)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_payer_profiles_company_id ON payer_profiles(company_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_business_categories_name ON business_categories(name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_expense_documents_linked_transaction_id ON expense_documents(linked_transaction_id)")
        conn.commit()


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}
