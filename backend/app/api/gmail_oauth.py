from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import os

from app.api import deps
from app.models.workspace import Workspace
from app.core.config import settings
from app.core.security_utils import encrypt_token

router = APIRouter()

# OAuth scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_oauth_flow(redirect_uri: str):
    """Create OAuth flow instance"""
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    return flow

@router.get("/gmail/connect")
def start_gmail_oauth(
    request: Request,
    current_user = Depends(deps.get_current_user)
):
    """
    Initiate Gmail OAuth flow
    """
    # Build redirect URI
    redirect_uri = f"{settings.FRONTEND_URL}/settings/gmail-callback"
    
    flow = get_oauth_flow(redirect_uri)
    
    # Generate authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent to get refresh token
    )
    
    # Store state in session or return to frontend
    return {
        "authorization_url": authorization_url,
        "state": state
    }

@router.post("/gmail/callback")
def gmail_oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Handle OAuth callback and save tokens
    """
    try:
        redirect_uri = f"{settings.FRONTEND_URL}/settings/gmail-callback"
        flow = get_oauth_flow(redirect_uri)
        
        # Exchange code for tokens
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Get workspace
        workspace = db.query(Workspace).filter(
            Workspace.id == current_user.workspace_id
        ).first()
        
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Encrypt and save refresh token
        encrypted_token = encrypt_token(credentials.refresh_token)
        
        workspace.google_connected = True
        workspace.google_refresh_token = encrypted_token
        workspace.google_email = credentials.token  # Store email if available
        
        db.commit()
        
        return {
            "message": "Gmail connected successfully",
            "connected": True
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth failed: {str(e)}")

@router.post("/gmail/disconnect")
def disconnect_gmail(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Disconnect Gmail integration
    """
    workspace = db.query(Workspace).filter(
        Workspace.id == current_user.workspace_id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    workspace.google_connected = False
    workspace.google_refresh_token = None
    workspace.google_email = None
    
    db.commit()
    
    return {
        "message": "Gmail disconnected",
        "connected": False
    }

@router.get("/gmail/status")
def get_gmail_status(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Check Gmail connection status
    """
    workspace = db.query(Workspace).filter(
        Workspace.id == current_user.workspace_id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    return {
        "connected": workspace.google_connected or False,
        "email": workspace.google_email if workspace.google_connected else None
    }
