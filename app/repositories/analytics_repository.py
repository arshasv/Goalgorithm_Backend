import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.evaluation import PresentationEvaluationModel, TechnicalEvaluationModel
from app.models.leaderboard import LeaderboardModel
from app.models.match import MatchModel
from app.models.model_submission import ModelSubmissionModel
from app.models.score import ScoreModel
from app.models.team import TeamModel
from app.models.judge import JudgeModel

class AnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_judges(self) -> List[JudgeModel]:
        return self.db.query(JudgeModel).all()

    def get_active_teams(self) -> List[TeamModel]:
        return self.db.query(TeamModel).filter(TeamModel.is_active == True).all()

    def get_team_by_id_or_code(self, identifier: str) -> Optional[TeamModel]:
        try:
            uid = uuid.UUID(identifier)
            team = self.db.query(TeamModel).filter(TeamModel.id == uid).first()
            if team:
                return team
        except (ValueError, TypeError):
            pass
        return self.db.query(TeamModel).filter(TeamModel.team_id == identifier.upper(), TeamModel.is_active == True).first()

    def get_all_leaderboard_entries(self) -> List[LeaderboardModel]:
        return self.db.query(LeaderboardModel).all()

    def get_leaderboard_entry_for_team(self, team_id_str: str | uuid.UUID) -> Optional[LeaderboardModel]:
        uid = uuid.UUID(str(team_id_str)) if not isinstance(team_id_str, uuid.UUID) else team_id_str
        return self.db.query(LeaderboardModel).filter(LeaderboardModel.team_id == uid).first()

    def get_all_calculated_scores(self) -> List[ScoreModel]:
        return self.db.query(ScoreModel).filter(ScoreModel.base_score.isnot(None)).order_by(ScoreModel.computed_at.asc()).all()

    def get_scores_for_team(self, team_id_str: str) -> List[ScoreModel]:
        import uuid
        uid = uuid.UUID(team_id_str)
        return self.db.query(ScoreModel).filter(ScoreModel.team_id == uid, ScoreModel.base_score.isnot(None)).all()

    def get_all_matches(self) -> List[MatchModel]:
        return self.db.query(MatchModel).all()

    def get_latest_model_for_team(self, team_uuid: uuid.UUID) -> Optional[ModelSubmissionModel]:
        return self.db.query(ModelSubmissionModel).filter(ModelSubmissionModel.team_id == team_uuid).order_by(ModelSubmissionModel.uploaded_at.desc()).first()

    def get_all_presentation_evaluations(self) -> List[PresentationEvaluationModel]:
        return self.db.query(PresentationEvaluationModel).all()

    def get_presentation_evaluations_for_team(self, team_id_str: str | uuid.UUID) -> List[PresentationEvaluationModel]:
        uid = uuid.UUID(str(team_id_str)) if not isinstance(team_id_str, uuid.UUID) else team_id_str
        return self.db.query(PresentationEvaluationModel).filter(PresentationEvaluationModel.team_id == uid).all()
