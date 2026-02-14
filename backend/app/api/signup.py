from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta
import re

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.workspace import Workspace
from app.models.user import User
from app.schemas.signup import SignupRequest, SignupResponse
from app.db.session import SessionLocal

router = APIRouter()

def create_slug(business_name: str) -> str:
    """Generate URL-friendly slug from business name"""
    slug = business_name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug[:50]  # Limit length

@router.post("/signup", response_model=SignupResponse)
def signup_business(
    signup_data: SignupRequest,
    db: Session = Depends(deps.get_db)
):
    """
    Create new business workspace + owner account
    """
    # 1. Check if email already exists
    existing_user = db.query(User).filter(User.email == signup_data.owner_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 2. Generate unique slug
    base_slug = create_slug(signup_data.business_name)
    slug = base_slug
    counter = 1
    while db.query(Workspace).filter(Workspace.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # 3. Create Workspace
    workspace = Workspace(
        name=signup_data.business_name,
        slug=slug,
        contact_email=signup_data.owner_email,
        address=signup_data.business_address,
        timezone=signup_data.timezone,
        is_active=True
    )
    db.add(workspace)
    db.flush()
    
    # 4. Create Owner User
    owner = User(
        email=signup_data.owner_email,
        hashed_password=security.get_password_hash(signup_data.owner_password),
        full_name=signup_data.owner_full_name,
        role="owner",
        workspace_id=workspace.id,
        is_active=True
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)
    
    # 5. Generate Access Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=owner.id,
        workspace_id=workspace.id,
        expires_delta=access_token_expires,
    )
    
    return SignupResponse(
        workspace_id=workspace.id,
        workspace_slug=slug,
        access_token=access_token,
        message="Business created successfully! Welcome to CareOps."
    )
