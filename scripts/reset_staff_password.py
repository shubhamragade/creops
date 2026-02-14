
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.models.user import User
from app.core.config import settings

# Setup DB connection
engine = create_engine(str(settings.DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_password(email: str, new_password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"User with email {email} not found.")
        return

    hashed_password = pwd_context.hash(new_password)
    user.hashed_password = hashed_password
    db.commit()
    print(f"Password for {email} has been reset to: {new_password}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reset_staff_password.py <email> [new_password]")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else "Staff123!"
    
    reset_password(email, password)
