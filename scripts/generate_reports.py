#!/usr/bin/env python3
"""
Automated Report Generation Pipeline
======================================
Generates Game Prediction + Presentation Evaluation reports for all teams.
Outputs: Markdown, HTML, PDF per team per report type.

Usage:
    cd /home/opentrends/Desktop/Arsha/Goalgorithm/backend
    python3 scripts/generate_reports.py
"""

import os, sys, json, time, math, base64, subprocess, logging, warnings
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

warnings.filterwarnings("ignore")

# ── Path setup ──────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
TEMPLATE_DIR = BACKEND_DIR / "templates"
OUTPUT_DIR = BACKEND_DIR / "result_reports"

os.environ.setdefault("DATABASE_URL",
    "postgresql://goalgorithm:npg_VAFnHKdGy3O9@ep-solitary-fire-as2no21e-pooler.c-4.eu-central-1.aws.neon.tech/goalgorithm?sslmode=require")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("pipeline")

# ── Reuse existing evaluate_models infrastructure ────────────────
from scripts.evaluate_models import (
    DatabaseReader, ModelDiscovery, EvaluationEngine, ModelEvaluation,
    MatchInfo, ActualResult, Prediction, Score, LeaderboardEntry,
    TeamInfo, TechnicalEval, PresentationEval, ModelFile,
)
from scripts.evaluate_models import VisualizationGenerator
from pathlib import Path as _P

import jinja2
import markdown

# ══════════════════════════════════════════════════════════════════
#  GRADE UTILITIES
# ══════════════════════════════════════════════════════════════════

def compute_grade(score: float, max_score: float = 100) -> str:
    pct = (score / max_score * 100) if max_score else 0
    if pct >= 90: return "A+"
    if pct >= 80: return "A"
    if pct >= 70: return "B+"
    if pct >= 60: return "B"
    if pct >= 50: return "C+"
    if pct >= 40: return "C"
    return "D"

def grade_badge(grade: str) -> str:
    cls = "badge-a" if grade.startswith("A") else "badge-b" if grade.startswith("B") else "badge-c"
    return f'<span class="badge {cls}">{grade}</span>'

def pct_str(val, decimals=1) -> str:
    return f"{val:.{decimals}f}%"

def correct_badge(is_correct: bool) -> str:
    return '<span class="badge badge-correct">YES</span>' if is_correct else '<span class="badge badge-incorrect">NO</span>'

# ══════════════════════════════════════════════════════════════════
#  DATA AGGREGATION
# ══════════════════════════════════════════════════════════════════

@dataclass
class TeamData:
    team: TeamInfo
    members: list[dict]
    model_files: list[ModelFile]
    evaluations: list[ModelEvaluation]
    db_predictions: list[Prediction]
    db_scores: list[Score]
    match_breakdown: list[dict]
    leaderboard: LeaderboardEntry | None
    tech_eval: TechnicalEval | None
    pres_eval: PresentationEval | None
    db_prediction_accuracy: float = 0.0
    db_correct: int = 0
    db_total: int = 0
    best_eval: ModelEvaluation | None = None

def gather_team_data(db: DatabaseReader, discovery: ModelDiscovery,
                     all_model_files: list[ModelFile], all_evaluations: dict,
                     matches: list[MatchInfo], results: dict,
                     all_predictions: list[Prediction], all_scores: list[Score],
                     leaderboard: list[LeaderboardEntry],
                     tech_evals: dict, pres_evals: dict) -> list[TeamData]:
    teams = db.get_teams()
    result_map = {r.match_id: r for r in results.values()}
    code_to_folder = {"A": "paulneerali", "B": "goalGPT", "C": "soccersence",
                      "D": "goaljyolsyan", "E": "bol"}
    team_data_list = []

    for team in teams:
        folder = code_to_folder.get(team.team_id_code, "")
        team_files = [mf for mf in all_model_files if mf.team_folder.lower().replace(" ","") == folder.lower().replace(" ","")]
        team_preds = [p for p in all_predictions if p.team_id == team.id]
        team_scores = [s for s in all_scores if s.team_id == team.id]
        entry = next((e for e in leaderboard if e.team_id == team.id), None)
        tech = tech_evals.get(team.id)
        pres = pres_evals.get(team.id)
        evals = all_evaluations.get(team.id, [])

        # Compute match breakdown from DB predictions
        match_breakdown = []
        correct_count = 0
        for pred in team_preds:
            match = next((m for m in matches if m.id == pred.match_id), None)
            actual = result_map.get(pred.match_id)
            if match and actual:
                pw = (pred.predicted_winner or "").lower()
                aw = (actual.actual_winner or "").lower()
                is_correct = pw == aw
                if is_correct:
                    correct_count += 1
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
                    "confidence": max(pred.home_win_probability or 0, pred.draw_probability or 0, pred.away_win_probability or 0),
                    "correct": is_correct,
                })
        match_breakdown.sort(key=lambda x: x["match_number"])
        db_total = len(team_preds)
        db_accuracy = (correct_count / db_total * 100) if db_total else 0

        best_eval = max(evals, key=lambda e: e.accuracy) if evals else None

        team_data_list.append(TeamData(
            team=team, members=[], model_files=team_files, evaluations=evals,
            db_predictions=team_preds, db_scores=team_scores,
            match_breakdown=match_breakdown, leaderboard=entry,
            tech_eval=tech, pres_eval=pres,
            db_prediction_accuracy=round(db_accuracy, 1),
            db_correct=correct_count, db_total=db_total, best_eval=best_eval,
        ))

    # Fetch members per team
    members_data = db._query("SELECT team_id::text, name, employee_id FROM team_members")
    members_by_team = defaultdict(list)
    for m in members_data:
        members_by_team[str(m["team_id"])].append({"name": m["name"], "employee_id": m["employee_id"]})
    for td in team_data_list:
        td.members = members_by_team.get(td.team.id, [])

    return team_data_list

# ══════════════════════════════════════════════════════════════════
#  MARKDOWN GENERATORS
# ══════════════════════════════════════════════════════════════════

def generate_game_prediction_markdown(td: TeamData, viz_dir: Path) -> str:
    team = td.team
    lines = []
    a = lines.append

    # --- Match Breakdown Table ---
    a("### Match-wise Breakdown")
    a("")
    a("| # | Home | Away | Actual | Predicted | Correct | Confidence | Score |")
    a("|---|------|------|--------|-----------|---------|------------|-------|")
    for m in td.match_breakdown:
        actual_str = f"{m['actual_winner'].upper()} ({m['actual_home_goals']}-{m['actual_away_goals']})"
        pred_str = f"{m['predicted_winner'].upper()} ({m['predicted_home_goals']}-{m['predicted_away_goals']})"
        conf = f"{m['confidence']*100:.1f}%" if m['confidence'] else "N/A"
        cb = correct_badge(m['correct'])
        a(f"| {m['match_number']} | {m['home_team']} | {m['away_team']} | {actual_str} | {pred_str} | {cb} | {conf} | {m.get('score', 'N/A')} |")
    a("")
    a(f"**Total Correct: {td.db_correct}/{td.db_total} ({td.db_prediction_accuracy}%)**")
    a("")

    return "\n".join(lines)


def generate_game_prediction_sections(td: TeamData, all_td: list[TeamData],
                                       viz_dir: Path, viz: VisualizationGenerator) -> list[dict]:
    """Generate all sections for Game Prediction report."""
    team = td.team
    sections = []

    # --- Section 1: Executive Summary ---
    best = td.best_eval
    best_model_name = best.model_file.filename if best and best.model_file else "N/A"
    best_acc = f"{best.accuracy:.1f}%" if best else "N/A"

    # Determine rank among teams by best model accuracy
    team_best_accs = []
    for t in all_td:
        if t.best_eval:
            team_best_accs.append((t.team.name, t.best_eval.accuracy))
    team_best_accs.sort(key=lambda x: x[1], reverse=True)
    team_rank_model = next((i+1 for i, (n, _) in enumerate(team_best_accs) if n == team.name), "N/A")

    grade = compute_grade(td.leaderboard.final_score if td.leaderboard else 0)

    members_html = "".join(f"<li>{m['name']} ({m['employee_id']})</li>" for m in td.members)

    content = f"""
    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-value">{len(td.model_files)}</div><div class="kpi-label">Models Uploaded</div></div>
      <div class="kpi-card"><div class="kpi-value">{td.db_prediction_accuracy}%</div><div class="kpi-label">DB Prediction Accuracy</div></div>
      <div class="kpi-card"><div class="kpi-value">{best_acc}</div><div class="kpi-label">Best Model Accuracy</div></div>
      <div class="kpi-card"><div class="kpi-value">#{td.leaderboard.rank if td.leaderboard else 'N/A'}</div><div class="kpi-label">Tournament Rank</div></div>
      <div class="kpi-card"><div class="kpi-value">{td.leaderboard.final_score if td.leaderboard else 0:.1f}</div><div class="kpi-label">Final Score</div></div>
      <div class="kpi-card"><div class="kpi-value">{grade_badge(grade)}</div><div class="kpi-label">Overall Grade</div></div>
    </div>

    <h3>Team Members</h3>
    <ul>{members_html}</ul>

    <h3>Key Findings</h3>
    <div class="callout callout-info">
      <strong>Best Model:</strong> {best_model_name} with {best_acc} accuracy<br>
      <strong>DB Predictions:</strong> {td.db_correct}/{td.db_total} correct ({td.db_prediction_accuracy}%)<br>
      <strong>Total Model Versions:</strong> {len(td.model_files)} files uploaded<br>
      <strong>Model Ranking:</strong> #{team_rank_model} among all teams by best model accuracy
    </div>
    """
    sections.append({"title": "Executive Summary", "content": content})

    # --- Section 2: Model Summary ---
    model_rows = ""
    for i, mf in enumerate(sorted(td.model_files, key=lambda x: x.filename), 1):
        loadable = "Yes" if mf.loadable else "No"
        mtype = mf.model_type or "Unknown"
        if len(mtype) > 40:
            mtype = mtype.split(".")[-1]
        size_mb = f"{mf.file_size / 1024 / 1024:.1f} MB"
        model_rows += f"<tr><td>{i}</td><td>{mf.filename}</td><td>{size_mb}</td><td>v{mf.version or '?'}</td><td>{loadable}</td><td>{mtype}</td></tr>"

    content = f"""
    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-value">{len(td.model_files)}</div><div class="kpi-label">Total Files</div></div>
      <div class="kpi-card"><div class="kpi-value">{sum(1 for m in td.model_files if m.loadable)}</div><div class="kpi-label">Loadable Models</div></div>
      <div class="kpi-card"><div class="kpi-value">{sum(m.file_size for m in td.model_files)/1024/1024:.1f} MB</div><div class="kpi-label">Total Size</div></div>
    </div>
    <table>
      <thead><tr><th>#</th><th>Filename</th><th>Size</th><th>Version</th><th>Loadable</th><th>Type</th></tr></thead>
      <tbody>{model_rows}</tbody>
    </table>
    """
    sections.append({"title": "Model Summary", "content": content})

    # --- Section 3: Match Breakdown ---
    match_rows = ""
    for m in td.match_breakdown:
        actual_str = f"{m['actual_winner'].upper()} ({m['actual_home_goals']}-{m['actual_away_goals']})"
        pred_str = f"{m['predicted_winner'].upper()} ({m['predicted_home_goals']}-{m['predicted_away_goals']})"
        conf = f"{m['confidence']*100:.1f}%" if m['confidence'] else "N/A"
        cb = correct_badge(m['correct'])
        match_rows += f'<tr class="page-break"><td>{m["match_number"]}</td><td>{m["home_team"]}</td><td>{m["away_team"]}</td><td>{actual_str}</td><td>{pred_str}</td><td>{cb}</td><td>{conf}</td></tr>'

    content = f"""
    <p><strong>Total Correct:</strong> {td.db_correct}/{td.db_total} ({td.db_prediction_accuracy}%)</p>
    <table>
      <thead><tr><th>#</th><th>Home</th><th>Away</th><th>Actual</th><th>Predicted</th><th>Correct</th><th>Confidence</th></tr></thead>
      <tbody>{match_rows}</tbody>
    </table>
    """
    sections.append({"title": "Match-wise Breakdown (32 Matches)", "content": content})

    # --- Section 4: Match Analytics (charts) ---
    charts_html = ""
    chart_files = {
        "Accuracy Timeline": f"{td.team.team_id_code}_accuracy_timeline.png",
        "Correct vs Incorrect": f"{td.team.team_id_code}_correct_incorrect.png",
        "Win/Draw/Loss Distribution": f"{td.team.team_id_code}_win_draw_loss.png",
        "Confidence Distribution": f"{td.team.team_id_code}_confidence.png",
        "Score Distribution": f"{td.team.team_id_code}_score_distribution.png",
        "Confusion Matrix": f"{td.team.team_id_code}_confusion_matrix.png",
    }
    for title, fname in chart_files.items():
        fpath = viz_dir / fname
        if fpath.exists():
            b64 = encode_image_base64(fpath)
            charts_html += f'<div class="chart-container"><img src="data:image/png;base64,{b64}" alt="{title}"><div class="chart-caption">{title}</div></div>'

    if not charts_html:
        charts_html = "<p>Charts will be available after running the evaluation pipeline.</p>"
    sections.append({"title": "Match Analytics", "content": charts_html})

    # --- Section 5: Model Performance Analysis ---
    if td.evaluations:
        eval_rows = ""
        sorted_evals = sorted(td.evaluations, key=lambda e: e.accuracy, reverse=True)
        for i, ev in enumerate(sorted_evals, 1):
            fname = ev.model_file.filename if ev.model_file else "N/A"
            correct_str = f"{ev.correct_winner}/{ev.total_matches}"
            eval_rows += f"""<tr>
              <td>{i}</td><td>{fname}</td><td>{ev.accuracy:.1f}%</td>
              <td>{ev.precision:.1f}%</td><td>{ev.recall:.1f}%</td><td>{ev.f1_score:.1f}%</td>
              <td>{correct_str}</td><td>{ev.avg_confidence:.1f}%</td>
            </tr>"""
        content = f"""
        <table>
          <thead><tr><th>#</th><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>Correct</th><th>Avg Confidence</th></tr></thead>
          <tbody>{eval_rows}</tbody>
        </table>
        """
        # Add chart
        chart_path = viz_dir / f"{td.team.team_id_code}_accuracy_comparison.png"
        if chart_path.exists():
            b64 = encode_image_base64(chart_path)
            content += f'<div class="chart-container"><img src="data:image/png;base64,{b64}" alt="Model Accuracy Comparison"><div class="chart-caption">Model Accuracy Comparison</div></div>'
        chart_path2 = viz_dir / f"{td.team.team_id_code}_model_radar.png"
        if chart_path2.exists():
            b64 = encode_image_base64(chart_path2)
            content += f'<div class="chart-container"><img src="data:image/png;base64,{b64}" alt="Model Radar Chart"><div class="chart-caption">Model Performance Radar</div></div>'
    else:
        content = "<p>No model evaluations available.</p>"
    sections.append({"title": "Model Performance Analysis", "content": content})

    # --- Section 6: Best Model Analysis ---
    if best:
        mlops = _compute_mlops(td)
        content = f"""
        <div class="callout callout-success">
          <strong>Best Model:</strong> {best.model_file.filename if best.model_file else 'N/A'}<br>
          <strong>Accuracy:</strong> {best.accuracy:.1f}% &nbsp;|&nbsp;
          <strong>Precision:</strong> {best.precision:.1f}% &nbsp;|&nbsp;
          <strong>Recall:</strong> {best.recall:.1f}% &nbsp;|&nbsp;
          <strong>F1:</strong> {best.f1_score:.1f}%<br>
          <strong>Correct Winner:</strong> {best.correct_winner}/{best.total_matches} &nbsp;|&nbsp;
          <strong>Exact Score:</strong> {best.correct_score}/{best.total_matches}<br>
          <strong>Goal Diff Correct:</strong> {best.correct_goal_diff}/{best.total_matches}<br>
          <strong>Log Loss:</strong> {best.log_loss:.4f} &nbsp;|&nbsp;
          <strong>Brier Score:</strong> {best.brier_score:.4f}<br>
          <strong>Avg Confidence:</strong> {best.avg_confidence:.1f}%
        </div>

        <h3>MLOps Evaluation</h3>
        <table>
          <thead><tr><th>Criterion</th><th>Score (0-10)</th></tr></thead>
          <tbody>
          {''.join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k, v in mlops.items())}
          <tr style="font-weight:bold;border-top:2px solid #1a365d"><td>Overall MLOps Score</td><td>{sum(mlops.values())/len(mlops):.1f}/10</td></tr>
          </tbody>
        </table>
        """
    else:
        content = "<p>No best model evaluation available.</p>"
    sections.append({"title": "Best Model Analysis & MLOps", "content": content})

    # --- Section 7: Team Performance ---
    pres_grade = ""
    if td.pres_eval:
        pres_grade = grade_badge(td.pres_eval.grade or "N/A")

    content = f"""
    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-value">{td.db_prediction_accuracy}%</div><div class="kpi-label">DB Accuracy</div></div>
      <div class="kpi-card"><div class="kpi-value">#{td.leaderboard.rank if td.leaderboard else 'N/A'}</div><div class="kpi-label">Rank</div></div>
      <div class="kpi-card"><div class="kpi-value">{td.leaderboard.phase1_score if td.leaderboard else 0:.1f}/60</div><div class="kpi-label">Phase 1</div></div>
      <div class="kpi-card"><div class="kpi-value">{td.leaderboard.technical_score if td.leaderboard else 0:.1f}/20</div><div class="kpi-label">Technical</div></div>
      <div class="kpi-card"><div class="kpi-value">{td.leaderboard.presentation_score if td.leaderboard else 0:.1f}/20</div><div class="kpi-label">Presentation</div></div>
      <div class="kpi-card"><div class="kpi-value">{td.leaderboard.final_score if td.leaderboard else 0:.1f}/100</div><div class="kpi-label">Final Score</div></div>
    </div>
    """
    sections.append({"title": "Team Performance Overview", "content": content})

    # --- Section 8: Conclusions ---
    accuracy_ranking = sorted(all_td, key=lambda t: t.db_prediction_accuracy, reverse=True)
    team_acc_rank = next((i+1 for i, t in enumerate(accuracy_ranking) if t.team.id == team.id), "N/A")

    content = f"""
    <div class="callout callout-info">
      <h4>Key Findings</h4>
      <ol>
        <li>The team uploaded <strong>{len(td.model_files)}</strong> model versions during the competition.</li>
        <li>DB prediction accuracy of <strong>{td.db_prediction_accuracy}%</strong> ({td.db_correct}/{td.db_total}).</li>
        <li>Best automated model: <strong>{best.model_file.filename if best and best.model_file else 'N/A'}</strong> with {best.accuracy:.1f}% accuracy.</li>
        <li>Tournament rank: <strong>#{td.leaderboard.rank if td.leaderboard else 'N/A'}</strong> with final score {td.leaderboard.final_score if td.leaderboard else 0:.1f}.</li>
      </ol>
    </div>
    <div class="callout callout-warning">
      <h4>Recommendations</h4>
      <ol>
        <li>Focus on draw prediction accuracy - the hardest outcome to predict.</li>
        <li>Improve probability calibration for better confidence scores.</li>
        <li>Consider ensemble methods combining multiple model versions.</li>
        <li>Add feature engineering for team-specific statistics.</li>
      </ol>
    </div>
    """
    sections.append({"title": "Conclusions & Recommendations", "content": content})

    return sections


def generate_presentation_sections(td: TeamData, all_td: list[TeamData]) -> list[dict]:
    """Generate all sections for Presentation Evaluation report."""
    team = td.team
    sections = []
    pres = td.pres_eval
    tech = td.tech_eval

    # --- Section 1: Executive Summary ---
    pres_score = td.leaderboard.presentation_score if td.leaderboard else (pres.presentation_score if pres else None)
    pres_grade = pres.grade if pres else "N/A"
    pres_rank = pres.rank if pres else "N/A"
    judge_count = pres.judge_count if pres else 0

    score_display = f"{pres_score:.2f}" if pres_score is not None else "N/A"
    final_score = f"{td.leaderboard.final_score:.2f}" if td.leaderboard and td.leaderboard.final_score else "N/A"

    content = f"""
    <div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-value">{score_display}</div><div class="kpi-label">Presentation Score</div></div>
      <div class="kpi-card"><div class="kpi-value">#{pres_rank}</div><div class="kpi-label">Overall Rank</div></div>
      <div class="kpi-card"><div class="kpi-value">{grade_badge(pres_grade)}</div><div class="kpi-label">Overall Grade</div></div>
      <div class="kpi-card"><div class="kpi-value">{judge_count}</div><div class="kpi-label">Judges</div></div>
      <div class="kpi-card"><div class="kpi-value">{final_score}</div><div class="kpi-label">Final Score</div></div>
    </div>
    """
    sections.append({"title": "Executive Summary", "content": content})

    # --- Section 2: Judges Evaluation ---
    categories = ["Problem Understanding", "Feature Engineering", "Team Work", "Presentation Quality", "Q&A"]
    max_vals = [10, 15, 10, 10, 5]
    
    averages = {}
    from collections import defaultdict
    if pres and pres.judge_scores:
        totals = defaultdict(float)
        counts = defaultdict(int)
        for js in pres.judge_scores:
            scores = js.get("scores", {}) if isinstance(js, dict) else {}
            for name, val in scores.items():
                totals[name] += float(val)
                counts[name] += 1
        for cat in categories:
            if counts[cat] > 0:
                averages[cat] = totals[cat] / counts[cat]
            else:
                averages[cat] = 0.0
    else:
        averages = {
            "AI Explanation": pres.ai_explanation_score or 0.0 if pres else 0.0,
            "Q&A": pres.qa_score or 0.0 if pres else 0.0,
            "Delivery": pres.delivery_score or 0.0 if pres else 0.0
        }

    kpi_cards = ""
    for name, avg in averages.items():
        kpi_cards += f'<div class="kpi-card"><div class="kpi-value">{avg:.1f}</div><div class="kpi-label">{name}</div></div>'
    kpi_cards += f'<div class="kpi-card"><div class="kpi-value">{pres.raw_total if pres and pres.raw_total is not None else "N/A"}</div><div class="kpi-label">Raw Total</div></div>'
    kpi_cards += f'<div class="kpi-card"><div class="kpi-value">{judge_count}</div><div class="kpi-label">Number of Judges</div></div>'

    content = f'<div class="kpi-grid">{kpi_cards}</div>'
    sections.append({"title": "Judges Evaluation", "content": content})

    # --- Section 3: Evaluation Criteria ---
    table_rows = ""
    if pres and pres.judge_scores:
        for cat, max_v in zip(categories, max_vals):
            avg = averages.get(cat, 0.0)
            table_rows += f"<tr><td>{cat}</td><td>{avg:.1f}</td><td>{max_v}</td></tr>"
    else:
        table_rows += f"<tr><td>AI Explanation</td><td>{pres.ai_explanation_score if pres and pres.ai_explanation_score is not None else 'N/A'}</td><td>20</td></tr>"
        table_rows += f"<tr><td>Q&A Handling</td><td>{pres.qa_score if pres and pres.qa_score is not None else 'N/A'}</td><td>15</td></tr>"
        table_rows += f"<tr><td>Delivery</td><td>{pres.delivery_score if pres and pres.delivery_score is not None else 'N/A'}</td><td>15</td></tr>"

    content = f"""
    <table>
      <thead><tr><th>Category</th><th>Score</th><th>Max</th></tr></thead>
      <tbody>{table_rows}</tbody>
    </table>
    """
    sections.append({"title": "Evaluation Criteria", "content": content})

    # --- Section 4: Score Breakdown ---
    mult_display = f"x{pres.multiplier}" if pres and pres.multiplier is not None else "N/A"
    content = f"""
    <h3>Presentation Score Analysis</h3>
    <div class="callout callout-info">
      <strong>Presentation Score:</strong> {score_display}<br>
      <strong>Grade:</strong> {grade_badge(pres_grade)}<br>
      <strong>Raw Total:</strong> {pres.raw_total if pres and pres.raw_total is not None else 'N/A'}<br>
      <strong>Multiplier:</strong> {mult_display}
    </div>

    <h3>Technical Evaluation</h3>
    <table>
      <thead><tr><th>Category</th><th>Score</th></tr></thead>
      <tbody>
        <tr><td>Code Quality</td><td>{tech.code_quality if tech else 'N/A'}</td></tr>
        <tr><td>Backend Quality</td><td>{tech.backend_quality if tech else 'N/A'}</td></tr>
        <tr><td>Teamwork</td><td>{tech.teamwork if tech else 'N/A'}</td></tr>
        <tr><td>AI Explanation</td><td>{tech.ai_explanation if tech else 'N/A'}</td></tr>
        <tr style="font-weight:bold"><td>Total Technical</td><td>{tech.total_score if tech else 'N/A'}</td></tr>
      </tbody>
    </table>
    """
    sections.append({"title": "Score Breakdown", "content": content})

    # --- Section 5: Visualizations (placeholder - charts generated separately) ---
    sections.append({"title": "Visualizations", "content": "<p>Charts are embedded in the rendered HTML report.</p>"})

    # --- Section 6: Overall Ranking ---
    ranking_rows = ""
    sorted_teams = sorted(all_td, key=lambda t: t.leaderboard.presentation_score if t.leaderboard and t.leaderboard.presentation_score is not None else 0, reverse=True)
    for i, t in enumerate(sorted_teams, 1):
        p = t.pres_eval
        pg = grade_badge(p.grade if p else "N/A")
        is_self = "font-weight:bold;background:#ebf8ff;" if t.team.id == team.id else ""
        ps = f"{t.leaderboard.presentation_score:.2f}" if t.leaderboard and t.leaderboard.presentation_score is not None else "N/A"
        ranking_rows += f"""<tr style="{is_self}">
          <td>#{i}</td><td>{t.team.name}</td><td>{ps}</td>
          <td>{pg}</td><td>{p.rank if p else 'N/A'}</td>
        </tr>"""

    content = f"""
    <table>
      <thead><tr><th>Rank</th><th>Team</th><th>Score</th><th>Grade</th><th>Rank #</th></tr></thead>
      <tbody>{ranking_rows}</tbody>
    </table>
    """
    sections.append({"title": "Overall Presentation Ranking", "content": content})

    # --- Section 7: Final Evaluation ---
    strengths = []
    weaknesses = []
    if pres and pres.judge_scores:
        max_marks_map = {
            "Problem Understanding": 10,
            "Feature Engineering": 15,
            "Team Work": 10,
            "Presentation Quality": 10,
            "Q&A": 5
        }
        for cat in categories:
            avg = averages.get(cat, 0.0)
            max_v = max_marks_map.get(cat, 10)
            pct = (avg / max_v * 100) if max_v else 0
            if pct >= 80:
                strengths.append(f"Excellent performance in {cat} ({pct:.1f}%)")
            elif pct < 70:
                weaknesses.append(f"Improvement needed in {cat} ({pct:.1f}%)")
    else:
        if pres:
            ps = pres.presentation_score or 0
            aes = pres.ai_explanation_score or 0
            ds = pres.delivery_score or 0
            qs = pres.qa_score or 0
            if ps >= 35:
                strengths.append("Strong presentation score above team average")
            if aes >= 15:
                strengths.append("Good AI explanation capability")
            if ds >= 12:
                strengths.append("Effective delivery and communication")
            if qs < 10:
                weaknesses.append("Q&A handling needs improvement")
            if ds < 10:
                weaknesses.append("Presentation delivery could be stronger")

    score_display_final = f"{pres_score:.2f}" if pres_score is not None else "N/A"
    content = f"""
    <div class="callout callout-success">
      <h4>Strengths</h4>
      <ul>{''.join(f'<li>{s}</li>' for s in strengths) if strengths else '<li>Data pending analysis</li>'}</ul>
    </div>
    <div class="callout callout-warning">
      <h4>Areas for Improvement</h4>
      <ul>{''.join(f'<li>{w}</li>' for w in weaknesses) if weaknesses else '<li>Continue maintaining quality</li>'}</ul>
    </div>
    <div class="callout callout-info">
      <h4>Final Verdict</h4>
      <p>Team <strong>{team.name}</strong> achieved a presentation grade of <strong>{grade_badge(pres_grade)}</strong> with a score of <strong>{score_display_final}</strong>, ranking <strong>#{pres_rank}</strong> among all teams.</p>
    </div>
    """
    sections.append({"title": "Final Evaluation", "content": content})

    return sections


def _compute_mlops(td: TeamData) -> dict:
    n_models = len(td.model_files)
    n_loadable = sum(1 for m in td.model_files if m.loadable)
    versions = [m.version for m in td.model_files if m.version]
    n_versions = len(set(versions))
    avg_size = sum(m.file_size for m in td.model_files) / max(len(td.model_files), 1) / 1024 / 1024
    return {
        "Versioning": min(10, n_versions),
        "Reproducibility": 10.0 if n_loadable == n_models else round(n_loadable / max(n_models, 1) * 10, 1),
        "Pipeline Design": 5.0 if n_models > 5 else 3.0,
        "Feature Engineering": min(10, n_models),
        "Model Architecture": 10.0 if n_loadable > 0 else 0.0,
        "Maintainability": 5.0 if n_models > 3 else 3.0,
        "Deployment Readiness": 6.0 if n_loadable > 5 else 4.0,
        "Documentation": 3.0,
        "Code Quality": 5.0,
        "Scalability": 5.0,
        "Monitoring Readiness": 3.0,
        "Artifact Management": min(10, n_versions),
    }


# ══════════════════════════════════════════════════════════════════
#  IMAGE UTILITIES
# ══════════════════════════════════════════════════════════════════

def encode_image_base64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ══════════════════════════════════════════════════════════════════
#  HTML RENDERING
# ══════════════════════════════════════════════════════════════════

def render_html(template_name: str, context: dict) -> str:
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)))
    tmpl = env.get_template(template_name)
    return tmpl.render(**context)


# ══════════════════════════════════════════════════════════════════
#  PDF GENERATION
# ══════════════════════════════════════════════════════════════════

def html_to_pdf(html_path: Path, pdf_path: Path) -> bool:
    chrome = "/usr/bin/google-chrome"
    if not Path(chrome).exists():
        log.warning("  Chrome not found, skipping PDF generation")
        return False
    try:
        result = subprocess.run([
            chrome,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-software-rasterizer",
            f"--print-to-pdf={pdf_path}",
            "--no-pdf-header-footer",
            f"file://{html_path.resolve()}",
        ], capture_output=True, timeout=60, text=True)
        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            return True
        log.warning(f"  PDF generation issue: {result.stderr[:200] if result.stderr else 'empty output'}")
        return False
    except Exception as e:
        log.warning(f"  PDF generation failed: {e}")
        return False


# ══════════════════════════════════════════════════════════════════
#  PRESENTATION CHARTS
# ══════════════════════════════════════════════════════════════════

def generate_presentation_charts(td: TeamData, all_td: list[TeamData], output_dir: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from collections import defaultdict

    code = td.team.team_id_code
    pres = td.pres_eval

    # Get categories, average scores, and max scores dynamically
    categories = ["Problem Understanding", "Feature Engineering", "Team Work", "Presentation Quality", "Q&A"]
    max_vals = [10, 15, 10, 10, 5]
    
    # Calculate average scores for current team
    values = [0.0] * len(categories)
    if pres and pres.judge_scores:
        totals = defaultdict(float)
        counts = defaultdict(int)
        for js in pres.judge_scores:
            scores = js.get("scores", {}) if isinstance(js, dict) else {}
            for name, val in scores.items():
                totals[name] += float(val)
                counts[name] += 1
        for idx, cat in enumerate(categories):
            if counts[cat] > 0:
                values[idx] = totals[cat] / counts[cat]
    else:
        values = [pres.ai_explanation_score or 0, pres.qa_score or 0, pres.delivery_score or 0] if pres else [0, 0, 0]
        categories = ["AI Explanation", "Q&A", "Delivery"]
        max_vals = [20, 15, 15]

    norm_vals = [v / m * 100 if m else 0 for v, m in zip(values, max_vals)]

    # 1. Radar chart of criteria
    if any(v > 0 for v in norm_vals):
        fig, ax = plt.subplots(figsize=(8, 6), subplot_kw=dict(polar=True))
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]
        norm_vals_plot = norm_vals + norm_vals[:1]
        ax.plot(angles, norm_vals_plot, "o-", linewidth=2, color="#3182ce")
        ax.fill(angles, norm_vals_plot, alpha=0.25, color="#3182ce")
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=9)
        ax.set_ylim(0, 100)
        ax.set_title(f"{td.team.name} - Presentation Criteria", fontsize=14, fontweight="bold", pad=20)
        plt.tight_layout()
        plt.savefig(output_dir / f"{code}_pres_radar.png", dpi=150, bbox_inches="tight")
        plt.close()

    # 2. Judge score comparison (bar chart)
    if any(s > 0 for s in values):
        fig, ax = plt.subplots(figsize=(8, 5))
        colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(values)))
        ax.bar(categories, values, color=colors, edgecolor="#2d3748", linewidth=0.5)
        ax.set_ylabel("Score", fontsize=11)
        ax.set_title(f"{td.team.name} - Score Breakdown", fontsize=14, fontweight="bold")
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, rotation=15, ha="right", fontsize=9)
        for i, v in enumerate(values):
            ax.text(i, (v or 0) + 0.1, f"{v:.1f}", ha="center", fontweight="bold", fontsize=9)
        plt.tight_layout()
        plt.savefig(output_dir / f"{code}_pres_judges.png", dpi=150, bbox_inches="tight")
        plt.close()

    # 3. Team ranking comparison (based on leaderboard.presentation_score)
    fig, ax = plt.subplots(figsize=(10, 5))
    team_names = [t.team.name for t in all_td]
    team_scores = [t.leaderboard.presentation_score if t.leaderboard and t.leaderboard.presentation_score is not None else 0 for t in all_td]
    sorted_pairs = sorted(zip(team_scores, team_names), reverse=True)
    team_scores_s = [p[0] for p in sorted_pairs]
    team_names_s = [p[1] for p in sorted_pairs]
    colors = ["#38a169" if n == td.team.name else "#3182ce" for n in team_names_s]
    bars = ax.barh(team_names_s, team_scores_s, color=colors, edgecolor="#2d3748", linewidth=0.5)
    ax.set_xlabel("Presentation Score", fontsize=11)
    ax.set_title("Presentation Score Ranking (Combined)", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    for bar, score in zip(bars, team_scores_s):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2, f"{score:.2f}", va="center", fontsize=10)
    plt.tight_layout()
    plt.savefig(output_dir / f"{code}_pres_ranking.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 4. Score heatmap (latest round)
    fig, ax = plt.subplots(figsize=(10, 4))
    data = []
    for t in all_td:
        t_pres = t.pres_eval
        t_values = [0.0] * len(categories)
        if t_pres and t_pres.judge_scores:
            t_totals = defaultdict(float)
            t_counts = defaultdict(int)
            for js in t_pres.judge_scores:
                scores = js.get("scores", {}) if isinstance(js, dict) else {}
                for name, val in scores.items():
                    t_totals[name] += float(val)
                    t_counts[name] += 1
            for idx, cat in enumerate(categories):
                if t_counts[cat] > 0:
                    t_values[idx] = t_totals[cat] / t_counts[cat]
        data.append(t_values)
    
    data_arr = np.array(data, dtype=float)
    im = ax.imshow(data_arr, cmap="RdYlGn", aspect="auto", vmin=0, vmax=15)
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, rotation=15, ha="right", fontsize=9)
    ax.set_yticks(range(len(all_td)))
    ax.set_yticklabels([t.team.name for t in all_td], fontsize=10)
    for i in range(len(all_td)):
        for j in range(len(categories)):
            ax.text(j, i, f"{data_arr[i,j]:.1f}", ha="center", va="center", fontsize=10, fontweight="bold")
    plt.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title("Presentation Score Heatmap (Latest Round)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_dir / f"{code}_pres_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()


# ══════════════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════

TEAM_MAP = {
    "A": {"folder": "paulneerali", "dir": "Team_1"},
    "B": {"folder": "goalGPT",     "dir": "Team_2"},
    "C": {"folder": "soccersence", "dir": "Team_3"},
    "D": {"folder": "goaljyolsyan","dir": "Team_4"},
    "E": {"folder": "bol",         "dir": "Team_5"},
}

def main():
    start_time = time.time()
    log.info("=" * 70)
    log.info("  AUTOMATED REPORT GENERATION PIPELINE")
    log.info("=" * 70)

    # 1. Read database
    log.info("Phase 1: Reading database...")
    db = DatabaseReader()
    matches = db.get_matches()
    results = db.get_actual_results()
    all_predictions = db.get_predictions()
    all_scores = db.get_scores()
    leaderboard = db.get_leaderboard()
    tech_evals = db.get_technical_evals()
    pres_evals = db.get_presentation_evals()
    log.info(f"  {len(matches)} matches, {len(all_predictions)} predictions, {len(leaderboard)} leaderboard entries")

    # 2. Discover and evaluate models
    log.info("Phase 2: Loading and evaluating models...")
    discovery = ModelDiscovery(BACKEND_DIR / "uploads")
    all_model_files = discovery.discover_all()
    log.info(f"  Found {len(all_model_files)} model files")

    # Group by team folder
    models_by_folder = defaultdict(list)
    for mf in all_model_files:
        models_by_folder[mf.team_folder].append(mf)

    # Evaluate all models
    all_evaluations = {}
    result_map = {r.match_id: r for r in results.values()}
    teams = db.get_teams()

    for team in teams:
        code_map = TEAM_MAP.get(team.team_id_code, {})
        folder = code_map.get("folder", "")
        model_files = models_by_folder.get(folder, [])
        evaluations = []

        for mf in model_files:
            try:
                model = discovery.load_model(mf)
            except:
                continue
            if model and mf.has_predict:
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

        all_evaluations[team.id] = evaluations
        best = max(evaluations, key=lambda e: e.accuracy) if evaluations else None
        best_acc = f"{best.accuracy:.1f}%" if best else "N/A"
        log.info(f"  {team.name}: {len(evaluations)} models evaluated, best={best_acc}")

    # 3. Gather team data
    log.info("Phase 3: Aggregating team data...")
    all_td = gather_team_data(db, discovery, all_model_files, all_evaluations,
                              matches, results, all_predictions, all_scores,
                              leaderboard, tech_evals, pres_evals)

    # 4. Create output directories
    log.info("Phase 4: Setting up output directories...")
    for tm in TEAM_MAP.values():
        (OUTPUT_DIR / tm["dir"] / "game_prediction").mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / tm["dir"] / "presentation_evaluation").mkdir(parents=True, exist_ok=True)

    viz_dir = BACKEND_DIR / "reports" / "visualizations"
    viz = VisualizationGenerator(viz_dir)

    # 5. Generate reports for each team
    log.info("Phase 5: Generating reports...")
    report_date = datetime.now().strftime("%B %d, %Y")

    for td in all_td:
        code = td.team.team_id_code
        tm = TEAM_MAP.get(code, {})
        team_dir_name = tm.get("dir", f"Team_{code}")
        team_output = OUTPUT_DIR / team_dir_name

        log.info(f"  --- {td.team.name} ({code}) ---")

        # Ensure viz exist for this team
        log.info(f"    Generating visualizations...")
        if td.evaluations:
            # Team-level charts
            td_best = td.best_eval
            if td_best:
                try:
                    viz.correct_incorrect_pie(td.team.name, td.db_correct, td.db_total - td.db_correct, f"{code}_correct_incorrect.png")
                except: pass
                try:
                    viz.match_accuracy_timeline(td.team.name, td.match_breakdown, f"{code}_accuracy_timeline.png")
                except: pass
                try:
                    viz.win_draw_loss_distribution(td.team.name, td.match_breakdown, f"{code}_win_draw_loss.png")
                except: pass
                try:
                    viz.confidence_distribution(td.team.name, td.match_breakdown, f"{code}_confidence.png")
                except: pass
                try:
                    viz.score_distribution(td.team.name, td.match_breakdown, f"{code}_score_distribution.png")
                except: pass
                try:
                    viz.accuracy_bar_chart(td.team.name, td.evaluations, f"{code}_accuracy_comparison.png")
                except: pass
                try:
                    viz.confusion_matrix_heatmap(td.team.name, td_best.confusion_matrix, f"{code}_confusion_matrix.png")
                except: pass
                try:
                    viz.radar_chart(td.team.name, {
                        "Accuracy": td_best.accuracy / 100,
                        "Precision": td_best.precision / 100,
                        "Recall": td_best.recall / 100,
                        "F1 Score": td_best.f1_score / 100,
                        "Win Accuracy": td_best.win_accuracy / 100,
                        "Goal Accuracy": td_best.goal_accuracy / 100,
                    }, f"{code}_radar_best.png")
                except: pass
                if len(td.evaluations) > 1:
                    try:
                        viz.model_comparison_radar(td.team.name, td.evaluations, f"{code}_model_radar.png")
                    except: pass

        # Presentation charts
        log.info(f"    Generating presentation charts...")
        try:
            generate_presentation_charts(td, all_td, viz_dir)
        except Exception as e:
            log.warning(f"    Presentation chart error: {e}")

        # ── Game Prediction Report ──
        log.info(f"    Generating Game Prediction Report...")
        sections = generate_game_prediction_sections(td, all_td, viz_dir, viz)
        markdown_content = f"# {td.team.name} - Game Prediction Analytics Report\n\n"
        markdown_content += f"**Date:** {report_date} | **Team Code:** {code} | **Rank:** #{td.leaderboard.rank if td.leaderboard else 'N/A'}\n\n---\n\n"
        for i, s in enumerate(sections, 1):
            markdown_content += f"## {i}. {s['title']}\n\n"
            # Strip HTML for pure markdown
            md_content = s['content']
            markdown_content += md_content + "\n\n---\n\n"

        gp_dir = team_output / "game_prediction"
        (gp_dir / "report.md").write_text(markdown_content, encoding="utf-8")

        html_content = render_html("report_template.html", {
            "title": f"{td.team.name} - Game Prediction Analytics Report",
            "team_name": td.team.name,
            "team_code": code,
            "report_subtitle": "Game Prediction Analytics Report",
            "report_date": report_date,
            "rank": td.leaderboard.rank if td.leaderboard else "N/A",
            "cover_icon": "⚽",
            "tournament_name": "FIFA World Cup AI Prediction Tournament 2026",
            "sections": sections,
        })
        html_path = gp_dir / "report.html"
        html_path.write_text(html_content, encoding="utf-8")

        pdf_path = gp_dir / "report.pdf"
        log.info(f"    Generating PDF for Game Prediction...")
        html_to_pdf(html_path, pdf_path)

        # ── Presentation Evaluation Report ──
        log.info(f"    Generating Presentation Evaluation Report...")
        pres_sections = generate_presentation_sections(td, all_td)

        # Add presentation charts to sections
        pres_chart_html = ""
        for chart_name in ["pres_radar", "pres_judges", "pres_ranking", "pres_heatmap"]:
            chart_path = viz_dir / f"{code}_{chart_name}.png"
            if chart_path.exists():
                b64 = encode_image_base64(chart_path)
                pres_chart_html += f'<div class="chart-container"><img src="data:image/png;base64,{b64}" alt="{chart_name}"><div class="chart-caption">{chart_name.replace("_", " ").title()}</div></div>'
        if pres_chart_html:
            # Replace the visualizations section
            for s in pres_sections:
                if s["title"] == "Visualizations":
                    s["content"] = pres_chart_html
                    break

        pres_markdown = f"# {td.team.name} - Presentation Evaluation Report\n\n"
        pres_markdown += f"**Date:** {report_date} | **Team Code:** {code}\n\n---\n\n"
        for i, s in enumerate(pres_sections, 1):
            pres_markdown += f"## {i}. {s['title']}\n\n{s['content']}\n\n---\n\n"

        pe_dir = team_output / "presentation_evaluation"
        (pe_dir / "report.md").write_text(pres_markdown, encoding="utf-8")

        pres_html = render_html("report_template.html", {
            "title": f"{td.team.name} - Presentation Evaluation Report",
            "team_name": td.team.name,
            "team_code": code,
            "report_subtitle": "Presentation Evaluation Report",
            "report_date": report_date,
            "rank": td.leaderboard.rank if td.leaderboard else "N/A",
            "cover_icon": "🎯",
            "tournament_name": "FIFA World Cup AI Prediction Tournament 2026",
            "sections": pres_sections,
        })
        pres_html_path = pe_dir / "report.html"
        pres_html_path.write_text(pres_html, encoding="utf-8")

        pres_pdf_path = pe_dir / "report.pdf"
        log.info(f"    Generating PDF for Presentation Evaluation...")
        html_to_pdf(pres_html_path, pres_pdf_path)

    # 6. Summary
    elapsed = time.time() - start_time
    log.info("")
    log.info("=" * 70)
    log.info("  ALL REPORTS GENERATED SUCCESSFULLY")
    log.info("=" * 70)
    log.info(f"  Output directory: {OUTPUT_DIR}")
    log.info(f"  Time elapsed: {elapsed:.1f}s")
    log.info("")

    for td in all_td:
        code = td.team.team_id_code
        tm = TEAM_MAP.get(code, {})
        team_dir = OUTPUT_DIR / tm.get("dir", "")
        gp = team_dir / "game_prediction"
        pe = team_dir / "presentation_evaluation"
        log.info(f"  {td.team.name}:")
        log.info(f"    Game Prediction:     MD={_fsize(gp/'report.md')}  HTML={_fsize(gp/'report.html')}  PDF={_fsize(gp/'report.pdf')}")
        log.info(f"    Presentation Eval:   MD={_fsize(pe/'report.md')}  HTML={_fsize(pe/'report.html')}  PDF={_fsize(pe/'report.pdf')}")


def _fsize(p: Path) -> str:
    if p.exists():
        s = p.stat().st_size
        if s > 1024*1024: return f"{s/1024/1024:.1f}MB"
        if s > 1024: return f"{s/1024:.0f}KB"
        return f"{s}B"
    return "MISSING"


if __name__ == "__main__":
    main()
