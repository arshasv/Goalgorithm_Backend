#!/usr/bin/env python3
"""
Consolidated Game Prediction Evaluation Report Generator
=========================================================
Generates a single PDF comparing all teams' game prediction performance
across the FIFA World Cup AI Prediction Tournament 2026.

Usage:
    cd /home/opentrends/Desktop/Arsha/Goalgorithm/backend
    python3 scripts/generate_consolidated_prediction_report.py
"""

import os
import sys
import logging
import warnings
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
OUTPUT_DIR = BACKEND_DIR / "result_reports"
CHART_DIR = BACKEND_DIR / "reports" / "visualizations" / "consolidated"
CHART_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("consolidated_prediction")

from scripts.generate_reports import gather_team_data, TEAM_MAP, compute_grade

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

PRIMARY_BLUE = colors.HexColor('#1E3A8A')
ACCENT_BLUE = colors.HexColor('#2563EB')
LIGHT_BG = colors.HexColor('#F8FAFC')
CARD_BORDER = colors.HexColor('#E2E8F0')
TEXT_DARK = colors.HexColor('#0F172A')
TEXT_MUTED = colors.HexColor('#64748B')
GOLD = colors.HexColor('#FEF08A')

styles = getSampleStyleSheet()

title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold',
                             fontSize=24, leading=30, textColor=PRIMARY_BLUE, spaceAfter=6)
subtitle_style = ParagraphStyle('DocSubTitle', parent=styles['Normal'], fontName='Helvetica',
                                fontSize=13, leading=17, textColor=TEXT_MUTED, spaceAfter=15)
h1_style = ParagraphStyle('Heading1_Custom', parent=styles['Normal'], fontName='Helvetica-Bold',
                          fontSize=17, leading=21, textColor=PRIMARY_BLUE, spaceBefore=12, spaceAfter=10)
h2_style = ParagraphStyle('Heading2_Custom', parent=styles['Normal'], fontName='Helvetica-Bold',
                          fontSize=12, leading=15, textColor=PRIMARY_BLUE, spaceBefore=10, spaceAfter=6)
body_style = ParagraphStyle('Body_Custom', parent=styles['Normal'], fontName='Helvetica',
                            fontSize=9.5, leading=13.5, textColor=TEXT_DARK, spaceAfter=6)
bullet_style = ParagraphStyle('Bullet_Custom', parent=body_style, leftIndent=15, bulletIndent=5, spaceAfter=4)
card_val_style = ParagraphStyle('CardVal', parent=styles['Normal'], fontName='Helvetica-Bold',
                                fontSize=18, leading=22, textColor=PRIMARY_BLUE, alignment=1)
card_lbl_style = ParagraphStyle('CardLbl', parent=styles['Normal'], fontName='Helvetica-Bold',
                                fontSize=7, leading=9, textColor=TEXT_MUTED, alignment=1)
th_style = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8.5, leading=10.5, textColor=colors.white, alignment=1)
td_style = ParagraphStyle('TD', fontName='Helvetica', fontSize=8, leading=10.5, textColor=TEXT_DARK, alignment=1)
td_left = ParagraphStyle('TDL', fontName='Helvetica', fontSize=8, leading=10.5, textColor=TEXT_DARK, alignment=0)
td_bold = ParagraphStyle('TDB', fontName='Helvetica-Bold', fontSize=8, leading=10.5, textColor=TEXT_DARK, alignment=1)


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_header_footer(self, page_count):
        self.saveState()
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(PRIMARY_BLUE)
            self.drawString(36, 760, "Consolidated Game Prediction Evaluation Report - All Teams")
            self.setFont("Helvetica", 8)
            self.setFillColor(TEXT_MUTED)
            self.drawRightString(576, 760, "FIFA World Cup AI Prediction Tournament 2026")

            self.setStrokeColor(CARD_BORDER)
            self.setLineWidth(0.75)
            self.line(36, 752, 576, 752)

            self.line(36, 42, 576, 42)
            self.setFont("Helvetica", 8)
            self.setFillColor(TEXT_MUTED)
            self.drawString(36, 30, "Report Date: " + datetime.now().strftime("%B %d, %Y") + " | Generated by Automated Analytics Pipeline")
            self.drawRightString(576, 30, "Page %d of %d" % (self._pageNumber, page_count))
        self.restoreState()


# ═══════════════════════════════════════════════════════════════
#  CHART GENERATION
# ═══════════════════════════════════════════════════════════════
def generate_charts(all_td):
    plt.rcParams['font.sans-serif'] = 'Helvetica'
    plt.rcParams['axes.edgecolor'] = '#CBD5E1'
    plt.rcParams['axes.linewidth'] = 0.8

    short = [td.team.name for td in all_td]
    colors_seq = ['#1E3A8A', '#2563EB', '#3B82F6', '#60A5FA', '#93C5FD']
    x = np.arange(len(short))

    # 1. DB Prediction Accuracy
    db_acc = [td.db_prediction_accuracy for td in all_td]
    fig, ax = plt.subplots(figsize=(6, 3.2))
    bars = ax.bar(short, db_acc, color=colors_seq, width=0.5, edgecolor='#0F172A')
    ax.set_ylabel('Accuracy (%)', fontsize=8.5, weight='bold', color='#1E3A8A')
    ax.set_title('Database Prediction Accuracy by Team', fontsize=10.5, weight='bold', color='#1E3A8A', pad=12)
    ax.set_ylim(0, 100)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    for bar, v in zip(bars, db_acc):
        ax.text(bar.get_x() + bar.get_width()/2., v + 1.5, '%.1f%%' % v, ha='center', va='bottom', fontsize=8, weight='bold')
    plt.tight_layout()
    plt.savefig(CHART_DIR / 'db_accuracy.png', dpi=300)
    plt.close()

    # 2. Best Model Accuracy
    best_acc = [td.best_eval.accuracy if td.best_eval else 0 for td in all_td]
    fig, ax = plt.subplots(figsize=(6, 3.2))
    bars = ax.bar(short, best_acc, color=colors_seq, width=0.5, edgecolor='#0F172A')
    ax.set_ylabel('Accuracy (%)', fontsize=8.5, weight='bold', color='#1E3A8A')
    ax.set_title('Best Model Winner Accuracy by Team', fontsize=10.5, weight='bold', color='#1E3A8A', pad=12)
    ax.set_ylim(0, 100)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    for bar, v in zip(bars, best_acc):
        ax.text(bar.get_x() + bar.get_width()/2., v + 1.5, '%.1f%%' % v, ha='center', va='bottom', fontsize=8, weight='bold')
    plt.tight_layout()
    plt.savefig(CHART_DIR / 'best_model_accuracy.png', dpi=300)
    plt.close()

    # 3. Radar Chart (Best Model Metrics)
    categories = ['Accuracy', 'Precision', 'Recall', 'F1 Score', 'Goal Accuracy']
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles_closed = angles + [angles[0]]
    fig, ax = plt.subplots(figsize=(5.5, 4.0), subplot_kw=dict(polar=True))
    for td, c in zip(all_td, ['#1E3A8A', '#2563EB', '#3B82F6', '#F59E0B', '#10B981']):
        b = td.best_eval
        vals = [b.accuracy, b.precision, b.recall, b.f1_score, b.goal_accuracy] if b else [0, 0, 0, 0, 0]
        ax.plot(angles_closed, vals + [vals[0]], color=c, linewidth=2, label=td.team.name)
    ax.set_xticks(angles)
    ax.set_xticklabels(categories, size=8, color='#0F172A', weight='bold')
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], size=6.5, color='#64748B')
    ax.set_ylim(0, 100)
    ax.set_title("Best Model Performance Benchmark (%)", size=10.5, pad=15, weight='bold', color='#1E3A8A')
    ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1.1), fontsize=7)
    plt.tight_layout()
    plt.savefig(CHART_DIR / 'radar.png', dpi=300)
    plt.close()

    # 4. Exact Score & Goal Diff Correct
    score_c = [b.correct_score / b.total_matches * 100 if b else 0 for b in (td.best_eval for td in all_td)]
    gd_c = [b.correct_goal_diff / b.total_matches * 100 if b else 0 for b in (td.best_eval for td in all_td)]
    width = 0.35
    fig, ax = plt.subplots(figsize=(6, 3.2))
    r1 = ax.bar(x - width/2, score_c, width, label='Exact Score', color='#2563EB', edgecolor='#1E3A8A')
    r2 = ax.bar(x + width/2, gd_c, width, label='Goal Diff', color='#1E3A8A', edgecolor='#0F172A')
    ax.set_ylabel('Correct Predictions (%)', fontsize=8.5, weight='bold', color='#1E3A8A')
    ax.set_title('Exact Score vs Goal Difference Accuracy (Best Model)', fontsize=10.5, weight='bold', color='#1E3A8A', pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(short, fontsize=8, weight='bold')
    ax.legend(fontsize=7.5)
    ax.set_ylim(0, 45)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    for r in (r1, r2):
        for bar in r:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., h + 0.8, '%.1f' % h, ha='center', va='bottom', fontsize=7, weight='bold')
    plt.tight_layout()
    plt.savefig(CHART_DIR / 'score_goal_diff.png', dpi=300)
    plt.close()

    # 5. Final Score Composition Stacked Bar
    p1 = [td.leaderboard.phase1_score if td.leaderboard else 0 for td in all_td]
    tech = [td.leaderboard.technical_score if td.leaderboard else 0 for td in all_td]
    pres = [td.leaderboard.presentation_score if td.leaderboard else 0 for td in all_td]
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.bar(x, p1, width=0.45, label='Phase 1 (/60)', color='#93C5FD', edgecolor='#2563EB')
    ax.bar(x, tech, width=0.45, bottom=p1, label='Technical (/20)', color='#60A5FA', edgecolor='#2563EB')
    ax.bar(x, pres, width=0.45, bottom=np.array(p1) + np.array(tech), label='Presentation (/20)', color='#1E3A8A', edgecolor='#0F172A')
    ax.set_ylabel('Final Score (/100)', fontsize=8.5, weight='bold', color='#1E3A8A')
    ax.set_title('Leaderboard Final Score Composition', fontsize=10.5, weight='bold', color='#1E3A8A', pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(short, fontsize=8, weight='bold')
    ax.legend(fontsize=7.5)
    ax.set_ylim(0, 50)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    for i, td in enumerate(all_td):
        v = td.leaderboard.final_score if td.leaderboard else 0
        ax.text(i, v + 1, '%.1f' % v, ha='center', va='bottom', fontsize=8, weight='bold')
    plt.tight_layout()
    plt.savefig(CHART_DIR / 'final_score.png', dpi=300)
    plt.close()

    # 6. Average Confidence
    conf = [b.avg_confidence if b else 0 for b in (td.best_eval for td in all_td)]
    fig, ax = plt.subplots(figsize=(6, 3.2))
    bars = ax.bar(short, conf, color=colors_seq, width=0.5, edgecolor='#0F172A')
    ax.set_ylabel('Avg Confidence (%)', fontsize=8.5, weight='bold', color='#1E3A8A')
    ax.set_title('Average Prediction Confidence by Team (Best Model)', fontsize=10.5, weight='bold', color='#1E3A8A', pad=12)
    ax.set_ylim(0, 100)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    for bar, v in zip(bars, conf):
        ax.text(bar.get_x() + bar.get_width()/2., v + 1.5, '%.1f%%' % v, ha='center', va='bottom', fontsize=8, weight='bold')
    plt.tight_layout()
    plt.savefig(CHART_DIR / 'confidence.png', dpi=300)
    plt.close()


def make_card(value, label, width=125, height=52):
    content = [
        Spacer(1, 6),
        Paragraph(str(value), card_val_style),
        Spacer(1, 2),
        Paragraph(label.upper(), card_lbl_style)
    ]
    t = Table([[content]], colWidths=[width], rowHeights=[height])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 1, CARD_BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('LINEABOVE', (0,0), (-1,0), 2.5, ACCENT_BLUE),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    return t


# ═══════════════════════════════════════════════════════════════
#  PDF BUILD
# ═══════════════════════════════════════════════════════════════
def build_pdf(all_td):
    pdf_filename = str(OUTPUT_DIR / "Consolidated_Game_Prediction_Evaluation_Report.pdf")
    doc = SimpleDocTemplate(
        pdf_filename, pagesize=letter,
        leftMargin=36, rightMargin=36, topMargin=48, bottomMargin=48
    )
    story = []
    report_date = datetime.now().strftime("%B %d, %Y")

    # ---- COVER PAGE ----
    story.append(Spacer(1, 40))
    story.append(HRFlowable(width="100%", thickness=6, color=PRIMARY_BLUE, spaceAfter=25, spaceBefore=0))
    story.append(Paragraph("FIFA World Cup AI Prediction Tournament 2026", subtitle_style))
    story.append(Paragraph("Consolidated Game Prediction Evaluation Report", title_style))
    story.append(Paragraph("Comparative Model & Match Prediction Assessment Across All Participating Teams",
                           ParagraphStyle('CoverTeam', parent=title_style, fontSize=16, leading=20, textColor=ACCENT_BLUE)))
    story.append(Spacer(1, 30))

    best_team = min(all_td, key=lambda t: t.leaderboard.rank if t.leaderboard else 999)
    best_db = max(all_td, key=lambda t: t.db_prediction_accuracy)
    best_model_team = max((td for td in all_td if td.best_eval), key=lambda t: t.best_eval.accuracy)

    cover_meta = [
        [Paragraph("<b>Tournament Name:</b>", td_left), Paragraph("FIFA World Cup AI Prediction Tournament 2026", td_left)],
        [Paragraph("<b>Report Type:</b>", td_left), Paragraph("Consolidated Game Prediction Evaluation Report", td_left)],
        [Paragraph("<b>Participating Teams:</b>", td_left), Paragraph("5 Teams (Paul Neerali, SoccerSense, Goal Jyolsyan, Goal GPT, BOL)", td_left)],
        [Paragraph("<b>Scope:</b>", td_left), Paragraph("DB predictions, automated model evaluation, leaderboard scoring", td_left)],
        [Paragraph("<b>Report Date:</b>", td_left), Paragraph(report_date, td_left)],
        [Paragraph("<b>Generated By:</b>", td_left), Paragraph("Automated Analytics Pipeline", td_left)],
        [Paragraph("<b>Tournament Champion:</b>", td_left),
         Paragraph("<b>%s (Team %s) - Score: %.2f / 100</b>" % (best_team.team.name, best_team.team.team_id_code,
                    best_team.leaderboard.final_score if best_team.leaderboard else 0), td_left)],
        [Paragraph("<b>Best Prediction Accuracy:</b>", td_left),
         Paragraph("<b>%s - %.1f%% (DB) / %.1f%% (Best Model)</b>" % (best_model_team.team.name,
                    best_db.db_prediction_accuracy, best_model_team.best_eval.accuracy if best_model_team.best_eval else 0), td_left)],
    ]
    t_cover = Table(cover_meta, colWidths=[180, 300])
    t_cover.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 1, CARD_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(t_cover)

    story.append(Spacer(1, 70))
    story.append(HRFlowable(width="100%", thickness=1, color=CARD_BORDER, spaceAfter=15, spaceBefore=0))
    story.append(Paragraph("Confidential & Official Evaluation Document (c) 2026",
                           ParagraphStyle('Conf', parent=body_style, fontSize=8, textColor=TEXT_MUTED, alignment=1)))
    story.append(PageBreak())

    # ---- PAGE 2: TOC + EXECUTIVE SUMMARY ----
    story.append(Paragraph("Table of Contents", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_BLUE, spaceAfter=12, spaceBefore=0))
    toc_data = [
        [Paragraph("<b>1. Executive Summary</b>", td_left), Paragraph("Page 2", td_style)],
        [Paragraph("<b>2. Official Championship Standings</b>", td_left), Paragraph("Page 2", td_style)],
        [Paragraph("<b>3. Database Prediction Performance</b>", td_left), Paragraph("Page 3", td_style)],
        [Paragraph("<b>4. Best Model Performance Analysis</b>", td_left), Paragraph("Page 4", td_style)],
        [Paragraph("<b>5. Visualizations & Comparative Analytics</b>", td_left), Paragraph("Page 5", td_style)],
        [Paragraph("<b>6. Team Profiles & Final Evaluation Narrative</b>", td_left), Paragraph("Page 6", td_style)],
    ]
    t_toc = Table(toc_data, colWidths=[440, 100])
    t_toc.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 0.5, CARD_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_toc)
    story.append(Spacer(1, 15))

    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_BLUE, spaceAfter=10, spaceBefore=0))
    story.append(Paragraph(
        "This consolidated report compares game prediction performance across all 5 participating teams in the "
        "<i>FIFA World Cup AI Prediction Tournament 2026</i>. Teams submitted automated prediction models that were "
        "evaluated against actual match outcomes, alongside their live database predictions. Key metrics include DB "
        "prediction accuracy, best model winner accuracy, precision, recall, F1 score, exact score predictions, goal "
        "difference accuracy, calibration (log loss / Brier score) and average prediction confidence.", body_style))
    story.append(Spacer(1, 8))

    c1 = make_card("%.1f%%" % best_model_team.best_eval.accuracy if best_model_team.best_eval else "N/A", "Best Model Accuracy")
    c2 = make_card("32", "Matches Evaluated")
    c3 = make_card("42", "Models Evaluated")
    c4 = make_card("5", "Participating Teams")
    grid1 = Table([[c1, c2, c3, c4]], colWidths=[135, 135, 135, 135])
    grid1.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(grid1)
    story.append(Spacer(1, 14))

    story.append(Paragraph("2. Official Championship Standings", h2_style))
    standings = [
        [Paragraph("Rank", th_style), Paragraph("Team Name", th_style), Paragraph("Code", th_style),
         Paragraph("Phase 1 (/60)", th_style), Paragraph("Technical (/20)", th_style),
         Paragraph("Presentation (/20)", th_style), Paragraph("Final Score (/100)", th_style), Paragraph("Grade", th_style)],
    ]
    for td in sorted(all_td, key=lambda t: t.leaderboard.rank if t.leaderboard else 999):
        lb = td.leaderboard
        grade = compute_grade(lb.final_score if lb else 0, 100)
        standings.append([
            Paragraph("<b>#%s</b>" % (lb.rank if lb else "N/A"), td_bold),
            Paragraph(td.team.name, td_left),
            Paragraph(td.team.team_id_code, td_style),
            Paragraph("%.2f" % (lb.phase1_score if lb else 0), td_style),
            Paragraph("%.2f" % (lb.technical_score if lb else 0), td_style),
            Paragraph("%.2f" % (lb.presentation_score if lb else 0), td_style),
            Paragraph("<b>%.2f</b>" % (lb.final_score if lb else 0), td_bold),
            Paragraph("<b>%s</b>" % grade, td_bold),
        ])
    t_stand = Table(standings, colWidths=[40, 120, 45, 70, 70, 80, 80, 55])
    t_stand.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_BLUE),
        ('GRID', (0,0), (-1,-1), 0.5, CARD_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('BACKGROUND', (0,1), (-1,1), GOLD),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_stand)

    story.append(PageBreak())

    # ---- PAGE 3: DB PREDICTION PERFORMANCE ----
    story.append(Paragraph("3. Database Prediction Performance", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_BLUE, spaceAfter=10, spaceBefore=0))
    story.append(Paragraph("Live database submissions from each team, scored against official match results.", body_style))
    story.append(Spacer(1, 8))

    db_rows = [
        [Paragraph("Team", th_style), Paragraph("Models", th_style), Paragraph("Correct", th_style),
         Paragraph("Total", th_style), Paragraph("Accuracy", th_style), Paragraph("Accuracy Rank", th_style)],
    ]
    db_rank = {td.team.id: i + 1 for i, td in enumerate(sorted(all_td, key=lambda t: t.db_prediction_accuracy, reverse=True))}
    for td in sorted(all_td, key=lambda t: t.db_prediction_accuracy, reverse=True):
        db_rows.append([
            Paragraph(td.team.name, td_left),
            Paragraph(str(len(td.model_files)), td_style),
            Paragraph(str(td.db_correct), td_style),
            Paragraph(str(td.db_total), td_style),
            Paragraph("<b>%.1f%%</b>" % td.db_prediction_accuracy, td_bold),
            Paragraph("#%d" % db_rank[td.team.id], td_bold),
        ])
    t_db = Table(db_rows, colWidths=[140, 70, 70, 70, 90, 100])
    t_db.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_BLUE),
        ('GRID', (0,0), (-1,-1), 0.5, CARD_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_db)
    story.append(Spacer(1, 15))

    img_db = Image(str(CHART_DIR / 'db_accuracy.png'), width=270, height=190)
    img_best = Image(str(CHART_DIR / 'best_model_accuracy.png'), width=270, height=190)
    t_row1 = Table([[img_db, img_best]], colWidths=[270, 270])
    t_row1.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t_row1)

    story.append(PageBreak())

    # ---- PAGE 4: BEST MODEL PERFORMANCE ----
    story.append(Paragraph("4. Best Model Performance Analysis", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_BLUE, spaceAfter=10, spaceBefore=0))
    story.append(Paragraph("Evaluation of each team's best-scoring model against the full 32-match schedule.", body_style))
    story.append(Spacer(1, 8))

    best_rows = [
        [Paragraph("Team", th_style), Paragraph("Best Model", th_style), Paragraph("Accuracy", th_style),
         Paragraph("Precision", th_style), Paragraph("Recall", th_style), Paragraph("F1", th_style),
         Paragraph("Winner", th_style), Paragraph("Exact Score", th_style), Paragraph("Goal Diff", th_style)],
    ]
    for td in sorted((t for t in all_td if t.best_eval), key=lambda t: t.best_eval.accuracy, reverse=True):
        b = td.best_eval
        best_rows.append([
            Paragraph(td.team.name, td_left),
            Paragraph(b.model_file.filename if b.model_file else "N/A", td_style),
            Paragraph("<b>%.1f%%</b>" % b.accuracy, td_bold),
            Paragraph("%.1f%%" % b.precision, td_style),
            Paragraph("%.1f%%" % b.recall, td_style),
            Paragraph("%.1f%%" % b.f1_score, td_style),
            Paragraph("%d/%d" % (b.correct_winner, b.total_matches), td_style),
            Paragraph("%d/%d" % (b.correct_score, b.total_matches), td_style),
            Paragraph("%d/%d" % (b.correct_goal_diff, b.total_matches), td_style),
        ])
    t_best = Table(best_rows, colWidths=[95, 105, 55, 55, 50, 45, 55, 60, 60])
    t_best.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_BLUE),
        ('GRID', (0,0), (-1,-1), 0.5, CARD_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_best)
    story.append(Spacer(1, 15))

    story.append(Paragraph("Calibration & Confidence Benchmarks", h2_style))
    calib_rows = [
        [Paragraph("Team", th_style), Paragraph("Win Acc", th_style), Paragraph("Draw Acc", th_style),
         Paragraph("Loss Acc", th_style), Paragraph("Goal Acc", th_style), Paragraph("Log Loss", th_style),
         Paragraph("Brier", th_style), Paragraph("Avg Confidence", th_style)],
    ]
    for td in sorted((t for t in all_td if t.best_eval), key=lambda t: t.best_eval.accuracy, reverse=True):
        b = td.best_eval
        calib_rows.append([
            Paragraph(td.team.name, td_left),
            Paragraph("%.1f%%" % b.win_accuracy, td_style),
            Paragraph("%.1f%%" % b.draw_accuracy, td_style),
            Paragraph("%.1f%%" % b.loss_accuracy, td_style),
            Paragraph("%.1f%%" % b.goal_accuracy, td_style),
            Paragraph("%.3f" % b.log_loss, td_style),
            Paragraph("%.3f" % b.brier_score, td_style),
            Paragraph("%.1f%%" % b.avg_confidence, td_style),
        ])
    t_calib = Table(calib_rows, colWidths=[95, 70, 70, 70, 70, 70, 60, 85])
    t_calib.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_BLUE),
        ('GRID', (0,0), (-1,-1), 0.5, CARD_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_calib)

    story.append(PageBreak())

    # ---- PAGE 5: VISUALIZATIONS ----
    story.append(Paragraph("5. Visualizations & Comparative Analytics", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_BLUE, spaceAfter=12, spaceBefore=0))

    img_radar = Image(str(CHART_DIR / 'radar.png'), width=270, height=190)
    img_sg = Image(str(CHART_DIR / 'score_goal_diff.png'), width=270, height=190)
    t_v1 = Table([[img_radar, img_sg]], colWidths=[270, 270])
    t_v1.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t_v1)
    story.append(Spacer(1, 15))

    img_fs = Image(str(CHART_DIR / 'final_score.png'), width=270, height=190)
    img_cf = Image(str(CHART_DIR / 'confidence.png'), width=270, height=190)
    t_v2 = Table([[img_fs, img_cf]], colWidths=[270, 270])
    t_v2.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t_v2)

    story.append(PageBreak())

    # ---- PAGE 6: TEAM PROFILES & VERDICT ----
    story.append(Paragraph("6. Team Profiles & Final Evaluation Narrative", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_BLUE, spaceAfter=8, spaceBefore=0))

    for td in sorted(all_td, key=lambda t: t.leaderboard.rank if t.leaderboard else 999):
        lb = td.leaderboard
        b = td.best_eval
        acc_rank = db_rank[td.team.id]
        grade = compute_grade(lb.final_score if lb else 0, 100)
        if b:
            line = ("\u2022 <b>%s (Team %s) - Rank #%s:</b> DB accuracy %.1f%% (%d/%d), best model <i>%s</i> "
                    "with %.1f%% winner accuracy (F1 %.1f%%, precision %.1f%%, recall %.1f%%). Exact score %d/%d, "
                    "goal diff %d/%d, log loss %.3f. Final score %.2f/100 (Grade %s)." % (
                        td.team.name, td.team.team_id_code, lb.rank if lb else "N/A",
                        td.db_prediction_accuracy, td.db_correct, td.db_total,
                        b.model_file.filename if b.model_file else "N/A",
                        b.accuracy, b.f1_score, b.precision, b.recall,
                        b.correct_score, b.total_matches, b.correct_goal_diff, b.total_matches,
                        b.log_loss, lb.final_score if lb else 0, grade))
        else:
            line = ("\u2022 <b>%s (Team %s) - Rank #%s:</b> DB accuracy %.1f%% (%d/%d). No loadable model evaluated. "
                    "Final score %.2f/100 (Grade %s)." % (
                        td.team.name, td.team.team_id_code, lb.rank if lb else "N/A",
                        td.db_prediction_accuracy, td.db_correct, td.db_total,
                        lb.final_score if lb else 0, grade))
        story.append(Paragraph(line, bullet_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Final Tournament Verdict", h2_style))
    story.append(Paragraph(
        "<b>%s</b> leads the final championship standings with %.2f / 100, while <b>%s</b> achieved the highest "
        "best-model winner accuracy (%.1f%%) and <b>%s</b> posted the strongest database prediction accuracy (%.1f%%). "
        "Across all teams, winner prediction was consistently strong while exact-score and draw prediction remain the "
        "principal areas for improvement in future rounds." % (
            best_team.team.name, best_team.leaderboard.final_score if best_team.leaderboard else 0,
            best_model_team.team.name, best_model_team.best_eval.accuracy if best_model_team.best_eval else 0,
            best_db.team.name, best_db.db_prediction_accuracy), body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print("Successfully generated %s" % pdf_filename)


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    start = datetime.now()
    log.info("=" * 70)
    log.info("  CONSOLIDATED GAME PREDICTION REPORT GENERATOR")
    log.info("=" * 70)

    # 1. Read database
    log.info("Phase 1: Reading database...")
    from scripts.evaluate_models import DatabaseReader, ModelDiscovery, EvaluationEngine
    from collections import defaultdict

    db = DatabaseReader()
    matches = db.get_matches()
    results = db.get_actual_results()
    all_predictions = db.get_predictions()
    all_scores = db.get_scores()
    leaderboard = db.get_leaderboard()
    tech_evals = db.get_technical_evals()
    pres_evals = db.get_presentation_evals()

    # 2. Discover and evaluate models
    log.info("Phase 2: Discovering and evaluating models...")
    discovery = ModelDiscovery(BACKEND_DIR / "uploads")
    all_model_files = discovery.discover_all()
    models_by_folder = defaultdict(list)
    for mf in all_model_files:
        models_by_folder[mf.team_folder].append(mf)

    all_evaluations = {}
    result_map = {r.match_id: r for r in results.values()}
    for team in db.get_teams():
        folder = TEAM_MAP.get(team.team_id_code, {}).get("folder", "")
        evals = []
        for mf in models_by_folder.get(folder, []):
            try:
                model = discovery.load_model(mf)
            except Exception:
                continue
            if model and mf.has_predict:
                match_preds = []
                for match in matches:
                    actual = result_map.get(match.id)
                    if not actual:
                        continue
                    out = discovery.run_inference(model, mf, match.home_team, match.away_team)
                    if out:
                        predicted = EvaluationEngine.extract_prediction(out)
                        comp = EvaluationEngine.compare_match_prediction(predicted, actual, match)
                        match_preds.append(comp)
                if match_preds:
                    ev = EvaluationEngine.evaluate_predictions(match_preds, matches, results)
                    ev.model_file = mf
                    evals.append(ev)
        all_evaluations[team.id] = evals
        best = max(evals, key=lambda e: e.accuracy) if evals else None
        log.info("  %s: %d models evaluated, best=%.1f%%" % (team.name, len(evals), best.accuracy if best else 0))

    # 3. Gather team data
    log.info("Phase 3: Aggregating team data...")
    all_td = gather_team_data(db, discovery, all_model_files, all_evaluations,
                              matches, results, all_predictions, all_scores,
                              leaderboard, tech_evals, pres_evals)

    total_models = sum(len(td.model_files) for td in all_td)
    total_evals = sum(len(td.evaluations) for td in all_td)
    log.info("  Teams=%d  Model files=%d  Evaluated=%d" % (len(all_td), total_models, total_evals))

    # 4. Generate charts + PDF
    log.info("Phase 4: Generating charts...")
    generate_charts(all_td)
    log.info("Phase 5: Building PDF...")
    build_pdf(all_td)

    elapsed = (datetime.now() - start).total_seconds()
    log.info("=" * 70)
    log.info("  REPORT GENERATED SUCCESSFULLY: %s" % (OUTPUT_DIR / "Consolidated_Game_Prediction_Evaluation_Report.pdf"))
    log.info("  Time elapsed: %.1fs" % elapsed)
    log.info("=" * 70)


if __name__ == "__main__":
    main()
