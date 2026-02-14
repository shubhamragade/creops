from app.core.security import get_password_hash
try:
    print(f"Hashing 'owner123'...")
    h = get_password_hash("owner123")
    print(f"Success: {h}")
except Exception as e:
    print(f"Error: {e}")
