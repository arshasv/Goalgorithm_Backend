# Team Management API

## Endpoints

### 1. Upload Team Members File
`POST /api/v1/teams/upload-members-csv`

#### Description
Uploads a CSV or Excel (`.xls`/`.xlsx`) file to populate team member rosters. Parses rows, validates that team codes match A–E, deletes old CSV-managed members for the specified teams, and creates new member records.

#### HTTP Method
POST

#### Request Format
`multipart/form-data`
- `file`: Binary file upload (CSV, XLS, or XLSX).

#### Processing Flow
1. Receives file and checks file type.
2. Uses Pandas or CSV reader to parse rows.
3. Checks for presence of required headers: `SL No`, `EmployeeID`, `Name`, `Seniority`, `Gender`, `Football Knowledge`, `Group`.
4. Extracts `EmployeeID`, `Name`, and `Group`. Normalizes `Group` to uppercase letter.
5. Groups rows by the `Group` field.
6. For each group:
   - Validates that group is one of `A`, `B`, `C`, `D`, `E`.
   - Locates target team in database.
   - Clears existing members for the target team.
   - Saves new members with `name` and `employee_id`.
   - Sets target team's `is_csv_managed = true`.
7. Commits database transaction.

#### Response JSON (Success)
```json
{
  "message": "Successfully imported X members across Y teams",
  "details": {
    "A": 12,
    "B": 15
  }
}
```

#### Error Scenarios
- **400 Bad Request**: File format is invalid or required headers are missing.
- **422 Unprocessable Entity**: Row data contains an invalid group code (not A-E) or empty fields.

---

### 2. List Teams
`GET /api/v1/teams`

#### Description
Retrieves all registered teams with their registration status and CSV management flag.

#### HTTP Method
GET

#### Response JSON
```json
[
  {
    "id": "3b3ea51d-bbab-4d94-af73-34a3b7c3ac23",
    "name": "A",
    "code": "A",
    "team_leader_name": "Alice Smith",
    "registered_at": "2026-06-12T04:22:03.123456+00:00",
    "is_active": true,
    "is_csv_managed": true
  }
]
```

---

### 3. Get Team Members
`GET /api/v1/teams/{team_id}/members`

#### Description
Retrieves a list of members for a specific team.

#### HTTP Method
GET

#### Response JSON
```json
[
  {
    "id": "9ca187f5-a1bb-4e63-ac38-c68ab91350a2",
    "team_id": "3b3ea51d-bbab-4d94-af73-34a3b7c3ac23",
    "name": "John Smith",
    "employee_id": "EMP001",
    "created_at": "2026-06-12T04:22:15.552991+00:00"
  }
]
```

---

### 4. Register Team & Leader
`POST /api/v1/auth/register`

#### Description
Registers a new team leader account and sets team registration info.

#### HTTP Method
POST

#### Request JSON
```json
{
  "username": "leader_a",
  "email": "leader@corp.com",
  "password": "securepassword123",
  "team_name": "A",
  "team_leader_name": "Alice Smith"
}
```

#### Validation Rules
- `team_name` must be one of: `A`, `B`, `C`, `D`, `E`.
- `team_name` cannot already be registered by another user.
- If target team has `is_csv_managed = true`, manual registration is blocked.

---

## Affected Models & Database Schema

### `TeamModel` (`teams` table)
- Added `is_csv_managed` (Boolean, default `False`): Tracks whether the roster was imported via CSV.
- Added `name_normalized` (String, unique): Normalized form of the team name.

### `TeamMemberModel` (`team_members` table)
- Added `employee_id` (String, not-null): Links member to their corporate employee ID.
- Dropped legacy unused columns (`email`, `contact`, `role`).
