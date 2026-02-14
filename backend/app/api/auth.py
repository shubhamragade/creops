from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.workspace import Workspace

router = APIRouter()

@router.post("/login")
def login_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # 1. Authenticate User
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not user.is_active:
         raise HTTPException(status_code=400, detail="Inactive user")

    # 2. Get Workspace Slug (for frontend routing convenience)
    workspace = db.query(Workspace).filter(Workspace.id == user.workspace_id).first()
    workspace_slug = workspace.slug if workspace else ""

    # 3. Generate Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id,
        workspace_id=user.workspace_id,
        expires_delta=access_token_expires,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "workspace_slug": workspace_slug,
        "permissions": user.permissions if user.permissions else "{}"
    }
