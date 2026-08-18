# Feature 19: Excel/CSV Bulk Upload

## Feature Overview

Bulk team roster import via CSV/Excel files supporting .csv, .xlsx, and .xls formats. Maps group letters (A-E) to teams, processes rows with header normalization, and atomically replaces team members within a transaction.

## Purpose & Requirements

- Upload roster via CSV (.csv), Excel (.xlsx), or legacy Excel (.xls)
- Required columns: Name, Group (case-insensitive, whitespace-tolerant)
- Optional: EmployeeID
- Group-to-team mapping: A→Team A, B→Team B, ..., E→Team E
- Unknown groups silently skipped
- Transactional: DELETE old CSV-managed → INSERT new → SET is_csv_managed
- Non-organizer rejected (403)

## Related Specifications

- `features/excel-csv-upload.md` — Complete upload specification (309 lines)
- `features/team-management.md` — Team management integration
- `api/team-management-api.md` — Upload endpoint documentation

## How the Feature Works Internally

### File Processing Pipeline

```
1. DETECT FORMAT by file extension:
   .csv  → csv.DictReader (UTF-8)
   .xlsx → openpyxl.load_workbook(data_only=True)
   .xls  → xlrd.open_workbook

2. NORMALIZE HEADERS:
   "First Name" → "first_name"
   " Group " → "group"

3. LOCATE COLUMNS:
   Required: "group", "name"
   Optional: "employee_id"

4. SKIP LEADING BLANK ROWS (Excel formats)

5. PROCESS ROWS:
   for row in rows:
       group = row["group"].upper()
       if group not in GROUP_TO_TEAM: skip
       if not row["name"]: skip
       team = GROUP_TO_TEAM[group]
       members[team].append({name, employee_id})

6. VALIDATE:
   For each team with members:
       Check no manual members exist (conflict → 400)

7. TRANSACTION:
   BEGIN
   DELETE FROM team_members WHERE team_id IN (affected_teams) AND is_csv_managed
   INSERT all new members
   UPDATE teams SET is_csv_managed = True WHERE id IN (affected_teams)
   COMMIT
```

### Group-to-Team Mapping
```python
GROUP_TO_TEAM = {
    "A": "Team A",
    "B": "Team B",
    "C": "Team C",
    "D": "Team D",
    "E": "Team E",
}
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/api/team_routes.py` | 672 | Upload endpoint (parsing logic inlined) |
| `app/services/team_service.py` | 343 | Business logic + member management |

The CSV/Excel parsing logic is **inlined in the route handler** (`team_routes.py`), not extracted into a separate service or utility module.

### Key Patterns

```python
# Route handler inline parsing
if filename.endswith('.csv'):
    content = file.file.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
elif filename.endswith('.xlsx'):
    workbook = openpyxl.load_workbook(file.file, data_only=True)
    sheet = workbook.active
    # Skip leading blank rows, find header, extract data
elif filename.endswith('.xls'):
    workbook = xlrd.open_workbook(file_contents=file.file.read())
    # Similar extraction
```

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/teams/upload-members-csv` | ORGANIZER | Bulk CSV/Excel upload |
| GET | `/api/v1/teams/template/csv` | ORGANIZER | Download CSV template |
| GET | `/api/v1/teams/template/xlsx` | ORGANIZER | Download XLSX template |

### Request Format
```
POST /api/v1/teams/upload-members-csv
Content-Type: multipart/form-data
Body: file=<spreadsheet>
```

### Response Format
```json
{
  "message": "CSV uploaded successfully",
  "teams_affected": 5,
  "total_members": 50,
  "team_summary": {"Team A": 10, "Team B": 10, ...}
}
```

## Database/Data Models Involved

Modifies:
- `team_members` — DELETE old CSV-managed, INSERT new
- `teams` — UPDATE is_csv_managed = True

## External Dependencies

| Library | Purpose |
|---------|---------|
| `csv` (stdlib) | CSV parsing |
| `openpyxl` | XLSX parsing |
| `xlrd` | XLS parsing (legacy) |

## Error Handling

| Scenario | HTTP Code |
|----------|-----------|
| Unsupported extension | 400 BAD_REQUEST |
| Missing Group/Name columns | 400 BAD_REQUEST |
| Empty file | 400 BAD_REQUEST |
| Manual members conflict | 400 BAD_REQUEST |
| Non-organizer | 403 FORBIDDEN |

## Edge Cases

- Unknown group letters → silently skipped
- Empty Group/Name cells → silently skipped
- XLSX with blank header rows → auto-detected
- Non-UTF-8 CSV → potential errors (no encoding detection)
- No file size limit enforced

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_api.py` | CSV upload endpoint tests |

## Known Limitations/Technical Debt

- Parsing logic inlined in route (should be in service layer)
- No file size limit
- No encoding detection
- xlrd is deprecated

## Dependencies on Other Features

- **Team Management** — Team records referenced
- **Authentication** — Organizer role required

## Step-by-Step Implementation Sequence

1. Add CSV parsing with csv.DictReader
2. Add XLSX parsing with openpyxl
3. Add XLS parsing with xlrd
4. Implement header normalization
5. Implement group-to-team mapping
6. Add conflict detection
7. Implement transactional member replacement
8. Add template download endpoints
9. Write tests
