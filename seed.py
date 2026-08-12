"""Seed the database with default organizer account only."""
import argparse
import sys

from app.auth.auth_service import hash_password
from app.database.base import Base
from app.database.connection import engine
from app.database.session import SessionLocal
from app.models.enums import UserRole
from app.models.user import UserModel
from app.utils.email_validator import validate_email_domain


def seed(force: bool = False):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing_org = (
            db.query(UserModel)
            .filter(UserModel.role == UserRole.ORGANIZER)
            .first()
        )
        if existing_org and not force:
            print("Organizer already exists. Use --force to reseed.")
        else:
            if existing_org:
                db.delete(existing_org)
                db.flush()

            org_email = "arshas@opentrends.net"
            email_err = validate_email_domain(org_email)
            if email_err:
                print(
                    f"Invalid organizer email domain: {org_email}",
                    file=sys.stderr,
                )
                sys.exit(1)

            org = UserModel(
                username="admin",
                email=org_email,
                password_hash=hash_password("admin123"),
                role=UserRole.ORGANIZER,
            )
            db.add(org)
            db.flush()
            print(f"Created organizer: arshas@opentrends.net / admin123")

        db.commit()
        print("\nSeed complete! Only organizer account created.")
        print("Teams, matches, and test users are no longer auto-created.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Force reseed")
    args = parser.parse_args()
    seed(force=args.force)
