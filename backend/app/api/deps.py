from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core import security
from app.core.config import settings
from app.models.user import User, UserRole
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_active_owner(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != UserRole.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_active_staff_or_owner(
    current_user: User = Depends(get_current_active_user),
) -> User:
    return current_user

def get_current_active_staff_or_owner_optional(
    current_user: User = Depends(get_current_active_user),
) -> User:
    # Same as above, but allows None if not authenticated?
    # Actually, Depends(get_current_active_user) will raise 401 if no token.
    # We need a new dependency chain for optional auth.
    return current_user

# --- Optional Auth Chain ---

oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def get_current_user_optional(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme_optional)
) -> User:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
    except jwt.PyJWTError:
        return None
        
    user = db.query(User).filter(User.id == user_id).first()
    return user if user and user.is_active else None

def get_current_active_staff_or_owner_optional(
    current_user: User = Depends(get_current_user_optional),
) -> User:
    # Returns User if valid, None otherwise.
    return current_user
