from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import asyncio

from app.db.session import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.api.deps import get_current_user
from app.core.security_utils import encrypt_token
from app.services.email import send_test_email
from app.core.config import settings

# Google Libraries
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

router = APIRouter()

class GoogleConnectRequest(BaseModel):
    code: str
    redirect_uri: str

class GoogleConnectResponse(BaseModel):
    success: bool
    email: str

class GoogleStatusResponse(BaseModel):
    connected: bool
    email: Optional[str] = None

@router.get("/google", response_model=GoogleStatusResponse)
def get_google_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    return {
        "connected": workspace.google_connected or False,
        "email": workspace.google_email
    }

@router.post("/google/connect", response_model=GoogleConnectResponse)
def connect_google(
    request: GoogleConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Not authorized")

    # If client ID/Secret are not configured, we cannot proceed with real exchange
    if not hasattr(settings, 'GOOGLE_CLIENT_ID') or not settings.GOOGLE_CLIENT_ID:
        # Check if we should fail or mock based on context (Hackathon/Dev)
        # For now, we will raise an error if not present, but user can mock via frontend sending "MOCK_CODE"
        # Or better: let's include a fallback logic for demonstration if keys are missing
        if request.code.startswith("mock_"):
            # Allow mock connection for testing UI flow if backend isn't fully configured with cloud console
            workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
            workspace.google_connected = True
            workspace.google_email = "mock-owner@example.com"
            workspace.google_refresh_token = encrypt_token(f"mock-refresh-{request.code}")
            workspace.google_token_expiry = datetime.utcnow()
            db.commit()
            return {"success": True, "email": workspace.google_email}
            
        raise HTTPException(status_code=500, detail="Server misconfiguration: Missing GOOGLE_CLIENT_ID")

    try:
        # Real OAuth Exchange
        # Note: In production, client secrets should be in a file or env.
        # Flow needs client_config dictionary if not from file.
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/userinfo.email'],
            redirect_uri=request.redirect_uri
        )
        
        flow.fetch_token(code=request.code)
        creds = flow.credentials
        
        # Get Email Address
        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()
        email = user_info.get('email')
        
        workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
        workspace.google_connected = True
        workspace.google_email = email
        workspace.google_refresh_token = encrypt_token(creds.refresh_token)
        # Note: creds.expiry is a datetime object usually
        workspace.google_token_expiry = creds.expiry if creds.expiry else datetime.utcnow()
        
        db.commit()
        
        return {"success": True, "email": email}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth Exchange Failed: {str(e)}")

@router.post("/google/disconnect")
def disconnect_google(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if workspace:
        workspace.google_connected = False
        workspace.google_email = None
        workspace.google_refresh_token = None
        workspace.google_token_expiry = None
        db.commit()
        
    return {"success": True}

@router.post("/google/test")
async def test_google_integration(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Not authorized")

    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    
    if not workspace.google_connected:
         raise HTTPException(status_code=400, detail="Google not connected")

    # Send test email
    await send_test_email(workspace.id)
    
    return {"status": "success", "message": "Test email queued. Check your inbox."}
