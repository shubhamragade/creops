from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class EmailIntegrationBase(BaseModel):
    provider: str = "google"
    email: EmailStr


class EmailIntegrationCreate(EmailIntegrationBase):
    access_token: str
    refresh_token: str
    expires_at: datetime
    scope: Optional[str] = None


class EmailIntegrationUpdate(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    last_sync_at: Optional[datetime] = None


class EmailIntegrationResponse(EmailIntegrationBase):
    id: int
    workspace_id: int
    is_active: bool
    connected_at: datetime
    last_sync_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmailIntegrationStatus(BaseModel):
    """Public status response - never exposes tokens"""
    connected: bool
    email: Optional[str] = None
    provider: Optional[str] = None
    last_sync_at: Optional[datetime] = None
