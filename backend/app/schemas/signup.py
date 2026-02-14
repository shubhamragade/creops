from pydantic import BaseModel, EmailStr
from typing import Optional

class SignupRequest(BaseModel):
    business_name: str
    owner_email: EmailStr
    owner_password: str
    owner_full_name: str
    business_address: Optional[str] = None
    business_phone: Optional[str] = None
    timezone: str = "Asia/Kolkata"

class SignupResponse(BaseModel):
    workspace_id: int
    workspace_slug: str
    access_token: str
    message: str

class LeadFormSubmission(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    message: Optional[str] = None

class LeadResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    status: str
    source: str
    created_at: str

class UpdateLeadStatus(BaseModel):
    status: str  # new, contacted, booked
