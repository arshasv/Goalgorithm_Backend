# Feature 15: Model Submission

## Feature Overview

Secure upload of ML model files (.pkl, .pickle, .joblib, etc.) for organizational review. Supports time-windowed upload scheduling, version tracking, file size validation, and model status management (Uploaded → Testing → Evaluated → Failed).

## Purpose & Requirements

- Teams upload ML model files (max 50MB)
- Supported: .pkl, .pickle, .pt, .pth, .h5, .joblib, .onnx, .sav
- Time-windowed upload (enable/disable window with start/end times)
- Version tracking per team
- Status management: Uploaded → Testing → Evaluated → Failed
- Organizer download and status update

## Related Specifications

- `features/model-submission.md` — Model submission specification
- `features/model-performance-analytics.md` — Model evaluation specification

## How the Feature Works Internally

### Upload Flow
```
Team Leader → POST /model-submissions/upload → multipart/form-data
    ↓
Check upload window is enabled
Check current time within window
    ↓
Validate file extension against MODEL_EXTENSIONS
Validate file size <= 50MB
    ↓
Save file to disk (uploads/models/)
    ↓
Create ModelSubmissionModel record
    ↓
Return submission details
```

### Version Management
Each team can have multiple model submissions. The `is_active` flag marks the current version. Only one model per team is active at a time.

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/models/model_submission.py` | 39 | ModelSubmissionModel ORM |
| `app/models/upload_window.py` | 23 | UploadWindowModel ORM |
| `app/schemas/model_submission_schema.py` | 34 | Response schema |
| `app/schemas/upload_window_schema.py` | 22 | Window update/response |
| `app/repositories/model_submission_repository.py` | 46 | Model queries |
| `app/repositories/upload_window_repository.py` | 10 | Window get/update |
| `app/services/model_submission_service.py` | 116 | Upload, validation, metadata |
| `app/services/upload_window_service.py` | 25 | Window management |
| `app/api/model_submission_routes.py` | 171 | Model upload/download endpoints |
| `app/api/upload_window_routes.py` | 39 | Window config endpoints |

### Key Constants
```python
MODEL_EXTENSIONS = {".pkl", ".pickle", ".pt", ".pth", ".h5", ".joblib", ".onnx", ".sav"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
```

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/model-submissions/upload` | TEAM_LEADER | Upload model file |
| GET | `/api/v1/model-submissions/team/{team_id}` | Any | List team submissions |
| GET | `/api/v1/model-submissions/{id}/download` | Any | Download model file |
| PUT | `/api/v1/model-submissions/{id}/status` | ORGANIZER | Update status |
| PUT | `/api/v1/model-submissions/{id}/activate` | ORGANIZER | Set as active |
| GET | `/api/v1/upload-window` | Any | Get upload window |
| PUT | `/api/v1/upload-window` | ORGANIZER | Update window |

## Database/Data Models Involved

### `model_submissions` Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| team_id | UUID | FK → teams.id |
| model_name | String | not null |
| file_name | String | not null |
| file_path | String | not null |
| file_size | Integer | |
| version | Integer | |
| uploaded_at | DateTime | server_default=now |
| is_active | Boolean | default True |
| status | Enum | default Uploaded |
| model_type | String | nullable |
| description | String | nullable |

### `upload_windows` Table (Singleton)
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| is_enabled | Boolean | default False |
| start_time | DateTime | nullable |
| end_time | DateTime | nullable |

## Error Handling

| Scenario | HTTP Code |
|----------|-----------|
| Upload outside window | 423 LOCKED |
| Invalid file extension | 400 BAD_REQUEST |
| File too large | 413 PAYLOAD_TOO_LARGE |
| Model not found | 404 NOT_FOUND |

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_model_execution.py` | Upload success/rejection (4 tests) |

## Dependencies on Other Features

- **Authentication** — Team leader role required for upload
- **Model Execution** — Models executed from submissions
- **Analytics** — Model performance data

## Step-by-Step Implementation Sequence

1. Create ModelSubmissionModel + UploadWindowModel ORM
2. Create Pydantic schemas
3. Create repositories
4. Create services with validation logic
5. Create API routes
6. Implement file storage
7. Implement upload window enforcement
8. Run Alembic migrations
9. Write tests
