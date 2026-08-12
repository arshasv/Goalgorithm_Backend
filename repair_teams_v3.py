"""Safe seed/repair script: creates missing teams & users, resets all team leader passwords to a known dev password.

Run from the backend directory:
    python repair_teams_v3.py

Safe to run multiple times — will not duplicate existing records.
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.team import TeamModel
from app.models.user import UserModel
from app.models.enums import UserRole
from app.auth.auth_service import hash_password
from app.utils.team_name_utils import normalize_team_name

DEV_PASSWORD = "password123"

TEAMS = [
    {"team_id": "A", "name": "Team A", "code": "A", "email": "teama@fifa-scoring.com", "username": "team_a_leader"},
    {"team_id": "B", "name": "Team B", "code": "B", "email": "teamb@fifa-scoring.com", "username": "team_b_leader"},
    {"team_id": "C", "name": "Team C", "code": "C", "email": "teamc@fifa-scoring.com", "username": "team_c_leader"},
    {"team_id": "D", "name": "Team D", "code": "D", "email": "teamd@fifa-scoring.com", "username": "team_d_leader"},
    {"team_id": "E", "name": "Team E", "code": "E", "email": "teame@fifa-scoring.com", "username": "team_e_leader"},
]


def repair():
    db = SessionLocal()
    try:
        for td in TEAMS:
            tid = td["team_id"]

            # --- Ensure team record exists with correct name ---
            team = db.query(TeamModel).filter(TeamModel.team_id == tid).first()
            if not team:
                team = TeamModel(
                    team_id=tid,
                    name=td["name"],
                    code=td["code"],
                    name_normalized=normalize_team_name(td["name"]),
                )
                db.add(team)
                db.flush()
                print(f"Created team: {td['name']}")
            else:
                # Fix name if it differs (e.g. "goalkuing" -> "Team A")
                if team.name != td["name"]:
                    old = team.name
                    team.name = td["name"]
                    team.name_normalized = normalize_team_name(td["name"])
                    print(f"Fixed team name: {old} -> {td['name']}")

            # --- Ensure user account exists with known password ---
            user = db.query(UserModel).filter(UserModel.email == td["email"]).first()
            if not user:
                # Also check if there's already a user linked to this team via user_id
                if team.user_id:
                    user = db.query(UserModel).filter(UserModel.id == team.user_id).first()
                if not user:
                    user = UserModel(
                        username=td["username"],
                        email=td["email"],
                        password_hash=hash_password(DEV_PASSWORD),
                        role=UserRole.TEAM_LEADER,
                        is_active=True,
                    )
                    db.add(user)
                    db.flush()
                    print(f"Created user: {td['email']} / {DEV_PASSWORD}")
                else:
                    # User exists via team link but with different email — update email
                    old_email = user.email
                    user.email = td["email"]
                    user.password_hash = hash_password(DEV_PASSWORD)
                    user.is_active = True
                    print(f"Updated user {old_email} -> {td['email']}, password reset to {DEV_PASSWORD}")
            else:
                # User exists — reset password to known dev password
                user.password_hash = hash_password(DEV_PASSWORD)
                user.role = UserRole.TEAM_LEADER
                user.is_active = True
                print(f"Reset password for {td['email']} to {DEV_PASSWORD}")

            # --- Link team <-> user ---
            if team.user_id != user.id:
                team.user_id = user.id
                print(f"Linked {td['email']} -> Team {tid}")

        db.commit()
        print("\nRepair complete! All team accounts:")
        for td in TEAMS:
            print(f"  Team {td['team_id']}: {td['email']} / {DEV_PASSWORD}")
        print("\nOrganizer: arshas@opentrends.net / admin123")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    repair()
