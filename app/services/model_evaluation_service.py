import uuid
from typing import Sequence

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.models.model_evaluation import ModelEvaluationModel
from app.models.model_submission import ModelSubmissionModel
from app.models.team import TeamModel
from app.schemas.model_evaluation_schema import (
    ModelEvaluationCreate,
    ModelEvaluationResponse,
    ModelEvaluationAnalyticsResponse,
    AnalyticsTeamScore,
)
from app.exceptions.business_exceptions import ResourceNotFoundException
from app.models.enums import ModelStatus


class ModelEvaluationService:
    def __init__(self, db: Session):
        self.db = db

    def get_submitted_models(self) -> list[dict]:
        stmt = select(ModelSubmissionModel, TeamModel.name).join(
            TeamModel, ModelSubmissionModel.team_id == TeamModel.id
        ).order_by(desc(ModelSubmissionModel.uploaded_at))
        results = self.db.execute(stmt).all()
        
        response = []
        for sub, team_name in results:
            response.append({
                "id": str(sub.id),
                "team": team_name,
                "model_name": sub.model_name or sub.file_name,
                "version": sub.version,
                "upload_date": sub.uploaded_at.isoformat(),
                "status": sub.status.value if hasattr(sub.status, "value") else str(sub.status),
                "active_flag": sub.is_active,
            })
        return response

    def _calculate_insights(self, data: ModelEvaluationCreate) -> tuple[str | None, str | None]:
        metrics = {
            "Winner": data.winner_prediction_accuracy,
            "Scoreline": data.scoreline_accuracy,
            "Probability": data.probability_accuracy,
            "Player": data.player_prediction_accuracy,
        }
        
        valid_metrics = {k: v for k, v in metrics.items() if v is not None}
        if not valid_metrics:
            return None, None
            
        strongest = max(valid_metrics, key=valid_metrics.get)
        weakest = min(valid_metrics, key=valid_metrics.get)
        
        # If all are the same, don't label weakness as the same as strength
        if valid_metrics[strongest] == valid_metrics[weakest]:
            weakest = None
            
        return strongest, weakest

    def save_evaluation(self, data: ModelEvaluationCreate) -> ModelEvaluationResponse:
        submission = self.db.get(ModelSubmissionModel, data.model_id)
        if not submission:
            raise ResourceNotFoundException("Model submission")
            
        strength, weakness = self._calculate_insights(data)
        
        eval_model = ModelEvaluationModel(
            model_id=submission.id,
            team_id=submission.team_id,
            overall_accuracy=data.overall_accuracy,
            winner_prediction_accuracy=data.winner_prediction_accuracy,
            scoreline_accuracy=data.scoreline_accuracy,
            probability_accuracy=data.probability_accuracy,
            player_prediction_accuracy=data.player_prediction_accuracy,
            matches_tested=data.matches_tested,
            average_score=data.average_score,
            final_ai_score=data.final_ai_score,
            evaluation_notes=data.evaluation_notes,
            strength_category=strength,
            weakness_category=weakness,
        )
        
        submission.status = ModelStatus.EVALUATED
        
        self.db.add(eval_model)
        self.db.commit()
        self.db.refresh(eval_model)
        return ModelEvaluationResponse.model_validate(eval_model)

    def get_analytics(self) -> ModelEvaluationAnalyticsResponse:
        # Fetch active models for current ranking
        stmt = select(ModelEvaluationModel, TeamModel.name, ModelSubmissionModel.version).join(
            TeamModel, ModelEvaluationModel.team_id == TeamModel.id
        ).join(
            ModelSubmissionModel, ModelEvaluationModel.model_id == ModelSubmissionModel.id
        ).where(ModelSubmissionModel.is_active == True)
        
        active_evals = self.db.execute(stmt).all()
        
        team_scores = []
        for eval_m, team_name, version in active_evals:
            team_scores.append(AnalyticsTeamScore(
                team_name=team_name,
                overall_accuracy=eval_m.overall_accuracy,
                winner_prediction_accuracy=eval_m.winner_prediction_accuracy,
                scoreline_accuracy=eval_m.scoreline_accuracy,
                probability_accuracy=eval_m.probability_accuracy,
                player_prediction_accuracy=eval_m.player_prediction_accuracy,
                final_ai_score=eval_m.final_ai_score,
                version=version,
            ))
            
        # Sort by overall accuracy for rankings
        rankings = sorted(team_scores, key=lambda x: (x.overall_accuracy or 0), reverse=True)
        
        # Version History - fetching all evaluations, not just active
        hist_stmt = select(ModelEvaluationModel, TeamModel.name, ModelSubmissionModel.version).join(
            TeamModel, ModelEvaluationModel.team_id == TeamModel.id
        ).join(
            ModelSubmissionModel, ModelEvaluationModel.model_id == ModelSubmissionModel.id
        ).order_by(TeamModel.name, ModelSubmissionModel.version)
        
        hist_evals = self.db.execute(hist_stmt).all()
        
        history_map = {}
        for eval_m, team_name, version in hist_evals:
            if team_name not in history_map:
                history_map[team_name] = []
            history_map[team_name].append({
                "version": version,
                "accuracy": eval_m.overall_accuracy,
            })
            
        version_history = [{"team_name": k, "history": v} for k, v in history_map.items()]
        
        return ModelEvaluationAnalyticsResponse(
            team_rankings=rankings,
            model_scores=rankings,
            accuracy_comparison=rankings,
            category_breakdown=rankings,
            version_history=version_history
        )
