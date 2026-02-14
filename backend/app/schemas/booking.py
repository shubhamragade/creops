from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.schemas.onboarding import ServiceCreate # Re-use or redefine? Better to have dedicated output.

class BookingCreate(BaseModel):
    service_id: int
    start_datetime: datetime
    name: str
    email: EmailStr
    phone: Optional[str] = None

class ServiceOut(BaseModel):
    id: int
    name: str
    duration_minutes: int
    location: Optional[str] = None
    class Config:
        orm_mode = True

class ContactOut(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    class Config:
        orm_mode = True

class BookingOut(BaseModel):
    id: int
    service_id: int
    contact_id: int
    start_time: datetime
    end_time: datetime
    status: str
    created_at: Optional[datetime] = None
    service: Optional[ServiceOut] = None
    contact: Optional[ContactOut] = None

    class Config:
        orm_mode = True

class BookingUpdate(BaseModel):
    start_datetime: Optional[datetime] = None
    status: Optional[str] = None # For minor status updates like NO_SHOW

class ContactUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        orm_mode = True
