# Feature 03: Team Management

## Feature Overview

CRUD management of 5 competition teams (A-E) with member roster management. Teams are linked to team leader user accounts. Supports manual member management by organizers and bulk CSV/Excel import with `is_csv_managed` flagging.

## Purpose & Requirements

- Manage 5 competition teams (Team A through Team E)
- Each team linked to one team leader (UserModel)
- Organizer can CRUD team members manually
- Bulk import via CSV/Excel with group-to-team mapping
- `is_csv_managed` flag prevents mixing CSV-imported and manual members
- Team statistics endpoint for team performance data

## Related Specifications

- `features/team-management.md` — Team roster upload, role badge system
- `features/excel-csv-upload.md` — Bulk import specification (309 lines)
- `api/team-management-api.md` — Team management API endpoints
- `database/schema-design.md` — Teams and team_members table design

## User/Business Flow

### Manual Member Management
```
Organizer → POST /teams/{id}/members → {name, employee_id}
    ↓
Validate team exists
    ↓
Check team.is_csv_managed == False (if True → 400)
    ↓
Create TeamMemberModel
    ↓
Return member
```

### CSV/Excel Bulk Import
```
Organizer → POST /teams/upload-members-csv → multipart/form-data file
    ↓
Detect file extension (.csv / .xlsx / .xls)
    ↓
Parse with appropriate parser (csv.DictReader / openpyxl / xlrd)
    ↓
Normalize headers (lowercase, spaces → underscores)
    ↓
Validate Group and Name columns present
    ↓
For each row: map Group letter → Team via GROUP_TO_TEAM
    ↓
For each team: check no conflicting manual members
    ↓
Transaction: DELETE old CSV-managed members → INSERT new → SET is_csv_managed
    ↓
Return affected team/member counts
```

## How the Feature is Created

1. TeamModel + TeamMemberModel ORM models defined
2. TeamRepository provides CRUD operations
3. TeamService orchestrates business logic
4. Team routes expose API endpoints
5. CSV parsing logic inlined in route handler

## How the Feature Works Internally

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

### CSV Processing Pipeline
1. **File Detection:** Extension-based routing (`.csv` → `csv.DictReader`, `.xlsx` → `openpyxl`, `.xls` → `xlrd`)
2. **Header Normalization:** Lowercase, strip whitespace, replace spaces with underscores
3. **Column Extraction:** Locate `Group`, `Name`, and optional `EmployeeID` columns
4. **Row Processing:** Group value uppercased, mapped through `GROUP_TO_TEAM`, unknown groups skipped
5. **Conflict Detection:** For each team, check if manual members exist (conflict → 400)
6. **Atomic Transaction:** Delete old CSV-managed members, insert new ones, update `is_csv_managed`

### Team Name Normalization (`app/utils/team_name_utils.py`)
```python
def normalize_team_name(name: str) -> str:
    # lowercase, strip, remove "team " prefix
    # "Team A" → "a", "TEAM B" → "b"
```

## Architecture & Components Involved

```
app/models/
├── team.py              ← TeamModel ORM
└── team_member.py       ← TeamMemberModel ORM

app/repositories/
└── team_repository.py   ← Team CRUD operations

app/services/
└── team_service.py      ← Team business logic + CSV import

app/api/
└── team_routes.py       ← Team API endpoints (672 lines)

app/schemas/
└── team_schema.py       ← Team/Member Pydantic schemas

app/utils/
└── team_name_utils.py   ← Team name normalization
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/models/team.py` | 86 | TeamModel ORM with relationships |
| `app/models/team_member.py` | 26 | TeamMemberModel ORM |
| `app/repositories/team_repository.py` | 24 | Team CRUD |
| `app/services/team_service.py` | 343 | Team business logic + CSV import |
| `app/api/team_routes.py` | 672 | Team API endpoints |
| `app/schemas/team_schema.py` | 116 | Team/Member Pydantic schemas |
| `app/utils/team_name_utils.py` | 17 | Name normalization |

### Key Classes & Functions

- `TeamService.get_all_teams()` → List of teams with member counts
- `TeamService.get_team_by_id(team_id)` → Single team with members
- `TeamService.create_team(data)` → Creates team
- `TeamService.update_team(team_id, data)` → Updates team
- `TeamService.add_member(team_id, data)` → Adds manual member
- `TeamService.update_member(team_id, member_id, data)` → Updates member
- `TeamService.remove_member(team_id, member_id)` → Deletes member
- `TeamService.upload_members_csv(file, db)` → Bulk CSV/Excel import
- `TeamService.get_team_stats(team_id)` → Team statistics
- `normalize_team_name(name)` → Normalized team name

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/teams` | Any | List all teams |
| GET | `/api/v1/teams/{team_id}` | Any | Get team details |
| PUT | `/api/v1/teams/{team_id}` | ORGANIZER | Update team |
| POST | `/api/v1/teams/{team_id}/members` | ORGANIZER | Add member |
| PUT | `/api/v1/teams/{team_id}/members/{member_id}` | ORGANIZER | Update member |
| DELETE | `/api/v1/teams/{team_id}/members/{member_id}` | ORGANIZER | Remove member |
| POST | `/api/v1/teams/upload-members-csv` | ORGANIZER | Bulk CSV/Excel import |
| GET | `/api/v1/teams/{team_id}/stats` | Any | Team statistics |
| GET | `/api/v1/teams/template/csv` | ORGANIZER | Download CSV template |
| GET | `/api/v1/teams/template/xlsx` | ORGANIZER | Download XLSX template |

## Database/Data Models Involved

### `teams` Table (`TeamModel`)
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| team_id | String | unique (A-E) |
| name | String | not null |
| name_normalized | String | unique |
| team_leader_name | String | nullable |
| user_id | UUID | FK → users.id, nullable |
| registered_at | DateTime | server_default=now |
| is_active | Boolean | default True |
| is_csv_managed | Boolean | default False |

### `team_members` Table (`TeamMemberModel`)
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| team_id | UUID | FK → teams.id |
| name | String | not null |
| employee_id | String | nullable |
| group_code | String | nullable |
| created_at | DateTime | server_default=now |

## Authentication/Authorization Requirements

- `GET /teams` and `GET /teams/{id}`: Any authenticated user
- `POST /teams/upload-members-csv`: ORGANIZER only
- `POST/PUT/DELETE` member endpoints: ORGANIZER only
- `PUT /teams/{id}`: ORGANIZER only

## Important Classes, Functions, Services, Modules

### CSV Parsers (inlined in `team_routes.py`)
- `csv.DictReader` — For `.csv` files (UTF-8)
- `openpyxl.load_workbook(data_only=True)` — For `.xlsx` files
- `xlrd.open_workbook` — For `.xls` files (legacy)

### Transaction Pattern
```python
# In team_routes.py upload endpoint:
try:
    # DELETE old CSV-managed members for affected teams
    # INSERT all new members
    # UPDATE is_csv_managed = True
    db.commit()
except Exception:
    db.rollback()
    raise
```

## Request/Response Flow

### CSV Upload Request Flow
```
POST /api/v1/teams/upload-members-csv
Content-Type: multipart/form-data
Body: file=<spreadsheet>

Response (200):
{
  "message": "CSV uploaded successfully",
  "teams_affected": 5,
  "total_members": 50,
  "team_summary": {
    "Team A": 10,
    "Team B": 10,
    ...
  }
}
```

## Error Handling

| Scenario | HTTP Code | Error Code |
|----------|-----------|------------|
| Unsupported file format | 400 | BAD_REQUEST |
| Missing required columns | 400 | BAD_REQUEST |
| Empty file | 400 | BAD_REQUEST |
| CSV-managed team has manual members | 400 | CONFLICT |
| Team not found | 404 | NOT_FOUND |
| Member not found | 404 | NOT_FOUND |
| Non-organizer access | 403 | FORBIDDEN |

## Validation

- File extension must be `.csv`, `.xlsx`, or `.xls`
- `Group` and `Name` columns required in uploaded file
- Group values must be A-E (unknown silently skipped)
- Empty Group/Name rows silently skipped
- Team name must match existing team

## External Dependencies/Integrations

- `csv` (stdlib) — CSV parsing
- `openpyxl` — XLSX parsing
- `xlrd` — XLS parsing (legacy format)

## Edge Cases

- CSV with unknown group letters → silently skipped
- CSV with empty rows → silently skipped
- Mixed CSV-managed and manual members → rejected (400)
- Very large CSV files → no explicit size limit
- Non-UTF-8 CSV encoding → potential parsing errors
- XLSX with blank header rows → auto-skipped to find true header

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_api.py` | Team CRUD, member management, CSV upload (30+ tests) |
| `tests/test_full_competition_flow.py` | Team creation in competition flow |

## Known Limitations/Technical Debt

- CSV parsing logic is inlined in route handler (should be in service layer)
- No file size limit enforcement
- No encoding detection for CSV files
- Missing repository methods called by TeamService (get_by_user_id, create_member, get_members_by_team)
- XLS support via xlrd (deprecated library)

## Dependencies on Other Features

- **Authentication** — Team leaders linked to teams via user_id
- **Exception Handling** — Uses global handlers for error responses
- **Match Management** — Teams referenced in match home/away team names
- **Prediction Management** — Teams submit predictions

## Step-by-Step Implementation Sequence

1. Create `app/models/team.py` with TeamModel
2. Create `app/models/team_member.py` with TeamMemberModel
3. Create `app/schemas/team_schema.py` with all team/member schemas
4. Create `app/repositories/team_repository.py` with CRUD operations
5. Create `app/services/team_service.py` with business logic
6. Create `app/utils/team_name_utils.py` with name normalization
7. Create `app/api/team_routes.py` with all endpoints
8. Implement CSV/Excel parsing logic in upload endpoint
9. Add group-to-team mapping
10. Add transaction management for bulk import
11. Add template download endpoints
12. Run Alembic migration for teams + team_members tables
13. Write tests for team CRUD, member management, CSV upload
