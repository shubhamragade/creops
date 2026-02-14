import sys
import os

# Add backend to path explicitly
current_dir = os.getcwd()
backend_dir = os.path.join(current_dir, "backend")
sys.path.append(backend_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, ".env"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

try:
    from app.models.user import User
    from app.models.workspace import Workspace
    from app.core.config import settings
except ImportError as e:
    print(f"Import Error: {e}")
    # Fallback for debugging
    class MockSettings:
        DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/careops" # Default fallback
    settings = MockSettings()
    print("Using fallback settings due to import error.")

# Setup DB connection
try:
    # Handle the case where DATABASE_URL might be a distinct object object or string
    db_url = str(settings.DATABASE_URL)
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    print("Database connected.")
except Exception as e:
    print(f"DB Connection Error: {e}")
    sys.exit(1)

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_password(email, new_password):
    try:
        # Check if user exists using raw SQL
        result = db.execute(text("SELECT email FROM users WHERE email = :email"), {"email": email})
        user = result.fetchone()
        
        if not user:
            print(f"User with email {email} not found.")
            # List all users for debugging
            result_all = db.execute(text("SELECT email FROM users"))
            print("Available users:", [row[0] for row in result_all])
            return

        hashed_password = pwd_context.hash(new_password)
        
        # Update password using raw SQL
        db.execute(
            text("UPDATE users SET hashed_password = :hp WHERE email = :email"),
            {"hp": hashed_password, "email": email}
        )
        db.commit()
        print(f"SUCCESS: Password for {email} has been reset to: {new_password}")
    except Exception as e:
        print(f"Error during reset: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reset_password_root.py <email> [new_password]")
        # Default run for specific case
        reset_password("shubhamragade2014@gmail.com", "Staff123!")
    else:
        email = sys.argv[1]
        password = sys.argv[2] if len(sys.argv) > 2 else "Staff123!"
        reset_password(email, password)
