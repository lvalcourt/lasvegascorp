from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

from core.db import connect


def seed_demo_data(db_path: Path, replace_existing: bool = False) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    current_year = now.year
    previous_year = current_year - 1
    created_at = now.isoformat()

    with connect(db_path) as conn:
        if replace_existing:
            conn.execute("DELETE FROM business_transactions")
            conn.execute("DELETE FROM business_categories")
            conn.execute("DELETE FROM expense_documents")
            conn.execute("DELETE FROM payment_records")
            conn.execute("DELETE FROM payment_imports")
            conn.execute("DELETE FROM payer_profiles")
            conn.execute("DELETE FROM company_profiles")
            conn.execute("DELETE FROM payees")
            conn.execute("DELETE FROM work_entries")
            conn.execute("DELETE FROM imports")
            conn.execute("DELETE FROM employees")

        category_seed = [
            ("Professional Services", "expense", "Service providers and contractors", "emerald", 1),
            ("Clinical Supplies", "expense", "Operational supplies and care materials", "amber", 0),
            ("Travel & Mileage", "expense", "Mileage and travel-related costs", "cyan", 0),
            ("Software & Subscriptions", "expense", "Software tools and subscriptions", "violet", 0),
        ]
        for name, kind, description, color_token, is_default in category_seed:
            existing = conn.execute("SELECT id FROM business_categories WHERE name = ?", (name,)).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE business_categories
                    SET kind = ?, description = ?, color_token = ?, is_default = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (kind, description, color_token, is_default, created_at, existing["id"]),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO business_categories
                    (name, kind, description, color_token, is_default, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (name, kind, description, color_token, is_default, created_at, created_at),
                )

        companies = [
            {
                "name": "TrakinPR",
                "legal_name": "TrakinPR LLC",
                "tax_id": "66-1234567",
                "address_line1": "100 Calle Principal",
                "address_line2": "Suite 300",
                "city": "San Juan",
                "state": "PR",
                "zip_code": "00901",
                "email": "finance@lasvegascorp.com",
                "phone": "787-555-0100",
                "is_default": 1,
            },
            {
                "name": "Autonomy PR",
                "legal_name": "Autonomy PR Services Inc.",
                "tax_id": "66-7654321",
                "address_line1": "55 Avenida Roosevelt",
                "address_line2": "",
                "city": "Hato Rey",
                "state": "PR",
                "zip_code": "00918",
                "email": "ops@autonomypr.com",
                "phone": "787-555-0188",
                "is_default": 0,
            },
        ]
        company_ids: Dict[str, int] = {}
        for company in companies:
            existing = conn.execute("SELECT id FROM company_profiles WHERE name = ?", (company["name"],)).fetchone()
            if existing:
                company_ids[company["name"]] = int(existing["id"])
                conn.execute(
                    """
                    UPDATE company_profiles
                    SET legal_name = ?, tax_id = ?, address_line1 = ?, address_line2 = ?, city = ?, state = ?, zip_code = ?, email = ?, phone = ?, is_default = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        company["legal_name"],
                        company["tax_id"],
                        company["address_line1"],
                        company["address_line2"],
                        company["city"],
                        company["state"],
                        company["zip_code"],
                        company["email"],
                        company["phone"],
                        company["is_default"],
                        created_at,
                        existing["id"],
                    ),
                )
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO company_profiles
                    (name, legal_name, tax_id, address_line1, address_line2, city, state, zip_code, email, phone, is_default, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        company["name"],
                        company["legal_name"],
                        company["tax_id"],
                        company["address_line1"],
                        company["address_line2"],
                        company["city"],
                        company["state"],
                        company["zip_code"],
                        company["email"],
                        company["phone"],
                        company["is_default"],
                        created_at,
                        created_at,
                    ),
                )
                company_ids[company["name"]] = int(cursor.lastrowid)

        conn.execute("UPDATE payer_profiles SET is_default = 0")
        payer_profiles = [
            {
                "company_name": "TrakinPR",
                "name": "TrakinPR - Main Filing",
                "tax_id": "66-1234567",
                "address_line1": "100 Calle Principal",
                "address_line2": "Suite 300",
                "city": "San Juan",
                "state": "PR",
                "zip_code": "00901",
                "email": "finance@lasvegascorp.com",
                "phone": "787-555-0100",
                "is_default": 1,
            },
            {
                "company_name": "Autonomy PR",
                "name": "Autonomy PR - Advisory Division",
                "tax_id": "66-7654321",
                "address_line1": "55 Avenida Roosevelt",
                "address_line2": "",
                "city": "Hato Rey",
                "state": "PR",
                "zip_code": "00918",
                "email": "ops@autonomypr.com",
                "phone": "787-555-0188",
                "is_default": 0,
            },
        ]
        payer_count = 0
        for payer in payer_profiles:
            existing = conn.execute("SELECT id FROM payer_profiles WHERE name = ?", (payer["name"],)).fetchone()
            payload = (
                company_ids[payer["company_name"]],
                payer["name"],
                payer["tax_id"],
                payer["address_line1"],
                payer["address_line2"],
                payer["city"],
                payer["state"],
                payer["zip_code"],
                payer["email"],
                payer["phone"],
                payer["is_default"],
                created_at,
                created_at,
            )
            if existing:
                conn.execute(
                    """
                    UPDATE payer_profiles
                    SET company_id = ?, tax_id = ?, address_line1 = ?, address_line2 = ?, city = ?, state = ?, zip_code = ?, email = ?, phone = ?, is_default = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        company_ids[payer["company_name"]],
                        payer["tax_id"],
                        payer["address_line1"],
                        payer["address_line2"],
                        payer["city"],
                        payer["state"],
                        payer["zip_code"],
                        payer["email"],
                        payer["phone"],
                        payer["is_default"],
                        created_at,
                        existing["id"],
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO payer_profiles
                    (company_id, name, tax_id, address_line1, address_line2, city, state, zip_code, email, phone, is_default, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    payload,
                )
            payer_count += 1

        payees = [
            {
                "name": "Ana Rivera Therapy Services",
                "tax_id": "580-11-1234",
                "payee_type": "individual",
                "address_line1": "12 Calle Luna",
                "address_line2": "",
                "city": "Ponce",
                "state": "PR",
                "zip_code": "00716",
                "email": "ana.rivera@example.com",
                "phone": "787-555-0111",
            },
            {
                "name": "Caribe Consulting Group PSC",
                "tax_id": "66-9988776",
                "payee_type": "corporation",
                "address_line1": "220 Avenida De Diego",
                "address_line2": "Floor 5",
                "city": "Mayaguez",
                "state": "PR",
                "zip_code": "00680",
                "email": "billing@caribeconsulting.com",
                "phone": "787-555-0222",
            },
            {
                "name": "Luis Mercado DBA Health Advisory",
                "tax_id": "",
                "payee_type": "individual",
                "address_line1": "44 Calle Salud",
                "address_line2": "",
                "city": "Bayamon",
                "state": "PR",
                "zip_code": "00961",
                "email": "lmercado@example.com",
                "phone": "787-555-0333",
            },
        ]
        payee_ids: Dict[str, int] = {}
        for payee in payees:
            existing = conn.execute("SELECT id FROM payees WHERE name = ?", (payee["name"],)).fetchone()
            if existing:
                payee_ids[payee["name"]] = int(existing["id"])
                conn.execute(
                    """
                    UPDATE payees
                    SET tax_id = ?, payee_type = ?, address_line1 = ?, address_line2 = ?, city = ?, state = ?, zip_code = ?, email = ?, phone = ?
                    WHERE id = ?
                    """,
                    (
                        payee["tax_id"],
                        payee["payee_type"],
                        payee["address_line1"],
                        payee["address_line2"],
                        payee["city"],
                        payee["state"],
                        payee["zip_code"],
                        payee["email"],
                        payee["phone"],
                        existing["id"],
                    ),
                )
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO payees
                    (name, tax_id, payee_type, address_line1, address_line2, city, state, zip_code, email, phone, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payee["name"],
                        payee["tax_id"],
                        payee["payee_type"],
                        payee["address_line1"],
                        payee["address_line2"],
                        payee["city"],
                        payee["state"],
                        payee["zip_code"],
                        payee["email"],
                        payee["phone"],
                        created_at,
                    ),
                )
                payee_ids[payee["name"]] = int(cursor.lastrowid)

        payment_imports = [
            ("demo-payment-current", f"demo_services_{current_year}.xlsx", "completed", 6, f"Demo payment import for tax year {current_year}"),
            ("demo-payment-previous", f"demo_services_{previous_year}.xlsx", "completed", 4, f"Demo payment import for tax year {previous_year}"),
        ]
        for import_id, filename, status, row_count, notes in payment_imports:
            exists = conn.execute("SELECT id FROM payment_imports WHERE id = ?", (import_id,)).fetchone()
            if exists:
                conn.execute(
                    "UPDATE payment_imports SET filename = ?, uploaded_at = ?, status = ?, row_count = ?, notes = ? WHERE id = ?",
                    (filename, created_at, status, row_count, notes, import_id),
                )
                conn.execute("DELETE FROM payment_records WHERE payment_import_id = ?", (import_id,))
            else:
                conn.execute(
                    """
                    INSERT INTO payment_imports (id, filename, source_hash, uploaded_at, status, row_count, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (import_id, filename, f"demo-{import_id}", created_at, status, row_count, notes),
                )

        payment_rows = [
            ("demo-payment-current", "Ana Rivera Therapy Services", f"{current_year}-01-15", 1250.00, "Therapy Services", "Invoice", "AR-1001", current_year, "Monthly therapy services", 1),
            ("demo-payment-current", "Ana Rivera Therapy Services", f"{current_year}-02-15", 1380.00, "Therapy Services", "Invoice", "AR-1002", current_year, "Follow-up services", 1),
            ("demo-payment-current", "Caribe Consulting Group PSC", f"{current_year}-03-01", 2400.00, "Advisory Services", "Check", "CC-2001", current_year, "Operational consulting", 1),
            ("demo-payment-current", "Caribe Consulting Group PSC", f"{current_year}-04-01", 2100.00, "Advisory Services", "Check", "CC-2002", current_year, "Quarterly advisory", 1),
            ("demo-payment-current", "Luis Mercado DBA Health Advisory", f"{current_year}-05-10", 900.00, "Health Advisory", "ACH", "LM-3001", current_year, "Health provider support", 1),
            ("demo-payment-current", "Luis Mercado DBA Health Advisory", f"{current_year}-06-10", 950.00, "Health Advisory", "ACH", "LM-3002", current_year, "Health provider support", 1),
            ("demo-payment-previous", "Ana Rivera Therapy Services", f"{previous_year}-09-15", 1100.00, "Therapy Services", "Invoice", "AR-0901", previous_year, "Prior year reference", 0),
            ("demo-payment-previous", "Caribe Consulting Group PSC", f"{previous_year}-10-01", 1800.00, "Advisory Services", "Check", "CC-1001", previous_year, "Prior year reference", 0),
            ("demo-payment-previous", "Luis Mercado DBA Health Advisory", f"{previous_year}-11-12", 820.00, "Health Advisory", "ACH", "LM-1001", previous_year, "Prior year reference", 0),
            ("demo-payment-previous", "Luis Mercado DBA Health Advisory", f"{previous_year}-12-12", 780.00, "Health Advisory", "ACH", "LM-1002", previous_year, "Prior year reference", 0),
        ]
        payment_count = 0
        for payment_import_id, payee_name, payment_date, amount, category, document_type, reference_number, tax_year, notes, is_active in payment_rows:
            raw_row_json = json.dumps(
                {
                    "payee_name": payee_name,
                    "payment_date": payment_date,
                    "amount": amount,
                    "category": category,
                    "document_type": document_type,
                    "reference_number": reference_number,
                }
            )
            cursor = conn.execute(
                """
                INSERT INTO payment_records
                (payment_import_id, payee_id, payment_date, amount, category, document_type, reference_number, tax_year, notes, source_row_json, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payment_import_id,
                    payee_ids[payee_name],
                    payment_date,
                    amount,
                    category,
                    document_type,
                    reference_number,
                    tax_year,
                    notes,
                    raw_row_json,
                    is_active,
                    created_at,
                ),
            )
            conn.execute(
                """
                INSERT INTO business_transactions
                (source_type, source_id, payee_id, company_id, transaction_type, status, transaction_date, due_date, amount, category, reference_number, document_type, notes, tax_year, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "payment_record",
                    str(cursor.lastrowid),
                    payee_ids[payee_name],
                    None,
                    "payment",
                    "posted",
                    payment_date,
                    None,
                    amount,
                    category,
                    reference_number,
                    document_type,
                    notes,
                    tax_year,
                    is_active,
                    created_at,
                    created_at,
                ),
            )
            payment_count += 1

        seeded_transaction_ids: Dict[str, int] = {}
        business_transactions = [
            ("manual", uuid.uuid4().hex, payee_ids["Caribe Consulting Group PSC"], company_ids["TrakinPR"], "bill", "open", f"{current_year}-07-01", f"{current_year}-07-15", 1450.0, "Office Systems", "BILL-7001", "Invoice", "Quarterly software and consulting bill", current_year, 1),
            ("manual", uuid.uuid4().hex, payee_ids["Ana Rivera Therapy Services"], company_ids["TrakinPR"], "expense", "posted", f"{current_year}-07-03", None, 220.0, "Supplies", "EXP-8100", "Receipt", "Clinical supplies purchase", current_year, 1),
        ]
        for source_type, source_id, payee_id, company_id, transaction_type, status, transaction_date, due_date, amount, category, reference_number, document_type, notes, tax_year, is_active in business_transactions:
            cursor = conn.execute(
                """
                INSERT INTO business_transactions
                (source_type, source_id, payee_id, company_id, transaction_type, status, transaction_date, due_date, amount, category, reference_number, document_type, notes, tax_year, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_type,
                    source_id,
                    payee_id,
                    company_id,
                    transaction_type,
                    status,
                    transaction_date,
                    due_date,
                    amount,
                    category,
                    reference_number,
                    document_type,
                    notes,
                    tax_year,
                    is_active,
                    created_at,
                    created_at,
                ),
            )
            seeded_transaction_ids[reference_number] = int(cursor.lastrowid)

        expense_documents = [
            (
                "demo-expense-doc-1",
                "office_subscription_receipt.pdf",
                "demo-expense-hash-1",
                "classified",
                "Software & Subscriptions",
                payee_ids["Caribe Consulting Group PSC"],
                company_ids["TrakinPR"],
                seeded_transaction_ids.get("BILL-7001"),
                "Linked demo receipt for subscription billing.",
            ),
            (
                "demo-expense-doc-2",
                "clinical_supply_receipt.jpg",
                "demo-expense-hash-2",
                "reviewed",
                "Clinical Supplies",
                payee_ids["Ana Rivera Therapy Services"],
                company_ids["TrakinPR"],
                None,
                "Waiting for amount confirmation before creating expense.",
            ),
        ]
        for document_id, filename, source_hash, status, suggested_category, payee_id, company_id, linked_transaction_id, notes in expense_documents:
            existing = conn.execute("SELECT id FROM expense_documents WHERE id = ?", (document_id,)).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE expense_documents
                    SET filename = ?, source_hash = ?, uploaded_at = ?, status = ?, linked_transaction_id = ?, suggested_category = ?, payee_id = ?, company_id = ?, notes = ?
                    WHERE id = ?
                    """,
                    (filename, source_hash, created_at, status, linked_transaction_id, suggested_category, payee_id, company_id, notes, document_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO expense_documents
                    (id, filename, source_hash, uploaded_at, status, linked_transaction_id, suggested_category, payee_id, company_id, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (document_id, filename, source_hash, created_at, status, linked_transaction_id, suggested_category, payee_id, company_id, notes),
                )

        import_id = "demo-employee-import"
        exists = conn.execute("SELECT id FROM imports WHERE id = ?", (import_id,)).fetchone()
        if exists:
            conn.execute("DELETE FROM work_entries WHERE import_id = ?", (import_id,))
            conn.execute(
                "UPDATE imports SET filename = ?, uploaded_at = ?, status = ?, row_count = ?, error_count = ? WHERE id = ?",
                ("demo_employee_records.xlsx", created_at, "completed", 6, 0, import_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO imports (id, filename, tool_type, source_hash, uploaded_at, status, row_count, error_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (import_id, "demo_employee_records.xlsx", "generic", "demo-employee-source", created_at, "completed", 6, 0),
            )

        employees = [
            "Maria Gomez",
            "Pedro Sanchez",
            "Julia Torres",
        ]
        employee_ids: Dict[str, int] = {}
        for name in employees:
            existing = conn.execute("SELECT id FROM employees WHERE name = ?", (name,)).fetchone()
            if existing:
                employee_ids[name] = int(existing["id"])
            else:
                cursor = conn.execute("INSERT INTO employees (name) VALUES (?)", (name,))
                employee_ids[name] = int(cursor.lastrowid)

        work_entries = [
            ("Maria Gomez", "RN Skilled Visit", "Enfermeria", "2026-03-03", "Carlos Lopez", "Metro", 55.0, 12.0, 0.0, 55.0),
            ("Maria Gomez", "RN Skilled Visit", "Enfermeria", "2026-03-04", "Elena Diaz", "Metro", 55.0, 14.0, 0.0, 55.0),
            ("Pedro Sanchez", "PTA G0151", "Terapia", "2026-03-05", "Luis Cruz", "North", 35.0, 5.0, 0.0, 35.0),
            ("Pedro Sanchez", "PTA G0151", "Terapia", "2026-03-06", "Rosa Vega", "North", 35.0, 6.0, 0.0, 35.0),
            ("Julia Torres", "Consult Follow Up", "Enfermeria", "2026-03-07", "Mateo Ruiz", "South", 75.0, 0.0, 5.0, 80.0),
            ("Julia Torres", "OT Session", "Terapia", "2026-03-08", "Lucia Mendez", "South", 65.0, 8.0, 0.0, 65.0),
        ]
        work_count = 0
        for index, (employee_name, task, classification, entry_date, patient_name, branch, rate, mileage, surcharge, amount) in enumerate(work_entries):
            raw = json.dumps(
                {
                    "Employee": employee_name,
                    "Task": task,
                    "Date": entry_date,
                    "Patient Name": patient_name,
                    "Branch": branch,
                }
            )
            conn.execute(
                """
                INSERT INTO work_entries
                (import_id, employee_id, task, entry_date, patient_name, branch, classification, rate, mileage, surcharge, amount, is_active, row_index, raw_row_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    import_id,
                    employee_ids[employee_name],
                    task,
                    entry_date,
                    patient_name,
                    branch,
                    classification,
                    rate,
                    mileage,
                    surcharge,
                    amount,
                    1,
                    index,
                    raw,
                    created_at,
                ),
            )
            work_count += 1

        conn.commit()

    return {
        "companies_created": len(companies),
        "payers_created": payer_count,
        "payees_created": len(payees),
        "payment_records_created": payment_count,
        "employee_rows_created": work_count,
        "current_tax_year": current_year,
        "recommended_payee_for_pdf": "Ana Rivera Therapy Services",
    }
