"""
Batch Execution Routes
----------------------
Registers all /batch-executions/* endpoints required by the frontend.

Frontend API calls (modelExecutionService.js):
  POST   /batch-executions              → discoverLatestModels
  POST   /batch-executions/create       → createBatch
  POST   /batch-executions/{id}/execute → executeBatch
  GET    /batch-executions/{id}/progress→ getBatchProgress
  GET    /batch-executions              → listBatches
  POST   /batch-executions/{id}/cancel  → cancelBatch
  POST   /batch-executions/{id}/retry   → retryBatch
  POST   /batch-executions/jobs/{id}/retry → retryJob
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_organizer, get_db
from app.models.user import UserModel
from app.model_execution.services.batch_execution_service import BatchExecutionService

router = APIRouter(prefix="/batch-executions", tags=["batch_executions"])


class CreateBatchRequest(BaseModel):
    match_ids: List[str]


class RetryBatchRequest(BaseModel):
    force_all: bool = False


# ---------------------------------------------------------------------------
# POST /batch-executions  →  discover latest models per active team
# ---------------------------------------------------------------------------
@router.post("")
def discover_latest_models(
    db: Session = Depends(get_db),
    current_organizer: UserModel = Depends(get_current_organizer),
):
    """Return the latest active model submission for every team with an uploaded model."""
    service = BatchExecutionService(db)
    return service.discover_latest_models()


# ---------------------------------------------------------------------------
# GET /batch-executions  →  list all batches
# ---------------------------------------------------------------------------
@router.get("")
def list_batches(
    db: Session = Depends(get_db),
    current_organizer: UserModel = Depends(get_current_organizer),
):
    """List all batch executions ordered by most recent first."""
    service = BatchExecutionService(db)
    return service.list_batches()


# ---------------------------------------------------------------------------
# POST /batch-executions/create  →  create new batch
# ---------------------------------------------------------------------------
@router.post("/create")
def create_batch(
    body: CreateBatchRequest,
    db: Session = Depends(get_db),
    current_organizer: UserModel = Depends(get_current_organizer),
):
    """Create a new batch for all teams × selected matches."""
    service = BatchExecutionService(db)
    return service.create_batch(body.match_ids)


# ---------------------------------------------------------------------------
# POST /batch-executions/jobs/{job_id}/retry  →  retry a single job
# NOTE: must be declared BEFORE /{batch_id}/... routes to avoid path clash
# ---------------------------------------------------------------------------
@router.post("/jobs/{job_id}/retry")
def retry_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_organizer: UserModel = Depends(get_current_organizer),
):
    """Retry a single failed batch job."""
    service = BatchExecutionService(db)
    return service.retry_job(job_id)


# ---------------------------------------------------------------------------
# POST /batch-executions/{batch_id}/execute  →  trigger async execution
# ---------------------------------------------------------------------------
@router.post("/{batch_id}/execute")
def execute_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_organizer: UserModel = Depends(get_current_organizer),
):
    """Trigger asynchronous execution of all pending jobs in a batch."""
    service = BatchExecutionService(db)
    return service.execute_batch(batch_id)


# ---------------------------------------------------------------------------
# GET /batch-executions/{batch_id}/progress  →  real-time progress
# ---------------------------------------------------------------------------
@router.get("/{batch_id}/progress")
def get_batch_progress(
    batch_id: str,
    db: Session = Depends(get_db),
    current_organizer: UserModel = Depends(get_current_organizer),
):
    """Get detailed progress for a specific batch execution."""
    service = BatchExecutionService(db)
    return service.get_batch_progress(batch_id)


# ---------------------------------------------------------------------------
# POST /batch-executions/{batch_id}/cancel  →  cancel running batch
# ---------------------------------------------------------------------------
@router.post("/{batch_id}/cancel")
def cancel_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_organizer: UserModel = Depends(get_current_organizer),
):
    """Cancel a running or pending batch."""
    service = BatchExecutionService(db)
    return service.cancel_batch(batch_id)


# ---------------------------------------------------------------------------
# POST /batch-executions/{batch_id}/retry  →  retry failed/all jobs in batch
# ---------------------------------------------------------------------------
@router.post("/{batch_id}/retry")
def retry_batch(
    batch_id: str,
    body: RetryBatchRequest = RetryBatchRequest(),
    db: Session = Depends(get_db),
    current_organizer: UserModel = Depends(get_current_organizer),
):
    """Retry failed jobs (or all jobs if force_all=True) in a batch."""
    service = BatchExecutionService(db)
    return service.retry_batch(batch_id, force_all=body.force_all)
