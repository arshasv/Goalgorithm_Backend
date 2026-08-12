from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.database.session import get_db
from app.models.scoring_config import ScoringConfigModel
from app.repositories.scoring_config_repository import ScoringConfigRepository
from app.schemas.scoring_config_schema import (
    GUIDELINE_DESCRIPTIONS,
    ScoringConfigCreate,
    ScoringConfigGuidelines,
    ScoringConfigResponse,
    ScoringConfigUpdate,
)

DEFAULT_NAME = "Default 2026"
DEFAULT_UUID = "00000000-0000-0000-0000-000000000001"

def _validate_config_values(data: dict) -> None:
    errors: list[str] = []
    for key, val in data.items():
        if val is None:
            continue
        if key in ("probability_threshold", "probability_high_threshold", "probability_medium_threshold"):
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


class ScoringConfigService:
    def __init__(self, config_repo: ScoringConfigRepository) -> None:
        self.config_repo = config_repo

    def get_config_guidelines(self) -> ScoringConfigGuidelines:
        config = self.config_repo.get_active()
        return ScoringConfigGuidelines(
            config=ScoringConfigResponse.model_validate(config) if config else None,
            guidelines=GUIDELINE_DESCRIPTIONS,
        )

    def get_active_config(self) -> ScoringConfigModel | None:
        return self.config_repo.get_active()

    def list_configs(self) -> list[ScoringConfigModel]:
        return self.config_repo.get_all_by_created()

    def get_config(self, config_id: uuid.UUID) -> ScoringConfigModel:
        config = self.config_repo.get(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Scoring config not found")
        return config

    def create_config(self, body: ScoringConfigCreate) -> ScoringConfigModel:
        latest = self.config_repo.get_latest_version()
        next_version = (latest.version + 1) if latest else 1

        self.config_repo.deactivate_all()

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
            probability_high_threshold=body.probability_high_threshold,
            probability_high_points=body.probability_high_points,
            probability_medium_threshold=body.probability_medium_threshold,
            probability_medium_points=body.probability_medium_points,
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
        return self.config_repo.create(**{
            "name": config.name,
            "is_active": config.is_active,
            "version": config.version,
            "winner_points_correct": config.winner_points_correct,
            "winner_points_incorrect": config.winner_points_incorrect,
            "scoreline_points_exact": config.scoreline_points_exact,
            "scoreline_points_margin": config.scoreline_points_margin,
            "scoreline_points_incorrect": config.scoreline_points_incorrect,
            "probability_threshold": config.probability_threshold,
            "probability_points_pass": config.probability_points_pass,
            "probability_points_fail": config.probability_points_fail,
            "probability_high_threshold": config.probability_high_threshold,
            "probability_high_points": config.probability_high_points,
            "probability_medium_threshold": config.probability_medium_threshold,
            "probability_medium_points": config.probability_medium_points,
            "player_points_exact": config.player_points_exact,
            "player_points_close": config.player_points_close,
            "player_points_wrong": config.player_points_wrong,
            "player_avg_threshold_exact": config.player_avg_threshold_exact,
            "player_avg_threshold_close": config.player_avg_threshold_close,
            "max_base_score": config.max_base_score,
            "technical_max_per_category": config.technical_max_per_category,
            "technical_max_total": config.technical_max_total,
            "presentation_ai_explanation_max": config.presentation_ai_explanation_max,
            "presentation_qa_score_max": config.presentation_qa_score_max,
            "presentation_delivery_score_max": config.presentation_delivery_score_max,
            "presentation_denominator": config.presentation_denominator,
            "presentation_max_marks": config.presentation_max_marks,
            "multiplier_a": config.multiplier_a,
            "multiplier_b": config.multiplier_b,
            "multiplier_c": config.multiplier_c,
            "phase1_max_marks": config.phase1_max_marks,
            "presentation_criteria": config.presentation_criteria,
            "presentation_judge_count": config.presentation_judge_count,
        })

    def update_config(self, config_id: uuid.UUID, body: ScoringConfigUpdate) -> ScoringConfigModel:
        config = self.config_repo.get(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Scoring config not found")

        update_data = body.model_dump(exclude_unset=True)
        _validate_config_values(update_data)

        return self.config_repo.update(config, **update_data)

    def activate_config(self, config_id: uuid.UUID) -> ScoringConfigModel:
        config = self.config_repo.get(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Scoring config not found")

        self.config_repo.deactivate_all()
        return self.config_repo.update(config, is_active=True)

    def reset_to_default(self) -> ScoringConfigModel:
        default_uuid = uuid.UUID(DEFAULT_UUID)
        default = self.config_repo.get(default_uuid)
        if not default:
            default = self.config_repo.create(id=default_uuid, name=DEFAULT_NAME, is_active=True, version=1)

        self.config_repo.deactivate_all_except(default_uuid)
        return self.config_repo.update(default, is_active=True)
