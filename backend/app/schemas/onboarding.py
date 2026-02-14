from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional, Any

class WorkspaceCreate(BaseModel):
    name: str
    address: str
    timezone: str = 'Asia/Kolkata'
    contact_email: EmailStr
    owner_email: EmailStr
    owner_password: str

class EmailConfig(BaseModel):
    api_key: str
    provider: str = 'brevo'
    from_email: EmailStr

class ServiceCreate(BaseModel):
    name: str
    duration_minutes: int
    availability: Dict[str, Any]  # e.g. {"days": ["mon","tue"], "slots": ["10:00-18:00"]}
    location: str
    inventory_item_id: Optional[int] = None
    inventory_quantity_required: Optional[int] = 0

class FormCreate(BaseModel):
    name: str
    linked_services: List[int] = []

class InventoryCreate(BaseModel):
    name: str
    quantity_available: int
    low_threshold: int

class StaffInvite(BaseModel):
    email: EmailStr
    permissions: Dict[str, bool]  # e.g. {"inbox": true, "bookings": true}

class Token(BaseModel):
    workspace_id: int
    access_token: str
