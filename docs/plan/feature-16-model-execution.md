# Feature 16: Model Execution System

## Feature Overview

ML model execution pipeline that loads uploaded .pkl files, runs predictions against match data, and feeds results into the existing prediction system. Supports single model execution and batch execution across all teams × matches. Includes safe unpickling, background task execution, and retry logic.

## Purpose & Requirements

- Execute uploaded ML models against match fixtures
- Safe pickle deserialization with restricted classes
- Background task execution (non-blocking)
- Single execution: upload → execute → get prediction
- Batch execution: discover models → create jobs → execute all → track progress
- Retry failed/cancelled jobs
- Cancel running batches
- Status polling (IDLE → RUNNING → SUCCESS/FAILED)

## Related Specifications

- `features/MODEL_EXECUTION_SYSTEM.md` — Complete execution pipeline spec (1050 lines)
- `features/model-performance-analytics.md` — Model evaluation metrics

## User/Business Flow

### Single Execution
```
Organizer → POST /model-execution/upload → upload .pkl
    ↓
POST /model-execution/{id}/execute → trigger background execution
    ↓
BackgroundTask: load model → predict → serialize → save prediction
    ↓
GET /model-execution/{id}/status → poll until SUCCESS/FAILED
```

### Batch Execution
```
Organizer → POST /batch-executions/create → discover models × matches
    ↓
POST /batch-executions/{id}/execute → trigger batch
    ↓
Background thread: iterate all PENDING jobs sequentially
    ↓
GET /batch-executions/{id}/progress → real-time progress
    ↓
POST /batch-executions/{id}/cancel → cancel remaining
POST /batch-executions/{id}/retry → retry failed jobs
```

## How the Feature Works Internally

### Safe Unpickler (`model_compat.py`)
```python
class CompatUnpickler(pickle.Unpickler):
    # Handles sklearn module migration issues
    # Maps old module paths to new ones
    # Allows: sklearn, xgboost, lightgbm, numpy, pandas, etc.
    # Blocks: os, subprocess, eval, exec
```

### Model Executor Pipeline (`model_executor.py`)
```python
def execute_in_background(execution_id, model_path, match_data):
    # 1. Load model with safe unpickler
    model = safe_load(model_path)

    # 2. Verify predict() method exists
    assert hasattr(model, 'predict')

    # 3. Build input features
    input_data = {"home_team": match.home, "away_team": match.away}

    # 4. Run prediction
    raw_output = model.predict(input_data)

    # 5. Serialize to prediction format
    prediction_payload = ModelSerializer.serialize_output(raw_output)

    # 6. Save via PredictionService
    prediction = PredictionService.save_prediction(prediction_payload)

    # 7. Link to execution record
    execution.prediction_id = prediction.id
    execution.status = "SUCCESS"
```

### Model Serializer (`model_serializer.py`)
Transforms AI model output dict → PredictionSubmission format:
- Maps `win_probabilities` → flat probability fields
- Maps `predicted_scoreline` → home/away goals
- Auto-calculates winner from probabilities
- Validates goal scorer counts

### Batch Execution Service (`batch_execution_service.py`)
```python
def execute_batch(batch_id):
    batch = get_batch(batch_id)
    jobs = batch.jobs.filter(status="PENDING")

    for job in jobs:
        if batch.overall_status == "CANCELLED":
            break

        try:
            execute_job(job)  # Load → Predict → Save
            job.status = "SUCCESS"
        except Exception as e:
            job.status = "FAILED"
            job.error_message = str(e)

        batch.completed_jobs += 1
        update_batch_progress(batch)
```

## Relevant Backend Implementation

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/model_execution/models/model_upload.py` | 22 | ModelUploadModel |
| `app/model_execution/models/model_execution.py` | 26 | ModelExecutionModel |
| `app/model_execution/models/batch_execution.py` | 55 | BatchExecutionModel + BatchJobModel |
| `app/model_execution/schemas/execution_schema.py` | 22 | ExecutionResponse schema |
| `app/model_execution/services/model_compat.py` | 36 | Safe unpickler |
| `app/model_execution/services/model_serializer.py` | 134 | Output normalization |
| `app/model_execution/services/model_executor.py` | 197 | Single execution pipeline |
| `app/model_execution/services/execution_service.py` | 84 | Execution orchestration |
| `app/model_execution/services/batch_execution_service.py` | 483 | Batch execution pipeline |
| `app/model_execution/routes/execution_routes.py` | 47 | Single execution endpoints |
| `app/model_execution/routes/batch_execution_routes.py` | 145 | Batch execution endpoints |

### Key Classes & Functions

- `ExecutionService.upload_model(file, team_id, match_id)` → UploadModelModel
- `ExecutionService.execute_model(model_id)` → Triggers BackgroundTask
- `ExecutionService.get_status(execution_id)` → StatusResponse
- `BatchExecutionService.discover_models()` → Latest active per team
- `BatchExecutionService.create_batch(matches)` → Batch + Jobs
- `BatchExecutionService.execute_batch(batch_id)` → Background thread
- `BatchExecutionService.get_progress(batch_id)` → ProgressResponse
- `BatchExecutionService.cancel_batch(batch_id)` → Cancel
- `BatchExecutionService.retry(batch_id, mode)` → Retry failed/all
- `safe_load(path)` → Loaded model via CompatUnpickler
- `ModelSerializer.serialize_output(raw)` → PredictionSubmission dict

## APIs/Endpoints Involved

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/model-execution/upload` | ORGANIZER | Upload model for execution |
| POST | `/api/v1/model-execution/{id}/execute` | ORGANIZER | Execute model |
| GET | `/api/v1/model-execution/{id}/status` | ORGANIZER | Check status |
| POST | `/api/v1/batch-executions` | ORGANIZER | Discover models |
| POST | `/api/v1/batch-executions/create` | ORGANIZER | Create batch |
| POST | `/api/v1/batch-executions/{id}/execute` | ORGANIZER | Trigger batch |
| GET | `/api/v1/batch-executions/{id}/progress` | ORGANIZER | Progress |
| GET | `/api/v1/batch-executions` | ORGANIZER | List batches |
| POST | `/api/v1/batch-executions/{id}/cancel` | ORGANIZER | Cancel batch |
| POST | `/api/v1/batch-executions/{id}/retry` | ORGANIZER | Retry batch |
| POST | `/api/v1/batch-executions/jobs/{id}/retry` | ORGANIZER | Retry single job |

## Database/Data Models Involved

### `model_uploads` Table
- id, team_id, match_id, original_filename, stored_file_path, status

### `model_executions` Table
- id, model_upload_id, status, started_at, completed_at, error_message, prediction_id

### `batch_executions` Table
- id, overall_status, total_jobs, completed_jobs, failed_jobs, pending_jobs

### `batch_jobs` Table
- id, batch_execution_id, team_id, match_id, model_submission_id, status, prediction_id, error_message

## Error Handling

| Scenario | Handling |
|----------|----------|
| Model has no predict() method | FAILED with error message |
| Pickle deserialization fails | FAILED with error message |
| Model output invalid | FAILED (logged) |
| Background task crash | Status set to FAILED, error logged |
| Batch cancellation | Remaining jobs stay PENDING |

## External Dependencies/Integrations

- `pickle` / `joblib` — Model deserialization
- `scikit-learn`, `xgboost`, `lightgbm` — ML frameworks (model compat)
- `cloudpickle`, `onnxruntime` — Additional model formats
- FastAPI `BackgroundTasks` — Non-blocking execution

## Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_model_execution.py` | Upload, execute, failure handling (4 tests) |

## Dependencies on Other Features

- **Model Submission** — Models uploaded via submission system
- **Prediction Management** — Execution generates predictions
- **Match Management** — Match data for model input
- **Scoring Engine** — Predictions auto-scored

## Step-by-Step Implementation Sequence

1. Create model execution ORM models (3 models)
2. Create safe unpickler with module aliasing
3. Create model serializer for output normalization
4. Create model executor for single execution
5. Create execution service for orchestration
6. Create batch execution service
7. Create execution routes (single + batch)
8. Implement background task execution
9. Implement retry and cancel logic
10. Write tests
