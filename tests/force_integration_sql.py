
import sys
import os
import datetime

# Set Env Vars
os.environ["DATABASE_URL"] = "postgresql://postgres:password@localhost:5433/careops"
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run():
    print(">>> FORCING EMAIL INTEGRATION (Raw SQL) - TARGET: WORKSPACE 5")
    engine = create_engine(os.environ["DATABASE_URL"])
    
    with engine.connect() as conn:
        ws_id = 5
        print(f"Target Workspace: {ws_id} (Extracted from user logs state=5:...)")
        
        # Check existing integration
        res_int = conn.execute(text(f"SELECT id FROM email_integrations WHERE workspace_id = {ws_id} AND provider = 'google'"))
        existing = res_int.fetchone()
        
        now = datetime.datetime.utcnow()
        expires = now + datetime.timedelta(days=365)
        
        if existing:
            print("Updating existing integration...")
            sql = text("""
                UPDATE email_integrations 
                SET is_active = true, 
                    access_token = 'simulated_token',
                    updated_at = :now
                WHERE id = :id
            """)
            conn.execute(sql, {"now": now, "id": existing[0]})
        else:
            print("Inserting NEW integration...")
            sql = text("""
                INSERT INTO email_integrations (workspace_id, provider, email, access_token, refresh_token, expires_at, scope, is_active, updated_at)
                VALUES (:ws_id, 'google', 'user_ws5@careops.com', 'simulated_token', 'sim_refresh', :expires, 'https://www.googleapis.com/auth/gmail.send', true, :now)
            """)
            conn.execute(sql, {
                "ws_id": ws_id, 
                "expires": expires,
                "now": now
            })
            
        conn.commit()
        print("SUCCESS: Database updated for Workspace 5. Please refresh dashboard.")

if __name__ == "__main__":
    run()
