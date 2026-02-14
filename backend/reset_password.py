import sys
import os
from sqlalchemy.orm import Session
# Add parent directory to path to import app
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.user import User
from app.models.workspace import Workspace # Often needed for User relationship
from app.models.service import Service # Often needed
from app.models.contact import Contact # Often needed
from app.models.booking import Booking
from app.models.form import Form
from app.models.inventory import InventoryItem
from app.models.conversation import Conversation
from app.models.email_integration import EmailIntegration
from app.core.security import get_password_hash

def reset_password():
    db = SessionLocal()
    try:
        user_email = "shubhamragade2003@gmail.com"
        new_password = "Demo@2026!"
        
        user = db.query(User).filter(User.email == user_email).first()
        
        if user:
            print(f"Found user: {user.email}")
            user.hashed_password = get_password_hash(new_password)
            db.commit()
            print(f"Password reset successfully to: {new_password}")
        else:
            print(f"User {user_email} not found!")
            
    except Exception as e:
        print(f"Error resetting password: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_password()
