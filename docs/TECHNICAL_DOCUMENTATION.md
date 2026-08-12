# Technical Documentation

> Entry point for the GOALGORITHM Scoring System documentation.

---

## Documentation Structure

```
docs/
├── TECHNICAL_DOCUMENTATION.md    ← You are here
├── TEST_PLAN.md                  ← Testing strategy and test cases
├── features/                     ← Feature documentation
├── api/                          ← API endpoint documentation
├── database/                     ← Database design documentation
├── architecture/                 ← Architecture documentation
└── reviews/                      ← Review and deployment guides
```

---

## Features

| Document | Description |
|---|---|
| [Prediction Management](features/prediction-management.md) | Prediction submission, validation, storage |
| [Actual Result Management](features/actual-result-management.md) | Match result ingestion |
| [Base Scoring Engine](features/base-scoring-engine.md) | Winner, scoreline, probability, player scoring |
| [Ranking & Multiplier](features/ranking-multiplier.md) | Per-match ranking and grade multiplier assignment |
| [Phase Normalization](features/phase-normalization.md) | Cumulative score normalization to 60-mark scale |
| [Technical Evaluation](features/technical-evaluation.md) | Phase 2 committee scoring |
| [Presentation Evaluation](features/presentation-evaluation.md) | Phase 3 peer scoring with multiplier |
| [Leaderboard](features/leaderboard.md) | Final leaderboard generation |
| [Excel/CSV Upload](features/excel-csv-upload.md) | Bulk roster import, file parsing, group mapping, CSV management lock |
| [Team Management](features/team-management.md) | CSV/Excel roster import, manual restrictions, and role badge system |
| [Admin Scoring Configuration](features/admin-scoring-config.md) | Dynamic scoring thresholds and configuration |
| [Model Submission](features/model-submission.md) | Team model file uploads and upload window management |
| [Match Management](features/match-management.md) | Manual match creation, CSV schedule upload, and status tracking |

---

## API Reference

| Document | Endpoints |
|---|---|
| [Prediction API](api/prediction-api.md) | `POST /api/v1/predictions` |
| [Actual Result API](features/actual-result-management.md) | `POST /api/v1/actual-results` |
| [Scoring API](api/scoring-api.md) | `POST /api/v1/calculate-match-score`, `POST /api/v1/technical-score`, `POST /api/v1/presentation-score` |
| [Leaderboard API](api/leaderboard-api.md) | `POST /api/v1/leaderboard/calculate` |
| [Evaluation API](api/evaluation-api.md) | Technical and presentation evaluation endpoints |
| [Team Management API](api/team-management-api.md) | `/api/v1/teams/upload-members-csv`, `/api/v1/teams`, `/api/v1/teams/{team_id}/members` |
| [Error Responses](api/error-responses.md) | Standard error envelope, HTTP codes, example responses |
| Admin Scoring Configuration | `/api/v1/admin/scoring-config`, `/api/v1/admin/scoring-config/active`, `/api/v1/admin/scoring-config/{id}`, `/api/v1/admin/scoring-config/{id}/activate`, `/api/v1/admin/scoring-config/reset` |
| Model Submission | `/api/v1/upload-window`, `/api/v1/teams/my-team/model`, `/api/v1/admin/models`, `/api/v1/admin/models/{id}/download` |
| [Match Management API](api/match-management-api.md) | `/api/v1/matches`, `/api/v1/matches/upload-csv` |

---

## Database Design

| Document | Description |
|---|---|
| [Database Overview](database/database-overview.md) | Engine, design goals, table list |
| [Schema Design](database/schema-design.md) | Full entity-relationship details |
| [Feature-Database Mapping](database/feature-database-mapping.md) | Which features read/write which tables |
| Scoring Configuration | `scoring_configs` table tracks dynamically adjustable base scoring and evaluation thresholds |
| Model Submissions | `upload_window_config` tracks window time constraints; `model_submissions` tracks uploaded ML files |

---

## Architecture

| Document | Description |
|---|---|
| [System Architecture](architecture/system-architecture.md) | Layer diagram, design principles, technology stack |
| [Error Handling Architecture](architecture/error-handling-architecture.md) | Exception flow, exception module, standard error responses |
| [Prediction Architecture](architecture/prediction-architecture.md) | Prediction data flow |
| [Scoring Architecture](architecture/scoring-architecture.md) | Scoring computation data flow |
| [Leaderboard Architecture](architecture/leaderboard-architecture.md) | Leaderboard generation data flow |
| [Database Architecture](architecture/database-architecture.md) | Database layer, error handling, connection config |
| [Excel/CSV Upload Architecture](features/excel-csv-upload.md) | Bulk roster import, file parsing, group mapping, CSV management lock |
| [Deployment Guide](architecture/DEPLOYMENT.md) | Local setup, Docker build/run/compose |

---

## Reviews

| Document | Description |
|---|---|
| [Final Architecture Review](reviews/FINAL_REVIEW.md) | Architecture, validation, testing, Docker readiness review |

---

## Testing

| Document | Description |
|---|---|
| [Test Plan](TEST_PLAN.md) | Testing strategy, test cases by layer |

---

## Excel/CSV Upload Feature Architecture

### Layer Responsibilities

```
Frontend (TeamsView.jsx / TeamService)
    │
    │  FormData with file → POST /teams/upload-members-csv
    │
    ▼
API Layer (team_routes.py)
    │  → Authorize (ORGANIZER role)
    │  → Detect file extension (.csv / .xls / .xlsx)
    │  → Dispatch to format-specific parser
    │
    ▼
File Parsers (inline in route)
    ├── csv.DictReader (stdlib, UTF-8 decode)
    ├── openpyxl (XLSX, data_only mode)
    └── xlrd (XLS, legacy format)
    │
    ▼
Column Extraction
    │  → Normalise headers (lowercase, spaces → underscores)
    │  → Locate Group, Name, EmployeeID columns
    │  → Ignore: SL No, Seniority, Gender, Football Knowledge
    │
    ▼
Business Logic (inline in route)
    │  → Map group letter to team via GROUP_TO_TEAM dict
    │  → Query/create TeamModel records
    │  → Validate no conflicting manual members
    │  → Accumulate TeamMemberModel records
    │
    ▼
Persistence
    │  → DELETE old members for affected teams
    │  → INSERT all new members
    │  → UPDATE is_csv_managed = true
    │  → Single commit
    │
    ▼
Database
    ├── teams (is_csv_managed flag)
    └── team_members (name, employee_id → linked by team_id)
```

There is no separate service or repository layer for this feature — the route handler directly queries models and commits the transaction.

### API Flow Explanation

1. **Request arrives** at `POST /api/v1/teams/upload-members-csv` with a `multipart/form-data` body containing a single `file` field.
2. **Authorization guard** — if `current_user.role != ORGANIZER`, a 403 is returned immediately.
3. **Format routing** — the `filename` extension determines which parser runs:
   - `.csv` → `csv.DictReader` with UTF-8 decoding
   - `.xlsx` → `openpyxl.load_workbook(data_only=True)`
   - `.xls` → `xlrd.open_workbook`
4. **Header scanning** — all parsers normalise column names to lowercase with underscores. For Excel formats, leading blank rows are automatically skipped to locate the true header row.
5. **Content validation** — after parsing, the code verifies that `Group` and `Name` columns are present. If either is missing, a 400 is returned.
6. **Row processing** — each non-empty row is iterated:
   - Group value is uppercased and mapped through `GROUP_TO_TEAM`.
   - Unrecognised groups and rows with empty Group/Name are skipped.
   - For each unique team, existing manual members are checked (conflict → 400).
7. **Transaction** — old members are bulk-deleted, new members are bulk-inserted, and `is_csv_managed` is set in a single transaction. On failure, all changes roll back.
8. **Response** — a JSON success message with the count of affected teams and members is returned.

### Frontend-Backend Interaction Details

| Aspect | Frontend (`TeamsView.jsx`) | Backend (`team_routes.py`) |
|---|---|---|
| **Trigger** | Hidden `<input type="file">` opened by button click | — |
| **Validation** | Client-side extension check (`.csv`/`.xls`/`.xlsx` only) | Server-side extension + content validation |
| **Envelope** | `FormData` with `file` field | FastAPI `UploadFile` |
| **Service call** | `TeamService.uploadMembersCsv(formData)` via `axios` instance | `router.post("/upload-members-csv")` |
| **Loading state** | React state `isUploading = true` | — |
| **Success** | Success state set, `loadTeams()` triggered | `200` JSON with message |
| **Error** | Error state set with detail message | `400`/`403`/`422` JSON with detail |
| **State refresh** | Re-fetches team list + members via React hook | — |

The `teamService.js` layer sends the `FormData` object using an Axios instance with standard headers, allowing the browser to set the correct `multipart/form-data` boundary.

After a successful upload, `loadTeams()` re-fetches `GET /api/v1/teams` which includes the updated `is_csv_managed` flag and member counts. The React state updates trigger re-renders to reflect the newly imported members.

---

## Constraints

| Constraint | Value |
|---|---|
| Number of teams | 5 |
| Total matches | 32 knockout matches |
| Prediction freeze | 2 hours before kickoff |
| Max base score per match | 25 points |
| Max earned points per match | 75 points (25 × 3×) |
| Max Phase 1 score | 60 marks |
| Max Phase 2 score | 20 marks |
| Max Phase 3 score | 20 marks |
| Max grand total | 100 marks |
