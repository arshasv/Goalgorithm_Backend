from app.database.session import SessionLocal
from app.models.match import MatchModel
from app.models.prediction import PredictionModel, PlayerPredictionModel
from app.models.actual_result import ActualResultModel, PlayerActualModel
from app.models.score import ScoreModel
from app.models.evaluation import TechnicalEvaluationModel, PresentationEvaluationModel
from app.models.leaderboard import LeaderboardModel

db = SessionLocal()
try:
    db.query(LeaderboardModel).delete()
    db.query(TechnicalEvaluationModel).delete()
    db.query(PresentationEvaluationModel).delete()
    db.query(ScoreModel).delete()
    db.query(PlayerActualModel).delete()
    db.query(ActualResultModel).delete()
    db.query(PlayerPredictionModel).delete()
    db.query(PredictionModel).delete()
    db.query(MatchModel).delete()
    db.commit()
    print("Database cleared successfully.")
except Exception as e:
    db.rollback()
    print("Error clearing database:", e)
finally:
    db.close()
