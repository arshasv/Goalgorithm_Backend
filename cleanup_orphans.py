import sys
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database.session as session_module
from app.models.prediction import PredictionModel, PlayerPredictionModel
from app.models.score import ScoreModel
from app.models.match import MatchModel
from app.models.actual_result import ActualResultModel, PlayerActualModel

def main():
    engine = session_module.engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        match_ids = [str(m[0]) for m in db.query(MatchModel.id).all()]
        
        orphan_preds = db.query(PredictionModel.id).filter(
            ~PredictionModel.match_id.in_(match_ids)
        ).all()
        orphan_pred_ids = [p[0] for p in orphan_preds]
        
        orphan_scores = db.query(ScoreModel).filter(
            ~ScoreModel.match_id.in_(match_ids)
        ).all()
        
        orphan_results = db.query(ActualResultModel.id).filter(
            ~ActualResultModel.match_id.in_(match_ids)
        ).all()
        orphan_result_ids = [r[0] for r in orphan_results]
        
        print(f"Found {len(orphan_pred_ids)} orphan predictions.")
        print(f"Found {len(orphan_scores)} orphan scores.")
        print(f"Found {len(orphan_result_ids)} orphan results.")
        
        if orphan_scores:
            db.query(ScoreModel).filter(
                ~ScoreModel.match_id.in_(match_ids)
            ).delete(synchronize_session=False)
            print(f"Deleted {len(orphan_scores)} orphan scores.")
            
        if orphan_pred_ids:
            # Delete player predictions first
            player_preds_deleted = db.query(PlayerPredictionModel).filter(
                PlayerPredictionModel.prediction_id.in_(orphan_pred_ids)
            ).delete(synchronize_session=False)
            print(f"Deleted {player_preds_deleted} orphan player predictions.")
            
            db.query(PredictionModel).filter(
                PredictionModel.id.in_(orphan_pred_ids)
            ).delete(synchronize_session=False)
            print(f"Deleted {len(orphan_pred_ids)} orphan predictions.")
            
        if orphan_result_ids:
            player_actuals_deleted = db.query(PlayerActualModel).filter(
                PlayerActualModel.actual_result_id.in_(orphan_result_ids)
            ).delete(synchronize_session=False)
            print(f"Deleted {player_actuals_deleted} orphan player actuals.")
            
            db.query(ActualResultModel).filter(
                ActualResultModel.id.in_(orphan_result_ids)
            ).delete(synchronize_session=False)
            print(f"Deleted {len(orphan_result_ids)} orphan results.")
            
        db.commit()
        print("Cleanup successful.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
