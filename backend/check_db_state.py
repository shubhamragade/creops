import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())
print(f"CWD: {os.getcwd()}")
print(f"Sys Path: {sys.path}")

from app.db.session import SessionLocal

# Import base which imports all models in correct order (theoretically)
from app.db.base import Base
# We still need to import the classes to use them in query, but Base should have registered them
from app.models.user import User
from app.models.workspace import Workspace
from app.models.booking import Booking



# ... add others if needed

db = SessionLocal()
try:
    print("--- USERS ---")
    users = db.query(User).all()
    print(f"Count: {len(users)}")
    for u in users:
        print(f" - ID: {u.id}, Email: {u.email}, Role: {u.role}, WorkspaceID: {u.workspace_id}")

    print("\n--- WORKSPACES ---")
    workspaces = db.query(Workspace).all()
    print(f"Count: {len(workspaces)}")
    for w in workspaces:
        print(f" - ID: {w.id}, Name: {w.name}, Slug: {w.slug}")

    print("\n--- BOOKINGS ---")
    bookings = db.query(Booking).all()
    print(f"Count: {len(bookings)}")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
