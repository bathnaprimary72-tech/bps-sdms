"""Publish strictly allowlisted, explicitly approved student directory fields."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials

REQUIRED = ("APPROVED", "NAME", "CLASS")
OPTIONAL = ("YEAR", "ROLL")
LIMITS = {"NAME": 100, "CLASS": 30, "YEAR": 30, "ROLL": 30}

def build_export(values):
    if not values:
        raise ValueError("PUBLIC_STUDENTS is empty")
    headers = [str(v).strip().upper() for v in values[0]]
    if len(headers) != len(set(headers)):
        raise ValueError("Duplicate headings found in row 1")
    missing = [name for name in REQUIRED if name not in headers]
    if missing:
        raise ValueError("Missing required headings: " + ", ".join(missing))
    indexes = {name: headers.index(name) for name in REQUIRED + OPTIONAL if name in headers}
    students = []
    for row_no, row in enumerate(values[1:], 2):
        def cell(field):
            index = indexes.get(field)
            return str(row[index]).strip() if index is not None and index < len(row) else ""
        if cell("APPROVED").upper() != "YES":
            continue
        values_out = {key: cell(key) for key in LIMITS}
        if not values_out["NAME"] or not values_out["CLASS"]:
            raise ValueError(f"Approved row {row_no} is missing NAME or CLASS")
        for key, value in values_out.items():
            if len(value) > LIMITS[key] or any(ord(c) < 32 for c in value):
                raise ValueError(f"Invalid {key} in row {row_no}")
        students.append({"name": values_out["NAME"], "class": values_out["CLASS"], "year": values_out["YEAR"], "roll": values_out["ROLL"]})
        if len(students) > 5000:
            raise ValueError("Too many approved records")
    if not students and os.getenv("ALLOW_EMPTY_EXPORT") != "true":
        raise ValueError("No approved records; refusing to replace existing directory")
    students.sort(key=lambda s: (s["class"].casefold(), s["name"].casefold()))
    return {"updated_at": datetime.now(timezone.utc).isoformat(), "students": students}

def main():
    creds = Credentials.from_service_account_info(json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]), scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    worksheet = gspread.authorize(creds).open_by_key(os.environ["GOOGLE_SHEET_ID"]).worksheet("PUBLIC_STUDENTS")
    data = build_export(worksheet.get_all_values())
    target = Path(__file__).resolve().parent.parent / "site" / "data" / "students.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Published {len(data['students'])} approved records (NAME, CLASS, YEAR, ROLL only)")

if __name__ == "__main__":
    main()
