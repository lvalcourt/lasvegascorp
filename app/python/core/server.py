from __future__ import annotations

import json
import os
import re
import uuid
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


@app.post("/validate", response_model=ValidationResponse)
def validate_file(
    file: UploadFile = File(...),
    rule_ids: Optional[str] = Form(default=None),
    categories: Optional[str] = Form(default=None),
    discipline_filter: Optional[str] = Form(default=None),
    check_for_completion: Optional[str] = Form(default=None),
):
    if file.filename is None:
        raise HTTPException(status_code=400, detail="File name is required")

    filename = file.filename.lower()
    if not (filename.endswith(".xlsx") or filename.endswith(".xls") or filename.endswith(".csv")):
        raise HTTPException(status_code=400, detail="Only .xlsx, .xls, or .csv files are supported")

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(file.file)
        else:
            df = pd.read_excel(file.file)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read input file: {exc}") from exc
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
            def build_summary(codes: List[str], sheet_name: str) -> None:
                pattern = "|".join(re.escape(code) for code in codes)
                task_series = df["Task"].astype(str)
                match = task_series.str.contains(pattern, case=False, na=False)
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

            build_summary(["RPT", "PTA", "ST", "T"], "Terapia")
            build_summary(["RN"], "Enfermeria")
        if completion_check_enabled and "Task Status" in df.columns:
            status_series = df["Task Status"].astype(str).str.strip()
            incomplete_rows = df[status_series.str.casefold() != "completed"]
            incomplete_rows.to_excel(writer, sheet_name="Check for Completion", index=False)

    return ValidationResponse(summary=summary, rules=rule_summaries, report_id=report_id)


@app.get("/report/{report_id}")
def download_report(report_id: str):
    report_path = REPORTS_DIR / f"validation_report_{report_id}.xlsx"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(report_path, filename=report_path.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
