# Excel/CSV Team Member Upload Feature

## Purpose
Provides tournament organizers with a bulk mechanism to import team rosters from spreadsheet files. Replaces manual per-member data entry, enforces a structured roster format, and locks teams against unsynchronised manual edits once uploaded.

---

## Complete Workflow

```
Organizer clicks "Upload Members (CSV/Excel)"
                │
                ▼
File picker opens (.csv, .xls, .xlsx)
                │
                ▼
Frontend validates file extension
                │
                ▼
File sent as multipart/form-data → POST /api/v1/teams/upload-members-csv
                │
                ▼
Backend authorizes (organizer role check)
                │
                ▼
Backend parses file by extension (csv.DictReader / openpyxl / xlrd)
                │
                ▼
Columns extracted: EmployeeID, Name, Group
                │
                ▼
Group letter mapped to team (A–E)
                │
                ▼
Validation: group exists, team has no conflicting manual members
                │
                ▼
Database transaction:
  ├── Existing members for affected teams cleared
  ├── New members inserted
  └── Team is_csv_managed flag set to true
                │
                ▼
Response returned with import summary
                │
                ▼
Frontend refreshes team list to show updated rosters
```

---

## Organizer Upload Process

1. Organizer navigates to the **Teams** section of the dashboard.
2. Clicks **Upload Members (CSV/Excel)** button.
3. Selects a file with one of the supported extensions.
4. File is sent to the backend for processing.
5. On success, a toast notification displays the result and the team cards refresh.
6. On failure, an error toast describes the issue (invalid format, missing columns, conflicting manual members, etc.).

---

## Supported Formats

| Format | Extension | Parser Library | Notes |
|---|---|---|---|
| Comma-Separated Values | `.csv` | `csv.DictReader` (stdlib) | UTF-8 encoding expected |
| Excel Workbook | `.xlsx` | `openpyxl` | Data-only mode, skips blank rows |
| Excel 97-2003 Workbook | `.xls` | `xlrd` | Float integers auto-converted |

---

## Expected Input Columns

The uploaded file must contain the following column headers (case-insensitive, whitespace-tolerant):

| Column | Required | Persisted | Purpose |
|---|---|---|---|
| `SL No` | No | No | Serial number (ignored) |
| `EmployeeID` | No | Yes | Corporate employee identifier |
| `Name` | Yes | Yes | Member display name |
| `Seniority` | No | No | Seniority level (ignored) |
| `Gender` | No | No | Gender indicator (ignored) |
| `Football Knowledge` | No | No | Self-rated knowledge (ignored) |
| `Group` | Yes | Yes | Target team letter (A, B, C, D, E) |

---

## Processing Logic

### File Reading

**CSV** (`backend/app/api/team_routes.py:252-265`):
- File bytes decoded as UTF-8.
- `csv.DictReader` reads rows into dictionaries keyed by header.
- Headers are normalised: lowercased, spaces replaced with underscores (` ` → `_`).
- Empty strings replace `None` values.

**XLSX** (`backend/app/api/team_routes.py:267-297`):
- `openpyxl.load_workbook(data_only=True)` parses the workbook.
- First non-empty row is treated as the header row (leading blank rows skipped).
- Headers normalised identically to CSV.
- Subsequent non-empty rows become data dictionaries.
- `None` cells become empty strings.

**XLS** (`backend/app/api/team_routes.py:299-334`):
- `xlrd.open_workbook` reads the legacy format.
- Same header-scanning logic as XLSX.
- Float values that are whole numbers (e.g. `1.0`) are converted to integers.
- All values serialised to strings.

### Column Extraction

After parsing, headers are searched case-insensitively:
- `group` column required for team assignment.
- `name` column required (also matches `member` fallback).
- `employeeid` / `employee_id` column optional.

All other columns in the file are ignored at the application level. The code builds row dictionaries keyed by normalised header name, so columns like `sl_no`, `seniority`, `gender`, and `football_knowledge` are present in the dict but never read.

### Why Unused Columns Are Ignored

The source spreadsheet (e.g. an HR export) contains columns irrelevant to the tournament system. Only `Name`, `EmployeeID`, and `Group` serve a functional purpose:
- **Name** identifies the participant in the UI.
- **EmployeeID** links the participant to the corporate directory.
- **Group** determines team assignment.

Columns like `Seniority` and `Football Knowledge` were considered for future gamification but are not part of the current scoring or display logic. They are parsed into the row dictionary (to avoid schema-change errors if the file structure varies) but are never read or persisted.

### EmployeeID + Name Storage

Each row produces a `TeamMemberModel` record:
- `name` → `TeamMemberModel.name` (string, required, max 255 chars)
- `employee_id` → `TeamMemberModel.employee_id` (string, optional, max 100 chars)
- `team_id` → foreign key to the resolved `TeamModel`

Empty `EmployeeID` values are stored as `NULL` in the database.

### Group-Based Team Assignment

The `Group` column value is processed through `_map_group_to_team()` (`team_routes.py:229-233`):
1. Value is stripped of whitespace and uppercased.
2. Looked up in the `GROUP_TO_TEAM` dictionary:

```python
GROUP_TO_TEAM = {
    'A': 'Team A',
    'B': 'Team B',
    'C': 'Team C',
    'D': 'Team D',
    'E': 'Team E',
}
```

3. If the value matches a key, the corresponding team name is returned.
4. If no match, `None` is returned and the row is silently skipped.

### A–E Team Creation / Mapping

For each unique team name encountered during processing (`team_routes.py:363-382`):

1. The backend queries the `teams` table for an existing record with that name.
2. If found:
   - Checks for conflicting manual members (see validation section).
   - Sets `team.is_csv_managed = True`.
3. If not found:
   - Creates a new `TeamModel` with the team name, code, and `is_csv_managed = True`.
   - Flushes to obtain the new `team.id` for member insertion.

After all rows are processed, old members for each affected team are deleted in bulk, then all new members are inserted in a single `add_all()` call.

### Validation and Error Handling

| Scenario | HTTP Status | Detail |
|---|---|---|
| Non-organizer user | 403 | `Only organizers can upload files.` |
| Unsupported extension | 400 | `Unsupported file format. Please upload a .csv, .xls, or .xlsx file.` |
| Empty file | 400 | `CSV is empty or invalid.` / `Excel file is empty.` |
| Missing `Group` or `Name` columns | 400 | `Uploaded file must contain at least Group and Name columns.` |
| Team has existing manual members | 400 | `Team '{name}' already contains manually added members.` |
| Corrupt or unreadable file | 400 | `Invalid file encoding: ...` / `Failed to parse XLSX file: ...` |

Rows with empty `Group` or empty `Name` are silently skipped (no error raised). Rows with an unrecognised group letter (not A–E) are also silently skipped.

---

## API Details

### Endpoint

```
POST /api/v1/teams/upload-members-csv
```

### Request Format

`multipart/form-data` with a single field:
- `file`: The uploaded file (`.csv`, `.xls`, or `.xlsx`).

### Response Format

**Success (200)**:
```json
{
  "message": "Successfully imported members CSV/Excel file. Updated 5 teams with 47 members."
}
```

**Error (400)**:
```json
{
  "detail": "Team 'Team A' already contains manually added members. A team can only use CSV-managed or manual members, not both."
}
```

**Error (403)**:
```json
{
  "detail": "Only organizers can upload files."
}
```

### Backend Flow

1. **Authorization** — `current_user.role` must be `ORGANIZER`.
2. **File detection** — filename extension determines parser path.
3. **Parsing** — file read into structured row dictionaries.
4. **Column validation** — `Group` and `Name` columns must exist.
5. **Row iteration** — each row is mapped to a team; conflicting manual members trigger a 400.
6. **Persistence** — old members deleted, new members inserted, `is_csv_managed` set, all in one DB transaction.
7. **Response** — summary message returned.

There is no separate service layer for this feature; all logic resides in the route handler (`team_routes.py:236-403`).

---

## Database Changes / Models Involved

### TeamModel (`backend/app/models/team.py`)

| Column | Type | Notes |
|---|---|---|
| `is_csv_managed` | `Boolean` | Default `false`. Set to `true` when a roster is imported via CSV/Excel. |

When `is_csv_managed` is `true`:
- `POST /my-team/members` is blocked (400).
- `DELETE /my-team/members/{member_id}` is blocked (400).
- `POST /auth/register` with this team is blocked (400).

### TeamMemberModel (`backend/app/models/team_member.py`)

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` (PK) | Auto-generated |
| `team_id` | `UUID` (FK → teams.id) | Cascade delete |
| `name` | `String(255)` | Required, from `Name` column |
| `employee_id` | `String(100)` | Nullable, from `EmployeeID` column |
| `created_at` | `DateTime` | Auto-set on creation |

### Alembic Migration

`7cc606d61ec5_add_name_normalized_drop_college_name.py` — adds `is_csv_managed` column to the `teams` table.

---

## Frontend Integration Flow

### Upload Trigger (`frontend/js/features/teams.js`)

The **Upload Members (CSV/Excel)** button (`teams.js:17`) opens a hidden `<input type="file">` accepting `.csv`, `.xls`, `.xlsx`. On file selection, `uploadMembersCsv()` is called:

```javascript
async function uploadMembersCsv(event) {
  const file = event.target.files[0];
  if (!file) return;

  const ext = file.name.split('.').pop().toLowerCase();
  if (ext !== 'csv' && ext !== 'xls' && ext !== 'xlsx') {
    Toast.error('Invalid file format.');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  Toast.info('Uploading file...');
  const res = await TeamService.uploadMembersCsv(formData);
  Toast.success(res.message);
  await loadOrgTeams();
}
```

### API Service (`frontend/js/api.js`)

```javascript
uploadMembersCsv: (formData) => Api.request('POST', '/teams/upload-members-csv', formData, true),
```

The `true` parameter signals an external FormData request (no JSON Content-Type header).

### UI Feedback

- **Upload in progress**: Toast `Uploading file...`
- **Success**: Toast with the backend's success message, team grid refreshed.
- **Error**: Toast with the backend's error detail.

### Conditional UI Logic

When `loadOrgTeams()` renders team cards, each team's `is_csv_managed` field is available in the API response. The team dashboard (`frontend/js/features/team-dashboard.js:141`) reads this flag to conditionally enable/disable member editing UI elements.
