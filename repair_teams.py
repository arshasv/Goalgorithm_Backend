import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.team import TeamModel
from app.models.user import UserModel
from app.models.enums import UserRole
from app.auth.auth_service import hash_password

def repair():
    db = SessionLocal()
    teams = db.query(TeamModel).filter(TeamModel.user_id == None).all()
    print(f"Found {len(teams)} teams without users.")
    for team in teams:
        tid = team.team_id.lower()
        email = f"team{tid}@fifa-scoring.com"
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            user = UserModel(
                username=f"team_{tid}_leader",
                email=email,
                password_hash=hash_password(f"team{tid}123"),
                role=UserRole.TEAM_LEADER,
            )
            db.add(user)
            db.flush()
            print(f"Created user for team {team.team_id} with email {email} and password team{tid}123")
        team.user_id = user.id
    db.commit()
    db.close()
    print("Repaired all teams.")

if __name__ == "__main__":
    repair()
