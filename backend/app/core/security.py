from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
# Lazy import to avoid circular dependency if possible, or use string forward ref check
# But here we need to query DB for user/workspace presumably, or just return token payload? 
# The brief says: "decode with pyjwt, get user/workspace from DB."
# So we need db session.
from app.db.session import SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Endpoint doesn't exist yet but required for Swagger

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], workspace_id: int, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "workspace_id": workspace_id}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        workspace_id: int = payload.get("workspace_id")
        if user_id is None or workspace_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    # Ideally verify user exists in DB
    # from app.models.user import User
    # user = db.query(User).filter(User.id == user_id).first()
    # if user is None:
    #     raise credentials_exception
    # For now returning payload/context as implied by "get user/workspace from DB"
    # To keep it simple and avoid circular imports within this file if models import security:
    # We will return the payload or a simple object. 
    # But brief says "get user/workspace from DB". I'll try to do that.
    
    # Check for circular imports: models.user -> ... 
    # Usually models don't import security. Security might import models.
    # We will perform the query.
    
    from app.models.user import User
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
         raise credentials_exception
         
    return user
