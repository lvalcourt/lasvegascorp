from __future__ import annotations

import json
import os
import re
import uuid
import io
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pypdf import PdfReader, PdfWriter
from pydantic import BaseModel, Field
from reportlab.pdfbase import pdfdoc
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from core.db import connect, init_db
from core.seed_data import seed_demo_data


def _compat_md5(*args, **kwargs):
    kwargs.pop("usedforsecurity", None)
    return hashlib.md5(*args, **kwargs)


pdfdoc.md5 = _compat_md5

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("LASVEGASCORP_DATA_DIR", str(ROOT_DIR)))
DEFAULT_RULES_PATH = Path(os.getenv("LASVEGASCORP_DEFAULT_RULES_PATH", str(ROOT_DIR / "rules.json")))
RULES_PATH = DATA_DIR / "rules.json"
REPORTS_DIR = DATA_DIR / "reports"
PAYMENT_DOCUMENTS_DIR = DATA_DIR / "payment_documents"
DB_PATH = DATA_DIR / "app.db"
ROLE_ORDER = {"viewer": 1, "operator": 2, "admin": 3}
REPO_ROOT = ROOT_DIR.parent.parent
FORM_4806SP_TEMPLATE = REPO_ROOT / "reference" / "480.6sp_2024_informativo.pdf"


class Rule(BaseModel):
    id: str
    name: str
    type: str = Field(..., pattern="^(not_empty|number_range|allowed_values|conditional_required)$")
    column: str
    min: Optional[float] = None
    max: Optional[float] = None
    allowed: Optional[List[str]] = None
    when_column: Optional[str] = None
    when_operator: Optional[str] = None
    when_equals: Optional[str] = None
    then_column: Optional[str] = None


class RuleSummary(BaseModel):
    rule_id: str
    rule_name: str
    column: str
    failed_rows: int
    passed_rows: int
    total_rows: int


class ValidationResponse(BaseModel):
    summary: Dict[str, Any]
    rules: List[RuleSummary]
    report_id: str


class SummaryToolResponse(BaseModel):
    summary: Dict[str, Any]
    report_id: str


class ImportResponse(BaseModel):
    import_id: str
    filename: str
    tool_type: str
    row_count: int
    employees_identified: int
    terapia_employees: int
    enfermeria_employees: int
    unclassified_employees: int


class ClearDataResponse(BaseModel):
    deleted_imports: int
    deleted_entries: int
    deleted_employees: int


class DemoSeedResponse(BaseModel):
    companies_created: int
    payers_created: int
    payees_created: int
    payment_records_created: int
    employee_rows_created: int
    current_tax_year: int
    recommended_payee_for_pdf: str


class PaymentImportResponse(BaseModel):
    payment_import_id: str
    filename: str
    status: str
    records_created: int
    payees_identified: int
    notes: Optional[str] = None


class PaymentRecordCreate(BaseModel):
    payee_name: str
    payment_date: Optional[str] = None
    amount: float = 0
    category: Optional[str] = None
    document_type: Optional[str] = None
    reference_number: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None


class PayerProfilePayload(BaseModel):
    company_id: Optional[int] = None
    name: str
    tax_id: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_default: bool = False


class CompanyProfilePayload(BaseModel):
    name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_default: bool = False


class PayeeProfilePayload(BaseModel):
    name: str
    tax_id: Optional[str] = None
    payee_type: str = "contractor"
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


def build_4806sp_payee_rows(year_value: int, include_history: bool) -> Dict[str, Any]:
    history_clause = "" if include_history else "AND pr.is_active = 1"
    with connect(DB_PATH) as conn:
        totals = conn.execute(
            f"""
            SELECT
              COUNT(*) AS records_count,
              COUNT(DISTINCT pr.payee_id) AS payees_count,
              SUM(pr.amount) AS amount_total
            FROM payment_records pr
            WHERE COALESCE(pr.tax_year, ?) = ?
              {history_clause}
            """,
            (year_value, year_value),
        ).fetchone()

        payees = conn.execute(
            f"""
            SELECT
              p.id AS payee_id,
              p.name AS payee_name,
              p.tax_id,
              p.payee_type,
              COUNT(*) AS payments_count,
              SUM(pr.amount) AS amount_total,
              MIN(pr.payment_date) AS first_payment_date,
              MAX(pr.payment_date) AS last_payment_date,
              MAX(COALESCE(NULLIF(TRIM(pr.category), ''), '')) AS category_sample,
              CASE WHEN COALESCE(TRIM(p.tax_id), '') = '' THEN 1 ELSE 0 END AS missing_tax_id,
              CASE WHEN SUM(pr.amount) <= 0 THEN 1 ELSE 0 END AS non_positive_total
            FROM payment_records pr
            JOIN payees p ON p.id = pr.payee_id
            WHERE COALESCE(pr.tax_year, ?) = ?
              {history_clause}
            GROUP BY p.id, p.name, p.tax_id, p.payee_type
            ORDER BY amount_total DESC, p.name ASC
            """,
            (year_value, year_value),
        ).fetchall()

    payee_rows = []
    missing_tax_id_count = 0
    ready_count = 0
    for row in payees:
        issues = []
        if row["missing_tax_id"]:
            issues.append("Missing tax ID")
            missing_tax_id_count += 1
        if row["non_positive_total"]:
            issues.append("No positive payment total")
        if not row["first_payment_date"]:
            issues.append("Missing payment date")
        ready = len(issues) == 0
        if ready:
            ready_count += 1
        payee_rows.append(
            {
                "payee_id": row["payee_id"],
                "payee_name": row["payee_name"],
                "tax_id": row["tax_id"],
                "payee_type": row["payee_type"],
                "payments_count": row["payments_count"] or 0,
                "amount_total": row["amount_total"] or 0,
                "first_payment_date": row["first_payment_date"],
                "last_payment_date": row["last_payment_date"],
                "category_sample": row["category_sample"] or "",
                "missing_tax_id": bool(row["missing_tax_id"]),
                "ready": ready,
                "issues": issues,
            }
        )

    return {
        "tax_year": year_value,
        "totals": {
            "records_count": totals["records_count"] or 0,
            "payees_count": totals["payees_count"] or 0,
            "amount_total": totals["amount_total"] or 0,
            "payees_missing_tax_id": missing_tax_id_count,
            "payees_ready": ready_count,
        },
        "payees": payee_rows,
    }


def get_default_payer_profile() -> Dict[str, Any]:
    with connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT id, company_id, name, tax_id, address_line1, address_line2, city, state, zip_code, email, phone
            FROM payer_profiles
            WHERE is_default = 1
            ORDER BY id ASC
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        company = get_default_company_profile()
        return {
            "id": None,
            "company_id": company.get("id"),
            "name": company.get("name", "Las Vegas Corp"),
            "tax_id": company.get("tax_id", ""),
            "address_line1": company.get("address_line1", ""),
            "address_line2": company.get("address_line2", ""),
            "city": company.get("city", ""),
            "state": company.get("state", "PR"),
            "zip_code": company.get("zip_code", ""),
            "email": company.get("email", ""),
            "phone": company.get("phone", ""),
        }
    return dict(row)


def get_default_company_profile() -> Dict[str, Any]:
    with connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT id, name, legal_name, tax_id, address_line1, address_line2, city, state, zip_code, email, phone, is_default
            FROM company_profiles
            WHERE is_default = 1
            ORDER BY id ASC
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        return {
            "id": None,
            "name": "Las Vegas Corp",
            "legal_name": "Las Vegas Corp",
            "tax_id": "",
            "address_line1": "",
            "address_line2": "",
            "city": "",
            "state": "PR",
            "zip_code": "",
            "email": "",
            "phone": "",
            "is_default": True,
        }
    return dict(row)


def upsert_payee_profile(conn, payload: Dict[str, Any], now: str) -> int:
    payee_name = (payload.get("name") or "").strip()
    if not payee_name:
        raise HTTPException(status_code=400, detail="Payee name is required")
    conn.execute(
        """
        INSERT OR IGNORE INTO payees
        (name, tax_id, payee_type, address_line1, address_line2, city, state, zip_code, email, phone, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payee_name,
            payload.get("tax_id"),
            payload.get("payee_type") or "contractor",
            payload.get("address_line1"),
            payload.get("address_line2"),
            payload.get("city"),
            payload.get("state"),
            payload.get("zip_code"),
            payload.get("email"),
            payload.get("phone"),
            now,
        ),
    )
    conn.execute(
        """
        UPDATE payees
        SET
          tax_id = COALESCE(NULLIF(?, ''), tax_id),
          payee_type = COALESCE(NULLIF(?, ''), payee_type),
          address_line1 = COALESCE(NULLIF(?, ''), address_line1),
          address_line2 = COALESCE(NULLIF(?, ''), address_line2),
          city = COALESCE(NULLIF(?, ''), city),
          state = COALESCE(NULLIF(?, ''), state),
          zip_code = COALESCE(NULLIF(?, ''), zip_code),
          email = COALESCE(NULLIF(?, ''), email),
          phone = COALESCE(NULLIF(?, ''), phone)
        WHERE name = ?
        """,
        (
            payload.get("tax_id"),
            payload.get("payee_type"),
            payload.get("address_line1"),
            payload.get("address_line2"),
            payload.get("city"),
            payload.get("state"),
            payload.get("zip_code"),
            payload.get("email"),
            payload.get("phone"),
            payee_name,
        ),
    )
    row = conn.execute("SELECT id FROM payees WHERE name = ?", (payee_name,)).fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="Unable to save payee profile")
    return int(row["id"])


def generate_4806sp_draft_pdf(prefill: Dict[str, Any]) -> Path:
    if not FORM_4806SP_TEMPLATE.exists():
        raise HTTPException(status_code=500, detail="480.6SP template PDF not found in reference directory")

    report_id = uuid.uuid4().hex
    output_path = REPORTS_DIR / f"4806sp_draft_{report_id}.pdf"

    template_reader = PdfReader(str(FORM_4806SP_TEMPLATE))
    writer = PdfWriter()

    packet = prefill["prefill_packet"]

    overlay_buffer = io.BytesIO()
    c = canvas.Canvas(overlay_buffer, pagesize=letter)
    c.setFont("Helvetica", 10)

    # Draft overlay for the official 480.6SP template.
    c.drawString(505, 650, str(prefill["tax_year"]))
    c.drawString(65, 724, packet.get("payer_tax_id", ""))
    c.drawString(65, 706, packet.get("payer_name", ""))
    c.drawString(65, 688, packet.get("payer_address_line1", ""))
    payer_city_line = " ".join(part for part in [packet.get("payer_city", ""), packet.get("payer_state", ""), packet.get("payer_zip_code", "")] if part)
    c.drawString(65, 670, payer_city_line)
    c.drawString(65, 594, packet.get("recipient_tax_id", ""))
    c.drawString(65, 575, packet.get("recipient_name", ""))
    c.drawString(65, 557, packet.get("recipient_address_line1", ""))
    recipient_city_line = " ".join(part for part in [packet.get("recipient_city", ""), packet.get("recipient_state", ""), packet.get("recipient_zip_code", "")] if part)
    c.drawString(65, 539, recipient_city_line)
    c.drawRightString(300, 435, f"{float(packet.get('services_total', 0) or 0):,.2f}")
    c.drawString(65, 118, "DRAFT PREFILL - Verify all fields before filing in SURI")
    c.save()
    overlay_buffer.seek(0)

    overlay_pdf = PdfReader(overlay_buffer)
    first_page = template_reader.pages[0]
    first_page.merge_page(overlay_pdf.pages[0])
    writer.add_page(first_page)

    for page in template_reader.pages[1:]:
        writer.add_page(page)

    summary_buffer = io.BytesIO()
    c2 = canvas.Canvas(summary_buffer, pagesize=letter)
    c2.setFont("Helvetica-Bold", 16)
    c2.drawString(54, 744, "480.6SP Draft Prefill Summary")
    c2.setFont("Helvetica", 10)
    y = 712
    lines = [
        f"Tax year: {prefill['tax_year']}",
        f"Recipient: {packet.get('recipient_name', '')}",
        f"Recipient tax ID: {packet.get('recipient_tax_id', '')}",
        f"Services total: {float(packet.get('services_total', 0) or 0):,.2f}",
        f"Payments count: {packet.get('payments_count', 0)}",
        f"First payment date: {packet.get('first_payment_date') or ''}",
        f"Last payment date: {packet.get('last_payment_date') or ''}",
        f"Categories: {', '.join(packet.get('service_categories', []))}",
        "",
        "Issues:",
    ]
    for issue in prefill["issues"] or ["No blocking issues found."]:
        lines.append(f"- {issue}")
    lines.extend(
        [
            "",
            "Not yet mapped from app data:",
            "- Withholding-specific boxes beyond total paid",
            "",
            "This file is a draft support export for review before final SURI preparation.",
        ]
    )
    for line in lines:
        c2.drawString(54, y, line)
        y -= 16
        if y < 72:
            c2.showPage()
            c2.setFont("Helvetica", 10)
            y = 744
    c2.save()
    summary_buffer.seek(0)
    summary_pdf = PdfReader(summary_buffer)
    for page in summary_pdf.pages:
        writer.add_page(page)

    with output_path.open("wb") as fh:
        writer.write(fh)
    return output_path


def require_role(user_role: str | None, minimum_role: str) -> str:
    normalized = (user_role or "viewer").strip().lower()
    if normalized not in ROLE_ORDER:
        raise HTTPException(status_code=403, detail="Invalid user role")
    if ROLE_ORDER[normalized] < ROLE_ORDER[minimum_role]:
        raise HTTPException(status_code=403, detail=f"{minimum_role.title()} role required")
    return normalized


def ensure_rules_file() -> None:
    if not RULES_PATH.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if DEFAULT_RULES_PATH.exists():
            RULES_PATH.write_text(DEFAULT_RULES_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            RULES_PATH.write_text("[]", encoding="utf-8")


def load_rules() -> List[Rule]:
    ensure_rules_file()
    data = json.loads(RULES_PATH.read_text(encoding="utf-8") or "[]")
    return [Rule(**item) for item in data]


def save_rules(rules: List[Rule]) -> None:
    RULES_PATH.write_text(json.dumps([rule.model_dump() for rule in rules], indent=2), encoding="utf-8")


@app.on_event("startup")
def startup() -> None:
    init_db(DB_PATH)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    PAYMENT_DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/rules", response_model=List[Rule])
def get_rules():
    return load_rules()


@app.post("/rules", response_model=List[Rule])
def update_rules(rules: List[Rule], x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "operator")
    save_rules(rules)
    return rules


@app.post("/imports", response_model=ImportResponse)
def create_import(file: UploadFile = File(...), x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "operator")
    df, source_hash = read_uploaded_dataframe(file)
    df.columns = [str(col).strip() for col in df.columns]

    now = datetime.now(timezone.utc).isoformat()
    import_id = uuid.uuid4().hex
    filename = file.filename or "uploaded_file"

    if "Employee" in df.columns:
        employee_series = df["Employee"].fillna("").astype(str).str.strip()
    else:
        employee_series = derive_employee_series_from_markers(df).fillna("").astype(str).str.strip()

    task_series = df["Task"] if "Task" in df.columns else pd.Series([""] * len(df), index=df.index, dtype="string")
    terapia_match, enfermeria_match = classify_task_series(task_series)

    classification = pd.Series(["Unclassified"] * len(df), index=df.index, dtype="string")
    classification.loc[terapia_match] = "Terapia"
    classification.loc[enfermeria_match] = "Enfermeria"

    rate_series = pd.Series([0.0] * len(df), index=df.index)
    mileage_series = pd.Series([0.0] * len(df), index=df.index)
    surcharge_series = pd.Series([0.0] * len(df), index=df.index)
    amount_series = pd.Series([0.0] * len(df), index=df.index)
    if "Rate" in df.columns:
        rate_series = df["Rate"].apply(parse_number)
    if "Mileage" in df.columns:
        mileage_series = df["Mileage"].apply(parse_number)
    elif "Millage" in df.columns:
        mileage_series = df["Millage"].apply(parse_number)
    if "Surcharge" in df.columns:
        surcharge_series = df["Surcharge"].apply(parse_number)
    if "Amount" in df.columns:
        amount_series = df["Amount"].apply(parse_number)

    rows_to_insert: List[Dict[str, Any]] = []
    for row_idx in range(len(df)):
        employee_name = employee_series.iloc[row_idx]
        if employee_name == "":
            continue
        row_dict = {
            key: (None if pd.isna(value) else str(value))
            for key, value in df.iloc[row_idx].to_dict().items()
        }
        rows_to_insert.append(
            {
                "employee_name": employee_name,
                "task": "" if pd.isna(task_series.iloc[row_idx]) else str(task_series.iloc[row_idx]),
                "classification": classification.iloc[row_idx],
                "rate": float(rate_series.iloc[row_idx]),
                "mileage": float(mileage_series.iloc[row_idx]),
                "surcharge": float(surcharge_series.iloc[row_idx]),
                "amount": float(amount_series.iloc[row_idx]),
                "row_index": row_idx,
                "raw_row_json": json.dumps(row_dict),
            }
        )

    with connect(DB_PATH) as conn:
        existing = conn.execute(
            "SELECT id FROM imports WHERE tool_type = ? AND source_hash = ? ORDER BY uploaded_at DESC LIMIT 1",
            ("generic", source_hash),
        ).fetchone()
        if existing:
            import_id = existing["id"]
            conn.execute("DELETE FROM work_entries WHERE import_id = ?", (import_id,))
            conn.execute(
                "UPDATE imports SET filename = ?, uploaded_at = ?, status = ?, row_count = ?, error_count = ? WHERE id = ?",
                (filename, now, "processing", 0, 0, import_id),
            )
        else:
            conn.execute(
                "INSERT INTO imports (id, filename, tool_type, source_hash, uploaded_at, status, row_count, error_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (import_id, filename, "generic", source_hash, now, "processing", 0, 0),
            )

        employee_names = sorted({row["employee_name"] for row in rows_to_insert})
        for employee_name in employee_names:
            conn.execute("INSERT OR IGNORE INTO employees (name) VALUES (?)", (employee_name,))

        rows_by_employee = {
            row["name"]: row["id"]
            for row in conn.execute("SELECT id, name FROM employees WHERE name IN ({})".format(",".join(["?"] * len(employee_names))), employee_names).fetchall()
        } if employee_names else {}

        # Employee-level upsert with history: deactivate prior generic rows for employees found in this import.
        employee_ids = list(rows_by_employee.values())
        if employee_ids:
            placeholders = ",".join(["?"] * len(employee_ids))
            conn.execute(
                f"""
                UPDATE work_entries
                SET is_active = 0
                WHERE employee_id IN ({placeholders})
                  AND import_id IN (SELECT id FROM imports WHERE tool_type = ?)
                  AND import_id <> ?
                """,
                (*employee_ids, "generic", import_id),
            )

        for entry in rows_to_insert:
            employee_id = rows_by_employee.get(entry["employee_name"])
            if employee_id is None:
                continue
            conn.execute(
                """
                INSERT INTO work_entries
                (import_id, employee_id, task, entry_date, patient_name, branch, classification, rate, mileage, surcharge, amount, is_active, row_index, raw_row_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    import_id,
                    employee_id,
                    entry["task"],
                    None,
                    None,
                    None,
                    entry["classification"],
                    entry["rate"],
                    entry["mileage"],
                    entry["surcharge"],
                    entry["amount"],
                    1,
                    entry["row_index"],
                    entry["raw_row_json"],
                    now,
                ),
            )

        conn.execute(
            "UPDATE imports SET status = ?, row_count = ? WHERE id = ?",
            ("completed", len(rows_to_insert), import_id),
        )
        conn.commit()

    employee_count = len({row["employee_name"] for row in rows_to_insert})
    terapia_count = len({row["employee_name"] for row in rows_to_insert if row["classification"] == "Terapia"})
    enfermeria_count = len({row["employee_name"] for row in rows_to_insert if row["classification"] == "Enfermeria"})
    unclassified_count = len({row["employee_name"] for row in rows_to_insert if row["classification"] == "Unclassified"})

    return ImportResponse(
        import_id=import_id,
        filename=filename,
        tool_type="generic",
        row_count=len(rows_to_insert),
        employees_identified=employee_count,
        terapia_employees=terapia_count,
        enfermeria_employees=enfermeria_count,
        unclassified_employees=unclassified_count,
    )


@app.get("/imports")
def list_imports(limit: int = 50, offset: int = 0):
    with connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, filename, tool_type, uploaded_at, status, row_count, error_count FROM imports ORDER BY uploaded_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/imports/{import_id}/stats")
def import_stats(import_id: str):
    with connect(DB_PATH) as conn:
        import_row = conn.execute(
            "SELECT id, filename, tool_type, uploaded_at, status, row_count, error_count FROM imports WHERE id = ?",
            (import_id,),
        ).fetchone()
        if import_row is None:
            raise HTTPException(status_code=404, detail="Import not found")

        totals = conn.execute(
            """
            SELECT
              COUNT(*) AS rows_count,
              COUNT(DISTINCT employee_id) AS employees_count,
              SUM(rate) AS rate_total,
              SUM(mileage) AS mileage_total,
              SUM(surcharge) AS surcharge_total,
              SUM(amount) AS amount_total
            FROM work_entries
            WHERE import_id = ?
              AND is_active = 1
            """,
            (import_id,),
        ).fetchone()

        by_class = conn.execute(
            """
            SELECT classification, COUNT(DISTINCT employee_id) AS employees
            FROM work_entries
            WHERE import_id = ?
              AND is_active = 1
            GROUP BY classification
            """,
            (import_id,),
        ).fetchall()

    classification = {row["classification"]: row["employees"] for row in by_class}
    return {
        "import": dict(import_row),
        "summary": {
            "rows_count": totals["rows_count"] or 0,
            "employees_count": totals["employees_count"] or 0,
            "rate_total": totals["rate_total"] or 0,
            "mileage_total": totals["mileage_total"] or 0,
            "surcharge_total": totals["surcharge_total"] or 0,
            "amount_total": totals["amount_total"] or 0,
            "terapia_employees": classification.get("Terapia", 0),
            "enfermeria_employees": classification.get("Enfermeria", 0),
            "unclassified_employees": classification.get("Unclassified", 0),
        },
    }


@app.get("/employees")
def list_employees(search: str = "", limit: int = 100, offset: int = 0, include_history: bool = False):
    terms = [term for term in re.split(r"\s+", search.strip()) if term]
    where_sql = "1=1"
    params: List[Any] = []
    if terms:
        where_parts = []
        for term in terms:
            where_parts.append("e.name LIKE ?")
            params.append(f"%{term}%")
        where_sql = " AND ".join(where_parts)

    with connect(DB_PATH) as conn:
        rows = conn.execute(
            f"""
            SELECT
              e.id,
              e.name,
              COUNT(we.id) AS rows_count,
              SUM(we.rate) AS rate_total,
              SUM(we.mileage) AS mileage_total,
              SUM(we.surcharge) AS surcharge_total,
              SUM(we.amount) AS amount_total
            FROM employees e
            LEFT JOIN work_entries we ON we.employee_id = e.id
            WHERE {where_sql}
              AND ({1 if include_history else 0} = 1 OR we.is_active = 1 OR we.id IS NULL)
            GROUP BY e.id, e.name
            ORDER BY e.name ASC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "rows_count": row["rows_count"] or 0,
            "rate_total": row["rate_total"] or 0,
            "mileage_total": row["mileage_total"] or 0,
            "surcharge_total": row["surcharge_total"] or 0,
            "amount_total": row["amount_total"] or 0,
        }
        for row in rows
    ]


@app.get("/employees/{employee_id}/entries")
def employee_entries(employee_id: int, limit: int = 200, offset: int = 0, include_history: bool = False):
    with connect(DB_PATH) as conn:
        employee = conn.execute("SELECT id, name FROM employees WHERE id = ?", (employee_id,)).fetchone()
        if employee is None:
            raise HTTPException(status_code=404, detail="Employee not found")

        rows = conn.execute(
            """
            SELECT
              we.id,
              we.import_id,
                i.filename,
                i.tool_type,
                i.uploaded_at,
                we.entry_date,
                we.patient_name,
                we.task,
                we.branch,
                we.classification,
                we.rate,
                we.mileage,
                we.surcharge,
                we.amount,
              we.row_index
            FROM work_entries we
            JOIN imports i ON i.id = we.import_id
            WHERE we.employee_id = ?
              AND (? = 1 OR we.is_active = 1)
            ORDER BY i.uploaded_at DESC, we.row_index ASC
            LIMIT ? OFFSET ?
            """,
            (employee_id, 1 if include_history else 0, limit, offset),
        ).fetchall()

    return {
        "employee": {"id": employee["id"], "name": employee["name"]},
        "entries": [dict(row) for row in rows],
    }


@app.get("/records")
def records_table(
    search: str = "",
    import_id: str = "",
    classification: str = "",
    branch: str = "",
    date_from: str = "",
    date_to: str = "",
    include_history: bool = False,
    limit: int = 300,
    offset: int = 0,
):
    where = ["1=1"]
    params: List[Any] = []

    if search.strip():
        where.append("(e.name LIKE ? OR COALESCE(we.patient_name, '') LIKE ? OR COALESCE(we.task, '') LIKE ?)")
        like = f"%{search.strip()}%"
        params.extend([like, like, like])
    if import_id.strip():
        where.append("we.import_id = ?")
        params.append(import_id.strip())
    if classification.strip():
        where.append("we.classification = ?")
        params.append(classification.strip())
    if branch.strip():
        where.append("COALESCE(we.branch, '') = ?")
        params.append(branch.strip())
    if date_from.strip():
        where.append("COALESCE(we.entry_date, '') >= ?")
        params.append(date_from.strip())
    if date_to.strip():
        where.append("COALESCE(we.entry_date, '') <= ?")
        params.append(date_to.strip())

    query = f"""
        SELECT
          we.id,
          we.import_id,
          i.filename,
          i.tool_type,
          i.uploaded_at,
          e.id AS employee_id,
          e.name AS employee_name,
          we.entry_date,
          we.patient_name,
          we.task,
          we.branch,
          we.classification,
          we.rate,
          we.mileage,
          we.surcharge,
          we.amount,
          we.row_index
        FROM work_entries we
        JOIN employees e ON e.id = we.employee_id
        JOIN imports i ON i.id = we.import_id
        WHERE {' AND '.join(where)}
          AND ({1 if include_history else 0} = 1 OR we.is_active = 1)
        ORDER BY i.uploaded_at DESC, e.name ASC, we.row_index ASC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    with connect(DB_PATH) as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


@app.get("/dashboard/metrics")
def dashboard_metrics(include_history: bool = False):
    active_clause = "" if include_history else "WHERE we.is_active = 1"
    date_filter_clause = "" if include_history else "AND we.is_active = 1"

    with connect(DB_PATH) as conn:
        totals = conn.execute(
            f"""
            SELECT
              COUNT(*) AS rows_count,
              COUNT(DISTINCT we.employee_id) AS employees_count,
              SUM(we.rate) AS rate_total,
              SUM(we.mileage) AS mileage_total,
              SUM(we.surcharge) AS surcharge_total,
              SUM(we.amount) AS amount_total
            FROM work_entries we
            {active_clause}
            """
        ).fetchone()

        by_classification = conn.execute(
            f"""
            SELECT
              we.classification AS label,
              COUNT(*) AS rows_count,
              COUNT(DISTINCT we.employee_id) AS employees_count
            FROM work_entries we
            {active_clause}
            GROUP BY we.classification
            ORDER BY rows_count DESC
            """
        ).fetchall()

        by_task = conn.execute(
            f"""
            SELECT
              COALESCE(TRIM(we.task), '(blank)') AS label,
              COUNT(*) AS rows_count,
              SUM(we.rate) AS rate_total,
              SUM(we.amount) AS amount_total
            FROM work_entries we
            {active_clause}
            GROUP BY COALESCE(TRIM(we.task), '(blank)')
            ORDER BY rows_count DESC
            LIMIT 12
            """
        ).fetchall()

        by_date = conn.execute(
            f"""
            SELECT
              we.entry_date AS date,
              COUNT(*) AS rows_count,
              COUNT(DISTINCT we.employee_id) AS employees_count,
              COUNT(DISTINCT CASE WHEN COALESCE(TRIM(we.patient_name), '') <> '' THEN TRIM(we.patient_name) END) AS patients_count,
              SUM(we.rate) AS rate_total,
              SUM(we.amount) AS amount_total
            FROM work_entries we
            WHERE COALESCE(we.entry_date, '') <> ''
              {date_filter_clause}
            GROUP BY we.entry_date
            ORDER BY we.entry_date ASC
            """
        ).fetchall()

    return {
        "totals": {
            "rows_count": totals["rows_count"] or 0,
            "employees_count": totals["employees_count"] or 0,
            "rate_total": totals["rate_total"] or 0,
            "mileage_total": totals["mileage_total"] or 0,
            "surcharge_total": totals["surcharge_total"] or 0,
            "amount_total": totals["amount_total"] or 0,
        },
        "by_classification": [dict(row) for row in by_classification],
        "by_task": [dict(row) for row in by_task],
        "by_date": [dict(row) for row in by_date],
    }


@app.post("/admin/clear-employee-data", response_model=ClearDataResponse)
def clear_employee_data(x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "admin")
    with connect(DB_PATH) as conn:
        deleted_entries = conn.execute("SELECT COUNT(*) AS n FROM work_entries").fetchone()["n"]
        deleted_imports = conn.execute("SELECT COUNT(*) AS n FROM imports").fetchone()["n"]
        deleted_employees = conn.execute("SELECT COUNT(*) AS n FROM employees").fetchone()["n"]

        conn.execute("DELETE FROM work_entries")
        conn.execute("DELETE FROM imports")
        conn.execute("DELETE FROM employees")
        conn.commit()

    return ClearDataResponse(
        deleted_imports=deleted_imports,
        deleted_entries=deleted_entries,
        deleted_employees=deleted_employees,
    )


@app.post("/admin/seed-demo-data", response_model=DemoSeedResponse)
def create_demo_seed_data(replace_existing: bool = True, x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "admin")
    data = seed_demo_data(DB_PATH, replace_existing=replace_existing)
    return DemoSeedResponse(**data)


@app.post("/payments/imports", response_model=PaymentImportResponse)
def create_payment_import(file: UploadFile = File(...), x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "operator")
    if file.filename is None:
        raise HTTPException(status_code=400, detail="File name is required")

    raw_bytes, source_hash = read_upload_bytes(file)
    now = datetime.now(timezone.utc).isoformat()
    payment_import_id = uuid.uuid4().hex
    filename = file.filename
    document_path = save_payment_document(payment_import_id, filename, raw_bytes)

    df = try_read_tabular_bytes(filename, raw_bytes)
    status = "needs_review"
    notes = f"Document stored at {document_path}. Manual review needed."
    payment_rows: List[Dict[str, Any]] = []
    if df is not None:
        payment_rows = create_payment_rows_from_dataframe(df)
        status = "completed"
        notes = f"Imported {len(payment_rows)} payment rows from spreadsheet."

    with connect(DB_PATH) as conn:
        existing = conn.execute(
            "SELECT id FROM payment_imports WHERE source_hash = ? ORDER BY uploaded_at DESC LIMIT 1",
            (source_hash,),
        ).fetchone()
        if existing:
            payment_import_id = existing["id"]
            conn.execute("DELETE FROM payment_records WHERE payment_import_id = ?", (payment_import_id,))
            conn.execute(
                "UPDATE payment_imports SET filename = ?, uploaded_at = ?, status = ?, row_count = ?, notes = ? WHERE id = ?",
                (filename, now, status, len(payment_rows), notes, payment_import_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO payment_imports (id, filename, source_hash, uploaded_at, status, row_count, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (payment_import_id, filename, source_hash, now, status, len(payment_rows), notes),
            )

        payee_names = sorted({row["payee_name"] for row in payment_rows if row["payee_name"]})
        for row in payment_rows:
            upsert_payee_profile(
                conn,
                {
                    "name": row["payee_name"],
                    "tax_id": row.get("tax_id"),
                    "payee_type": "contractor",
                },
                now,
            )

        rows_by_payee = {
            row["name"]: row["id"]
            for row in conn.execute(
                "SELECT id, name FROM payees WHERE name IN ({})".format(",".join(["?"] * len(payee_names))),
                payee_names,
            ).fetchall()
        } if payee_names else {}

        payee_ids = list(rows_by_payee.values())
        if payee_ids:
            placeholders = ",".join(["?"] * len(payee_ids))
            conn.execute(
                f"""
                UPDATE payment_records
                SET is_active = 0
                WHERE payee_id IN ({placeholders})
                  AND payment_import_id <> ?
                """,
                (*payee_ids, payment_import_id),
            )

        for row in payment_rows:
            payee_id = rows_by_payee.get(row["payee_name"])
            if payee_id is None:
                continue
            conn.execute(
                """
                INSERT INTO payment_records
                (payment_import_id, payee_id, payment_date, amount, category, document_type, reference_number, tax_year, notes, source_row_json, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payment_import_id,
                    payee_id,
                    row["payment_date"],
                    row["amount"],
                    row.get("category"),
                    row.get("document_type"),
                    row.get("reference_number"),
                    row.get("tax_year"),
                    row.get("notes"),
                    row.get("source_row_json"),
                    1,
                    now,
                ),
            )
        conn.commit()

    return PaymentImportResponse(
        payment_import_id=payment_import_id,
        filename=filename,
        status=status,
        records_created=len(payment_rows),
        payees_identified=len({row["payee_name"] for row in payment_rows if row["payee_name"]}),
        notes=notes,
    )


@app.post("/payments/records")
def create_payment_record(record: PaymentRecordCreate, x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "operator")
    payee_name = record.payee_name.strip()
    if not payee_name:
        raise HTTPException(status_code=400, detail="Payee name is required")

    now = datetime.now(timezone.utc).isoformat()
    normalized_date = normalize_date(record.payment_date) if record.payment_date else None
    tax_year = int(normalized_date[:4]) if normalized_date else None

    with connect(DB_PATH) as conn:
        manual_import_id = f"manual-{uuid.uuid4().hex}"
        conn.execute(
            """
            INSERT INTO payment_imports (id, filename, source_hash, uploaded_at, status, row_count, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (manual_import_id, "Manual Entry", None, now, "completed", 1, "Created from the Payments workspace form."),
        )
        upsert_payee_profile(
            conn,
            {
                "name": payee_name,
                "tax_id": record.tax_id,
                "payee_type": "contractor",
            },
            now,
        )
        payee = conn.execute("SELECT id, name, tax_id FROM payees WHERE name = ?", (payee_name,)).fetchone()
        if payee is None:
            raise HTTPException(status_code=500, detail="Unable to create payee")

        conn.execute(
            """
            INSERT INTO payment_records
            (payment_import_id, payee_id, payment_date, amount, category, document_type, reference_number, tax_year, notes, source_row_json, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                manual_import_id,
                payee["id"],
                normalized_date,
                float(record.amount or 0),
                record.category,
                record.document_type,
                record.reference_number,
                tax_year,
                record.notes,
                json.dumps(record.model_dump()),
                1,
                now,
            ),
        )
        conn.commit()

    return {"status": "created", "payee_name": payee_name}


@app.get("/companies")
def list_company_profiles():
    with connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT id, name, legal_name, tax_id, address_line1, address_line2, city, state, zip_code, email, phone, is_default, created_at, updated_at
            FROM company_profiles
            ORDER BY is_default DESC, name ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/companies")
def create_company_profile(company: CompanyProfilePayload, x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "operator")
    now = datetime.now(timezone.utc).isoformat()
    with connect(DB_PATH) as conn:
        if company.is_default:
            conn.execute("UPDATE company_profiles SET is_default = 0")
        cursor = conn.execute(
            """
            INSERT INTO company_profiles
            (name, legal_name, tax_id, address_line1, address_line2, city, state, zip_code, email, phone, is_default, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company.name,
                company.legal_name,
                company.tax_id,
                company.address_line1,
                company.address_line2,
                company.city,
                company.state,
                company.zip_code,
                company.email,
                company.phone,
                1 if company.is_default else 0,
                now,
                now,
            ),
        )
        company_id = cursor.lastrowid
        conn.commit()
        row = conn.execute(
            """
            SELECT id, name, legal_name, tax_id, address_line1, address_line2, city, state, zip_code, email, phone, is_default, created_at, updated_at
            FROM company_profiles
            WHERE id = ?
            """,
            (company_id,),
        ).fetchone()
    return dict(row) if row is not None else {}


@app.put("/companies/{company_id}")
def update_company_profile(company_id: int, company: CompanyProfilePayload, x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "operator")
    now = datetime.now(timezone.utc).isoformat()
    with connect(DB_PATH) as conn:
        if company.is_default:
            conn.execute("UPDATE company_profiles SET is_default = 0")
        conn.execute(
            """
            UPDATE company_profiles
            SET name = ?, legal_name = ?, tax_id = ?, address_line1 = ?, address_line2 = ?, city = ?, state = ?, zip_code = ?, email = ?, phone = ?, is_default = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                company.name,
                company.legal_name,
                company.tax_id,
                company.address_line1,
                company.address_line2,
                company.city,
                company.state,
                company.zip_code,
                company.email,
                company.phone,
                1 if company.is_default else 0,
                now,
                company_id,
            ),
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT id, name, legal_name, tax_id, address_line1, address_line2, city, state, zip_code, email, phone, is_default, created_at, updated_at
            FROM company_profiles
            WHERE id = ?
            """,
            (company_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return dict(row)


@app.delete("/companies/{company_id}")
def delete_company_profile(company_id: int, x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "operator")
    with connect(DB_PATH) as conn:
        conn.execute("UPDATE payer_profiles SET company_id = NULL WHERE company_id = ?", (company_id,))
        cursor = conn.execute("DELETE FROM company_profiles WHERE id = ?", (company_id,))
        conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"status": "deleted", "company_id": company_id}


@app.get("/profiles/payers")
def list_payer_profiles():
    with connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT p.id, p.company_id, c.name AS company_name, p.name, p.tax_id, p.address_line1, p.address_line2, p.city, p.state, p.zip_code, p.email, p.phone, p.is_default, p.created_at, p.updated_at
            FROM payer_profiles p
            LEFT JOIN company_profiles c ON c.id = p.company_id
            ORDER BY p.is_default DESC, p.name ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/profiles/payer")
def get_payer_profile():
    return get_default_payer_profile()


@app.post("/profiles/payer")
def save_payer_profile(profile: PayerProfilePayload, x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "operator")
    now = datetime.now(timezone.utc).isoformat()
    with connect(DB_PATH) as conn:
        existing = conn.execute("SELECT id FROM payer_profiles ORDER BY id ASC LIMIT 1").fetchone()
        conn.execute("UPDATE payer_profiles SET is_default = 0")
        if existing:
            conn.execute(
                """
                UPDATE payer_profiles
                SET company_id = ?, name = ?, tax_id = ?, address_line1 = ?, address_line2 = ?, city = ?, state = ?, zip_code = ?, email = ?, phone = ?, is_default = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    profile.company_id,
                    profile.name,
                    profile.tax_id,
                    profile.address_line1,
                    profile.address_line2,
                    profile.city,
                    profile.state,
                    profile.zip_code,
                    profile.email,
                    profile.phone,
                    1,
                    now,
                    existing["id"],
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO payer_profiles
                (company_id, name, tax_id, address_line1, address_line2, city, state, zip_code, email, phone, is_default, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    profile.company_id,
                    profile.name,
                    profile.tax_id,
                    profile.address_line1,
                    profile.address_line2,
                    profile.city,
                    profile.state,
                    profile.zip_code,
                    profile.email,
                    profile.phone,
                    now,
                    now,
                ),
            )
        conn.commit()
    return get_default_payer_profile()


@app.post("/profiles/payers")
def create_payer_profile(profile: PayerProfilePayload, x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "operator")
    now = datetime.now(timezone.utc).isoformat()
    with connect(DB_PATH) as conn:
        existing_count = conn.execute("SELECT COUNT(*) AS n FROM payer_profiles").fetchone()["n"]
        if profile.is_default:
            conn.execute("UPDATE payer_profiles SET is_default = 0")
        is_default = 1 if profile.is_default or existing_count == 0 else 0
        cursor = conn.execute(
            """
            INSERT INTO payer_profiles
            (company_id, name, tax_id, address_line1, address_line2, city, state, zip_code, email, phone, is_default, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile.company_id,
                profile.name,
                profile.tax_id,
                profile.address_line1,
                profile.address_line2,
                profile.city,
                profile.state,
                profile.zip_code,
                profile.email,
                profile.phone,
                is_default,
                now,
                now,
            ),
        )
        payer_id = cursor.lastrowid
        conn.commit()
    return {"status": "created", "payer_id": payer_id}


@app.put("/profiles/payers/{payer_id}")
def update_payer_profile(payer_id: int, profile: PayerProfilePayload, x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "operator")
    now = datetime.now(timezone.utc).isoformat()
    with connect(DB_PATH) as conn:
        if profile.is_default:
            conn.execute("UPDATE payer_profiles SET is_default = 0")
        conn.execute(
            """
            UPDATE payer_profiles
            SET company_id = ?, name = ?, tax_id = ?, address_line1 = ?, address_line2 = ?, city = ?, state = ?, zip_code = ?, email = ?, phone = ?, is_default = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                profile.company_id,
                profile.name,
                profile.tax_id,
                profile.address_line1,
                profile.address_line2,
                profile.city,
                profile.state,
                profile.zip_code,
                profile.email,
                profile.phone,
                1 if profile.is_default else 0,
                now,
                payer_id,
            ),
        )
        conn.commit()
    return {"status": "updated", "payer_id": payer_id}


@app.delete("/profiles/payers/{payer_id}")
def delete_payer_profile(payer_id: int, x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "operator")
    with connect(DB_PATH) as conn:
        cursor = conn.execute("DELETE FROM payer_profiles WHERE id = ?", (payer_id,))
        conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Payer profile not found")
    return {"status": "deleted", "payer_id": payer_id}


@app.get("/payments/payees")
def list_payment_payees(search: str = "", limit: int = 200, offset: int = 0):
    params: List[Any] = []
    where = "1=1"
    if search.strip():
        where = "name LIKE ? OR COALESCE(tax_id, '') LIKE ?"
        like = f"%{search.strip()}%"
        params.extend([like, like])
    with connect(DB_PATH) as conn:
        rows = conn.execute(
            f"""
            SELECT id, name, tax_id, payee_type, address_line1, address_line2, city, state, zip_code, email, phone, created_at
            FROM payees
            WHERE {where}
            ORDER BY name ASC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/payments/payees")
def save_payment_payee(payee: PayeeProfilePayload, x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "operator")
    now = datetime.now(timezone.utc).isoformat()
    with connect(DB_PATH) as conn:
        payee_id = upsert_payee_profile(conn, payee.model_dump(), now)
        conn.commit()
        row = conn.execute(
            """
            SELECT id, name, tax_id, payee_type, address_line1, address_line2, city, state, zip_code, email, phone, created_at
            FROM payees
            WHERE id = ?
            """,
            (payee_id,),
        ).fetchone()
    return dict(row) if row is not None else {}


@app.put("/payments/payees/{payee_id}")
def update_payment_payee(payee_id: int, payee: PayeeProfilePayload, x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "operator")
    with connect(DB_PATH) as conn:
        existing = conn.execute("SELECT id FROM payees WHERE id = ?", (payee_id,)).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Payee not found")
        conn.execute(
            """
            UPDATE payees
            SET name = ?, tax_id = ?, payee_type = ?, address_line1 = ?, address_line2 = ?, city = ?, state = ?, zip_code = ?, email = ?, phone = ?
            WHERE id = ?
            """,
            (
                payee.name,
                payee.tax_id,
                payee.payee_type,
                payee.address_line1,
                payee.address_line2,
                payee.city,
                payee.state,
                payee.zip_code,
                payee.email,
                payee.phone,
                payee_id,
            ),
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT id, name, tax_id, payee_type, address_line1, address_line2, city, state, zip_code, email, phone, created_at
            FROM payees
            WHERE id = ?
            """,
            (payee_id,),
        ).fetchone()
    return dict(row) if row is not None else {}


@app.delete("/payments/payees/{payee_id}")
def delete_payment_payee(payee_id: int, x_user_role: Optional[str] = Header(default=None)):
    require_role(x_user_role, "operator")
    with connect(DB_PATH) as conn:
        count = conn.execute("SELECT COUNT(*) AS n FROM payment_records WHERE payee_id = ?", (payee_id,)).fetchone()["n"]
        if count:
            raise HTTPException(status_code=400, detail="Cannot delete payee with linked payment records")
        cursor = conn.execute("DELETE FROM payees WHERE id = ?", (payee_id,))
        conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Payee not found")
    return {"status": "deleted", "payee_id": payee_id}


@app.get("/payments/imports")
def list_payment_imports(limit: int = 50, offset: int = 0):
    with connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT id, filename, uploaded_at, status, row_count, notes
            FROM payment_imports
            ORDER BY uploaded_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/payments/records")
def list_payment_records(
    search: str = "",
    tax_year: Optional[int] = None,
    include_history: bool = False,
    limit: int = 300,
    offset: int = 0,
):
    where = ["1=1"]
    params: List[Any] = []
    if search.strip():
        like = f"%{search.strip()}%"
        where.append("(p.name LIKE ? OR COALESCE(pr.category, '') LIKE ? OR COALESCE(pr.reference_number, '') LIKE ?)")
        params.extend([like, like, like])
    if tax_year is not None:
        where.append("pr.tax_year = ?")
        params.append(tax_year)
    if not include_history:
        where.append("pr.is_active = 1")

    with connect(DB_PATH) as conn:
        rows = conn.execute(
            f"""
            SELECT
              pr.id,
              pr.payment_import_id,
              pi.filename,
              pi.uploaded_at,
              p.name AS payee_name,
              p.tax_id,
              p.payee_type,
              pr.payment_date,
              pr.amount,
              pr.category,
              pr.document_type,
              pr.reference_number,
              pr.tax_year,
              pr.notes,
              pr.is_active
            FROM payment_records pr
            JOIN payees p ON p.id = pr.payee_id
            LEFT JOIN payment_imports pi ON pi.id = pr.payment_import_id
            WHERE {' AND '.join(where)}
            ORDER BY COALESCE(pr.payment_date, '') DESC, p.name ASC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/payments/summary")
def payment_summary(tax_year: Optional[int] = None, include_history: bool = False):
    return build_4806sp_payee_rows(tax_year or datetime.now().year, include_history)


@app.get("/payments/4806sp/summary")
def payment_4806sp_summary(tax_year: Optional[int] = None, include_history: bool = False):
    return build_4806sp_payee_rows(tax_year or datetime.now().year, include_history)


@app.get("/payments/4806sp/payees/{payee_id}/prefill")
def payment_4806sp_prefill(payee_id: int, tax_year: Optional[int] = None, include_history: bool = False):
    year_value = tax_year or datetime.now().year
    history_clause = "" if include_history else "AND pr.is_active = 1"
    payer_profile = get_default_payer_profile()
    with connect(DB_PATH) as conn:
        payee = conn.execute(
            """
            SELECT id, name, tax_id, payee_type, address_line1, address_line2, city, state, zip_code, email, phone
            FROM payees
            WHERE id = ?
            """,
            (payee_id,),
        ).fetchone()
        if payee is None:
            raise HTTPException(status_code=404, detail="Payee not found")

        totals = conn.execute(
            f"""
            SELECT
              COUNT(*) AS payments_count,
              SUM(pr.amount) AS amount_total,
              MIN(pr.payment_date) AS first_payment_date,
              MAX(pr.payment_date) AS last_payment_date,
              GROUP_CONCAT(DISTINCT COALESCE(NULLIF(TRIM(pr.category), ''), '(uncategorized)')) AS categories
            FROM payment_records pr
            WHERE pr.payee_id = ?
              AND COALESCE(pr.tax_year, ?) = ?
              {history_clause}
            """,
            (payee_id, year_value, year_value),
        ).fetchone()

        rows = conn.execute(
            f"""
            SELECT payment_date, amount, category, document_type, reference_number, notes
            FROM payment_records pr
            WHERE pr.payee_id = ?
              AND COALESCE(pr.tax_year, ?) = ?
              {history_clause}
            ORDER BY COALESCE(pr.payment_date, '') ASC
            """,
            (payee_id, year_value, year_value),
        ).fetchall()

    issues = []
    if not payer_profile.get("tax_id"):
        issues.append("Missing payer tax ID")
    if not payee["tax_id"]:
        issues.append("Missing payee tax ID")
    if not payer_profile.get("address_line1") or not payer_profile.get("zip_code"):
        issues.append("Missing payer address")
    if not payee["address_line1"] or not payee["zip_code"]:
        issues.append("Missing payee address")
    if not totals["payments_count"]:
        issues.append("No payments found for selected tax year")
    if (totals["amount_total"] or 0) <= 0:
        issues.append("Payment total is not positive")

    return {
        "form": "480.6SP",
        "tax_year": year_value,
        "autofill_ready": len(issues) == 0,
        "issues": issues,
        "prefill_packet": {
            "payer_name": payer_profile.get("name", ""),
            "payer_tax_id": payer_profile.get("tax_id", ""),
            "payer_address_line1": payer_profile.get("address_line1", ""),
            "payer_address_line2": payer_profile.get("address_line2", ""),
            "payer_city": payer_profile.get("city", ""),
            "payer_state": payer_profile.get("state", ""),
            "payer_zip_code": payer_profile.get("zip_code", ""),
            "recipient_name": payee["name"],
            "recipient_tax_id": payee["tax_id"] or "",
            "recipient_type": payee["payee_type"],
            "recipient_address_line1": payee["address_line1"] or "",
            "recipient_address_line2": payee["address_line2"] or "",
            "recipient_city": payee["city"] or "",
            "recipient_state": payee["state"] or "",
            "recipient_zip_code": payee["zip_code"] or "",
            "services_total": totals["amount_total"] or 0,
            "payments_count": totals["payments_count"] or 0,
            "first_payment_date": totals["first_payment_date"],
            "last_payment_date": totals["last_payment_date"],
            "service_categories": [] if not totals["categories"] else str(totals["categories"]).split(","),
        },
        "records": [dict(row) for row in rows],
        "note": "This prefill packet is structured for future PDF field mapping. Exact PDF autofill depends on the official fillable 480.6SP field names.",
    }


@app.get("/payments/4806sp/payees/{payee_id}/draft-pdf")
def payment_4806sp_draft_pdf(payee_id: int, tax_year: Optional[int] = None, include_history: bool = False):
    prefill = payment_4806sp_prefill(payee_id, tax_year=tax_year, include_history=include_history)
    pdf_path = generate_4806sp_draft_pdf(prefill)
    filename = f"480.6SP_draft_{payee_id}_{prefill['tax_year']}.pdf"
    return FileResponse(pdf_path, media_type="application/pdf", filename=filename)


def rule_failures(df: pd.DataFrame, rule: Rule) -> List[Dict[str, Any]]:
    failures = []

    if rule.type == "not_empty":
        if rule.column not in df.columns:
            return [
                {"row_number": int(idx) + 2, "value": None, "message": "Missing column"}
                for idx in df.index
            ]
        series = df[rule.column]
        mask = series.isna() | (series.astype(str).str.strip() == "")
    elif rule.type == "number_range":
        if rule.column not in df.columns:
            return [
                {"row_number": int(idx) + 2, "value": None, "message": "Missing column"}
                for idx in df.index
            ]
        series = df[rule.column]
        numeric = pd.to_numeric(series, errors="coerce")
        mask = numeric.isna()
        if rule.min is not None:
            mask = mask | (numeric < rule.min)
        if rule.max is not None:
            mask = mask | (numeric > rule.max)
    elif rule.type == "allowed_values":
        if rule.column not in df.columns:
            return [
                {"row_number": int(idx) + 2, "value": None, "message": "Missing column"}
                for idx in df.index
            ]
        series = df[rule.column]
        allowed = rule.allowed or []
        mask = ~series.astype(str).isin([str(val) for val in allowed])
    elif rule.type == "conditional_required":
        when_col = rule.when_column or ""
        then_col = rule.then_column or ""
        if when_col not in df.columns or then_col not in df.columns:
            return [
                {"row_number": int(idx) + 2, "value": None, "message": "Missing column"}
                for idx in df.index
            ]
        when_series = df[when_col].astype(str).str.strip()
        then_series = df[then_col]
        series = then_series
        target = (rule.when_equals or "").strip()
        operator = (rule.when_operator or "equals").lower()
        if operator == "contains":
            match = when_series.str.contains(target, na=False)
        else:
            match = when_series == target
        missing = then_series.isna() | (then_series.astype(str).str.strip() == "")
        mask = match & missing
    else:
        series = df[rule.column] if rule.column in df.columns else pd.Series([None] * len(df), index=df.index)
        mask = pd.Series([True] * len(series), index=series.index)

    for idx in series.index[mask]:
        value = series.loc[idx]
        failures.append(
            {
                "row_number": int(idx) + 2,
                "value": None if pd.isna(value) else str(value),
                "message": "Rule failed",
            }
        )

    return failures


def classify_task_series(task_series: pd.Series) -> tuple[pd.Series, pd.Series]:
    task_text = task_series.astype(str)
    enfermeria_match = task_text.str.contains(r"\b(?:RN|HHA)\b|Consult", case=False, na=False, regex=True)
    terapia_match = task_text.str.contains(r"\b(?:ST|OT|PT|PTA)\b", case=False, na=False, regex=True) & ~enfermeria_match
    return terapia_match, enfermeria_match


def read_uploaded_dataframe(file: UploadFile) -> tuple[pd.DataFrame, str]:
    if file.filename is None:
        raise HTTPException(status_code=400, detail="File name is required")

    filename = file.filename.lower()
    if not (filename.endswith(".xlsx") or filename.endswith(".xls") or filename.endswith(".csv")):
        raise HTTPException(status_code=400, detail="Only .xlsx, .xls, or .csv files are supported")

    try:
        raw_bytes = file.file.read()
        source_hash = hashlib.sha256(raw_bytes).hexdigest()
        if filename.endswith(".csv"):
            text = raw_bytes.decode("utf-8-sig", errors="replace")
            return pd.read_csv(io.StringIO(text)), source_hash
        return pd.read_excel(io.BytesIO(raw_bytes)), source_hash
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read input file: {exc}") from exc


def read_upload_bytes(file: UploadFile) -> tuple[bytes, str]:
    if file.filename is None:
        raise HTTPException(status_code=400, detail="File name is required")
    try:
        raw_bytes = file.file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {exc}") from exc
    return raw_bytes, hashlib.sha256(raw_bytes).hexdigest()


def try_read_tabular_bytes(filename: str, raw_bytes: bytes) -> pd.DataFrame | None:
    lower_name = filename.lower()
    try:
        if lower_name.endswith(".csv"):
            return pd.read_csv(io.StringIO(raw_bytes.decode("utf-8-sig", errors="replace")))
        if lower_name.endswith(".xlsx") or lower_name.endswith(".xls"):
            return pd.read_excel(io.BytesIO(raw_bytes))
    except Exception:
        return None
    return None


def parse_number(value: Any) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text == "":
        return 0.0
    negative_parentheses = text.startswith("(") and text.endswith(")")
    cleaned = re.sub(r"[^0-9.\\-]", "", text.replace(",", ""))
    if cleaned in {"", "-", ".", "-."}:
        return 0.0
    try:
        value_num = float(cleaned)
        if negative_parentheses and value_num > 0:
            value_num = -value_num
        return value_num
    except ValueError:
        return 0.0


def derive_employee_series_from_markers(df: pd.DataFrame) -> pd.Series:
    derived = pd.Series([""] * len(df), index=df.index, dtype="string")
    marker_text = "payroll summary"
    current_employee = ""
    for row_idx in range(len(df)):
        row_values = ["" if pd.isna(v) else str(v).strip().casefold() for v in df.iloc[row_idx].tolist()]
        if marker_text in row_values:
            next_row = row_idx + 1
            current_employee = ""
            if next_row < len(df):
                for value in df.iloc[next_row].tolist():
                    if pd.isna(value):
                        continue
                    text = str(value).strip()
                    if text:
                        current_employee = text
                        break
            continue
        derived.iloc[row_idx] = current_employee
    return derived


def normalize_date(value: Any) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text == "":
        return None
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date().isoformat()


def save_payment_document(import_id: str, filename: str, raw_bytes: bytes) -> str:
    PAYMENT_DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", filename) or "payment_document"
    stored_name = f"{import_id}_{safe_name}"
    output_path = PAYMENT_DOCUMENTS_DIR / stored_name
    output_path.write_bytes(raw_bytes)
    return str(output_path)


def create_payment_rows_from_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]

    def find_column(options: List[str]) -> str | None:
        lowered = {str(col).strip().casefold(): col for col in df.columns}
        for option in options:
            matched = lowered.get(option.casefold())
            if matched is not None:
                return matched
        return None

    payee_col = find_column(["Employee", "Payee", "Payee Name", "Vendor", "Name"])
    amount_col = find_column(["Amount", "Payment Amount", "Total", "Net Amount"])
    date_col = find_column(["Date", "Payment Date", "Paid Date", "Check Date"])
    category_col = find_column(["Category", "Service Type", "Type"])
    tax_id_col = find_column(["Tax ID", "TIN", "SSN", "EIN"])
    ref_col = find_column(["Reference", "Reference Number", "Check Number", "Receipt Number"])
    doc_type_col = find_column(["Document Type", "Payment Method", "Method"])
    notes_col = find_column(["Notes", "Memo", "Description"])

    if payee_col is None or amount_col is None:
        raise HTTPException(
            status_code=400,
            detail="Payment spreadsheet must contain payee and amount columns. Accepted payee headers include Employee, Payee, Vendor, or Name.",
        )

    rows: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        payee_name = "" if pd.isna(row.get(payee_col)) else str(row.get(payee_col)).strip()
        if not payee_name:
            continue
        payment_date = normalize_date(row.get(date_col)) if date_col else None
        amount = parse_number(row.get(amount_col))
        if amount == 0 and not payment_date and not payee_name:
            continue
        tax_year = None
        if payment_date:
            try:
                tax_year = int(payment_date[:4])
            except ValueError:
                tax_year = None
        source_row = {key: (None if pd.isna(value) else str(value)) for key, value in row.to_dict().items()}
        rows.append(
            {
                "payee_name": payee_name,
                "payment_date": payment_date,
                "amount": amount,
                "category": None if category_col is None or pd.isna(row.get(category_col)) else str(row.get(category_col)).strip(),
                "document_type": None if doc_type_col is None or pd.isna(row.get(doc_type_col)) else str(row.get(doc_type_col)).strip(),
                "reference_number": None if ref_col is None or pd.isna(row.get(ref_col)) else str(row.get(ref_col)).strip(),
                "tax_id": None if tax_id_col is None or pd.isna(row.get(tax_id_col)) else str(row.get(tax_id_col)).strip(),
                "notes": None if notes_col is None or pd.isna(row.get(notes_col)) else str(row.get(notes_col)).strip(),
                "tax_year": tax_year,
                "source_row_json": json.dumps(source_row),
            }
        )
    return rows


@app.post("/validate", response_model=ValidationResponse)
def validate_file(
    file: UploadFile = File(...),
    rule_ids: Optional[str] = Form(default=None),
    categories: Optional[str] = Form(default=None),
    discipline_filter: Optional[str] = Form(default=None),
    check_for_completion: Optional[str] = Form(default=None),
    mileage_cost: Optional[str] = Form(default=None),
    x_user_role: Optional[str] = Header(default=None),
):
    require_role(x_user_role, "operator")
    df, _ = read_uploaded_dataframe(file)
    df.columns = [str(col).strip() for col in df.columns]

    all_rules = load_rules()
    selected_rules = all_rules

    if rule_ids:
        try:
            requested = set(json.loads(rule_ids))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Invalid rule_ids payload") from exc
        selected_rules = [rule for rule in all_rules if rule.id in requested]

    if not selected_rules:
        raise HTTPException(status_code=400, detail="No rules selected")

    selected_categories: List[str] = []
    if categories:
        try:
            selected_categories = [str(item) for item in json.loads(categories)]
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Invalid categories payload") from exc

    discipline_enabled = str(discipline_filter or "").lower() in {"true", "1", "yes"}
    completion_check_enabled = str(check_for_completion or "").lower() in {"true", "1", "yes"}
    try:
        mileage_cost_value = float(mileage_cost) if mileage_cost is not None and str(mileage_cost).strip() != "" else 1.0
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Mileage cost must be a number") from exc

    employee_series = pd.Series([""] * len(df), index=df.index, dtype="string")
    if "Employee" in df.columns:
        employee_series = df["Employee"].fillna("").astype(str).str.strip()

    enfermeria_match = pd.Series([False] * len(df), index=df.index)
    terapia_match = pd.Series([False] * len(df), index=df.index)
    if "Task" in df.columns:
        terapia_match, enfermeria_match = classify_task_series(df["Task"])

    employee_non_empty = employee_series != ""
    all_employees = set(employee_series[employee_non_empty].unique().tolist())
    enfermeria_employee_set = set(employee_series[enfermeria_match & employee_non_empty].unique().tolist())
    terapia_candidate_set = set(employee_series[terapia_match & employee_non_empty].unique().tolist())
    terapia_employee_set = terapia_candidate_set - enfermeria_employee_set
    unclassified_employee_set = all_employees - enfermeria_employee_set - terapia_candidate_set

    total_employees = len(all_employees)
    terapia_employees = len(terapia_employee_set)
    enfermeria_employees = len(enfermeria_employee_set)
    unclassified_employees = len(unclassified_employee_set)

    employee_in_terapia = employee_series.isin(terapia_employee_set)
    employee_in_enfermeria = employee_series.isin(enfermeria_employee_set)
    employee_in_unclassified = employee_series.isin(unclassified_employee_set)

    failures_rows_union = set()
    rule_summaries: List[RuleSummary] = []
    failures_output = []

    for rule in selected_rules:
        failures = rule_failures(df, rule)
        failed_rows = [item["row_number"] for item in failures]
        failures_rows_union.update(failed_rows)
        rule_summaries.append(
            RuleSummary(
                rule_id=rule.id,
                rule_name=rule.name,
                column=rule.column,
                failed_rows=len(failed_rows),
                passed_rows=max(len(df) - len(failed_rows), 0),
                total_rows=len(df),
            )
        )
        for item in failures:
            failures_output.append(
                {
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "column": rule.column,
                    "row_number": item["row_number"],
                    "value": item["value"],
                    "message": item["message"],
                }
            )

    summary = {
        "total_rows": len(df),
        "total_rules": len(selected_rules),
        "failed_rows": len(failures_rows_union),
        "passed_rows": max(len(df) - len(failures_rows_union), 0),
        "total_employees": total_employees,
        "terapia_employees": terapia_employees,
        "enfermeria_employees": enfermeria_employees,
        "unclassified_employees": unclassified_employees,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_id = uuid.uuid4().hex
    report_path = REPORTS_DIR / f"validation_report_{report_id}.xlsx"

    summary_df = pd.DataFrame([summary])
    rule_summary_df = pd.DataFrame([item.model_dump() for item in rule_summaries])
    failures_df = pd.DataFrame(failures_output)

    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Original", index=False)
        if selected_categories and "Discipline" in df.columns:
            discipline_series = df["Discipline"].astype(str).str.strip()
            normalized_categories = {str(category).strip().casefold(): str(category).strip() for category in selected_categories}
            for category in selected_categories:
                category_key = str(category).strip().casefold()
                sheet_rows = df[discipline_series.str.casefold() == category_key]
                safe_name = normalized_categories.get(category_key, str(category))[:31] or "Category"
                sheet_rows.to_excel(writer, sheet_name=safe_name, index=False)
        if discipline_enabled and {"Task", "Employee"}.issubset(df.columns):
            def build_summary_from_mask(match: pd.Series, sheet_name: str) -> None:
                subset = df[match].copy()
                if subset.empty:
                    pd.DataFrame(columns=["Employee", "Rate", "Millage", "Surcharge", "Amount"]).to_excel(
                        writer, sheet_name=sheet_name[:31], index=False
                    )
                    return

                numeric_map = {
                    "Rate": ["Rate"],
                    "Millage": ["Millage", "Mileage"],
                    "Surcharge": ["Surcharge"],
                    "Amount": ["Amount"],
                }
                for canonical, aliases in numeric_map.items():
                    source_col = next((col for col in aliases if col in subset.columns), None)
                    if source_col:
                        subset[canonical] = pd.to_numeric(subset[source_col], errors="coerce").fillna(0)
                    else:
                        subset[canonical] = 0
                subset["Millage"] = subset["Millage"] * mileage_cost_value

                summary = (
                    subset.groupby("Employee", as_index=False)[["Rate", "Millage", "Surcharge", "Amount"]].sum()
                )
                summary.to_excel(writer, sheet_name=sheet_name[:31], index=False)

            build_summary_from_mask(terapia_match & employee_in_terapia, "Terapia")
            build_summary_from_mask(enfermeria_match & employee_in_enfermeria, "Enfermeria")

            unclassified_rows = df[employee_in_unclassified].copy()
            if not unclassified_rows.empty:
                unclassified_rows["Classification Note"] = "Employee has no Task token RN/HHA/ST/OT/PT."
            else:
                unclassified_rows = pd.DataFrame(
                    columns=list(df.columns) + ["Classification Note"]
                )
            unclassified_rows.to_excel(writer, sheet_name="Unclassified Employees", index=False)
        if completion_check_enabled and "Task Status" in df.columns:
            status_series = df["Task Status"].astype(str).str.strip()
            incomplete_rows = df[status_series.str.casefold() != "completed"]
            incomplete_rows.to_excel(writer, sheet_name="Check for Completion", index=False)

    return ValidationResponse(summary=summary, rules=rule_summaries, report_id=report_id)


@app.post("/process-payroll-summary", response_model=SummaryToolResponse)
def process_payroll_summary(
    file: UploadFile = File(...),
    mileage_cost: Optional[str] = Form(default=None),
    x_user_role: Optional[str] = Header(default=None),
):
    require_role(x_user_role, "operator")
    df, _ = read_uploaded_dataframe(file)
    df.columns = [str(col).strip() for col in df.columns]

    if df.shape[1] < 5:
        raise HTTPException(status_code=400, detail="Input must contain at least 5 columns.")
    try:
        mileage_cost_value = float(mileage_cost) if mileage_cost is not None and str(mileage_cost).strip() != "" else 1.0
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Mileage cost must be a number") from exc

    marker_text = "payroll summary"

    def first_non_empty_in_row(row_idx: int) -> str:
        if row_idx >= len(df):
            return ""
        for value in df.iloc[row_idx].tolist():
            if pd.isna(value):
                continue
            text = str(value).strip()
            if text:
                return text
        return ""

    # Split into section boundaries where a row contains the marker token in any cell.
    marker_rows: List[int] = []
    for row_idx in range(len(df)):
        row_values = ["" if pd.isna(v) else str(v).strip().casefold() for v in df.iloc[row_idx].tolist()]
        if marker_text in row_values:
            marker_rows.append(row_idx)

    section_records: List[Dict[str, Any]] = []
    for marker_pos, marker_row in enumerate(marker_rows):
        section_end = marker_rows[marker_pos + 1] if marker_pos + 1 < len(marker_rows) else len(df)
        employee_name = first_non_empty_in_row(marker_row + 1)

        # In each section, identify header columns by looking for Task/Rate/Mileage/Surcharge labels.
        task_col = -1
        rate_col = -1
        mileage_col = -1
        surcharge_col = -1
        header_row = -1
        for row_idx in range(marker_row + 2, section_end):
            normalized_cells = ["" if pd.isna(v) else str(v).strip().casefold() for v in df.iloc[row_idx].tolist()]
            has_task = "task" in normalized_cells
            has_rate = "rate" in normalized_cells
            has_mileage = "mileage" in normalized_cells
            has_surcharge = any(label in normalized_cells for label in ["surcharge", "surchage"])
            if has_task and has_rate and has_mileage and has_surcharge:
                header_row = row_idx
                task_col = normalized_cells.index("task")
                rate_col = normalized_cells.index("rate")
                mileage_col = normalized_cells.index("mileage")
                surcharge_col = (
                    normalized_cells.index("surcharge")
                    if "surcharge" in normalized_cells
                    else normalized_cells.index("surchage")
                )
                break

        if header_row == -1 or employee_name == "":
            continue

        # Classification uses all task tokens in the section body.
        task_tokens: List[str] = []
        last_value_row = -1
        for row_idx in range(header_row + 1, section_end):
            row_values = df.iloc[row_idx].tolist()
            task_value = row_values[task_col] if task_col < len(row_values) else ""
            task_text = "" if pd.isna(task_value) else str(task_value).strip()
            if task_text:
                task_tokens.append(task_text)

            rate_value = row_values[rate_col] if rate_col < len(row_values) else ""
            mileage_value = row_values[mileage_col] if mileage_col < len(row_values) else ""
            surcharge_value = row_values[surcharge_col] if surcharge_col < len(row_values) else ""
            def has_numeric_token(v: Any) -> bool:
                if pd.isna(v):
                    return False
                return bool(re.search(r"\d", str(v)))

            if has_numeric_token(rate_value) or has_numeric_token(mileage_value) or has_numeric_token(surcharge_value):
                last_value_row = row_idx

        if last_value_row == -1:
            continue

        combined_tasks = " ".join(task_tokens)
        task_series = pd.Series([combined_tasks])
        terapia_match, enfermeria_match = classify_task_series(task_series)
        if bool(enfermeria_match.iloc[0]):
            classification = "Enfermeria"
        elif bool(terapia_match.iloc[0]):
            classification = "Terapia"
        else:
            classification = "Unclassified"

        section_values = df.iloc[last_value_row].tolist()
        section_records.append(
            {
                "Employee": employee_name,
                "Classification": classification,
                "Rate": parse_number(section_values[rate_col] if rate_col < len(section_values) else 0),
                "Mileage": parse_number(section_values[mileage_col] if mileage_col < len(section_values) else 0) * mileage_cost_value,
                "Surcharge": parse_number(section_values[surcharge_col] if surcharge_col < len(section_values) else 0),
            }
        )

    records_df = pd.DataFrame(section_records)
    if records_df.empty:
        totals_df = pd.DataFrame(columns=["Employee", "Classification", "Rate", "Mileage", "Surcharge"])
    else:
        totals_df = (
            records_df.groupby(["Employee", "Classification"], as_index=False)[["Rate", "Mileage", "Surcharge"]].sum()
        )
    terapia_totals_df = (
        totals_df[totals_df["Classification"] == "Terapia"][["Employee", "Rate", "Mileage", "Surcharge"]]
        .sort_values(by="Employee")
        .reset_index(drop=True)
    )
    enfermeria_totals_df = (
        totals_df[totals_df["Classification"] == "Enfermeria"][["Employee", "Rate", "Mileage", "Surcharge"]]
        .sort_values(by="Employee")
        .reset_index(drop=True)
    )

    summary = {
        "total_rows": len(df),
        "marker_count": len(marker_rows),
        "employees_identified": int(totals_df["Employee"].nunique()) if not totals_df.empty else 0,
        "terapia_employees": int(totals_df[totals_df["Classification"] == "Terapia"]["Employee"].nunique()) if not totals_df.empty else 0,
        "enfermeria_employees": int(totals_df[totals_df["Classification"] == "Enfermeria"]["Employee"].nunique()) if not totals_df.empty else 0,
        "unclassified_employees": int(totals_df[totals_df["Classification"] == "Unclassified"]["Employee"].nunique()) if not totals_df.empty else 0,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_id = uuid.uuid4().hex
    report_path = REPORTS_DIR / f"payroll_summary_report_{report_id}.xlsx"

    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Original", index=False)
        pd.DataFrame([summary]).to_excel(writer, sheet_name="Statistics", index=False)
        totals_df.to_excel(writer, sheet_name="Employee Totals", index=False)
        if terapia_totals_df.empty:
            terapia_totals_df = pd.DataFrame(columns=["Employee", "Rate", "Mileage", "Surcharge"])
        if enfermeria_totals_df.empty:
            enfermeria_totals_df = pd.DataFrame(columns=["Employee", "Rate", "Mileage", "Surcharge"])
        terapia_totals_df.to_excel(writer, sheet_name="Terapia", index=False)
        enfermeria_totals_df.to_excel(writer, sheet_name="Enfermeria", index=False)

    return SummaryToolResponse(summary=summary, report_id=report_id)


@app.post("/imports/payroll-summary", response_model=ImportResponse)
def create_payroll_summary_import(
    file: UploadFile = File(...),
    mileage_cost: Optional[str] = Form(default=None),
    x_user_role: Optional[str] = Header(default=None),
):
    require_role(x_user_role, "operator")
    df, source_hash = read_uploaded_dataframe(file)
    df.columns = [str(col).strip() for col in df.columns]
    if df.shape[1] < 6:
        raise HTTPException(status_code=400, detail="Expected at least 6 columns for Payroll Summary format.")

    try:
        mileage_cost_value = float(mileage_cost) if mileage_cost is not None and str(mileage_cost).strip() != "" else 1.0
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Mileage cost must be a number") from exc

    marker_rows: List[int] = []
    for idx in range(len(df)):
        first_cell = "" if pd.isna(df.iloc[idx, 0]) else str(df.iloc[idx, 0]).strip().casefold()
        if first_cell == "payroll summary":
            marker_rows.append(idx)

    if not marker_rows:
        raise HTTPException(status_code=400, detail="No Payroll Summary sections found in column A.")

    now = datetime.now(timezone.utc).isoformat()
    import_id = uuid.uuid4().hex
    filename = file.filename or "payroll_summary_upload"

    section_rows: List[Dict[str, Any]] = []
    for marker_index, marker_row in enumerate(marker_rows):
        section_end = marker_rows[marker_index + 1] if marker_index + 1 < len(marker_rows) else len(df)
        section_date = normalize_date(df.iloc[marker_row, 1]) if df.shape[1] > 1 else None

        employee_name = ""

        header_row = -1
        header_cells: List[str] = []
        for candidate_row in range(marker_row + 1, section_end):
            normalized = ["" if pd.isna(v) else str(v).strip().casefold() for v in df.iloc[candidate_row].tolist()]
            if "patient name" in normalized and "task" in normalized and "rate" in normalized and ("mileage" in normalized or "millage" in normalized):
                header_row = candidate_row
                header_cells = normalized
                break

        if header_row == -1:
            continue

        # Prefer extracting employee name from the row immediately after Payroll Summary.
        first_name_row = marker_row + 1
        if first_name_row < header_row:
            row_values = ["" if pd.isna(v) else str(v).strip() for v in df.iloc[first_name_row].tolist()]
            label_positions = [idx for idx, text in enumerate(row_values) if text.casefold() in {"employee name", "employee"}]
            if label_positions:
                for label_pos in label_positions:
                    for candidate in row_values[label_pos + 1:]:
                        if candidate and normalize_date(candidate) is None:
                            employee_name = candidate
                            break
                    if employee_name:
                        break
            if not employee_name:
                for text in row_values:
                    lowered = text.casefold()
                    if not text:
                        continue
                    if lowered in {"employee name", "employee", "payroll summary"}:
                        continue
                    if normalize_date(text) is not None:
                        continue
                    employee_name = text
                    break

        # Resolve employee name from any row between marker and header.
        for name_row in range(marker_row + 1, header_row):
            if employee_name:
                break
            row_values = ["" if pd.isna(v) else str(v).strip() for v in df.iloc[name_row].tolist()]
            for text in row_values:
                lowered = text.casefold()
                if not text:
                    continue
                if lowered in {"employee name", "employee", "payroll summary"}:
                    continue
                if normalize_date(text) is not None:
                    continue
                employee_name = text
                break
            if employee_name:
                break

        def find_index(candidates: List[str]) -> int:
            for i, cell in enumerate(header_cells):
                if cell in candidates:
                    return i
            return -1

        patient_col = find_index(["patient name"])
        task_col = find_index(["task"])
        rate_col = find_index(["rate"])
        mileage_col = find_index(["mileage", "millage"])
        surcharge_col = find_index(["surcharge", "surchage"])
        branch_col = find_index(["branch"])

        if employee_name == "":
            employee_name = f"Unknown Employee (Section {marker_index + 1})"

        if min(patient_col, task_col, rate_col, mileage_col, surcharge_col, branch_col) < 0:
            continue

        current_entry_date = section_date
        for row_idx in range(header_row + 1, section_end):
            row_values = df.iloc[row_idx].tolist()
            task_text = "" if pd.isna(row_values[task_col]) else str(row_values[task_col]).strip()
            patient_name = "" if pd.isna(row_values[patient_col]) else str(row_values[patient_col]).strip()
            branch = "" if pd.isna(row_values[branch_col]) else str(row_values[branch_col]).strip()

            # Date-group row inside section: update current date and apply it to following patient rows.
            inline_date = normalize_date(patient_name)
            if inline_date is not None and task_text == "":
                current_entry_date = inline_date
                continue

            if task_text == "":
                continue

            section_rows.append(
                {
                    "employee_name": employee_name,
                    "entry_date": current_entry_date,
                    "patient_name": patient_name,
                    "task": task_text,
                    "branch": branch,
                    "rate": parse_number(row_values[rate_col]),
                    # Persist raw spreadsheet mileage; multiplier is a view/report concern.
                    "mileage": parse_number(row_values[mileage_col]),
                    "surcharge": parse_number(row_values[surcharge_col]),
                    "amount": 0.0,
                    "row_index": row_idx,
                    "raw_row_json": json.dumps({k: (None if pd.isna(v) else str(v)) for k, v in df.iloc[row_idx].to_dict().items()}),
                }
            )

    task_series = pd.Series([row["task"] for row in section_rows], dtype="string")
    if len(task_series) > 0:
        terapia_match, enfermeria_match = classify_task_series(task_series)
    else:
        terapia_match = pd.Series([], dtype=bool)
        enfermeria_match = pd.Series([], dtype=bool)

    for idx, row in enumerate(section_rows):
        if idx < len(enfermeria_match) and bool(enfermeria_match.iloc[idx]):
            row["classification"] = "Enfermeria"
        elif idx < len(terapia_match) and bool(terapia_match.iloc[idx]):
            row["classification"] = "Terapia"
        else:
            row["classification"] = "Unclassified"

    with connect(DB_PATH) as conn:
        existing = conn.execute(
            "SELECT id FROM imports WHERE tool_type = ? AND source_hash = ? ORDER BY uploaded_at DESC LIMIT 1",
            ("payroll_summary", source_hash),
        ).fetchone()
        if existing:
            import_id = existing["id"]
            conn.execute("DELETE FROM work_entries WHERE import_id = ?", (import_id,))
            conn.execute(
                "UPDATE imports SET filename = ?, uploaded_at = ?, status = ?, row_count = ?, error_count = ? WHERE id = ?",
                (filename, now, "processing", 0, 0, import_id),
            )
        else:
            conn.execute(
                "INSERT INTO imports (id, filename, tool_type, source_hash, uploaded_at, status, row_count, error_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (import_id, filename, "payroll_summary", source_hash, now, "processing", 0, 0),
            )

        employee_names = sorted({row["employee_name"] for row in section_rows})
        for employee_name in employee_names:
            conn.execute("INSERT OR IGNORE INTO employees (name) VALUES (?)", (employee_name,))

        employee_ids = {
            row["name"]: row["id"]
            for row in conn.execute(
                "SELECT id, name FROM employees WHERE name IN ({})".format(",".join(["?"] * len(employee_names))),
                employee_names,
            ).fetchall()
        } if employee_names else {}

        # Employee-level upsert with history: deactivate prior payroll-summary rows for employees found in this import.
        employee_id_values = list(employee_ids.values())
        if employee_id_values:
            placeholders = ",".join(["?"] * len(employee_id_values))
            conn.execute(
                f"""
                UPDATE work_entries
                SET is_active = 0
                WHERE employee_id IN ({placeholders})
                  AND import_id IN (SELECT id FROM imports WHERE tool_type = ?)
                  AND import_id <> ?
                """,
                (*employee_id_values, "payroll_summary", import_id),
            )

        for row in section_rows:
            employee_id = employee_ids.get(row["employee_name"])
            if employee_id is None:
                continue
            conn.execute(
                """
                INSERT INTO work_entries
                (import_id, employee_id, task, entry_date, patient_name, branch, classification, rate, mileage, surcharge, amount, is_active, row_index, raw_row_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    import_id,
                    employee_id,
                    row["task"],
                    row["entry_date"],
                    row["patient_name"],
                    row["branch"],
                    row["classification"],
                    row["rate"],
                    row["mileage"],
                    row["surcharge"],
                    row["amount"],
                    1,
                    row["row_index"],
                    row["raw_row_json"],
                    now,
                ),
            )

        conn.execute("UPDATE imports SET status = ?, row_count = ? WHERE id = ?", ("completed", len(section_rows), import_id))
        conn.commit()

    employees_set = {row["employee_name"] for row in section_rows}
    terapia_set = {row["employee_name"] for row in section_rows if row["classification"] == "Terapia"}
    enfermeria_set = {row["employee_name"] for row in section_rows if row["classification"] == "Enfermeria"}
    unclassified_set = {row["employee_name"] for row in section_rows if row["classification"] == "Unclassified"}

    return ImportResponse(
        import_id=import_id,
        filename=filename,
        tool_type="payroll_summary",
        row_count=len(section_rows),
        employees_identified=len(employees_set),
        terapia_employees=len(terapia_set),
        enfermeria_employees=len(enfermeria_set),
        unclassified_employees=len(unclassified_set),
    )


@app.get("/report/{report_id}")
def download_report(report_id: str):
    candidate_paths = [
        REPORTS_DIR / f"validation_report_{report_id}.xlsx",
        REPORTS_DIR / f"payroll_summary_report_{report_id}.xlsx",
    ]
    report_path = next((path for path in candidate_paths if path.exists()), None)
    if report_path is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(report_path, filename=report_path.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
