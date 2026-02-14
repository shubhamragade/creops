from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.config import settings
from sqlalchemy import text
import os

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    # 1. Check DB connection and details
    db_status = "Unknown"
    current_db = "Unknown"
    tables = []
    try:
        # Check connection
        db.execute(text("SELECT 1"))
        db_status = "Connected"
        
        # Get DB name
        res = db.execute(text("SELECT current_database()"))
        current_db = res.scalar()
        
        # List tables
        res = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in res]
        
    except Exception as e:
        db_status = f"Error: {str(e)}"

    # 2. Inspect Environment Variables (Selective/Masked)
    masked_db = settings.DATABASE_URL[:30] + "..." if settings.DATABASE_URL else "None"
    
    return {
        "status": "alive",
        "database": {
            "status": db_status,
            "name": current_db,
            "tables_found": len(tables),
            "tables": tables
        },
        "config": {
            "PROJECT_NAME": settings.PROJECT_NAME,
            "DATABASE_URL_START": masked_db,
            "FRONTEND_URL": settings.FRONTEND_URL,
            "ENV_JWT_SECRET_SET": bool(os.getenv("JWT_SECRET")),
            "PYTHON_VERSION": os.getenv("PYTHON_VERSION")
        }
    }
