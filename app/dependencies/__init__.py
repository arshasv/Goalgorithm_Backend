from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.session import get_db

# Repositories
from app.repositories.user_repository import UserRepository, PasswordResetOtpRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.match_repository import MatchRepository, ActualResultRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.score_repository import ScoreRepository, CumulativePhaseScoreRepository
from app.repositories.scoring_config_repository import ScoringConfigRepository
from app.repositories.leaderboard_repository import (
    TechnicalEvaluationRepository,
    PresentationEvaluationRepository,
    PresentationRoundRepository,
    LeaderboardRepository,
    LeaderboardVisibilityRepository,
    JudgeRepository,
    PresentationScoreRepository,
    PresentationRoundRepository,
)
from app.repositories.upload_window_repository import UploadWindowRepository
from app.repositories.model_submission_repository import ModelSubmissionRepository

# Services
from app.services.auth_service import AuthService
from app.services.team_service import TeamService
from app.services.match_service import MatchService
from app.services.prediction_service import PredictionService
from app.services.scoring_service import ScoringService
from app.services.scoring_config_service import ScoringConfigService
from app.services.upload_window_service import UploadWindowService
from app.services.leaderboard_service import LeaderboardService
from app.services.scores_service import ScoresService
from app.services.result_service import ResultService
from app.services.model_submission_service import ModelSubmissionService
from app.services.presentation_round_service import PresentationRoundService

# Repository Providers
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_password_reset_otp_repository(db: Session = Depends(get_db)) -> PasswordResetOtpRepository:
    return PasswordResetOtpRepository(db)

def get_team_repository(db: Session = Depends(get_db)) -> TeamRepository:
    return TeamRepository(db)

def get_match_repository(db: Session = Depends(get_db)) -> MatchRepository:
    return MatchRepository(db)

def get_actual_result_repository(db: Session = Depends(get_db)) -> ActualResultRepository:
    return ActualResultRepository(db)

def get_prediction_repository(db: Session = Depends(get_db)) -> PredictionRepository:
    return PredictionRepository(db)

def get_score_repository(db: Session = Depends(get_db)) -> ScoreRepository:
    return ScoreRepository(db)

def get_cumulative_phase_score_repository(db: Session = Depends(get_db)) -> CumulativePhaseScoreRepository:
    return CumulativePhaseScoreRepository(db)

def get_scoring_config_repository(db: Session = Depends(get_db)) -> ScoringConfigRepository:
    return ScoringConfigRepository(db)

def get_technical_evaluation_repository(db: Session = Depends(get_db)) -> TechnicalEvaluationRepository:
    return TechnicalEvaluationRepository(db)

def get_presentation_evaluation_repository(db: Session = Depends(get_db)) -> PresentationEvaluationRepository:
    return PresentationEvaluationRepository(db)

def get_leaderboard_repository(db: Session = Depends(get_db)) -> LeaderboardRepository:
    return LeaderboardRepository(db)

def get_leaderboard_visibility_repository(db: Session = Depends(get_db)) -> LeaderboardVisibilityRepository:
    return LeaderboardVisibilityRepository(db)

def get_upload_window_repository(db: Session = Depends(get_db)) -> UploadWindowRepository:
    return UploadWindowRepository(db)

def get_model_submission_repository(db: Session = Depends(get_db)) -> ModelSubmissionRepository:
    return ModelSubmissionRepository(db)

def get_judge_repository(db: Session = Depends(get_db)) -> JudgeRepository:
    return JudgeRepository(db)

def get_presentation_score_repository(db: Session = Depends(get_db)) -> PresentationScoreRepository:
    return PresentationScoreRepository(db)

def get_presentation_round_repository(db: Session = Depends(get_db)) -> PresentationRoundRepository:
    return PresentationRoundRepository(db)


# Service Providers
def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    team_repo: TeamRepository = Depends(get_team_repository),
    otp_repo: PasswordResetOtpRepository = Depends(get_password_reset_otp_repository),
) -> AuthService:
    return AuthService(user_repo, team_repo, otp_repo)

def get_team_service(
    team_repo: TeamRepository = Depends(get_team_repository),
) -> TeamService:
    return TeamService(team_repo)

def get_scoring_service(
    score_repo: ScoreRepository = Depends(get_score_repository),
    cumulative_repo: CumulativePhaseScoreRepository = Depends(get_cumulative_phase_score_repository),
    config_repo: ScoringConfigRepository = Depends(get_scoring_config_repository),
    tech_repo: TechnicalEvaluationRepository = Depends(get_technical_evaluation_repository),
    pres_repo: PresentationEvaluationRepository = Depends(get_presentation_evaluation_repository),
    leaderboard_repo: LeaderboardRepository = Depends(get_leaderboard_repository),
    team_repo: TeamRepository = Depends(get_team_repository),
    match_repo: MatchRepository = Depends(get_match_repository),
    actual_repo: ActualResultRepository = Depends(get_actual_result_repository),
    prediction_repo: PredictionRepository = Depends(get_prediction_repository),
    judge_repo: JudgeRepository = Depends(get_judge_repository),
    pres_score_repo: PresentationScoreRepository = Depends(get_presentation_score_repository),
    pres_round_repo: PresentationRoundRepository = Depends(get_presentation_round_repository),
) -> ScoringService:
    return ScoringService(
        score_repo,
        cumulative_repo,
        config_repo,
        tech_repo,
        pres_repo,
        leaderboard_repo,
        team_repo,
        match_repo,
        actual_repo,
        prediction_repo,
        judge_repo,
        pres_score_repo,
        pres_round_repo,
    )

def get_match_service(
    match_repo: MatchRepository = Depends(get_match_repository),
    actual_repo: ActualResultRepository = Depends(get_actual_result_repository),
    scoring_service: ScoringService = Depends(get_scoring_service),
) -> MatchService:
    return MatchService(match_repo, actual_repo, scoring_service)

def get_prediction_service(
    prediction_repo: PredictionRepository = Depends(get_prediction_repository),
    team_repo: TeamRepository = Depends(get_team_repository),
    match_repo: MatchRepository = Depends(get_match_repository),
) -> PredictionService:
    return PredictionService(prediction_repo, team_repo, match_repo)

def get_scoring_config_service(
    config_repo: ScoringConfigRepository = Depends(get_scoring_config_repository),
) -> ScoringConfigService:
    return ScoringConfigService(config_repo)

def get_upload_window_service(
    upload_window_repo: UploadWindowRepository = Depends(get_upload_window_repository),
) -> UploadWindowService:
    return UploadWindowService(upload_window_repo)

def get_model_submission_service(
    submission_repo: ModelSubmissionRepository = Depends(get_model_submission_repository),
    team_repo: TeamRepository = Depends(get_team_repository),
    window_service: UploadWindowService = Depends(get_upload_window_service),
) -> ModelSubmissionService:
    return ModelSubmissionService(submission_repo, team_repo, window_service)

def get_leaderboard_service(
    team_repo: TeamRepository = Depends(get_team_repository),
    leaderboard_repo: LeaderboardRepository = Depends(get_leaderboard_repository),
    visibility_repo: LeaderboardVisibilityRepository = Depends(get_leaderboard_visibility_repository),
) -> LeaderboardService:
    return LeaderboardService(team_repo, leaderboard_repo, visibility_repo)

def get_scores_service(
    score_repo: ScoreRepository = Depends(get_score_repository),
    match_repo: MatchRepository = Depends(get_match_repository),
    team_repo: TeamRepository = Depends(get_team_repository),
    actual_repo: ActualResultRepository = Depends(get_actual_result_repository),
    pred_repo: PredictionRepository = Depends(get_prediction_repository),
    tech_repo: TechnicalEvaluationRepository = Depends(get_technical_evaluation_repository),
    pres_repo: PresentationEvaluationRepository = Depends(get_presentation_evaluation_repository),
    judge_repo: JudgeRepository = Depends(get_judge_repository),
    pres_score_repo: PresentationScoreRepository = Depends(get_presentation_score_repository),
) -> ScoresService:
    return ScoresService(
        score_repo,
        match_repo,
        team_repo,
        actual_repo,
        pred_repo,
        tech_repo,
        pres_repo,
        judge_repo,
        pres_score_repo,
    )

def get_result_service(
    actual_repo: ActualResultRepository = Depends(get_actual_result_repository),
) -> ResultService:
    return ResultService(actual_repo)

def get_presentation_round_service(
    round_repo: PresentationRoundRepository = Depends(get_presentation_round_repository),
) -> PresentationRoundService:
    return PresentationRoundService(round_repo)
