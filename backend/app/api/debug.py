from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.deps import get_db
from app.core.config import settings
import os

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    # 1. Check DB connection and details
    db_status = "Unknown"
    current_db = "Unknown"
    tables = []
    orm_ok = "Not Tested"
    user_count = -1
    user_emails = []
    shubham_pass_verified = "N/A"

    try:
        # Check connection
        db.execute(text("SELECT 1"))
        db_status = "Connected"
        
        # Get DB name
        res = db.execute(text("SELECT current_database()"))
        current_db = res.scalar()
        
        # Get Current Schema
        res = db.execute(text("SELECT current_schema()"))
        current_schema = res.scalar()
        
        # List tables with their schemas
        res = db.execute(text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog')"))
        tables = [f"{row[0]}.{row[1]}" for row in res]
        
        # Try ORM query
        from app.models.user import User
        from app.core.security import verify_password
        try:
            users = db.query(User).all()
            user_count = len(users)
            user_emails = [u.email for u in users]
            
            # Test password for shubham user
            shub_user = db.query(User).filter(User.email == "shubhamragade2003@gmail.com").first()
            pass_test = "User Not Found"
            if shub_user:
                is_valid = verify_password("Demo@2026!", shub_user.hashed_password)
                pass_test = "Correct" if is_valid else "Incorrect"
            shubham_pass_verified = pass_test
            
            orm_ok = True
        except Exception as orm_err:
            orm_ok = f"Error: {str(orm_err)}"
            user_count = -1
            user_emails = []
        
    except Exception as e:
        db_status = f"Error: {str(e)}"
        orm_ok = "Skipped"

    # 2. Inspect Environment Variables (Selective/Masked)
    masked_db = settings.DATABASE_URL[:30] + "..." if settings.DATABASE_URL else "None"
    
    return {
        "status": "alive",
        "database": {
            "status": db_status,
            "name": current_db,
            "current_schema": current_schema,
            "tables_found": len(tables),
            "tables": tables,
            "orm_test": {
                "ok": orm_ok,
                "user_count": user_count,
                "emails": user_emails,
                "shubham_pass_verified": shubham_pass_verified
            }
        },
        "config": {
            "PROJECT_NAME": settings.PROJECT_NAME,
            "DATABASE_URL_START": masked_db,
            "FRONTEND_URL": settings.FRONTEND_URL,
            "PYTHON_VERSION": os.getenv("PYTHON_VERSION")
        }
    }
