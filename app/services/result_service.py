import uuid
from sqlalchemy.orm import Session

from app.models.actual_result import ActualResultModel, PlayerActualModel
from app.models.enums import Winner
from app.models.match import MatchModel
from app.models.enums import MatchStatus


class ResultService:
    def __init__(self, db: Session):
        self.db = db

    def _resolve_match_id(self, match_id: str) -> uuid.UUID:
        """Normalize match_id to a UUID object for DB querying."""
        if isinstance(match_id, uuid.UUID):
            return match_id
        return uuid.UUID(match_id)

    def save_actual_result(self, payload: dict) -> dict:
        match_id = self._resolve_match_id(payload["match_id"])
        
        # Verify match exists before creating result
        match = self.db.query(MatchModel).filter(MatchModel.id == match_id).first()
        if not match:
            return {"status": "error", "detail": "Match not found"}

        # Check if result already exists
        actual_result = self.db.query(ActualResultModel).filter(
            ActualResultModel.match_id == match_id
        ).first()

        if actual_result:
            actual_result.actual_winner = Winner(payload["actual_winner"])
            actual_result.actual_home_goals = payload.get("final_score", {}).get("home_team_goals")
            actual_result.actual_away_goals = payload.get("final_score", {}).get("away_team_goals")
            actual_result.goal_scorers = payload.get("goal_scorers")
            actual_result.first_team_to_score = payload.get("first_team_to_score", "none")
            
            # Delete old player actuals
            self.db.query(PlayerActualModel).filter(
                PlayerActualModel.actual_result_id == actual_result.id
            ).delete()
        else:
            actual_result = ActualResultModel(
                match_id=match_id,
                actual_winner=Winner(payload["actual_winner"]),
                actual_home_goals=payload.get("final_score", {}).get("home_team_goals"),
                actual_away_goals=payload.get("final_score", {}).get("away_team_goals"),
                goal_scorers=payload.get("goal_scorers"),
                first_team_to_score=payload.get("first_team_to_score", "none"),
            )
            self.db.add(actual_result)
        
        self.db.flush()

        for pr in payload.get("player_results", []):
            player_actual = PlayerActualModel(
                actual_result_id=actual_result.id,
                player_id=pr["player_id"],
                player_name=pr["player_name"],
                actual_goals=pr.get("actual_goals"),
            )
            self.db.add(player_actual)

        # Set match status to COMPLETED
        match.status = MatchStatus.COMPLETED

        self.db.commit()
        self.db.refresh(actual_result)

        return {
            "status": "accepted",
            "match_id": actual_result.match_id,
        }

    def get_by_match(self, match_id: str):
        result = self.db.query(ActualResultModel).filter(
            ActualResultModel.match_id == match_id
        ).first()
        if not result:
            return None
        return {
            "match_id": result.match_id,
            "actual_winner": result.actual_winner.value if result.actual_winner else None,
            "final_score": {
                "home_team_goals": result.actual_home_goals,
                "away_team_goals": result.actual_away_goals,
            },
            "goal_scorers": result.goal_scorers or {"home": [], "away": []},
            "first_team_to_score": result.first_team_to_score,
            "player_results": [
                {
                    "player_id": p.player_id,
                    "player_name": p.player_name,
                    "actual_goals": p.actual_goals,
                }
                for p in result.player_actuals
            ],
        }
