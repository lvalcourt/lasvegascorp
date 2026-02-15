from __future__ import annotations

import json
import os
import re
import uuid
import io
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/rules", response_model=List[Rule])
def get_rules():
    return load_rules()


@app.post("/rules", response_model=List[Rule])
def update_rules(rules: List[Rule]):
    save_rules(rules)
    return rules


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


def read_uploaded_dataframe(file: UploadFile) -> pd.DataFrame:
    if file.filename is None:
        raise HTTPException(status_code=400, detail="File name is required")

    filename = file.filename.lower()
    if not (filename.endswith(".xlsx") or filename.endswith(".xls") or filename.endswith(".csv")):
        raise HTTPException(status_code=400, detail="Only .xlsx, .xls, or .csv files are supported")

    try:
        raw_bytes = file.file.read()
        if filename.endswith(".csv"):
            text = raw_bytes.decode("utf-8-sig", errors="replace")
            return pd.read_csv(io.StringIO(text))
        return pd.read_excel(io.BytesIO(raw_bytes))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read input file: {exc}") from exc


@app.post("/validate", response_model=ValidationResponse)
def validate_file(
    file: UploadFile = File(...),
    rule_ids: Optional[str] = Form(default=None),
    categories: Optional[str] = Form(default=None),
    discipline_filter: Optional[str] = Form(default=None),
    check_for_completion: Optional[str] = Form(default=None),
):
    df = read_uploaded_dataframe(file)
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
def process_payroll_summary(file: UploadFile = File(...)):
    df = read_uploaded_dataframe(file)
    df.columns = [str(col).strip() for col in df.columns]

    if df.shape[1] < 5:
        raise HTTPException(status_code=400, detail="Input must contain at least 5 columns.")

    marker_text = "payroll summary"

    def parse_number(value: Any) -> float:
        if pd.isna(value):
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if text == "":
            return 0.0
        negative_parentheses = text.startswith("(") and text.endswith(")")
        cleaned = re.sub(r"[^0-9.\-]", "", text.replace(",", ""))
        if cleaned in {"", "-", ".", "-."}:
            return 0.0
        try:
            value_num = float(cleaned)
            if negative_parentheses and value_num > 0:
                value_num = -value_num
            return value_num
        except ValueError:
            return 0.0

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
                "Mileage": parse_number(section_values[mileage_col] if mileage_col < len(section_values) else 0),
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
