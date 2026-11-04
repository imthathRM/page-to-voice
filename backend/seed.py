import os
import sys
from pathlib import Path

# Ensure backend directory is in python sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from database import engine, SessionLocal, Base
import models
from security import get_password_hash


def seed_database():
    """Initialize database tables and create the default admin user if not present."""
    print("Checking and creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin_email = "admin@pagetovoice.com"
        admin_user = db.query(models.User).filter(models.User.email == admin_email).first()

        if admin_user:
            print(f"Admin user already exists: {admin_email}")
        else:
            print(f"Creating default admin user: {admin_email}...")
            admin_user = models.User(
                username="admin",
                email=admin_email,
                password_hash=get_password_hash("admin123"),
                role=models.UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"Default admin user successfully created with ID: {admin_user.id}")

    except Exception as exc:
        db.rollback()
        print(f"Error seeding database: {exc}")
        raise exc
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
