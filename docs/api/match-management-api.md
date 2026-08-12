# Match Management API

## Endpoints

### 1. List Matches
`GET /api/v1/matches`

#### Description
Retrieves a list of all matches. Accessible by any authenticated user (organizer or team leader).

#### Response JSON
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "match_number": 1,
    "home_team_name": "Brazil",
    "away_team_name": "Argentina",
    "scheduled_at": "2026-06-17T18:00:00+00:00",
    "freeze_deadline": "2026-06-17T17:00:00+00:00",
    "round": "Group Stage",
    "status": "SCHEDULED",
    "created_at": "2026-06-16T12:00:00+00:00"
  }
]
```

---

### 2. Create Match
`POST /api/v1/matches`

#### Description
Creates a single new match. Organizers only.

#### Request JSON
```json
{
  "match_number": 2,
  "home_team_name": "Germany",
  "away_team_name": "France",
  "scheduled_at": "2026-06-18T20:00:00+00:00",
  "round": "Group Stage"
}
```
*Note: `freeze_deadline` is automatically calculated as 1 hour before `scheduled_at` if omitted.*

---

### 3. Update Match
`PUT /api/v1/matches/{match_id}`

#### Description
Updates match details. Organizers only.

#### Request JSON
```json
{
  "scheduled_at": "2026-06-18T21:00:00+00:00"
}
```

---

### 4. Delete Match
`DELETE /api/v1/matches/{match_id}`

#### Description
Deletes a match. Organizers only.

---

### 5. Upload Match Schedule (CSV)
`POST /api/v1/matches/upload-csv`

#### Description
Bulk uploads matches from a CSV file. Parses columns `match_number`, `home_team`, `away_team`, `kickoff_date` and `round`. Creates match records and auto-calculates `freeze_deadline`. Organizers only.

#### Request Format
`multipart/form-data`
- `file`: Binary file upload (CSV only).

#### Response JSON
```json
{
  "created": 1,
  "errors": [],
  "matches": [
    {
      "match_number": 1,
      "home_team_name": "Argentina",
      "away_team_name": "Brazil",
      ...
    }
  ]
}
```
