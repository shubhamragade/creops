from sqlalchemy import create_engine, text
from app.core.config import settings

# Create database engine
engine = create_engine(settings.DATABASE_URL)

def run_migration():
    print("Starting manual migration: Adding Google columns to workspaces table...")
    
    statements = [
        "ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS google_connected BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS google_refresh_token VARCHAR;",
        "ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS google_email VARCHAR;",
        "ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS google_token_expiry TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS google_from_name VARCHAR;"
    ]
    
    with engine.connect() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
                conn.commit()
                print(f"Executed: {stmt}")
            except Exception as e:
                print(f"Error executing {stmt}: {e}")
                
    print("Migration completed.")

if __name__ == "__main__":
    run_migration()
