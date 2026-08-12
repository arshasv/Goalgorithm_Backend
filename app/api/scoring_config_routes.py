import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_organizer, get_current_user
from app.database.session import get_db
from app.models.scoring_config import ScoringConfigModel
from app.schemas.scoring_config_schema import (
    GUIDELINE_DESCRIPTIONS,
    ScoringConfigCreate,
    ScoringConfigGuidelines,
    ScoringConfigResponse,
    ScoringConfigUpdate,
)

router = APIRouter(
    prefix="/admin/scoring-config",
    tags=["scoring-config"],
)

DEFAULT_NAME = "Default 2026"
DEFAULT_UUID = "00000000-0000-0000-0000-000000000001"


def _get_active_config(db: Session) -> ScoringConfigModel | None:
    return db.query(ScoringConfigModel).filter(
        ScoringConfigModel.is_active.is_(True)
    ).first()


def _validate_config_values(data: dict) -> None:
    errors: list[str] = []
    for key, val in data.items():
        if val is None:
            continue
        if key in ("probability_threshold",):
            if val < 0:
                errors.append(f"{key} cannot be negative")
            if val > 100:
                errors.append(f"{key} must be ≤ 100")
        elif "threshold" in key or "avg" in key:
            if val < 0:
                errors.append(f"{key} cannot be negative")
        elif key != "name":
            if isinstance(val, (int, float)) and val < 0:
                errors.append(f"{key} cannot be negative")
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))


@router.get("/guidelines", response_model=ScoringConfigGuidelines)
def get_config_guidelines(
    db: Session = Depends(get_db),
):
    config = _get_active_config(db)
    return ScoringConfigGuidelines(
        config=ScoringConfigResponse.model_validate(config) if config else None,
        guidelines=GUIDELINE_DESCRIPTIONS,
    )


@router.get("/active", response_model=ScoringConfigResponse | None)
def get_active_config(
    db: Session = Depends(get_db),
):
    config = _get_active_config(db)
    return config


@router.get("", response_model=list[ScoringConfigResponse])
def list_configs(
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    return db.query(ScoringConfigModel).order_by(
        ScoringConfigModel.created_at.desc()
    ).all()


@router.get("/{config_id}", response_model=ScoringConfigResponse)
def get_config(
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    config = db.query(ScoringConfigModel).filter(
        ScoringConfigModel.id == config_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Scoring config not found")
    return config


@router.post("", response_model=ScoringConfigResponse, status_code=201)
def create_config(
    body: ScoringConfigCreate,
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    latest = db.query(ScoringConfigModel).order_by(
        ScoringConfigModel.version.desc()
    ).first()
    next_version = (latest.version + 1) if latest else 1

    db.query(ScoringConfigModel).filter(
        ScoringConfigModel.is_active.is_(True)
    ).update({"is_active": False})
    db.flush()

    config = ScoringConfigModel(
        name=body.name,
        is_active=True,
        version=next_version,
        winner_points_correct=body.winner_points_correct,
        winner_points_incorrect=body.winner_points_incorrect,
        scoreline_points_exact=body.scoreline_points_exact,
        scoreline_points_margin=body.scoreline_points_margin,
        scoreline_points_incorrect=body.scoreline_points_incorrect,
        probability_threshold=body.probability_threshold,
        probability_points_pass=body.probability_points_pass,
        probability_points_fail=body.probability_points_fail,
        player_points_exact=body.player_points_exact,
        player_points_close=body.player_points_close,
        player_points_wrong=body.player_points_wrong,
        player_avg_threshold_exact=body.player_avg_threshold_exact,
        player_avg_threshold_close=body.player_avg_threshold_close,
        max_base_score=body.max_base_score,
        technical_max_per_category=body.technical_max_per_category,
        technical_max_total=body.technical_max_total,
        presentation_ai_explanation_max=body.presentation_ai_explanation_max,
        presentation_qa_score_max=body.presentation_qa_score_max,
        presentation_delivery_score_max=body.presentation_delivery_score_max,
        presentation_denominator=body.presentation_denominator,
        presentation_max_marks=body.presentation_max_marks,
        multiplier_a=body.multiplier_a,
        multiplier_b=body.multiplier_b,
        multiplier_c=body.multiplier_c,
        phase1_max_marks=body.phase1_max_marks,
        presentation_criteria=body.presentation_criteria,
        presentation_judge_count=body.presentation_judge_count,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.put("/{config_id}", response_model=ScoringConfigResponse)
def update_config(
    config_id: uuid.UUID,
    body: ScoringConfigUpdate,
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    config = db.query(ScoringConfigModel).filter(
        ScoringConfigModel.id == config_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Scoring config not found")

    update_data = body.model_dump(exclude_unset=True)
    _validate_config_values(update_data)

    if "name" in update_data:
        config.name = update_data["name"]
    for field in [
        "winner_points_correct", "winner_points_incorrect",
        "scoreline_points_exact", "scoreline_points_margin", "scoreline_points_incorrect",
        "probability_threshold", "probability_points_pass", "probability_points_fail",
        "player_points_exact", "player_points_close", "player_points_wrong",
        "player_avg_threshold_exact", "player_avg_threshold_close",
        "max_base_score",
        "technical_max_per_category", "technical_max_total",
        "presentation_ai_explanation_max", "presentation_qa_score_max",
        "presentation_delivery_score_max", "presentation_denominator", "presentation_max_marks",
        "multiplier_a", "multiplier_b", "multiplier_c",
        "phase1_max_marks", "presentation_criteria", "presentation_judge_count",
    ]:
        if field in update_data and update_data[field] is not None:
            setattr(config, field, update_data[field])

    db.commit()
    db.refresh(config)
    return config



@router.post("/{config_id}/activate", response_model=ScoringConfigResponse)
def activate_config(
    config_id: uuid.UUID,
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    config = db.query(ScoringConfigModel).filter(
        ScoringConfigModel.id == config_id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Scoring config not found")

    db.query(ScoringConfigModel).filter(
        ScoringConfigModel.is_active.is_(True)
    ).update({"is_active": False})
    db.flush()

    config.is_active = True
    db.commit()
    db.refresh(config)
    return config


@router.post("/reset", response_model=ScoringConfigResponse)
def reset_to_default(
    db: Session = Depends(get_db),
    _organizer: object = Depends(get_current_organizer),
):
    default_uuid = uuid.UUID(DEFAULT_UUID)
    default = db.query(ScoringConfigModel).filter(
        ScoringConfigModel.id == default_uuid
    ).first()
    if not default:
        default = ScoringConfigModel(id=default_uuid, name=DEFAULT_NAME, is_active=True, version=1)
        db.add(default)

    db.query(ScoringConfigModel).filter(
        ScoringConfigModel.is_active.is_(True),
        ScoringConfigModel.id != default_uuid,
    ).update({"is_active": False})
    db.flush()

    default.is_active = True
    db.commit()
    db.refresh(default)
    return default
