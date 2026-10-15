
"""Publish only approved, allowlisted student fields."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

REQUIRED = ["APPROVED", "NAME", "CLASS"]
OPTIONAL = ["YEAR", "ROLL"]
MAX_RECORDS = 5000


def main():
    credentials_info = json.loads(
        os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    )

    credentials = Credentials.from_service_account_info(
        credentials_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets.readonly"
        ]
    )

    client = gspread.authorize(credentials)

    worksheet = client.open_by_key(
        os.environ["GOOGLE_SHEET_ID"]
    ).worksheet("PUBLIC_STUDENTS")

    values = worksheet.get_all_values()

    if not values:
        raise ValueError("Google Sheet is empty")

    headers = [
        value.strip().upper()
        for value in values[0]
    ]

    if len(headers) != len(set(headers)):
        raise ValueError("Duplicate column headings found")

    missing = [
        name for name in REQUIRED
        if name not in headers
    ]

    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing)
        )

    columns = {
        name: headers.index(name)
        for name in REQUIRED + OPTIONAL
        if name in headers
    }

    students = []

    for row_number, row in enumerate(values[1:], start=2):

        def cell(column):
            if column not in columns:
                return ""
            index = columns[column]
            return row[index].strip() if index < len(row) else ""

        if cell("APPROVED").upper() != "YES":
            continue

        name = cell("NAME")
        student_class = cell("CLASS")
        year = cell("YEAR")
        roll = cell("ROLL")

        if not name or not student_class:
            raise ValueError(
                f"Approved row {row_number}: NAME or CLASS missing"
            )

        fields = {
            "name": name,
            "class": student_class,
            "year": year,
            "roll": roll
        }

        for field, value in fields.items():
            if len(value) > 100 or any(
                ord(character) < 32 for character in value
            ):
                raise ValueError(
                    f"Invalid {field} in row {row_number}"
                )

        students.append(fields)

        if len(students) > MAX_RECORDS:
            raise ValueError("Too many approved records")

    if not students and os.environ.get(
        "ALLOW_EMPTY_EXPORT"
    ) != "true":
        raise ValueError(
            "No approved records. Export stopped for safety."
        )

    students.sort(
        key=lambda s: (
            s["class"].casefold(),
            s["name"].casefold()
        )
    )

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "students": students
    }

    destination = Path("site/data/students.json")
    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    destination.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            separators=(",", ":")
        ),
        encoding="utf-8"
    )

    print(
        f"Successfully exported {len(students)} approved records"
    )


if __name__ == "__main__":
    main()
