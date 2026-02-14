
import sys
import os
from sqlalchemy import text

sys.path.append(os.getcwd())

from app.db.session import engine

def dump_users():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT email, is_active FROM users"))
        rows = result.fetchall()
        print(f"User Count: {len(rows)}")
        for row in rows:
            print(f"User: {row[0]}, Active: {row[1]}")

if __name__ == "__main__":
    dump_users()
