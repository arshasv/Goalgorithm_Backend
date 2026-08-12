import uuid
import pickle
from datetime import datetime, timezone

from app.model_execution.services.model_compat import safe_load
from sqlalchemy.orm import Session

from app.database import session
from app.model_execution.models.model_execution import ModelExecutionModel
from app.model_execution.services.model_serializer import ModelSerializer
from app.services.prediction_service import PredictionService
import pandas as pd
import numpy as np
import scipy
from scipy import stats
import xgboost as xgb
import lightgbm as lgb
import sklearn
import math
import os

class ModelExecutor:
    def __init__(self, execution_id: uuid.UUID):
        self.execution_id = execution_id


    def execute_in_background(self):
        db: Session = session.SessionLocal()

        try:
            execution = db.query(ModelExecutionModel).filter(
                ModelExecutionModel.id == self.execution_id
            ).first()

            if not execution:
                return


            execution.status = "RUNNING"
            execution.started_at = datetime.now(timezone.utc)
            db.commit()


            model_upload = execution.model_upload

            if not model_upload:
                raise ValueError(
                    "Model upload record not found"
                )


            file_path = model_upload.stored_file_path


            # -------------------------
            # Deserialize model
            # -------------------------

            try:
                with open(file_path, "rb") as f:
                    model = safe_load(f)

            except Exception as e:
                raise ValueError(
                    f"Failed to deserialize model: {str(e)}"
                )


            if not hasattr(model, "predict"):
                raise AttributeError(
                    "Uploaded model object has no 'predict' method"
                )


            # -------------------------
            # Get match details
            # -------------------------

            try:
                from app.models.match import MatchModel

                match = db.query(MatchModel).filter(
                    MatchModel.id == model_upload.match_id
                ).first()

                if not match:
                    raise ValueError(
                        "Match record not found"
                    )

            except Exception as e:
                raise RuntimeError(
                    f"Unable to fetch match data: {str(e)}"
                )


            # -------------------------
            # Execute AI model
            # -------------------------

            try:

                model_input = {
                        "home_team": match.home_team_name,
                        "away_team": match.away_team_name
                    }


                model_output = model.predict(
    model_input
)

            except Exception as e:
                raise RuntimeError(
                    f"Error during model execution: {str(e)}"
                )


            # -------------------------
            # Convert model output
            # -------------------------

            serializer = ModelSerializer()

            payload = serializer.serialize_output(
                model_output=model_output,
                team_id=model_upload.team_id,
                match_id=model_upload.match_id
            )


            # -------------------------
            # Save prediction
            # -------------------------

            pred_service = PredictionService(db)

            result = pred_service.save_prediction(
                payload
            )


            from app.models.prediction import PredictionModel

            pred_record = db.query(
                PredictionModel
            ).filter(

                PredictionModel.team_id
                == model_upload.team_id,

                PredictionModel.match_id
                == model_upload.match_id

            ).first()


            if pred_record:
                execution.prediction_id = pred_record.id


            execution.status = "SUCCESS"
            execution.completed_at = datetime.now(timezone.utc)

            db.commit()


        except Exception as e:

            db.rollback()

            execution = db.query(
                ModelExecutionModel
            ).filter(

                ModelExecutionModel.id
                == self.execution_id

            ).first()


            if execution:

                execution.status = "FAILED"

                execution.error_message = str(e)

                execution.completed_at = datetime.now(
                    timezone.utc
                )

                db.commit()


        finally:

            db.close()
