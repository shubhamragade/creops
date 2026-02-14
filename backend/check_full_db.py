
import sys
import os
from sqlalchemy import text

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app.db.session import engine

def dump_all_tables():
    with engine.connect() as connection:
        # Get all table names
        result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [row[0] for row in result.fetchall()]
        print(f"Tables in DB: {tables}")
        
        for table in tables:
            rows = connection.execute(text(f"SELECT count(*) FROM {table}")).scalar()
            print(f"Table {table}: {rows} rows")
            if table == 'users':
                users = connection.execute(text(f"SELECT email, password FROM {table}")).fetchall()
                for u in users:
                    print(f"  User: {u[0]} | PwdHash: {u[1][:10]}...")

if __name__ == "__main__":
    dump_all_tables()
