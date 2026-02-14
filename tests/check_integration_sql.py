
import sys
import os
import datetime

# Set Env Vars
os.environ["DATABASE_URL"] = "postgresql://postgres:password@localhost:5433/careops"
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy import create_engine, text

def run():
    print(">>> CHECKING INTEGRATION STATUS (Raw SQL) - TARGET: WORKSPACE 5")
    engine = create_engine(os.environ["DATABASE_URL"])
    
    with engine.connect() as conn:
        ws_id = 5
        print(f"Target Workspace: {ws_id}")
        
        # Check existing integration
        res_int = conn.execute(text(f"SELECT id, is_active, email FROM email_integrations WHERE workspace_id = {ws_id} AND provider = 'google'"))
        existing = res_int.fetchone()
        
        if existing:
            print(f"SUCCESS: Integration Found!")
            print(f" - ID: {existing[0]}")
            print(f" - Active: {existing[1]}")
            print(f" - Email: {existing[2]}")
        else:
            print("FAILURE: No integration found for Workspace 5")

if __name__ == "__main__":
    run()
