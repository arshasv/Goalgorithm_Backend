from fastapi import APIRouter

from app.api.prediction_routes import router as prediction_router
from app.api.result_routes import router as result_router
from app.api.scoring_routes import router as scoring_router
from app.api.leaderboard_routes import router as leaderboard_router
from app.api.auth_routes import router as auth_router
from app.api.team_routes import router as team_router
from app.api.scores_routes import router as scores_router
from app.api.scoring_config_routes import router as scoring_config_router
from app.api.model_submission_routes import team_model_router, admin_model_router
from app.api.upload_window_routes import router as upload_window_router
from app.api.match_routes import router as match_router
from app.api.external_matches_routes import router as external_matches_router
from app.api.leaderboard_settings_routes import router as leaderboard_settings_router
from app.api.admin_auth_routes import router as admin_auth_router
from app.api.analytics_routes import router as analytics_router
from app.api.model_evaluation_routes import router as model_evaluation_router
from app.api.report_routes import router as report_router

router = APIRouter()

router.include_router(prediction_router)
router.include_router(result_router)
router.include_router(scoring_router)
router.include_router(leaderboard_router)
router.include_router(auth_router)
router.include_router(team_router)
router.include_router(scores_router)
router.include_router(scoring_config_router)
router.include_router(team_model_router)
router.include_router(admin_model_router)
router.include_router(upload_window_router)
router.include_router(match_router)
router.include_router(external_matches_router)
router.include_router(leaderboard_settings_router)
router.include_router(admin_auth_router)
router.include_router(analytics_router)
router.include_router(model_evaluation_router)
router.include_router(report_router)
