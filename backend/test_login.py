from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import verify_password

db = SessionLocal()

try:
    # Get the owner user
    user = db.query(User).filter(User.email == "owner@careops.com").first()
    
    if not user:
        print("❌ User not found!")
    else:
        print(f"✅ User found: {user.email}")
        print(f"   Role: {user.role}")
        print(f"   Active: {user.is_active}")
        print(f"   Workspace ID: {user.workspace_id}")
        print(f"   Hashed password (first 20 chars): {user.hashed_password[:20]}...")
        
        # Test password verification
        test_password = "owner123"
        is_valid = verify_password(test_password, user.hashed_password)
        
        if is_valid:
            print(f"✅ Password verification PASSED for '{test_password}'")
        else:
            print(f"❌ Password verification FAILED for '{test_password}'")
            
finally:
    db.close()
