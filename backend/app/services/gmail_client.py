"""
Gmail Client Service - Production-Grade Multi-Tenant Implementation

This service provides workspace-isolated Gmail API access with automatic token management.

Key Features:
- Workspace isolation (each workspace has its own Gmail connection)
- Automatic token refresh
- Encrypted token storage
- Error handling for invalid/expired tokens
"""

from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.models.email_integration import EmailIntegration
from app.core.security_utils import encrypt_token, decrypt_token
from app.core.config import settings


class GmailClientService:
    """
    Service for managing Gmail API clients per workspace.
    Ensures workspace isolation and automatic token refresh.
    """
    
    @staticmethod
    def get_integration(workspace_id: int, db: Session) -> Optional[EmailIntegration]:
        """
        Get active email integration for workspace.
        
        Args:
            workspace_id: ID of the workspace
            db: Database session
            
        Returns:
            EmailIntegration if found and active, None otherwise
        """
        return db.query(EmailIntegration).filter(
            EmailIntegration.workspace_id == workspace_id,
            EmailIntegration.provider == "google",
            EmailIntegration.is_active == True
        ).first()
    
    @staticmethod
    def _refresh_token_if_needed(integration: EmailIntegration, db: Session) -> bool:
        """
        Refresh access token if expired or about to expire.
        
        Args:
            integration: EmailIntegration instance
            db: Database session
            
        Returns:
            True if token is valid (refreshed or not expired), False if refresh failed
        """
        # Check if token expires in next 5 minutes
        # meaningful comparison: both must be offset-aware or both naive.
        # expires_at is TIMESTAMPTZ (aware), so we need aware UTC current time.
        from datetime import timezone
        if integration.expires_at > datetime.now(timezone.utc) + timedelta(minutes=5):
            return True  # Token still valid
        
        try:
            # Decrypt refresh token
            refresh_token = decrypt_token(integration.refresh_token)
            
            if not refresh_token:
                integration.is_active = False
                db.commit()
                return False
            
            # Create credentials with refresh token
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                scopes=['https://www.googleapis.com/auth/gmail.send',
                       'https://www.googleapis.com/auth/gmail.readonly',
                       'https://www.googleapis.com/auth/gmail.modify']
            )
            
            # Refresh the token
            request = Request()
            creds.refresh(request)
            
            # Update integration with new token
            integration.access_token = encrypt_token(creds.token)
            integration.expires_at = creds.expiry
            integration.updated_at = datetime.utcnow()
            
            db.commit()
            return True
            
        except Exception as e:
            print(f"Token refresh failed for workspace {integration.workspace_id}: {str(e)}")
            # Mark integration as unhealthy
            integration.is_active = False
            db.commit()
            return False
    
    @staticmethod
    def get_gmail_client(workspace_id: int, db: Session):
        """
        Get authenticated Gmail API client for workspace.
        
        This is the main entry point for all Gmail operations.
        Handles workspace isolation, token refresh, and error handling.
        
        Args:
            workspace_id: ID of the workspace
            db: Database session
            
        Returns:
            Authenticated Gmail service object
            
        Raises:
            ValueError: If no active integration found
            Exception: If token refresh fails
        """
        # Get integration for workspace
        integration = GmailClientService.get_integration(workspace_id, db)
        
        if not integration:
            raise ValueError(f"No active Gmail integration found for workspace {workspace_id}")
        
        # Refresh token if needed
        if not GmailClientService._refresh_token_if_needed(integration, db):
            raise Exception(f"Failed to refresh token for workspace {workspace_id}. Please reconnect Gmail.")
        
        # Decrypt access token
        access_token = decrypt_token(integration.access_token)
        
        if not access_token:
            raise ValueError(f"Invalid access token for workspace {workspace_id}")
        
        # Create credentials
        creds = Credentials(
            token=access_token,
            refresh_token=decrypt_token(integration.refresh_token),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=['https://www.googleapis.com/auth/gmail.send',
                   'https://www.googleapis.com/auth/gmail.readonly',
                   'https://www.googleapis.com/auth/gmail.modify']
        )
        
        # Build and return Gmail service
        return build('gmail', 'v1', credentials=creds)
    
    @staticmethod
    def create_or_update_integration(
        workspace_id: int,
        email: str,
        access_token: str,
        refresh_token: str,
        expires_at: datetime,
        scope: str,
        db: Session
    ) -> EmailIntegration:
        """
        Create or update email integration for workspace.
        
        Args:
            workspace_id: ID of the workspace
            email: Connected email address
            access_token: OAuth access token (will be encrypted)
            refresh_token: OAuth refresh token (will be encrypted)
            expires_at: Token expiry datetime
            scope: OAuth scopes granted
            db: Database session
            
        Returns:
            Created or updated EmailIntegration
        """
        # Check if integration exists
        integration = db.query(EmailIntegration).filter(
            EmailIntegration.workspace_id == workspace_id,
            EmailIntegration.provider == "google"
        ).first()
        
        if integration:
            # Update existing
            integration.email = email
            integration.access_token = encrypt_token(access_token)
            integration.refresh_token = encrypt_token(refresh_token)
            integration.expires_at = expires_at
            integration.scope = scope
            integration.is_active = True
            integration.connected_at = datetime.utcnow()
            integration.updated_at = datetime.utcnow()
        else:
            # Create new
            integration = EmailIntegration(
                workspace_id=workspace_id,
                provider="google",
                email=email,
                access_token=encrypt_token(access_token),
                refresh_token=encrypt_token(refresh_token),
                expires_at=expires_at,
                scope=scope,
                is_active=True
            )
            db.add(integration)
        
        db.commit()
        db.refresh(integration)
        return integration
    
    @staticmethod
    def disconnect_integration(workspace_id: int, db: Session) -> bool:
        """
        Disconnect Gmail integration for workspace.
        
        Args:
            workspace_id: ID of the workspace
            db: Database session
            
        Returns:
            True if disconnected, False if no integration found
        """
        integration = db.query(EmailIntegration).filter(
            EmailIntegration.workspace_id == workspace_id,
            EmailIntegration.provider == "google"
        ).first()
        
        if integration:
            # Soft delete - mark as inactive
            integration.is_active = False
            integration.updated_at = datetime.utcnow()
            db.commit()
            return True
        
        return False


# Convenience function for easy imports
def get_gmail_client(workspace_id: int, db: Session):
    """
    Convenience function to get Gmail client.
    
    Usage:
        from app.services.gmail_client import get_gmail_client
        
        service = get_gmail_client(workspace_id=1, db=db)
        messages = service.users().messages().list(userId='me').execute()
    """
    return GmailClientService.get_gmail_client(workspace_id, db)
