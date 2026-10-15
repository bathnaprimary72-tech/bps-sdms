"""Export only explicitly approved and allowlisted student fields from a private Sheet."""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials

HEADERS = ['APPROVED', 'PUBLIC NAME', 'CLASS', 'SECTION']
MAX_RECORDS = 5000
MAX_LENGTH = {'PUBLIC NAME': 100, 'CLASS': 30, 'SECTION': 30}

def main():
    raw = os.environ['GOOGLE_SERVICE_ACCOUNT_JSON']
    credentials = Credentials.from_service_account_info(json.loads(raw), scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    sheet = gspread.authorize(credentials).open_by_key(os.environ['GOOGLE_SHEET_ID']).worksheet('PUBLIC_STUDENTS')
    values = sheet.get_all_values()
    if not values:
        raise ValueError('Sheet is empty; refusing to overwrite published data')
    header = [v.strip().upper() for v in values[0]]
    if len(header) != len(set(header)) or not all(h in header for h in HEADERS):
        raise ValueError('Required headers missing or duplicate; expected APPROVED, PUBLIC NAME, CLASS, SECTION')
    columns = {name:header.index(name) for name in HEADERS}
    students=[]
    for row_number,row in enumerate(values[1:],start=2):
        def cell(name):
            idx=columns[name]
            return row[idx].strip() if idx<len(row) else ''
        if cell('APPROVED').upper() != 'YES':
            continue
        name=cell('PUBLIC NAME'); student_class=cell('CLASS'); section=cell('SECTION')
        if not name or not student_class:
            raise ValueError(f'Approved row {row_number} missing name or class')
        for label,value in [('PUBLIC NAME',name),('CLASS',student_class),('SECTION',section)]:
            if len(value)>MAX_LENGTH[label] or any(ord(c)<32 for c in value):
                raise ValueError(f'Invalid {label} in row {row_number}')
        students.append({'name':name,'class':student_class,'section':section})
        if len(students)>MAX_RECORDS:raise ValueError('Too many records; refusing export')
    if not students and os.environ.get('ALLOW_EMPTY_EXPORT')!='true':
        raise ValueError('No approved records; refusing to replace existing published directory. Set ALLOW_EMPTY_EXPORT=true for intentional removal.')
    students.sort(key=lambda s:(s['class'].casefold(),s['name'].casefold()))
    output={'updated_at':datetime.now(timezone.utc).isoformat(),'students':students}
    destination=Path('site/data/students.json')
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(output,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f'Exported {len(students)} approved public records')

if __name__=='__main__':main()
