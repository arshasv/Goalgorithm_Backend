#!/usr/bin/env python3
"""Debug script to test actual model outputs for a single match."""
import sys, os, json, pickle, traceback
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DATABASE_URL",
    "postgresql://goalgorithm:npg_VAFnHKdGy3O9@ep-solitary-fire-as2no21e-pooler.c-4.eu-central-1.aws.neon.tech/goalgorithm?sslmode=require")

from app.model_execution.services.model_compat import safe_load

UPLOADS = BACKEND_DIR / "uploads"

TEST_MATCH = {"home_team": "France", "away_team": "Spain"}

def test_model(filepath, team_label):
    print(f"\n{'='*60}")
    print(f"TEAM: {team_label} | FILE: {filepath.name}")
    print(f"{'='*60}")
    try:
        with open(filepath, "rb") as f:
            model = safe_load(f)
        
        print(f"  Type: {type(model).__name__}")
        print(f"  Module: {type(model).__module__}")
        print(f"  Has predict: {hasattr(model, 'predict')}")
        
        if hasattr(model, 'predict'):
            result = model.predict(TEST_MATCH)
            print(f"  Output type: {type(result).__name__}")
            if isinstance(result, dict):
                print(f"  Output keys: {list(result.keys())}")
                print(f"  Output (pretty):")
                print(json.dumps(result, indent=2, default=str)[:3000])
            else:
                print(f"  Output value: {str(result)[:2000]}")
        else:
            print(f"  Attributes: {[a for a in dir(model) if not a.startswith('_')]}")
    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()

# Test one model from each team
test_files = [
    (UPLOADS / "paulneerali" / "paulneerali_v11.pkl", "Paul Neerali"),
    (UPLOADS / "goalGPT" / "goalgpt_v2.pkl", "Goal GPT"),
    (UPLOADS / "soccersence" / "soccersense_v3.pkl", "SoccerSense"),
    (UPLOADS / "goaljyolsyan" / "goaljolsyan_v1.pkl", "Goal Jyolsyan"),
    (UPLOADS / "bol" / "bol_v2.pkl", "BOL"),
]

for fp, label in test_files:
    if fp.exists():
        test_model(fp, label)
    else:
        print(f"\n  SKIP: {fp} not found")

# Also test additional BOL models
for v in ["bol_v3.pkl", "bol_v5.pkl", "bol_v10.pkl"]:
    fp = UPLOADS / "bol" / v
    if fp.exists():
        test_model(fp, f"BOL ({v})")
