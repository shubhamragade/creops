
import sys
import os

# Set Env Vars
os.environ["DATABASE_URL"] = "postgresql://postgres:password@localhost:5433/careops"
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy import create_engine, text

def run():
    print(">>> FORCING HARD DISCONNECT (Raw SQL) - TARGET: WORKSPACE 5")
    engine = create_engine(os.environ["DATABASE_URL"])
    
    with engine.connect() as conn:
        ws_id = 5
        print(f"Target Workspace: {ws_id}")
        
        # Check existing integration
        res_int = conn.execute(text(f"SELECT id, is_active FROM email_integrations WHERE workspace_id = {ws_id} AND provider = 'google'"))
        existing = res_int.fetchone()
        
        if existing:
            print(f"Found Integration (ID: {existing[0]}, Active: {existing[1]}). DELETING...")
            sql = text("DELETE FROM email_integrations WHERE id = :id")
            conn.execute(sql, {"id": existing[0]})
            conn.commit()
            print("SUCCESS: Integration DELETED. Dashboard should show 'Connect Gmail'.")
        else:
            print("No integration found to delete.")

if __name__ == "__main__":
    run()
