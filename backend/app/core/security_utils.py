from cryptography.fernet import Fernet
from app.core.config import settings
import base64
import os

# Generate a key if not present in settings (for MVP/Dev only)
# Ideally this should come from env var via settings.ENCRYPTION_KEY
# If not set, we'll derive one from SECRET_KEY or generate a temporary one (bad for restarts)
# For this hackathon, let's use a fixed salt with the JWT_SECRET to be deterministic but simple
# Or just a simple obfuscation if true encryption is too heavy setup (but requirement said ENCRYPTED)

def _get_cipher_suite():
    # Use JWT_SECRET to derive a key, ensuring it's 32url-safe base64-encoded bytes
    # This is a bit hacky for MVP but keeps it stateless without new env vars
    key = settings.JWT_SECRET.encode()
    # Pad or truncate to 32 bytes
    if len(key) < 32:
        key = key + b'=' * (32 - len(key))
    else:
        key = key[:32]
    
    encoded_key = base64.urlsafe_b64encode(key)
    return Fernet(encoded_key)

def encrypt_token(token: str) -> str:
    if not token:
        return None
    cipher_suite = _get_cipher_suite()
    return cipher_suite.encrypt(token.encode()).decode()

def decrypt_token(token: str) -> str:
    if not token:
        return None
    cipher_suite = _get_cipher_suite()
    try:
        return cipher_suite.decrypt(token.encode()).decode()
    except Exception:
        return None

def generate_cancel_token(booking_id: int) -> str:
    """
    Generate a signed token for public cancellation.
    Format: "booking_id:signature"
    """
    data = str(booking_id)
    cipher_suite = _get_cipher_suite()
    signature = cipher_suite.encrypt(data.encode()).decode()
    return f"{booking_id}:{signature}"

def verify_cancel_token(token: str, booking_id: int) -> bool:
    """
    Verify if the token is valid for the given booking_id.
    """
    try:
        if not token or ":" not in token:
            return False
            
        token_id_str, signature = token.split(":", 1)
        
        # 1. ID Match Check
        if int(token_id_str) != booking_id:
            return False
            
        # 2. Signature Check
        cipher_suite = _get_cipher_suite()
        decoded_id = cipher_suite.decrypt(signature.encode()).decode()
        
        return int(decoded_id) == booking_id
    except Exception:
        return False
