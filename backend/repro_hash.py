from passlib.context import CryptContext
import logging

try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    print("Hashing 'test'...")
    hash_params = pwd_context.hash("test")
    print(f"Success: {hash_params}")
except Exception as e:
    print(f"FAIL: {e}")
