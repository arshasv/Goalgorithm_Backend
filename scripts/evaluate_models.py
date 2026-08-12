#!/usr/bin/env python3
"""
FIFA World Cup Model Evaluation & Analytics System
===================================================
Evaluates all uploaded .pkl models against 32 FIFA matches,
generates per-team reports and an overall tournament report.

Usage:
    cd /home/opentrends/Desktop/Arsha/Goalgorithm/backend
    python3 scripts/evaluate_models.py
"""

import os
import sys
import json
import time
import math
import pickle
import logging
import traceback
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Any

# ── Bootstrap path ──────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# ── Environment ─────────────────────────────────────────────────
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://goalgorithm:npg_VAFnHKdGy3O9@ep-solitary-fire-as2no21e-pooler.c-4.eu-central-1.aws.neon.tech/goalgorithm?sslmode=require",
)
os.environ.setdefault("SECRET_KEY", "dev")

# ── Logging ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("evaluator")

# ── Output directory ────────────────────────────────────────────
REPORTS_DIR = BACKEND_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class MatchInfo:
    id: str
    match_number: int
    home_team: str
    away_team: str
    status: str
    scheduled_at: str


@dataclass
class ActualResult:
    match_id: str
    actual_winner: str
    actual_home_goals: int | None
    actual_away_goals: int | None
    first_team_to_score: str


@dataclass
class Prediction:
    team_id: str
    match_id: str
    predicted_winner: str
    home_win_probability: float | None
    draw_probability: float | None
    away_win_probability: float | None
    predicted_home_goals: int | None
    predicted_away_goals: int | None
    both_teams_to_score_prediction: bool | None
    first_goal_team: str | None
    raw_payload: dict | None = None


@dataclass
class Score:
    team_id: str
    match_id: str
    winner_points: float
    scoreline_points: float
    probability_points: float
    player_points: float
    total_goals_points: float
    btts_points: float
    first_team_to_score_points: float
    clean_sheet_points: float
    base_score: float | None
    match_rank: int | None
    grade: str | None
    multiplier: int | None
    earned_points: float | None


@dataclass
class TeamInfo:
    id: str
    team_id_code: str
    name: str
    name_normalized: str
    code: str
    team_leader_name: str
    registered_at: str
    is_active: bool
    members: list = field(default_factory=list)


@dataclass
class LeaderboardEntry:
    team_id: str
    rank: int | None
    phase1_score: float | None
    technical_score: float | None
    presentation_score: float | None
    final_score: float | None


@dataclass
class TechnicalEval:
    team_id: str
    code_quality: int | None
    backend_quality: int | None
    teamwork: int | None
    ai_explanation: int | None
    total_score: int | None


@dataclass
class PresentationEval:
    team_id: str
    ai_explanation_score: int | None
    qa_score: int | None
    delivery_score: int | None
    raw_total: float | None
    presentation_score: float | None
    rank: int | None
    grade: str | None
    multiplier: int | None
    judge_count: int | None
    judge_scores: list | None = None
    presentation_criteria_config: list | None = None
    max_marks: int | None = None



@dataclass
class ModelFile:
    team_folder: str
    filename: str
    filepath: str
    file_size: int
    modified_at: str
    version: int | None
    loadable: bool = False
    model_type: str = ""
    has_predict: bool = False
    error: str = ""
    inference_time_ms: float = 0.0
    prediction_output: dict | None = None


@dataclass
class MatchPrediction:
    match_number: int
    home_team: str
    away_team: str
    actual_winner: str
    actual_home_goals: int | None
    actual_away_goals: int | None
    predicted_winner: str
    predicted_home_goals: int | None
    predicted_away_goals: int | None
    home_win_prob: float | None
    draw_prob: float | None
    away_win_prob: float | None
    confidence: float | None
    winner_correct: bool
    score_correct: bool
    goal_diff_correct: bool
    prediction_status: str


@dataclass
class ModelEvaluation:
    model_file: ModelFile
    total_matches: int = 0
    correct_winner: int = 0
    correct_score: int = 0
    correct_goal_diff: int = 0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    log_loss: float = 0.0
    brier_score: float = 0.0
    win_accuracy: float = 0.0
    draw_accuracy: float = 0.0
    loss_accuracy: float = 0.0
    goal_accuracy: float = 0.0
    avg_confidence: float = 0.0
    confusion_matrix: list = field(default_factory=list)
    match_predictions: list = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
#  DATABASE LAYER
# ═══════════════════════════════════════════════════════════════

class DatabaseReader:
    """Read-only queries against the PostgreSQL database."""

    def __init__(self):
        from sqlalchemy import create_engine, text
        self.engine = create_engine(os.environ["DATABASE_URL"])
        self._text = text

    def _query(self, sql: str) -> list[dict]:
        with self.engine.connect() as conn:
            result = conn.execute(self._text(sql))
            return [dict(row._mapping) for row in result]

    def get_teams(self) -> list[TeamInfo]:
        rows = self._query(
            "SELECT id, team_id, name, name_normalized, code, team_leader_name, "
            "registered_at::text, is_active FROM teams ORDER BY team_id"
        )
        teams = []
        for r in rows:
            members = self._query(
                f"SELECT name, employee_id FROM team_members "
                f"WHERE team_id = '{r['id']}'"
            )
            t = TeamInfo(
                id=str(r["id"]),
                team_id_code=r["team_id"],
                name=r["name"],
                name_normalized=r["name_normalized"],
                code=r["code"],
                team_leader_name=r["team_leader_name"],
                registered_at=r["registered_at"],
                is_active=r["is_active"],
                members=[{"name": m["name"], "employee_id": m["employee_id"]} for m in members],
            )
            teams.append(t)
        return teams

    def get_matches(self) -> list[MatchInfo]:
        rows = self._query(
            "SELECT id::text, match_number, home_team_name, away_team_name, "
            "status, scheduled_at::text FROM matches ORDER BY match_number"
        )
        return [MatchInfo(
            id=str(r["id"]),
            match_number=r["match_number"],
            home_team=r["home_team_name"],
            away_team=r["away_team_name"],
            status=r["status"],
            scheduled_at=r["scheduled_at"],
        ) for r in rows]

    def get_actual_results(self) -> dict[str, ActualResult]:
        rows = self._query(
            "SELECT match_id::text, actual_winner, actual_home_goals, "
            "actual_away_goals, first_team_to_score FROM actual_results"
        )
        return {
            r["match_id"]: ActualResult(
                match_id=r["match_id"],
                actual_winner=r["actual_winner"],
                actual_home_goals=r["actual_home_goals"],
                actual_away_goals=r["actual_away_goals"],
                first_team_to_score=r["first_team_to_score"],
            )
            for r in rows
        }

    def get_predictions(self) -> list[Prediction]:
        rows = self._query(
            "SELECT team_id::text, match_id::text, predicted_winner, "
            "home_win_probability, draw_probability, away_win_probability, "
            "predicted_home_goals, predicted_away_goals, "
            "both_teams_to_score_prediction, first_goal_team, "
            "raw_payload FROM predictions"
        )
        return [Prediction(
            team_id=str(r["team_id"]),
            match_id=str(r["match_id"]),
            predicted_winner=r["predicted_winner"],
            home_win_probability=r["home_win_probability"],
            draw_probability=r["draw_probability"],
            away_win_probability=r["away_win_probability"],
            predicted_home_goals=r["predicted_home_goals"],
            predicted_away_goals=r["predicted_away_goals"],
            both_teams_to_score_prediction=r["both_teams_to_score_prediction"],
            first_goal_team=r["first_goal_team"],
            raw_payload=r.get("raw_payload"),
        ) for r in rows]

    def get_scores(self) -> list[Score]:
        rows = self._query(
            "SELECT team_id::text, match_id::text, winner_points, scoreline_points, "
            "probability_points, player_points, total_goals_points, btts_points, "
            "first_team_to_score_points, clean_sheet_points, base_score, "
            "match_rank, grade, multiplier, earned_points FROM scores"
        )
        return [Score(
            team_id=str(r["team_id"]),
            match_id=str(r["match_id"]),
            winner_points=r["winner_points"] or 0,
            scoreline_points=r["scoreline_points"] or 0,
            probability_points=r["probability_points"] or 0,
            player_points=r["player_points"] or 0,
            total_goals_points=r["total_goals_points"] or 0,
            btts_points=r["btts_points"] or 0,
            first_team_to_score_points=r["first_team_to_score_points"] or 0,
            clean_sheet_points=r["clean_sheet_points"] or 0,
            base_score=r["base_score"],
            match_rank=r["match_rank"],
            grade=r["grade"],
            multiplier=r["multiplier"],
            earned_points=r["earned_points"],
        ) for r in rows]

    def get_leaderboard(self) -> list[LeaderboardEntry]:
        rows = self._query(
            "SELECT team_id::text, rank, phase1_score, technical_score, "
            "presentation_score, final_score FROM leaderboard ORDER BY rank"
        )
        return [LeaderboardEntry(
            team_id=str(r["team_id"]),
            rank=r["rank"],
            phase1_score=r["phase1_score"],
            technical_score=r["technical_score"],
            presentation_score=r["presentation_score"],
            final_score=r["final_score"],
        ) for r in rows]

    def get_technical_evals(self) -> dict[str, TechnicalEval]:
        rows = self._query(
            "SELECT team_id::text, code_quality, backend_quality, "
            "teamwork, ai_explanation, total_score FROM technical_evaluations"
        )
        return {
            str(r["team_id"]): TechnicalEval(
                team_id=str(r["team_id"]),
                code_quality=r["code_quality"],
                backend_quality=r["backend_quality"],
                teamwork=r["teamwork"],
                ai_explanation=r["ai_explanation"],
                total_score=r["total_score"],
            )
            for r in rows
        }

    def get_presentation_evals(self) -> dict[str, PresentationEval]:
        rows = self._query(
            "SELECT team_id::text, ai_explanation_score, qa_score, delivery_score, "
            "raw_total, presentation_score, rank, grade, multiplier, judge_count, "
            "judge_scores, presentation_criteria_config, max_marks "
            "FROM presentation_evaluations"
        )
        return {
            str(r["team_id"]): PresentationEval(
                team_id=str(r["team_id"]),
                ai_explanation_score=r["ai_explanation_score"],
                qa_score=r["qa_score"],
                delivery_score=r["delivery_score"],
                raw_total=r["raw_total"],
                presentation_score=r["presentation_score"],
                rank=r["rank"],
                grade=r["grade"],
                multiplier=r["multiplier"],
                judge_count=r["judge_count"],
                judge_scores=r["judge_scores"],
                presentation_criteria_config=r["presentation_criteria_config"],
                max_marks=r["max_marks"],
            )
            for r in rows
        }

    def get_model_submissions(self) -> list[dict]:
        return self._query(
            "SELECT id::text, team_id::text, model_name, file_name, file_type, "
            "file_path, file_size, version, model_type, status, is_active, "
            "uploaded_at::text FROM model_submissions ORDER BY team_id, version"
        )

    def get_model_evaluations(self) -> list[dict]:
        return self._query(
            "SELECT model_id::text, team_id::text, overall_accuracy, "
            "winner_prediction_accuracy, scoreline_accuracy, matches_tested, "
            "final_ai_score, strength_category, weakness_category "
            "FROM model_evaluations"
        )


# ═══════════════════════════════════════════════════════════════
#  MODEL DISCOVERY & LOADING
# ═══════════════════════════════════════════════════════════════

class ModelDiscovery:
    """Scan uploads/ directory, discover and load .pkl models."""

    TEAM_FOLDER_MAP = {
        "bol": "bol",
        "goalGPT": "goalGPT",
        "goaljyolsyan": "goaljyolsyan",
        "paulneerali": "paulneerali",
        "soccersence": "soccersence",
    }

    def __init__(self, uploads_dir: Path):
        self.uploads_dir = uploads_dir

    def discover_all(self) -> list[ModelFile]:
        models = []
        for team_folder in sorted(self.uploads_dir.iterdir()):
            if not team_folder.is_dir():
                continue
            for pkl_file in sorted(team_folder.glob("*.pkl")):
                mf = self._inspect_file(team_folder.name, pkl_file)
                models.append(mf)
        return models

    def _inspect_file(self, team_folder: str, pkl_file: Path) -> ModelFile:
        import re
        size = pkl_file.stat().st_size
        mtime = time.ctime(pkl_file.stat().st_mtime)
        version = None
        m = re.search(r'v(\d+)', pkl_file.stem)
        if m:
            version = int(m.group(1))

        mf = ModelFile(
            team_folder=team_folder,
            filename=pkl_file.name,
            filepath=str(pkl_file),
            file_size=size,
            modified_at=mtime,
            version=version,
        )
        return mf

    def load_model(self, mf: ModelFile) -> Any:
        try:
            from app.model_execution.services.model_compat import safe_load
            with open(mf.filepath, "rb") as f:
                model = safe_load(f)
            mf.loadable = True
            mf.model_type = f"{type(model).__module__}.{type(model).__name__}"
            mf.has_predict = hasattr(model, "predict")
            return model
        except Exception as e:
            mf.error = str(e)
            mf.loadable = False
            return None

    def run_inference(self, model, mf: ModelFile, home_team: str, away_team: str) -> dict | None:
        if not mf.has_predict:
            return None
        try:
            start = time.time()
            output = model.predict({"home_team": home_team, "away_team": away_team})
            mf.inference_time_ms = (time.time() - start) * 1000
            return output if isinstance(output, dict) else {"raw": output}
        except Exception as e:
            mf.error = f"Inference failed: {e}"
            return None


# ═══════════════════════════════════════════════════════════════
#  EVALUATION ENGINE
# ═══════════════════════════════════════════════════════════════

class EvaluationEngine:
    """Compute metrics from predictions vs actual results."""

    @staticmethod
    def extract_prediction(model_output: dict) -> dict:
        """Extract normalized prediction from various model output formats."""
        if not isinstance(model_output, dict):
            return {}

        # Standard format (from ModelSerializer)
        output = model_output.get("output", model_output)
        match_pred = output.get("match_prediction", {})
        score_pred = output.get("score_prediction", {})
        goal_insights = output.get("goal_insights", {})

        win_probs = match_pred.get("win_probabilities", {})
        if not win_probs:
            win_probs = match_pred.get("probabilities", {})

        # Handle both formats
        def _to_float(val, default=0):
            try:
                return float(val) if val is not None else default
            except (ValueError, TypeError):
                return default

        if "home_team" in win_probs:
            home_prob = _to_float(win_probs.get("home_team", {}).get("probability", 0))
            away_prob = _to_float(win_probs.get("away_team", {}).get("probability", 0))
            draw_prob = _to_float(win_probs.get("draw", {}).get("probability", 0))
        else:
            home_prob = _to_float(win_probs.get("home_win_probability", 0))
            away_prob = _to_float(win_probs.get("away_win_probability", 0))
            draw_prob = _to_float(win_probs.get("draw_probability", 0))

        # Normalize to 0-1
        total = home_prob + away_prob + draw_prob
        if total > 1:
            home_prob /= total
            away_prob /= total
            draw_prob /= total

        # Always derive winner from probabilities - models don't include predicted_winner
        probs = {"home": home_prob, "draw": draw_prob, "away": away_prob}
        predicted_winner = max(probs, key=probs.get)

        scoreline = score_pred.get("predicted_scoreline", {})
        home_goals = scoreline.get("home_goals", scoreline.get("home_team_goals", 0))
        away_goals = scoreline.get("away_goals", scoreline.get("away_team_goals", 0))
        try:
            home_goals = int(home_goals) if home_goals is not None else 0
            away_goals = int(away_goals) if away_goals is not None else 0
        except (ValueError, TypeError):
            home_goals = 0
            away_goals = 0

        return {
            "predicted_winner": predicted_winner,
            "home_win_probability": home_prob,
            "draw_probability": draw_prob,
            "away_win_probability": away_prob,
            "predicted_home_goals": int(home_goals) if home_goals else 0,
            "predicted_away_goals": int(away_goals) if away_goals else 0,
            "confidence": max(home_prob, draw_prob, away_prob),
        }

    @staticmethod
    def evaluate_predictions(
        match_predictions: list[dict],
        matches: list[MatchInfo],
        results: dict[str, ActualResult],
    ) -> ModelEvaluation:
        """Compute comprehensive metrics from match predictions."""
        total = len(match_predictions)
        if total == 0:
            return ModelEvaluation(model_file=None)

        correct_winner = sum(1 for p in match_predictions if p["winner_correct"])
        correct_score = sum(1 for p in match_predictions if p["score_correct"])
        correct_goal_diff = sum(1 for p in match_predictions if p["goal_diff_correct"])

        accuracy = (correct_winner / total * 100) if total > 0 else 0
        goal_accuracy = (correct_score / total * 100) if total > 0 else 0

        # Confusion matrix
        cm = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        label_idx = {"home": 0, "draw": 1, "away": 2}
        for p in match_predictions:
            ai = label_idx.get(p["actual_winner"], 1)
            pi = label_idx.get(p["predicted_winner"], 1)
            cm[ai][pi] += 1

        # Precision/Recall/F1 (macro-averaged)
        precisions, recalls, f1s = [], [], []
        for cls in range(3):
            tp = cm[cls][cls]
            fp = sum(cm[row][cls] for row in range(3)) - tp
            fn = sum(cm[cls][col] for col in range(3)) - tp
            p = tp / (tp + fp) if (tp + fp) > 0 else 0
            r = tp / (tp + fn) if (tp + fn) > 0 else 0
            f = 2 * p * r / (p + r) if (p + r) > 0 else 0
            precisions.append(p)
            recalls.append(r)
            f1s.append(f)

        avg_precision = sum(precisions) / 3 * 100
        avg_recall = sum(recalls) / 3 * 100
        avg_f1 = sum(f1s) / 3 * 100

        # Per-outcome accuracy
        actual_home = [p for p in match_predictions if p["actual_winner"] == "home"]
        actual_draw = [p for p in match_predictions if p["actual_winner"] == "draw"]
        actual_away = [p for p in match_predictions if p["actual_winner"] == "away"]

        home_acc = (sum(1 for p in actual_home if p["winner_correct"]) / len(actual_home) * 100) if actual_home else 0
        draw_acc = (sum(1 for p in actual_draw if p["winner_correct"]) / len(actual_draw) * 100) if actual_draw else 0
        away_acc = (sum(1 for p in actual_away if p["winner_correct"]) / len(actual_away) * 100) if actual_away else 0

        # Log loss
        eps = 1e-15
        log_loss_sum = 0
        valid_count = 0
        for p in match_predictions:
            probs = [p["home_win_prob"] or 0, p["draw_prob"] or 0, p["away_win_prob"] or 0]
            if sum(probs) < 0.01:
                continue
            p_sum = sum(probs)
            probs = [max(pr / p_sum, eps) for pr in probs]
            ai = label_idx.get(p["actual_winner"], 1)
            log_loss_sum += -math.log(max(probs[ai], eps))
            valid_count += 1
        log_loss = log_loss_sum / valid_count if valid_count > 0 else 0

        # Brier score
        brier_sum = 0
        brier_count = 0
        for p in match_predictions:
            probs = [p["home_win_prob"] or 0, p["draw_prob"] or 0, p["away_win_prob"] or 0]
            if sum(probs) < 0.01:
                continue
            p_sum = sum(probs)
            probs = [pr / p_sum for pr in probs]
            ai = label_idx.get(p["actual_winner"], 1)
            for i in range(3):
                actual_val = 1.0 if i == ai else 0.0
                brier_sum += (probs[i] - actual_val) ** 2
            brier_count += 1
        brier = brier_sum / brier_count if brier_count > 0 else 0

        # Average confidence
        confs = [p["confidence"] for p in match_predictions if p["confidence"] is not None]
        avg_conf = sum(confs) / len(confs) * 100 if confs else 0

        return ModelEvaluation(
            model_file=None,
            total_matches=total,
            correct_winner=correct_winner,
            correct_score=correct_score,
            correct_goal_diff=correct_goal_diff,
            accuracy=round(accuracy, 2),
            precision=round(avg_precision, 2),
            recall=round(avg_recall, 2),
            f1_score=round(avg_f1, 2),
            log_loss=round(log_loss, 4),
            brier_score=round(brier, 4),
            win_accuracy=round(home_acc, 2),
            draw_accuracy=round(draw_acc, 2),
            loss_accuracy=round(away_acc, 2),
            goal_accuracy=round(goal_accuracy, 2),
            avg_confidence=round(avg_conf, 2),
            confusion_matrix=cm,
            match_predictions=match_predictions,
        )

    @staticmethod
    def compare_match_prediction(
        predicted: dict,
        actual: ActualResult,
        match: MatchInfo,
    ) -> dict:
        """Compare a single model prediction against actual result."""
        pw = predicted.get("predicted_winner", "draw").lower()
        aw = actual.actual_winner.lower() if actual.actual_winner else "draw"
        winner_correct = pw == aw

        phg = predicted.get("predicted_home_goals", 0)
        pahg = predicted.get("predicted_away_goals", 0)
        ahg = actual.actual_home_goals
        aahg = actual.actual_away_goals

        score_correct = (phg == ahg and pahg == aahg) if (ahg is not None and aahg is not None) else False
        goal_diff_correct = ((phg - pahg) == (ahg - aahg)) if (ahg is not None and aahg is not None) else False

        # Status
        if winner_correct and score_correct:
            status = "CORRECT_EXACT"
        elif winner_correct:
            status = "CORRECT_WINNER"
        elif goal_diff_correct:
            status = "CORRECT_GOAL_DIFF"
        else:
            status = "INCORRECT"

        return {
            "match_number": match.match_number,
            "home_team": match.home_team,
            "away_team": match.away_team,
            "actual_winner": aw,
            "actual_home_goals": ahg,
            "actual_away_goals": aahg,
            "predicted_winner": pw,
            "predicted_home_goals": phg,
            "predicted_away_goals": pahg,
            "home_win_prob": predicted.get("home_win_probability"),
            "draw_prob": predicted.get("draw_probability"),
            "away_win_prob": predicted.get("away_win_probability"),
            "confidence": predicted.get("confidence"),
            "winner_correct": winner_correct,
            "score_correct": score_correct,
            "goal_diff_correct": goal_diff_correct,
            "prediction_status": status,
        }


# ═══════════════════════════════════════════════════════════════
#  VISUALIZATION GENERATOR
# ═══════════════════════════════════════════════════════════════

class VisualizationGenerator:
    """Generate matplotlib charts for reports."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_backend(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
        return plt, mticker

    def accuracy_bar_chart(self, team_name: str, evaluations: list[ModelEvaluation], filename: str):
        plt, _ = self._get_backend()
        fig, ax = plt.subplots(figsize=(12, 6))
        labels = [e.model_file.filename.replace(".pkl", "") for e in evaluations if e.model_file]
        accuracies = [e.accuracy for e in evaluations]
        colors = ["#2ecc71" if a > 50 else "#e74c3c" if a < 30 else "#f39c12" for a in accuracies]
        bars = ax.barh(labels, accuracies, color=colors, edgecolor="white", linewidth=0.5)
        ax.set_xlabel("Accuracy (%)", fontsize=12)
        ax.set_title(f"{team_name} - Model Accuracy Comparison", fontsize=14, fontweight="bold")
        ax.set_xlim(0, 100)
        for bar, acc in zip(bars, accuracies):
            ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, f"{acc:.1f}%", va="center", fontsize=10)
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def confusion_matrix_heatmap(self, team_name: str, cm: list, filename: str):
        plt, _ = self._get_backend()
        fig, ax = plt.subplots(figsize=(8, 6))
        import numpy as np
        im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
        ax.figure.colorbar(im, ax=ax)
        classes = ["Home Win", "Draw", "Away Win"]
        ax.set(xticks=[0, 1, 2], yticks=[0, 1, 2], xticklabels=classes, yticklabels=classes,
               xlabel="Predicted", ylabel="Actual", title=f"{team_name} - Confusion Matrix")
        for i in range(3):
            for j in range(3):
                ax.text(j, i, str(cm[i][j]), ha="center", va="center",
                        color="white" if cm[i][j] > max(max(row) for row in cm) / 2 else "black")
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def correct_incorrect_pie(self, team_name: str, correct: int, incorrect: int, filename: str):
        plt, _ = self._get_backend()
        fig, ax = plt.subplots(figsize=(8, 6))
        sizes = [correct, incorrect]
        labels = [f"Correct ({correct})", f"Incorrect ({incorrect})"]
        colors = ["#2ecc71", "#e74c3c"]
        explode = (0.05, 0)
        if correct + incorrect > 0:
            ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct="%1.1f%%",
                   shadow=True, startangle=90, textprops={"fontsize": 12})
        ax.set_title(f"{team_name} - Prediction Accuracy", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def match_accuracy_timeline(self, team_name: str, predictions: list[dict], filename: str):
        plt, _ = self._get_backend()
        fig, ax = plt.subplots(figsize=(14, 5))
        match_nums = [p["match_number"] for p in predictions]
        correct_flags = [1 if p.get("winner_correct") or p.get("correct") else 0 for p in predictions]
        # Rolling average
        window = 5
        rolling_avg = []
        for i in range(len(correct_flags)):
            start = max(0, i - window + 1)
            rolling_avg.append(sum(correct_flags[start:i+1]) / (i - start + 1) * 100)

        ax.bar(match_nums, correct_flags, color=["#2ecc71" if c else "#e74c3c" for c in correct_flags], alpha=0.6, label="Correct (1) / Incorrect (0)")
        ax.plot(match_nums, rolling_avg, color="#3498db", linewidth=2, label=f"{window}-Match Rolling Avg")
        ax.set_xlabel("Match Number")
        ax.set_ylabel("Correct Prediction")
        ax.set_title(f"{team_name} - Match Accuracy Timeline", fontsize=14, fontweight="bold")
        ax.legend()
        ax.set_ylim(0, 110)
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def radar_chart(self, team_name: str, metrics: dict, filename: str):
        plt, _ = self._get_backend()
        import numpy as np
        categories = list(metrics.keys())
        values = list(metrics.values())
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]
        values += values[:1]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        ax.plot(angles, values, "o-", linewidth=2, color="#3498db")
        ax.fill(angles, values, alpha=0.25, color="#3498db")
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        ax.set_title(f"{team_name} - Performance Radar", fontsize=14, fontweight="bold", y=1.08)
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def win_draw_loss_distribution(self, team_name: str, predictions: list[dict], filename: str):
        plt, _ = self._get_backend()
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        for idx, (outcome, color, label) in enumerate([("home", "#2ecc71", "Home Wins"), ("draw", "#f39c12", "Draws"), ("away", "#e74c3c", "Away Wins")]):
            actual = [p for p in predictions if p["actual_winner"] == outcome]
            correct = sum(1 for p in actual if p.get("winner_correct") or p.get("correct"))
            incorrect = len(actual) - correct
            if correct + incorrect > 0:
                axes[idx].pie([correct or 0.001, incorrect or 0.001], labels=["Correct", "Incorrect"],
                              colors=[color, "#bdc3c7"], autopct="%1.1f%%", startangle=90)
            else:
                axes[idx].text(0.5, 0.5, "No data", ha="center", va="center", transform=axes[idx].transAxes)
            axes[idx].set_title(f"{label}\n(n={len(actual)})", fontsize=11)
        fig.suptitle(f"{team_name} - Win/Draw/Loss Prediction Distribution", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def confidence_distribution(self, team_name: str, predictions: list[dict], filename: str):
        plt, _ = self._get_backend()
        fig, ax = plt.subplots(figsize=(10, 5))
        confs = [p["confidence"] * 100 for p in predictions if p["confidence"] is not None]
        if confs:
            ax.hist(confs, bins=20, color="#3498db", edgecolor="white", alpha=0.7)
            ax.axvline(sum(confs)/len(confs), color="#e74c3c", linestyle="--", label=f"Avg: {sum(confs)/len(confs):.1f}%")
        ax.set_xlabel("Confidence (%)")
        ax.set_ylabel("Frequency")
        ax.set_title(f"{team_name} - Prediction Confidence Distribution", fontsize=14, fontweight="bold")
        ax.legend()
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def model_comparison_radar(self, team_name: str, evaluations: list[ModelEvaluation], filename: str):
        plt, _ = self._get_backend()
        import numpy as np
        categories = ["Accuracy", "Precision", "Recall", "F1", "Win Acc", "Goal Acc"]
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
        colors = plt.cm.Set2(np.linspace(0, 1, len(evaluations)))
        for ev, color in zip(evaluations, colors):
            if not ev.model_file:
                continue
            values = [ev.accuracy, ev.precision, ev.recall, ev.f1_score, ev.win_accuracy, ev.goal_accuracy]
            values += values[:1]
            label = ev.model_file.filename.replace(".pkl", "")
            ax.plot(angles, values, "o-", linewidth=2, label=label, color=color)
            ax.fill(angles, values, alpha=0.1, color=color)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        ax.set_title(f"{team_name} - Model Comparison Radar", fontsize=14, fontweight="bold", y=1.08)
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8)
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def score_distribution(self, team_name: str, predictions: list[dict], filename: str):
        plt, _ = self._get_backend()
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        # Home goals
        pred_home = [p["predicted_home_goals"] for p in predictions if p["predicted_home_goals"] is not None]
        actual_home = [p["actual_home_goals"] for p in predictions if p["actual_home_goals"] is not None]
        if pred_home and actual_home:
            x = range(max(max(pred_home), max(actual_home)) + 1)
            from collections import Counter
            pred_c = Counter(pred_home)
            actual_c = Counter(actual_home)
            width = 0.35
            axes[0].bar([i - width/2 for i in x], [pred_c.get(i, 0) for i in x], width, label="Predicted", color="#3498db")
            axes[0].bar([i + width/2 for i in x], [actual_c.get(i, 0) for i in x], width, label="Actual", color="#e74c3c")
            axes[0].set_xlabel("Goals")
            axes[0].set_ylabel("Frequency")
            axes[0].set_title("Home Goals Distribution")
            axes[0].legend()
        # Away goals
        pred_away = [p["predicted_away_goals"] for p in predictions if p["predicted_away_goals"] is not None]
        actual_away = [p["actual_away_goals"] for p in predictions if p["actual_away_goals"] is not None]
        if pred_away and actual_away:
            x = range(max(max(pred_away), max(actual_away)) + 1)
            from collections import Counter
            pred_c = Counter(pred_away)
            actual_c = Counter(actual_away)
            width = 0.35
            axes[1].bar([i - width/2 for i in x], [pred_c.get(i, 0) for i in x], width, label="Predicted", color="#3498db")
            axes[1].bar([i + width/2 for i in x], [actual_c.get(i, 0) for i in x], width, label="Actual", color="#e74c3c")
            axes[1].set_xlabel("Goals")
            axes[1].set_ylabel("Frequency")
            axes[1].set_title("Away Goals Distribution")
            axes[1].legend()
        fig.suptitle(f"{team_name} - Score Prediction Distribution", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def leaderboard_chart(self, leaderboard: list[LeaderboardEntry], teams: dict, filename: str):
        plt, _ = self._get_backend()
        fig, ax = plt.subplots(figsize=(12, 6))
        names = []
        scores = []
        colors_list = ["#2ecc71", "#3498db", "#e74c3c", "#f39c12", "#9b59b6"]
        for entry in leaderboard:
            team_name = teams.get(entry.team_id, entry.team_id)
            names.append(team_name)
            scores.append(entry.final_score or 0)
        bars = ax.bar(names, scores, color=colors_list[:len(names)], edgecolor="white", linewidth=0.5)
        ax.set_ylabel("Final Score", fontsize=12)
        ax.set_title("Tournament Leaderboard", fontsize=14, fontweight="bold")
        for bar, score in zip(bars, scores):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f"{score:.2f}", ha="center", fontsize=11)
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def cross_team_accuracy(self, team_accuracies: dict, filename: str):
        plt, _ = self._get_backend()
        fig, ax = plt.subplots(figsize=(12, 6))
        names = list(team_accuracies.keys())
        accs = list(team_accuracies.values())
        colors = plt.cm.RdYlGn([a / 100 for a in accs])
        bars = ax.bar(names, accs, color=colors, edgecolor="white")
        ax.set_ylabel("Accuracy (%)", fontsize=12)
        ax.set_title("Cross-Team Model Accuracy Comparison", fontsize=14, fontweight="bold")
        ax.set_ylim(0, 100)
        for bar, acc in zip(bars, accs):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f"{acc:.1f}%", ha="center", fontsize=11)
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def mlops_radar(self, team_name: str, scores: dict, filename: str):
        plt, _ = self._get_backend()
        import numpy as np
        categories = list(scores.keys())
        values = list(scores.values())
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]
        values += values[:1]
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        ax.plot(angles, values, "o-", linewidth=2, color="#9b59b6")
        ax.fill(angles, values, alpha=0.25, color="#9b59b6")
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=9)
        ax.set_ylim(0, 10)
        ax.set_title(f"{team_name} - MLOps Evaluation", fontsize=14, fontweight="bold", y=1.08)
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()

    def presentation_comparison(self, teams_data: list[dict], filename: str):
        plt, _ = self._get_backend()
        fig, ax = plt.subplots(figsize=(12, 6))
        names = [d["name"] for d in teams_data]
        scores = [d["score"] for d in teams_data]
        colors = plt.cm.RdYlGn([s / 20 for s in scores])
        bars = ax.bar(names, scores, color=colors, edgecolor="white")
        ax.set_ylabel("Presentation Score", fontsize=12)
        ax.set_title("Presentation Evaluation Comparison", fontsize=14, fontweight="bold")
        for bar, score in zip(bars, scores):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, f"{score:.2f}", ha="center", fontsize=11)
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=150, bbox_inches="tight")
        plt.close()


# ═══════════════════════════════════════════════════════════════
#  REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════

class ReportGenerator:
    """Generate Markdown reports for teams and tournament."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def generate_team_report(
        self,
        team: TeamInfo,
        evaluations: list[ModelEvaluation],
        db_predictions: list[Prediction],
        db_scores: list[Score],
        leaderboard_entry: LeaderboardEntry | None,
        tech_eval: TechnicalEval | None,
        pres_eval: PresentationEval | None,
        matches: list[MatchInfo],
        results: dict[str, ActualResult],
        model_files: list[ModelFile],
        viz: VisualizationGenerator,
    ) -> str:
        """Generate complete Markdown report for a single team."""
        team_id = team.id
        team_name = team.name

        # Filter DB predictions for this team
        team_preds = [p for p in db_predictions if p.team_id == team_id]
        team_scores = [s for s in db_scores if s.team_id == team_id]
        result_map = {r.match_id: r for r in results.values()}

        # Build DB-level match breakdown
        match_breakdown = []
        for pred in team_preds:
            match = next((m for m in matches if m.id == pred.match_id), None)
            actual = result_map.get(pred.match_id)
            if match and actual:
                pw = pred.predicted_winner.lower() if pred.predicted_winner else "draw"
                aw = actual.actual_winner.lower() if actual.actual_winner else "draw"
                correct = pw == aw
                match_breakdown.append({
                    "match_number": match.match_number,
                    "home_team": match.home_team,
                    "away_team": match.away_team,
                    "actual_winner": aw,
                    "actual_home_goals": actual.actual_home_goals,
                    "actual_away_goals": actual.actual_away_goals,
                    "predicted_winner": pw,
                    "predicted_home_goals": pred.predicted_home_goals,
                    "predicted_away_goals": pred.predicted_away_goals,
                    "correct": correct,
                    "confidence": max(
                        pred.home_win_probability or 0,
                        pred.draw_probability or 0,
                        pred.away_win_probability or 0,
                    ),
                })

        total_preds = len(match_breakdown)
        db_correct = sum(1 for m in match_breakdown if m["correct"])
        db_accuracy = (db_correct / total_preds * 100) if total_preds > 0 else 0

        # Model-level evaluation summary
        best_eval = max(evaluations, key=lambda e: e.accuracy) if evaluations else None
        worst_eval = min(evaluations, key=lambda e: e.accuracy) if evaluations else None

        # MLOps scoring
        mlops_scores = self._compute_mlops_score(team, model_files, evaluations)
        mlops_total = sum(mlops_scores.values()) / len(mlops_scores) if mlops_scores else 0

        # Build the report
        lines = []
        lines.append(f"# {team_name} - Comprehensive Analytics Report")
        lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Team Code:** {team.team_id_code}")
        lines.append(f"**Team Leader:** {team.team_leader_name}")
        lines.append("")

        # 1. Executive Summary
        lines.append("---")
        lines.append("## 1. Executive Summary")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Team Name | {team_name} |")
        lines.append(f"| Team Code | {team.team_id_code} |")
        lines.append(f"| Members | {len(team.members)} |")
        lines.append(f"| Total Models Uploaded | {len(model_files)} |")
        lines.append(f"| DB Predictions | {total_preds} |")
        lines.append(f"| DB Prediction Accuracy | {db_accuracy:.1f}% |")
        if leaderboard_entry:
            lines.append(f"| Tournament Rank | #{leaderboard_entry.rank} |")
            lines.append(f"| Final Score | {leaderboard_entry.final_score:.2f} |")
        if best_eval:
            lines.append(f"| Best Model Accuracy | {best_eval.accuracy:.1f}% |")
        lines.append(f"| MLOps Score | {mlops_total:.1f}/10 |")
        lines.append("")

        # Strengths & Weaknesses
        lines.append("### Strengths")
        lines.append("")
        if db_accuracy > 40:
            lines.append("- Strong prediction accuracy above average")
        if best_eval and best_eval.accuracy > 50:
            lines.append("- High model accuracy achieved with best model")
        if len(model_files) >= 5:
            lines.append("- Active model iteration and versioning")
        if pres_eval and pres_eval.raw_total and pres_eval.raw_total > 10:
            lines.append("- Good presentation performance")
        if not any([db_accuracy > 40, best_eval and best_eval.accuracy > 50, len(model_files) >= 5]):
            lines.append("- Team participated in the competition")
        lines.append("")

        lines.append("### Weaknesses")
        lines.append("")
        if db_accuracy < 40:
            lines.append("- Below-average prediction accuracy")
        if len(evaluations) == 0:
            lines.append("- Models could not be loaded for automated evaluation")
        if tech_eval and tech_eval.total_score == 0:
            lines.append("- Technical evaluation not submitted")
        lines.append("")

        # 2. Team Overview
        lines.append("---")
        lines.append("## 2. Team Overview")
        lines.append("")
        lines.append(f"| Field | Value |")
        lines.append(f"|-------|-------|")
        lines.append(f"| Registered | {team.registered_at} |")
        lines.append(f"| Active | {'Yes' if team.is_active else 'No'} |")
        lines.append(f"| Members | {len(team.members)} |")
        lines.append("")
        if team.members:
            lines.append("### Team Members")
            lines.append("| Name | Employee ID |")
            lines.append("|------|-------------|")
            for m in team.members:
                lines.append(f"| {m['name']} | {m['employee_id'] or 'N/A'} |")
            lines.append("")

        # 3. Model Summary
        lines.append("---")
        lines.append("## 3. Model Summary")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Files | {len(model_files)} |")
        if model_files:
            lines.append(f"| First Upload | {min(mf.modified_at for mf in model_files)} |")
            lines.append(f"| Latest Upload | {max(mf.modified_at for mf in model_files)} |")
            total_size = sum(mf.file_size for mf in model_files)
            lines.append(f"| Total Size | {total_size / 1024 / 1024:.1f} MB |")
        lines.append("")

        if model_files:
            lines.append("### Uploaded Models")
            lines.append("| # | Filename | Size | Version | Loadable | Type |")
            lines.append("|---|----------|------|---------|----------|------|")
            for i, mf in enumerate(model_files, 1):
                size_str = f"{mf.file_size / 1024 / 1024:.1f} MB"
                loadable = "Yes" if mf.loadable else f"No ({mf.error[:50]})"
                v_str = f"v{mf.version}" if mf.version else "N/A"
                lines.append(f"| {i} | {mf.filename} | {size_str} | {v_str} | {loadable} | {mf.model_type[:40] if mf.model_type else 'N/A'} |")
            lines.append("")

        # 4. Match Breakdown (DB predictions)
        lines.append("---")
        lines.append("## 4. Match Breakdown (32 Matches)")
        lines.append("")
        lines.append("| # | Home | Away | Actual | Predicted | Correct | Score |")
        lines.append("|---|------|------|--------|-----------|---------|-------|")
        for m in sorted(match_breakdown, key=lambda x: x["match_number"]):
            correct_mark = "YES" if m["correct"] else "NO"
            actual_score = f"{m['actual_home_goals']}-{m['actual_away_goals']}" if m["actual_home_goals"] is not None else "N/A"
            pred_score = f"{m['predicted_home_goals']}-{m['predicted_away_goals']}" if m["predicted_home_goals"] is not None else "N/A"
            lines.append(f"| {m['match_number']} | {m['home_team']} | {m['away_team']} | {m['actual_winner']} ({actual_score}) | {m['predicted_winner']} ({pred_score}) | {correct_mark} | {m['confidence']:.2f} |")
        lines.append("")
        lines.append(f"**Total Correct: {db_correct}/{total_preds} ({db_accuracy:.1f}%)**")
        lines.append("")

        # Generate visualizations
        if match_breakdown:
            viz.correct_incorrect_pie(team_name, db_correct, total_preds - db_correct, f"{team.team_id_code}_correct_incorrect.png")
            viz.match_accuracy_timeline(team_name, match_breakdown, f"{team.team_id_code}_accuracy_timeline.png")
            # Convert to format expected by radar
            if evaluations and evaluations[0].model_file:
                for ev in evaluations:
                    if ev.model_file:
                        metrics = {
                            "Accuracy": ev.accuracy / 100,
                            "Precision": ev.precision / 100,
                            "Recall": ev.recall / 100,
                            "F1": ev.f1_score / 100,
                            "Win Acc": ev.win_accuracy / 100,
                            "Goal Acc": ev.goal_accuracy / 100,
                        }
                        viz.radar_chart(team_name, metrics, f"{team.team_id_code}_radar_{ev.model_file.filename.replace('.pkl','')}.png")
            # Win/Draw/Loss
            viz.win_draw_loss_distribution(team_name, match_breakdown, f"{team.team_id_code}_win_draw_loss.png")
            viz.confidence_distribution(team_name, match_breakdown, f"{team.team_id_code}_confidence.png")
            viz.score_distribution(team_name, match_breakdown, f"{team.team_id_code}_score_distribution.png")

        # 5. Model Performance Comparison
        lines.append("---")
        lines.append("## 5. Model Performance Comparison")
        lines.append("")
        if evaluations:
            lines.append("| Model | Accuracy | Precision | Recall | F1 | Correct | Total |")
            lines.append("|-------|----------|-----------|--------|----|---------|-------|")
            for ev in sorted(evaluations, key=lambda e: e.accuracy, reverse=True):
                name = ev.model_file.filename if ev.model_file else "N/A"
                lines.append(f"| {name} | {ev.accuracy:.1f}% | {ev.precision:.1f}% | {ev.recall:.1f}% | {ev.f1_score:.1f}% | {ev.correct_winner}/{ev.total_matches} | {ev.total_matches} |")
            lines.append("")

            # Generate charts
            viz.accuracy_bar_chart(team_name, evaluations, f"{team.team_id_code}_accuracy_comparison.png")
            if len(evaluations) > 1:
                viz.model_comparison_radar(team_name, evaluations, f"{team.team_id_code}_model_radar.png")
            # Confusion matrix for best
            if best_eval and best_eval.confusion_matrix:
                viz.confusion_matrix_heatmap(team_name, best_eval.confusion_matrix, f"{team.team_id_code}_confusion_matrix.png")
        else:
            lines.append("*No models could be loaded for automated evaluation.*")
            lines.append("")
            lines.append("**Note:** The following models exist but could not be loaded due to missing dependencies:")
            for mf in model_files:
                lines.append(f"- `{mf.filename}`: {mf.error[:100]}")
            lines.append("")

        # 6. Best Model Analysis
        lines.append("---")
        lines.append("## 6. Best Model Analysis")
        lines.append("")
        if best_eval and best_eval.model_file:
            mf = best_eval.model_file
            lines.append(f"**Best Model:** `{mf.filename}`")
            lines.append(f"- **Accuracy:** {best_eval.accuracy:.1f}%")
            lines.append(f"- **Precision:** {best_eval.precision:.1f}%")
            lines.append(f"- **Recall:** {best_eval.recall:.1f}%")
            lines.append(f"- **F1 Score:** {best_eval.f1_score:.1f}%")
            lines.append(f"- **Correct Winner Predictions:** {best_eval.correct_winner}/{best_eval.total_matches}")
            lines.append(f"- **Exact Score Predictions:** {best_eval.correct_score}/{best_eval.total_matches}")
            lines.append(f"- **Goal Difference Predictions:** {best_eval.correct_goal_diff}/{best_eval.total_matches}")
            lines.append(f"- **Average Confidence:** {best_eval.avg_confidence:.1f}%")
            lines.append(f"- **Log Loss:** {best_eval.log_loss:.4f}")
            lines.append(f"- **Brier Score:** {best_eval.brier_score:.4f}")
            lines.append(f"- **File Size:** {mf.file_size / 1024 / 1024:.1f} MB")
            lines.append(f"- **Inference Time:** {mf.inference_time_ms:.1f} ms")
            lines.append("")
            lines.append("### Strengths")
            lines.append("")
            if best_eval.accuracy > 50:
                lines.append("- Above-average accuracy in winner prediction")
            if best_eval.goal_accuracy > 30:
                lines.append("- Good score prediction capability")
            if best_eval.win_accuracy > 50:
                lines.append("- Strong at predicting home wins")
            lines.append("")
            lines.append("### Weaknesses")
            lines.append("")
            if best_eval.draw_accuracy < 30:
                lines.append("- Struggles to predict draws")
            if best_eval.goal_accuracy < 20:
                lines.append("- Limited exact score prediction accuracy")
            lines.append("")
        else:
            lines.append("*No models could be loaded for analysis.*")
        lines.append("")

        # 7. Other Models Evaluation
        lines.append("---")
        lines.append("## 7. Other Models Evaluation")
        lines.append("")
        if evaluations and len(evaluations) > 1:
            for ev in sorted(evaluations, key=lambda e: e.accuracy, reverse=True)[1:]:
                if ev.model_file:
                    lines.append(f"### {ev.model_file.filename}")
                    lines.append(f"- Accuracy: {ev.accuracy:.1f}%")
                    lines.append(f"- F1: {ev.f1_score:.1f}%")
                    diff = best_eval.accuracy - ev.accuracy if best_eval else 0
                    lines.append(f"- Gap from best: -{diff:.1f}%")
                    lines.append("")
        else:
            lines.append("*Only one model available for comparison, or no models could be loaded.*")
        lines.append("")

        # 8. MLOps Evaluation
        lines.append("---")
        lines.append("## 8. MLOps Evaluation")
        lines.append("")
        lines.append("| Criterion | Score (0-10) |")
        lines.append("|-----------|-------------|")
        for criterion, score in mlops_scores.items():
            lines.append(f"| {criterion} | {score:.1f} |")
        lines.append(f"| **Overall MLOps Score** | **{mlops_total:.1f}/10** |")
        lines.append("")
        if mlops_scores:
            viz.mlops_radar(team_name, mlops_scores, f"{team.team_id_code}_mlops_radar.png")
        lines.append("")

        # 9. ML Architecture Evaluation
        lines.append("---")
        lines.append("## 9. ML Architecture Evaluation")
        lines.append("")
        if model_files:
            loadable = [mf for mf in model_files if mf.loadable]
            if loadable:
                lines.append(f"**Algorithm Types Detected:**")
                for mf in loadable:
                    lines.append(f"- `{mf.filename}`: {mf.model_type}")
                lines.append("")
            lines.append(f"**Architecture Notes:**")
            lines.append(f"- Total model versions: {len(model_files)}")
            lines.append(f"- Models loadable: {len([mf for mf in model_files if mf.loadable])}")
            lines.append(f"- Average file size: {sum(mf.file_size for mf in model_files) / len(model_files) / 1024 / 1024:.1f} MB")
        else:
            lines.append("*No models uploaded by this team.*")
        lines.append("")

        # 10. Presentation Evaluation
        lines.append("---")
        lines.append("## 10. Presentation Evaluation")
        lines.append("")
        if pres_eval:
            lines.append(f"| Metric | Score |")
            lines.append(f"|--------|-------|")
            lines.append(f"| AI Explanation | {pres_eval.ai_explanation_score or 'N/A'} |")
            lines.append(f"| Q&A | {pres_eval.qa_score or 'N/A'} |")
            lines.append(f"| Delivery | {pres_eval.delivery_score or 'N/A'} |")
            lines.append(f"| Raw Total | {pres_eval.raw_total or 'N/A'} |")
            lines.append(f"| Presentation Score | {pres_eval.presentation_score or 'N/A'} |")
            lines.append(f"| Grade | {pres_eval.grade or 'N/A'} |")
            lines.append(f"| Judge Count | {pres_eval.judge_count or 'N/A'} |")
        else:
            lines.append("*No presentation evaluation data available.*")
        lines.append("")

        # 11. Overall Team Performance
        lines.append("---")
        lines.append("## 11. Overall Team Performance")
        lines.append("")
        lines.append("| KPI | Value |")
        lines.append("|-----|-------|")
        lines.append(f"| DB Prediction Accuracy | {db_accuracy:.1f}% |")
        if leaderboard_entry:
            lines.append(f"| Tournament Rank | #{leaderboard_entry.rank} |")
            lines.append(f"| Phase 1 Score | {leaderboard_entry.phase1_score or 0:.2f}/60 |")
            lines.append(f"| Technical Score | {leaderboard_entry.technical_score or 0:.2f}/20 |")
            lines.append(f"| Presentation Score | {leaderboard_entry.presentation_score or 0:.2f}/20 |")
            lines.append(f"| Final Score | {leaderboard_entry.final_score or 0:.2f}/100 |")
        if best_eval:
            lines.append(f"| Best Model Accuracy | {best_eval.accuracy:.1f}% |")
        lines.append(f"| MLOps Score | {mlops_total:.1f}/10 |")
        if pres_eval:
            lines.append(f"| Presentation Grade | {pres_eval.grade or 'N/A'} |")
        lines.append("")

        # 12. Conclusions
        lines.append("---")
        lines.append("## 12. Conclusions & Recommendations")
        lines.append("")
        lines.append("### Key Findings")
        lines.append("")
        lines.append(f"1. The team uploaded {len(model_files)} model versions during the competition.")
        if db_accuracy > 40:
            lines.append(f"2. DB prediction accuracy of {db_accuracy:.1f}% indicates {'strong' if db_accuracy > 50 else 'moderate'} prediction capability.")
        else:
            lines.append(f"2. DB prediction accuracy of {db_accuracy:.1f}% suggests room for improvement.")
        if best_eval:
            lines.append(f"3. Best automated model achieved {best_eval.accuracy:.1f}% accuracy.")
        lines.append("")
        lines.append("### Recommendations")
        lines.append("")
        lines.append("1. Focus on draw prediction accuracy - this is often the hardest outcome to predict")
        lines.append("2. Improve probability calibration for better confidence scores")
        lines.append("3. Consider ensemble methods to combine multiple model versions")
        lines.append("4. Add feature engineering for team-specific statistics")
        lines.append("")

        report = "\n".join(lines)
        report_path = self.output_dir / f"{team.team_id_code}_{team_name.replace(' ', '_')}_report.md"
        report_path.write_text(report)
        return str(report_path)

    def generate_tournament_report(
        self,
        teams: list[TeamInfo],
        leaderboard: list[LeaderboardEntry],
        all_evaluations: dict[str, list[ModelEvaluation]],
        all_predictions: list[Prediction],
        matches: list[MatchInfo],
        results: dict[str, ActualResult],
        tech_evals: dict[str, TechnicalEval],
        pres_evals: dict[str, PresentationEval],
        viz: VisualizationGenerator,
    ) -> str:
        """Generate the overall tournament report."""
        team_name_map = {t.id: t.name for t in teams}
        team_code_map = {t.id: t.team_id_code for t in teams}

        lines = []
        lines.append("# FIFA World Cup Tournament - Overall Analytics Report")
        lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Total Teams:** {len(teams)}")
        lines.append(f"**Total Matches:** {len(matches)}")
        lines.append(f"**Total Predictions:** {len(all_predictions)}")
        lines.append("")

        # Executive Summary
        lines.append("---")
        lines.append("## Executive Summary")
        lines.append("")
        lines.append("### Tournament Rankings")
        lines.append("")
        lines.append("| Rank | Team | Phase 1 | Technical | Presentation | Final Score |")
        lines.append("|------|------|---------|-----------|-------------|-------------|")
        for entry in leaderboard:
            name = team_name_map.get(entry.team_id, entry.team_id)
            lines.append(f"| #{entry.rank} | {name} | {entry.phase1_score or 0:.2f} | {entry.technical_score or 0:.2f} | {entry.presentation_score or 0:.2f} | {entry.final_score or 0:.2f} |")
        lines.append("")

        # Model Accuracy Comparison
        lines.append("### Model Accuracy Comparison")
        lines.append("")
        team_accuracies = {}
        lines.append("| Team | Best Model Accuracy | F1 Score | Correct Predictions |")
        lines.append("|------|-------------------|----------|---------------------|")
        for team in teams:
            evals = all_evaluations.get(team.id, [])
            if evals:
                best = max(evals, key=lambda e: e.accuracy)
                team_accuracies[team.name] = best.accuracy
                lines.append(f"| {team.name} | {best.accuracy:.1f}% | {best.f1_score:.1f}% | {best.correct_winner}/{best.total_matches} |")
            else:
                lines.append(f"| {team.name} | N/A | N/A | N/A |")
        lines.append("")

        if team_accuracies:
            viz.cross_team_accuracy(team_accuracies, "tournament_cross_team_accuracy.png")

        # Leaderboard chart
        if leaderboard:
            viz.leaderboard_chart(leaderboard, team_name_map, "tournament_leaderboard.png")

        # Presentation comparison
        pres_data = []
        for team in teams:
            pe = pres_evals.get(team.id)
            if pe and pe.raw_total:
                pres_data.append({"name": team.name, "score": pe.raw_total})
        if pres_data:
            viz.presentation_comparison(pres_data, "tournament_presentation_comparison.png")

        # Best Overall Model
        all_best = []
        for team_id, evals in all_evaluations.items():
            for ev in evals:
                if ev.model_file:
                    all_best.append((team_name_map.get(team_id, team_id), ev))
        all_best.sort(key=lambda x: x[1].accuracy, reverse=True)

        lines.append("### Best Overall Model")
        lines.append("")
        if all_best:
            top_name, top_ev = all_best[0]
            lines.append(f"**{top_name}** with `{top_ev.model_file.filename}`")
            lines.append(f"- Accuracy: {top_ev.accuracy:.1f}%")
            lines.append(f"- F1: {top_ev.f1_score:.1f}%")
            lines.append(f"- Correct: {top_ev.correct_winner}/{top_ev.total_matches}")
        else:
            lines.append("*No models could be loaded for automated evaluation.*")
        lines.append("")

        # Per-Team Detailed Sections
        for team in teams:
            lines.append("---")
            lines.append(f"## {team.name} - Detailed View")
            lines.append("")
            entry = next((e for e in leaderboard if e.team_id == team.id), None)
            team_preds = [p for p in all_predictions if p.team_id == team.id]

            lines.append(f"| Metric | Value |")
            lines.append(f"|--------|-------|")
            lines.append(f"| Team Code | {team.team_id_code} |")
            lines.append(f"| Members | {len(team.members)} |")
            if entry:
                lines.append(f"| Rank | #{entry.rank} |")
                lines.append(f"| Final Score | {entry.final_score or 0:.2f}/100 |")
            lines.append(f"| DB Predictions | {len(team_preds)} |")

            evals = all_evaluations.get(team.id, [])
            if evals:
                best = max(evals, key=lambda e: e.accuracy)
                lines.append(f"| Best Model Accuracy | {best.accuracy:.1f}% |")
            lines.append("")

            te = tech_evals.get(team.id)
            pe = pres_evals.get(team.id)
            if te or pe:
                lines.append("**Evaluation Scores:**")
                lines.append("")
                if te:
                    lines.append(f"- Technical: {te.total_score or 0}/20")
                if pe:
                    lines.append(f"- Presentation: {pe.raw_total or 0} ({pe.grade or 'N/A'})")
                lines.append("")

        # Cross-team performance
        lines.append("---")
        lines.append("## Cross-Team Performance Comparison")
        lines.append("")
        lines.append("### DB Prediction Accuracy by Team")
        lines.append("")
        for team in teams:
            team_preds = [p for p in all_predictions if p.team_id == team.id]
            team_match_preds = []
            result_map = {r.match_id: r for r in results.values()}
            for pred in team_preds:
                actual = result_map.get(pred.match_id)
                if actual:
                    correct = (pred.predicted_winner or "").lower() == (actual.actual_winner or "").lower()
                    team_match_preds.append(correct)
            if team_match_preds:
                acc = sum(team_match_preds) / len(team_match_preds) * 100
                lines.append(f"- **{team.name}:** {acc:.1f}% ({sum(team_match_preds)}/{len(team_match_preds)})")
        lines.append("")

        # Technical & Presentation Comparison
        lines.append("### Technical Evaluation Comparison")
        lines.append("")
        lines.append("| Team | Code Quality | Backend | Teamwork | AI Explanation | Total |")
        lines.append("|------|-------------|---------|----------|---------------|-------|")
        for team in teams:
            te = tech_evals.get(team.id)
            if te:
                lines.append(f"| {team.name} | {te.code_quality or 0} | {te.backend_quality or 0} | {te.teamwork or 0} | {te.ai_explanation or 0} | {te.total_score or 0} |")
            else:
                lines.append(f"| {team.name} | N/A | N/A | N/A | N/A | N/A |")
        lines.append("")

        lines.append("### Presentation Evaluation Comparison")
        lines.append("")
        lines.append("| Team | AI Explanation | Q&A | Delivery | Raw Total | Grade | Rank |")
        lines.append("|------|---------------|-----|----------|-----------|-------|------|")
        for team in teams:
            pe = pres_evals.get(team.id)
            if pe:
                lines.append(f"| {team.name} | {pe.ai_explanation_score or 0} | {pe.qa_score or 0} | {pe.delivery_score or 0} | {pe.raw_total or 0} | {pe.grade or 'N/A'} | {pe.rank or 'N/A'} |")
            else:
                lines.append(f"| {team.name} | N/A | N/A | N/A | N/A | N/A | N/A |")
        lines.append("")

        # Conclusions
        lines.append("---")
        lines.append("## Conclusions & Recommendations")
        lines.append("")
        lines.append("### Key Findings")
        lines.append("")
        if leaderboard:
            winner = next((team_name_map.get(e.team_id, e.team_id) for e in leaderboard if e.rank == 1), "N/A")
            lines.append(f"1. **Champion:** {winner}")
        lines.append(f"2. {len(teams)} teams competed with a total of {len(all_predictions)} predictions across {len(matches)} matches")
        if all_best:
            lines.append(f"3. **Best Model:** {all_best[0][0]} with {all_best[0][1].accuracy:.1f}% accuracy")
        lines.append(f"4. Technical evaluations were {'submitted' if any(te.total_score for te in tech_evals.values()) else 'not completed'}")
        lines.append("")
        lines.append("### Tournament Statistics")
        lines.append("")
        total_correct = 0
        total_preds = 0
        for team in teams:
            team_preds = [p for p in all_predictions if p.team_id == team.id]
            result_map = {r.match_id: r for r in results.values()}
            for pred in team_preds:
                actual = result_map.get(pred.match_id)
                if actual:
                    total_preds += 1
                    if (pred.predicted_winner or "").lower() == (actual.actual_winner or "").lower():
                        total_correct += 1
        if total_preds > 0:
            lines.append(f"- **Overall Prediction Accuracy:** {total_correct/total_preds*100:.1f}% ({total_correct}/{total_preds})")
        lines.append(f"- **Matches with Results:** {len(results)}/{len(matches)}")
        lines.append(f"- **Average Predictions per Team:** {len(all_predictions)/len(teams):.0f}")
        lines.append("")

        report = "\n".join(lines)
        report_path = self.output_dir / "TOURNAMENT_OVERALL_REPORT.md"
        report_path.write_text(report)
        return str(report_path)

    def _compute_mlops_score(self, team: TeamInfo, model_files: list[ModelFile], evaluations: list[ModelEvaluation]) -> dict:
        scores = {}
        # Versioning
        versions = [mf.version for mf in model_files if mf.version]
        scores["Versioning"] = min(10, len(set(versions)) * 2) if versions else 0
        # Reproducibility
        loadable = sum(1 for mf in model_files if mf.loadable)
        scores["Reproducibility"] = min(10, loadable * 2) if model_files else 0
        # Pipeline Design
        scores["Pipeline Design"] = 5 if model_files else 0
        # Feature Engineering
        scores["Feature Engineering"] = 4 if evaluations and any(e.accuracy > 40 for e in evaluations) else 2
        # Model Architecture
        scores["Model Architecture"] = min(10, len(model_files)) if model_files else 0
        # Maintainability
        scores["Maintainability"] = 5 if len(model_files) > 3 else 3
        # Deployment Readiness
        scores["Deployment Readiness"] = 6 if loadable > 0 else 2
        # Documentation
        scores["Documentation"] = 3
        # Code Quality
        scores["Code Quality"] = 5
        # Scalability
        scores["Scalability"] = 5 if len(model_files) > 5 else 3
        # Monitoring Readiness
        scores["Monitoring Readiness"] = 3
        # Artifact Management
        scores["Artifact Management"] = min(10, len(model_files)) if model_files else 0
        return scores


# ═══════════════════════════════════════════════════════════════
#  MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

def main():
    log.info("=" * 60)
    log.info("FIFA World Cup Model Evaluation & Analytics System")
    log.info("=" * 60)

    # 1. Read database
    log.info("Phase 1: Reading database...")
    db = DatabaseReader()
    teams = db.get_teams()
    matches = db.get_matches()
    results = db.get_actual_results()
    all_predictions = db.get_predictions()
    all_scores = db.get_scores()
    leaderboard = db.get_leaderboard()
    tech_evals = db.get_technical_evals()
    pres_evals = db.get_presentation_evals()
    model_submissions = db.get_model_submissions()

    log.info(f"  Teams: {len(teams)}")
    log.info(f"  Matches: {len(matches)}")
    log.info(f"  Actual Results: {len(results)}")
    log.info(f"  Predictions: {len(all_predictions)}")
    log.info(f"  Scores: {len(all_scores)}")
    log.info(f"  Leaderboard entries: {len(leaderboard)}")

    # 2. Discover models
    log.info("Phase 2: Discovering models...")
    discovery = ModelDiscovery(BACKEND_DIR / "uploads")
    all_model_files = discovery.discover_all()
    log.info(f"  Found {len(all_model_files)} model files")

    # Group by team folder
    models_by_folder = defaultdict(list)
    for mf in all_model_files:
        models_by_folder[mf.team_folder].append(mf)

    # 3. Load and evaluate models
    log.info("Phase 3: Loading and evaluating models...")
    all_evaluations = {}
    result_map = {r.match_id: r for r in results.values()}

    for team in teams:
        team_name = team.name.lower().replace(" ", "")
        # Match team to folder
        folder = None
        for f in models_by_folder:
            if f.lower().replace(" ", "") in team_name or team_name in f.lower().replace(" ", ""):
                folder = f
                break
        # Fallback: use team code mapping
        if not folder:
            code_to_folder = {
                "A": "paulneerali", "B": "goalGPT", "C": "soccersence",
                "D": "goaljyolsyan", "E": "bol",
            }
            folder = code_to_folder.get(team.team_id_code)

        model_files = models_by_folder.get(folder, []) if folder else []
        evaluations = []

        log.info(f"  Team: {team.name} ({team.team_id_code}) -> folder: {folder} ({len(model_files)} files)")

        for mf in model_files:
            log.info(f"    Loading {mf.filename}...")
            try:
                model = discovery.load_model(mf)
            except Exception as e:
                log.info(f"      -> {mf.filename}: Failed to load ({str(e)[:80]})")
                continue
            if model and mf.has_predict:
                # Run inference on all matches
                match_preds = []
                for match in matches:
                    actual = result_map.get(match.id)
                    if not actual:
                        continue
                    output = discovery.run_inference(model, mf, match.home_team, match.away_team)
                    if output:
                        predicted = EvaluationEngine.extract_prediction(output)
                        comparison = EvaluationEngine.compare_match_prediction(predicted, actual, match)
                        match_preds.append(comparison)

                if match_preds:
                    ev = EvaluationEngine.evaluate_predictions(match_preds, matches, results)
                    ev.model_file = mf
                    evaluations.append(ev)
                    log.info(f"      -> {mf.filename}: {ev.accuracy:.1f}% accuracy ({ev.correct_winner}/{ev.total_matches})")
                else:
                    log.info(f"      -> {mf.filename}: No matches to evaluate")
            else:
                log.info(f"      -> {mf.filename}: Could not load ({mf.error[:80]})")

        all_evaluations[team.id] = evaluations

    # 4. Generate reports
    log.info("Phase 4: Generating reports...")
    viz_dir = REPORTS_DIR / "visualizations"
    viz = VisualizationGenerator(viz_dir)
    report_gen = ReportGenerator(REPORTS_DIR)

    for team in teams:
        log.info(f"  Generating report for {team.name}...")
        entry = next((e for e in leaderboard if e.team_id == team.id), None)
        tech = tech_evals.get(team.id)
        pres = pres_evals.get(team.id)
        evals = all_evaluations.get(team.id, [])
        team_files = [mf for mf in all_model_files if mf.team_folder.lower().replace(" ", "") in team.name.lower().replace(" ", "")]

        # Fallback matching
        if not team_files:
            code_to_folder = {
                "A": "paulneerali", "B": "goalGPT", "C": "soccersence",
                "D": "goaljyolsyan", "E": "bol",
            }
            folder = code_to_folder.get(team.team_id_code)
            if folder:
                team_files = [mf for mf in all_model_files if mf.team_folder == folder]

        path = report_gen.generate_team_report(
            team=team,
            evaluations=evals,
            db_predictions=all_predictions,
            db_scores=all_scores,
            leaderboard_entry=entry,
            tech_eval=tech,
            pres_eval=pres,
            matches=matches,
            results=results,
            model_files=team_files,
            viz=viz,
        )
        log.info(f"    -> {path}")

    # 5. Tournament report
    log.info("  Generating tournament report...")
    path = report_gen.generate_tournament_report(
        teams=teams,
        leaderboard=leaderboard,
        all_evaluations=all_evaluations,
        all_predictions=all_predictions,
        matches=matches,
        results=results,
        tech_evals=tech_evals,
        pres_evals=pres_evals,
        viz=viz,
    )
    log.info(f"    -> {path}")

    # 6. Summary
    log.info("")
    log.info("=" * 60)
    log.info("REPORTS GENERATED SUCCESSFULLY")
    log.info("=" * 60)
    log.info(f"Output directory: {REPORTS_DIR}")
    log.info(f"Visualizations: {viz_dir}")
    log.info("")
    log.info("Team Reports:")
    for team in teams:
        code = team.team_id_code
        name = team.name.replace(" ", "_")
        log.info(f"  - {code}_{name}_report.md")
    log.info(f"  - TOURNAMENT_OVERALL_REPORT.md")
    log.info("")
    log.info("Visualizations:")
    for f in sorted(viz_dir.glob("*.png")):
        log.info(f"  - {f.name}")


if __name__ == "__main__":
    main()
